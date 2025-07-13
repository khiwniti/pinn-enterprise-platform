#!/bin/bash

# Open Source PINN Platform - Startup Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Copy environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_warning "No .env file found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your configuration before continuing."
        read -p "Press Enter when you've configured the .env file..."
    fi
    
    # Create necessary directories
    mkdir -p services/nginx/ssl
    mkdir -p storage/postgres
    mkdir -p storage/minio
    mkdir -p storage/redis
    mkdir -p services/monitoring/prometheus
    mkdir -p services/monitoring/grafana/provisioning
    mkdir -p services/monitoring/grafana/dashboards
    
    print_success "Environment setup complete!"
}

# Build and start services
start_services() {
    local mode=${1:-dev}
    
    print_status "Starting PINN platform in $mode mode..."
    
    case $mode in
        "dev")
            print_status "Starting development environment..."
            docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
            ;;
        "prod")
            print_status "Starting production environment..."
            docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
            ;;
        *)
            print_status "Starting default environment..."
            docker-compose up --build -d
            ;;
    esac
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
}

# Check service health
check_service_health() {
    print_status "Checking service health..."
    
    services=("postgres" "redis" "minio" "api")
    
    for service in "${services[@]}"; do
        if docker-compose ps $service | grep -q "Up (healthy)"; then
            print_success "$service is healthy"
        else
            print_warning "$service is not healthy yet"
        fi
    done
}

# Show service URLs
show_urls() {
    print_success "🎉 PINN Platform is running!"
    echo ""
    echo "📊 Service URLs:"
    echo "  🌐 UI Frontend:      http://localhost:3000"
    echo "  🔧 API Backend:      http://localhost:8000"
    echo "  📈 API Docs:         http://localhost:8000/docs"
    echo "  🏥 Health Check:     http://localhost:8000/health"
    echo ""
    echo "📊 Monitoring:"
    echo "  📈 Grafana:          http://localhost:3001 (admin/admin123)"
    echo "  📊 Prometheus:       http://localhost:9090"
    echo "  🔍 Jaeger:           http://localhost:16686"
    echo "  📋 Kibana:           http://localhost:5601"
    echo ""
    echo "💾 Storage:"
    echo "  🗄️  MinIO Console:    http://localhost:9001 (minioadmin/secure123)"
    echo "  🗃️  PostgreSQL:       localhost:5432 (pinn/secure123)"
    echo "  🔄 Redis:            localhost:6379"
    echo ""
    echo "🔧 Management:"
    echo "  📋 View logs:        docker-compose logs -f"
    echo "  🔄 Restart:          docker-compose restart"
    echo "  🛑 Stop:             docker-compose down"
    echo "  🧹 Clean:            docker-compose down -v"
}

# Stop services
stop_services() {
    print_status "Stopping PINN platform..."
    docker-compose down
    print_success "Platform stopped!"
}

# Clean up everything
clean_services() {
    print_status "Cleaning up PINN platform..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    print_success "Cleanup complete!"
}

# Show logs
show_logs() {
    local service=${1:-}
    
    if [ -z "$service" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f $service
    fi
}

# Main function
main() {
    echo "🧠 Open Source PINN Platform"
    echo "============================="
    echo ""
    
    case "${1:-start}" in
        "start"|"dev")
            check_prerequisites
            setup_environment
            start_services "dev"
            show_urls
            ;;
        "prod")
            check_prerequisites
            setup_environment
            start_services "prod"
            show_urls
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            start_services "dev"
            show_urls
            ;;
        "clean")
            clean_services
            ;;
        "logs")
            show_logs "${2:-}"
            ;;
        "status")
            check_service_health
            ;;
        "urls")
            show_urls
            ;;
        "check")
            check_prerequisites
            ;;
        *)
            echo "Usage: $0 [start|dev|prod|stop|restart|clean|logs|status|urls|check]"
            echo ""
            echo "Commands:"
            echo "  start/dev  - Start development environment (default)"
            echo "  prod       - Start production environment"
            echo "  stop       - Stop all services"
            echo "  restart    - Restart all services"
            echo "  clean      - Stop and remove all data"
            echo "  logs       - Show logs (optionally for specific service)"
            echo "  status     - Check service health"
            echo "  urls       - Show service URLs"
            echo "  check      - Check prerequisites only"
            echo ""
            echo "Examples:"
            echo "  $0 start           # Start development environment"
            echo "  $0 prod            # Start production environment"
            echo "  $0 logs api        # Show API service logs"
            echo "  $0 clean           # Clean up everything"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"