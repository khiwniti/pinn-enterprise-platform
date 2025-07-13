#!/usr/bin/env python3
"""
PINN Enterprise Platform - Server Startup
"""

import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import random
import math

# Create FastAPI app
app = FastAPI(
    title="PINN Enterprise Platform",
    description="Production-ready Physics-Informed Neural Networks with RAG and 3D Visualization",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
workflows_db = {}
results_db = {}

@app.get("/")
async def root():
    """Root endpoint with platform information"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PINN Enterprise Platform</title>
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            min-height: 100vh;
        }
        .container { max-width: 1200px; margin: 0 auto; text-align: center; }
        .header { margin-bottom: 40px; }
        .btn { 
            background: rgba(255,255,255,0.2); 
            color: white; 
            padding: 12px 24px; 
            border: none; 
            border-radius: 8px; 
            text-decoration: none; 
            display: inline-block; 
            margin: 8px; 
            transition: all 0.3s; 
            font-weight: 600;
        }
        .btn:hover { 
            background: rgba(255,255,255,0.3); 
            transform: translateY(-2px); 
        }
        .status { 
            background: rgba(0,255,0,0.2); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 4px solid #00ff00;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧮 PINN Enterprise Platform</h1>
            <h2>🚀 AI-Powered Physics Simulations</h2>
            <p>Production-ready Physics-Informed Neural Networks with RAG and 3D Visualization</p>
            
            <div class="status">
                ✅ <strong>SERVER RUNNING</strong> - Demo mode with full API
            </div>
            
            <a href="/docs" class="btn">📚 API Documentation</a>
            <a href="/health" class="btn">💚 Health Check</a>
            <a href="/ui" class="btn">🎨 Research Canvas UI</a>
        </div>
        
        <div>
            <h3>🌐 Available Endpoints</h3>
            <div style="text-align: left; max-width: 600px; margin: 0 auto; background: rgba(0,0,0,0.3); padding: 20px; border-radius: 8px;">
                <div style="font-family: monospace; margin: 5px 0;">GET  /health - Health check</div>
                <div style="font-family: monospace; margin: 5px 0;">POST /api/v2/simulations - Create simulation</div>
                <div style="font-family: monospace; margin: 5px 0;">GET  /api/v2/simulations/{id}/status - Get status</div>
                <div style="font-family: monospace; margin: 5px 0;">GET  /api/v2/simulations/{id}/code - Get Python code</div>
                <div style="font-family: monospace; margin: 5px 0;">GET  /ui - Research Canvas Interface</div>
            </div>
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
        "version": "2.0.0",
        "mode": "demo",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "running",
            "rag_generator": "ready",
            "visualization_3d": "ready"
        }
    }

@app.get("/ui")
async def research_canvas_ui():
    """CopilotKit-style Research Canvas UI"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PINN Enterprise Platform - Research Canvas</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&display=swap');
        
        body {
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
            background: #F5F8FF;
        }
        
        .simulation-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .simulation-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transform: translateY(-2px);
        }
        
        .field-input {
            width: 100%;
            padding: 16px 24px;
            border: none;
            border-radius: 12px;
            background: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            font-size: 16px;
            font-weight: 300;
            transition: all 0.3s ease;
        }
        
        .field-input:focus {
            outline: none;
            box-shadow: 0 0 0 3px rgba(103, 102, 252, 0.1);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #6766FC, #8B5CF6);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(103, 102, 252, 0.3);
        }
        
        .domain-card {
            background: white;
            border: 2px solid #E5E7EB;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .domain-card:hover {
            border-color: #6766FC;
            transform: translateY(-2px);
        }
        
        .domain-card.selected {
            border-color: #6766FC;
            background: #F8F9FF;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <!-- Header -->
    <header class="flex h-[60px] bg-[#0E103D] text-white items-center px-10 text-2xl font-medium">
        🧮 PINN Enterprise Platform
    </header>

    <!-- Main Layout -->
    <div class="flex flex-1 border" style="height: calc(100vh - 60px);">
        
        <!-- Main Content Area -->
        <div class="flex-1 overflow-hidden">
            <div class="w-full h-full overflow-y-auto p-10 bg-[#F5F8FF]">
                <div class="space-y-8 pb-10">
                    
                    <!-- Simulation Configuration Section -->
                    <div class="simulation-card">
                        <h2 class="text-lg font-medium mb-4 text-[#0E103D]">🚀 Create New Simulation</h2>
                        
                        <!-- Simulation Name -->
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 mb-2">Simulation Name</label>
                            <input 
                                type="text" 
                                class="field-input" 
                                placeholder="Enter simulation name (e.g., Golf Ball Aerodynamics)"
                                id="simulation-name"
                            />
                        </div>
                        
                        <!-- Physics Domain Selection -->
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 mb-3">Physics Domain</label>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="domain-card" data-domain="fluid_dynamics">
                                    <div class="text-3xl mb-2">🌊</div>
                                    <h3 class="font-semibold">Fluid Dynamics</h3>
                                    <p class="text-sm text-gray-600 mt-1">CFD, Aerodynamics, Flow Analysis</p>
                                </div>
                                <div class="domain-card" data-domain="heat_transfer">
                                    <div class="text-3xl mb-2">🔥</div>
                                    <h3 class="font-semibold">Heat Transfer</h3>
                                    <p class="text-sm text-gray-600 mt-1">Thermal Analysis, Cooling Systems</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Application -->
                        <div class="mb-6">
                            <label class="block text-sm font-medium text-gray-700 mb-2">Engineering Application</label>
                            <input 
                                type="text" 
                                class="field-input" 
                                placeholder="Describe your engineering application"
                                id="application"
                            />
                        </div>
                        
                        <!-- Create Button -->
                        <button class="btn-primary w-full" onclick="createSimulation()">
                            🚀 Create Simulation with AI-Generated Code
                        </button>
                    </div>
                    
                    <!-- Platform Metrics -->
                    <div class="simulation-card">
                        <h2 class="text-lg font-medium mb-4 text-[#0E103D]">📈 Platform Status</h2>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div class="metric-card">
                                <div class="text-2xl font-bold">🚀</div>
                                <div class="text-sm opacity-90">Demo Ready</div>
                            </div>
                            <div class="metric-card">
                                <div class="text-2xl font-bold">⚡</div>
                                <div class="text-sm opacity-90">Fast API</div>
                            </div>
                            <div class="metric-card">
                                <div class="text-2xl font-bold">🤖</div>
                                <div class="text-sm opacity-90">AI-Powered</div>
                            </div>
                        </div>
                    </div>
                    
                </div>
            </div>
        </div>
        
        <!-- CopilotKit-style Chat Sidebar -->
        <div class="w-[500px] h-full flex-shrink-0 bg-[#E0E9FD] border-l">
            <div class="h-full p-6 flex flex-col">
                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-[#0E103D] mb-2">🤖 AI Research Assistant</h3>
                    <p class="text-sm text-gray-600">Ask me about physics simulations, PINN theory, or engineering applications!</p>
                </div>
                
                <!-- Chat Messages Container -->
                <div class="flex-1 overflow-y-auto mb-4" id="chat-messages">
                    <div class="bg-white rounded-lg p-4 mb-4 shadow-sm">
                        <div class="flex items-start gap-3">
                            <div class="w-8 h-8 bg-[#6766FC] rounded-full flex items-center justify-center text-white text-sm font-bold">
                                AI
                            </div>
                            <div class="flex-1">
                                <p class="text-sm text-gray-800">
                                    Welcome to the PINN Enterprise Platform! 🎉
                                </p>
                                <p class="text-sm text-gray-600 mt-2">
                                    I can help you create professional physics simulations with AI-generated Python code. Try creating a simulation above!
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Chat Input -->
                <div class="flex gap-2">
                    <input 
                        type="text" 
                        class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6766FC] focus:border-transparent"
                        placeholder="Ask about PINN simulations..."
                        id="chat-input"
                        onkeypress="handleChatKeyPress(event)"
                    />
                    <button 
                        class="btn-primary px-6"
                        onclick="sendChatMessage()"
                    >
                        Send
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedDomain = null;
        
        // Domain selection
        document.querySelectorAll('.domain-card').forEach(card => {
            card.addEventListener('click', function() {
                document.querySelectorAll('.domain-card').forEach(c => c.classList.remove('selected'));
                this.classList.add('selected');
                selectedDomain = this.dataset.domain;
            });
        });
        
        // Create simulation
        async function createSimulation() {
            const name = document.getElementById('simulation-name').value;
            const application = document.getElementById('application').value;
            
            if (!name || !application || !selectedDomain) {
                alert('Please fill in all fields and select a physics domain');
                return;
            }
            
            try {
                addChatMessage('AI', '🚀 Creating your simulation with AI-generated code...');
                
                const response = await fetch('/api/v2/simulations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: name,
                        domain_type: selectedDomain,
                        application: application,
                        complexity_level: 'intermediate'
                    })
                });
                
                const result = await response.json();
                addChatMessage('AI', `🎉 Simulation "${name}" created! Workflow ID: ${result.workflow_id}`);
                
                // Clear form
                document.getElementById('simulation-name').value = '';
                document.getElementById('application').value = '';
                document.querySelectorAll('.domain-card').forEach(c => c.classList.remove('selected'));
                selectedDomain = null;
                
            } catch (error) {
                addChatMessage('AI', `❌ Error: ${error.message}`);
            }
        }
        
        // Chat functionality
        function handleChatKeyPress(event) {
            if (event.key === 'Enter') {
                sendChatMessage();
            }
        }
        
        function sendChatMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            addChatMessage('User', message);
            input.value = '';
            
            // Simple AI responses
            setTimeout(() => {
                let response = 'I can help you with PINN theory, physics equations, and simulation setup. What would you like to know?';
                
                if (message.toLowerCase().includes('pinn')) {
                    response = 'Physics-Informed Neural Networks (PINNs) solve PDEs by incorporating physics laws directly into neural network training. They minimize both data loss and physics equation residuals.';
                } else if (message.toLowerCase().includes('navier')) {
                    response = 'The Navier-Stokes equations describe fluid motion: momentum conservation (∇·τ + ρf = ρa) and mass conservation (∇·v = 0 for incompressible flow).';
                } else if (message.toLowerCase().includes('heat')) {
                    response = 'Heat transfer simulations solve the heat equation: ∂T/∂t = α∇²T + Q, including conduction, convection, and radiation effects.';
                }
                
                addChatMessage('AI', response);
            }, 1000);
        }
        
        function addChatMessage(sender, message) {
            const container = document.getElementById('chat-messages');
            const isUser = sender === 'User';
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'bg-white rounded-lg p-4 mb-4 shadow-sm';
            messageDiv.innerHTML = `
                <div class="flex items-start gap-3">
                    <div class="w-8 h-8 ${isUser ? 'bg-gray-500' : 'bg-[#6766FC]'} rounded-full flex items-center justify-center text-white text-sm font-bold">
                        ${isUser ? 'U' : 'AI'}
                    </div>
                    <div class="flex-1">
                        <p class="text-sm text-gray-800">${message}</p>
                    </div>
                </div>
            `;
            
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
    </script>
</body>
</html>
    """)

@app.post("/api/v2/simulations")
async def create_simulation(request: Dict[str, Any]):
    """Create a new PINN simulation"""
    workflow_id = str(uuid.uuid4())
    
    # Store workflow
    workflows_db[workflow_id] = {
        "workflow_id": workflow_id,
        "name": request.get("name", "Unnamed Simulation"),
        "domain_type": request.get("domain_type", "fluid_dynamics"),
        "application": request.get("application", "Generic Application"),
        "status": "initiated",
        "progress": 0,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Generate sample Python code
    python_code = generate_sample_code(request.get("domain_type", "fluid_dynamics"), request.get("application", "Generic"))
    
    # Store generated code
    results_db[workflow_id] = {
        "python_code": python_code,
        "status": "completed"
    }
    
    return {
        "workflow_id": workflow_id,
        "status": "initiated",
        "name": request.get("name"),
        "domain_type": request.get("domain_type"),
        "endpoints": {
            "status": f"/api/v2/simulations/{workflow_id}/status",
            "code": f"/api/v2/simulations/{workflow_id}/code"
        }
    }

@app.get("/api/v2/simulations/{workflow_id}/status")
async def get_simulation_status(workflow_id: str):
    """Get simulation status"""
    if workflow_id not in workflows_db:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return workflows_db[workflow_id]

@app.get("/api/v2/simulations/{workflow_id}/code")
async def get_simulation_code(workflow_id: str):
    """Get generated Python code"""
    if workflow_id not in results_db:
        raise HTTPException(status_code=404, detail="Code not found")
    
    return {
        "workflow_id": workflow_id,
        "python_code": results_db[workflow_id]["python_code"],
        "language": "python",
        "framework": "deepxde"
    }

def generate_sample_code(domain_type: str, application: str) -> str:
    """Generate sample PINN code"""
    class_name = application.replace(" ", "").replace("-", "") + "Simulation"
    
    if domain_type == "fluid_dynamics":
        return f'''import numpy as np
import deepxde as dde
import tensorflow as tf

class {class_name}:
    """Professional {application} simulation using PINNs"""
    
    def __init__(self, config):
        self.config = config
        self.setup_geometry()
        self.setup_physics()
        
    def setup_geometry(self):
        """Define computational domain"""
        self.geom = dde.geometry.Rectangle([-2, -2], [2, 2])
        
    def setup_physics(self):
        """Define Navier-Stokes equations"""
        def navier_stokes(x, u):
            u_vel, v_vel, p = u[:, 0:1], u[:, 1:2], u[:, 2:3]
            
            # Gradients
            u_x = dde.grad.jacobian(u_vel, x, i=0, j=0)
            u_y = dde.grad.jacobian(u_vel, x, i=0, j=1)
            v_x = dde.grad.jacobian(v_vel, x, i=0, j=0)
            v_y = dde.grad.jacobian(v_vel, x, i=0, j=1)
            p_x = dde.grad.jacobian(p, x, i=0, j=0)
            p_y = dde.grad.jacobian(p, x, i=0, j=1)
            
            # Viscous terms
            u_xx = dde.grad.hessian(u_vel, x, i=0, j=0)
            u_yy = dde.grad.hessian(u_vel, x, i=1, j=1)
            v_xx = dde.grad.hessian(v_vel, x, i=0, j=0)
            v_yy = dde.grad.hessian(v_vel, x, i=1, j=1)
            
            Re = self.config.get("reynolds_number", 100)
            
            # Momentum equations
            momentum_x = u_vel * u_x + v_vel * u_y + p_x - (u_xx + u_yy) / Re
            momentum_y = u_vel * v_x + v_vel * v_y + p_y - (v_xx + v_yy) / Re
            continuity = u_x + v_y
            
            return [momentum_x, momentum_y, continuity]
        
        self.pde = navier_stokes
        
    def create_model(self):
        """Create PINN model"""
        net = dde.nn.FNN([2, 100, 100, 100, 3], "tanh", "Glorot uniform")
        data = dde.data.PDE(self.geom, self.pde, [], num_domain=2000)
        model = dde.Model(data, net)
        model.compile("adam", lr=1e-3)
        return model
        
    def train(self):
        """Train the model"""
        model = self.create_model()
        losshistory, train_state = model.train(epochs=10000)
        return model, losshistory

# Usage example
if __name__ == "__main__":
    config = {{"reynolds_number": 100}}
    sim = {class_name}(config)
    model, history = sim.train()
    print("Training completed!")
'''
    
    else:  # heat_transfer
        return f'''import numpy as np
import deepxde as dde
import tensorflow as tf

class {class_name}:
    """Professional {application} heat transfer simulation using PINNs"""
    
    def __init__(self, config):
        self.config = config
        self.setup_geometry()
        self.setup_physics()
        
    def setup_geometry(self):
        """Define thermal domain"""
        self.geom = dde.geometry.Rectangle([0, 0], [1, 1])
        
    def setup_physics(self):
        """Define heat equation"""
        def heat_equation(x, T):
            T_x = dde.grad.jacobian(T, x, i=0, j=0)
            T_y = dde.grad.jacobian(T, x, i=0, j=1)
            T_xx = dde.grad.hessian(T, x, i=0, j=0)
            T_yy = dde.grad.hessian(T, x, i=1, j=1)
            
            k = self.config.get("thermal_conductivity", 1.0)
            source = self.config.get("heat_source", 0.0)
            
            return k * (T_xx + T_yy) + source
        
        self.pde = heat_equation
        
    def create_model(self):
        """Create thermal PINN model"""
        net = dde.nn.FNN([2, 50, 50, 50, 1], "tanh", "Glorot uniform")
        data = dde.data.PDE(self.geom, self.pde, [], num_domain=1000)
        model = dde.Model(data, net)
        model.compile("adam", lr=1e-3)
        return model

# Usage example
if __name__ == "__main__":
    config = {{"thermal_conductivity": 1.0, "heat_source": 10.0}}
    sim = {class_name}(config)
    model = sim.create_model()
    print("Thermal model ready!")
'''

if __name__ == "__main__":
    print("🚀 Starting PINN Platform Demo Server...")
    print("📍 Server will be available at: http://localhost:51736")
    print("📚 API Documentation: http://localhost:51736/docs")
    print("🔍 Health Check: http://localhost:51736/health")
    print("🎨 Research Canvas UI: http://localhost:51736/ui")
    print("⚡ Mode: Demo (lightweight, no ML dependencies)")
    print("")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=51736,
        reload=False,
        log_level="info"
    )