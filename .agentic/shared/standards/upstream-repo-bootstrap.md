# Upstream Repo Bootstrap Standard

## Purpose

Use this when seeding a reusable upstream repo from a source repo that already
contains working harness, product, infrastructure, or process artifacts.

The standard applies across layers. Layer workflows define the specific
portable file set for chat, frontend, CRUD factory, AWS CI/CD, or other
upstream repo types.

## Ownership

- The source repo provides working evidence and candidate files.
- The upstream repo owns reusable behavior after bootstrap.
- The layer-specific bootstrap workflow owns the portable file set.
- Source-repo-specific product, deployment, customer, environment, credential,
  path, and session-history details stay out of the upstream repo.

## Required Inspection

Before writing to the upstream repo, inspect and record:

- source repo absolute path
- upstream repo absolute path
- target upstream repo purpose
- whether the upstream repo is empty or already initialized
- whether the upstream repo has a valid `HEAD`
- current branch name, or the intended initial branch for an unborn `HEAD`
- candidate portable paths
- required exclusions
- source paths that must remain private or source-specific
- whether any target paths would be overwritten
- whether the bootstrap creates a minimal usable product surface or only an
  internal file baseline

## Approval Boundaries

- Read-only inspection does not approve writes.
- Writing or overwriting upstream files requires explicit approval.
- Creating an upstream commit requires explicit approval.
- Pushing upstream changes requires separate explicit approval.
- Deleting, moving, or rewriting upstream history requires separate explicit
  approval and a workflow that governs that action.

## Empty Repo Bootstrap

For an empty upstream repo with no valid `HEAD`:

- establish the initial branch before running workflows that require a current
  branch
- add starter public files required by the layer workflow
- create an initial commit before attempting normal chat startup in the
  upstream repo
- do not push the initial commit without separate explicit approval

Do not pre-copy source repo `commitLogs/`. The upstream repo's first chat
startup creates its own `commitLogs/<date>/<session>/README.md` after the
initial commit exists.

## Required Exclusions

Exclude by default:

- `commitLogs/`
- chat transcripts and local session artifacts
- source repo product code
- source repo deployment, cloud, or environment-specific rules
- credentials, tokens, local profiles, and machine-specific paths
- customer, tenant, or private business data
- generated reports unless the layer workflow explicitly defines them as
  reusable source material

## Required Output

A bootstrap workflow must produce or record:

- source repo and upstream repo paths
- file set copied or proposed
- exclusions applied
- initial branch and initial commit status for empty upstream repos
- product-shell files created, when the upstream repo is intended for external
  use
- whether `commitLogs/` was created by a first upstream chat or intentionally
  left absent until then
- checks run
- commit status
- push status
- follow-up needed before downstream repos can install or sync the upstream
  repo

## Stop Conditions

Stop before writing when:

- upstream ownership is ambiguous
- the portable file set is not defined by a layer workflow
- target repo contains files that would be overwritten without approval
- source-specific or private material cannot be cleanly separated
- an externally usable upstream repo lacks install docs, examples, or smoke
  tests defined by its layer workflow
- the requested bootstrap would require a copy, commit, push, delete, move, or
  overwrite action not governed by the current workflow
