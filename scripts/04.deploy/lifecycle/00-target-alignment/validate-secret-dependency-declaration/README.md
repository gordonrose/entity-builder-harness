<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.validate-secret-dependency-declaration.readme
version: 4
status: active
created_on: "2026-10-22"
updated_on: "2026-11-09"
layer: 04.deploy
domain: deployment.secret-management
disciplines: [agentic, security, sre]
kind: documentation
purpose: Explain the offline validator for non-secret workload dependency declarations.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: deploy.command.validate-secret-dependency-declaration
  path: scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.sh
-->
# Validate Secret Dependency Declaration

This read-only validator checks the provider-neutral secret dependency portion
of one scope contract. It does not read a secret store, call a provider, or
print secret material. It validates declaration shape and common unsafe
formats; it is not a replacement for repository secret scanning.

Concrete provider secret references, permissions, delivery mechanisms, target
isolation, and live rotation proof remain provider-binding and target-alignment
work. An ARN is a reference, not a secret value, but it is intentionally
excluded from this portable contract.

Every active new-framework scope is checked through the active-workload
inventory gate. A future persistence scope must run this command directly
during declaration coverage and will be checked again when it enters that
target's active scope inventory.

Each credential identifies the declared dependency it serves. A
server-mediated verifier cannot receive a credential for its tested dependency,
and a declared migration executor must receive a matching `migration`-class
credential. These are portable declaration checks; provider reference
resolution, executable policies, effective database grants, session
termination, and live rotation/revocation proof remain later target-alignment
and provider-binding work. In particular, an `access_grant` owner/policy is
accountability and declared intent, not evidence of effective least privilege.

## Administration and permission testing

Administration configures database access; a permission probe connects using
the restricted application account to test that access. The validator supports
both the existing probe inside the administrator task and a separate restricted
completion task. The [contract guide](../../../../../.agentic/04.deploy/00-target-alignment/schemas/secret-dependency-contract.v1.guide.md#who-tests-runtime-permissions)
explains the declaration and gives an example.

For a separate task, `script.py` resolves its explicit `workload` and the
application's `target_workload`, checks their types/completion and requires the
same single runtime authentication reference for the same dependency. A
missing or mismatched identity reports
`runtime-identity-proof-authentication-mismatch`. Administrative or migration
credentials on that task report
`runtime-identity-proof-privileged-access-prohibited`. Invalid workload selection
or completion reports `runtime-identity-proof-workload-invalid`. Existing
in-administrator declarations retain their own runtime identity requirement.

`smoke-test.py`, invoked by `smoke-test.sh`, exercises both arrangements through
the actual CLI and rejects missing selectors, duplicate workloads, incorrect
identities and privileged access. These are offline checks: success does not
establish that permissions have been applied, SQL operations work, or the
application can connect. Physical bindings and live application/database proofs
remain required before acceptance.
