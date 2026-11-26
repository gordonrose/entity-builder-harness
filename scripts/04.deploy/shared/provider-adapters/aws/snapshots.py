#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.library.aws.snapshot-execution
#   version: 1
#   status: draft
#   created_on: "2026-11-15"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Share reserved single snapshot submission while callers retain source ownership, chronology and observation policy.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files]
#   used_by:
#   - id: deploy.library.entity-smoke.resource-control
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/controls-and-readiness/implementation/resource-control.py
"""No retries, deletion authority, missing-object adoption or completion store."""


class SnapshotFailure(Exception):
    def __init__(self, code, provider_code=None):
        super().__init__(code)
        self.code, self.provider_code = code, provider_code


class ProviderFailure(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def create(provider, store, *, phase, request, arguments, precondition,
           validate_reservation, observe, passthrough=()):
    reservation, fresh = store.reserve(phase, request)
    validate_reservation(reservation)
    if fresh:
        precondition(reservation)
        parameters = arguments(reservation)
        try: provider("rds", "create-db-snapshot", **parameters)
        except passthrough: raise
        except Exception as failure:
            raise SnapshotFailure("submission-uncertain",
                failure.code if isinstance(failure, ProviderFailure) else None) from None
    return observe(reservation, fresh)
