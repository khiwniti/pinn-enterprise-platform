# PINN DeepXDE Platform Deployment Guide

This guide provides step-by-step instructions for deploying the complete serverless backend architecture for Physics-Informed Neural Networks with DeepXDE.

## Prerequisites

### Required Tools
- AWS CLI v2 configured with appropriate permissions
- Node.js 16+ and npm
- Python 3.9+
- Docker (for container builds)
- Serverless Framework

### AWS Permissions
Your AWS credentials need the following permissions:
- Lambda (create, update, invoke)
- API Gateway (create, update)
- DynamoDB (create, read, write)
- S3 (create, read, write)
- ECS/Fargate (create, run tasks)
- ECR (create repositories, push images)
- CloudFormation (create, update stacks)
- IAM (create roles, policies)
- CloudWatch (create dashboards, alarms)

### Network Requirements
- VPC with private subnets for ECS tasks
- Internet gateway for container image pulls
- NAT gateway for outbound internet access from private subnets

## Deployment Steps

### 1. Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt

# Install Serverless Framework globally
npm install -g serverless
```

### 2. Configure Environment Variables

```bash
# Set your AWS region
export AWS_REGION=us-east-1

# Set your VPC and subnet information
export VPC_ID=vpc-12345678
export PRIVATE_SUBNET_IDS=subnet-12345678,subnet-87654321

# Optional: Set custom project name
export PROJECT_NAME=pinn-deepxde-platform
```

### 3. Deploy Serverless Functions

```bash
# Deploy the main serverless stack
serverless deploy --stage prod

# This creates:
# - API Gateway endpoints
# - Lambda functions for coordination, analysis, inference
# - DynamoDB table for state management
# - S3 bucket for model storage
# - SQS queues for async processing
```

### 4. Build and Deploy Lambda Layers

```bash
# Build scientific computing and DeepXDE layers
./scripts/build-layers.sh

# This creates optimized Lambda layers with:
# - NumPy, SciPy, TensorFlow
# - DeepXDE and dependencies
```

### 5. Deploy ECS Infrastructure

```bash
# Deploy ECS cluster and training infrastructure
./scripts/deploy-infrastructure.sh

# This creates:
# - ECS Fargate cluster
# - Task definitions for PINN training
# - Auto-scaling configuration
# - Security groups and IAM roles
# - ECR repository for container images
```

### 6. Build and Deploy Training Container

```bash
# Build and push the PINN training container
./scripts/deploy-containers.sh

# This:
# - Builds Docker image with DeepXDE
# - Pushes to ECR repository
# - Updates ECS service (if exists)
```

### 7. Verify Deployment

```bash
# Test API health
curl https://your-api-gateway-url.amazonaws.com/prod/health

# List workflows
curl https://your-api-gateway-url.amazonaws.com/prod/pinn/workflows

# Check CloudWatch dashboard
# Navigate to CloudWatch > Dashboards > PINNPlatform-prod
```

## Configuration Options

### Serverless Configuration

Edit `serverless.yml` to customize:

```yaml
provider:
  region: us-east-1  # Change region
  timeout: 900       # Lambda timeout
  memory: 3008       # Lambda memory

custom:
  pythonRequirements:
    dockerizePip: true  # Use Docker for package builds
    slim: true          # Remove unnecessary files
```

### ECS Configuration

Edit `infrastructure/ecs-training-service.yml`:

```yaml
# Task resources
Cpu: 4096      # 4 vCPU
Memory: 16384  # 16 GB

# Auto-scaling
MaxCapacity: 10  # Maximum tasks
MinCapacity: 0   # Minimum tasks
```

### Training Configuration

Modify `container/pinn_training_service/app.py`:

```python
# Training parameters
max_epochs = 50000
learning_rate = 1e-3
batch_size = 1000

# GPU configuration
tf.config.experimental.set_memory_growth(gpu, True)
```

## Monitoring and Observability

### CloudWatch Dashboard

The deployment creates a comprehensive dashboard showing:
- Workflow statistics and success rates
- Training times by physics domain
- Inference latency metrics
- Resource utilization
- Cost estimates

### CloudWatch Alarms

Automatic alarms for:
- High error rates (>5 failures in 1 hour)
- High costs (>$100/day)
- Long training times
- Queue depth issues

### Logs

Access logs through CloudWatch:
```bash
# API logs
aws logs tail /aws/lambda/pinn-deepxde-platform-prod-api-coordinator --follow

# Training logs
aws logs tail /ecs/pinn-deepxde-platform-pinn-training --follow

