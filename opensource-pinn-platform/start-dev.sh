#!/bin/bash

# Development startup script for PINN Platform (without Docker)
# This script starts the services directly for development/testing

set -e

echo "🚀 Starting Open Source PINN Platform (Development Mode)"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip

# Install core dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary redis minio celery
pip install numpy scipy matplotlib tensorflow deepxde
pip install prometheus-client pydantic python-multipart aiofiles
pip install python-dotenv

print_header "📋 Service Status Check"

# Check if Redis is available (optional for dev mode)
if command -v redis-server &> /dev/null; then
    print_status "Redis server found"
    if ! pgrep -x "redis-server" > /dev/null; then
        print_warning "Starting Redis server..."
        redis-server --daemonize yes --port 6379
        sleep 2
    else
        print_status "Redis server already running"
    fi
else
    print_warning "Redis not found - using in-memory cache for development"
fi

# Check if PostgreSQL is available (optional for dev mode)
if command -v psql &> /dev/null; then
    print_status "PostgreSQL found"
else
    print_warning "PostgreSQL not found - using SQLite for development"
fi

print_header "🔧 Configuration Setup"

# Create development environment file
cat > .env.dev << EOF
# Development Environment Configuration
ENVIRONMENT=development
DEBUG=true

# Database (SQLite for development)
DATABASE_URL=sqlite:///./pinn_platform.db

# Redis (optional in dev mode)
REDIS_URL=redis://localhost:6379/0

# MinIO (mock for development)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=secure123
MINIO_SECURE=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Security
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256

# CORS
CORS_ORIGINS=["*"]

# Monitoring
ENABLE_MONITORING=true
ENABLE_TRACING=false
ENABLE_LOGGING=true
EOF

print_status "Created development environment configuration"

print_header "🌐 Starting Services"

# Create a simple mock storage service
cat > mock_storage.py << 'EOF'
"""Mock storage service for development"""
import os
import json
from pathlib import Path

class MockStorage:
    def __init__(self):
        self.storage_dir = Path("./dev_storage")
        self.storage_dir.mkdir(exist_ok=True)
    
    def upload_file(self, key, file_path):
        dest = self.storage_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(file_path, dest)
        return True
    
    def upload_json(self, key, data):
        dest = self.storage_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    
    def download_json(self, key):
        file_path = self.storage_dir / key
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return None

# Global instance
storage = MockStorage()
EOF

# Create a simplified API server
cat > dev_server.py << 'EOF'
"""Development server for PINN Platform"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the API directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "services" / "api"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PINN Platform - Development Server",
    description="Physics-Informed Neural Networks Platform",
    version="1.0.0-dev"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock database
workflows_db = {}
models_db = {}

@app.get("/")
async def root():
    """Root endpoint with platform information"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>PINN Platform - Development</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .endpoint { background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
            .code { background: #f4f4f4; padding: 10px; border-radius: 3px; font-family: monospace; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧮 PINN Platform - Development Server</h1>
            
            <div class="status">
                <strong>✅ Server Status:</strong> Running in Development Mode<br>
                <strong>🌐 API Base URL:</strong> <a href="http://localhost:8000">http://localhost:8000</a><br>
                <strong>📚 API Documentation:</strong> <a href="/docs">/docs</a> | <a href="/redoc">/redoc</a>
            </div>
            
            <h2>🚀 Quick Start</h2>
            <p>This is a development server for the Open Source PINN Platform. The platform provides Physics-Informed Neural Networks for solving complex physics problems.</p>
            
            <h3>📡 Available Endpoints</h3>
            <div class="endpoint"><strong>GET /health</strong> - Health check</div>
            <div class="endpoint"><strong>POST /api/v1/pinn/solve</strong> - Submit PINN problem</div>
            <div class="endpoint"><strong>GET /api/v1/pinn/status/{id}</strong> - Get workflow status</div>
            <div class="endpoint"><strong>GET /api/v1/workflows</strong> - List workflows</div>
            <div class="endpoint"><strong>GET /api/v1/monitoring/metrics</strong> - System metrics</div>
            
            <h3>🧪 Example Usage</h3>
            <div class="code">
curl -X POST "http://localhost:8000/api/v1/pinn/solve" \\
     -H "Content-Type: application/json" \\
     -d '{
       "name": "Heat Transfer Example",
       "description": "2D heat conduction in square domain",
       "domain_type": "heat_transfer",
       "geometry": {"type": "rectangle", "xmin": 0, "ymin": 0, "xmax": 1, "ymax": 1},
       "boundary_conditions": {
         "left": {"type": "dirichlet", "value": 0},
         "right": {"type": "dirichlet", "value": 1}
       },
       "physics_parameters": {"thermal_diffusivity": 1.0}
     }'
            </div>
            
            <h3>🔗 Links</h3>
            <ul>
                <li><a href="/docs">Interactive API Documentation (Swagger)</a></li>
                <li><a href="/redoc">Alternative API Documentation (ReDoc)</a></li>
                <li><a href="/health">Health Check</a></li>
                <li><a href="/api/v1/pinn/domains">Supported Physics Domains</a></li>
            </ul>
        </div>
    </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "development",
        "services": {
            "api": "running",
            "database": "mock",
            "storage": "mock",
            "workers": "mock"
        }
    }

