"""
Open Source PINN Platform - FastAPI Backend
Main application entry point with CopilotKit integration
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# CopilotKit Integration
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import CopilotKitRemoteEndpoint, LangGraphAgent

# Internal imports
from core.config import settings
from core.database import engine, create_tables
from core.redis_client import redis_client
from core.minio_client import minio_client
from api.routes import pinn, workflows, monitoring
from agents.pinn_agent import create_pinn_agent_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting PINN Platform...")
    
    # Initialize database
    await create_tables()
    logger.info("Database initialized")
    
    # Test connections
    try:
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
    
    try:
        if minio_client.bucket_exists("pinn-models"):
            logger.info("MinIO connection established")
        else:
            minio_client.make_bucket("pinn-models")
            logger.info("MinIO bucket created")
    except Exception as e:
        logger.error(f"MinIO connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down PINN Platform...")

# Create FastAPI app
app = FastAPI(
    title="Open Source PINN Platform",
    description="Physics-Informed Neural Networks with CopilotKit",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database
        from core.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        
        # Check Redis
        await redis_client.ping()
        
        # Check MinIO
        minio_client.bucket_exists("pinn-models")
        
        return {
            "status": "healthy",
            "services": {
                "database": "up",
                "redis": "up",
                "minio": "up"
            },
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Include API routes
app.include_router(pinn.router, prefix="/api/v1/pinn", tags=["PINN"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["Monitoring"])

# CopilotKit Integration
try:
    # Create the PINN agent graph
    pinn_graph = create_pinn_agent_graph()
    
    # Create CopilotKit SDK
    sdk = CopilotKitRemoteEndpoint(
        agents=[
            LangGraphAgent(
                name="pinn_solver_agent",
                description="Physics-Informed Neural Network solver for complex physics problems",
                graph=pinn_graph,
            ),
        ],
    )
    
    # Add CopilotKit endpoint
    add_fastapi_endpoint(app, sdk, "/copilotkit")
    logger.info("CopilotKit integration enabled")
    
except Exception as e:
    logger.error(f"CopilotKit integration failed: {e}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "status_code": 500}
    )

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Open Source PINN Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )