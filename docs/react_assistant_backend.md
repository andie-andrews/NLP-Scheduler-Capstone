# React AI Assistant Backend

The assistant backend is implemented in .NET at:

- `apis/Assistant.Api/src/Assistant.Api`

It preserves the same frontend API contract.

## API contract

- `GET /health`
- `POST /api/assistant/chat`
  - body: `{ "message": "...", "conversationId": "optional" }`
  - returns: `{ "conversationId": "...", "response": <assistant-response> }`
- `DELETE /api/assistant/chat/{conversationId}`

## OpenAPI-driven orchestration (minimal manual intent code)

The .NET orchestrator now loads `.openapi/scheduler.api.json` and converts operations into OpenAI function tools dynamically.

Flow:
1. User message is sent to OpenAI with generated tools from the OpenAPI spec.
2. Model selects tool(s) and arguments (intent + params decided by model).
3. Backend executes mapped Scheduler API operations.
4. Tool outputs are returned to OpenAI for final assistant response.

This removes most hardcoded intent routing and keeps behavior tied to the OpenAPI contract.

## Can we "train" the model on OpenAPI?

Not in the fine-tuning sense inside this service. Instead, we provide the OpenAPI operations as runtime tools/context each request. This is the correct pattern for intent/action selection over your API surface.

## Environment variables

- `OPENAI_API_KEY` (required)
- `ASSISTANT_OPENAI_MODEL` (default `gpt-4o-mini`)
- `ASSISTANT_API_ALLOW_ORIGINS` (default `*`)
- `ASSISTANT_SESSION_TTL_SECONDS` (default `28800`)
- `SCHEDULER_API_BASE_URL` (default `http://localhost:5048`)
