# Backend and GenAI Build Guide

This guide explains how to build the backend for this DQ Agent learning project, with extra focus on the GenAI design decisions. The goal is not only to make the app work, but to understand why each backend piece exists.

The project backend is a FastAPI service that uses an LLM to:

1. Inspect uploaded CSV metadata.
2. Suggest useful data quality rules.
3. Generate Python validation code for the selected rules.
4. Review the generated code.
5. Execute the generated validation logic and stream results back to the frontend.

Current backend location:

```text
backend/
  api.py
  main.py
  pyproject.toml
  src/dq_agent/
    state.py
    graph.py
    thread_manager.py
    api/
      models.py
      rules_routes.py
      thread_routes.py
      utils.py
    nodes/
      load_data.py
      rule_generator.py
      code_generator.py
      code_validator.py
      code_executor.py
      result_formatter.py
```

## 1. Choose the Backend Shape

For this project, the backend has two jobs:

1. Act like a normal web API.
2. Act like an AI workflow engine.

FastAPI handles the web API part. LangGraph-style nodes handle the AI workflow part.

Conceptually, split the backend into these layers:

```text
Frontend
  |
FastAPI routes
  |
Thread/session manager
  |
Agent state
  |
Workflow nodes
  |
LLM, pandas, generated code execution
```

Why this split matters:

- FastAPI should know about HTTP, files, request bodies, and streaming responses.
- The agent workflow should know about data, rules, prompts, generated code, and execution results.
- The thread manager should preserve state between user actions.
- The LLM should be called from isolated nodes so prompts and model behavior are easy to improve.

## 2. Create the Backend Project

Use Python 3.12 because `backend/pyproject.toml` requires it.

```bash
cd backend
uv venv
source .venv/bin/activate
uv sync
```

Create a `.env` file:

```bash
OPENAI_API_KEY=your_api_key_here
```

Core dependencies:

- `fastapi`: HTTP API framework.
- `uvicorn`: ASGI server for FastAPI.
- `python-multipart`: file upload support.
- `pandas`: CSV parsing and validation execution.
- `python-dotenv`: loads `.env`.
- `langchain-openai`: OpenAI chat model wrapper.
- `langgraph`: graph-based agent orchestration.

## 3. Define the Agent State First

Start with `backend/src/dq_agent/state.py`.

The state object is the shared memory passed between workflow nodes. In this project, `DQState` contains:

- Input paths: uploaded CSV and rules file paths.
- Data profile: columns, dtypes, sample data serialized as JSON.
- User rules: original rules from the user.
- AI rules: rules suggested by the model.
- Generated code: Python code produced by the model.
- Execution results: pass/fail result dictionaries.
- Final report: human-readable output.
- Errors: accumulated failures from each step.

The key learning point: agent state is the contract between nodes. Each node should read only what it needs and return only the fields it updates.

Example mental model:

```text
load_data_node
  reads: csv_path, rules_path
  writes: dataframe_json, columns, dtypes, rules

rule_generator_node
  reads: columns, dtypes, dataframe_json, metadata, rules
  writes: all_rules

code_generator_node
  reads: all_rules, dataframe_json, columns, dtypes, metadata
  writes: generated_code

code_validator_node
  reads: generated_code, rules
  writes: validation_passed, validation_details

code_executor_node
  reads: generated_code, dataframe_json
  writes: execution_results
```

For learning projects, it is tempting to pass loose dictionaries everywhere. `TypedDict` is a good compromise: simple enough for experimentation, but explicit enough to understand the workflow.

## 4. Build the File Loading Node

File: `backend/src/dq_agent/nodes/load_data.py`

This node does deterministic work, not GenAI work.

Responsibilities:

1. Read the uploaded CSV using pandas.
2. Convert the DataFrame to JSON records.
3. Extract column names.
4. Extract pandas dtypes.
5. Read user-provided rules from a text file.

Why it matters for GenAI:

LLMs should not receive the entire dataset unless the dataset is tiny. They need a compact data profile:

- column names
- data types
- a few sample rows
- optional column descriptions
- existing user rules

This keeps prompts cheaper, faster, and less likely to leak unnecessary data.

Good practice:

- Send only the first 5 to 10 rows as sample data.
- Avoid sending personally identifiable data in production.
- Add profiling later: null counts, unique counts, min/max, regex-like patterns, and frequent values.

## 5. Add Thread-Based State

File: `backend/src/dq_agent/thread_manager.py`

The frontend flow is multi-step:

1. Create thread.
2. Upload CSV and optional rules.
3. Review AI-suggested rules.
4. Edit/delete rules.
5. Confirm and run validation.

