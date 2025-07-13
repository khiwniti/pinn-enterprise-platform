import json
import boto3
import os
from typing import Dict, Any, List
import numpy as np
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PINNArchitectureConfig:
    """Configuration for PINN model architecture"""
    input_dim: int
    output_dim: int
    hidden_layers: List[int]
    activation: str
    layer_sizes: List[int]
    network_type: str  # "feedforward", "resnet", "modified_mfnn"
    initialization: str
    loss_weights: Dict[str, float]
    optimizer_config: Dict[str, Any]

class ComplexityEstimator:
    """Estimate problem complexity for PINN architecture selection"""
    
    def assess_complexity(self, geometry: Dict, physics: Dict, domain_type: str) -> float:
        """Assess problem complexity on a scale of 0-1"""
        
        complexity_score = 0.0
        
        # Geometry complexity
        if geometry.get("type") == "rectangle":
            complexity_score += 0.1
        elif geometry.get("type") == "circle":
            complexity_score += 0.2
        elif geometry.get("type") == "complex_polygon":
            complexity_score += 0.4
        elif geometry.get("type") == "3d_mesh":
            complexity_score += 0.6
        
        # Spatial dimensions
        spatial_dims = geometry.get("spatial_dims", 2)
        complexity_score += min(spatial_dims / 3.0, 0.3)
        
        # Time dependency
        if geometry.get("time_dependent", False):
            complexity_score += 0.2
        
        # Physics complexity
        if domain_type == "heat_transfer":
            complexity_score += 0.1
        elif domain_type == "fluid_dynamics":
            complexity_score += 0.4  # Navier-Stokes is complex
        elif domain_type == "structural_mechanics":
            complexity_score += 0.3
        elif domain_type == "electromagnetics":
            complexity_score += 0.5
        
        # Nonlinear terms
        if physics.get("nonlinear", False):
            complexity_score += 0.2
        
        # Multiple physics coupling
        if physics.get("coupled_physics", False):
            complexity_score += 0.3
        
        return min(complexity_score, 1.0)

