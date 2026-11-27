#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.capability.environment-lifecycle.policy
#   version: 1
#   status: active
#   created_on: "2026-11-26"
#   updated_on: "2026-11-27"
#   layer: 04.deploy
#   domain: deployment.environment-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Check provider-neutral environment lifetime and data retention without granting resource mutation or cleanup authority.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.library.aws.preparation-inputs
#     path: scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/preparation-inputs.py
#   - id: deploy.command.core-platform-target-declaration.implementation
#     path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py
"""Checked lifecycle settings, not ownership evidence or destructive authority."""
from dataclasses import dataclass


class PolicyFailure(ValueError):
    """Finite source-setting concern; rejected values never enter the message."""

    def __init__(self, condition):
        self.code = "environment-lifecycle-" + condition
        super().__init__(self.code)


@dataclass(frozen=True)
class LifecyclePolicy:
    mode: str
    data_retention: str
    max_duration_seconds: int | None
    explicit: bool


def _choice(policy, name, choices):
    reason = name.replace("_", "-")
    if name not in policy:
        raise PolicyFailure(reason + "-missing")
    value = policy[name]
    if value is None:
        raise PolicyFailure(reason + "-null")
    if not isinstance(value, str):
        raise PolicyFailure(reason + "-type-invalid")
    if not value:
        raise PolicyFailure(reason + "-empty")
    if value not in choices:
        raise PolicyFailure(reason + "-unsupported")
    return value


def read(profile):
    """Validate one already parsed profile; absence preserves protected defaults."""
    if not isinstance(profile, dict):
        raise PolicyFailure("profile-type-invalid")
    if "environment_lifecycle" not in profile:
        return LifecyclePolicy("persistent", "preserve", None, False)
    policy = profile["environment_lifecycle"]
    if policy is None:
        raise PolicyFailure("policy-null")
    if not isinstance(policy, dict):
        raise PolicyFailure("policy-type-invalid")
    if not policy:
        raise PolicyFailure("policy-empty")
    if set(policy) - {"mode", "data_retention", "max_duration_seconds"}:
        raise PolicyFailure("policy-field-unsupported")
    mode = _choice(policy, "mode", {"persistent", "temporary"})
    retention = _choice(policy, "data_retention", {"preserve", "discard"})
    if mode == "persistent":
        if retention != "preserve":
            raise PolicyFailure("persistent-data-retention-conflict")
        if "max_duration_seconds" in policy:
            raise PolicyFailure("persistent-expiry-prohibited")
        return LifecyclePolicy(mode, retention, None, True)
    if retention != "discard":
        raise PolicyFailure("temporary-data-retention-conflict")
    if "max_duration_seconds" not in policy:
        raise PolicyFailure("max-duration-seconds-missing")
    duration = policy["max_duration_seconds"]
    if duration is None:
        raise PolicyFailure("max-duration-seconds-null")
    if type(duration) is not int:
        raise PolicyFailure("max-duration-seconds-type-invalid")
    if duration <= 0:
        raise PolicyFailure("max-duration-seconds-not-positive")
    return LifecyclePolicy(mode, retention, duration, True)


def require_persistent(policy):
    """Existing fixed-target routes have no separately owned session binding."""
    if policy.mode != "persistent":
        raise PolicyFailure("session-binding-unsupported")
    return policy
