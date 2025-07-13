"""Demo for PINN Solver with CopilotKit"""

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
import uvicorn
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent
from pinn_solver.langgraph.agent import graph

app = FastAPI()

# Create the CopilotKit SDK with PINN agents
sdk = CopilotKitRemoteEndpoint(
    agents=[
        LangGraphAgent(
            name="pinn_solver_agent",
            description="Physics-Informed Neural Network solver for engineering problems. Can solve heat transfer, fluid dynamics, structural mechanics, and electromagnetics problems using deep learning.",
            graph=graph,
        ),
        LangGraphAgent(
            name="heat_transfer_specialist",
            description="Specialized agent for heat transfer and thermal analysis problems using PINNs.",
            graph=graph,
        ),
        LangGraphAgent(
            name="fluid_dynamics_specialist", 
            description="Specialized agent for fluid dynamics and CFD problems using PINNs.",
            graph=graph,
        ),
        LangGraphAgent(
            name="structural_specialist",
            description="Specialized agent for structural mechanics and FEA problems using PINNs.",
            graph=graph,
        ),
    ],
)

# Add the CopilotKit FastAPI endpoint
add_fastapi_endpoint(app, sdk, "/copilotkit")

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "PINN Solver Agent",
        "version": "0.1.0"
    }

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "PINN Solver Agent with CopilotKit",
        "endpoints": {
            "health": "/health",
            "copilotkit": "/copilotkit"
        }
    }

def main():
    """Run the uvicorn server"""
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting PINN Solver Agent on {host}:{port}")
    print(f"🔗 CopilotKit endpoint: http://{host}:{port}/copilotkit")
    print(f"🏥 Health check: http://{host}:{port}/health")
    
    uvicorn.run(
        "pinn_solver.demo:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=["."]
    )