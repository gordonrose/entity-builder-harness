"""Explicit synthetic local store inputs; these are not production policy."""
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.control-store-fixtures
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Supply fixed synthetic local-only intent and bounded safe evidence for conformance.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.control-store-conformance
#     path: scripts/04.deploy/operational-realization-gate/control_store_conformance.py
import operation_journal as contract

NOW=1000000
OWNER_A='a'*32
OWNER_B='b'*32
OWNER_C='c'*32

def intent(operation='fixture-operation', *, resources=('shared-resource',), release='1'):
    scopes=[]
    for resource in resources:
        scope={'provider':'local-fixture','namespace':'fixture-estate','target':'fixture-target','resource':resource}
        scopes.append({'scope_id':contract.digest(scope),**scope})
    policy={'scope':'local-conformance','lease_ms':1000,'operation_timeout_ms':10000,
            'call_timeout_ms':500,'max_attempts':2,'evidence_lifetime_ms':5000}
    return {'schema':'operation-control/v1','operation_id':operation,
            'idempotency_key':contract.digest({'fixture_operation':operation}),
            'release_digest':'sha256:'+release*64,'profile_digest':'sha256:'+'2'*64,
            'artifact_digest':'sha256:'+'3'*64,'environment_digest':'sha256:'+'4'*64,
            'authority_policy_digest':contract.digest(policy),'recovery_route':'local-fixture-reconcile',
            'scopes':sorted(scopes,key=lambda row:row['scope_id']),
            'policy':policy}

def evidence(document, attempt, assertion='fixture-effect', *, now=NOW, verdict='passed', effect=1, resources=0, revision=2, fences=None):
    return {'schema':'operation-evidence/v1','operation_id':document['operation_id'],
            'release_digest':document['release_digest'],'profile_digest':document['profile_digest'],
            'attempt':attempt,'observed_revision':revision,'fences':fences if fences is not None else [{'scope_id':scope['scope_id'],'generation':1} for scope in document['scopes']],'assertion':assertion,'verdict':verdict,
            'subject_digest':document['artifact_digest'],'observed_at_ms':now,'expires_at_ms':now+4000,
            'counts':{'effect_count':effect,'owned_resources':resources}}
