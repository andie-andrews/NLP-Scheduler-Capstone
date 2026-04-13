# MCP Integration Guide for NLP Scheduler Capstone

This project is a strong candidate for integrating the Model Context Protocol (MCP).

## Why MCP fits this app

The current assistant architecture already has three MCP-like building blocks:

1. **Tool invocation abstraction** via `build_tools(...)` and `sanitize_tools_for_openai(...)`.
2. **Operation registry** via OpenAPI parsing (`parse_operations(...)`) and operation IDs.
3. **Orchestration layer** (`orchestrator_v2`) that handles intent, clarifications, disambiguation, and API execution.

MCP can formalize these integrations so your assistant can discover and use resources/tools through MCP servers, rather than only from code-local adapters.

## High-level target architecture

- Keep the current orchestrator and UI.
- Add an **MCP client adapter** in Python to connect to one or more MCP servers.
- Expose your scheduler API and domain helpers as MCP tools/resources.
- Let the orchestrator decide whether to call:
  - local OpenAPI-derived tools (existing path), or
  - MCP-discovered tools/resources (new path).

## Recommended implementation steps

### 1) Introduce a tool-provider interface

Create a small abstraction for tool sources, e.g.:

- `OpenApiToolProvider` (current logic)
- `McpToolProvider` (new)

Both should provide:

- `list_tools()`
- `invoke_tool(name, args)`
- optional `list_resources()` / `read_resource(uri)`

This minimizes changes in `orchestrator_v2` because it can remain provider-agnostic.

### 2) Start with one MCP server for scheduler operations

Stand up an MCP server that wraps:

- shifts CRUD
- schedules CRUD
- employee search/resolution helpers

In practice, start with read-heavy operations first (`get shifts`, `get employees`) to validate transport, auth, and schema mapping before mutation endpoints.

### 3) Add MCP resource support for context

Expose stable domain context as MCP resources, for example:

- current schedule list
- employee directory snapshot
- role definitions/business constraints

The assistant can read these quickly without repeatedly calling your REST API for every turn.

### 4) Add routing logic in orchestrator

Add a simple routing policy:

- Use local OpenAPI path by default.
- If a requested capability exists in MCP with higher confidence (or richer metadata), use MCP.
- Fall back to local OpenAPI tools if MCP fails/timeouts.

This gives you incremental adoption and avoids a risky full migration.

### 5) Keep pending-flow state unchanged

Your pending flows (`create_shift`, `update_shift`, `delete_shift`, employee/schedule disambiguation) are valuable app logic and should stay in-process.

Only replace the execution backend (tool invocation), not conversation state logic.

### 6) Add observability and guardrails

Track:

- tool selected (OpenAPI vs MCP)
- latency and error rates by tool source
- fallback frequency

Add guardrails:

- idempotency keys for create/update operations where possible
- explicit confirmation for destructive actions
- retries only for safe operations

### 7) Security and identity propagation

Propagate user identity/token from Streamlit session into MCP calls.

Enforce:

- least-privilege access per role
- server-side authorization checks
- audit logs for write/delete actions

### 8) Rollout plan

1. **Phase 1:** read-only MCP tools (employee/schedule lookups).
2. **Phase 2:** create/update shift through MCP behind feature flag.
3. **Phase 3:** delete/advanced operations + partial deprecation of direct OpenAPI path.

## Benefits you should expect

### Product benefits

- Faster expansion: add new capabilities by publishing MCP tools/resources rather than editing orchestration internals each time.
- Better interoperability: same scheduler tools can be reused by other MCP-capable agents/clients.
- Easier multi-system workflows: connect HR, payroll, or time-clock systems as additional MCP servers.

### Engineering benefits

- Cleaner separation of concerns (orchestration vs execution backends).
- Stronger extensibility with a standard protocol for tools/resources.
- Improved maintainability and testability of integrations.

### Operations benefits

- Better observability over tool usage and failure domains.
- Safer rollouts through fallback to your current OpenAPI pipeline.
- Reduced coupling to one API schema evolution path.

## Risks and mitigations

- **Added infrastructure complexity** → start with one MCP server + read-only operations.
- **Latency overhead** → cache stable resources and apply timeout/fallback policy.
- **Schema drift** between MCP and OpenAPI → contract tests for shared operations.

## Practical first milestone (1–2 days)

1. Add a provider interface + `OpenApiToolProvider` wrapper around current behavior.
2. Implement a minimal `McpToolProvider` with one read tool (`search employees`).
3. Route one intent path (`who is scheduled` / employee lookup) through MCP.
4. Measure latency and reliability, then expand.

