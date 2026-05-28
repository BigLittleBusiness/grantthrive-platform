#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_DIR="$ROOT_DIR/terraform"

usage() {
  cat <<EOF
Usage:
  scripts/deploy.sh <prod|uat|staging> [--tag <image_tag>] [--dockerfile <path>] [--task-definition <arn_or_family_revision>] [--region <aws_region>] [--skip-build]

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

run_aws ecs wait services-stable \
  --cluster "$CLUSTER_NAME" \
  --services "$SERVICE_NAME"

echo "Backend deployment completed: ${TARGET_ENV}"
echo "Cluster: ${CLUSTER_NAME}"
echo "Service: ${SERVICE_NAME}"
if [[ "$SKIP_BUILD" != "true" ]]; then
  echo "Image pushed: ${ECR_REPOSITORY_URL}:${IMAGE_TAG}"
fi