@app.post("/api/v1/pinn/solve")
async def solve_pinn_problem(request: dict):
    """Submit a PINN problem for solving (mock implementation)"""
    import uuid
    
    workflow_id = str(uuid.uuid4())
    
    # Store in mock database
    workflows_db[workflow_id] = {
        "id": workflow_id,
        "name": request.get("name", "Unnamed Problem"),
        "status": "completed",  # Mock as completed for demo
        "progress": 100.0,
        "accuracy": 0.95,
        "domain_type": request.get("domain_type", "heat_transfer"),
        "created_at": "2025-07-13T14:00:00Z"
    }
    
    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "estimated_completion_time": 0,
        "endpoints": {
            "status": f"/api/v1/pinn/status/{workflow_id}",
            "results": f"/api/v1/pinn/results/{workflow_id}"
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
    
    return {
        "workflow_id": workflow_id,
        "results": {
            "solution": "Mock solution data",
            "accuracy": 0.95,
            "training_time": 120.5,
            "loss_history": [0.1, 0.05, 0.02, 0.01]
        }
    }

@app.get("/api/v1/workflows")
async def list_workflows():
    """List all workflows"""
    return list(workflows_db.values())

@app.get("/api/v1/pinn/domains")
async def get_supported_domains():
    """Get supported physics domains"""
    return {
        "domains": [
            {
                "id": "heat_transfer",
                "name": "Heat Transfer",
                "description": "Steady-state and transient heat conduction",
                "examples": ["2D heat conduction", "Transient heating"]
            },
            {
                "id": "fluid_dynamics", 
                "name": "Fluid Dynamics",
                "description": "Incompressible Navier-Stokes equations",
                "examples": ["Lid-driven cavity", "Flow around cylinder"]
            }
        ]
    }

@app.get("/api/v1/monitoring/metrics")
async def get_metrics():
    """Get system metrics"""
    return {
        "active_workflows": len(workflows_db),
        "total_workflows": len(workflows_db),
        "system_status": "healthy",
        "uptime": "5 minutes"
    }

if __name__ == "__main__":
    print("🚀 Starting PINN Platform Development Server...")
    uvicorn.run(
        "dev_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
EOF

print_status "Created development server"

print_header "🎯 Starting Development Server"

# Start the development server
print_status "Starting FastAPI development server on http://localhost:8000"
print_status "API Documentation available at: http://localhost:8000/docs"
print_status "Alternative docs at: http://localhost:8000/redoc"
print_status ""
print_status "Press Ctrl+C to stop the server"
print_status ""

# Run the server
python dev_server.py
EOF