# 🚀 PINN Solver - Quick Start Guide

Get your Physics-Informed Neural Network platform running in minutes!

## 🎯 What You'll Get

A complete conversational AI platform for solving physics problems:
- **Heat Transfer**: "Solve 2D heat conduction with 100°C left wall, 0°C right wall"
- **Fluid Dynamics**: "Analyze lid-driven cavity flow at Reynolds 100"
- **Structural Mechanics**: "Calculate stress in a cantilever beam with 1000N load"
- **Electromagnetics**: "Find electric field between parallel plates at 100V"

## ⚡ 5-Minute Setup

### 1. Prerequisites
```bash
# Check you have these installed:
node --version    # v18+
python3 --version # 3.12+
poetry --version  # Latest
aws --version     # Latest
```

### 2. Clone & Setup
```bash
git clone <your-repo-url>
cd workspace/coagents-pinn-solver
```

### 3. Configure Environment
```bash
# Agent backend
cp agent/.env.example agent/.env
# Edit agent/.env with your API keys

# UI frontend  
cp ui/.env.example ui/.env.local
# Edit ui/.env.local with your API keys
```

### 4. Start Development Environment
```bash
./deploy.sh dev
```

That's it! 🎉

## 🌐 Access Your Platform

- **UI**: http://localhost:3000
- **Agent API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## 💬 Try These Examples

### Heat Transfer
```
"I need to solve a 2D heat conduction problem in a square domain. 
The left wall is at 100°C, right wall at 0°C, and top/bottom walls are insulated."
```

### Fluid Dynamics
```
"Can you solve lid-driven cavity flow with Reynolds number 100? 
The top wall moves with velocity 1 m/s."
```

### Structural Analysis
```
"Analyze a cantilever beam with length 1m, fixed at left end, 
point load 1000N at free end. Material is steel."
```

## 🚀 Production Deployment

### Deploy Serverless Backend
```bash
cd ../  # Go to workspace root
serverless deploy --stage prod
```

### Deploy Full Platform
```bash
cd coagents-pinn-solver/
./deploy.sh prod
```

## 🔧 Environment Variables

### Required for Agent (.env)
```bash
OPENAI_API_KEY=sk-...                    # OpenAI API key
AWS_ACCESS_KEY_ID=AKIA...               # AWS credentials
AWS_SECRET_ACCESS_KEY=...               # AWS credentials
PINN_API_ENDPOINT=https://...           # Serverless backend URL
```

### Required for UI (.env.local)
```bash
OPENAI_API_KEY=sk-...                    # OpenAI API key
PINN_AGENT_URL=http://localhost:8000/copilotkit  # Agent backend
```

## 🆘 Troubleshooting

### Common Issues

**Agent won't start:**
```bash
cd agent/
poetry install
poetry run demo
```

**UI won't start:**
```bash
cd ui/
npm install
npm run dev
```

**Backend deployment fails:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check serverless config
serverless info
```

### Get Help
- Check logs: `./deploy.sh check`
- View health: http://localhost:8000/health
- Clean restart: `./deploy.sh clean && ./deploy.sh dev`

## 📊 What Happens Next

1. **User describes physics problem** in natural language
2. **AI agent analyzes** and configures PINN automatically  
3. **Serverless backend** trains the neural network
4. **Real-time monitoring** shows progress and metrics
5. **Results visualization** displays solution and insights

## 🎓 Learn More

- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Full Documentation**: [README.md](README.md)
- **Deployment Details**: [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)

## 🏆 Success Metrics

Your platform is working when you see:
- ✅ Agent responds to physics questions
- ✅ Workflows appear in dashboard
- ✅ Training progress updates in real-time
- ✅ Results visualize automatically

---

**Need help?** Open an issue or check the troubleshooting section above.

**Ready to scale?** Follow the production deployment guide.

**Want to customize?** Check the integration guide for advanced features.