"""Closed, nonauthoritative selected store evidence contract."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.selected-store-evidence
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Validate bounded fixture evidence for immutable shared store conformance without release authority.
#   portability: {class: internal, targets: [kanbien/staging]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.aws-selected-store
#     path: scripts/04.deploy/release-control/adapters/aws/selected_store.py
import operation_journal as journal
import selected_operation as contract


def validate_evidence(value):
    contract.validate('selected-operation-evidence', value)
    if (value['expires_at_ms'] <= value['observed_at_ms']
            or value['expires_at_ms'] - value['observed_at_ms'] > 900000):
        journal.fail('evidence-lifetime-invalid')
    return value