HTTP is stateless, so the backend needs a way to remember what happened in step 2 when the user reaches step 5.

The current `ThreadManager` stores this in memory:

- `thread_id`
- `created_at`
- `updated_at`
- `phase`
- `state`

Important concept: phase is a lightweight state machine.

Current phases include:

```text
created -> rules_loaded -> generating -> validating -> executing -> complete
```

For a learning project, in-memory state is fine. For production, move this to Redis, Postgres, or another persistent store.

## 6. Create the FastAPI App

File: `backend/api.py`

The API layer:

1. Loads environment variables.
2. Creates the FastAPI app.
3. Enables CORS for frontend dev servers.
4. Mounts route modules.
5. Checks whether `OPENAI_API_KEY` is available.

Run it with:

```bash
cd backend
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

Design rule: keep `api.py` small. Put endpoint behavior in route modules and AI behavior in nodes.

## 7. Build Thread Routes

File: `backend/src/dq_agent/api/thread_routes.py`

Endpoints:

- `POST /thread/create`: create a conversation thread.
- `GET /thread/{thread_id}`: check thread phase.
- `DELETE /thread/{thread_id}`: delete thread state and temp files.

These routes are intentionally boring. That is good design. They should not know about prompts, pandas, or generated code.

## 8. Build Rules and Validation Routes

File: `backend/src/dq_agent/api/rules_routes.py`

This is the main backend orchestration file.

Important endpoints:

### `POST /thread/{thread_id}/load-rules`

This endpoint:

1. Receives CSV upload.
2. Receives optional rules text/file.
3. Receives optional metadata text/file.
4. Saves uploaded content to temporary files.
5. Initializes `DQState`.
6. Calls `load_data_node`.
7. Calls `rule_generator_node`.
8. Stores state in `ThreadManager`.
9. Returns rules for frontend review.

GenAI concept: this endpoint performs AI-assisted rule discovery, but it does not yet execute anything. That gives the human user a review step before generated code is created.

### `PUT /thread/{thread_id}/rules`

This endpoint lets the frontend send edited/deleted rules back to the backend.

This is important because AI suggestions should be treated as drafts, not truth. The human reviewer stays in control.

### `POST /thread/{thread_id}/confirm`

This endpoint streams the final workflow:

1. Generate code from confirmed rules.
2. Validate generated code.
3. Execute generated code.
4. Format final results.
5. Send Server-Sent Events to the frontend.

The app uses SSE instead of waiting for one large response. This makes the UI feel responsive and teaches a useful pattern for AI apps: stream progress events, not only final text.

## 9. GenAI Step 1: Generate Data Quality Rules

File: `backend/src/dq_agent/nodes/rule_generator.py`

The rule generator asks the model to inspect dataset metadata and suggest useful validation rules.

Inputs to the prompt:

- columns
- dtypes
- sample rows
- column metadata
- user-provided rules

Output expected from the model:

```json
[
  "Check that 'email' column contains valid email addresses",
  "Ensure 'age' column values are between 0 and 120"
]
```

Important prompt design choices:

1. Give the model a role: "You are a data quality expert."
2. Provide compact structured context.
3. Tell it what to consider.
4. Tell it what not to do: do not duplicate user rules.
5. Force a machine-readable output: JSON array only.

Temperature is set to `0.3`.

Why not `0`? Rule suggestion is partly creative. A little variation can help. For code generation, use `0` because consistency matters more.

Learning concept: LLMs are good at semantic inference. If a column is named `email_address`, the model can infer an email-format rule. If metadata says `status must be ACTIVE, INACTIVE, or PENDING`, the model can infer an allowed-values check.

Current limitation:

The code manually strips markdown fences and parses JSON. A stronger version would use structured outputs or a Pydantic schema so the model is constrained to valid JSON.

Better future shape:

```python
class GeneratedRules(BaseModel):
    rules: list[str]
```

Then ask the model for structured output matching that schema.

## 10. GenAI Step 2: Generate Validation Code

File: `backend/src/dq_agent/nodes/code_generator.py`

This node turns natural-language rules into executable pandas code.

The model is instructed to generate:

```python
def validate_dq_rules(df):
    ...
    return [
        {"rule": "...", "passed": True, "details": "..."}
    ]