class PINNProblemAnalyzer:
    """Analyze physics problems and recommend optimal PINN configuration"""
    
    def __init__(self):
        self.supported_domains = {
            "heat_transfer": self._configure_heat_transfer_pinn,
            "fluid_dynamics": self._configure_fluid_dynamics_pinn,
            "structural_mechanics": self._configure_structural_pinn,
            "electromagnetics": self._configure_em_pinn,
            "wave_propagation": self._configure_wave_pinn
        }
        
        self.complexity_estimator = ComplexityEstimator()
        
    def analyze_problem(self, problem_request: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze problem and return PINN configuration"""
        
        domain_type = problem_request["domain_type"]
        geometry = problem_request["geometry"]
        physics_params = problem_request["physics_parameters"]
        accuracy_req = problem_request.get("accuracy_requirements", 0.95)
        
        # Assess problem complexity
        complexity_score = self.complexity_estimator.assess_complexity(
            geometry, physics_params, domain_type
        )
        
        # Determine optimal PINN architecture
        if domain_type not in self.supported_domains:
            raise ValueError(f"Unsupported domain type: {domain_type}")
            
        pinn_config = self.supported_domains[domain_type](
            problem_request, complexity_score
        )
        
        # Estimate computational requirements
        compute_estimate = self._estimate_compute_requirements(
            pinn_config, complexity_score, accuracy_req
        )
        
        # Determine deployment strategy
        deployment_strategy = self._select_deployment_strategy(
            compute_estimate, problem_request.get("real_time_inference", True)
        )
        
        return {
            "pinn_config": pinn_config.__dict__,
            "complexity_score": complexity_score,
            "compute_estimate": compute_estimate,
            "deployment_strategy": deployment_strategy,
            "recommended_resources": self._recommend_resources(compute_estimate),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def _configure_heat_transfer_pinn(self, problem: Dict, complexity: float) -> PINNArchitectureConfig:
        """Configure PINN for heat transfer problems"""
        
        # Base configuration for heat equation
        input_dim = problem["geometry"]["spatial_dims"] + (1 if problem["geometry"].get("time_dependent", True) else 0)
        output_dim = 1  # temperature
        
        # Adjust architecture based on complexity
        if complexity < 0.3:  # Simple problems
            hidden_layers = [50, 50, 50]
            loss_weights = {"pde": 1.0, "bc": 10.0, "ic": 10.0}
            optimizer = "adam"
        elif complexity < 0.7:  # Medium complexity
            hidden_layers = [100, 100, 100, 100]
            loss_weights = {"pde": 1.0, "bc": 50.0, "ic": 50.0}
            optimizer = "adam"
        else:  # Complex problems
            hidden_layers = [200, 200, 200, 200, 200]
            loss_weights = {"pde": 1.0, "bc": 100.0, "ic": 100.0}
            optimizer = "lbfgs"
            
        return PINNArchitectureConfig(
            input_dim=input_dim,
            output_dim=output_dim,
            hidden_layers=hidden_layers,
            activation="tanh",
            layer_sizes=hidden_layers,
            network_type="feedforward",
            initialization="Glorot uniform",
            loss_weights=loss_weights,
            optimizer_config={
                "optimizer": optimizer,
                "learning_rate": 1e-3,
                "decay_rate": 0.9,
                "decay_steps": 1000,
                "max_iter": 50000
            }
        )
    
    def _configure_fluid_dynamics_pinn(self, problem: Dict, complexity: float) -> PINNArchitectureConfig:
        """Configure PINN for fluid dynamics (Navier-Stokes)"""
        
        spatial_dims = problem["geometry"]["spatial_dims"]
        input_dim = spatial_dims + (1 if problem["geometry"].get("time_dependent", True) else 0)
        output_dim = spatial_dims + 1  # velocity components + pressure
        
        # Navier-Stokes requires deeper networks
        if complexity < 0.3:
            hidden_layers = [100, 100, 100, 100]
            loss_weights = {"continuity": 1.0, "momentum": 1.0, "bc": 100.0}
        elif complexity < 0.7:
            hidden_layers = [200, 200, 200, 200, 200]
            loss_weights = {"continuity": 1.0, "momentum": 1.0, "bc": 500.0}
        else:
            hidden_layers = [300, 300, 300, 300, 300, 300]
            loss_weights = {"continuity": 1.0, "momentum": 1.0, "bc": 1000.0}
            
        return PINNArchitectureConfig(
            input_dim=input_dim,
            output_dim=output_dim,
            hidden_layers=hidden_layers,
            activation="tanh",
            layer_sizes=hidden_layers,
            network_type="modified_mfnn",  # Multi-fidelity for complex physics
            initialization="Xavier",
            loss_weights=loss_weights,
            optimizer_config={
                "optimizer": "lbfgs",  # Better for Navier-Stokes
                "learning_rate": 1e-3,
                "max_iter": 100000
            }
        )
    
    def _configure_structural_pinn(self, problem: Dict, complexity: float) -> PINNArchitectureConfig:
        """Configure PINN for structural mechanics problems"""
        
        spatial_dims = problem["geometry"]["spatial_dims"]
        input_dim = spatial_dims
        output_dim = spatial_dims  # displacement components
        
        if complexity < 0.3:
            hidden_layers = [80, 80, 80, 80]
            loss_weights = {"equilibrium": 1.0, "bc": 50.0}
        elif complexity < 0.7:
            hidden_layers = [150, 150, 150, 150, 150]
            loss_weights = {"equilibrium": 1.0, "bc": 100.0}
        else:
            hidden_layers = [250, 250, 250, 250, 250]
            loss_weights = {"equilibrium": 1.0, "bc": 200.0}
            
        return PINNArchitectureConfig(
            input_dim=input_dim,
            output_dim=output_dim,
            hidden_layers=hidden_layers,
            activation="tanh",
            layer_sizes=hidden_layers,
            network_type="feedforward",
            initialization="Glorot uniform",
            loss_weights=loss_weights,
            optimizer_config={
                "optimizer": "adam",
                "learning_rate": 1e-3,
                "decay_rate": 0.95,
                "decay_steps": 2000,
                "max_iter": 75000
            }
        )
    
    def _configure_em_pinn(self, problem: Dict, complexity: float) -> PINNArchitectureConfig:
        """Configure PINN for electromagnetics problems"""
        
        spatial_dims = problem["geometry"]["spatial_dims"]
        input_dim = spatial_dims + (1 if problem["geometry"].get("time_dependent", False) else 0)
        output_dim = spatial_dims * 2  # Electric and magnetic field components
        
        # EM problems are inherently complex
        if complexity < 0.4:
            hidden_layers = [120, 120, 120, 120, 120]
            loss_weights = {"maxwell": 1.0, "bc": 100.0}
        elif complexity < 0.7:
            hidden_layers = [200, 200, 200, 200, 200, 200]
            loss_weights = {"maxwell": 1.0, "bc": 200.0}
        else:
            hidden_layers = [300, 300, 300, 300, 300, 300]
            loss_weights = {"maxwell": 1.0, "bc": 500.0}
            
        return PINNArchitectureConfig(
            input_dim=input_dim,
            output_dim=output_dim,
            hidden_layers=hidden_layers,
            activation="tanh",
            layer_sizes=hidden_layers,
            network_type="resnet",  # ResNet for deep EM networks
            initialization="Xavier",
            loss_weights=loss_weights,
            optimizer_config={
                "optimizer": "adam",
                "learning_rate": 5e-4,
                "decay_rate": 0.9,
                "decay_steps": 1500,
                "max_iter": 100000
            }
        )
    
    def _configure_wave_pinn(self, problem: Dict, complexity: float) -> PINNArchitectureConfig:
        """Configure PINN for wave propagation problems"""
        
        spatial_dims = problem["geometry"]["spatial_dims"]
        input_dim = spatial_dims + 1  # space + time (always time-dependent)
        output_dim = 1  # wave amplitude
        
        if complexity < 0.3:
            hidden_layers = [60, 60, 60, 60]
            loss_weights = {"wave": 1.0, "bc": 20.0, "ic": 20.0}
        elif complexity < 0.7:
            hidden_layers = [120, 120, 120, 120, 120]
            loss_weights = {"wave": 1.0, "bc": 50.0, "ic": 50.0}
        else:
            hidden_layers = [200, 200, 200, 200, 200]
            loss_weights = {"wave": 1.0, "bc": 100.0, "ic": 100.0}
            
        return PINNArchitectureConfig(
            input_dim=input_dim,
            output_dim=output_dim,
            hidden_layers=hidden_layers,
            activation="tanh",
            layer_sizes=hidden_layers,
            network_type="feedforward",
            initialization="Glorot uniform",
            loss_weights=loss_weights,
            optimizer_config={
                "optimizer": "adam",
                "learning_rate": 1e-3,
                "decay_rate": 0.9,
                "decay_steps": 1000,
                "max_iter": 60000
            }
        )
    
    def _estimate_compute_requirements(self, config: PINNArchitectureConfig, 
                                     complexity: float, accuracy: float) -> Dict[str, Any]:
        """Estimate computational requirements for PINN training"""
        
        # Estimate based on network size and problem complexity
        total_params = self._count_parameters(config.hidden_layers, config.input_dim, config.output_dim)
        
        # Training time estimation
        base_epochs = config.optimizer_config.get("max_iter", 50000)
        complexity_multiplier = 1 + complexity * 2
        accuracy_multiplier = 1 + max(0, (accuracy - 0.8) * 5)  # Higher accuracy needs more training
        
        estimated_epochs = int(base_epochs * complexity_multiplier * accuracy_multiplier)
        
        # GPU memory estimation (MB)
        estimated_memory = total_params * 4 * 3  # 4 bytes per param, factor for gradients/optimizer
        estimated_memory = max(estimated_memory, 2048)  # Minimum 2GB
        
        # Training time on different hardware (seconds per epoch)
        time_estimates = {
            "gpu_v100": estimated_epochs * 0.01,
            "gpu_a100": estimated_epochs * 0.005,
            "gpu_t4": estimated_epochs * 0.02,
            "cpu": estimated_epochs * 0.5
        }
        
        return {
            "total_parameters": total_params,
            "estimated_epochs": estimated_epochs,
            "memory_requirement_mb": estimated_memory,
            "training_time_estimates": time_estimates,
            "recommended_hardware": self._select_hardware(estimated_memory, time_estimates["gpu_v100"])
        }
    
    def _count_parameters(self, hidden_layers: List[int], input_dim: int, output_dim: int) -> int:
        """Count total parameters in the network"""
        total_params = 0
        
        # Input to first hidden layer
        total_params += input_dim * hidden_layers[0] + hidden_layers[0]
        
        # Hidden layers
        for i in range(len(hidden_layers) - 1):
            total_params += hidden_layers[i] * hidden_layers[i + 1] + hidden_layers[i + 1]
        
        # Last hidden to output
        total_params += hidden_layers[-1] * output_dim + output_dim
        
        return total_params
    
    def _select_hardware(self, memory_mb: int, training_time_seconds: int) -> str:
        """Select optimal hardware based on requirements"""
        
        if memory_mb > 16384:  # > 16GB
            return "gpu_a100"
        elif memory_mb > 8192:  # > 8GB
            return "gpu_v100"
        elif training_time_seconds > 3600:  # > 1 hour
            return "gpu_v100"
        else:
            return "gpu_t4"
    
    def _select_deployment_strategy(self, compute_estimate: Dict, real_time: bool) -> Dict[str, Any]:
        """Select optimal deployment strategy based on requirements"""
        
        training_time = compute_estimate["training_time_estimates"]["gpu_v100"]
        memory_req = compute_estimate["memory_requirement_mb"]
        
        if training_time > 3600:  # > 1 hour
            training_platform = "aws_batch"  # Long-running jobs
        elif training_time > 900:  # > 15 minutes  
            training_platform = "ecs_fargate"  # Medium jobs
        else:
            training_platform = "lambda_container"  # Short jobs
            
        if real_time and memory_req < 3008:  # Lambda limit
            inference_platform = "lambda"
        elif real_time:
            inference_platform = "sagemaker_endpoint"
        else:
            inference_platform = "batch_inference"
            
        return {
            "training_platform": training_platform,
            "inference_platform": inference_platform,
            "scaling_strategy": "auto" if real_time else "manual",
            "containerization": "required" if memory_req > 3008 else "optional"
        }
    
    def _recommend_resources(self, compute_estimate: Dict) -> Dict[str, Any]:
        """Recommend specific AWS resources"""
        
        hardware = compute_estimate["recommended_hardware"]
        memory_mb = compute_estimate["memory_requirement_mb"]
        
        if hardware == "gpu_a100":
            instance_type = "ml.p4d.xlarge"
            ecs_cpu = 8192
            ecs_memory = 32768
        elif hardware == "gpu_v100":
            instance_type = "ml.p3.2xlarge"
            ecs_cpu = 4096
            ecs_memory = 16384
        else:  # gpu_t4
            instance_type = "ml.g4dn.xlarge"
            ecs_cpu = 2048
            ecs_memory = 8192
        
        return {
            "sagemaker_instance_type": instance_type,
            "ecs_cpu": ecs_cpu,
            "ecs_memory": ecs_memory,
            "lambda_memory": min(memory_mb, 3008),
            "estimated_cost_per_hour": self._estimate_hourly_cost(hardware)
        }
    
    def _estimate_hourly_cost(self, hardware: str) -> float:
        """Estimate hourly cost for different hardware"""
        
        cost_map = {
            "gpu_a100": 4.50,  # Approximate AWS pricing
            "gpu_v100": 3.06,
            "gpu_t4": 0.736,
            "cpu": 0.20
        }
        
        return cost_map.get(hardware, 1.0)

# Lambda handler
def handler(event, context):
    """Lambda handler for PINN problem analysis"""
    
    try:
        # Initialize AWS clients
        dynamodb = boto3.resource('dynamodb')
        sqs = boto3.client('sqs')
        state_table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        # Parse SQS messages
        for record in event['Records']:
            message_body = json.loads(record['body'])
            workflow_id = message_body['workflow_id']
            problem_request = message_body['payload']
            
            print(f"Analyzing PINN problem for workflow {workflow_id}")
            
            # Analyze problem
            analyzer = PINNProblemAnalyzer()
            analysis_result = analyzer.analyze_problem(problem_request)
            
            # Store analysis results in DynamoDB
            state_table.update_item(
                Key={"workflow_id": workflow_id},
                UpdateExpression="SET analysis_result = :analysis, #status = :status, progress = :progress, current_step = :step, updated_at = :updated_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":analysis": analysis_result,
                    ":status": "analysis_complete",
                    ":progress": 25.0,
                    ":step": "preparing_training",
                    ":updated_at": datetime.utcnow().isoformat()
                }
            )
            
            # Trigger training pipeline based on deployment strategy
            training_message = {
                "workflow_id": workflow_id,
                "step": "training",
                "analysis_result": analysis_result,
                "original_request": problem_request,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send to training queue
            sqs.send_message(
                QueueUrl=os.environ['SQS_TRAINING_QUEUE'],
                MessageBody=json.dumps(training_message, default=str),
                MessageAttributes={
                    'workflow_id': {
                        'StringValue': workflow_id,
                        'DataType': 'String'
                    },
                    'deployment_strategy': {
                        'StringValue': analysis_result['deployment_strategy']['training_platform'],
                        'DataType': 'String'
                    }
                }
            )
            
            print(f"Analysis completed for workflow {workflow_id}, sent to training queue")
            
        return {"statusCode": 200, "body": "Analysis completed successfully"}
        
    except Exception as e:
        print(f"Error in PINN analysis: {str(e)}")
        
        # Update workflow status to failed if we have workflow_id
        if 'workflow_id' in locals():
            try:
                state_table.update_item(
                    Key={"workflow_id": workflow_id},
                    UpdateExpression="SET #status = :status, error_message = :error, updated_at = :updated_at",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":status": "failed",
                        ":error": str(e),
                        ":updated_at": datetime.utcnow().isoformat()
                    }
                )
            except:
                pass
        
        return {"statusCode": 500, "body": str(e)}