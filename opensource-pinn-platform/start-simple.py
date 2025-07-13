#!/usr/bin/env python3
"""
Simple PINN Platform Demo Server
Runs without heavy dependencies for quick testing
"""

import json
import uuid
import time
import math
from datetime import datetime
from typing import Dict, Any, Optional

try:
    from fastapi import FastAPI, HTTPException, WebSocket
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    import uvicorn
except ImportError:
    print("Installing FastAPI...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    from fastapi import FastAPI, HTTPException, WebSocket
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
    import uvicorn

# Create FastAPI app
app = FastAPI(
    title="PINN Platform - Demo Server",
    description="Physics-Informed Neural Networks Platform (Demo Mode)",
    version="1.0.0-demo"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
workflows_db = {}
models_db = {}

@app.get("/")
async def root():
    """Root endpoint with platform information"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PINN Platform - Demo</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 40px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1000px; 
                margin: 0 auto; 
                background: white; 
                padding: 40px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
            }
            h1 { 
                color: #2c3e50; 
                border-bottom: 3px solid #3498db; 
                padding-bottom: 15px; 
                margin-bottom: 30px;
                font-size: 2.5em;
            }
            .status { 
                background: linear-gradient(135deg, #e8f5e8, #d4edda); 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0; 
                border-left: 5px solid #28a745;
            }
            .endpoint { 
                background: #f8f9fa; 
                padding: 15px; 
                margin: 15px 0; 
                border-left: 4px solid #007bff; 
                border-radius: 5px;
                font-family: monospace;
            }
            .code { 
                background: #2d3748; 
                color: #e2e8f0; 
                padding: 20px; 
                border-radius: 8px; 
                font-family: 'Courier New', monospace; 
                overflow-x: auto;
                margin: 15px 0;
            }
            a { 
                color: #007bff; 
                text-decoration: none; 
                font-weight: 500;
            }
            a:hover { 
                text-decoration: underline; 
                color: #0056b3;
            }
            .grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 20px 0;
            }
            .card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #dee2e6;
            }
            .badge {
                background: #007bff;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                font-weight: bold;
            }
            .demo-badge {
                background: #ffc107;
                color: #212529;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧮 PINN Platform <span class="badge demo-badge">DEMO</span></h1>
            
            <div class="status">
                <strong>✅ Server Status:</strong> Running in Demo Mode<br>
                <strong>🌐 API Base URL:</strong> <a href="http://localhost:8000">http://localhost:8000</a><br>
                <strong>📚 API Documentation:</strong> <a href="/docs">/docs</a> | <a href="/redoc">/redoc</a><br>
                <strong>⚡ Mode:</strong> Lightweight demo (no heavy ML dependencies)
            </div>
            
            <h2>🚀 What is PINN Platform?</h2>
            <p>The <strong>Physics-Informed Neural Networks (PINN) Platform</strong> is a complete open-source solution for solving complex physics problems using AI. It combines the power of neural networks with physics equations to solve PDEs in engineering and science.</p>
            
            <div class="grid">
                <div class="card">
                    <h3>🔬 Physics Domains</h3>
                    <ul>
                        <li>Heat Transfer</li>
                        <li>Fluid Dynamics</li>
                        <li>Structural Mechanics</li>
                        <li>Electromagnetics</li>
                    </ul>
                </div>
                <div class="card">
                    <h3>🛠️ Technology Stack</h3>
                    <ul>
                        <li>FastAPI + Python</li>
                        <li>PostgreSQL + Redis</li>
                        <li>Docker + Kubernetes</li>
                        <li>DeepXDE + TensorFlow</li>
                    </ul>
                </div>
            </div>
            
            <h3>📡 Available Endpoints</h3>
            <div class="endpoint"><strong>GET /health</strong> - Health check and system status</div>
            <div class="endpoint"><strong>POST /api/v1/pinn/solve</strong> - Submit PINN problem for solving</div>
            <div class="endpoint"><strong>GET /api/v1/pinn/status/{id}</strong> - Get workflow status</div>
            <div class="endpoint"><strong>GET /api/v1/pinn/results/{id}</strong> - Get simulation results</div>
            <div class="endpoint"><strong>GET /api/v1/workflows</strong> - List all workflows</div>
            <div class="endpoint"><strong>GET /api/v1/pinn/domains</strong> - Get supported physics domains</div>
            
            <h3>🧪 Example: Heat Transfer Problem</h3>
            <div class="code">curl -X POST "http://localhost:8000/api/v1/pinn/solve" \\
     -H "Content-Type: application/json" \\
     -d '{
       "name": "2D Heat Conduction",
       "description": "Heat transfer in square domain",
       "domain_type": "heat_transfer",
       "geometry": {
         "type": "rectangle",
         "xmin": 0, "ymin": 0, "xmax": 1, "ymax": 1
       },
       "boundary_conditions": {
         "left": {"type": "dirichlet", "value": 0},
         "right": {"type": "dirichlet", "value": 1}
       },
       "physics_parameters": {
         "thermal_diffusivity": 1.0
       }
     }'</div>
            
            <h3>🔗 Quick Links</h3>
            <div class="grid">
                <div class="card">
                    <h4>📖 Documentation</h4>
                    <a href="/docs">Interactive API Docs (Swagger)</a><br>
                    <a href="/redoc">Alternative Docs (ReDoc)</a>
                </div>
                <div class="card">
                    <h4>🔍 Explore</h4>
                    <a href="/health">Health Check</a><br>
                    <a href="/api/v1/pinn/domains">Physics Domains</a><br>
                    <a href="/api/v1/workflows">Workflows</a>
                </div>
            </div>
            
            <div style="margin-top: 40px; padding: 20px; background: #e9ecef; border-radius: 10px; text-align: center;">
                <h4>🚀 Ready for Production?</h4>
                <p>This is a demo server. For full production deployment with GPU training, monitoring, and all features:</p>
                <div class="code" style="text-align: left;">./start.sh  # Full Docker deployment
./start-dev.sh  # Development with all dependencies</div>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "demo",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "database": "mock (in-memory)",
            "storage": "mock (in-memory)",
            "workers": "mock (simulated)",
            "ml_backend": "demo (no actual training)"
        },
        "features": {
            "pinn_solving": "simulated",
            "real_training": False,
            "gpu_support": False,
            "monitoring": False
        }
    }

@app.get("/demo", response_class=HTMLResponse)
async def realtime_demo():
    """Serve the real-time workflow demo page"""
    try:
        with open("services/frontend/realtime-demo.html", "r") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
            <body>
                <h1>Demo page not found</h1>
                <p>The real-time demo page could not be loaded.</p>
                <p><a href="/docs">Go to API Documentation</a></p>
            </body>
        </html>
        """, status_code=404)

@app.post("/api/v1/pinn/solve")
async def solve_pinn_problem(request: Dict[str, Any]):
    """Submit a PINN problem for solving (demo implementation)"""
    
    workflow_id = str(uuid.uuid4())
    
    # Simulate processing time
    import asyncio
    await asyncio.sleep(0.1)
    
    # Store in mock database
    workflows_db[workflow_id] = {
        "id": workflow_id,
        "name": request.get("name", "Unnamed Problem"),
        "description": request.get("description", ""),
        "domain_type": request.get("domain_type", "heat_transfer"),
        "status": "completed",  # Mock as completed for demo
        "progress": 100.0,
        "accuracy": 0.95 + (hash(workflow_id) % 100) / 1000,  # Mock accuracy
        "training_time": 45.2 + (hash(workflow_id) % 100) / 10,  # Mock training time
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "problem_config": request,
        "results": {
            "solution_type": "mock_solution",
            "convergence": True,
            "final_loss": 0.001 + (hash(workflow_id) % 100) / 100000,
            "epochs_trained": 5000 + (hash(workflow_id) % 1000)
        }
    }
    
    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "estimated_completion_time": 0,
        "message": "Demo: Problem solved instantly (mock result)",
        "endpoints": {
            "status": f"/api/v1/pinn/status/{workflow_id}",
            "results": f"/api/v1/pinn/results/{workflow_id}",
            "inference": f"/api/v1/pinn/inference/{workflow_id}"
        }
    }

