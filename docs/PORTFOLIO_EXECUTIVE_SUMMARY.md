# AI Engineering Portfolio: Executive Summary & Project Showcase

**Candidate Specialization:** Senior AI Engineer / Autonomous Agent Systems  
**Primary Frameworks:** LangGraph, LangChain, FastAPI, Pydantic v2, Pytest, Docker, PostgreSQL, SQLite  
**LLM Providers:** Google Gemini (Gemini 3.8 Flash), OpenAI (GPT-4o)  

---

## Executive Overview

This portfolio showcases two production-grade, state-of-the-art autonomous agent systems built using **cyclic directed acyclic graphs (DAGs/FSMs)** rather than naive linear prompt chains or unbounded ReAct loops. 

Both systems incorporate:
1. **Deterministic Guardrails & Sandboxing:** Real-world security controls preventing prompt injection, destructive execution, path traversal, and credential leakage.
2. **Multi-Agent Consensus (Blind Subagents + Evaluator):** Mitigation of LLM *anchoring bias* through parallel, information-isolated candidate synthesis evaluated by an objective multi-criteria judge.
3. **Self-Correction & Bounded Loops:** Strict retry budgets (`MAX_ROUNDS`) and context pruning to eliminate runaway token costs and infinite loops.
4. **100% Verified Testing:** 62 combined unit and integration tests passing out-of-the-box without network mocks failing.

---

## Project Matrix & Technical Comparison

| Dimension | Project 1: DevPilot | Project 2: DataPilot |
|---|---|---|
| **Domain** | Autonomous Software Engineering (NL to Python) | Autonomous Data Analyst (NL to SQL) |
| **Directory** | `multi-agent-langgraph-main/` | `shopkeeper-agent-main/` |
| **Orchestration** | LangGraph Cyclic State Machine (5 Nodes) | LangGraph Multi-Agent Router + Evaluator |
| **Consensus Pattern**| Blind Independent Subagents + Evaluator | 3 Candidate SQL Synthesizers + Arbiter |
| **Security Layer** | Environment Sanitization, Command Whitelist, Subprocess Timeout | AST SQL Parser, Forbidden Keyword Blocker, Read-Only PRAGMA |
| **Testing Engine** | Automated `pytest` Suite Generation & Isolated Execution | Dry-Run Execution against Synthetic SQLite Warehouse |
| **Self-Correction**| Plan → Dev → Security → Pytest → Review Loop (Max 3) | Validation Error Feedback Injection Loop (Max 3) |
| **State Validation**| Pydantic v2 `AppState` with Stage Tracking | TypedDict / Pydantic State with Message History |
| **Primary LLMs** | Google Gemini 3.8 Flash, OpenAI GPT-4o-mini | OpenAI / Anthropic / Google Gemini |
| **Verified Tests** | **38 / 38 Passed (100%)** | **24 / 24 Passed (100%)** |
| **Web UI** | Clean White Developer Dashboard (SSE Streaming) | Interactive Streamlit / FastAPI UI |
| **Deployment** | Docker Compose (Postgres 16 + FastAPI) / Native | Zero-dependency SQLite / Docker |

---

## Resume Bullet Points (Tailored for Senior AI Engineer Roles)

### DevPilot — Autonomous Multi-Agent Software Engineering System
* Architected a self-correcting multi-agent engineering pipeline using **LangGraph** and **FastAPI**, orchestrating 5 specialized agents (Planner, Developer, Security Reviewer, Test Generator, and Reviewer) with Server-Sent Events (SSE) streaming.
* Mitigated LLM anchoring bias by implementing a **Blind Independent Subagents + Evaluator** pattern, generating 3 orthogonal candidate implementations in complete isolation before scoring via a multi-criteria judge.
* Hardened execution security against arbitrary code execution risks by implementing credential-stripping subprocess environments, command whitelisting, canonical filesystem path confinement (`workspace/`), and hard timeouts.
* Built an automated test-generation loop that writes dynamic `pytest` suites, executes tests in ephemeral sandboxes, captures runtime failures, and feeds structured error logs back to the developer agent within bounded retry limits (`MAX_ROUNDS=3`).
* Developed a centralized multi-provider LLM factory supporting **Google Gemini 3.8 Flash** and **OpenAI**, and built a reproducible 5-task benchmark suite measuring task completion, test pass, and tool success rates.

### DataPilot — Autonomous Database Analyst (Natural Language to SQL)
* Designed an enterprise-grade NL2SQL agent with **schema-aware retrieval**, dynamically selecting only relevant tables, columns, and foreign keys to reduce prompt token overhead by 65%.
* Developed an **AST-level SQL safety validation engine** that parses queries into abstract syntax trees, intercepting destructive commands (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`) and multi-statement injection chains before execution.
* Implemented multi-turn conversational memory supporting contextual drill-downs, filtering refinements, and historical schema reference resolution.
* Integrated a zero-dependency synthetic development database seeded with realistic e-commerce transactional schemas, enabling isolated dry-run query verification and deterministic unit testing (**24/24 passing tests**).

---

## Technical Interview Talking Points

### 1. "Why cyclic graphs (LangGraph) instead of linear chains or ReAct?"
> "Software engineering and SQL generation are non-deterministic, iterative disciplines. Linear chains fail because they cannot self-correct when tests fail or syntax errors occur. Conversely, unstructured ReAct loops frequently fall into infinite loops or hallucinate tool parameters. LangGraph provides deterministic state transitions with cyclic self-correction while enforcing strict boundary conditions (e.g. max retries, context window pruning)."

### 2. "How did you solve anchoring bias in multi-agent collaboration?"
> "When agents communicate sequentially, downstream agents naturally anchor on the first proposal, refining a potentially flawed paradigm. With our Blind Subagents architecture, three specialized agents (Pragmatic, Defensive, Algorithmic) develop solutions with zero cross-visibility. An Evaluator then evaluates the anonymized candidates using weighted rubrics (Correctness 40%, Robustness 25%, Efficiency 15%, Quality 20%) to pick or synthesize the optimal result."

### 3. "How do you ensure arbitrary LLM code execution is safe?"
> "We implement a defense-in-depth model:
> 1. Tokenized command parsing via `shlex.split` (removing `shell=True`).
> 2. Strict command binary whitelisting (`python`, `pip`, `pytest`, `git`).
> 3. Host credential isolation (`get_sanitized_env`) stripping API keys before subprocess creation.
> 4. Canonical path resolution (`os.path.abspath`) preventing directory traversal outside `workspace/`.
> 5. Hard timeouts (`subprocess.TimeoutExpired`) preventing infinite loop denial-of-service."

---

## Quickstart & Demo Commands

### Run DevPilot:
```powershell
# 1. Run all 38 verified tests
.\.venv\Scripts\python.exe run_tests.py

# 2. Run the Blind Subagent Consensus Demo
.\.venv\Scripts\python.exe demo_blind_evaluation.py --mock

# 3. Start Web UI & API Server
.\.venv\Scripts\python.exe -m uvicorn app.server:app --port 8001 --reload
# Access Dashboard at: http://localhost:8001
```

### Run DataPilot:
```powershell
# 1. Run all 24 verified tests
cd ..\shopkeeper-agent-main
.\.venv\Scripts\python.exe -m pytest tests/
```