```

Why generate code instead of asking the model to directly validate the data?

Because code is:

- repeatable
- inspectable
- easier to debug
- cheaper to run on larger data
- deterministic once generated

The LLM translates rule intent into pandas operations. Pandas then performs the actual checks.

Prompt inputs:

- columns
- dtypes
- sample rows
- column metadata
- confirmed rules

Prompt constraints:

- return only Python code
- define `validate_dq_rules`
- return a list of dictionaries
- include original rule text
- use pandas operations
- handle edge cases

Temperature is set to `0` because code generation should be as deterministic as possible.

Important learning concept: natural language is ambiguous. The generated code is the model's interpretation. That is why this project exposes the generated code in the streamed response.

Common failure modes:

- Model references a column that does not exist.
- Model assumes a date format incorrectly.
- Model treats null values as failures when the business rule allows nulls.
- Model generates code with imports or operations you do not want.
- Model returns markdown despite being told not to.

Mitigations:

- Include exact column names.
- Include sample data.
- Include metadata.
- Validate generated code before execution.
- Add tests with tricky CSVs.
- Consider a rule DSL later for high-confidence checks.

## 11. GenAI Step 3: Validate Generated Code

File: `backend/src/dq_agent/nodes/code_validator.py`

This project uses two validation layers:

1. AST validation.
2. LLM self-review.

### AST validation

AST means Abstract Syntax Tree. Python can parse source code into a tree structure before executing it.

This lets the backend inspect generated code and reject risky constructs.

Current checks include:

- forbidden imports
- forbidden calls like `eval`, `exec`, `open`, `input`
- suspicious operations like `os.system` or `subprocess`
- `with` statements, because they can indicate file access

This is deterministic and should be treated as the first safety gate.

### LLM self-review

The second pass asks an LLM to review the generated code for:

- security issues
- logic errors
- edge cases
- output format

This is useful but should not be your only safety mechanism. LLM review can miss problems. Deterministic checks should always come first.

Important note about the current implementation:

The route streams a `validation_failed` event if validation fails, but then continues execution. For a stricter backend, stop execution when validation fails.

Safer learning improvement:

```python
if not state.get("validation_passed", True):
    yield validation_failed
    return
```

## 12. Execute Generated Code Carefully

File: `backend/src/dq_agent/nodes/code_executor.py`

This node:

1. Recreates a pandas DataFrame from JSON.
2. Defines a restricted import function.
3. Builds a limited execution environment.
4. Calls `exec` on the generated code.
5. Looks for `validate_dq_rules`.
6. Runs that function against the DataFrame.
7. Returns execution results.

This is the riskiest part of the system because generated code is being executed.

Learning concept: `exec` is powerful and dangerous. It should never be used casually with untrusted code. This project reduces risk with AST checks and restricted imports, but it is still not a production sandbox.

Production-grade options:

- Do not generate Python code. Generate a constrained JSON rule plan and interpret it yourself.
- Run generated code in an isolated container.
- Use a short timeout.
- Limit memory.
- Disable network access.
- Run under a low-permission user.
- Block filesystem access.
- Keep an audit trail of generated code.

For a learning project, this pattern is valuable because it teaches how LLMs can produce executable artifacts, but always treat the execution boundary as high risk.

## 13. Format Results

File: `backend/src/dq_agent/nodes/result_formatter.py`

This deterministic node converts raw execution results into a readable report.

The result format from generated code should look like:

```json
[
  {
    "rule": "Check that 'email' contains valid email addresses",
    "passed": false,
    "details": "3 rows contain invalid email addresses"
  }
]
```

The formatter counts passed and failed rules and creates a final report.

Learning point: keep final formatting deterministic unless you truly need an LLM-written narrative. For data quality results, exact counts matter more than fluent prose.

## 14. Optional LangGraph Wiring

File: `backend/src/dq_agent/graph.py`

The graph currently shows a linear workflow:

```text
load_data -> code_generator -> code_executor -> result_formatter
```

In the route-based flow, `rules_routes.py` manually calls nodes because the frontend needs a human review step after AI rule generation.

This is a useful distinction:

- Use a graph when the workflow can run end-to-end.
- Use route-level orchestration when the user must pause, inspect, edit, and confirm.

A fuller graph could look like:

```text
load_data
  -> rule_generator
  -> human_review_pause
  -> code_generator
  -> code_validator
  -> code_executor
  -> result_formatter
```

LangGraph is especially useful when you add:

- branching
- retries
- conditional validation failures
- tool calls
- checkpointing
- long-running workflows

## 15. Design the GenAI Workflow Like a Compiler

This project is easier to understand if you think of it like a compiler pipeline:

```text
CSV + metadata
  -> data profile
  -> natural-language DQ rules
  -> generated Python validation function
  -> reviewed code
  -> executed checks
  -> structured results
  -> final report
