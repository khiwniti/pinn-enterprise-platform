import json
import boto3
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

def handler(event, context):
    """Lambda handler for resource optimization and cost management"""
    
    try:
        # Initialize AWS clients
        ecs = boto3.client('ecs')
        cloudwatch = boto3.client('cloudwatch')
        s3 = boto3.client('s3')
        dynamodb = boto3.resource('dynamodb')
        
        print("Starting resource optimization cycle")
        
        # 1. Optimize ECS cluster capacity
        optimize_ecs_capacity(ecs, cloudwatch)
        
        # 2. Clean up old models and data
        cleanup_old_resources(s3, dynamodb)
        
        # 3. Publish cost and usage metrics
        publish_usage_metrics(cloudwatch, dynamodb)
        
        print("Resource optimization completed successfully")
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Resource optimization completed",
                "timestamp": datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in resource optimization: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def optimize_ecs_capacity(ecs_client, cloudwatch_client):
    """Optimize ECS cluster capacity based on demand"""
    
    try:
        cluster_name = os.environ.get('ECS_CLUSTER_NAME', 'pinn-training-cluster')
        
        # Get current running tasks
        tasks_response = ecs_client.list_tasks(cluster=cluster_name)
        running_tasks = len(tasks_response.get('taskArns', []))
        
        # Get SQS queue metrics for the last 5 minutes
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        queue_metrics = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/SQS',
            MetricName='ApproximateNumberOfMessages',
            Dimensions=[
                {
                    'Name': 'QueueName',
                    'Value': os.environ.get('SQS_TRAINING_QUEUE', '').split('/')[-1]
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=300,
            Statistics=['Average']
        )
        
        # Calculate average queue depth
        avg_queue_depth = 0
        if queue_metrics['Datapoints']:
            avg_queue_depth = sum(dp['Average'] for dp in queue_metrics['Datapoints']) / len(queue_metrics['Datapoints'])
        
        # Determine optimal capacity (1 task per 2 messages in queue, min 0, max 5)
        optimal_capacity = min(max(int(avg_queue_depth / 2), 0), 5)
        
        print(f"Current tasks: {running_tasks}, Queue depth: {avg_queue_depth}, Optimal capacity: {optimal_capacity}")
        
        # Update service capacity if needed
        if abs(running_tasks - optimal_capacity) > 1:  # Only update if significant difference
            service_name = os.environ.get('ECS_SERVICE_NAME', 'pinn-training-service')
            
            ecs_client.update_service(
                cluster=cluster_name,
                service=service_name,
                desiredCount=optimal_capacity
            )
            
            print(f"Updated ECS service desired count to {optimal_capacity}")
        
        # Publish capacity metrics
        cloudwatch_client.put_metric_data(
            Namespace='PINNPlatform',
            MetricData=[
                {
                    'MetricName': 'ECSRunningTasks',
                    'Value': running_tasks,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'TrainingQueueDepth',
                    'Value': avg_queue_depth,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'OptimalCapacity',
                    'Value': optimal_capacity,
                    'Unit': 'Count'
                }
            ]
        )
        
    except Exception as e:
        print(f"Error optimizing ECS capacity: {str(e)}")

def cleanup_old_resources(s3_client, dynamodb):
    """Clean up old models and data to reduce storage costs"""
    
    try:
        bucket_name = os.environ['S3_MODELS_BUCKET']
        state_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        # Clean up models older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # List old objects in S3
        paginator = s3_client.get_paginator('list_objects_v2')
        objects_to_delete = []
        total_size_deleted = 0
        
        for page in paginator.paginate(Bucket=bucket_name, Prefix='models/'):
            for obj in page.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    objects_to_delete.append({'Key': obj['Key']})
                    total_size_deleted += obj['Size']
        
        # Delete old objects in batches
        if objects_to_delete:
            # S3 delete_objects can handle up to 1000 objects at a time
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i:i+1000]
                s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': batch}
                )
            
            print(f"Deleted {len(objects_to_delete)} old model files, freed {total_size_deleted / (1024*1024):.2f} MB")
        
        # Clean up old DynamoDB records (completed workflows older than 7 days)
        scan_response = state_table.scan(
            FilterExpression='#status = :status AND created_at < :cutoff',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':cutoff': (datetime.utcnow() - timedelta(days=7)).isoformat()
            },
            ProjectionExpression='workflow_id'
        )
        
        # Delete old completed workflows
        old_workflows = scan_response.get('Items', [])
        for workflow in old_workflows:
            state_table.delete_item(Key={'workflow_id': workflow['workflow_id']})
        
        if old_workflows:
            print(f"Deleted {len(old_workflows)} old workflow records")
        
        # Publish cleanup metrics
        cloudwatch = boto3.client('cloudwatch')
        cloudwatch.put_metric_data(
            Namespace='PINNPlatform',
            MetricData=[
                {
                    'MetricName': 'DeletedModelFiles',
                    'Value': len(objects_to_delete),
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'FreedStorageMB',
                    'Value': total_size_deleted / (1024*1024),
                    'Unit': 'None'
                },
                {
                    'MetricName': 'DeletedWorkflowRecords',
                    'Value': len(old_workflows),
                    'Unit': 'Count'
                }
            ]
        )
        
    except Exception as e:
        print(f"Error cleaning up old resources: {str(e)}")

