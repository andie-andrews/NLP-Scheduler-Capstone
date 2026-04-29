# Appcode-Oriented Orchestration Guide

This document explains what changed in the assistant orchestration architecture, why it was done, and how other teams can onboard additional applications.

## What changed

The assistant runtime now supports a centralized, appcode-oriented orchestration model:

- Requests can be routed by **required `appcode`** in the v2 assistant API.
- App-level behavior is configured in one registry: `app/config/app_registry.json`.
- Routing is split into composable layers:
  - appcode resolution
  - domain/workflow routing
  - prompt composition
  - flow dispatch validation
  - domain runtime execution

### Key components

- **HTTP v2 route:** `app/api/routes.py`
  - `POST /api/v2/assistant/chat`
  - `DELETE /api/v2/assistant/chat/{conversation_id}`
- **Request/response contracts:** `app/api/request_models.py`
- **Session/auth store:** `app/api/session_store.py`
- **App registry loader:** `app/orchestration/appcode_resolver.py`
- **Domain/workflow router:** `app/orchestration/domain_router.py`
- **Prompt composer:** `app/orchestration/prompt_composer.py`
- **Flow metadata + dispatcher:**
  - `app/orchestration/flow_metadata.py`
  - `app/orchestration/flow_dispatcher.py`
- **Domain runtime dispatch:**
  - `app/orchestration/domain_executors.py`
  - `app/orchestration/engine.py`

## Why this was done

1. **Explicit app routing:**
   The API now requires appcode so requests are deterministically scoped per application.

2. **Centralized config:**
   Prompt layers, domains, workflows, and cross-domain allowlists are declared in one place (`app_registry.json`) instead of spread across code constants.

3. **Safer policy enforcement:**
   Cross-domain routing and workflow allowlisting are validated in orchestration before runtime execution.

4. **Extensibility:**
   New applications can be added by config + targeted intent/workflow handling without rewriting API scaffolding.

## How to add a new application

Use this checklist when onboarding a new appcode (example: `inventory`).

### 1) Add the app to registry

Update `app/config/app_registry.json`:

- Add app entry under `apps.<appcode>` with:
  - `primary_domain`
  - `domain_priority`
  - `max_cross_domain_hops`
  - `prompts` (`global`, `appcode`, `domains`, `flows`, `roles`)
  - `domains.<domain>.workflows`
  - `domains.<domain>.plugin` (for example: `legacy_orchestrator` or your custom plugin)
  - `cross_domain` allowlists
- Add workflow->handler mappings to top-level `workflow_handlers` for each new workflow key.

### 2) Ensure workflow inference exists

Update `app/orchestration/domain_router.py`:

- Add or reuse intent checks in `infer_workflow_from_message(...)` so user messages can map to your new workflow keys.
- Keep workflow keys aligned with `app_registry.json`.

### 3) Add/extend flow handlers

Also register or implement the domain runtime plugin in `app/orchestration/domain_plugins.py` and reference it from `domains.<domain>.plugin` in registry.


Update the runtime flow handling path used by your app workflows:

- Add handler implementations in existing orchestration runtime modules.
- Ensure handler names match `workflow_handlers` values in registry.

### 4) Validate dispatch metadata

`app/orchestration/flow_dispatcher.py` uses:

- domain ownership from registry (`build_workflow_domain_map`)
- handler mapping from registry (`get_workflow_handler`)

So you must keep registry definitions complete and consistent.

### 5) Add API client appcode usage

Any client calling v2 assistant API must send:

```json
{
  "appcode": "<your-appcode>",
  "message": "..."
}
```

For the React app, this is set in `reactUI/src/components/AssistantChat.tsx`.

### 6) Add/adjust tests

At minimum:

- appcode resolution test
- directional routing/cross-domain policy tests
- prompt composition test
- flow dispatcher policy tests
- integration tests for allowlisted and blocked cross-domain scenarios

Use current tests under `tests/unit` and `tests/integration` as templates.

## Areas teams need to update for their app

When another team adds support for their app, they should coordinate updates across these areas:

1. **Configuration**
   - `app/config/app_registry.json`

2. **Routing semantics**
   - `app/orchestration/domain_router.py`
   - intent parsing modules used by router

3. **Execution logic**
   - existing orchestrator/flow runtime modules
   - any app-specific handler modules

4. **Client request payloads**
   - frontend/backend clients to send the correct `appcode`

5. **Operational settings**
   - CORS origins and environment variables (`app/.env.example`, deployment config)

6. **Quality gates**
   - unit/integration tests for routing and policy enforcement

## Migration notes

- Legacy endpoint (`/api/assistant/chat`) remains for compatibility.
- New features should target v2 (`/api/v2/assistant/chat`) with required `appcode`.
- If a team sees cross-origin browser failures, confirm `ASSISTANT_API_ALLOW_ORIGINS` includes their exact origin (scheme + host + port).

## Troubleshooting quick checks

1. Unknown appcode errors
   - Verify app exists in `app_registry.json` under `apps`.

2. Workflow blocked/not configured
   - Verify workflow appears under the app's domain workflows.
   - Verify cross-domain allowlist includes workflow if target is non-primary domain.

3. Handler missing errors
   - Verify workflow exists in top-level `workflow_handlers`.

4. CORS issues
   - Verify browser origin is present in `ASSISTANT_API_ALLOW_ORIGINS`.
