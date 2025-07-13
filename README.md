# 🧮 PINN Enterprise Platform

> **AI-Powered Physics Simulations with CopilotKit-style Research Canvas UI**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Cloudflare Workers](https://img.shields.io/badge/Cloudflare-Workers-orange.svg)](https://workers.cloudflare.com/)
[![DeepXDE](https://img.shields.io/badge/DeepXDE-Physics-purple.svg)](https://deepxde.readthedocs.io/)

A complete, production-ready enterprise platform for Physics-Informed Neural Networks (PINNs) featuring a CopilotKit-inspired research canvas UI, RAG-powered AI code generation, and global serverless deployment.

## 🌟 **Live Demo**

🎨 **Research Canvas UI**: [Try the Interactive Demo](http://localhost:51736/ui)  
📚 **API Documentation**: [Explore the API](http://localhost:51736/docs)  
🚀 **Production Deployment**: Coming soon at `api.ensimu.space`

## Architecture Principles

### Core Design Philosophy
- **Hybrid Serverless**: Lambda for coordination, containers for computation
- **Event-Driven**: Asynchronous messaging for all components
- **GPU-Optimized**: Intelligent GPU resource allocation for PINN training/inference
- **Cost-Efficient**: Pay-per-use with automatic scaling and resource optimization
- **Fault-Tolerant**: Graceful degradation and automatic retries

## Quick Start

```bash
# Install dependencies
npm install -g serverless
pip install -r requirements.txt

# Deploy the platform
serverless deploy --stage prod

# Build and deploy training containers
./scripts/deploy-containers.sh

# Deploy infrastructure
./scripts/deploy-infrastructure.sh
```

## Architecture Components

1. **API Gateway & Orchestration** - Main entry point and workflow coordination
2. **PINN Problem Analyzer** - Intelligent problem analysis and architecture recommendation
3. **ECS Training Service** - GPU-accelerated PINN training with DeepXDE
4. **Fast Inference Handler** - Real-time inference with model caching
5. **Model Deployment** - SageMaker integration for production inference
6. **Monitoring & Optimization** - Cost optimization and performance monitoring

## Supported Physics Domains

- Heat Transfer (Diffusion equations)
- Fluid Dynamics (Navier-Stokes equations)
- Structural Mechanics (Elasticity equations)
- Electromagnetics (Maxwell equations)
- Wave Propagation (Wave equations)

## Features

- **Automatic PINN Architecture Selection**: Based on problem complexity and physics domain
- **Hybrid Compute Strategy**: Lambda for coordination, ECS/Batch for heavy computation
- **Real-time Inference**: Sub-second inference with cached models
- **Cost Optimization**: Intelligent resource scaling and cleanup
- **Production Monitoring**: CloudWatch dashboards and custom metrics
- **Multi-GPU Support**: Automatic GPU allocation for training workloads

## API Endpoints

- `POST /pinn/solve` - Submit physics problem for PINN solution
- `GET /pinn/status/{workflow_id}` - Check workflow status
- `GET /pinn/results/{workflow_id}` - Retrieve simulation results
- `POST /pinn/inference/{workflow_id}` - Real-time inference

## Cost Estimates

Typical costs for different problem types:
- Simple heat transfer: $0.10 - $0.50 per solution
- Complex fluid dynamics: $2.00 - $10.00 per solution
- Real-time inference: $0.001 - $0.01 per request

## License

MIT License - see LICENSE file for details.