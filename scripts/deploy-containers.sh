#!/bin/bash

# Deploy PINN Training Container to ECR
set -e

# Configuration
PROJECT_NAME="pinn-deepxde-platform"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_NAME="pinn-trainer"
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO_NAME}"

echo "Deploying PINN Training Container..."
echo "Account ID: ${ACCOUNT_ID}"
echo "Region: ${REGION}"
echo "ECR URI: ${ECR_URI}"

# Create ECR repository if it doesn't exist
echo "Creating ECR repository..."
aws ecr describe-repositories --repository-names ${ECR_REPO_NAME} --region ${REGION} 2>/dev/null || \
aws ecr create-repository --repository-name ${ECR_REPO_NAME} --region ${REGION}

# Get ECR login token
echo "Logging into ECR..."
aws ecr get-login-password --region ${REGION} | docker login --username AWS --password-stdin ${ECR_URI}

# Build Docker image
echo "Building Docker image..."
cd container/pinn_training_service
docker build -t ${ECR_REPO_NAME}:latest .

# Tag image for ECR
echo "Tagging image..."
docker tag ${ECR_REPO_NAME}:latest ${ECR_URI}:latest
docker tag ${ECR_REPO_NAME}:latest ${ECR_URI}:$(date +%Y%m%d-%H%M%S)

# Push image to ECR
echo "Pushing image to ECR..."
docker push ${ECR_URI}:latest
docker push ${ECR_URI}:$(date +%Y%m%d-%H%M%S)

echo "Container deployment completed successfully!"
echo "Image URI: ${ECR_URI}:latest"

# Return to root directory
cd ../..

# Update ECS service to use new image (if service exists)
echo "Checking for existing ECS service..."
if aws ecs describe-services --cluster ${PROJECT_NAME}-prod-cluster --services ${PROJECT_NAME}-pinn-training --region ${REGION} 2>/dev/null; then
    echo "Updating ECS service with new image..."
    aws ecs update-service \
        --cluster ${PROJECT_NAME}-prod-cluster \
        --service ${PROJECT_NAME}-pinn-training \
        --force-new-deployment \
        --region ${REGION}
    echo "ECS service update initiated"
else
    echo "ECS service not found - will be created during infrastructure deployment"
fi

echo "Container deployment script completed!"