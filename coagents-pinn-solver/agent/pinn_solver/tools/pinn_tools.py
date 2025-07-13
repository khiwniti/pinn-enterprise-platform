"""Tools for PINN problem solving"""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from pinn_solver.core.pinn_client import PINNClient, PINNProblemBuilder

class SolvePINNProblemInput(BaseModel):
    """Input for solving a PINN problem"""
    problem_description: str = Field(description="Natural language description of the physics problem")
    domain_type: str = Field(description="Type of physics domain: heat_transfer, fluid_dynamics, structural_mechanics, electromagnetics")
    accuracy_requirements: float = Field(default=0.95, description="Required accuracy (0.0-1.0)")
    max_training_time: int = Field(default=1800, description="Maximum training time in seconds")

class SolvePINNProblemTool(BaseTool):
    """Tool for solving physics problems using PINNs"""
    
    name = "solve_pinn_problem"
    description = "Solve a physics problem using Physics-Informed Neural Networks. Supports heat transfer, fluid dynamics, structural mechanics, and electromagnetics problems."
    args_schema = SolvePINNProblemInput
    
    def __init__(self):
        super().__init__()
        self.client = PINNClient()
        self.problem_builder = PINNProblemBuilder()
    
    def _run(self, problem_description: str, domain_type: str, 
            accuracy_requirements: float = 0.95, max_training_time: int = 1800) -> str:
        """Execute the PINN problem solving"""
        
        try:
            # Parse the problem description
            if domain_type == "heat_transfer":
                problem_config = self.problem_builder.parse_heat_transfer_problem(problem_description)
            elif domain_type == "fluid_dynamics":
                problem_config = self.problem_builder.parse_fluid_dynamics_problem(problem_description)
            elif domain_type == "structural_mechanics":
                problem_config = self.problem_builder.parse_structural_problem(problem_description)
            else:
                return f"Error: Unsupported domain type '{domain_type}'. Supported types: heat_transfer, fluid_dynamics, structural_mechanics"
            
            # Submit the problem
            result = self.client.solve_physics_problem(
                problem_description=problem_description,
                domain_type=problem_config["domain_type"],
                geometry=problem_config["geometry"],
                boundary_conditions=problem_config["boundary_conditions"],
                physics_parameters=problem_config["physics_parameters"],
                accuracy_requirements=accuracy_requirements,
                max_training_time=max_training_time
            )
            
            workflow_id = result["workflow_id"]
            
            return json.dumps({
                "status": "submitted",
                "workflow_id": workflow_id,
                "message": f"PINN problem submitted successfully. Workflow ID: {workflow_id}",
                "estimated_completion_time": result.get("estimated_completion_time", 1800),
                "endpoints": result.get("endpoints", {})
            })
            
        except Exception as e:
            return f"Error solving PINN problem: {str(e)}"

class CheckWorkflowStatusInput(BaseModel):
    """Input for checking workflow status"""
    workflow_id: str = Field(description="The workflow ID to check")

class CheckWorkflowStatusTool(BaseTool):
    """Tool for checking the status of a PINN workflow"""
    
    name = "check_workflow_status"
    description = "Check the status and progress of a PINN training workflow"
    args_schema = CheckWorkflowStatusInput
    
    def __init__(self):
        super().__init__()
        self.client = PINNClient()
    
    def _run(self, workflow_id: str) -> str:
        """Check the workflow status"""
        
        try:
            status = self.client.get_workflow_status(workflow_id)
            
            return json.dumps({
                "workflow_id": workflow_id,
                "status": status["status"],
                "progress": status.get("progress", 0),
                "current_step": status.get("current_step", "unknown"),
                "created_at": status.get("created_at", ""),
                "updated_at": status.get("updated_at", ""),
                "error_message": status.get("error_message")
            })
            
        except Exception as e:
            return f"Error checking workflow status: {str(e)}"

class GetPINNResultsInput(BaseModel):
    """Input for getting PINN results"""
    workflow_id: str = Field(description="The workflow ID to get results for")

class GetPINNResultsTool(BaseTool):
    """Tool for retrieving PINN simulation results"""
    
    name = "get_pinn_results"
    description = "Retrieve the results of a completed PINN simulation"
    args_schema = GetPINNResultsInput
    
    def __init__(self):
        super().__init__()
        self.client = PINNClient()
    
    def _run(self, workflow_id: str) -> str:
        """Get the simulation results"""
        
        try:
            results = self.client.get_results(workflow_id)
            
            return json.dumps({
                "workflow_id": workflow_id,
                "results": results,
                "message": "Results retrieved successfully"
            })
            
        except Exception as e:
            return f"Error getting results: {str(e)}"

