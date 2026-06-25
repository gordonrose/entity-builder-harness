<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.architecture.adr.readme
  version: 1
  status: active
  layer: 03.deploy
  domain: infra.ci-cd
  disciplines:
  - agentic
  kind: adr
  purpose: Document AWS Architecture Decision Records.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: aws.readme
    path: .agentic/aws/README.md
-->
# AWS Architecture Decision Records

AWS ADRs record durable decisions about cloud infrastructure, environments,
deployment targets, runtime operations, access boundaries, and AWS resource
ownership.

Use sequential, zero-padded filenames:

```txt
0001-short-kebab-title.md
```

Use one of these statuses:

- `proposed`
- `accepted`
- `superseded`
