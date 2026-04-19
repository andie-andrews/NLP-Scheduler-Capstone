# Orchestration Platform Decision: .NET vs Python

## Short answer

Yes, .NET can fully orchestrate this assistant.

The current implementation uses .NET orchestration with OpenAPI-driven tool calling so intent mapping is handled primarily by the model, not handwritten intent trees.

## How intent is handled now

- Load Scheduler OpenAPI spec.
- Generate tool definitions from OpenAPI operations.
- Let the model choose tool + arguments.
- Execute operation and return tool output for final response.

## "Training" clarification

For this app, the right approach is runtime tool grounding (OpenAPI as tools), not custom model training/fine-tuning.
