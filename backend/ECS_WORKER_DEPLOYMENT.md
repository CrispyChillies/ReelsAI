# Deploy Video Worker to AWS ECS/Fargate

This guide shows how to run the video worker as a separate containerized service using AWS ECS.

## Prerequisites
- Docker installed locally
- AWS CLI configured
- ECR repository created

## Step 1: Create Dockerfile for Worker

Create `Dockerfile.worker`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run worker
CMD ["python", "manage.py", "run_video_worker"]
```

## Step 2: Build and Push to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name reelsai-video-worker

# Login to ECR
aws ecr get-login-password --region ap-southeast-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com

# Build image
docker build -f Dockerfile.worker -t reelsai-video-worker .

# Tag image
docker tag reelsai-video-worker:latest <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/reelsai-video-worker:latest

# Push to ECR
docker push <account-id>.dkr.ecr.ap-southeast-1.amazonaws.com/reelsai-video-worker:latest
```

## Step 3: Create ECS Task Definition

Go to AWS ECS Console:
1. Create new Task Definition (Fargate)
2. Task memory: 1GB
3. Task CPU: 0.5 vCPU
4. Add container:
   - Image: Your ECR image URI
   - Memory: 1GB
   - Environment variables: All your .env variables

## Step 4: Create ECS Service

1. Create ECS Cluster (if not exists)
2. Create Service:
   - Launch type: Fargate
   - Task definition: Your worker task
   - Number of tasks: 1 (or more for parallel processing)
   - VPC and security groups

## Step 5: Monitor

View logs in CloudWatch Logs Groups
