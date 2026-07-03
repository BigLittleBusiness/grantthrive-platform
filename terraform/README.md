# GrantThrive Backend Terraform

Provisions backend infrastructure for GrantThrive: ECS Fargate, ALB routing, RDS PostgreSQL, Redis, ECR, Secrets Manager, Route 53, and S3 document buckets.

## Current Environments

| Component | UAT | Production |
|-----------|-----|------------|
| API URL | `https://api.uat.grantthrive.com` | `https://api.grantthrive.com` |
| Frontend origin for CORS | `https://app.uat.grantthrive.com` | `https://app.grantthrive.com` |
| ECS cluster | `granthrive-uat-cluster` | `granthrive-prod-cluster` |
| ECS service | `granthrive-uat-uat` | `granthrive-prod-prod` |
| ECR repo | `granthrive-uat/backend` | `granthrive-prod/backend` |
| Image tag | `uat-latest` | `prod-latest` |
| Database | `granthrive_uat` | `granthrive` |
| Document bucket | `grantthrive-documents-uat` | `grantthrive-documents-prod` |

## Shared Resources

UAT owns the shared infrastructure:

- VPC and private/public subnets
- Public ALB and HTTPS listener
- RDS PostgreSQL instance

Production has separate ECS, Redis, ECR, S3 document bucket, Secrets Manager secrets, and target group resources. Production reuses the UAT-owned ALB and RDS instance.

Important implementation details:

- PROD reads the UAT-owned production `DATABASE_URL` secret so it uses the correct shared RDS password.
- PROD Terraform creates a security group ingress rule allowing PROD ECS tasks to connect to the UAT-owned RDS security group.
- UAT and PROD use separate logical PostgreSQL databases on the shared RDS instance.

## Prerequisites

- AWS account: `547154049278`
- AWS region: `ap-southeast-2`
- AWS profile: `biglittle`
- Terraform >= 1.6
- AWS CLI v2
- Docker with `docker buildx`

Backend ACM certificate:

- Region: `ap-southeast-2`
- Used by the ALB HTTPS listener
- Must cover `api.grantthrive.com` and `api.uat.grantthrive.com`

## Terraform Workflow

Remote state is required before running this repo. If the state buckets/table do not exist, bootstrap them first:

```bash
cd ../../grantthrive-state-management
AWS_PROFILE=biglittle terraform init
AWS_PROFILE=biglittle terraform apply
```

Initialize:

```bash
cd grantthrive-platform/terraform
AWS_PROFILE=biglittle terraform init
```

Apply UAT first because it owns shared RDS and ALB:

```bash
AWS_PROFILE=biglittle terraform workspace select uat || AWS_PROFILE=biglittle terraform workspace new uat
AWS_PROFILE=biglittle terraform apply -var-file=terraform.uat.tfvars
```

Apply production after UAT:

```bash
AWS_PROFILE=biglittle terraform workspace select prod || AWS_PROFILE=biglittle terraform workspace new prod
AWS_PROFILE=biglittle terraform apply -var-file=terraform.prod.tfvars
```

Useful outputs:

```bash
AWS_PROFILE=biglittle terraform output
```

## Application Deployment

Deploy UAT:

```bash
cd grantthrive-platform
AWS_PROFILE=biglittle ./scripts/deploy.sh uat --region ap-southeast-2
```

Deploy production:

```bash
cd grantthrive-platform
AWS_PROFILE=biglittle ./scripts/deploy.sh prod --region ap-southeast-2
```

The deploy script:

1. Reads ECS cluster, service, and ECR repo from Terraform outputs.
2. Builds and pushes a linux/amd64 Docker image with `docker buildx`.
3. Runs a one-off ECS task to create the target logical database if missing.
4. Runs `flask db upgrade` in a one-off ECS task.
5. Runs `flask seed-test-accounts` in a one-off ECS task when the deploy script is called with `--seed-test-accounts`.
6. Forces a new ECS service deployment.
7. Polls ECS service stability with status output.
8. Prints recent ECS events and CloudWatch logs if the service does not stabilize.

Options:

```bash
AWS_PROFILE=biglittle ./scripts/deploy.sh uat --region ap-southeast-2 --skip-build
AWS_PROFILE=biglittle ./scripts/deploy.sh prod --region ap-southeast-2 --skip-build
AWS_PROFILE=biglittle ./scripts/deploy.sh prod --region ap-southeast-2 --tag release-20260602
AWS_PROFILE=biglittle ./scripts/deploy.sh prod --region ap-southeast-2 --skip-db-bootstrap
AWS_PROFILE=biglittle ./scripts/deploy.sh prod --region ap-southeast-2 --skip-migrations
AWS_PROFILE=biglittle ./scripts/deploy.sh uat --region ap-southeast-2 --seed-test-accounts
```

## Database Bootstrap

Fresh RDS creates only the initial database. The deploy script handles missing logical databases by running an ECS task with the same task definition and private network settings as the service.

The bootstrap task:

- Reads `DATABASE_URL` from Secrets Manager through ECS secret injection.
- Connects to the `postgres` maintenance database.
- Creates the target database from the URL path if it does not exist.

