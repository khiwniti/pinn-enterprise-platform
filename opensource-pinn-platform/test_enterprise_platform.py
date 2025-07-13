#!/usr/bin/env python3
"""
Enterprise PINN Platform Test Suite
Comprehensive testing of RAG, 3D visualization, and API capabilities
"""

import asyncio
import json
import requests
import websocket
import time
from typing import Dict, Any
import sys
from pathlib import Path

# Add services to path
sys.path.append(str(Path(__file__).parent / "services"))

from rag.use_case_generator import EngineeringUseCaseRAG
from visualization.three_d_viewport import Professional3DViewport

class EnterprisePlatformTester:
    """Comprehensive test suite for enterprise PINN platform"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v2"
        self.ws_url = base_url.replace("http", "ws")
        
    def test_health_check(self) -> Dict[str, Any]:
        """Test API health check"""
        print("🔍 Testing API Health Check...")
        
        try:
            response = requests.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            health_data = response.json()
            print(f"✅ API Health: {health_data['status']}")
            print(f"   Version: {health_data['version']}")
            print(f"   Services: {list(health_data['services'].keys())}")
            print(f"   Capabilities: {list(health_data['capabilities'].keys())}")
            
            return health_data
            
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return {}
    
    async def test_rag_use_case_generation(self) -> Dict[str, Any]:
        """Test RAG-powered use case generation"""
        print("\n🤖 Testing RAG Use Case Generation...")
        
        try:
            rag_generator = EngineeringUseCaseRAG()
            
            # Test different domains and applications
            test_cases = [
                ("fluid_dynamics", "Golf Ball Aerodynamics", "intermediate"),
                ("heat_transfer", "Electronic Component Cooling", "advanced"),
                ("fluid_dynamics", "Wind Turbine Blade Analysis", "advanced"),
                ("heat_transfer", "Solar Panel Thermal Management", "basic")
            ]
            
            results = {}
            
            for domain, application, complexity in test_cases:
                print(f"   Generating: {application} ({domain}, {complexity})")
                
                use_case = await rag_generator.generate_use_case(
                    domain=domain,
                    application=application,
                    complexity=complexity
                )
                
                results[f"{domain}_{application.replace(' ', '_').lower()}"] = {
                    "id": use_case.id,
                    "name": use_case.name,
                    "description_length": len(use_case.description),
                    "code_length": len(use_case.python_code),
                    "parameters_count": len(use_case.parameters),
                    "insights_count": len(use_case.engineering_insights),
                    "complexity": use_case.complexity_level
                }
                
                print(f"   ✅ Generated: {use_case.name}")
                print(f"      Code: {len(use_case.python_code)} chars")
                print(f"      Insights: {len(use_case.engineering_insights)} items")
            
            print(f"✅ RAG Generation: {len(results)} use cases created")
            return results
            
        except Exception as e:
            print(f"❌ RAG generation failed: {e}")
            return {}
    
    def test_3d_visualization(self) -> Dict[str, Any]:
        """Test 3D visualization generation"""
        print("\n🎨 Testing 3D Visualization Generation...")
        
        try:
            viewport = Professional3DViewport()
            
            # Create sample simulation data
            import numpy as np
            
            x = np.linspace(-5, 5, 30)
            y = np.linspace(-3, 3, 20)
            X, Y = np.meshgrid(x, y)
            
            # Golf ball aerodynamics simulation data
            velocity_field = np.sin(X * 0.3) * np.cos(Y * 0.3)
            pressure_field = np.sin(X * 0.5) * np.cos(Y * 0.5)
            
            simulation_results = {
                "grid": {
                    "x": X.tolist(),
                    "y": Y.tolist(),
                    "z": (velocity_field * 0.5).tolist()
                },
                "fields": {
                    "velocity_magnitude": velocity_field.tolist(),
                    "pressure": pressure_field.tolist()
                },
                "metadata": {
                    "domain": "fluid_dynamics",
                    "application": "golf_ball_aerodynamics",
                    "resolution": [30, 20]
                }
            }
            
            # Generate 3D visualization
            visualization = viewport.create_3d_visualization(
                simulation_results,
                visualization_type="surface",
                color_scheme="viridis",
                interactive_features=["zoom", "rotate", "probe", "slice"]
            )
            
            # Save visualization HTML
            viz_file = "test_3d_visualization.html"
            with open(viz_file, "w") as f:
                f.write(visualization["html_content"])
            
            print(f"✅ 3D Visualization: {visualization['visualization_id']}")
            print(f"   Type: {visualization['type']}")
            print(f"   Features: {visualization['metadata']['interactive_features']}")
            print(f"   Fields: {visualization['metadata']['field_count']}")
            print(f"   Resolution: {visualization['metadata']['grid_resolution']}")
            print(f"   Saved to: {viz_file}")
            
            return {
                "visualization_id": visualization["visualization_id"],
                "type": visualization["type"],
                "features": visualization["metadata"]["interactive_features"],
                "field_count": visualization["metadata"]["field_count"],
                "file_saved": viz_file
            }
            
        except Exception as e:
            print(f"❌ 3D visualization failed: {e}")
            return {}
    
    def test_enterprise_api_simulation(self) -> Dict[str, Any]:
        """Test enterprise API simulation creation"""
        print("\n🚀 Testing Enterprise API Simulation...")
        
        try:
            # Create enterprise simulation request
            simulation_request = {
                "name": "Golf Ball Aerodynamics Analysis",
                "description": "Professional aerodynamic analysis of golf ball with dimple effects",
                "domain_type": "fluid_dynamics",
                "application": "Golf Ball Aerodynamics",
                "complexity_level": "intermediate",
                "geometry": {
                    "type": "sphere",
                    "radius": 0.021,
                    "dimples": True,
                    "dimple_count": 336
                },
                "physics_parameters": {
                    "reynolds_number": 110000,
                    "mach_number": 0.13,
                    "fluid_density": 1.225,
                    "dynamic_viscosity": 1.8e-5,
                    "inlet_velocity": 45.0
                },
                "boundary_conditions": {
                    "inlet": {"type": "velocity_inlet", "velocity": [45.0, 0.0, 0.0]},
                    "outlet": {"type": "pressure_outlet", "pressure": 0.0},
                    "ball_surface": {"type": "no_slip_wall"},
                    "symmetry": {"type": "symmetry_plane"}
                },
                "accuracy_requirements": 0.95,
                "max_training_time": 1800,
                "priority": "high",
                "tags": ["aerodynamics", "sports", "golf", "cfd"],
                "metadata": {
                    "client": "test_suite",
                    "purpose": "demonstration"
                }
            }
            
            # Submit simulation
            response = requests.post(
                f"{self.api_url}/simulations",
                json=simulation_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            simulation_data = response.json()
            workflow_id = simulation_data["workflow_id"]
            
            print(f"✅ Simulation Created: {workflow_id}")
            print(f"   Status: {simulation_data['status']}")
            print(f"   Estimated time: {simulation_data['estimated_completion_time']}s")
            print(f"   Use case generated: {simulation_data['use_case_generated']}")
            print(f"   Python code available: {simulation_data['python_code_available']}")
            
            # Wait a moment for processing to start
            time.sleep(2)
            
            # Check status
            status_response = requests.get(f"{self.api_url}/simulations/{workflow_id}/status")
            status_response.raise_for_status()
            status_data = status_response.json()
            
            print(f"   Current status: {status_data['status']}")
            print(f"   Progress: {status_data['progress']}%")
            print(f"   Current step: {status_data['current_step']}")
            
            # Get use case
            use_case_response = requests.get(f"{self.api_url}/simulations/{workflow_id}/use-case")
            use_case_response.raise_for_status()
            use_case_data = use_case_response.json()
            
            print(f"   Use case: {use_case_data['name']}")
            print(f"   Code length: {len(use_case_data['python_code'])} chars")
            print(f"   Insights: {len(use_case_data['engineering_insights'])} items")
            
            # Get Python code
            code_response = requests.get(f"{self.api_url}/simulations/{workflow_id}/code")
            code_response.raise_for_status()
            code_data = code_response.json()
            
            # Save Python code
            code_file = f"generated_simulation_{workflow_id[:8]}.py"
            with open(code_file, "w") as f:
                f.write(code_data["python_code"])
            
            print(f"   Python code saved to: {code_file}")
            
            return {
                "workflow_id": workflow_id,
                "status": simulation_data["status"],
                "use_case_generated": simulation_data["use_case_generated"],
                "code_file": code_file,
                "endpoints": simulation_data["endpoints"]
            }
            
        except Exception as e:
            print(f"❌ Enterprise API simulation failed: {e}")
            return {}
    
    def test_websocket_connection(self, workflow_id: str) -> Dict[str, Any]:
        """Test WebSocket real-time updates"""
        print(f"\n🔌 Testing WebSocket Connection for {workflow_id[:8]}...")
        
        try:
            messages_received = []
            connection_established = False
            
            def on_message(ws, message):
                nonlocal messages_received, connection_established
                data = json.loads(message)
                messages_received.append(data)
                
                if data.get("type") == "connection_established":
                    connection_established = True
                    print(f"   ✅ WebSocket connected: {data.get('connection_id', 'unknown')[:8]}")
                elif data.get("type") == "workflow_progress":
                    payload = data.get("payload", {})
                    print(f"   📊 Progress: {payload.get('progress', 0)}% - {payload.get('step', 'unknown')}")
                elif data.get("type") == "training_metrics":
                    metrics = data.get("payload", {}).get("metrics", {})
                    print(f"   📈 Metrics: Accuracy {metrics.get('accuracy', 0):.3f}, Loss {metrics.get('loss', 0):.6f}")
                elif data.get("type") == "visualization_ready":
                    print(f"   🎨 Visualization ready!")
            
            def on_error(ws, error):
                print(f"   ❌ WebSocket error: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                print(f"   🔌 WebSocket closed")
            
            # Connect to WebSocket
            ws_url = f"{self.ws_url}/ws/simulation/{workflow_id}"
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            
            # Run WebSocket in background for a short time
            import threading
            
            def run_websocket():
                ws.run_forever()
            
            ws_thread = threading.Thread(target=run_websocket)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection and some messages
            time.sleep(10)
            ws.close()
            
            print(f"✅ WebSocket Test: {len(messages_received)} messages received")
            
            return {
                "connection_established": connection_established,
                "messages_received": len(messages_received),
                "message_types": list(set(msg.get("type") for msg in messages_received))
            }
            
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return {}
    
    def test_list_simulations(self) -> Dict[str, Any]:
        """Test simulation listing API"""
        print("\n📋 Testing Simulation Listing...")
        
        try:
            # List all simulations
            response = requests.get(f"{self.api_url}/simulations")
            response.raise_for_status()
            
            data = response.json()
            
            print(f"✅ Simulations Listed: {data['total']} total")
            print(f"   Current page: {len(data['simulations'])} items")
            print(f"   Has more: {data['has_more']}")
            
            # List by domain
            response = requests.get(f"{self.api_url}/simulations?domain=fluid_dynamics")
            response.raise_for_status()
            
            fluid_data = response.json()
            print(f"   Fluid dynamics: {fluid_data['total']} simulations")
            
            return {
                "total_simulations": data["total"],
                "current_page_count": len(data["simulations"]),
                "fluid_dynamics_count": fluid_data["total"]
            }
            
        except Exception as e:
            print(f"❌ Simulation listing failed: {e}")
            return {}
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("🧮 PINN Enterprise Platform - Comprehensive Test Suite")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Health Check
        results["health_check"] = self.test_health_check()
        
        # Test 2: RAG Use Case Generation
        results["rag_generation"] = await self.test_rag_use_case_generation()
        
        # Test 3: 3D Visualization
        results["3d_visualization"] = self.test_3d_visualization()
        
        # Test 4: Enterprise API
        results["enterprise_api"] = self.test_enterprise_api_simulation()
        
        # Test 5: WebSocket (if simulation was created)
        if results["enterprise_api"].get("workflow_id"):
            results["websocket"] = self.test_websocket_connection(
                results["enterprise_api"]["workflow_id"]
            )
        
        # Test 6: List Simulations
        results["list_simulations"] = self.test_list_simulations()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
        
        if results.get("enterprise_api", {}).get("code_file"):
            print(f"\n📄 Generated Files:")
            print(f"  - Python Code: {results['enterprise_api']['code_file']}")
        
        if results.get("3d_visualization", {}).get("file_saved"):
            print(f"  - 3D Visualization: {results['3d_visualization']['file_saved']}")
        
        print("\n🚀 Enterprise Platform Test Complete!")
        
        return results

async def main():
    """Main test execution"""
    
    # Check if server is running
    tester = EnterprisePlatformTester()
    
    try:
        requests.get(tester.base_url, timeout=5)
    except:
        print("❌ Server not running. Please start the enterprise API server first:")
        print("   cd /workspace/opensource-pinn-platform/services/api")
        print("   python enterprise_api.py")
        return
    
    # Run comprehensive tests
    results = await tester.run_comprehensive_test()
    
    # Save results
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Test results saved to: test_results.json")

if __name__ == "__main__":
    asyncio.run(main())