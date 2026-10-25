#!/usr/bin/env python3
"""Select the ECR manifest that Basic Scanning can actually scan."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-persistence-observability-collector-package-custody.resolve-ecr-scan-manifest
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Select a single runnable amd64 OCI manifest beneath a published collector image without treating an OCI index as a scanned payload.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-observability-collector
#     path: .github/workflows/publish-kanbien-core-platform-observability-collector.yml
from __future__ import annotations

import json
import re
import sys
from typing import Any

DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
MANIFEST = "application/vnd.oci.image.manifest.v1+json"
INDEX = "application/vnd.oci.image.index.v1+json"


def valid_digest(value: object) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise ValueError("ECR response did not contain a valid immutable image digest")
    return value


def select(payload: dict[str, Any]) -> str:
    media_type = payload.get("mediaType")
    if media_type == MANIFEST:
        return valid_digest(payload.get("digest"))
    if media_type != INDEX:
        raise ValueError("ECR response used an unsupported collector manifest media type")
    manifest_text = payload.get("manifest")
    if not isinstance(manifest_text, str):
        raise ValueError("ECR index response did not contain a manifest")
    index = json.loads(manifest_text)
    manifests = index.get("manifests") if isinstance(index, dict) else None
    if not isinstance(manifests, list):
        raise ValueError("ECR index response did not contain manifests")
    candidates = [
        item.get("digest")
        for item in manifests
        if isinstance(item, dict)
        and item.get("mediaType") == MANIFEST
        and item.get("platform") == {"architecture": "amd64", "os": "linux"}
    ]
    if len(candidates) != 1:
        raise ValueError("ECR index did not resolve exactly one runnable amd64 manifest")
    return valid_digest(candidates[0])


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("ECR response was not an object")
        print(select(payload))
        return 0
    except (ValueError, json.JSONDecodeError) as error:
        print(f"collector-ecr-scan-manifest-invalid: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