def publish_usage_metrics(cloudwatch_client, dynamodb):
    """Publish platform usage and cost metrics"""
    
    try:
        state_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        # Get workflow statistics for the last 24 hours
        cutoff_time = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        # Scan for recent workflows
        scan_response = state_table.scan(
            FilterExpression='created_at > :cutoff',
            ExpressionAttributeValues={':cutoff': cutoff_time}
        )
        
        workflows = scan_response.get('Items', [])
        
        # Calculate statistics
        total_workflows = len(workflows)
        completed_workflows = len([w for w in workflows if w.get('status') == 'completed'])
        failed_workflows = len([w for w in workflows if w.get('status') == 'failed'])
        in_progress_workflows = len([w for w in workflows if w.get('status') in ['training_in_progress', 'analyzing_problem']])
        
        # Domain type distribution
        domain_counts = {}
        for workflow in workflows:
            domain = workflow.get('request', {}).get('domain_type', 'unknown')
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Publish metrics
        metric_data = [
            {
                'MetricName': 'TotalWorkflows24h',
                'Value': total_workflows,
                'Unit': 'Count'
            },
            {
                'MetricName': 'CompletedWorkflows24h',
                'Value': completed_workflows,
                'Unit': 'Count'
            },
            {
                'MetricName': 'FailedWorkflows24h',
                'Value': failed_workflows,
                'Unit': 'Count'
            },
            {
                'MetricName': 'InProgressWorkflows',
                'Value': in_progress_workflows,
                'Unit': 'Count'
            }
        ]
        
        # Add domain-specific metrics
        for domain, count in domain_counts.items():
            metric_data.append({
                'MetricName': 'WorkflowsByDomain',
                'Value': count,
                'Unit': 'Count',
                'Dimensions': [
                    {
                        'Name': 'Domain',
                        'Value': domain
                    }
                ]
            })
        
        # Calculate success rate
        if total_workflows > 0:
            success_rate = (completed_workflows / total_workflows) * 100
            metric_data.append({
                'MetricName': 'SuccessRate24h',
                'Value': success_rate,
                'Unit': 'Percent'
            })
        
        cloudwatch_client.put_metric_data(
            Namespace='PINNPlatform',
            MetricData=metric_data
        )
        
        print(f"Published usage metrics: {total_workflows} total, {completed_workflows} completed, {failed_workflows} failed")
        
        # Estimate costs (simplified)
        estimated_cost = estimate_daily_cost(workflows)
        
        cloudwatch_client.put_metric_data(
            Namespace='PINNPlatform',
            MetricData=[
                {
                    'MetricName': 'EstimatedDailyCost',
                    'Value': estimated_cost,
                    'Unit': 'None'  # USD
                }
            ]
        )
        
    except Exception as e:
        print(f"Error publishing usage metrics: {str(e)}")

def estimate_daily_cost(workflows: List[Dict]) -> float:
    """Estimate daily cost based on workflow usage"""
    
    total_cost = 0.0
    
    # AWS pricing (approximate, as of 2025)
    pricing = {
        'lambda_invocations': 0.0000002,  # per invocation
        'lambda_gb_sec': 0.0000166667,    # per GB-second
        'ecs_fargate_cpu_hour': 0.04048,  # per vCPU hour
        'ecs_fargate_memory_hour': 0.004445,  # per GB hour
        's3_storage_gb_month': 0.023,     # per GB per month
        'sqs_requests': 0.0000004         # per request
    }
    
    for workflow in workflows:
        # Lambda costs (API + analysis + inference)
        lambda_invocations = 10  # Estimated invocations per workflow
        lambda_duration_sec = 30  # Estimated total duration
        lambda_memory_gb = 3.008  # Max Lambda memory
        
        lambda_cost = (
            lambda_invocations * pricing['lambda_invocations'] +
            lambda_duration_sec * lambda_memory_gb * pricing['lambda_gb_sec']
        )
        
        # ECS training costs
        training_metrics = workflow.get('training_metrics', {})
        training_time_hours = training_metrics.get('total_training_time', 1800) / 3600  # Convert to hours
        
        ecs_cost = (
            training_time_hours * 4 * pricing['ecs_fargate_cpu_hour'] +  # 4 vCPUs
            training_time_hours * 16 * pricing['ecs_fargate_memory_hour']  # 16 GB memory
        )
        
        # Storage costs (estimated)
        storage_cost = 0.1 * pricing['s3_storage_gb_month'] / 30  # ~100MB per model per day
        
        # SQS costs
        sqs_cost = 20 * pricing['sqs_requests']  # Estimated messages per workflow
        
        workflow_cost = lambda_cost + ecs_cost + storage_cost + sqs_cost
        total_cost += workflow_cost
    
    return round(total_cost, 4)