# Analysis logs
aws logs tail /aws/lambda/pinn-deepxde-platform-prod-pinn-problem-analyzer --follow
```

## Cost Optimization

### Automatic Optimizations

The platform includes automatic cost optimizations:
- ECS auto-scaling based on queue depth
- Automatic cleanup of old models (30+ days)
- Spot instances for training workloads
- Lambda provisioned concurrency only when needed

### Manual Optimizations

1. **Adjust Training Resources**:
   ```yaml
   # Use smaller instances for simple problems
   InstanceType: ml.g4dn.large  # Instead of ml.g4dn.xlarge
   ```

2. **Optimize Lambda Memory**:
   ```yaml
   # Reduce memory for simple functions
   memory: 1024  # Instead of 3008
   ```

3. **Use Reserved Capacity**:
   - Purchase reserved instances for predictable workloads
   - Use Savings Plans for consistent usage

### Cost Monitoring

Monitor costs through:
- CloudWatch dashboard cost metrics
- AWS Cost Explorer
- AWS Budgets with alerts

## Troubleshooting

### Common Issues

1. **Lambda Timeout**:
   ```bash
   # Increase timeout in serverless.yml
   timeout: 900  # 15 minutes max
   ```

2. **ECS Task Failures**:
   ```bash
   # Check ECS logs
   aws ecs describe-tasks --cluster pinn-cluster --tasks task-id
   
   # Check container logs
   aws logs get-log-events --log-group-name /ecs/pinn-training
   ```

3. **Memory Issues**:
   ```bash
   # Increase ECS task memory
   Memory: 32768  # 32 GB
   
   # Or use larger instance types
   InstanceType: ml.p3.2xlarge
   ```

4. **Network Connectivity**:
   ```bash
   # Ensure NAT gateway exists
   aws ec2 describe-nat-gateways
   
   # Check security group rules
   aws ec2 describe-security-groups --group-ids sg-12345678
   ```

### Debug Mode

Enable debug logging:
```bash
# Set environment variable
export DEBUG=true

# Redeploy with debug enabled
serverless deploy --stage prod
```

### Performance Tuning

1. **GPU Optimization**:
   ```python
   # Enable mixed precision
   tf.keras.mixed_precision.set_global_policy('mixed_float16')
   
   # Optimize GPU memory
   tf.config.experimental.set_memory_growth(gpu, True)
   ```

2. **Training Optimization**:
   ```python
   # Use adaptive learning rates
   callbacks = [
       dde.callbacks.ReduceLROnPlateau(factor=0.8, patience=2000)
   ]
   
   # Progressive training
   model.compile("adam", lr=1e-3)
   model.train(epochs=10000)
   model.compile("L-BFGS")
   model.train()
   ```

## Security Considerations

### IAM Roles

The deployment creates least-privilege IAM roles:
- Lambda execution roles with minimal permissions
- ECS task roles with resource-specific access
- Cross-service access only where needed

### Network Security

- ECS tasks run in private subnets
- Security groups restrict access
- No public IP addresses on compute resources

### Data Protection

- S3 buckets with encryption at rest
- DynamoDB encryption enabled
- CloudWatch logs encrypted
- No sensitive data in environment variables

## Scaling Considerations

### Horizontal Scaling

- ECS auto-scaling based on queue depth
- Lambda concurrent execution limits
- SQS queue batching for efficiency

### Vertical Scaling

- Configurable ECS task resources
- Lambda memory allocation
- GPU instance types for training

### Geographic Scaling

Deploy in multiple regions:
```bash
# Deploy to additional regions
serverless deploy --stage prod --region eu-west-1
serverless deploy --stage prod --region ap-southeast-1
```

## Backup and Recovery

### Automated Backups

- DynamoDB point-in-time recovery enabled
- S3 versioning for model storage
- CloudFormation stack templates in version control

### Disaster Recovery

1. **Cross-region replication**:
   ```bash
   # Enable S3 cross-region replication
   aws s3api put-bucket-replication --bucket source-bucket --replication-configuration file://replication.json
   ```

2. **Database backup**:
   ```bash
   # Create DynamoDB backup
   aws dynamodb create-backup --table-name pinn-state-table --backup-name daily-backup
   ```

## Support and Maintenance

### Regular Maintenance

1. **Update Dependencies**:
   ```bash
   # Update Lambda layers monthly
   ./scripts/build-layers.sh
   
   # Update container images
   ./scripts/deploy-containers.sh
   ```

2. **Monitor Performance**:
   - Review CloudWatch metrics weekly
   - Analyze cost trends monthly
   - Update resource allocations as needed

3. **Security Updates**:
   - Update base container images
   - Review IAM permissions quarterly
   - Update TLS certificates

### Getting Help

- Check CloudWatch logs for error details
- Review AWS service health dashboard
- Consult AWS documentation for service limits
- Use AWS Support for infrastructure issues

## Next Steps

After successful deployment:

1. **Test the Platform**:
   ```bash
   # Run example problems
   python examples/heat_transfer_example.py
   
   # Run integration tests
   python -m pytest tests/test_api.py
   ```

2. **Customize for Your Use Case**:
   - Add new physics domains
   - Implement custom boundary conditions
   - Integrate with existing workflows

3. **Scale for Production**:
   - Set up monitoring alerts
   - Implement CI/CD pipelines
   - Add user authentication
   - Set up cost budgets

4. **Optimize Performance**:
   - Profile training workloads
   - Optimize network architectures
   - Implement caching strategies
   - Fine-tune resource allocation