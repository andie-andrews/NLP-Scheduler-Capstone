# Natural Language Scheduling Agent for API-Driven Workforce Management

**Andie Andrews**  
Course Capstone Project Proposal  
FullStack Academy AI/ML  
Cohort 2510-FTB-CT-AIM-PT  

Instructor: Dr. George Perdrizet  
Teacher Assistant: Andrew Thomas  

---

# Section 1: Problem Statement

Modern scheduling systems require users to navigate complex interfaces or APIs to create, retrieve, or modify shifts. These systems are powerful but often inefficient for quick operational tasks such as scheduling an employee, retrieving upcoming shifts, or modifying existing schedules. Users must know the exact fields, parameters, and workflow required by the application.

This project aims to build a **Natural Language Scheduling Agent** that allows users to interact with a scheduling system using conversational language.

For example:

> “Schedule John Doe for a shift Monday at 8am for 8 hours”

The system will interpret the request, determine the correct API endpoint, resolve entities like employee names to internal identifiers, gather missing parameters, and execute the appropriate API request.

Instead of requiring users to understand API structures or application workflows, the system will act as an intelligent intermediary between natural language and structured API operations.

## Why does this problem matter?

Scheduling systems are widely used across industries including retail, healthcare, hospitality, and manufacturing. Managers frequently need to create or adjust schedules quickly while handling other operational tasks.

A natural language interface could significantly improve usability by allowing users to interact with scheduling systems conversationally rather than navigating multiple screens or constructing API requests.

Potential beneficiaries include:

- Operations managers and supervisors  
- Workforce management software users  
- Developers building API-driven scheduling platforms  
- Organizations seeking productivity improvements  

This project also demonstrates how **large language models can be integrated with structured APIs to automate operational workflows.**

---

# Section 2: Project Objectives

## Primary Goal

Build a conversational AI system capable of interpreting natural language scheduling requests and translating them into structured API calls defined by an OpenAPI specification.

## Specific Objectives

### 1. Intent Recognition and API Mapping
Interpret natural language requests and determine which API endpoint should be called based on an OpenAPI specification.

### 2. Entity Resolution and Parameter Extraction
Extract required parameters from user input and resolve entities such as employee names into internal identifiers.

### 3. Conversational Parameter Completion
Detect missing required parameters and prompt the user with follow-up questions to complete the request before executing the API call.

---

# Section 3: Data

## What data will you use?

This project primarily uses **structured API specifications rather than large training datasets**. The OpenAPI specification defines the available routes, request parameters, and response structures used by the scheduling system.

The system will also use a **mock employee dataset** to demonstrate entity resolution (mapping employee names to employee IDs).

Example employee dataset fields:

- employeeId  
- firstName
- lastName  
- department  
- role  

## Data Sources

OpenAPI Specification  
https://swagger.io/specification/

OpenAPI Initiative  
https://www.openapis.org/

## Data Accessibility

Verified accessible: **Yes**

## Data Quality

The OpenAPI specification is structured JSON that clearly defines endpoints, parameters, and request/response schemas.

## Estimated Dataset Size

- OpenAPI specification: ~100 KB  
- Mock employee dataset: < 1 MB  

## Data Limitations

- The system will rely on **mock scheduling APIs rather than a full production backend**
- Employee names may require fuzzy matching
- Natural language input may contain ambiguity requiring clarification

## Licensing

The OpenAPI specification is publicly available.  
All employee data used in this project will be **synthetic mock data**.

---

# Section 4: Approach and Methods

## Technical Approach

The system will act as a **natural language interface for API-driven scheduling systems**.

### Natural Language Understanding

A large language model will interpret user prompts and determine intent.

Example input:

> Schedule John Doe Monday at 8am for 8 hours

The system identifies:

- Intent: Create shift  
- Employee: John Doe  
- Start time: Monday 8:00 AM  
- Duration: 8 hours  

### OpenAPI Tool Mapping

The OpenAPI specification will be parsed to dynamically generate callable tools representing each API route.

Example mapping:

POST /shifts → create_shift  
GET /shifts → get_shifts  
PATCH /shifts/{id} → update_shift  

### Entity Resolution

Employee names extracted from user input will be resolved to internal identifiers using a lookup mechanism.

Example:

resolveEmployee("John Doe") → employeeId: 482913

Fuzzy matching may be used to handle spelling variations.

### Parameter Completion

If required parameters are missing, the system will ask follow-up questions.

Example:

User:  
> Schedule John Monday

System:  
> What time should the shift start?

### Mock Scheduling API

The project will use stubbed API endpoints to simulate scheduling operations.

Example endpoints:

- POST /shifts  
- GET /shifts  
- PATCH /shifts/{shiftId}  
- DELETE /shifts/{shiftId}  

---

## Tools, Libraries, and Frameworks

- Python  
- FastAPI  
- LangChain or agent orchestration framework  
- OpenAI API or similar LLM  
- RapidFuzz (for fuzzy employee matching)  
- Jupyter Notebook  
- Streamlit (optional chat interface)

---

## Techniques and Algorithms

- LLM-based natural language interpretation  
- OpenAPI schema parsing  
- Tool-based API execution  
- Named entity extraction  
- Fuzzy string matching  
- Conversational state tracking

---

# Section 5: Expected Deliverables

The final project will include:

1. A working **Natural Language Scheduling Agent** capable of interpreting scheduling requests and executing API calls.

2. A **chat-based interface** allowing users to create, retrieve, and modify shifts using natural language.

3. A **Jupyter Notebook** documenting development, architecture decisions, and model behavior.

4. A **technical report** explaining the system design, implementation, and evaluation.

5. A **project presentation and live demonstration**.

## Stretch Goals

- Advanced scheduling queries  
- Shift conflict detection  
- Improved entity resolution using embeddings  
- Multi-step scheduling workflows  

---

# Section 6: Success Criteria

The project will be considered successful if the system reliably translates natural language requests into correct scheduling operations.

### Intent Accuracy
Correct identification of API actions such as create, retrieve, or update shifts.

### Parameter Extraction Accuracy
Correct extraction of parameters such as employee name, date, time, and duration.

### Task Completion Rate
Percentage of scheduling requests successfully executed after resolving missing parameters.

### Usability
Users can successfully perform scheduling tasks conversationally without needing to understand API structures.

---

# Section 7: Known Risks and Challenges

### Natural Language Ambiguity

User input may be incomplete or ambiguous.

Mitigation:  
Implement conversational clarification for missing parameters.

### Entity Resolution Issues

Employees may share similar names.

Mitigation:  
Provide disambiguation prompts when multiple matches are found.

### API Mapping Complexity

Some scheduling actions may require multiple API calls.

Mitigation:  
Focus the initial implementation on core actions:

- Create shifts  
- Retrieve shifts  
- Update shifts  

### Model Reliability

Large language models may occasionally produce incorrect outputs.

Mitigation:  
Constrain outputs using tool schemas and validation logic.

---

# Section 8: Resources Needed

- Access to an LLM API (OpenAI or similar)
- Python development environment
- FastAPI for mock scheduling APIs
- GitHub repository for project management
- Optional GPU for experimentation

---

# Section 9: GitHub Repository

Repository URL:
https://github.com/andie-andrews/NLP-Scheduler-Capstone


Example project structure:
```
nlp-scheduler-agent
├── api
├── agent
├── openapi_parser
├── entity_resolution
├── ui
└── notebooks
```