This prevents the ALB health check from failing with `503` because `/api/health` checks database connectivity.

After bootstrap, the deploy script runs:

```bash
flask db upgrade
```

This is required for fresh databases. `/api/health` can pass with only `SELECT 1`, while registration and other application flows still fail if the Alembic schema has not been applied.

## Test Account Seeding

The backend includes a Flask CLI command:

```bash
flask --app manage:app seed-test-accounts
```

It creates or repairs:

- Test council: `GrantThrive Test Council`
- Council admin: `council_admin_test@grantthrive.com`
- Council staff: `council_staff_test@grantthrive.com`

The operation is idempotent. Existing test users are updated in place with the expected role, council, active/approved flags, and password hash, so repeat CI/CD runs do not fail because of duplicate rows.

GitHub Actions runs this automatically for both UAT and Production.

Optional GitHub Actions settings:

```text
GT_TEST_ADMIN_PASSWORD      # secret
GT_TEST_STAFF_PASSWORD      # secret
GT_TEST_ADMIN_EMAIL         # variable
GT_TEST_STAFF_EMAIL         # variable
```

## Runtime Secrets

Secrets are stored in Secrets Manager and injected into ECS task definitions.

Key points:

- `FIELD_ENCRYPTION_KEY` and `FIELD_HMAC_KEY` are stored as base64-encoded 32-byte values.
- `DATABASE_URL` points to the correct logical database for the environment.
- `REDIS_URL` is environment-specific.
- `FRONTEND_BASE_URL` is a plain ECS environment variable and drives CORS.

## Validation

Backend health:

```bash
curl -i https://api.uat.grantthrive.com/api/health
curl -i https://api.grantthrive.com/api/health
```

Expected response:

```json
{"database":"ok","domain":"grantthrive.com","service":"grantthrive-backend","status":"ok"}
```

CORS checks:

```bash
curl -i -H 'Origin: https://app.uat.grantthrive.com' https://api.uat.grantthrive.com/api/health
curl -i -H 'Origin: https://app.grantthrive.com' https://api.grantthrive.com/api/health
```

Expected headers include the matching `access-control-allow-origin`.

Preflight:

```bash
curl -i -X OPTIONS \
  -H 'Origin: https://app.grantthrive.com' \
  -H 'Access-Control-Request-Method: GET' \
  https://api.grantthrive.com/api/health
```

ECS status:

```bash
AWS_PROFILE=biglittle aws ecs describe-services \
  --region ap-southeast-2 \
  --cluster granthrive-prod-cluster \
  --services granthrive-prod-prod \
  --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount,rollout:deployments[0].rolloutState}'
```

Logs:

```bash
AWS_PROFILE=biglittle aws logs tail /ecs/granthrive-uat/backend --region ap-southeast-2 --since 20m --format short
AWS_PROFILE=biglittle aws logs tail /ecs/granthrive-prod/backend --region ap-southeast-2 --since 20m --format short
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| ECS waiter takes too long | ALB health checks are failing | Use service events and CloudWatch logs from deploy script output |
| ALB returns `503` | No healthy ECS targets | Check `/api/health`, database existence, and DB security group access |
| `CannotPullContainerError` | Image tag missing in ECR | Run deploy script without `--skip-build` |
| Field key errors in logs | Secret value is not valid base64-decoded 32 bytes | Re-apply Terraform after current key-generation fix |
| CORS failure | `FRONTEND_BASE_URL` mismatch | Check environment tfvars and redeploy ECS |
| PROD DB connection failure | PROD ECS cannot access shared UAT RDS or wrong DB password | Apply PROD Terraform to add shared DB SG rule and shared `DATABASE_URL` |

## State

Remote state:

- Bucket: `grantthrive-terraform-state-backend-547154049278`
- Lock table: `grantthrive-terraform-locks`
- Region: `ap-southeast-2`
- Backend config file: `backend.tf`

This repo uses Terraform workspaces. State is stored in the backend state bucket using Terraform's default workspace prefix:

| Workspace | S3 object |
|-----------|-----------|
| `uat` | `env:/uat/terraform.tfstate` |
| `prod` | `env:/prod/terraform.tfstate` |

Do not run this stack from the default workspace. Always select `uat` or `prod` before `plan`, `apply`, `destroy`, or `state` commands.

Useful state commands:

```bash
AWS_PROFILE=biglittle terraform workspace list
AWS_PROFILE=biglittle terraform workspace select uat
AWS_PROFILE=biglittle terraform state list
AWS_PROFILE=biglittle aws s3api list-object-versions \
  --bucket grantthrive-terraform-state-backend-547154049278 \
  --prefix 'env:/uat/terraform.tfstate'
```

If Terraform reports a stale lock, first verify no apply is running. Then prefer:

```bash
AWS_PROFILE=biglittle terraform force-unlock <LOCK_ID>
```

The state-management repo documents the shared buckets, lock table, and recovery process:

```bash
../../grantthrive-state-management/README.md
```
