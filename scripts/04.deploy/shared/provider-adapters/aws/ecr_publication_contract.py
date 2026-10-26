#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.provider.aws.ecr-publication-contract
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.package-qualification
#   disciplines: [security, sre]
#   kind: script
#   purpose: Define the bounded ECR publication identity command contract used by both application package workflow owners.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.core-server-package-custody.validation
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/verify-workflow.py
import shlex

def publication_commands(local_image, tag_prefix, configuration_inputs):
    source='''set -euo pipefail
tag="PREFIX-${GITHUB_SHA::12}-run${GITHUB_RUN_ID}"
qualified_image="$(python3 scripts/04.deploy/lifecycle/40-package/package-custody-receipt/qualification.py verify --image LOCAL_IMAGE --receipt "$RUNNER_TEMP/qualified-image.json")"
docker tag "$qualified_image" "$ECR_URI:$tag"
docker push "$ECR_URI:$tag"
digest="$(aws ecr describe-images --repository-name "$ECR_REPOSITORY" --image-ids imageTag="$tag" --query 'imageDetails[0].imageDigest' --output text)"
[[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]
image="$ECR_URI@$digest"
docker pull "$image" >/dev/null
test "$(docker image inspect "$image" --format '{{.Id}}')" = "$qualified_image"
revision="$(docker image inspect "$image" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}')"
test "$revision" = "$GITHUB_SHA"
echo "digest=$digest" >> "$GITHUB_OUTPUT"
echo "tag=$tag" >> "$GITHUB_OUTPUT"'''
    binding=' '.join(shlex.quote(value) for item in configuration_inputs for value in ['--configuration-input',*item])
    source=source.replace('--receipt "$RUNNER_TEMP/qualified-image.json")"','--receipt "$RUNNER_TEMP/qualified-image.json" '+binding+')"')
    return [shlex.split(line) for line in source.replace('PREFIX',tag_prefix).replace('LOCAL_IMAGE',local_image).splitlines()]
