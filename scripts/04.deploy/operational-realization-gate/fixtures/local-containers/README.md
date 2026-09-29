<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.fixture.local-container-evidence
version: 1
status: active
layer: 04.deploy
domain: deployment.realization
disciplines: [architecture, security, sre]
kind: fixture
purpose: Provide inert container observation data for cross-receipt mutation tests without claiming real execution.
portability: {class: internal, targets: []}
used_by:
- id: deploy.test.local-container-contracts
  path: scripts/04.deploy/operational-realization-gate/test_local_container_contracts.py
-->
# Local container evidence fixtures

These hashes and one-byte files are synthetic test data, not real build or runtime
evidence. The valid result proves only closed-contract accounting; it retains
blocked deployment authority and pending bootstrap and external-image profiles.
Mutation tests alter one binding at a time and recompute outer digests where
appropriate, so rejection cannot rely only on an outdated envelope checksum.
