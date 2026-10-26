#!/usr/bin/env python3
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.provider.aws.cognito-provisioning-observation
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.provider-outcomes
#   disciplines: [security, sre]
#   kind: script
#   purpose: Observe declared Cognito provisioning effects without secret reads, mutation, or retries.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.script.provision-platform-shell-negative-authz-client
#     path: scripts/04.deploy/provision-platform-shell-negative-authz-client/script.py
#   - id: deploy.script.provision-platform-shell-persistence-write-client
#     path: scripts/04.deploy/provision-platform-shell-persistence-write-client/script.py
"""Shared response inspection for two existing bounded provisioning consumers."""

class ObservationFailure(Exception):
    pass


def selected(response, field, identity_key, identity):
    items=response.get(field)
    if not isinstance(items,list) or response.get('NextToken') or response.get('nextToken') or any(not isinstance(item,dict) for item in items):
        raise ObservationFailure('provisioning-observation-incomplete')
    result=[item for item in items if item.get(identity_key)==identity]
    if len(result)>1:raise ObservationFailure('provisioning-observation-ambiguous')
    return result[0] if result else None


def observe(run_json, aws_cli, policy, desired_scopes, baseline_scopes=None):
    """Return presence facts; these do not qualify client behavior or secret contents."""
    servers=run_json(aws_cli,policy,['cognito-idp','list-resource-servers','--user-pool-id',policy['user_pool_id'],'--max-results','50'])
    server=selected(servers,'ResourceServers','Identifier',policy['resource_server_identifier'])
    authority='absent'
    if server is not None:
        scopes=server.get('Scopes')
        if server.get('Name')!=policy['resource_server_name'] or not isinstance(scopes,list) or any(not isinstance(item,dict) or not isinstance(item.get('ScopeName'),str) for item in scopes):
            raise ObservationFailure('provisioning-authority-shape-unproven')
        actual=[item['ScopeName'] for item in scopes]
        if sorted(actual)==sorted(desired_scopes):authority='present'
        elif baseline_scopes is not None and sorted(actual)==sorted(baseline_scopes):authority='baseline'
        else:raise ObservationFailure('provisioning-authority-shape-unproven')
    clients=run_json(aws_cli,policy,['cognito-idp','list-user-pool-clients','--user-pool-id',policy['user_pool_id'],'--max-results','50'])
    client=selected(clients,'UserPoolClients','ClientName',policy['client_name'])
    if client is not None and (not isinstance(client.get('ClientId'),str) or not client['ClientId']):raise ObservationFailure('provisioning-client-identity-unproven')
    secrets=run_json(aws_cli,policy,['secretsmanager','list-secrets','--include-planned-deletion','--filters',f"Key=name,Values={policy['secret_name']}"])
    secret=selected(secrets,'SecretList','Name',policy['secret_name'])
    state={'authority':authority,'client':'present' if client is not None else 'absent','secret':'pending-deletion' if secret is not None and secret.get('DeletedDate') else 'present' if secret is not None else 'absent'}
    if state=={'authority':'present','client':'present','secret':'present'}:outcome='present-unqualified'
    elif authority==('baseline' if baseline_scopes is not None else 'absent') and state['client']==state['secret']=='absent':outcome='absent'
    else:outcome='partial'
    return {'schema':'deploy/provisioning-reconciliation/v1','verdict':outcome,'effects':state,'next_action':'retain-observation-and-review-recovery','mutation_performed':False}
