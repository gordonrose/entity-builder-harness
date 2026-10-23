<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.command.smoke-test-core-server-persistence-image.readme
version: 1
status: draft
layer: 04.deploy
domain: deployment.core-server-persistence
disciplines: [security, sre]
kind: capability-readme
purpose: Explain the disposable TLS PostgreSQL package qualification for the persistence candidate.
portability: { class: internal, targets: [] }
-->
# Persistence Image Package Smoke

This package-stage test starts disposable local Docker resources only: a TLS
PostgreSQL container and the candidate image. It proves the migration program,
server process, TLS driver path, readiness, a server-mediated record operation,
and that the runtime database principal cannot execute structural DDL.

It does not use AWS, target secrets, target networking, or target data. A
missing Docker engine is a failure for this command; the protected hosted image
workflow is the required qualification route when a developer workstation lacks
Docker.
