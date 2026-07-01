<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.source-material.mcp-server-deployment-architecture
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: source-material
purpose: Provide first source coverage for MCP server deployment architecture before structured rulebook conversion.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.recognition-candidate.2026-06-26.mcp-server
  path: .agentic/02.rag-rulebook/recognition-candidates/deferred/2026-06-26-mcp-server.yml
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# MCP Server Deployment Architecture

## Purpose

Provide first source material for the `MCP server` recognition candidate.

This document is source coverage only. It does not yet provide structured
rulebook YAML, generated chunks, or selector evaluation proof.

## Working Definition

For this harness, an MCP server is a deployable service boundary that exposes
governed capabilities, context, or workflows to MCP-capable clients.

The official MCP documentation describes MCP as a protocol for connecting AI
applications to external systems such as data sources, tools, and workflows.
The specification describes servers as services that provide context and
capabilities, with server features including resources, prompts, and tools.

## Why This Matters Here

The harness is being shaped into modular executable layers.

An MCP server may eventually expose one or more of those layers to clients:

- `00.chat` could expose chat lifecycle and git-governance capabilities.
- `01.harness` could expose harness validation, metadata, and governance
  checks.
- `02.rag-rulebook` could expose corpus indexing, recognition sources,
  rulebook chunks, and validated context packets.
- `04.deploy` could expose runtime and deployment inspection workflows.

The important boundary is that an MCP server should expose governed
capabilities. It should not bypass the harness workflow, approval, evidence, or
commit gates that already protect local execution.

## Initial Architecture Questions

Before this becomes structured rulebook content, the harness needs answers to
these questions:

- Which layer owns each MCP-exposed capability?
- Which capabilities are read-only, write-capable, deploy-capable, or
  destructive?
- Which commands can be exposed as tools, and which must remain internal?
- Which context or corpus resources can be exposed without leaking unrelated
  repo or user data?
- Which prompts or workflows can be exposed as reusable MCP prompts?
- What authentication, authorization, and user-consent model is required?
- What runtime transport and hosting model is allowed for local, staging, and
  production use?
- What audit log records every MCP request, selected tool, approval, and
  command result?
- How are tool schemas versioned so clients do not call stale or unsafe
  contracts?
- What failure modes become blocking stop conditions?

## Governance Expectations

MCP server work must preserve existing harness boundaries:

- Read-only capabilities should stay read-only unless a workflow explicitly
  grants write behavior.
- Tool execution should require the same approval and stop-condition logic as
  direct chat execution.
- Deploy-capable tools should belong to deployment governance, not general
  prompt recognition.
- RAG/rulebook tools should return validated context packets or explicit gaps,
  not unvalidated long-form context dumps.
- Missing source, missing corpus coverage, missing auth, or missing audit
  behavior should block production exposure.

## Candidate Coverage Status

This document provides the `source_material` stage for the MCP server
recognition candidate.

The structured rulebook stage is now present at
`docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml`.

The indexed chunks stage is now present through the rulebook index and chunk
generator smoke tests, which assert MCP server chunks are emitted from the
structured YAML.

The selector evaluation stage is now present through the MCP server planning
fixture, which proves the example prompt retrieves covered MCP server rulebook
chunks without treating the request as deploy execution.

## External References

- Official MCP introduction: https://modelcontextprotocol.io/docs/getting-started/intro
- MCP specification, version 2025-11-25: https://modelcontextprotocol.io/specification/2025-11-25
