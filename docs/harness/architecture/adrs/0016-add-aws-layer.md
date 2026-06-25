<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0016-add-aws-layer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr
purpose: Record the 0016 Add AWS Layer architecture decision.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
-->

# 0016 Add AWS Layer

Status: accepted
Date: 2026-06-19

## Context

The repo already separates shared process, harness maintenance, education
resources, chat lifecycle, and product/code work. AWS work does not fit cleanly
into those boundaries.

Cloud resource inspection and operational changes are not product behavior by
themselves. They may affect product deployment targets, but they also involve
account context, regions, runtime resources, infrastructure state, logs,
secrets references, cost, access, and blast radius. Treating that work as
generic shared process would make shared workflows too broad, while putting it
under product would hide cloud operations behind application code ownership.

The harness needs a place for AWS-specific workflows that can distinguish
read-only inspection from approved cloud mutation.

## Decision

Add `.agentic/aws/` as a first-class layer for AWS infrastructure,
environment, runtime-operation, and cloud deployment target work.

The AWS layer owns:

- AWS account, profile, region, and environment inventory
- AWS resource inspection and operational status review
- AWS change planning, blast-radius review, rollback notes, and verification
- approved execution of AWS changes
- AWS runbooks, non-secret inventory, and AWS-layer ADRs

Shared process still owns repo-wide deployment and release procedure. Product
still owns application code and product behavior. Chat still owns chat
lifecycle, branch, and worktree operations. Harness still owns changes to the
layer system itself.

## Consequences

Future AWS requests can route to AWS workflows instead of being treated as
shared-process or product tasks by default.

The layer gives agents a safer default: inspect AWS state in discovery mode,
plan before mutation, and require explicit approval before changing cloud
resources.

The repo gains another layer, but keeps always-loaded instructions small by
placing AWS-specific procedure in `.agentic/aws/` and durable layer rationale
in this ADR.