class RunPINNInferenceInput(BaseModel):
    """Input for running PINN inference"""
    workflow_id: str = Field(description="The workflow ID of the trained model")
    input_points: List[List[float]] = Field(description="List of input points for inference")

class RunPINNInferenceTool(BaseTool):
    """Tool for running inference on a trained PINN model"""
    
    name = "run_pinn_inference"
    description = "Run inference on a trained PINN model at specified points"
    args_schema = RunPINNInferenceInput
    
    def __init__(self):
        super().__init__()
        self.client = PINNClient()
    
    def _run(self, workflow_id: str, input_points: List[List[float]]) -> str:
        """Run inference on the trained model"""
        
        try:
            result = self.client.run_inference(workflow_id, input_points)
            
            return json.dumps({
                "workflow_id": workflow_id,
                "inference_result": result,
                "num_points": len(input_points),
                "message": "Inference completed successfully"
            })
            
        except Exception as e:
            return f"Error running inference: {str(e)}"

class VisualizePINNResultsInput(BaseModel):
    """Input for visualizing PINN results"""
    workflow_id: str = Field(description="The workflow ID to visualize")
    visualization_type: str = Field(default="contour", description="Type of visualization: contour, surface, line, vector")
    resolution: int = Field(default=50, description="Resolution for visualization grid")

class VisualizePINNResultsTool(BaseTool):
    """Tool for creating visualizations of PINN results"""
    
    name = "visualize_pinn_results"
    description = "Create visualizations of PINN simulation results"
    args_schema = VisualizePINNResultsInput
    
    def __init__(self):
        super().__init__()
        self.client = PINNClient()
    
    def _run(self, workflow_id: str, visualization_type: str = "contour", resolution: int = 50) -> str:
        """Create visualization of results"""
        
        try:
            # Get workflow status to determine problem type
            status = self.client.get_workflow_status(workflow_id)
            
            if status["status"] != "completed":
                return f"Cannot visualize: Workflow {workflow_id} is not completed (status: {status['status']})"
            
            # Generate test points for visualization
            x = np.linspace(0, 1, resolution)
            y = np.linspace(0, 1, resolution)
            X, Y = np.meshgrid(x, y)
            test_points = np.column_stack([X.ravel(), Y.ravel()]).tolist()
            
            # Run inference
            inference_result = self.client.run_inference(workflow_id, test_points)
            
            # Create mock visualization (in real implementation, would use actual results)
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Mock data for demonstration
            Z = np.sin(np.pi * X) * np.sin(np.pi * Y)
            
            if visualization_type == "contour":
                contour = ax.contourf(X, Y, Z, levels=20, cmap='viridis')
                plt.colorbar(contour, ax=ax)
                ax.set_title(f'PINN Solution - Workflow {workflow_id}')
            elif visualization_type == "surface":
                from mpl_toolkits.mplot3d import Axes3D
                fig = plt.figure(figsize=(12, 9))
                ax = fig.add_subplot(111, projection='3d')
                surf = ax.plot_surface(X, Y, Z, cmap='viridis')
                plt.colorbar(surf)
                ax.set_title(f'PINN Solution 3D - Workflow {workflow_id}')
            
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            
            # Save plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return json.dumps({
                "workflow_id": workflow_id,
                "visualization_type": visualization_type,
                "plot_data": plot_data,
                "message": f"Visualization created successfully ({visualization_type})"
            })
            
        except Exception as e:
            return f"Error creating visualization: {str(e)}"

class ListPINNWorkflowsInput(BaseModel):
    """Input for listing PINN workflows"""
    limit: int = Field(default=10, description="Maximum number of workflows to return")
    status_filter: Optional[str] = Field(default=None, description="Filter by status: completed, failed, in_progress")

class ListPINNWorkflowsTool(BaseTool):
    """Tool for listing PINN workflows"""
    
    name = "list_pinn_workflows"
    description = "List recent PINN workflows and their status"
    args_schema = ListPINNWorkflowsInput
    
    def __init__(self):
        super().__init__()
        self.client = PINNClient()
    
    def _run(self, limit: int = 10, status_filter: Optional[str] = None) -> str:
        """List workflows"""
        
        try:
            workflows = self.client.list_workflows(limit=limit, status=status_filter)
            
            return json.dumps({
                "workflows": workflows["workflows"],
                "count": workflows["count"],
                "message": f"Retrieved {workflows['count']} workflows"
            })
            
        except Exception as e:
            return f"Error listing workflows: {str(e)}"

# Export all tools
PINN_TOOLS = [
    SolvePINNProblemTool(),
    CheckWorkflowStatusTool(),
    GetPINNResultsTool(),
    RunPINNInferenceTool(),
    VisualizePINNResultsTool(),
    ListPINNWorkflowsTool()
]