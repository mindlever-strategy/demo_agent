# MetricAI Multi-Agent Demo — Implementation Plan

## Overview

Build a full-featured multi-agent demo powered by **LangGraph**, integrated with **MetricAI** for cost/session tracking, supporting **all MetricAI-supported providers** (OpenAI, Anthropic, Bedrock) with a frontend provider-switcher. Includes login/signup with local JSON storage and real-time agent execution visibility.

---

## Current State (What Exists)

- Basic FastAPI backend with LangGraph supervisor routing
- 3 sub-agents: Finance, Research, Reporting (all use OpenAI only)
- Login-only auth (no signup), hardcoded demo users in `users.json`
- MetricAI wrapper for tracking (logging only, no proxy metering)
- HTML/CSS/JS frontend with dark theme, sidebar with agent display
- No provider switching, no signup, no detailed execution trace in UI

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (HTML/JS/CSS)                     │
│  ┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │Login/   │  │Provider  │  │Agent Activity │  │Chat +       │  │
│  │Signup   │  │Switcher  │  │Panel (live)   │  │Trace View   │  │
│  └─────────┘  └──────────┘  └──────────────┘  └─────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API
┌──────────────────────────────▼──────────────────────────────────┐
│                     BACKEND (FastAPI + Python)                    │
│                                                                   │
│  ┌──────────────────────────────────────────────────────┐        │
│  │             LangGraph State Machine                    │        │
│  │                                                        │        │
│  │   ┌────────────┐                                      │        │
│  │   │ Supervisor │──┬──► Finance Agent (agt_finance)    │        │
│  │   │agt_super   │  ├──► Research Agent (agt_research)  │        │
│  │   │            │  ├──► Reporting Agent (agt_report)   │        │
│  │   │            │  ├──► Code Agent (agt_code)          │        │
│  │   │            │  └──► Creative Agent (agt_creative)  │        │
│  │   └────────────┘                                      │        │
│  └──────────────────────────────────────────────────────┘        │
│                               │                                   │
│  ┌────────────────────────────▼─────────────────────────────┐    │
│  │              MetricAI Integration Layer                    │    │
│  │  - Wrap every LLM call via metricai-sdk proxy             │    │
│  │  - X-MetricAI-Session, X-MetricAI-Agent headers           │    │
│  │  - Per-provider routing (OpenAI / Anthropic / Bedrock)    │    │
│  │  - Cost metering + token tracking per agent per user      │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌──────────────────────────┐  ┌─────────────────────────────┐  │
│  │ Auth (JSON file storage) │  │ Session/Trace Store (JSON)   │  │
│  │ - users.json             │  │ - sessions.json              │  │
│  │ - signup + login         │  │ - traces.json (exec details) │  │
│  └──────────────────────────┘  └─────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agents Registry

| Agent Name       | Agent ID        | Role                                      | Default Provider |
|-----------------|-----------------|-------------------------------------------|-----------------|
| Supervisor      | `agt_supervisor`| Routes queries to appropriate sub-agent   | OpenAI          |
| Finance Agent   | `agt_finance`   | Revenue, costs, budgets, margins          | OpenAI          |
| Research Agent  | `agt_research`  | Market research, data analysis, trends    | Anthropic       |
| Reporting Agent | `agt_report`    | Exec summaries, status reports            | OpenAI          |
| Code Agent      | `agt_code`      | Code generation, debugging, architecture  | Anthropic       |
| Creative Agent  | `agt_creative`  | Marketing copy, naming, brainstorming     | OpenAI          |

---

## Supported Providers (MetricAI-compatible)

| Provider   | Models                          | SDK / Integration                  |
|-----------|----------------------------------|-------------------------------------|
| OpenAI    | gpt-4o, gpt-4o-mini             | `langchain-openai` via MetricAI proxy |
| Anthropic | claude-sonnet-4-20250514, claude-3-haiku  | `langchain-anthropic` via MetricAI proxy |
| AWS Bedrock | anthropic.claude-v3, amazon.titan | `langchain-aws` via MetricAI proxy |

All LLM calls route through MetricAI's OpenAI-compatible proxy endpoint. Provider switching happens by changing the model string and base_url passed through the MetricAI wrapper.

---

## Implementation Tasks

### Phase 1: Backend — Auth & Data Layer

**1.1 Signup Endpoint**
- `POST /api/signup` — accepts `{name, email, password}`
- Generates `user_id` as `usr_<uuid[:8]>`
- Validates email uniqueness against `users.json`
- Appends user to `users.json`
- Returns user object + session_id

**1.2 Enhanced Login**
- Keep existing login logic
- On login, also return list of available providers

