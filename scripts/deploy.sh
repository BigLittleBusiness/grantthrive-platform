#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/terraform"

usage() {
  cat <<EOF
Usage:
  scripts/deploy.sh <prod|uat|staging> [--tag <image_tag>] [--dockerfile <path>] [--task-definition <arn_or_family_revision>] [--region <aws_region>] [--skip-build] [--skip-db-bootstrap] [--skip-migrations]

Examples:
  scripts/deploy.sh prod
  scripts/deploy.sh uat
  scripts/deploy.sh staging
  scripts/deploy.sh prod --tag release-20260525
  scripts/deploy.sh prod --task-definition granthrive-prod:42
EOF
}

if [[ $# -lt 1 ]]; then
  usage
  exit 1
fi

TARGET_ENV="$1"
shift

TASK_DEFINITION=""
AWS_REGION=""
DOCKERFILE_PATH="Dockerfile"
IMAGE_TAG=""
SKIP_BUILD="false"
SKIP_DB_BOOTSTRAP="false"
SKIP_MIGRATIONS="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task-definition)
      TASK_DEFINITION="$2"
      shift 2
      ;;
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --dockerfile)
      DOCKERFILE_PATH="$2"
      shift 2
      ;;
    --tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD="true"
      shift
      ;;
    --skip-db-bootstrap)
      SKIP_DB_BOOTSTRAP="true"
      shift
      ;;
    --skip-migrations)
      SKIP_MIGRATIONS="true"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

case "$TARGET_ENV" in
  prod)
    SERVICE_OUTPUT_KEY="prod_service_name"
    : "${IMAGE_TAG:=prod-latest}"
    ;;
  uat)
    SERVICE_OUTPUT_KEY="uat_service_name"
    : "${IMAGE_TAG:=uat-latest}"
    ;;
  staging)
    SERVICE_OUTPUT_KEY="uat_service_name"
    : "${IMAGE_TAG:=uat-latest}"
    TARGET_ENV="uat"
    ;;
  *)
    echo "Environment must be 'prod', 'uat', or 'staging'." >&2
    usage
    exit 1
    ;;
esac

cd "$ROOT_DIR"

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI is required for backend deployment." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to build and push backend images." >&2
  exit 1
fi

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform is required to read backend infrastructure outputs." >&2
  exit 1
fi

if terraform -chdir="$TF_DIR" workspace list | sed 's/*//g' | tr -d ' ' | grep -qx "$TARGET_ENV"; then
  terraform -chdir="$TF_DIR" workspace select "$TARGET_ENV" >/dev/null
else
  terraform -chdir="$TF_DIR" workspace new "$TARGET_ENV" >/dev/null
fi

CLUSTER_NAME="$(terraform -chdir="$TF_DIR" output -raw ecs_cluster_name)"
SERVICE_NAME="$(terraform -chdir="$TF_DIR" output -raw "$SERVICE_OUTPUT_KEY")"
ECR_REPOSITORY_URL="$(terraform -chdir="$TF_DIR" output -raw ecr_repository_url)"

AWS_ARGS=()
if [[ -n "$AWS_REGION" ]]; then
  AWS_ARGS+=(--region "$AWS_REGION")
fi

