<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.standards.main-refresh-conflict-types
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: standard
  purpose: Define governed conflict classification and resolution during chat refresh
    from main.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-refresh-from-main
    path: .agentic/00.chat/workflows/chat-refresh-from-main.md
  - id: chat.script.main-refresh.apply-rehearsed-refresh
    path: scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh
  - id: chat.script.main-refresh.classify-conflict
    path: scripts/00.chat/main-refresh/classify-conflict/script.sh
  - id: chat.script.main-refresh.verify-conflict-audit
    path: scripts/00.chat/main-refresh/verify-conflict-audit/script.sh
-->
# Main Refresh Conflict Types

## Purpose

Classify conflicts found while refreshing a chat branch from `main`.

Use this standard after preflight reports conflicts and before resolving any
conflicted path. Resolve only conflicts with a deterministic action. If no type
fits, stop and propose either a new type or an expansion of an existing type.

Use the deterministic classifier for known conflict shapes:

```bash
bash scripts/00.chat/main-refresh/classify-conflict/script.sh <conflicted-path>
```

The classifier is a guardrail, not a substitute for judgment. If the classifier
returns `normal-repo-conflict` or `unsupported-conflict`, stop before resolving
unless the user approves the next step or the harness is updated.

## Classification Method

For each conflicted path, compare:

- file ownership: canonical owner, compatibility path, generated artifact, or
  session evidence
- conflict shape: both modified, add/add, delete/modify, or deleted by them
- content source: authored prose/code, generated output, or bookkeeping
- governance direction: stricter rule added, ownership moved, artifact retired,
  or normal repo behavior changed
- risk: whether either side would discard user-authored work, session evidence,
  or stricter governance

Inspect Git stages when needed:

```bash
git show :1:<path>   # base
git show :2:<path>   # chat branch
git show :3:<path>   # incoming main
git diff :2:<path> :3:<path>
```

## Session Log Audit Trail

For every preflight conflict, record an audit entry under the current chat
session log's `## Main Refresh Conflicts` section before promoting the
preflight result.

Use:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/record-main-refresh-conflict/script.sh \
  --path <conflicted-path> \
  --type <conflict-type> \
  --reason <classification-reason> \
  --action <resolution-action> \
  --mode <deterministic|skill-assisted|manual|stopped> \
  --preflight-branch <branch> \
  --preflight-worktree <path> \
  --files <changed-files-summary> \
  --checks <checks-summary>
```

Each entry must record:

- preflight branch
- preflight worktree
- conflicted path
- conflict type
- classification reason
- resolution mode
- deterministic action, skill-assisted action, manual action, or stop reason
- files changed by the resolution
- checks run or still pending

## Applying After Conflict Resolution

Approval to run a governed main-refresh rehearsal includes approval to apply a
clean, tested rehearsed result back to the chat branch.

After every conflicted path has a `## Main Refresh Conflicts` audit entry and
the required checks pass, apply the preflight branch automatically with:

```bash
bash scripts/00.chat/main-refresh/verify-conflict-audit/script.sh \
  --path <conflicted-path> ...
bash scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh <preflight-branch>
```

Stop before applying if:

- unresolved conflicts remain
- required checks failed or were skipped
- the preflight worktree is dirty
- the preflight branch no longer descends from the chat branch
- the apply script refuses cleanup
- the user explicitly asked to inspect before applying

Do not ask for a second approval when none of those stop conditions apply.

## Type Index

| Type | Detect | Deterministic action |
| --- | --- | --- |
| `ownership-migration-conflict` | One side moves behavior to a canonical owner while the other side improves the old path | Keep the canonical owner; migrate useful improvements into it |
| `generated-artifact-conflict` | Conflict is only in a generated artifact that can be recreated from source evidence | Remove or restore the generated artifact according to its governing workflow, then regenerate only if an explicit output is requested |
| `session-bookkeeping-conflict` | Conflict is limited to the current chat session log or chat-owned bookkeeping | Preserve current session evidence; never discard recorded commits or retention markers |
| `retired-artifact-delete-modify-conflict` | Chat branch deletes a retired generated artifact while `main` modifies it | Keep the deletion when the retirement ADR/workflow is present; preserve useful policy references in canonical docs if needed |
| `retired-artifact-generator-conflict` | One side preserves generator behavior for a retired tracked artifact while the other side makes generation on-demand only | Preserve retired-artifact policy; keep safe print/explicit-output behavior; block recreation of the retired tracked artifact |
| `retired-artifact-policy-script-conflict` | One side adds classifier or workflow behavior for a retired tracked artifact while the other side retires that artifact | Preserve retired-artifact policy; remove recoverability paths for the retired tracked artifact |
| `script-add-add-conflict` | Both sides add the same script path independently | Compare behavior, tests, and call sites; if both implement the same governed capability, merge behavior and tests; otherwise stop |
| `normal-repo-conflict` | Conflict changes authored code/prose without a matching governed type | Stop for approval before resolving |
| `unsupported-conflict` | No existing type fits or classification is ambiguous | Stop with missing-governance response and propose a new or expanded type |

## Type Details

### ownership-migration-conflict

Detect:
- A workflow, checklist, or script path has moved to a canonical owner on one
  side.
- The other side keeps the old path as the implementation and adds useful
  governance, checks, or stricter safety behavior.