@app.get("/api/v1/pinn/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get workflow status"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflows_db[workflow_id]

@app.get("/api/v1/pinn/results/{workflow_id}")
async def get_workflow_results(workflow_id: str):
    """Get workflow results"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = workflows_db[workflow_id]
    
    # Generate mock solution data
    import math
    x_points = [i/10 for i in range(11)]
    y_points = [i/10 for i in range(11)]
    
    # Mock temperature field for heat transfer
    solution_field = []
    for x in x_points:
        row = []
        for y in y_points:
            # Simple mock solution: linear interpolation with some variation
            temp = x + 0.1 * math.sin(math.pi * y) + (hash(f"{x}{y}") % 100) / 1000
            row.append(round(temp, 4))
        solution_field.append(row)
    
    return {
        "workflow_id": workflow_id,
        "status": workflow["status"],
        "results": {
            "solution_field": solution_field,
            "x_coordinates": x_points,
            "y_coordinates": y_points,
            "accuracy": workflow["accuracy"],
            "training_time": workflow["training_time"],
            "convergence_history": [
                0.1, 0.05, 0.02, 0.01, 0.005, 0.002, 0.001
            ],
            "physics_residual": workflow["results"]["final_loss"],
            "boundary_error": workflow["results"]["final_loss"] * 0.1,
            "metadata": {
                "domain_type": workflow["domain_type"],
                "mesh_points": len(x_points) * len(y_points),
                "pde_type": "heat_equation" if workflow["domain_type"] == "heat_transfer" else "generic",
                "solver_method": "PINN (Physics-Informed Neural Network)",
                "demo_note": "This is simulated data for demonstration purposes"
            }
        }
    }

@app.get("/api/v1/workflows")
async def list_workflows():
    """List all workflows"""
    return {
        "workflows": list(workflows_db.values()),
        "total": len(workflows_db),
        "demo_note": "This is a demo server with mock data"
    }

@app.get("/api/v1/pinn/domains")
async def get_supported_domains():
    """Get supported physics domains"""
    return {
        "domains": [
            {
                "id": "heat_transfer",
                "name": "Heat Transfer",
                "description": "Steady-state and transient heat conduction problems",
                "equations": ["Heat equation: ∇²T = 0", "Transient: ∂T/∂t = α∇²T"],
                "boundary_conditions": ["Dirichlet", "Neumann", "Robin"],
                "examples": [
                    "2D heat conduction in square domain",
                    "Transient heat transfer in rod",
                    "Heat exchanger analysis"
                ],
                "typical_accuracy": "95-99%",
                "training_time": "5-30 minutes"
            },
            {
                "id": "fluid_dynamics",
                "name": "Fluid Dynamics",
                "description": "Incompressible Navier-Stokes equations",
                "equations": ["Continuity: ∇·u = 0", "Momentum: ∂u/∂t + u·∇u = -∇p + ν∇²u"],
                "boundary_conditions": ["No-slip", "Slip", "Inlet/Outlet"],
                "examples": [
                    "Lid-driven cavity flow",
                    "Flow around cylinder",
                    "Poiseuille flow"
                ],
                "typical_accuracy": "90-95%",
                "training_time": "15-60 minutes"
            },
            {
                "id": "structural_mechanics",
                "name": "Structural Mechanics",
                "description": "Linear and nonlinear elasticity problems",
                "equations": ["Equilibrium: ∇·σ + f = 0", "Constitutive: σ = C:ε"],
                "boundary_conditions": ["Fixed", "Free", "Applied force"],
                "examples": [
                    "Cantilever beam analysis",
                    "Plate with hole",
                    "Vibration analysis"
                ],
                "typical_accuracy": "92-97%",
                "training_time": "10-45 minutes"
            },
            {
                "id": "electromagnetics",
                "name": "Electromagnetics",
                "description": "Maxwell's equations and electromagnetic fields",
                "equations": ["∇×E = -∂B/∂t", "∇×H = J + ∂D/∂t", "∇·D = ρ", "∇·B = 0"],
                "boundary_conditions": ["Perfect conductor", "Absorbing", "Periodic"],
                "examples": [
                    "Electrostatic field analysis",
                    "Magnetic field distribution",
                    "Wave propagation"
                ],
                "typical_accuracy": "88-94%",
                "training_time": "20-90 minutes"
            }
        ],
        "total_domains": 4,
        "demo_note": "Full implementation available in production version"
    }

@app.post("/api/v1/pinn/inference/{workflow_id}")
async def run_inference(workflow_id: str, inference_data: Dict[str, Any]):
    """Run inference on trained model (demo)"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Mock inference
    input_points = inference_data.get("input_points", [[0.5, 0.5]])
    
    predictions = []
    for point in input_points:
        # Mock prediction based on point coordinates
        if len(point) >= 2:
            x, y = point[0], point[1]
            # For golf ball: pressure field simulation
            r = math.sqrt(x**2 + y**2)
            if r < 0.021:  # Inside ball
                prediction = 1.0
            else:
                # Pressure around golf ball
                theta = math.atan2(y, x)
                if x > 0:  # Wake region
                    prediction = 0.3 + 0.2 * math.exp(-x/0.2) * math.cos(2*theta)
                else:  # Front stagnation
                    prediction = 1.0 - 4 * math.sin(theta)**2 / (r/0.021)**2
        else:
            prediction = 0.5
        predictions.append(round(prediction, 4))
    
    return {
        "workflow_id": workflow_id,
        "predictions": predictions,
        "input_points": input_points,
        "inference_time_ms": 15.2,
        "model_accuracy": workflows_db[workflow_id]["accuracy"],
        "physical_interpretation": "Pressure field values around golf ball",
        "units": "Normalized pressure coefficient",
        "demo_note": "Mock inference result with realistic golf ball pressure field"
    }

@app.get("/api/v1/monitoring/metrics")
async def get_metrics():
    """Get system metrics (demo)"""
    return {
        "system": {
            "active_workflows": len([w for w in workflows_db.values() if w["status"] in ["pending", "training"]]),
            "completed_workflows": len([w for w in workflows_db.values() if w["status"] == "completed"]),
            "total_workflows": len(workflows_db),
            "uptime_seconds": 300,  # Mock uptime
            "cpu_usage": 25.4,
            "memory_usage": 45.2,
            "gpu_usage": 0.0  # No GPU in demo
        },
        "performance": {
            "avg_training_time": 45.2,
            "avg_accuracy": 0.94,
            "success_rate": 1.0,
            "api_requests_per_minute": 12
        },
        "demo_note": "Mock metrics for demonstration"
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws/workflow")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time workflow updates"""
    await websocket.accept()
    connection_id = str(uuid.uuid4())
    
    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe_workflow":
                workflow_id = message.get("workflow_id")
                await websocket.send_text(json.dumps({
                    "type": "subscription_confirmed",
                    "workflow_id": workflow_id,
                    "connection_id": connection_id
                }))
                
                # Start sending mock real-time updates
                if workflow_id in workflows_db:
                    import asyncio
                    asyncio.create_task(send_mock_training_updates(websocket, workflow_id))
            
            elif message.get("type") == "get_status":
                await websocket.send_text(json.dumps({
                    "type": "system_status",
                    "payload": {
                        "active_workflows": len(workflows_db),
                        "server_status": "running",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }))
                
    except Exception as e:
        print(f"WebSocket error: {e}")

async def send_mock_training_updates(websocket: WebSocket, workflow_id: str):
    """Send mock real-time training updates"""
    import asyncio
    
    steps = [
        {"id": "analyze", "name": "Problem Analysis"},
        {"id": "mesh", "name": "Mesh Generation"}, 
        {"id": "train", "name": "PINN Training"},
        {"id": "validate", "name": "Model Validation"},
        {"id": "visualize", "name": "Results Visualization"}
    ]
    
    try:
        for step_index, step in enumerate(steps):
            # Start step
            await websocket.send_text(json.dumps({
                "type": "step_started",
                "payload": {
                    "workflow_id": workflow_id,
                    "step_id": step["id"],
                    "step_name": step["name"],
                    "step_index": step_index
                }
            }))
            
            # Send progress updates
            for progress in range(0, 101, 25):
                # Generate realistic metrics for training step
                if step["id"] == "train":
                    metrics = {
                        "accuracy": min(0.99, 0.5 + (progress / 100) * 0.49),
                        "loss": max(0.001, 0.1 * (1 - progress / 100)),
                        "convergence": progress / 100,
                        "trainingTime": (progress / 100) * 45
                    }
                    
                    await websocket.send_text(json.dumps({
                        "type": "training_metrics",
                        "payload": {
                            "workflow_id": workflow_id,
                            "metrics": metrics,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }))
                
                await websocket.send_text(json.dumps({
                    "type": "workflow_progress",
                    "payload": {
                        "workflow_id": workflow_id,
                        "step_index": step_index,
                        "progress": progress,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }))
                
                await asyncio.sleep(1)  # Simulate real-time updates
            
            # Complete step
            await websocket.send_text(json.dumps({
                "type": "step_completed",
                "payload": {
                    "workflow_id": workflow_id,
                    "step_id": step["id"],
                    "status": "completed",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }))
        
        # Send final visualization
        await websocket.send_text(json.dumps({
            "type": "visualization_ready",
            "payload": {
                "workflow_id": workflow_id,
                "visualization_url": f"/visualizations/{workflow_id}/results.html",
                "results": {"status": "completed", "accuracy": 0.984},
                "timestamp": datetime.utcnow().isoformat()
            }
        }))
    except Exception as e:
        print(f"Error in training updates: {e}")

if __name__ == "__main__":
    print("🚀 Starting PINN Platform Demo Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("⚡ Mode: Demo (lightweight, no ML dependencies)")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    uvicorn.run(
        "start-simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )