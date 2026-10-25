#!/usr/bin/env python3
"""Validate the bounded ECS invocation while permitting captured empty defaults."""
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.kanbien-core-platform.persistence-ecs-task-evidence
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
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


def task_overrides_match(task: object, container_name: str, expected_environment: dict[str, str]) -> bool:
    """An empty inference list is inert; commands, roles and resources stay exact.

    The optional empty inferenceAcceleratorOverrides list is present in captured
    ECS responses. Unknown keys and nonempty/default-looking consequential
    fields are deliberately rejected rather than silently discarded.
    """
    if not isinstance(task, dict):
        return False
    overrides = task.get("overrides")
    if not isinstance(overrides, dict) or set(overrides) - {"containerOverrides", "inferenceAcceleratorOverrides"}:
        return False
    if "inferenceAcceleratorOverrides" in overrides and overrides["inferenceAcceleratorOverrides"] != []:
        return False
    containers = overrides.get("containerOverrides")
    if not isinstance(containers, list) or len(containers) != 1 or not isinstance(containers[0], dict):
        return False
    container = containers[0]
    if set(container) != {"name", "environment"} or container.get("name") != container_name:
        return False
    environment = container.get("environment")
    if not isinstance(environment, list) or len(environment) != len(expected_environment):
        return False
    if not all(isinstance(item, dict) and set(item) == {"name", "value"} and isinstance(item["name"], str) and isinstance(item["value"], str) for item in environment):
        return False
    return {item["name"]: item["value"] for item in environment} == expected_environment
