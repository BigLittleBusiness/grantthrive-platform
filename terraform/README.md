# GrantThrive Backend Terraform

Provisions AWS backend infrastructure: VPC, ECS Fargate cluster, RDS PostgreSQL, ElastiCache Redis, ALB, ECR, and related services.

## Quick Overview

**Infrastructure per environment:**

| Component | Production | UAT |
|-----------|-----------|-----|
| **API Endpoint** | `https://api.grantthrive.com` | `https://api.uat.grantthrive.com` |
| **ECS Service** | `granthrive-uat-prod` | `granthrive-uat-uat` |
| **Database** | `granthrive` | `granthrive_uat` |
| **Container Image** | `prod-latest` | `uat-latest` |
| **Desired Tasks** | 0 (scaled down) | 1 (active) |

**Shared Infrastructure** (single instance):
- RDS PostgreSQL with multiple databases
- ElastiCache Redis cluster for sessions/cache
- ALB with HTTP→HTTPS redirect
- VPC with public/private subnets across 2 AZs
- ECR repository for backend Docker images

**Key Architecture**:
- Multi-environment on shared infrastructure (reduces costs)
- ECS Fargate for serverless container management
- RDS Multi-AZ for high availability
- Dynamic CORS configuration via `FRONTEND_BASE_URL` environment variable
- Environment variables injected by Terraform at task runtime

## Prerequisites

1. **AWS Configuration**:
   - Account ID: `547154049278`
   - Region: `ap-southeast-2`
   - Configure: `aws configure --profile biglittle`

2. **Tools**:
   - Terraform >= 1.6.0
   - AWS CLI >= 2.0
   - Docker with `docker buildx` for multi-platform image building

3. **ACM Certificate** (for HTTPS):
   - Must exist in `ap-southeast-2`
   - Required for ALB HTTPS listener
   - Update `alb_certificate_arn` in tfvars

4. **Remote State Setup** (required for first deployment):
   ```bash
   cd ../grantthrive-state-management
   terraform apply
   ```

## Standard Deployment

### Step 1: Initialize

```bash
cd grantthrive-platform/terraform
terraform init
# Answer 'yes' to migrate existing state if prompted
```

### Step 2: Plan

```bash
terraform plan -var-file=terraform.uat.tfvars
```

### Step 3: Apply

```bash
terraform apply -var-file=terraform.uat.tfvars
```

**Outputs** (used by deployment scripts and team):
- `ecs_cluster_name`: ECS cluster name (e.g., granthrive-uat-cluster)
- `uat_service_name`: UAT service name (e.g., granthrive-uat-uat)
- `ecr_repository_url`: ECR container registry URL
- `rds_endpoint`: PostgreSQL database endpoint
- `redis_endpoint`: Redis cache endpoint

## Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `environment` | Environment name | `uat` or `prod` |
| `alb_certificate_arn` | ACM certificate in ap-southeast-2 | `arn:aws:acm:ap-southeast-2:...` |
| `route53_zone_id` | Route 53 hosted zone ID | `Z09860173N0NGB56RP1JJ` |
| `frontend_base_url` | Frontend URL for CORS | `https://app.uat.grantthrive.com` |
| `aws_s3_bucket` | S3 bucket for file uploads | `grantthrive-documents-uat` |
| `uat_desired_count` | Number of UAT ECS tasks | `1` |

**Important**: The `FRONTEND_BASE_URL` environment variable is injected by Terraform and used by Flask-CORS to dynamically allow the frontend origin.

## State Management

Remote state in S3 with DynamoDB locking:
- Bucket: `grantthrive-terraform-state-backend-547154049278`
- Lock table: `grantthrive-terraform-locks`
- Region: `ap-southeast-2`

## Application Deployment

After infrastructure is created, build and deploy the backend:

```bash
cd ../../  # Go to grantthrive-platform root
./scripts/deploy.sh uat
```

Script performs:
1. Reads cluster/service/ECR details from terraform outputs
2. Logs into ECR registry
3. Builds Docker image with `docker buildx build --platform linux/amd64`
4. Pushes image to ECR with `uat-latest` tag
5. Updates ECS service with `force-new-deployment`
6. Waits for stable service state

Options:
```bash
./scripts/deploy.sh uat --skip-build    # Just update ECS service (reuse existing image)
./scripts/deploy.sh uat --tag release-1 # Custom image tag
```

## Cleanup

To destroy infrastructure:

```bash
# 1. Scale down ECS services
terraform apply -var-file=terraform.uat.tfvars -var="uat_desired_count=0"

# 2. Wait for tasks to stop (~2-3 minutes)
aws ecs describe-services \
  --cluster granthrive-uat-cluster \
  --services granthrive-uat-uat

# 3. Empty S3 bucket (required - Terraform cannot destroy non-empty bucket)
aws s3 rm s3://grantthrive-documents-uat --recursive 2>/dev/null || true

# 4. Destroy infrastructure
terraform destroy -var-file=terraform.uat.tfvars
```

## Common Issues

