# `orchestrator_v2.py` Refactor Plan (SOLID-first)

## Why refactor now

`app/llm/orchestrator_v2.py` currently combines many unrelated responsibilities:

- intent detection
- natural language parsing
- entity resolution (employee/schedule)
- flow state management
- API tool schema generation
- OpenAI tool orchestration
- create/delete shift flow logic
- response summarization

This makes the file hard to read, hard to test in isolation, and risky to modify.

---

## Target architecture

Split into small, cohesive units grouped by responsibility:

```text
app/llm/orchestrator/
  __init__.py
  orchestrator.py              # thin coordinator only
  contracts.py                 # interfaces/protocols (dependency inversion)
  context.py                   # session + request context
  state_store.py               # pending flow get/set/clear
  intent_detector.py           # create/delete/general intent checks
  parsers.py                   # weekday, duration, schedule name extraction
  resolvers.py                 # employee/schedule resolution logic
  flows/
    create_shift_flow.py       # create-shift state machine
    delete_shift_flow.py       # delete-shift state machine
  tools/
    schema_builder.py          # OpenAPI -> function tools
    sanitizer.py               # OpenAI tool schema sanitizer
  postprocess/
    shift_summary.py           # summarize shifts + NL follow-up
```

Keep `app/llm/orchestrator_v2.py` as a compatibility shim that calls into the new package until migration is complete.

---

## SOLID mapping

### 1) Single Responsibility Principle (SRP)
Each module should have one reason to change:

- `parsers.py` changes when language patterns change.
- `resolvers.py` changes when lookup strategy changes.
- `create_shift_flow.py` changes when create flow rules change.
- `schema_builder.py` changes when tool schema format changes.

### 2) Open/Closed Principle (OCP)
Add new intents/flows without touching existing core coordinator:

- New flow: `flows/update_shift_flow.py`
- Register it in a flow registry rather than adding deep `if/else` chains.

### 3) Liskov Substitution Principle (LSP)
Use consistent flow contracts (same input/output shape), so any flow can replace another in orchestrator dispatch without breaking caller behavior.

### 4) Interface Segregation Principle (ISP)
Split broad dependencies into focused interfaces:

- `EmployeeResolver` interface
- `ScheduleResolver` interface
- `LLMClient` interface
- `SchedulerAPI` interface

Consumers depend only on what they use.

### 5) Dependency Inversion Principle (DIP)
`run_orchestrator` depends on abstractions (`contracts.py`) rather than direct OpenAI/API globals.

This allows:

- mock clients for tests
- easier migration between LLM providers
- cleaner local unit tests without network calls

---

## Suggested data contracts

Use typed dataclasses (or Pydantic models) for state and flow outputs.

```python
@dataclass
class CreateShiftState:
    employee_id: int | None = None
    schedule_id: int | None = None
    start_iso: str | None = None
    duration_hours: int | None = None
    awaiting: str | None = None
    employee_options: list[dict] = field(default_factory=list)
    schedule_options: list[dict] = field(default_factory=list)
```

Benefits:

- self-documenting state
- fewer typo bugs from raw dict keys
- easier validation and autocomplete

---

## Refactor sequence (safe, incremental)

### Phase 1: Pure helper extraction (lowest risk)
Move pure functions first (no side effects):

- `extract_duration_hours`
- `extract_weekday_datetime`
- `extract_weekday_date`
- `extract_schedule_name`
- `summarize_shifts`
- `get_week_start`

No behavioral changes expected.

### Phase 2: State management extraction
Move pending flow state get/set/clear into `state_store.py` with typed wrappers.

### Phase 3: Resolver extraction
Move employee/schedule resolver functions into `resolvers.py` and inject API dependency.

### Phase 4: Flow objects
Implement `CreateShiftFlow` and `DeleteShiftFlow` classes (or functions) with a shared contract:

```python
class Flow(Protocol):
    def can_handle(self, message: str, context: OrchestratorContext) -> bool: ...
    def handle(self, message: str, context: OrchestratorContext) -> FlowResult: ...
```

### Phase 5: Thin orchestrator
Reduce `run_orchestrator` to:

1. Build context
2. Pick matching flow
3. Fallback to tool-calling handler
4. Return standardized response

---

## Testing strategy

### Unit tests (fast)
- parsers (date/time/duration edge cases)
- resolvers (not found/exact match/disambiguation)
- create/delete flow transitions
- tool sanitizer and schema builder

### Integration tests
- create shift happy path
- create shift disambiguation path
- delete shift multi-option selection
- fallback tool call path

### Regression checks
Use a fixture set of user prompts from production logs (anonymized) to compare old vs new outputs.

---

## Practical coding rules for this repo

- Keep side effects at boundaries (API + LLM calls).
- Keep flow logic deterministic where possible.
- Prefer dependency injection over module globals.
- Keep each function below ~40 lines unless justified.
- Favor explicit return objects over mixed string/dict return types.

---

## Immediate next step (small PR)

A good first PR would only:

1. Create `app/llm/orchestrator/parsers.py` and `postprocess/shift_summary.py`
2. Move pure helper functions there
3. Import them back into `orchestrator_v2.py`
4. Add unit tests for parser behavior

This gives quick wins in readability and testability without risky behavior changes.
