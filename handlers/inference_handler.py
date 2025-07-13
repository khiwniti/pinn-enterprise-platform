import json
import os
import boto3
import numpy as np
import time
import pickle
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Global model cache to avoid cold start reloading
MODEL_CACHE = {}
MAX_CACHE_SIZE = 3

class PINNInferenceHandler:
    """Fast inference handler for trained PINN models"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.state_table = self.dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
    def handle_inference_batch(self, batch_messages: List[Dict]) -> List[Dict]:
        """Handle batch of inference requests"""
        
        results = []
        
        # Group by workflow_id for batch processing
        grouped_requests = {}
        for message in batch_messages:
            workflow_id = message['workflow_id']
            if workflow_id not in grouped_requests:
                grouped_requests[workflow_id] = []
            grouped_requests[workflow_id].append(message)
        
        # Process each workflow's requests
        for workflow_id, requests in grouped_requests.items():
            try:
                workflow_results = self.process_workflow_requests(workflow_id, requests)
                results.extend(workflow_results)
            except Exception as e:
                # Handle errors gracefully
                error_results = [
                    {
                        "workflow_id": workflow_id,
                        "status": "error", 
                        "error": str(e),
                        "request_id": req.get("request_id", "unknown")
                    } for req in requests
                ]
                results.extend(error_results)
        
        return results
    
    def process_workflow_requests(self, workflow_id: str, requests: List[Dict]) -> List[Dict]:
        """Process inference requests for a specific workflow"""
        
        # Load model (with caching)
        model_info = self.load_model_cached(workflow_id)
        
        results = []
        
        # Process requests in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for request in requests:
                future = executor.submit(
                    self.run_single_inference,
                    model_info, 
                    request['inference_params'],
                    request.get('request_id', 'unknown')
                )
                futures.append(future)
            
            # Collect results
            for i, future in enumerate(futures):
                try:
                    result = future.result(timeout=30)  # 30 second timeout per inference
                    result.update({
                        "workflow_id": workflow_id,
                        "status": "success",
                        "request_id": requests[i].get("request_id", "unknown")
                    })
                    results.append(result)
                    
                except Exception as e:
                    results.append({
                        "workflow_id": workflow_id,
                        "status": "error",
                        "error": str(e),
                        "request_id": requests[i].get("request_id", "unknown")
                    })
        
        return results
    
    def run_single_inference(self, model_info: Dict, inference_params: Dict, request_id: str) -> Dict:
        """Run single inference with the PINN model"""
        
        start_time = time.time()
        
        try:
            # Parse inference parameters
            input_points = np.array(inference_params['input_points'])
            
            # Validate input shape
            if len(input_points.shape) != 2:
                raise ValueError("Input points must be 2D array (n_points, n_dimensions)")
            
            # For this simplified implementation, we'll use a mock prediction
            # In a real implementation, you would load the actual DeepXDE model
            predictions = self.mock_pinn_prediction(input_points, model_info)
            
            # Convert to serializable format
            if isinstance(predictions, np.ndarray):
                predictions = predictions.tolist()
            
            inference_time = time.time() - start_time
            
            return {
                "predictions": predictions,
                "input_shape": input_points.shape,
                "inference_time_ms": inference_time * 1000,
                "n_points": len(input_points),
                "model_type": model_info.get("model_type", "unknown")
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "inference_time_ms": (time.time() - start_time) * 1000
            }
    
    def mock_pinn_prediction(self, input_points: np.ndarray, model_info: Dict) -> np.ndarray:
        """Mock PINN prediction for demonstration purposes"""
        
        # This is a simplified mock - in reality you would load and use the actual DeepXDE model
        domain_type = model_info.get("domain_type", "heat_transfer")
        
        if domain_type == "heat_transfer":
            # Mock heat transfer solution (e.g., steady-state heat equation)
            x, y = input_points[:, 0], input_points[:, 1]
            predictions = np.sin(np.pi * x) * np.sin(np.pi * y)
            
        elif domain_type == "fluid_dynamics":
            # Mock fluid flow solution
            x, y = input_points[:, 0], input_points[:, 1]
            u = np.sin(np.pi * x) * np.cos(np.pi * y)  # u velocity
            v = -np.cos(np.pi * x) * np.sin(np.pi * y)  # v velocity
            p = np.cos(np.pi * x) * np.cos(np.pi * y)   # pressure
            predictions = np.column_stack([u, v, p])
            
        elif domain_type == "structural_mechanics":
            # Mock displacement solution
            x, y = input_points[:, 0], input_points[:, 1]
            u_x = 0.1 * x * (1 - x) * y * (1 - y)  # x displacement
            u_y = 0.05 * x * (1 - x) * y * (1 - y)  # y displacement
            predictions = np.column_stack([u_x, u_y])
            
        else:
            # Default: single output
            predictions = np.random.normal(0, 0.1, len(input_points))
        
        return predictions
    
    def load_model_cached(self, workflow_id: str) -> Dict:
        """Load model with caching to avoid repeated S3 downloads"""
        
        if workflow_id in MODEL_CACHE:
            print(f"Using cached model for workflow {workflow_id}")
            return MODEL_CACHE[workflow_id]
        
        # Load model metadata from DynamoDB
        model_info = self.load_model_info(workflow_id)
        
        # Add to cache (with size limit)
        if len(MODEL_CACHE) >= MAX_CACHE_SIZE:
            # Remove oldest model
            oldest_key = next(iter(MODEL_CACHE))
            del MODEL_CACHE[oldest_key]
            print(f"Removed cached model {oldest_key} due to cache size limit")
        
        MODEL_CACHE[workflow_id] = model_info
        print(f"Cached model for workflow {workflow_id}")
        
        return model_info
    
    def load_model_info(self, workflow_id: str) -> Dict:
        """Load model information from DynamoDB"""
        
        try:
            response = self.state_table.get_item(Key={"workflow_id": workflow_id})
            
            if 'Item' not in response:
                raise ValueError(f"Workflow {workflow_id} not found")
            
            item = response['Item']
            
            if item.get('status') != 'completed':
                raise ValueError(f"Model for workflow {workflow_id} is not ready")
            
            # Extract model information
            analysis_result = item.get('analysis_result', {})
            original_request = item.get('request', {})
            
            model_info = {
                "workflow_id": workflow_id,
                "domain_type": original_request.get('domain_type', 'unknown'),
                "model_type": "deepxde_pinn",
                "architecture": analysis_result.get('pinn_config', {}),
                "training_metrics": item.get('training_metrics', {}),
                "loaded_at": datetime.utcnow().isoformat()
            }
            
            return model_info
            
        except Exception as e:
            raise ValueError(f"Failed to load model info for {workflow_id}: {str(e)}")

def handler(event, context):
    """Lambda handler for PINN inference"""
    
    try:
        # Parse SQS messages
        messages = []
        for record in event['Records']:
            message_body = json.loads(record['body'])
            messages.append(message_body)
        
        print(f"Processing {len(messages)} inference requests")
        
        # Run inference handler
        inference_handler = PINNInferenceHandler()
        results = inference_handler.handle_inference_batch(messages)
        
        # Store results in DynamoDB for client retrieval
        dynamodb = boto3.resource('dynamodb')
        state_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        for result in results:
            # Store inference result with TTL
            ttl = int((datetime.utcnow().timestamp()) + 3600)  # 1 hour TTL
            
            inference_record = {
                "workflow_id": f"inference_{result['workflow_id']}_{result['request_id']}",
                "ttl": ttl,
                "result_type": "inference",
                "inference_result": result,
                "created_at": datetime.utcnow().isoformat()
            }
            
            state_table.put_item(Item=inference_record)
            
            print(f"Stored inference result for request {result['request_id']}")
        
        # Publish metrics
        successful_inferences = len([r for r in results if r.get("status") == "success"])
        failed_inferences = len(results) - successful_inferences
        
        # CloudWatch metrics
        cloudwatch = boto3.client('cloudwatch')
        cloudwatch.put_metric_data(
            Namespace='PINNPlatform',
            MetricData=[
                {
                    'MetricName': 'InferenceRequests',
                    'Value': len(results),
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'SuccessfulInferences',
                    'Value': successful_inferences,
                    'Unit': 'Count'
                },
                {
                    'MetricName': 'FailedInferences',
                    'Value': failed_inferences,
                    'Unit': 'Count'
                }
            ]
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "processed": len(results),
                "successful": successful_inferences,
                "failed": failed_inferences
            })
        }
        
    except Exception as e:
        print(f"Error in inference handler: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }