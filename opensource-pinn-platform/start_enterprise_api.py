#!/usr/bin/env python3
"""
Enterprise PINN Platform Startup Script
Launches the production-ready AI SaaS backend
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add services to Python path
services_path = Path(__file__).parent / "services"
sys.path.insert(0, str(services_path))

# Import the enterprise API
from api.enterprise_api import app

def main():
    """Start the enterprise PINN platform"""
    
    print("🧮 Starting PINN Enterprise Platform...")
    print("=" * 50)
    print("🚀 Production-ready AI SaaS backend")
    print("🤖 RAG-powered use case generation")
    print("🎨 Professional 3D visualization")
    print("⚡ Real-time WebSocket updates")
    print("🏢 Enterprise-grade features")
    print("=" * 50)
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    
    print(f"🌐 Server: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"🎮 Demo: http://{host}:{port}/demo")
    print(f"💚 Health: http://{host}:{port}/health")
    print("=" * 50)
    
    # Start server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )

if __name__ == "__main__":
    main()