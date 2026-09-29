<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.fixture.dependency-effects
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: readme
purpose: Describe independently checked real PostgreSQL effects and disposable qualification boundaries.
portability: {class: internal, targets: [entity-builder]}
used_by:
- id: deploy.script.dependency-effects
  path: scripts/04.deploy/operational-realization-gate/dependency_effects.py
-->
# Disposable dependency effect expectations

The existing image-smoke capability runs the actual packaged PostgreSQL bootstrap
and migration commands against a pinned PostgreSQL 17.11 engine. These fixtures
are reviewed expected migration checksums, columns, constraints and table names;
they are never generated from workload-reported success during qualification.

The dependency lock selects the official linux/amd64 manifest and its configuration
digest. Public acquisition is explicit. Qualification creates an internal owned
Docker network with no published ports, generates private disposable credentials
and a two-day fixture CA, requires verified TLS and SCRAM authentication for all
network clients, and removes only its randomly labelled containers and network.
The database remains memory-backed and disposable. The administrative catalog
observer uses the owned fixture's local socket; runtime DML/DDL proofs authenticate
the actual generated runtime identity over verified TLS.

The product image retains its pinned RDS CA. Its explicit local qualification
binding accepts only the fixed fixture hostname, port, mode and CA mount; the
staging source-policy verifier rejects these fields in target descriptors. No
existing image file is replaced. The same rebuilt final image is used for server
compatibility, actual command execution and complete payload inventory checks.

Nine task executions cover local binding refusal, production-default distrust of
the fixture CA, wrong bootstrap password, bootstrap and repetition, denied
migration identity, migration and repetition, and changed migration checksum.
Independent observations verify role attributes and absence of role memberships,
schema/table ownership, all four DML privileges, exact columns and constraints,
immutable migration history and repeat stability. Four real grant revocations
must each cause the independent observer to refuse success. Separate runtime
checks prove authentication, DML transactions and actual permission-denied DDL.

Successful evidence is saved under the supplied scratch root at
`dependency-effect-evidence-<run_id>/build-result.json` and `effect-result.json`.
The former is the complete normalized upstream build/container receipt; the
latter binds its result digest. The output is unsigned local qualification
proof. All release and operation authority remain blocked; relay, worker, restore,
AWS identities, RDS behavior, hosted execution and live Stage 6 remain pending.

The official image source is recorded in `dependency-image.lock.json`. See the
[official PostgreSQL image documentation](https://hub.docker.com/_/postgres) for
initialization and authentication configuration. This fixture deliberately adds
stricter isolation and separate independent effect observations.
