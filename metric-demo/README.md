# MetricAI Multi-Agent Demo

A full-featured multi-agent system powered by **LangGraph** with **MetricAI** observability, supporting multiple LLM providers with real-time execution tracing.

---

## What It Does

This demo showcases an intelligent query routing system where a **Supervisor Agent** analyzes your question and delegates it to the most appropriate specialist agent — all while tracking costs, tokens, and performance through MetricAI.

---

## Agents

### Supervisor (`agt_supervisor`)
Routes every incoming query to the best-fit specialist based on intent analysis.

### Finance Agent (`agt_finance`)
- Revenue and cost analysis
- Profitability breakdowns
- Financial forecasting
- Budget planning and margin calculations

### Research Agent (`agt_research`)
- Market research and competitor analysis
- Data-driven investigation
- Trend identification
- Deep-dive studies

### Reporting Agent (`agt_reporting`)
- Executive summaries
- Status reports and dashboards
- Strategic recommendations
- Action item generation

### Code Agent (`agt_code`)
- Code generation and debugging
- Architecture guidance
- Algorithm explanations
- Technical design patterns

### Creative Agent (`agt_creative`)
- Marketing copy and taglines
- Product naming and branding
- Brainstorming and ideation
- Content strategy

---

## Features

### Multi-Provider Support
Switch between LLM providers on the fly from the UI:

| Provider | Models |
|----------|--------|
| OpenAI | gpt-4o, gpt-4o-mini |
| Anthropic | claude-sonnet-4-20250514, claude-3-haiku |
| AWS Bedrock | claude-3-sonnet, amazon titan |

### Execution Tracing
Every query shows full execution details:
- Which agent handled it
- Provider and model used
- Input/output token counts
- Cost in INR
- Execution time in milliseconds
- MetricAI tracking confirmation

### Authentication
- Sign up with name, email, and password
- Login with existing credentials
- Demo accounts for quick access

### Session Tracking
- Per-session cost accumulator
- Trace history panel with past queries
- User and session IDs visible in sidebar

---

## How It Works

```
User sends message
       │
       ▼
Supervisor Agent analyzes intent
       │
       ▼
Routes to specialist agent
       │
       ▼
Specialist generates response (tracked by MetricAI)
       │
       ▼
Response + execution trace returned to UI
```

---

## Running

```bash
cd "c:\Users\kumar\OneDrive\Desktop\demo_agent\metric-demo\backend"; python -m uvicorn main:app --host 127.0.0.1 --port 8000 2>&1
```

Open `http://localhost:8000` in your browser.

---

## Tech Stack

- **Backend:** FastAPI + LangGraph + LangChain
- **Frontend:** Vanilla HTML/CSS/JS (dark theme)
- **Observability:** MetricAI SDK
- **Storage:** JSON files (no database required)
- **Providers:** OpenAI, Anthropic, AWS Bedrock