Examples:
- `.agentic/00.chat/workflows/chat-promote-to-main.md` owns chat promotion on
  one side, while the other side adds verifier-based local convergence rules to
  a retired shared workflow path.

Deterministic action:
- Keep the canonical owner path.
- Migrate useful main-side improvements into the canonical owner named by the
  current workflow or artifact metadata.
- Adjust layer names, workflow paths, and exact blocked responses to the
  canonical owner.

Required checks:
- Run deterministic process drift checks on the legacy pointer and canonical
  owner.
- Run any script tests that cover the migrated behavior.

Session log entry:
- Record the conflicted path, canonical owner, migrated improvement, changed
  files, and checks.

Stop if:
- The canonical owner is missing.
- The improvement cannot be migrated without changing behavior outside the
  owner.
- Either side contains user-authored content whose ownership is unclear.

### generated-artifact-conflict

Detect:
- The conflicted path is a generated report, summary, build product, or other
  reproducible artifact.
- A workflow, script, or ADR defines the source evidence and output policy.

Deterministic action:
- Follow the artifact policy.
- Do not preserve stale generated content just because it appears in a conflict.
- Do not recreate tracked `commitLogs/README.md`.

Required checks:
- Run the generator smoke test or verifier when one exists.

Session log entry:
- Record source evidence, artifact path, and whether regeneration happened.

Stop if:
- The source evidence is missing.
- The artifact is not reproducible.
- The artifact policy is unclear.

### session-bookkeeping-conflict

Detect:
- The conflict is limited to the current chat session log or chat-owned metadata.

Deterministic action:
- Preserve recorded commits, latest commit metadata, decisions, issues, ADR
  disposition, and retention markers.
- Prefer additive merge of session evidence when entries are independent.

Required checks:
- Run commit prerequisite and session-log gates when applicable.

Session log entry:
- Record that session evidence was preserved and how.

Stop if:
- The conflict involves another chat's session log.
- Recorded commits or retention markers disagree.

### retired-artifact-delete-modify-conflict

Detect:
- One side deletes a generated artifact because it has been retired.
- The other side modifies the same artifact.
- A workflow or ADR records the retirement.

Deterministic action:
- Keep the deletion.
- Move any durable policy value into the canonical doc only if it is not already
  represented there.

Required checks:
- Run artifact generator and retirement smoke tests when present.

Session log entry:
- Record artifact path, retirement source, and whether any policy text moved.

Stop if:
- Retirement evidence is missing.
- The modified content includes non-generated user-authored decisions.

### retired-artifact-generator-conflict

Detect:
- The conflicted path is a generator script or generator test.
- One side writes, checks, or recreates a tracked artifact that another side has
  retired.
- A workflow or ADR records the artifact retirement.

Deterministic action:
- Preserve the retired-artifact policy.
- Do not restore default writes to the retired tracked artifact.
- Do not restore checks that require the retired tracked artifact to exist.
- Preserve safe non-persistent behavior such as stdout printing.
- Preserve explicit-output behavior only when it refuses the retired tracked
  artifact path.

Required checks:
- Run the generator smoke test.
- Run shell syntax checks for shell-based generators.

Session log entry:
- Record retired artifact path, generator path, retirement source, preserved
  safe behavior, and blocked behavior.

Stop if:
- The generator also produces non-retired artifacts and behavior cannot be
  separated deterministically.
- The retirement source is missing or ambiguous.

### retired-artifact-policy-script-conflict

Detect:
- The conflicted path is a classifier, workflow, verifier, or test.
- One side adds recoverability, validation, or workflow behavior for a tracked
  artifact that another side has retired.
- A workflow or ADR records the artifact retirement.

Deterministic action:
- Preserve the retired-artifact policy.
- Remove or avoid recoverability classes that treat the retired artifact as
  active state.
- Preserve unrelated classifier, verifier, or workflow behavior.
- Update tests so they verify the retired artifact is not reintroduced as an
  active governed path.

Required checks:
- Run the relevant classifier/verifier smoke tests.
- Run shell syntax checks for shell scripts.

Session log entry:
- Record retired artifact path, policy script path, removed recoverability, and
  preserved behavior.

Stop if:
- The policy script behavior cannot be separated from unrelated active
  behavior.
- The retirement source is missing or ambiguous.

### script-add-add-conflict

Detect:
- Both sides add the same script or test path.
- Git reports add/add (`AA`).

Deterministic action:
- Compare scripts by behavior, not just text.
- If both implement the same capability, produce a merged script that preserves
  stricter validation and all relevant tests.
- If the capability differs, stop.

Required checks:
- Run shell syntax checks and the relevant smoke tests.

Session log entry:
- Record merged behavior and tests run.

Stop if:
- Behavior differs in a way that changes ownership, safety, or data mutation.
- No test covers the merged script.

### normal-repo-conflict

Detect:
- Conflict is user-authored code/prose and no more specific governed type fits.

Deterministic action:
- None.

Required checks:
- N/A until resolution is approved.

Session log entry:
- Record the stop and requested next step.

Stop if:
- Always stop before resolving.

### unsupported-conflict

Detect:
- Existing types do not fit.
- More than one type fits and the action differs.
- The model cannot explain the classification in terms of ownership, shape,
  source, governance direction, and risk.

Deterministic action:
- None.

Required checks:
- N/A until governance is updated.

Session log entry:
- Record proposed new type or proposed expansion.

Stop if:
- Always stop with the missing-governance response.
