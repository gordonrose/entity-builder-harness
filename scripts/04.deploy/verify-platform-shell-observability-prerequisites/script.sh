#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-observability-prerequisites
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - sre
#   - security
#   kind: script
#   purpose: Fail closed before a platform-shell service update when the existing ECS cluster cannot emit the reviewed running-task alarm signal.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: github.workflow.deploy-platform-shell-staging
#     path: .github/workflows/deploy-platform-shell-staging.yml

PROFILE=""
REGION=""
CLUSTER=""
SERVICE=""

usage() {
  cat <<'EOF'
Usage: verify-platform-shell-observability-prerequisites/script.sh --region <aws-region> --cluster <ecs-cluster-name-or-arn> --service <ecs-service-name> [--profile <aws-profile>]

Reads ECS cluster settings and CloudWatch metric metadata only. It changes no AWS resource.
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --region)
      REGION="${2:-}"
      shift 2
      ;;
    --cluster)
      CLUSTER="${2:-}"
      shift 2
      ;;
    --service)
      SERVICE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$REGION" ] || [ -z "$CLUSTER" ] || [ -z "$SERVICE" ]; then
  echo "ERROR: --region, --cluster, and --service are required." >&2
  usage >&2
  exit 2
fi

AWS_ARGUMENTS=(--region "$REGION")
if [ -n "$PROFILE" ]; then
  AWS_ARGUMENTS+=(--profile "$PROFILE")
fi

container_insights_setting="$(
  aws ecs describe-clusters "${AWS_ARGUMENTS[@]}" \
    --clusters "$CLUSTER" \
    --include SETTINGS \
    --query "clusters[0].settings[?name=='containerInsights'].value | [0]" \
    --output text
)"

if [ "$container_insights_setting" != "enhanced" ]; then
  echo "ERROR: deployment blocked: ECS cluster must set containerInsights=enhanced before the running-task alarm is deployed; found ${container_insights_setting:-<none>}." >&2
  exit 1
fi

running_task_metric_count="$(
  aws cloudwatch list-metrics "${AWS_ARGUMENTS[@]}" \
    --namespace ECS/ContainerInsights \
    --metric-name RunningTaskCount \
    --dimensions "Name=ClusterName,Value=$CLUSTER" "Name=ServiceName,Value=$SERVICE" \
    --query "length(Metrics)" \
    --output text
)"

if ! [[ "$running_task_metric_count" =~ ^[0-9]+$ ]] || [ "$running_task_metric_count" -lt 1 ]; then
  echo "ERROR: deployment blocked: ECS/ContainerInsights RunningTaskCount is not yet published for the selected cluster and service." >&2
  exit 1
fi

printf '%s\n' "Platform-shell observability prerequisite check passed."
