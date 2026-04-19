# .NET Assistant API and Orchestration Layer Plan

The assistant orchestration is implemented in .NET and is now OpenAPI-driven.

## Architecture

- `Assistant.Api` hosts `/health`, `/api/assistant/chat`, and session lifecycle endpoints.
- `OpenApiToolRegistry` loads `.openapi/scheduler.api.json` and generates tool definitions.
- `OpenAiAssistantOrchestrator` delegates intent/tool selection to the model with those generated tools.
- `SchedulerApiClient` executes the selected OpenAPI operation against `Scheduler.Api`.

## Why this approach

- Minimal manual intent branching in application code.
- Behavior tied to API contract changes in OpenAPI spec.
- Easier to extend tools by updating API spec instead of writing new router logic.

## Important note on "training"

In this architecture we do runtime tool grounding (OpenAPI as tools), not model fine-tuning. The model learns which tool to call from the provided tool set and conversation context each request.
