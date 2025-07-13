#!/bin/bash

# PINN Enterprise Platform - Cloudflare Workers Deployment Script
# Deploy to api.ensimu.space with your Zone ID and Account ID

set -e

echo "🚀 PINN Enterprise Platform - Cloudflare Workers Deployment"
echo "=========================================================="

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

# Check if logged in to Cloudflare
echo "🔐 Checking Cloudflare authentication..."
if ! wrangler whoami &> /dev/null; then
    echo "❌ Not logged in to Cloudflare. Please run: wrangler login"
    exit 1
fi

echo "✅ Cloudflare authentication verified"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create KV namespaces if they don't exist
echo "🗄️ Setting up KV namespaces..."

# Check if namespaces exist, create if not
WORKFLOWS_KV_ID=$(wrangler kv:namespace list | grep "workflows_storage" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 || echo "")
if [ -z "$WORKFLOWS_KV_ID" ]; then
    echo "Creating workflows_storage KV namespace..."
    wrangler kv:namespace create "workflows_storage"
fi

RESULTS_KV_ID=$(wrangler kv:namespace list | grep "results_storage" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 || echo "")
if [ -z "$RESULTS_KV_ID" ]; then
    echo "Creating results_storage KV namespace..."
    wrangler kv:namespace create "results_storage"
fi

USECASES_KV_ID=$(wrangler kv:namespace list | grep "usecases_storage" | grep -o '"id":"[^"]*"' | cut -d'"' -f4 || echo "")
if [ -z "$USECASES_KV_ID" ]; then
    echo "Creating usecases_storage KV namespace..."
    wrangler kv:namespace create "usecases_storage"
fi

# Create R2 buckets if they don't exist
echo "🪣 Setting up R2 storage buckets..."

# Check if buckets exist, create if not
if ! wrangler r2 bucket list | grep -q "pinn-models-storage"; then
    echo "Creating pinn-models-storage R2 bucket..."
    wrangler r2 bucket create pinn-models-storage
fi

if ! wrangler r2 bucket list | grep -q "pinn-visualizations"; then
    echo "Creating pinn-visualizations R2 bucket..."
    wrangler r2 bucket create pinn-visualizations
fi

# Deploy to staging first
echo "🧪 Deploying to staging environment..."
wrangler deploy --env staging

echo "✅ Staging deployment completed!"
echo "🌐 Staging URL: https://staging-api.ensimu.space"

# Ask for confirmation before production deployment
read -p "🚀 Deploy to production (api.ensimu.space)? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying to production..."
    wrangler deploy --env production
    
    echo ""
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo "========================"
    echo "🌐 Production URL: https://api.ensimu.space"
    echo "📚 API Documentation: https://api.ensimu.space/docs"
    echo "🎮 Live Demo: https://api.ensimu.space/demo"
    echo "💚 Health Check: https://api.ensimu.space/health"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs: wrangler tail --env production"
    echo "  View KV data: wrangler kv:key list --binding WORKFLOWS_KV --env production"
    echo "  View R2 buckets: wrangler r2 bucket list"
    echo ""
    echo "🎯 Your PINN Enterprise Platform is now live!"
else
    echo "❌ Production deployment cancelled"
fi

echo ""
echo "📋 Next Steps:"
echo "1. Test the API endpoints at https://api.ensimu.space"
echo "2. Try the interactive demo at https://api.ensimu.space/demo"
echo "3. Monitor with: wrangler tail --env production"
echo "4. Update DNS if needed to point api.ensimu.space to Cloudflare"