run_aws() {
  if [[ ${#AWS_ARGS[@]} -gt 0 ]]; then
    aws "${AWS_ARGS[@]}" "$@"
  else
    aws "$@"
  fi
}

print_service_diagnostics() {
  echo "ECS service did not become stable. Recent service events:" >&2
  run_aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --query 'services[0].events[0:10].[createdAt,message]' \
    --output table >&2 || true

  echo "Recent backend logs:" >&2
  run_aws logs tail "/ecs/granthrive-${TARGET_ENV}/backend" \
    --since 20m \
    --format short >&2 || true
}

wait_for_service_stable() {
  local attempts=24
  local sleep_seconds=15
  local desired running pending rollout deployment_count

  for ((attempt = 1; attempt <= attempts; attempt++)); do
    desired="$(run_aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].desiredCount' --output text)"
    running="$(run_aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].runningCount' --output text)"
    pending="$(run_aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].pendingCount' --output text)"
    rollout="$(run_aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].deployments[0].rolloutState' --output text)"
    deployment_count="$(run_aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'length(services[0].deployments)' --output text)"

    if [[ "$running" == "$desired" && "$pending" == "0" && "$rollout" == "COMPLETED" && "$deployment_count" == "1" ]]; then
      return 0
    fi

    echo "Waiting for ECS stability (${attempt}/${attempts}): desired=${desired}, running=${running}, pending=${pending}, rollout=${rollout}"
    sleep "$sleep_seconds"
  done

  print_service_diagnostics
  return 1
}

bootstrap_database() {
  local task_definition="$1"
  local network_file overrides_file task_arn exit_code

  network_file="$(mktemp)"
  overrides_file="$(mktemp)"

  run_aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --query 'services[0].networkConfiguration' \
    --output json >"$network_file"

  cat >"$overrides_file" <<'JSON'
{
  "containerOverrides": [
    {
      "name": "backend",
      "command": [
        "python",
        "-c",
        "import os, psycopg2; from urllib.parse import urlparse, unquote; u=urlparse(os.environ['DATABASE_URL']); db=(u.path or '/').lstrip('/'); conn=psycopg2.connect(host=u.hostname, port=u.port or 5432, user=unquote(u.username), password=unquote(u.password), dbname='postgres'); conn.set_isolation_level(0); cur=conn.cursor(); cur.execute('SELECT 1 FROM pg_database WHERE datname=%s', (db,)); exists=cur.fetchone(); cur.execute('CREATE DATABASE \"{}\"'.format(db.replace('\"', '\"\"'))) if not exists else None; print(('exists ' if exists else 'created ') + db); cur.close(); conn.close()"
      ]
    }
  ]
}
JSON

  echo "Bootstrapping database for ${TARGET_ENV} using ${task_definition}"
  task_arn="$(run_aws ecs run-task \
    --cluster "$CLUSTER_NAME" \
    --task-definition "$task_definition" \
    --launch-type FARGATE \
    --network-configuration "file://${network_file}" \
    --overrides "file://${overrides_file}" \
    --query 'tasks[0].taskArn' \
    --output text)"

  rm -f "$network_file" "$overrides_file"

  if [[ -z "$task_arn" || "$task_arn" == "None" ]]; then
    echo "Database bootstrap task was not started." >&2
    return 1
  fi

  run_aws ecs wait tasks-stopped --cluster "$CLUSTER_NAME" --tasks "$task_arn"
  exit_code="$(run_aws ecs describe-tasks \
    --cluster "$CLUSTER_NAME" \
    --tasks "$task_arn" \
    --query 'tasks[0].containers[0].exitCode' \
    --output text)"

  if [[ "$exit_code" != "0" ]]; then
    echo "Database bootstrap failed for task ${task_arn} with exit code ${exit_code}." >&2
    print_service_diagnostics
    return 1
  fi
}

run_migrations() {
  local task_definition="$1"
  local network_file overrides_file task_arn exit_code

  network_file="$(mktemp)"
  overrides_file="$(mktemp)"

  run_aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --query 'services[0].networkConfiguration' \
    --output json >"$network_file"

  cat >"$overrides_file" <<'JSON'
{
  "containerOverrides": [
    {
      "name": "backend",
      "command": ["flask", "db", "upgrade"]
    }
  ]
}
JSON

  echo "Running database migrations for ${TARGET_ENV} using ${task_definition}"
  task_arn="$(run_aws ecs run-task \
    --cluster "$CLUSTER_NAME" \
    --task-definition "$task_definition" \
    --launch-type FARGATE \
    --network-configuration "file://${network_file}" \
    --overrides "file://${overrides_file}" \
    --query 'tasks[0].taskArn' \
    --output text)"

  rm -f "$network_file" "$overrides_file"

  if [[ -z "$task_arn" || "$task_arn" == "None" ]]; then
    echo "Migration task was not started." >&2
    return 1
  fi

  run_aws ecs wait tasks-stopped --cluster "$CLUSTER_NAME" --tasks "$task_arn"
  exit_code="$(run_aws ecs describe-tasks \
    --cluster "$CLUSTER_NAME" \
    --tasks "$task_arn" \
    --query 'tasks[0].containers[0].exitCode' \
    --output text)"

  if [[ "$exit_code" != "0" ]]; then
    echo "Migration task failed for ${task_arn} with exit code ${exit_code}." >&2
    print_service_diagnostics
    return 1
  fi
}

if [[ "$SKIP_BUILD" != "true" ]]; then
  if [[ ! -f "$ROOT_DIR/$DOCKERFILE_PATH" ]]; then
    echo "Dockerfile not found at: $DOCKERFILE_PATH" >&2
    exit 1
  fi

  ECR_REGISTRY="${ECR_REPOSITORY_URL%/*}"
  IMAGE_URI="${ECR_REPOSITORY_URL}:${IMAGE_TAG}"

  echo "Logging into ECR registry: ${ECR_REGISTRY}"
  run_aws ecr get-login-password | docker login --username AWS --password-stdin "$ECR_REGISTRY"

  echo "Building backend image: ${IMAGE_URI}"
  if docker buildx version >/dev/null 2>&1; then
    echo "Building and pushing linux/amd64 image for ECS"
    docker buildx build \
      --platform linux/amd64 \
      -f "$DOCKERFILE_PATH" \
      -t "$IMAGE_URI" \
      --push \
      "$ROOT_DIR"
  else
    echo "docker buildx is required to publish linux/amd64 images for ECS." >&2
    exit 1
  fi
fi

if [[ "$SKIP_DB_BOOTSTRAP" != "true" ]]; then
  SERVICE_TASK_DEFINITION="${TASK_DEFINITION:-$(run_aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].taskDefinition' --output text)}"
  bootstrap_database "$SERVICE_TASK_DEFINITION"
fi

if [[ "$SKIP_MIGRATIONS" != "true" ]]; then
  SERVICE_TASK_DEFINITION="${SERVICE_TASK_DEFINITION:-${TASK_DEFINITION:-$(run_aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].taskDefinition' --output text)}}"
  run_migrations "$SERVICE_TASK_DEFINITION"
fi

if [[ -n "$TASK_DEFINITION" ]]; then
  run_aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --task-definition "$TASK_DEFINITION" \
    --force-new-deployment >/dev/null
else
  run_aws ecs update-service \
    --cluster "$CLUSTER_NAME" \
    --service "$SERVICE_NAME" \
    --force-new-deployment >/dev/null
fi

wait_for_service_stable

echo "Backend deployment completed: ${TARGET_ENV}"
echo "Cluster: ${CLUSTER_NAME}"
echo "Service: ${SERVICE_NAME}"
if [[ "$SKIP_BUILD" != "true" ]]; then
  echo "Image pushed: ${ECR_REPOSITORY_URL}:${IMAGE_TAG}"
fi