**1.3 Trace Storage**
- New file: `backend/memory/traces.json`
- Each trace entry:
```json
{
  "trace_id": "trc_abc123",
  "user_id": "usr_001",
  "session_id": "sess_xyz",
  "timestamp": "2026-06-15T10:30:00Z",
  "query": "What are Q4 margins?",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "supervisor_decision": "agt_finance",
  "agent_id": "agt_finance",
  "agent_name": "Finance Agent",
  "tokens_in": 245,
  "tokens_out": 180,
  "cost_inr": 0.42,
  "execution_time_ms": 1200,
  "response": "...",
  "metricai_logged": true
}
```
- `GET /api/traces?user_id=xxx` — returns execution history for the UI

---

### Phase 2: Backend — Multi-Provider LLM Layer

**2.1 Provider Registry**
- New file: `backend/providers.py`
- Defines provider configs:
```python
PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini"],
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "anthropic": {
        "name": "Anthropic",
        "models": ["claude-sonnet-4-20250514", "claude-3-haiku-20240307"],
        "default_model": "claude-3-haiku-20240307",
        "env_key": "ANTHROPIC_API_KEY",
    },
    "bedrock": {
        "name": "AWS Bedrock",
        "models": ["anthropic.claude-3-sonnet-20240229-v1:0", "amazon.titan-text-express-v1"],
        "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "env_key": "AWS_ACCESS_KEY_ID",
    },
}
```

**2.2 MetricAI Proxy Integration**
- Rewrite `metric_ai_wrapper.py` to use the **proxy pattern** from MetricAI docs:
```python
from metricai import wrap
from openai import OpenAI

base = OpenAI()
client = wrap(base, project_key="pk_live__")

# Every call includes attribution headers
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    extra_headers={
        "X-MetricAI-Session": session_id,
        "X-MetricAI-Agent": agent_id,
    },
)
```
- For Anthropic: use the OpenAI-compatible endpoint through MetricAI's proxy
- For Bedrock: route through MetricAI proxy with provider hints

**2.3 LLM Factory Function**
- `get_llm(provider, model, session_id, agent_id)` → returns a wrapped LangChain LLM
- All agents call this instead of directly instantiating `ChatOpenAI`

**2.4 Provider Switch Endpoint**
- `GET /api/providers` — returns available providers and models
- `POST /api/chat` now accepts optional `provider` and `model` fields

---

### Phase 3: Backend — Expanded Agents via LangGraph

**3.1 New Agents**

**Code Agent** (`backend/agents/code.py`):
- System prompt for code generation, debugging, architecture questions
- Agent ID: `agt_code`

**Creative Agent** (`backend/agents/creative.py`):
- System prompt for marketing copy, brainstorming, naming
- Agent ID: `agt_creative`

**3.2 Updated Supervisor**
- Add `code_agent` and `creative_agent` to routing rules
- Supervisor prompt updated with new routing categories

**3.3 Updated LangGraph**
- Add new nodes for `code_agent` and `creative_agent`
- Add conditional edges from supervisor
- Update `AgentState` to include `provider`, `model`, `trace_id`

**3.4 Detailed Execution Trace**
- Each agent node emits structured trace data:
  - Which agent was invoked
  - Which provider/model was used
  - Token counts (input/output)
  - Execution time
  - MetricAI tracking confirmation
- Trace is saved to `traces.json` and returned in the response

---

### Phase 4: Frontend — Auth (Login + Signup)

**4.1 Signup Page** (`frontend/signup.html`)
- Fields: Name, Email, Password, Confirm Password
- Calls `POST /api/signup`
- On success, stores user in sessionStorage, redirects to chat
- Link to login page

**4.2 Updated Login Page**
- Add "Don't have an account? Sign up" link
- Keep demo account chips

---

### Phase 5: Frontend — Provider Switcher

**5.1 Provider Dropdown in Chat UI**
- Top bar or sidebar section: "Provider" dropdown
- Options: OpenAI, Anthropic, Bedrock
- Sub-dropdown for model selection per provider
- Persists selection in sessionStorage
- Sends `provider` + `model` with every `/api/chat` request

**5.2 Provider Status Indicator**
- Shows current active provider + model
- Color-coded badges (green = OpenAI, purple = Anthropic, orange = Bedrock)

---

### Phase 6: Frontend — Execution Trace Panel

**6.1 Trace Detail View**
- After each response, show an expandable "Execution Details" section:
  - Supervisor routing decision
  - Agent invoked (name + ID)
  - Provider used + model
  - Tokens consumed (in/out)
  - Estimated cost (INR)
  - Execution time
  - MetricAI session/correlation IDs
  - User context (user_id, session_id)

**6.2 Real-time Agent Activity Panel**
- Sidebar section updates live:
  - Current agent (name + ID + status indicator)
  - Provider being used
  - "Thinking..." / "Routing..." / "Responding..." states

**6.3 History Panel**
- Button to view past traces for current session
- Shows all queries with agent, provider, cost, time

