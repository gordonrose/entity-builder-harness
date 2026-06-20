<!-- agentic-artifact:
owner: harness
kind: doc
purpose: Define the current readiness boundary for bootstrapping a public chat workbench repo.
domain: bootstrap
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
  - .agentic/shared/standards/upstream-repo-bootstrap.md
-->

# Chat Workbench Public Repo Readiness

This document defines the current boundary for creating a standalone public
`llm-workbench` repository from this source repo.

It is a readiness manifest, not the export script. The bootstrap workflow still
owns the actual copy, transform, approval, and commit process.

## Current Status

The chat harness is close to a standalone public repo, but it is not yet a
blind copy operation.

The canonical chat scripts now live under `scripts/00.chat/`, every
`scripts/00.chat` folder has an onboarding README, and the bootstrap audit can
identify the required script set. The remaining work is to create the public
repo shell and transform source-specific files into upstream-safe files.

## Copy As-Is

These paths are intended to be copied directly into the first public workbench
bootstrap, subject to the normal upstream inspection gates:

- `.agentic/00.chat/`
- `.agentic/shared/standards/upstream-repo-bootstrap.md`
- `.agentic/shared/workflows/` entries required by cross-layer process and
  capability resolution
- `.agentic/01.harness/` standards and workflows required by metadata,
  deterministic process, governed script, and harness-maintenance checks
- `scripts/00.chat/`
- `scripts/01.harness/`
- `docs/harness/architecture/script-layout.md`
- `docs/harness/architecture/public-chat-workbench-adrs.md`
- ADRs listed in `docs/harness/architecture/public-chat-workbench-adrs.md`

The exact script set should be confirmed with:

```bash
npm run chat:audit-bootstrap
```

The target repo materialization plan should be inspected with:

```bash
bash scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh \
  --target <upstream-repo> \
  --dry-run
```

## Transform Before Copying

These source files are useful input, but must be rewritten for the public
workbench repo:

- `AGENTS.md`
  - keep the small router shape
  - remove source repo layers that do not exist in the public workbench
  - keep only public workbench source-of-truth paths
- `package.json`
  - rename the package from `entity-builder-harness`
  - decide whether the public repo should keep `"private": true` during early
    incubation or remove it before package publication
  - keep the `chat:*` command surface that delegates to canonical
    `scripts/00.chat/...` paths
- root `README.md`
  - do not copy the source repo README
  - write a public overview for engineers trying the workbench

## Create In The Public Repo

The first public repo bootstrap should add these files because outside
engineers need a product-shaped entry point, not only internal harness files:

- `README.md`
- `LICENSE` after the license choice is explicit
- `.gitignore`
- `docs/concepts.md`
- `docs/install.md`
- `docs/workflows.md`
- `docs/adapting-to-your-repo.md`
- `examples/minimal-repo/`
- `scripts/install.sh`
- `scripts/uninstall.sh`
- `tests/smoke-test-install.sh`

Starter templates for these files live under:

```txt
docs/harness/bootstrap/llm-workbench-template/root/
```

The install smoke test must prove that a throwaway Git repo can install the
workbench, run the public command surface, and create its own `commitLogs/`
inside a chat-owned worktree on first chat startup.

## Exclude

Do not copy:

- source repo `commitLogs/`
- `.agentic/product/`
- `.agentic/education/`
- `.agentic/aws/`
- product `src/`, app tests, or deployment docs
- local transcript paths
- local worktree paths
- source-specific open tabs or IDE state
- private product, customer, tenant, credential, profile, or environment data

## Current Export Risks

These are known issues to resolve before pushing an initial public bootstrap:

- The source `package.json` is source-specific and cannot be copied raw.
- The source `AGENTS.md` mentions non-chat layers, including product-specific
  routing, and must become a public workbench template.
- The upstream helper currently assumes the intended local path and Git remote
  for `gordonrose/llm-workbench`; that is useful for this source repo but
  should be documented as a source-side promotion helper, not a generic install
  command.
- Historical ADRs mention retired script paths. That is acceptable when framed
  as migration history, but public onboarding docs should point to canonical
  paths and package commands only.
- ADR export is intentionally selective. Future chat workbench ADRs should be
  added to `docs/harness/architecture/public-chat-workbench-adrs.md` when they
  explain current public workbench behavior; non-chat ADRs should stay out.

## Readiness Checklist

<!-- deterministic-check: allow reason="this manifest is human-governed readiness guidance; executable proof belongs to the bootstrap audit and install smoke test" -->
Before bootstrapping or updating `llm-workbench`:

- run the bootstrap script audit from the source repo
- inspect the upstream repo status, remotes, branch, and existing files
- decide whether the upstream repo is empty or already initialized
- transform `AGENTS.md` and `package.json`
- create the public README, docs, install scripts, example repo, and smoke test
<!-- deterministic-check: allow reason="readiness checks are listed for human review; bootstrap planner and install smoke test own executable validation" -->
- verify no excluded source-specific paths are copied
- verify the dry-run planner has no conflicts
- apply only after reviewing a clean dry-run plan
- verify `npm run chat:list` works in the upstream repo
- verify the install smoke test creates a target repo's own `commitLogs/`
  inside a chat-owned worktree
- commit only after explicit approval
- push only after separate explicit approval
