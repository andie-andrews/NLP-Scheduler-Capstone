---
marp: true
theme: default
paginate: true
title: NLP Scheduler Capstone Demo
---

# NLP Scheduler Capstone Demo
## Natural Language Scheduling Agent for API-Driven Workforce Management

- Conversational scheduling for managers and employees
- Built with a .NET Scheduler API + Python Streamlit + LLM orchestrator
- Demo focus: API-first operations through natural language

<!--
Speaker notes:
Welcome everyone. This capstone demonstrates how natural language can sit on top of an existing scheduling API so users can complete operational tasks quickly without navigating complex forms. I’ll walk through the problem, architecture, key features, and a live demo flow.
-->

---

# 1) Problem Statement + Accessibility Solution

## Scheduling is urgent, complex, and not always desk-friendly

- Employees need quick answers without opening and navigating an app
- Managers need to create, update, and review shifts quickly
- Traditional workflows require multiple screens or direct API knowledge
- Employees and supervisors often need schedule info while on the go
- Non-neurotypical users may benefit from voice-first, low-friction task support

## Solution impact (especially for voice-reliant workflows)

- Natural language reduces cognitive switching and navigation overhead
- Voice assistants (Alexa, Siri, Gemini, Google Assistant) can help users stay on task
- Faster check-ins: “When is my next shift?” or “Who is open Friday evening?”
- Hands-free scheduling support without logging in and navigating multiple screens
- Better accessibility by meeting users in familiar assistant interfaces

<!--
Speaker notes:
This combines the core problem with why the solution matters in day-to-day life for both employees and managers. For users who rely on assistants like Alexa, Siri, or Gemini to stay organized and focused, natural language scheduling can provide quick, hands-free answers without requiring app login and navigation.
-->

---

# 2) API-First Architecture

```text
User (Streamlit Chat/UI)
        |
        v
LLM Orchestrator (intent + parsing + flow state)
        |
        v
OpenAPI Operation Registry (tool schemas)
        |
        v
Scheduler REST API (.NET controllers)
        |
        v
Employees / Schedules / Shifts data
```

- OpenAPI spec drives discoverable operations and tool mapping
- Orchestrator remains thin over stable API contracts
- UI and AI assistant both rely on backend APIs as source of truth

<!--
Speaker notes:
This is intentionally API-first. Instead of hard-coding every behavior in the chat layer, we parse OpenAPI and map operations dynamically. That keeps the assistant aligned with backend capabilities and allows the same API to serve both conversational and traditional UI workflows.
-->

---

# 3) Core Components

## Streamlit App + LLM Engine + Scheduler API

- **Streamlit UI**: login, navigation, schedule management, AI Assistant tab
- **LLM orchestrator**: intent detection, entity resolution, pending-state workflows
- **OpenAPI loader/parser**: turns API routes into callable tool definitions
- **.NET API**: Auth, Employees, Schedules, Shifts endpoints

**Design principle:** conversation coordinates actions; API enforces business operations.

<!--
Speaker notes:
Think of this as layered responsibilities. Streamlit handles interaction, orchestrator handles reasoning and follow-up logic, and the backend API handles persistent business operations. This separation makes the system easier to test, evolve, and deploy.
-->

---

# 4) Key Features Delivered

- Natural language shift creation, update, and deletion flows
- Employee and schedule resolution from ambiguous user input
- Follow-up prompts for missing required parameters
- Shift summaries and lightweight metrics in chat responses
- Session memory for multi-turn conversations
- Role-aware UI with manager/employee views

<!--
Speaker notes:
The important part is reliability across multi-turn interactions. If users provide partial information, the assistant keeps context and asks only for what’s missing. This supports realistic manager behavior where requests are often short and incomplete.
-->

---

# 5) LLM Orchestrator Deep Dive

## Why orchestration (not just one-shot prompting)?

- Detects scheduling intent (create/update/delete/show)
- Parses date/time/duration and recurring patterns
- Resolves names to internal IDs via API lookups
- Stores pending flow state until all required fields are complete
- Executes final API call + returns structured summary

**Outcome:** predictable, auditable automation instead of brittle prompt-only behavior.

<!--
Speaker notes:
A simple chatbot often fails in real operations because requests are ambiguous. Our orchestrator behaves more like a workflow engine with guardrails, using deterministic parsing and state machines around the LLM to improve consistency.
-->

---

# 6) Streamlit UI Experience

## Practical operator workflow

- Sidebar navigation + secure login
- Dedicated **AI Assistant** workspace with persistent chat history
- “New chat” resets pending flow state cleanly
- Rich response rendering for shift totals and per-shift cards
- Complements existing management tabs instead of replacing them

<!--
Speaker notes:
The UI is designed for adoption. Teams can still use classic pages for detailed edits, while the assistant accelerates common actions. This reduces change risk because conversational workflows are additive, not disruptive.
-->

---

# 7) Demo Flow (Live Walkthrough)

1. Login as manager in Streamlit
2. Open AI Assistant
3. Ask: “Schedule Alex next Tuesday 9am for 6 hours”
4. Assistant resolves employee + schedule (or asks clarifying question)
5. Assistant confirms/executes create-shift API call
6. Ask: “Show me total hours for this week”
7. Review summarized shift metrics/cards
8. Update or delete a shift with follow-up confirmation

<!--
Speaker notes:
During demo, emphasize the clarification loop and API-backed execution. If the assistant cannot disambiguate confidently, it asks for a specific selection rather than guessing. That behavior is key for manager trust.
-->

---

# 8) Technical Challenges & Next Steps

## Challenges

- Ambiguous language (names, dates, intent overlap)
- Entity disambiguation and validation safety
- Balancing LLM flexibility with deterministic control
- Evolving API schemas and integration reliability

## Next Steps

- Add MCP-based tool/resource providers for broader integrations
- Introduce proactive conflict detection and recommendations
- Add observability dashboards (latency, fallbacks, failure rates)
- Expand omnichannel interfaces (mobile + voice assistant integration)

<!--
Speaker notes:
Close by framing this as a foundation. We’ve proven end-to-end orchestration on real API operations. The next phase focuses on reliability at scale, smarter scheduling intelligence, and broader interface channels including voice ecosystems.
-->
