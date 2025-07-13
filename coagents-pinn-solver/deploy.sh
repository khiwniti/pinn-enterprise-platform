#!/bin/bash

# PINN Solver with CopilotKit - Deployment Script
# This script deploys the complete PINN platform with CopilotKit integration

set -e

echo "🚀 Deploying PINN Solver with CopilotKit..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if required commands exist
    commands=("node" "npm" "python3" "poetry" "aws" "serverless")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            print_error "$cmd is not installed. Please install it first."
            exit 1
        fi
    done
    
    # Check Node.js version
    node_version=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$node_version" -lt 18 ]; then
        print_error "Node.js version 18 or higher is required. Current version: $(node --version)"
        exit 1
    fi
    
    # Check Python version
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)"; then
        print_error "Python 3.12 or higher is required. Current version: $(python3 --version)"
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Deploy serverless PINN backend
deploy_pinn_backend() {
    print_status "Deploying serverless PINN backend..."
    
    cd ../
    
    # Install serverless dependencies
    if [ ! -d "node_modules" ]; then
        print_status "Installing serverless dependencies..."
        npm install
    fi
    
    # Deploy the serverless backend
    print_status "Deploying to AWS..."
    serverless deploy --stage prod
    
    # Get the API Gateway URL
    API_URL=$(serverless info --stage prod | grep "ServiceEndpoint" | cut -d' ' -f2)
    print_success "PINN backend deployed! API URL: $API_URL"
    
    # Save API URL for agent configuration
    echo "PINN_API_ENDPOINT=$API_URL" > coagents-pinn-solver/agent/.env.local
    
    cd coagents-pinn-solver/
}

# Setup and start the agent
setup_agent() {
    print_status "Setting up PINN agent..."
    
    cd agent/
    
    # Install Python dependencies
    if [ ! -f "poetry.lock" ]; then
        print_status "Installing Python dependencies..."
        poetry install
    fi
    
    # Check for environment file
    if [ ! -f ".env" ]; then
        print_warning "No .env file found. Please copy .env.example to .env and configure it."
        cp .env.example .env
        print_warning "Please edit agent/.env with your API keys before continuing."
        read -p "Press Enter when you've configured the .env file..."
    fi
    
    cd ../
}

# Setup and start the UI
setup_ui() {
    print_status "Setting up PINN UI..."
    
    cd ui/
    
    # Install Node.js dependencies
    if [ ! -d "node_modules" ]; then
        print_status "Installing UI dependencies..."
        npm install
    fi
    
    # Check for environment file
    if [ ! -f ".env.local" ]; then
        print_warning "No .env.local file found. Please copy .env.example to .env.local and configure it."
        cp .env.example .env.local
        print_warning "Please edit ui/.env.local with your API keys before continuing."
        read -p "Press Enter when you've configured the .env.local file..."
    fi
    
    cd ../
}

# Start development servers
start_dev_servers() {
    print_status "Starting development servers..."
    
    # Start agent in background
    print_status "Starting PINN agent on port 8000..."
    cd agent/
    poetry run demo &
    AGENT_PID=$!
    cd ../
    
    # Wait for agent to start
    sleep 5
    
    # Start UI
    print_status "Starting UI on port 3000..."
    cd ui/
    npm run dev &
    UI_PID=$!
    cd ../
    
    # Wait for UI to start
    sleep 5
    
    print_success "🎉 PINN Solver is now running!"
    echo ""
    echo "📊 Agent Backend: http://localhost:8000"
    echo "🌐 UI Frontend: http://localhost:3000"
    echo "🏥 Health Check: http://localhost:8000/health"
    echo ""
    echo "Press Ctrl+C to stop all servers"
    
    # Wait for user interrupt
    trap "kill $AGENT_PID $UI_PID; exit" INT
    wait
}

# Production deployment
deploy_production() {
    print_status "Deploying to production..."
    
    # Deploy agent to cloud (Docker)
    print_status "Building agent Docker image..."
    cd agent/
    docker build -t pinn-agent:latest .
    
    # Tag and push to registry (user needs to configure)
    print_warning "Please configure your container registry and push the image:"
    echo "docker tag pinn-agent:latest your-registry/pinn-agent:latest"
    echo "docker push your-registry/pinn-agent:latest"
    
    cd ../
    
    # Deploy UI to Vercel/Netlify
    print_status "Building UI for production..."
    cd ui/
    npm run build
    
    print_warning "Please deploy the UI to your preferred platform:"
    echo "- Vercel: vercel deploy"
    echo "- Netlify: netlify deploy --prod"
    echo "- AWS S3: aws s3 sync out/ s3://your-bucket/"
    
    cd ../
}

# Main deployment flow
main() {
    echo "🧠 PINN Solver with CopilotKit Deployment"
    echo "========================================"
    echo ""
    
    # Parse command line arguments
    case "${1:-dev}" in
        "check")
            check_prerequisites
            ;;
        "backend")
            check_prerequisites
            deploy_pinn_backend
            ;;
        "dev")
            check_prerequisites
            setup_agent
            setup_ui
            start_dev_servers
            ;;
        "prod")
            check_prerequisites
            deploy_pinn_backend
            deploy_production
            ;;
        "clean")
            print_status "Cleaning up..."
            cd agent/ && rm -rf __pycache__ .pytest_cache && cd ../
            cd ui/ && rm -rf .next node_modules && cd ../
            rm -rf node_modules .serverless
            print_success "Cleanup complete!"
            ;;
        *)
            echo "Usage: $0 [check|backend|dev|prod|clean]"
            echo ""
            echo "Commands:"
            echo "  check   - Check prerequisites only"
            echo "  backend - Deploy serverless PINN backend only"
            echo "  dev     - Start development environment (default)"
            echo "  prod    - Deploy to production"
            echo "  clean   - Clean up build artifacts"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"