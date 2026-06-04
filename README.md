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

## GitHub CI/CD

The active GitHub Actions workflow is:

- `.github/workflows/deploy-aws.yml`

The previous EC2 deployment workflow is retained for reference but disabled:

- `.github/workflows/deploy.legacy.disabled`

Branch triggers:

| Branch | Target environment | What runs |
|--------|--------------------|-----------|
| `staging` | UAT | Terraform apply, backend image build/push, database bootstrap, migrations, ECS deployment, health/CORS check |
| `main` | Production | Terraform apply, backend image build/push, database bootstrap, migrations, ECS deployment, health/CORS check |

Manual deployment is also available from GitHub Actions using `workflow_dispatch` with `target_env` set to `uat` or `prod`.

Required GitHub Actions secrets:

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

The workflow expects these files to be present in the repository:

```text
terraform/terraform.uat.tfvars
terraform/terraform.prod.tfvars
```

If either tfvars file is intentionally not committed, add a workflow step to generate it from GitHub secrets before `Terraform apply`.

## Terraform references

Terraform remote state is managed outside this repo by `../grantthrive-state-management`.

New developers should bootstrap or verify state access before running backend Terraform:

```bash
cd ../grantthrive-state-management
AWS_PROFILE=biglittle terraform init
AWS_PROFILE=biglittle terraform apply
```

Then initialize this repo's backend Terraform and select a workspace:

```bash
cd ../grantthrive-platform/terraform
AWS_PROFILE=biglittle terraform init
AWS_PROFILE=biglittle terraform workspace select uat || AWS_PROFILE=biglittle terraform workspace new uat
```

Use the Terraform README for full infra details and operational commands:

- terraform/README.md

Related docs in this repo:

- DEPLOY_AWS.md
- AWS_EC2_BACKEND.md
- AWS_RDS_SETUP.md
- AWS_MONITORING.md