```

The LLM performs translation steps:

- data profile -> candidate rules
- rules -> validation code
- code -> review feedback

Pandas performs actual validation.

This separation is important. The LLM should help design checks. It should not be the only judge of whether rows pass or fail.

## 16. Prompt Engineering Principles Used Here

The project prompts demonstrate several core ideas.

### Provide role and task

Example:

```text
You are a data quality expert.
```

This helps anchor the model's behavior.

### Provide compact context

Do not paste an entire CSV. Give columns, dtypes, metadata, and sample rows.

### Constrain the output

For rule generation:

```text
Return ONLY a JSON array of rule strings.
```

For code generation:

```text
Return ONLY the Python code.
```

### Include negative instructions

Example:

```text
Do NOT duplicate any user-provided rules.
```

### Define an interface

For code generation, the interface is:

```python
def validate_dq_rules(df):
    ...
```

This makes generated code callable by the backend.

### Prefer structured outputs where possible

The current project parses JSON manually. That is okay for learning. For reliability, use structured output APIs or Pydantic parsers.

## 17. Suggested Step-by-Step Build Order

If you were rebuilding the backend from scratch, use this order:

1. Create `pyproject.toml` with FastAPI, pandas, LangChain/OpenAI, LangGraph, and dotenv.
2. Create `api.py` with a health route and CORS.
3. Create `state.py` with `DQState` and `Rule`.
4. Create `thread_manager.py`.
5. Add `POST /thread/create` and `GET /thread/{id}`.
6. Add file upload handling in `load-rules`.
7. Implement `load_data_node`.
8. Return columns and dtypes to verify upload parsing.
9. Add `rule_generator_node`.
10. Return user rules plus LLM rules with source tags.
11. Add `PUT /rules` so users can edit/delete suggestions.
12. Add `code_generator_node`.
13. Stream generated code with SSE.
14. Add AST validation.
15. Add LLM self-review.
16. Add code execution in a restricted environment.
17. Add result formatting.
18. Add frontend integration.
19. Add tests for each node.
20. Add production hardening only after the learning flow works.

## 18. Testing Strategy

Start with node-level tests because each node has a clear input/output contract.

Useful tests:

- `load_data_node` reads CSV and returns expected columns/dtypes.
- `rule_generator_node` handles invalid LLM JSON gracefully.
- `code_generator_node` returns a function named `validate_dq_rules`.
- `code_validator_node` blocks `open`, `eval`, `subprocess`, and unknown imports.
- `code_executor_node` rejects code without `validate_dq_rules`.
- `result_formatter_node` counts pass/fail results correctly.

For LLM-dependent tests, use mocks. Do not call the real OpenAI API in normal unit tests.

Example concept:

```text
Mock ChatOpenAI response -> run node -> assert parsed state update
```

Add a few end-to-end tests later with a small CSV:

```csv
id,email,age,status
1,a@example.com,25,ACTIVE
2,bad-email,140,UNKNOWN
3,,30,ACTIVE
```

Expected checks:

- email format fails
- age range fails
- status allowed values fails
- missing email fails if completeness rule is selected

## 19. Improvements Worth Building Next

For learning, these are high-value upgrades:

1. Use structured outputs for rule generation instead of manual JSON cleanup.
2. Stop execution when code validation fails.
3. Add retries: if generated code fails validation, send errors back to the model and regenerate once.
4. Add dataset profiling: null count, unique count, min/max, common values.
5. Add a rule schema or DSL so common checks do not need generated Python.
6. Add persistent thread storage.
7. Add test coverage around dangerous generated code.
8. Add request IDs and logging for each GenAI call.
9. Add token/cost tracking.
10. Add model configuration through environment variables.

## 20. Production Cautions

This project is a strong learning architecture, but production needs more controls.

Be careful with:

- executing generated code
- uploading sensitive data
- storing temporary files
- logging prompts that contain data
- relying on LLM review for security
- allowing large CSV uploads
- keeping state only in memory
- using unbounded API calls

Production-ready direction:

```text
Natural-language rules
  -> structured rule schema
  -> deterministic interpreter
  -> pandas validation
```

Use generated code only when you can run it in a real sandbox.

## 21. The Key GenAI Lesson

The best pattern in this backend is not "ask the LLM for the answer."

The better pattern is:

```text
Use the LLM to propose and translate.
Use deterministic code to verify and execute.
Keep humans in the loop where business meaning matters.
```

For data quality, business meaning matters a lot. The model can suggest that an `amount` column should not be negative, but only the domain expert knows whether refunds, chargebacks, or corrections can legitimately be negative.

That is why this backend has a review step before execution.
