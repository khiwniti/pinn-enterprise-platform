import pytest
import json
import requests
from typing import Dict, Any

# Test configuration
API_BASE_URL = "https://your-api-gateway-url.amazonaws.com/prod"  # Update with actual URL

class TestPINNAPI:
    """Test suite for PINN API endpoints"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "timestamp" in data
    
    def test_create_heat_transfer_solution(self):
        """Test creating a heat transfer PINN solution"""
        
        request_data = {
            "problem_description": "2D steady-state heat conduction in a square domain",
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
                "left_wall": {
                    "type": "dirichlet",
                    "value": 100.0
                },
                "right_wall": {
                    "type": "dirichlet", 
                    "value": 0.0
                },
                "top_bottom": {
                    "type": "neumann",
                    "value": 0.0
                }
            },
            "initial_conditions": {},
            "physics_parameters": {
                "thermal_diffusivity": 1.0,
                "source_term": 0.0
            },
            "accuracy_requirements": 0.95,
            "max_training_time": 1800,
            "real_time_inference": True
        }
        
        response = requests.post(
            f"{API_BASE_URL}/pinn/solve",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "workflow_id" in data
        assert data["status"] == "initiated"
        assert "endpoints" in data
        
        return data["workflow_id"]
    
    def test_create_fluid_dynamics_solution(self):
        """Test creating a fluid dynamics PINN solution"""
        
        request_data = {
            "problem_description": "2D lid-driven cavity flow",
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
                "walls": {
                    "type": "dirichlet",
                    "value": [0.0, 0.0]  # No-slip condition
                },
                "lid": {
                    "type": "dirichlet",
                    "value": [1.0, 0.0]  # Moving lid
                }
            },
            "initial_conditions": {},
            "physics_parameters": {
                "reynolds_number": 100,
                "viscosity": 0.01
            },
            "accuracy_requirements": 0.90,
            "max_training_time": 3600,
            "real_time_inference": True
        }
        
        response = requests.post(
            f"{API_BASE_URL}/pinn/solve",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "workflow_id" in data
        assert data["status"] == "initiated"
        
        return data["workflow_id"]
    
    def test_workflow_status(self):
        """Test workflow status endpoint"""
        
        # First create a workflow
        workflow_id = self.test_create_heat_transfer_solution()
        
        # Check status
        response = requests.get(f"{API_BASE_URL}/pinn/status/{workflow_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["workflow_id"] == workflow_id
        assert "status" in data
        assert "progress" in data
        assert "created_at" in data
    
    def test_list_workflows(self):
        """Test listing workflows"""
        
        response = requests.get(f"{API_BASE_URL}/pinn/workflows")
        assert response.status_code == 200
        
        data = response.json()
        assert "workflows" in data
        assert "count" in data
        assert isinstance(data["workflows"], list)
    
    def test_invalid_domain_type(self):
        """Test invalid domain type handling"""
        
        request_data = {
            "problem_description": "Invalid domain test",
            "domain_type": "invalid_domain",
            "geometry": {"type": "rectangle"},
            "boundary_conditions": {},
            "initial_conditions": {},
            "physics_parameters": {}
        }
        
        response = requests.post(
            f"{API_BASE_URL}/pinn/solve",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Should still accept the request but fail during analysis
        assert response.status_code == 200
    
    def test_missing_required_fields(self):
        """Test missing required fields"""
        
        request_data = {
            "problem_description": "Incomplete request test"
            # Missing required fields
        }
        
        response = requests.post(
            f"{API_BASE_URL}/pinn/solve",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error

@pytest.mark.integration
class TestPINNIntegration:
    """Integration tests for complete PINN workflows"""
    
    def test_complete_heat_transfer_workflow(self):
        """Test complete heat transfer workflow from creation to inference"""
        
        # Create workflow
        request_data = {
            "problem_description": "Simple heat transfer test",
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
                "boundary": {
                    "type": "dirichlet",
                    "value": 0.0
                }
            },
            "initial_conditions": {},
            "physics_parameters": {
                "thermal_diffusivity": 1.0
            },
            "accuracy_requirements": 0.85,  # Lower for faster testing
            "max_training_time": 600,  # 10 minutes max
            "real_time_inference": True
        }
        
        # Submit workflow
        response = requests.post(
            f"{API_BASE_URL}/pinn/solve",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        workflow_id = response.json()["workflow_id"]
        
        # Poll for completion (with timeout)
        import time
        max_wait_time = 1800  # 30 minutes
        poll_interval = 30    # 30 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            status_response = requests.get(f"{API_BASE_URL}/pinn/status/{workflow_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            status = status_data["status"]
            
            print(f"Workflow status: {status} (progress: {status_data.get('progress', 0)}%)")
            
            if status == "completed":
                break
            elif status == "failed":
                pytest.fail(f"Workflow failed: {status_data.get('error_message', 'Unknown error')}")
            
            time.sleep(poll_interval)
            elapsed_time += poll_interval
        
        if elapsed_time >= max_wait_time:
            pytest.fail("Workflow did not complete within timeout")
        
        # Test inference
        inference_data = {
            "input_points": [
                [0.5, 0.5],  # Center point
                [0.25, 0.25],
                [0.75, 0.75]
            ]
        }
        
        inference_response = requests.post(
            f"{API_BASE_URL}/pinn/inference/{workflow_id}",
            json=inference_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert inference_response.status_code == 200
        inference_result = inference_response.json()
        assert "status" in inference_result
        assert "request_id" in inference_result

if __name__ == "__main__":
    # Run basic tests
    test_api = TestPINNAPI()
    
    print("Running API tests...")
    try:
        test_api.test_health_check()
        print("✓ Health check test passed")
        
        workflow_id = test_api.test_create_heat_transfer_solution()
        print(f"✓ Heat transfer solution test passed (workflow: {workflow_id})")
        
        test_api.test_workflow_status()
        print("✓ Workflow status test passed")
        
        test_api.test_list_workflows()
        print("✓ List workflows test passed")
        
        print("\nAll API tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        raise