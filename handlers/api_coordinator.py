import json
import asyncio
import os
import uuid
from typing import Dict, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import boto3
from pydantic import BaseModel

app = FastAPI(title="PINN DeepXDE Simulation Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS clients
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# DynamoDB table for state management
state_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

class PINNRequest(BaseModel):
    problem_description: str
    domain_type: str  # "heat_transfer", "fluid_dynamics", "structural", "electromagnetics"
    geometry: Dict[str, Any]
    boundary_conditions: Dict[str, Any]
    initial_conditions: Dict[str, Any] = {}
    physics_parameters: Dict[str, Any]
    accuracy_requirements: float = 0.95
    max_training_time: int = 3600  # seconds
    real_time_inference: bool = True

class PINNResponse(BaseModel):
    workflow_id: str
    status: str
    estimated_completion_time: int
    endpoints: Dict[str, str]

class WorkflowStatus(BaseModel):
    workflow_id: str
    status: str
    progress: float
    created_at: str
    updated_at: str
    estimated_completion: str
    current_step: str
    error_message: str = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "PINN DeepXDE Platform",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Test DynamoDB connection
        state_table.scan(Limit=1)
        
        # Test SQS connection
        sqs.get_queue_attributes(
            QueueUrl=os.environ['SQS_TRAINING_QUEUE'],
            AttributeNames=['ApproximateNumberOfMessages']
        )
        
        return {
            "status": "healthy",
            "services": {
                "dynamodb": "connected",
                "sqs": "connected",
                "s3": "connected"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/pinn/solve", response_model=PINNResponse)
async def create_pinn_solution(request: PINNRequest, background_tasks: BackgroundTasks):
    """Main endpoint for PINN-based physics simulation"""
    
    workflow_id = str(uuid.uuid4())
    
    # Store initial state
    await store_workflow_state(workflow_id, {
        "status": "initiated",
        "progress": 0.0,
        "request": request.dict(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "estimated_completion": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "current_step": "problem_analysis"
    })
    
    # Start async workflow
    background_tasks.add_task(initiate_pinn_workflow, workflow_id, request)
    
    return PINNResponse(
        workflow_id=workflow_id,
        status="initiated",
        estimated_completion_time=3600,  # 1 hour default
        endpoints={
            "status": f"/pinn/status/{workflow_id}",
            "results": f"/pinn/results/{workflow_id}",
            "inference": f"/pinn/inference/{workflow_id}"
        }
    )

async def initiate_pinn_workflow(workflow_id: str, request: PINNRequest):
    """Orchestrate the complete PINN workflow"""
    
    try:
        # Step 1: Analyze problem and determine PINN architecture
        analysis_message = {
            "workflow_id": workflow_id,
            "step": "problem_analysis",
            "payload": request.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await send_to_queue(
            queue_url=os.environ['SQS_ANALYSIS_QUEUE'],
            message=analysis_message
        )
        
        await update_workflow_status(workflow_id, "analyzing_problem", 10.0)
        
    except Exception as e:
        await update_workflow_status(workflow_id, "failed", 0.0, error_message=str(e))

@app.get("/pinn/status/{workflow_id}", response_model=WorkflowStatus)
async def get_workflow_status(workflow_id: str):
    """Get current status of PINN workflow"""
    
    try:
        response = state_table.get_item(Key={"workflow_id": workflow_id})
        
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        item = response['Item']
        return WorkflowStatus(
            workflow_id=workflow_id,
            status=item.get('status', 'unknown'),
            progress=float(item.get('progress', 0.0)),
            created_at=item.get('created_at', ''),
            updated_at=item.get('updated_at', ''),
            estimated_completion=item.get('estimated_completion', ''),
            current_step=item.get('current_step', ''),
            error_message=item.get('error_message')
        )
        
    except Exception as e:
        if "Workflow not found" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pinn/results/{workflow_id}")
async def get_simulation_results(workflow_id: str):
    """Retrieve completed simulation results"""
    
    try:
        # Get workflow state
        state = await get_workflow_state(workflow_id)
        
        if state['status'] != 'completed':
            raise HTTPException(status_code=202, detail="Simulation still in progress")
            
        # Retrieve results from S3
        results_key = f"results/{workflow_id}/simulation_results.json"
        results = await download_from_s3(
            bucket=os.environ['S3_MODELS_BUCKET'],
            key=results_key
        )
        
        return json.loads(results)
        
    except Exception as e:
        if "still in progress" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/pinn/inference/{workflow_id}")
async def real_time_inference(workflow_id: str, inference_params: Dict[str, Any]):
    """Real-time inference using trained PINN model"""
    
    try:
        # Check if model is ready for inference
        state = await get_workflow_state(workflow_id)
        
        if state.get('status') != 'completed' or 'inference_endpoint' not in state:
            raise HTTPException(status_code=404, detail="Model not ready for inference")
        
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Send to fast inference queue
        inference_message = {
            "workflow_id": workflow_id,
            "request_id": request_id,
            "inference_params": inference_params,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await send_to_queue(
            queue_url=os.environ['SQS_INFERENCE_QUEUE'],
            message=inference_message
        )
        
        return {
            "status": "inference_queued",
            "request_id": request_id,
            "estimated_time": "5-30 seconds"
        }
        
    except Exception as e:
        if "not ready for inference" in str(e):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pinn/workflows")
async def list_workflows(limit: int = 10, status: str = None):
    """List recent workflows with optional status filter"""
    
    try:
        scan_kwargs = {
            'Limit': limit,
            'ProjectionExpression': 'workflow_id, #status, created_at, updated_at, current_step',
            'ExpressionAttributeNames': {'#status': 'status'}
        }
        
        if status:
            scan_kwargs['FilterExpression'] = '#status = :status'
            scan_kwargs['ExpressionAttributeValues'] = {':status': status}
        
        response = state_table.scan(**scan_kwargs)
        
        workflows = []
        for item in response.get('Items', []):
            workflows.append({
                'workflow_id': item['workflow_id'],
                'status': item.get('status', 'unknown'),
                'created_at': item.get('created_at', ''),
                'updated_at': item.get('updated_at', ''),
                'current_step': item.get('current_step', '')
            })
        
        # Sort by created_at descending
        workflows.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            "workflows": workflows,
            "count": len(workflows)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def store_workflow_state(workflow_id: str, state_data: Dict[str, Any]):
    """Store workflow state in DynamoDB"""
    state_table.put_item(
        Item={
            "workflow_id": workflow_id,
            "ttl": int((datetime.utcnow() + timedelta(days=7)).timestamp()),
            **state_data
        }
    )

async def update_workflow_status(workflow_id: str, status: str, progress: float, 
                               current_step: str = None, error_message: str = None):
    """Update workflow status in DynamoDB"""
    
    update_expression = "SET #status = :status, progress = :progress, updated_at = :updated_at"
    expression_attribute_names = {"#status": "status"}
    expression_attribute_values = {
        ":status": status,
        ":progress": progress,
        ":updated_at": datetime.utcnow().isoformat()
    }
    
    if current_step:
        update_expression += ", current_step = :current_step"
        expression_attribute_values[":current_step"] = current_step
    
    if error_message:
        update_expression += ", error_message = :error_message"
        expression_attribute_values[":error_message"] = error_message
    
    state_table.update_item(
        Key={"workflow_id": workflow_id},
        UpdateExpression=update_expression,
        ExpressionAttributeNames=expression_attribute_names,
        ExpressionAttributeValues=expression_attribute_values
    )

async def get_workflow_state(workflow_id: str) -> Dict[str, Any]:
    """Get workflow state from DynamoDB"""
    response = state_table.get_item(Key={"workflow_id": workflow_id})
    
    if 'Item' not in response:
        raise ValueError("Workflow not found")
    
    return response['Item']

async def send_to_queue(queue_url: str, message: Dict[str, Any]):
    """Send message to SQS queue"""
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message, default=str),
        MessageAttributes={
            'workflow_id': {
                'StringValue': message.get('workflow_id', ''),
                'DataType': 'String'
            },
            'step': {
                'StringValue': message.get('step', ''),
                'DataType': 'String'
            }
        }
    )

async def download_from_s3(bucket: str, key: str) -> str:
    """Download file content from S3"""
    response = s3.get_object(Bucket=bucket, Key=key)
    return response['Body'].read().decode('utf-8')

# Lambda handler
handler = Mangum(app)