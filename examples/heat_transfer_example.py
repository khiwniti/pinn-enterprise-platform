#!/usr/bin/env python3
"""
Example: 2D Heat Transfer Problem using PINN Platform

This example demonstrates how to solve a 2D steady-state heat conduction problem
using the PINN DeepXDE platform.

Problem: Heat conduction in a square domain with Dirichlet boundary conditions
- Left wall: T = 100°C
- Right wall: T = 0°C  
- Top and bottom walls: Insulated (∂T/∂n = 0)

PDE: ∇²T = 0 (Laplace equation)
"""

import requests
import json
import time
import numpy as np
import matplotlib.pyplot as plt

# Configuration
API_BASE_URL = "https://your-api-gateway-url.amazonaws.com/prod"  # Update with actual URL

def solve_heat_transfer_problem():
    """Solve 2D heat transfer problem using PINN platform"""
    
    print("🔥 Solving 2D Heat Transfer Problem with PINN")
    print("=" * 50)
    
    # Define the problem
    problem_request = {
        "problem_description": "2D steady-state heat conduction in a square domain with temperature boundary conditions",
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
                "value": 100.0,
                "description": "Hot wall at x=0"
            },
            "right_wall": {
                "type": "dirichlet",
                "value": 0.0,
                "description": "Cold wall at x=1"
            },
            "top_wall": {
                "type": "neumann",
                "value": 0.0,
                "description": "Insulated wall at y=1"
            },
            "bottom_wall": {
                "type": "neumann", 
                "value": 0.0,
                "description": "Insulated wall at y=0"
            }
        },
        "initial_conditions": {},
        "physics_parameters": {
            "thermal_diffusivity": 1.0,
            "thermal_conductivity": 1.0,
            "source_term": 0.0
        },
        "accuracy_requirements": 0.95,
        "max_training_time": 1800,  # 30 minutes
        "real_time_inference": True
    }
    
    # Submit the problem
    print("📤 Submitting problem to PINN platform...")
    response = requests.post(
        f"{API_BASE_URL}/pinn/solve",
        json=problem_request,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ Error submitting problem: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    workflow_id = result["workflow_id"]
    
    print(f"✅ Problem submitted successfully!")
    print(f"   Workflow ID: {workflow_id}")
    print(f"   Estimated completion time: {result['estimated_completion_time']} seconds")
    print(f"   Status endpoint: {result['endpoints']['status']}")
    
    # Monitor progress
    print("\n📊 Monitoring training progress...")
    return monitor_workflow_progress(workflow_id)

def monitor_workflow_progress(workflow_id: str):
    """Monitor workflow progress until completion"""
    
    start_time = time.time()
    last_status = None
    
    while True:
        # Get current status
        response = requests.get(f"{API_BASE_URL}/pinn/status/{workflow_id}")
        
        if response.status_code != 200:
            print(f"❌ Error getting status: {response.status_code}")
            break
        
        status_data = response.json()
        current_status = status_data["status"]
        progress = status_data.get("progress", 0)
        current_step = status_data.get("current_step", "unknown")
        
        # Print status update if changed
        if current_status != last_status:
            elapsed = time.time() - start_time
            print(f"   [{elapsed:6.1f}s] Status: {current_status} ({progress:.1f}%) - {current_step}")
            last_status = current_status
        
        # Check if completed
        if current_status == "completed":
            print(f"🎉 Training completed successfully!")
            return workflow_id
        elif current_status == "failed":
            error_msg = status_data.get("error_message", "Unknown error")
            print(f"❌ Training failed: {error_msg}")
            return None
        
        # Wait before next check
        time.sleep(10)

def test_inference(workflow_id: str):
    """Test inference with the trained model"""
    
    print(f"\n🔮 Testing inference with workflow {workflow_id}")
    print("=" * 50)
    
    # Create test points
    x = np.linspace(0, 1, 11)
    y = np.linspace(0, 1, 11)
    X, Y = np.meshgrid(x, y)
    test_points = np.column_stack([X.ravel(), Y.ravel()])
    
    print(f"📍 Testing {len(test_points)} points...")
    
    # Submit inference request
    inference_request = {
        "input_points": test_points.tolist()
    }
    
    response = requests.post(
        f"{API_BASE_URL}/pinn/inference/{workflow_id}",
        json=inference_request,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code != 200:
        print(f"❌ Inference request failed: {response.status_code}")
        print(response.text)
        return None
    
    result = response.json()
    request_id = result["request_id"]
    
    print(f"✅ Inference request submitted!")
    print(f"   Request ID: {request_id}")
    print(f"   Estimated time: {result['estimated_time']}")
    
    # Wait for inference results (in a real implementation, you'd poll for results)
    print("⏳ Waiting for inference results...")
    time.sleep(30)  # Wait for processing
    
    # For demonstration, create mock results
    # In reality, you'd retrieve actual results from the platform
    mock_predictions = create_mock_heat_transfer_solution(test_points)
    
    # Visualize results
    visualize_heat_transfer_results(test_points, mock_predictions)
    
    return mock_predictions

def create_mock_heat_transfer_solution(points: np.ndarray) -> np.ndarray:
    """Create mock analytical solution for visualization"""
    
    # Analytical solution for the given boundary conditions
    # T(x,y) = 100 * (1 - x) for the simplified case
    x = points[:, 0]
    y = points[:, 1]
    
    # Linear temperature distribution from hot to cold wall
    temperature = 100 * (1 - x)
    
    return temperature

def visualize_heat_transfer_results(points: np.ndarray, temperatures: np.ndarray):
    """Visualize heat transfer results"""
    
    print("\n📈 Visualizing results...")
    
    # Reshape for plotting
    x = points[:, 0]
    y = points[:, 1]
    
    # Create grid for contour plot
    xi = np.linspace(0, 1, 11)
    yi = np.linspace(0, 1, 11)
    Xi, Yi = np.meshgrid(xi, yi)
    Ti = temperatures.reshape(Xi.shape)
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # Contour plot
    contour = ax1.contourf(Xi, Yi, Ti, levels=20, cmap='hot')
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_title('Temperature Distribution')
    ax1.set_aspect('equal')
    plt.colorbar(contour, ax=ax1, label='Temperature (°C)')
    
    # Line plot along centerline
    centerline_idx = len(yi) // 2
    ax2.plot(xi, Ti[centerline_idx, :], 'b-', linewidth=2, label='PINN Solution')
    ax2.set_xlabel('X')
    ax2.set_ylabel('Temperature (°C)')
    ax2.set_title('Temperature along Centerline (y=0.5)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    plt.savefig('heat_transfer_results.png', dpi=300, bbox_inches='tight')
    print("💾 Results saved to 'heat_transfer_results.png'")
    
    # Print some statistics
    print(f"\n📊 Solution Statistics:")
    print(f"   Max temperature: {temperatures.max():.2f}°C")
    print(f"   Min temperature: {temperatures.min():.2f}°C")
    print(f"   Mean temperature: {temperatures.mean():.2f}°C")
    print(f"   Temperature range: {temperatures.max() - temperatures.min():.2f}°C")

def main():
    """Main execution function"""
    
    print("🚀 PINN Platform Heat Transfer Example")
    print("=" * 60)
    
    try:
        # Test API connectivity
        print("🔗 Testing API connectivity...")
        health_response = requests.get(f"{API_BASE_URL}/health")
        
        if health_response.status_code != 200:
            print(f"❌ API not accessible: {health_response.status_code}")
            print("Please check the API_BASE_URL and ensure the platform is deployed")
            return
        
        print("✅ API is accessible")
        
        # Solve the heat transfer problem
        workflow_id = solve_heat_transfer_problem()
        
        if workflow_id:
            # Test inference
            predictions = test_inference(workflow_id)
            
            if predictions is not None:
                print("\n🎯 Example completed successfully!")
                print(f"   Workflow ID: {workflow_id}")
                print(f"   Solution points: {len(predictions)}")
                print("   Check 'heat_transfer_results.png' for visualization")
            else:
                print("❌ Inference failed")
        else:
            print("❌ Problem solving failed")
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Please check:")
        print("   1. API_BASE_URL is correct")
        print("   2. Platform is deployed and running")
        print("   3. Network connectivity")
    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()