---

### Phase 7: Frontend — Styling & UX

- Keep existing dark theme (it's good)
- Add provider badge colors
- Add trace accordion animation
- Add signup form styling consistent with login
- Mobile-responsive adjustments
- Add cost counter in sidebar (running total for session)

---

## File Structure (Final)

```
demo_agent/
├── .env
├── plan.md
└── metric-demo/
    ├── .env
    ├── requirements.txt
    ├── backend/
    │   ├── main.py              (FastAPI app + signup endpoint)
    │   ├── graph.py             (LangGraph with 5 agents)
    │   ├── state.py             (AgentState with provider/trace fields)
    │   ├── providers.py         (Provider registry + factory)
    │   ├── metric_ai_wrapper.py (MetricAI proxy integration)
    │   ├── agents/
    │   │   ├── __init__.py
    │   │   ├── supervisor.py    (Updated routing for 5 agents)
    │   │   ├── finance.py       (Uses provider factory)
    │   │   ├── research.py      (Uses provider factory)
    │   │   ├── reporting.py     (Uses provider factory)
    │   │   ├── code.py          (NEW)
    │   │   └── creative.py      (NEW)
    │   └── memory/
    │       ├── users.json       (Signup data persisted here)
    │       ├── sessions.json
    │       └── traces.json      (NEW — execution traces)
    └── frontend/
        ├── login.html           (Updated with signup link)
        ├── signup.html          (NEW)
        ├── chat.html            (Updated with provider switcher + trace panel)
        ├── css/
        │   └── style.css        (Updated with new components)
        └── js/
            ├── login.js         (Existing)
            ├── signup.js        (NEW)
            └── chat.js          (Updated — provider switch, traces)
```

---

## Environment Variables Required

```env
# LLM Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=us-east-1

# MetricAI
METRIC_AI_API_KEY=metricai_7dZbYpVMNVE0GlTsOqvjDqqnrjN4g3UIN2ADDsyp32w
METRIC_AI_PROJECT_ID=proj_...
```

---

## Dependencies (requirements.txt)

```
fastapi
uvicorn[standard]
python-dotenv
langgraph
langchain-core
langchain-openai
langchain-anthropic
langchain-aws
pydantic
metricai-sdk
```

---

## MetricAI Integration Points

Every LLM call in the system flows through MetricAI:

1. **Supervisor routing call** → tracked as `agt_supervisor`
2. **Each sub-agent call** → tracked with respective `agt_*` ID
3. **Headers on every request**:
   - `X-MetricAI-Session`: current session ID
   - `X-MetricAI-Agent`: agent making the call
4. **Outcome recording** (optional): after each successful response, record outcome for billing
5. **Provider cost reconciliation**: MetricAI meters regardless of which provider is used

---

## API Endpoints (Final)

| Method | Path             | Description                              |
|--------|-----------------|------------------------------------------|
| POST   | /api/signup      | Create new user account                  |
| POST   | /api/login       | Authenticate existing user               |
| POST   | /api/chat        | Send query (with provider/model choice)  |
| GET    | /api/providers   | List available providers and models      |
| GET    | /api/traces      | Get execution traces for a session       |

---

## Execution Flow (Per User Query)

```
1. User sends message + selected provider/model
2. Backend creates trace_id
3. Supervisor agent routes query (LLM call #1 → MetricAI tracked)
4. Selected sub-agent executes (LLM call #2 → MetricAI tracked)
5. Trace saved to traces.json with full details
6. Response returned with:
   - Agent response text
   - Agent name + ID
   - Provider + model used
   - Token counts
   - Execution time
   - Trace ID
7. Frontend renders response + shows execution details panel
8. Sidebar updates with active agent info
```

---

## Order of Implementation

1. Backend: providers.py + LLM factory
2. Backend: Rewrite metric_ai_wrapper.py with proxy pattern
3. Backend: Add code + creative agents
4. Backend: Update supervisor routing
5. Backend: Update LangGraph with new nodes + trace emission
6. Backend: Add signup endpoint + traces endpoint
7. Frontend: signup.html + signup.js
8. Frontend: Provider switcher UI in chat
9. Frontend: Execution trace panel
10. Frontend: Polish + responsive

---

## Success Criteria

- [ ] User can sign up with name/email/password (saved to JSON)
- [ ] User can log in with existing credentials
- [ ] 5 sub-agents + 1 supervisor, each with unique IDs
- [ ] Provider can be switched live from frontend (OpenAI/Anthropic/Bedrock)
- [ ] Every LLM call is metered through MetricAI proxy
- [ ] Execution details visible per query (agent, provider, model, tokens, cost, time)
- [ ] All data stored locally in JSON (no database)
- [ ] Frontend shows which agent handled the query and for which user
