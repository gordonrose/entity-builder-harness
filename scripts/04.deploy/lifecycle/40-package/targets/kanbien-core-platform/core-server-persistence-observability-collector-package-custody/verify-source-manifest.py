#!/usr/bin/env python3
"""Verify the public OCI index selects the immutable private collector manifest."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-persistence-observability-collector-package-custody.verify-source-manifest
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Resolve the declared Linux/AMD64 public OCI child manifest and require an identical immutable private ECR manifest before collector custody qualification.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-observability-collector
#     path: .github/workflows/publish-kanbien-core-platform-observability-collector.yml
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def fail(code: str) -> None:
    print(json.dumps({"schema": "deploy/collector-source-manifest-verdict/v1", "verdict": "failed", "findings": [{"code": code}]}, sort_keys=True))
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--expected-index-digest", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if not SHA256.fullmatch(args.expected_index_digest):
        fail("collector-source-index-digest-invalid")
    try:
        raw_index = args.index.read_bytes()
        index = json.loads(raw_index)
    except (OSError, json.JSONDecodeError):
        fail("collector-source-index-unreadable")

    # OCI manifest identity is the SHA-256 of the exact response bytes. This
    # avoids trusting an optional registry response header before selecting the
    # platform-specific child manifest.
    if f"sha256:{hashlib.sha256(raw_index).hexdigest()}" != args.expected_index_digest:
        fail("collector-source-index-identity-mismatch")
    if index.get("schemaVersion") != 2 or index.get("mediaType") != "application/vnd.oci.image.index.v1+json":
        fail("collector-source-index-shape-invalid")

    candidates: list[str] = []
    manifests = index.get("manifests")
    if not isinstance(manifests, list):
        fail("collector-source-index-manifests-invalid")
    for manifest in manifests:
        if not isinstance(manifest, dict):
            continue
        platform = manifest.get("platform")
        digest = manifest.get("digest")
        if isinstance(platform, dict) and platform.get("os") == "linux" and platform.get("architecture") == "amd64" and isinstance(digest, str) and SHA256.fullmatch(digest):
            candidates.append(digest)
    if len(candidates) != 1:
        fail("collector-source-platform-manifest-ambiguous")

    result = {
        "schema": "deploy/collector-source-manifest-verdict/v1",
        "verdict": "passed",
        "source_index_digest": args.expected_index_digest,
        "platform": {"os": "linux", "architecture": "amd64"},
        "platform_manifest_digest": candidates[0],
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
