# 🚀 PINN Enterprise Platform - Cloudflare Workers Deployment

This directory contains the **production-ready Cloudflare Workers deployment** for the PINN Enterprise Platform.

## ⚡ **Quick Deploy**

```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Install dependencies
npm install

# Deploy to production
npm run deploy
```

## 🌐 **Live URLs**

- **Production API**: https://api.ensimu.space
- **Research Canvas UI**: https://api.ensimu.space/ui
- **API Documentation**: https://api.ensimu.space/docs
- **Health Check**: https://api.ensimu.space/health

## 📁 **Deployment Structure**

```
pinn-workers-deploy/
├── package.json          # Node.js dependencies (Wrangler only)
├── wrangler.toml         # Cloudflare Workers configuration
├── README.md             # This deployment guide
└── src/                  # Workers source code
    ├── index.js          # Main Workers entry point
    ├── ui/               # CopilotKit-style UI
    └── services/         # Core services (RAG, 3D, WebSocket)
```

## 🔧 **Configuration**

### **Cloudflare Account Settings**
- **Account ID**: `5adf62efd6cf179a8939c211b155e229`
- **Zone ID**: `11888a0ee8a4d631a3b430bd1b909674`
- **Domain**: `api.ensimu.space`

### **Workers Features**
- **KV Storage**: Workflows, results, use cases
- **R2 Storage**: Models, visualizations
- **Durable Objects**: WebSocket management
- **Global Edge**: 200+ locations worldwide

## 🚀 **Deployment Commands**

```bash
# Development
wrangler dev

# Production deployment
wrangler deploy

# Staging deployment  
wrangler deploy --env staging

# View logs
wrangler tail
```

## ✅ **Deployment Verification**

After deployment, verify these endpoints:

```bash
# Health check
curl https://api.ensimu.space/health

# Create simulation
curl -X POST https://api.ensimu.space/api/v2/simulations \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "domain_type": "fluid_dynamics"}'

# Access UI
open https://api.ensimu.space/ui
```

## 🌟 **Features Deployed**

- ✅ **CopilotKit-style Research Canvas UI**
- ✅ **RAG-powered AI code generation**
- ✅ **Real-time WebSocket support**
- ✅ **3D visualization engine**
- ✅ **Global edge performance**
- ✅ **Enterprise scalability**

---

**🧮 PINN Enterprise Platform - Deployed on Cloudflare Workers** ⚡