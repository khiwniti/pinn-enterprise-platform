"""Client for interacting with the serverless PINN backend"""

import os
import requests
import time
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

class PINNClient:
    """Client for the serverless PINN platform"""
    
    def __init__(self, api_endpoint: Optional[str] = None):
        self.api_endpoint = api_endpoint or os.getenv("PINN_API_ENDPOINT")
        if not self.api_endpoint:
            raise ValueError("PINN_API_ENDPOINT must be set in environment variables")
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "PINN-CopilotKit-Agent/1.0"
        })
    
    def solve_physics_problem(self, problem_description: str, domain_type: str, 
                            geometry: Dict[str, Any], boundary_conditions: Dict[str, Any],
                            physics_parameters: Dict[str, Any], 
                            accuracy_requirements: float = 0.95,
                            max_training_time: int = 1800) -> Dict[str, Any]:
        """Submit a physics problem for PINN solution"""
        
        request_data = {
            "problem_description": problem_description,
            "domain_type": domain_type,
            "geometry": geometry,
            "boundary_conditions": boundary_conditions,
            "initial_conditions": {},
            "physics_parameters": physics_parameters,
            "accuracy_requirements": accuracy_requirements,
            "max_training_time": max_training_time,
            "real_time_inference": True
        }
        
        try:
            response = self.session.post(
                f"{self.api_endpoint}/pinn/solve",
                json=request_data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to submit PINN problem: {str(e)}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a PINN workflow"""
        
        try:
            response = self.session.get(
                f"{self.api_endpoint}/pinn/status/{workflow_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get workflow status: {str(e)}")
    
    def wait_for_completion(self, workflow_id: str, max_wait_time: int = 3600,
                          poll_interval: int = 30) -> Dict[str, Any]:
        """Wait for a workflow to complete and return the final status"""
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.get_workflow_status(workflow_id)
            
            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                error_msg = status.get("error_message", "Unknown error")
                raise Exception(f"Workflow failed: {error_msg}")
            
            time.sleep(poll_interval)
        
        raise Exception(f"Workflow {workflow_id} did not complete within {max_wait_time} seconds")
    
    def get_results(self, workflow_id: str) -> Dict[str, Any]:
        """Get the results of a completed workflow"""
        
        try:
            response = self.session.get(
                f"{self.api_endpoint}/pinn/results/{workflow_id}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get results: {str(e)}")
    
    def run_inference(self, workflow_id: str, input_points: List[List[float]]) -> Dict[str, Any]:
        """Run inference on a trained model"""
        
        inference_data = {
            "input_points": input_points
        }
        
        try:
            response = self.session.post(
                f"{self.api_endpoint}/pinn/inference/{workflow_id}",
                json=inference_data,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to run inference: {str(e)}")
    
    def list_workflows(self, limit: int = 10, status: Optional[str] = None) -> Dict[str, Any]:
        """List recent workflows"""
        
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        try:
            response = self.session.get(
                f"{self.api_endpoint}/pinn/workflows",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list workflows: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the PINN platform"""
        
        try:
            response = self.session.get(
                f"{self.api_endpoint}/health",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Health check failed: {str(e)}")

class PINNProblemBuilder:
    """Helper class to build PINN problems from natural language descriptions"""
    
    @staticmethod
    def parse_heat_transfer_problem(description: str) -> Dict[str, Any]:
        """Parse a heat transfer problem description"""
        
        # Default heat transfer problem setup
        problem = {
            "domain_type": "heat_transfer",
            "geometry": {
                "type": "rectangle",
                "xmin": 0.0,
                "ymin": 0.0,
                "xmax": 1.0,
                "ymax": 1.0,
                "spatial_dims": 2,
                "time_dependent": False
            },
            "boundary_conditions": {
                "left_wall": {"type": "dirichlet", "value": 100.0},
                "right_wall": {"type": "dirichlet", "value": 0.0},
                "top_wall": {"type": "neumann", "value": 0.0},
                "bottom_wall": {"type": "neumann", "value": 0.0}
            },
            "physics_parameters": {
                "thermal_diffusivity": 1.0,
                "thermal_conductivity": 1.0,
                "source_term": 0.0
            }
        }
        
        # Parse description for specific parameters
        description_lower = description.lower()
        
        # Check for temperature values
        if "100" in description and "degree" in description_lower:
            problem["boundary_conditions"]["left_wall"]["value"] = 100.0
        if "0" in description and "degree" in description_lower:
            problem["boundary_conditions"]["right_wall"]["value"] = 0.0
        
        # Check for insulated walls
        if "insulated" in description_lower:
            problem["boundary_conditions"]["top_wall"]["type"] = "neumann"
            problem["boundary_conditions"]["bottom_wall"]["type"] = "neumann"
        
        # Check for time dependency
        if "transient" in description_lower or "time" in description_lower:
            problem["geometry"]["time_dependent"] = True
            problem["geometry"]["time_end"] = 1.0
        
        return problem
    
    @staticmethod
    def parse_fluid_dynamics_problem(description: str) -> Dict[str, Any]:
        """Parse a fluid dynamics problem description"""
        
        problem = {
            "domain_type": "fluid_dynamics",
            "geometry": {
                "type": "rectangle",
                "xmin": 0.0,
                "ymin": 0.0,
                "xmax": 1.0,
                "ymax": 1.0,
                "spatial_dims": 2,
                "time_dependent": False
            },
            "boundary_conditions": {
                "walls": {"type": "dirichlet", "value": [0.0, 0.0]},
                "lid": {"type": "dirichlet", "value": [1.0, 0.0]}
            },
            "physics_parameters": {
                "reynolds_number": 100,
                "viscosity": 0.01,
                "density": 1.0
            }
        }
        
        description_lower = description.lower()
        
        # Parse Reynolds number
        if "reynolds" in description_lower:
            import re
            re_match = re.search(r"reynolds.*?(\d+)", description_lower)
            if re_match:
                problem["physics_parameters"]["reynolds_number"] = int(re_match.group(1))
        
        # Check for lid-driven cavity
        if "lid" in description_lower and "driven" in description_lower:
            problem["boundary_conditions"]["lid"]["value"] = [1.0, 0.0]
        
        return problem
    
    @staticmethod
    def parse_structural_problem(description: str) -> Dict[str, Any]:
        """Parse a structural mechanics problem description"""
        
        problem = {
            "domain_type": "structural_mechanics",
            "geometry": {
                "type": "rectangle",
                "xmin": 0.0,
                "ymin": 0.0,
                "xmax": 1.0,
                "ymax": 0.1,
                "spatial_dims": 2,
                "time_dependent": False
            },
            "boundary_conditions": {
                "fixed_end": {"type": "dirichlet", "value": [0.0, 0.0]},
                "free_end": {"type": "neumann", "value": [0.0, -1000.0]}
            },
            "physics_parameters": {
                "youngs_modulus": 200e9,
                "poissons_ratio": 0.3,
                "density": 7850.0
            }
        }
        
        description_lower = description.lower()
        
        # Check for cantilever beam
        if "cantilever" in description_lower:
            problem["boundary_conditions"]["fixed_end"]["value"] = [0.0, 0.0]
        
        # Check for point load
        if "point load" in description_lower or "force" in description_lower:
            import re
            force_match = re.search(r"(\d+)\s*n", description_lower)
            if force_match:
                force_value = float(force_match.group(1))
                problem["boundary_conditions"]["free_end"]["value"] = [0.0, -force_value]
        
        return problem