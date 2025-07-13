#!/bin/bash

# Deploy PINN Platform Infrastructure
set -e

# Configuration
PROJECT_NAME="pinn-deepxde-platform"
ENVIRONMENT="prod"
REGION="us-east-1"
STACK_NAME="${PROJECT_NAME}-infrastructure"

echo "Deploying PINN Platform Infrastructure..."
echo "Project: ${PROJECT_NAME}"
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo "Stack: ${STACK_NAME}"

# Check if we have required parameters
if [ -z "$VPC_ID" ]; then
    echo "Error: VPC_ID environment variable is required"
    echo "Please set VPC_ID to your VPC ID"
    echo "Example: export VPC_ID=vpc-12345678"
    exit 1
fi

if [ -z "$PRIVATE_SUBNET_IDS" ]; then
    echo "Error: PRIVATE_SUBNET_IDS environment variable is required"
    echo "Please set PRIVATE_SUBNET_IDS to comma-separated subnet IDs"
    echo "Example: export PRIVATE_SUBNET_IDS=subnet-12345678,subnet-87654321"
    exit 1
fi

# Get DynamoDB table name and S3 bucket from Serverless outputs
echo "Getting Serverless stack outputs..."
DYNAMODB_TABLE=$(aws cloudformation describe-stacks \
    --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
    --query 'Stacks[0].Outputs[?OutputKey==`StateTableName`].OutputValue' \
    --output text \
    --region ${REGION})

S3_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name ${PROJECT_NAME}-${ENVIRONMENT} \
    --query 'Stacks[0].Outputs[?OutputKey==`ModelsBucketName`].OutputValue' \
    --output text \
    --region ${REGION})

if [ -z "$DYNAMODB_TABLE" ] || [ -z "$S3_BUCKET" ]; then
    echo "Error: Could not get DynamoDB table or S3 bucket from Serverless stack"
    echo "Please ensure the Serverless stack is deployed first with 'serverless deploy'"
    exit 1
fi

echo "DynamoDB Table: ${DYNAMODB_TABLE}"
echo "S3 Bucket: ${S3_BUCKET}"

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file infrastructure/ecs-training-service.yml \
    --stack-name ${STACK_NAME} \
    --parameter-overrides \
        ProjectName=${PROJECT_NAME} \
        Environment=${ENVIRONMENT} \
        VpcId=${VPC_ID} \
        PrivateSubnetIds=${PRIVATE_SUBNET_IDS} \
        DynamoDBTableName=${DYNAMODB_TABLE} \
        S3ModelsBucketName=${S3_BUCKET} \
    --capabilities CAPABILITY_IAM \
    --region ${REGION}

echo "Infrastructure deployment completed!"

# Get stack outputs
echo "Getting stack outputs..."
ECS_CLUSTER=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ECSClusterName`].OutputValue' \
    --output text \
    --region ${REGION})

ECR_URI=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ECRRepositoryURI`].OutputValue' \
    --output text \
    --region ${REGION})

echo "ECS Cluster: ${ECS_CLUSTER}"
echo "ECR Repository: ${ECR_URI}"

# Create CloudWatch Dashboard
echo "Creating CloudWatch Dashboard..."
aws cloudwatch put-dashboard \
    --dashboard-name "PINNPlatform-${ENVIRONMENT}" \
    --dashboard-body file://monitoring/cloudwatch_dashboard.json \
    --region ${REGION}

echo "CloudWatch Dashboard created: PINNPlatform-${ENVIRONMENT}"

# Set up CloudWatch Alarms
echo "Setting up CloudWatch Alarms..."

# High error rate alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "PINNPlatform-HighErrorRate" \
    --alarm-description "High error rate in PINN platform" \
    --metric-name "FailedWorkflows24h" \
    --namespace "PINNPlatform" \
    --statistic "Sum" \
    --period 3600 \
    --evaluation-periods 1 \
    --threshold 5 \
    --comparison-operator "GreaterThanThreshold" \
    --region ${REGION}

# High cost alarm
aws cloudwatch put-metric-alarm \
    --alarm-name "PINNPlatform-HighCost" \
    --alarm-description "High daily cost in PINN platform" \
    --metric-name "EstimatedDailyCost" \
    --namespace "PINNPlatform" \
    --statistic "Average" \
    --period 3600 \
    --evaluation-periods 1 \
    --threshold 100 \
    --comparison-operator "GreaterThanThreshold" \
    --region ${REGION}

echo "CloudWatch Alarms created"

# Output important information
echo ""
echo "=== DEPLOYMENT SUMMARY ==="
echo "Project: ${PROJECT_NAME}"
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo ""
echo "Resources Created:"
echo "- ECS Cluster: ${ECS_CLUSTER}"
echo "- ECR Repository: ${ECR_URI}"
echo "- DynamoDB Table: ${DYNAMODB_TABLE}"
echo "- S3 Bucket: ${S3_BUCKET}"
echo ""
echo "Next Steps:"
echo "1. Build and push container: ./scripts/deploy-containers.sh"
echo "2. Test the API endpoints"
echo "3. Monitor via CloudWatch Dashboard: PINNPlatform-${ENVIRONMENT}"
echo ""
echo "Infrastructure deployment completed successfully!"