| Issue | Solution |
|-------|----------|
| ECS task not starting | Check logs: `aws logs tail /ecs/granthrive-uat/backend --follow` |
| Database connection refused | Verify RDS security group allows port 5432 from ECS security group |
| CORS errors from frontend | Ensure `FRONTEND_BASE_URL` matches frontend domain in tfvars |
| Image not found in ECR | Run `./scripts/deploy.sh uat` to build and push image |
| "Bucket not empty" on destroy | Run: `aws s3 rm s3://grantthrive-documents-uat --recursive` |

## Environment Variables (at Runtime)

ECS task definition injects these environment variables:

| Variable | Source | Purpose |
|----------|--------|---------|
| `FRONTEND_BASE_URL` | `terraform.uat.tfvars` | Flask-CORS allowed origin |
| `DATABASE_URL` | RDS connection | PostgreSQL connection |
| `REDIS_URL` | ElastiCache | Session/cache storage |
| `AWS_S3_BUCKET` | `terraform.uat.tfvars` | File upload destination |

## Database Initialization

After infrastructure is created, create databases and apply migrations:

```bash
# Step 1: Create granthrive_uat database
aws ecs run-task \
  --cluster granthrive-uat-cluster \
  --task-definition granthrive-uat-uat \
  --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}' \
  --overrides '{
    "containerOverrides": [{
      "name": "backend",
      "command": ["python", "-c", "import psycopg2; conn = psycopg2.connect(user=\"granthrive\", password=\"...\", host=\"rds-host\"); conn.set_isolation_level(0); cur = conn.cursor(); cur.execute(\"CREATE DATABASE granthrive_uat\"); cur.close(); conn.close()"]
    }]
  }'

# Step 2: Apply migrations
aws ecs run-task \
  --cluster granthrive-uat-cluster \
  --task-definition granthrive-uat-uat \
  --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}' \
  --overrides '{
    "containerOverrides": [{
      "name": "backend",
      "command": ["flask", "--app", "manage.py", "db", "upgrade"]
    }]
  }'
```

## Health Check

Verify backend is running:

```bash
# Via ALB endpoint
curl https://api.uat.grantthrive.com/api/health

# Or via AWS CLI
aws ecs describe-services \
  --cluster granthrive-uat-cluster \
  --services granthrive-uat-uat \
  --query 'services[0].deployments'
```

## File Structure

```
grantthrive-platform/terraform/
├── backend.tf              # Remote state S3 config
├── main.tf                 # Core infrastructure
├── variables.tf            # Variable definitions
├── locals.tf               # Local values
├── outputs.tf              # Output values
├── providers.tf            # AWS provider
├── versions.tf             # Version constraints
├── s3_app_bucket.tf        # S3 file upload bucket
├── terraform.uat.tfvars    # UAT config (ACTIVE)
└── README.md               # This file
```

## Documentation

- **Application**: See [../README.md](../README.md)
- **Frontend Terraform**: See [../GrantThrive-frontend/terraform/README.md](../GrantThrive-frontend/terraform/README.md)
3. Set `backend_image` for production and `uat_backend_image` for UAT.
4. Set `aws_s3_bucket` in your tfvars file. The backend now stores documents and generated reports in S3.
5. Keep `aws_s3_use_local_fallback = false` for AWS environments so uploads fail fast if S3 is misconfigured.
6. Run Terraform from this directory with the env-specific tfvars:

```bash
terraform init
terraform plan -var-file=terraform.prod.tfvars
terraform apply -var-file=terraform.prod.tfvars
```

5. Push the production image to the ECR repository from `terraform output ecr_repository_url`.
6. Push the UAT image to the same repository with a UAT tag, then update `uat_backend_image` or your deployment pipeline to point at that tag.

Manual deploy helper commands:

```bash
# Build + push image with prod-latest tag, then force rolling deploy
scripts/deploy.sh prod

# Build + push image with uat-latest (UAT) tag, then force rolling deploy
scripts/deploy.sh uat

# Build + push image with custom tag, then deploy
scripts/deploy.sh prod --tag release-20260525

# Skip image build/push and only trigger ECS redeploy
scripts/deploy.sh uat --skip-build

# Deploy a specific task definition revision to production
scripts/deploy.sh prod --task-definition granthrive-prod:42
```

If you want to redeploy only one environment, keep the infrastructure applied and update just that environment's image tag.

## Access

Use the outputs after apply to confirm the live endpoints:

- `terraform output api_url`
- `terraform output uat_api_url`

If Route 53 is connected, those domains will resolve directly. If not, point your DNS provider at the ALB DNS name shown in Terraform outputs and create the same hostnames there.

## Notes

- `route53_zone_id` is optional. If it is blank, Terraform will create the load balancer but skip DNS records.
- The stack expects an ACM certificate ARN for the backend ALB.
- `DATABASE_URL` and `REDIS_URL` are injected into ECS from Secrets Manager.
- `AWS_S3_BUCKET` and `AWS_REGION` are injected into ECS task environment variables.
- ECS task role includes S3 permissions (`s3:ListBucket`, `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`) scoped to `aws_s3_bucket`.
- The current stack keeps prod and UAT on one RDS instance but separates the database names and application secrets.
