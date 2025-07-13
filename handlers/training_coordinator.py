import json
import boto3
import os
from typing import Dict, Any
from datetime import datetime

def handler(event, context):
    """Lambda handler for coordinating PINN training"""
    
    try:
        # Initialize AWS clients
        ecs = boto3.client('ecs')
        batch = boto3.client('batch')
        dynamodb = boto3.resource('dynamodb')
        state_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        # Parse SQS messages
        for record in event['Records']:
            message_body = json.loads(record['body'])
            workflow_id = message_body['workflow_id']
            analysis_result = message_body['analysis_result']
            original_request = message_body['original_request']
            
            print(f"Coordinating training for workflow {workflow_id}")
            
            # Determine training platform based on analysis
            deployment_strategy = analysis_result['deployment_strategy']
            training_platform = deployment_strategy['training_platform']
            
            # Update status
            state_table.update_item(
                Key={"workflow_id": workflow_id},
                UpdateExpression="SET #status = :status, progress = :progress, current_step = :step, updated_at = :updated_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": "training_starting",
                    ":progress": 30.0,
                    ":step": f"starting_{training_platform}",
                    ":updated_at": datetime.utcnow().isoformat()
                }
            )
            
            if training_platform == "ecs_fargate":
                task_arn = start_ecs_training(ecs, workflow_id, analysis_result)
                print(f"Started ECS training task: {task_arn}")
                
            elif training_platform == "aws_batch":
                job_id = start_batch_training(batch, workflow_id, analysis_result)
                print(f"Started Batch training job: {job_id}")
                
            elif training_platform == "lambda_container":
                # For small jobs, we could use Lambda with container images
                # For now, fall back to ECS
                task_arn = start_ecs_training(ecs, workflow_id, analysis_result)
                print(f"Started ECS training task (fallback): {task_arn}")
            
            # Store training job info
            state_table.update_item(
                Key={"workflow_id": workflow_id},
                UpdateExpression="SET training_job_info = :job_info, #status = :status, progress = :progress, updated_at = :updated_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":job_info": {
                        "platform": training_platform,
                        "job_id": task_arn if training_platform == "ecs_fargate" else job_id,
                        "started_at": datetime.utcnow().isoformat()
                    },
                    ":status": "training_in_progress",
                    ":progress": 35.0,
                    ":updated_at": datetime.utcnow().isoformat()
                }
            )
            
        return {"statusCode": 200, "body": "Training coordination completed"}
        
    except Exception as e:
        print(f"Error in training coordination: {str(e)}")
        
        # Update workflow status to failed if we have workflow_id
        if 'workflow_id' in locals():
            try:
                state_table.update_item(
                    Key={"workflow_id": workflow_id},
                    UpdateExpression="SET #status = :status, error_message = :error, updated_at = :updated_at",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":status": "training_failed",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat()
                    }
                )
            except:
                pass
        
        return {"statusCode": 500, "body": str(e)}

def start_ecs_training(ecs_client, workflow_id: str, analysis_result: Dict[str, Any]) -> str:
    """Start ECS Fargate training task"""
    
    # Get resource recommendations
    resources = analysis_result['recommended_resources']
    
    # ECS task definition and cluster names (these would be created by infrastructure)
    cluster_name = os.environ.get('ECS_CLUSTER_NAME', 'pinn-training-cluster')
    task_definition = os.environ.get('ECS_TASK_DEFINITION', 'pinn-training-task')
    
    # Subnets and security groups (from environment or infrastructure)
    subnet_ids = os.environ.get('SUBNET_IDS', '').split(',')
    security_group_id = os.environ.get('SECURITY_GROUP_ID', '')
    
    # Start ECS task
    response = ecs_client.run_task(
        cluster=cluster_name,
        taskDefinition=task_definition,
        launchType='FARGATE',
        platformVersion='1.4.0',
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': subnet_ids,
                'securityGroups': [security_group_id],
                'assignPublicIp': 'DISABLED'
            }
        },
        overrides={
            'cpu': str(resources['ecs_cpu']),
            'memory': str(resources['ecs_memory']),
            'containerOverrides': [
                {
                    'name': 'pinn-trainer',
                    'command': ['python', 'app.py', workflow_id],
                    'environment': [
                        {
                            'name': 'WORKFLOW_ID',
                            'value': workflow_id
                        },
                        {
                            'name': 'DYNAMODB_TABLE',
                            'value': os.environ['DYNAMODB_TABLE']
                        },
                        {
                            'name': 'S3_MODELS_BUCKET',
                            'value': os.environ['S3_MODELS_BUCKET']
                        }
                    ]
                }
            ]
        },
        tags=[
            {
                'key': 'WorkflowId',
                'value': workflow_id
            },
            {
                'key': 'Service',
                'value': 'PINN-Training'
            }
        ]
    )
    
    return response['tasks'][0]['taskArn']

def start_batch_training(batch_client, workflow_id: str, analysis_result: Dict[str, Any]) -> str:
    """Start AWS Batch training job for long-running tasks"""
    
    # Get resource recommendations
    resources = analysis_result['recommended_resources']
    compute_estimate = analysis_result['compute_estimate']
    
    # Job queue and definition names (these would be created by infrastructure)
    job_queue = os.environ.get('BATCH_JOB_QUEUE', 'pinn-training-queue')
    job_definition = os.environ.get('BATCH_JOB_DEFINITION', 'pinn-training-job-def')
    
    # Determine instance type based on requirements
    if compute_estimate['memory_requirement_mb'] > 16384:
        instance_type = 'p3.2xlarge'  # V100 GPU
    elif compute_estimate['memory_requirement_mb'] > 8192:
        instance_type = 'g4dn.xlarge'  # T4 GPU
    else:
        instance_type = 'g4dn.large'   # Small T4 GPU
    
    # Submit batch job
    response = batch_client.submit_job(
        jobName=f'pinn-training-{workflow_id}',
        jobQueue=job_queue,
        jobDefinition=job_definition,
        parameters={
            'workflowId': workflow_id,
            'dynamodbTable': os.environ['DYNAMODB_TABLE'],
            's3ModelsBucket': os.environ['S3_MODELS_BUCKET']
        },
        containerOverrides={
            'vcpus': 4,
            'memory': resources['ecs_memory'],
            'environment': [
                {
                    'name': 'WORKFLOW_ID',
                    'value': workflow_id
                },
                {
                    'name': 'DYNAMODB_TABLE',
                    'value': os.environ['DYNAMODB_TABLE']
                },
                {
                    'name': 'S3_MODELS_BUCKET',
                    'value': os.environ['S3_MODELS_BUCKET']
                }
            ]
        },
        timeout={
            'attemptDurationSeconds': 14400  # 4 hours max
        },
        tags={
            'WorkflowId': workflow_id,
            'Service': 'PINN-Training',
            'Platform': 'Batch'
        }
    )
    
    return response['jobId']