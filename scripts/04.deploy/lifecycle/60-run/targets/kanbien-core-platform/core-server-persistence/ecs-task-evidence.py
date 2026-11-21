#!/usr/bin/env python3
"""Validate the bounded ECS invocation while permitting captured empty defaults."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.kanbien-core-platform.persistence-ecs-task-evidence
#   version: 2
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate exact persistence ECS task overrides while allowing explicitly captured inert provider defaults.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
#   effects: [read-only]
from __future__ import annotations

import importlib.util
from pathlib import Path

_RESPONSE_SPEC = importlib.util.spec_from_file_location("persistence_aws_response", Path(__file__).resolve().parents[5] / "shared/provider-adapters/aws/response.py")
_RESPONSE = importlib.util.module_from_spec(_RESPONSE_SPEC)
_RESPONSE_SPEC.loader.exec_module(_RESPONSE)
# Retain this historical import path for existing migration/acceptance consumers.
task_overrides_match = _RESPONSE.task_overrides_match
