<!-- agentic-artifact:
owner: harness
kind: adr
purpose: Record the decision to place chat-owned workbench docs under docs/00.chat while keeping ADRs centralized.
domain: documentation
portability: llm-workbench-required
used_by:
  - docs/00.chat/README.md
  - docs/00.chat/public-chat-workbench-adrs.md
-->

# 0019 Use Chat Docs Namespace

Status: accepted
Date: 2026-06-23

## Context

The source repo had chat workbench docs under `docs/harness/architecture/`:

- `chat-workbench-public-repo-readiness.md`
- `public-chat-workbench-adrs.md`
- `script-layout.md`

Those files are not general product architecture guides. They explain portable
chat harness behavior, public `llm-workbench` bootstrap boundaries, and the
chat-related ADR export manifest.

Keeping them beside architecture rulebook material made ownership less clear.
Moving chat-specific docs closer to the `00.chat` layer makes their purpose
easier to understand, but moving ADR files at the same time would change the
repo's ADR storage contract and several commit and bootstrap checks.

## Decision

Create `docs/00.chat/` as the canonical documentation namespace for chat-owned
workbench docs.

Move these docs there:

- `docs/00.chat/script-layout.md`
- `docs/00.chat/chat-workbench-public-repo-readiness.md`
- `docs/00.chat/public-chat-workbench-adrs.md`

Add `docs/00.chat/README.md` to explain the namespace.

Keep harness ADRs centralized under `docs/harness/architecture/adrs/`. Use
`docs/00.chat/public-chat-workbench-adrs.md` to select chat-relevant ADRs for
public workbench export instead of moving ADR files into `docs/00.chat/`.

Update the `llm-workbench` bootstrap planner to copy `docs/00.chat/` as a chat
docs tree and continue copying only manifest-selected ADRs from the centralized
ADR directory.

## Consequences

Chat workbench docs now have a visible chat-layer home.

The public workbench bootstrap surface changes from individually selected
architecture docs to the `docs/00.chat/` tree plus selected centralized ADRs.

Existing ADR tooling and before-commit checks can continue to treat
`docs/harness/architecture/adrs/` as the canonical ADR root.

A future move to layer-owned ADR directories would need its own ADR and tooling
change, because it would alter the durable ADR storage contract.
