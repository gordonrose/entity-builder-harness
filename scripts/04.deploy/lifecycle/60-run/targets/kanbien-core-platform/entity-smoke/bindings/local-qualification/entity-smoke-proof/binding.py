#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.binding.entity-smoke.local-qualification-proof
#   version: 2
#   status: draft
#   created_on: "2026-11-21"
#   updated_on: "2026-11-22"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Reject entity-smoke live operations unless their custody receipt binds exact package-local qualification evidence.
#   portability: { class: internal, targets: [kanbien-core-platform] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.entity-smoke.infrastructure.implementation
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/script.py
"""Target binding for the qualification-to-deployment handoff."""

from __future__ import annotations
import re

TARGET = "kanbien-core-platform"
SCOPE = "entity-smoke"
REQUIRED_CHECKS = frozenset({"entity-smoke-infrastructure-route", "entity-smoke-composition-suite", "secret-dependency-declaration-regression"})
SHA = re.compile(r"^[a-f0-9]{40}$")
DIGEST = re.compile(r"^[a-f0-9]{64}$")

class BindingFailure(Exception):
    def __init__(self): super().__init__("infrastructure-local-qualification-not-confirmed")

def require(value: bool) -> None:
    if not value: raise BindingFailure()

def require_current(receipt: object) -> dict:
    require(isinstance(receipt, dict) and receipt.get("schema") == "deploy/package-custody-receipt/v2" and receipt.get("target") == TARGET and isinstance(receipt.get("source_revision"), str) and SHA.fullmatch(receipt["source_revision"]) is not None)
    value = receipt.get("local_qualification")
    require(isinstance(value, dict) and set(value) == {"schema", "target", "scope", "source_revision", "checks"} and value["schema"] == "deploy/local-qualification/v1" and value["target"] == TARGET and value["scope"] == SCOPE and value["source_revision"] == receipt["source_revision"])
    checks = value["checks"]
    require(isinstance(checks, dict) and set(checks) == REQUIRED_CHECKS)
    for item in checks.values():
        require(isinstance(item, dict) and set(item) == {"input_digest", "evidence_key"} and all(isinstance(item[key], str) and DIGEST.fullmatch(item[key]) is not None for key in item))
    return value
