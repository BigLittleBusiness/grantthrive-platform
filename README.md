# GrantThrive Platform (Backend)

Flask backend and AWS infrastructure code for GrantThrive.

This repository contains:

- API application code in app
- deployment scripts in scripts
- backend infrastructure Terraform in terraform

## Local development

Prerequisites:

- Python 3.11+
- Node and pnpm (only if you also run frontend locally)

Setup and run:

```bash
./setup.sh
source venv/bin/activate
flask run
```

Health check:

```bash
curl http://localhost:5000/api/health
```

## UAT deployment

1) Apply infrastructure:

```bash
cd terraform
terraform init
terraform plan -var-file=terraform.uat.tfvars
terraform apply -var-file=terraform.uat.tfvars
```

2) Deploy backend app:

```bash
cd ..
AWS_PROFILE=biglittle ./scripts/deploy.sh uat
```

3) Validate:

```bash
curl -i https://api.uat.grantthrive.com/api/health
```

## Production deployment

Infrastructure:

```bash
cd terraform
terraform plan -var-file=terraform.prod.tfvars
terraform apply -var-file=terraform.prod.tfvars
```

Application:

```bash
cd ..
AWS_PROFILE=biglittle ./scripts/deploy.sh prod
```

## Deployment behavior and current alignment

- Backend image is built for linux/amd64 and pushed to ECR by scripts/deploy.sh.
- scripts/deploy.sh bootstraps the target logical database and runs `flask db upgrade` before forcing ECS deployment.
- ECS service update is forced by scripts/deploy.sh and waits for service stability with status output.
- UAT API endpoint is https://api.uat.grantthrive.com.
- Production API endpoint is https://api.grantthrive.com.
- CORS allowlist now includes FRONTEND_BASE_URL from ECS environment, so UAT frontend origin is accepted.
- S3 upload bucket is injected into ECS via AWS_S3_BUCKET and used by file upload and retrieval routes.
- UAT and production share the UAT-owned ALB and RDS instance, while ECS, Redis, ECR, secrets, and document buckets remain environment-specific.

Validate deployed APIs:

```bash
curl -i -H 'Origin: https://app.uat.grantthrive.com' https://api.uat.grantthrive.com/api/health
curl -i -H 'Origin: https://app.grantthrive.com' https://api.grantthrive.com/api/health
```

For fresh environments, do not rely on `/api/health` alone. It checks database connectivity, but registration also requires the Alembic schema. The deploy script now runs migrations automatically.

## Terraform references

Use the Terraform README for full infra details and operational commands:

- terraform/README.md

Related docs in this repo:

- DEPLOY_AWS.md
- AWS_EC2_BACKEND.md
- AWS_RDS_SETUP.md
- AWS_MONITORING.md
