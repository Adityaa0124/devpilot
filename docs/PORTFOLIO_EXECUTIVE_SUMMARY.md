# AI Engineering Portfolio: Executive Summary & Project Showcase

**Candidate Specialization:** Senior AI Engineer / Autonomous Agent Systems  
**Primary Frameworks:** LangGraph, LangChain, FastAPI, Pydantic v2, Pytest, Docker, PostgreSQL, SQLite  
**LLM Providers:** Google Gemini (Gemini 2.5/3.8 Flash), OpenAI (GPT-4o), SiliconFlow (GLM-5.1)  

---

## Executive Overview

This portfolio showcases two production-grade, state-of-the-art autonomous agent systems built using **cyclic directed graphs and multi-agent consensus** rather than naive prompt chains or unbounded ReAct loops.

Both systems incorporate:
1. **Deterministic Guardrails & Sandboxing:** Real-world security controls preventing prompt injection, destructive execution, path traversal, and credential leakage.
2. **Multi-Agent Consensus (Blind Subagents + Evaluator):** Mitigation of LLM *anchoring bias* through parallel, information-isolated candidate synthesis evaluated by an objective multi-criteria judge.
3. **Self-Correction & Bounded Loops:** Strict retry budgets (`MAX_ROUNDS = 3`, `MAX_RETRIES = 3`) and context pruning to eliminate runaway token costs and infinite loops.
4. **100% Verified Testing:** 63 combined unit, integration, and security tests passing with zero failures.
5. **Production Deployment Packaging:** Complete multi-stage Dockerfiles, Docker Compose files, container healthchecks, and single-port React SPA serving.

---

## Project Matrix & Technical Comparison

| Dimension | Project 1: DevPilot | Project 2: DataPilot |
| :--- | :--- | :--- |
| **Domain** | Autonomous Software Engineering (NL to Python) | Autonomous Database Analyst (NL to SQL) |
| **Directory** | `multi-agent-langgraph-main/` | `shopkeeper-agent-main/` |
| **Orchestration** | LangGraph Cyclic State Machine (5 Nodes) | LangGraph Multi-Agent Router + Lead Evaluator |
| **Consensus Pattern** | Blind Independent Subagents + Evaluator | 3 Blind Candidate Synthesizers + Arbiter |
| **Security Layer** | Environment Sanitization, Command Whitelist, Subprocess Timeout | AST SQL Parser, Forbidden Keyword Blocker, Table Whitelist, Row Clamping |
| **Testing Engine** | Automated `pytest` Suite Generation & Isolated Execution | Dry-Run Execution against Synthetic SQLite Warehouse |
| **Self-Correction** | Plan → Dev → Security → Pytest → Review Loop (Max 3) | Validation Error Feedback Injection Loop (Max 3) |
| **State Validation** | Pydantic v2 `AppState` with Stage Tracking | Pydantic v2 Models + Typed Multi-Turn Context |
| **Primary LLMs** | Google Gemini 3.8 Flash, OpenAI GPT-4o-mini | SiliconFlow GLM-5.1, OpenAI GPT-4o, Google Gemini |
| **Verified Tests** | **38 / 38 Passed (100%)** | **25 / 25 Passed (100%)** |
| **Benchmark Accuracy** | 5/5 Tasks Completed | **14 / 14 Scenarios Passed (100.0%, 1.21ms latency)** |
| **Web UI** | Clean Developer Dashboard (SSE Streaming) | React 19 + Tailwind CSS + Interactive LangGraph Flow Graph |
| **Deployment** | Docker Compose (Postgres 16 + FastAPI) / Native | Multi-Stage Dockerfile (Node 22 + Python 3.11) / Single-Port SPA |
| **Live Demo URL** | [devpilot-tdjx.onrender.com](https://devpilot-tdjx.onrender.com/) | Local Container / Single-Port Server |

---

## Resume Bullet Points (Tailored for Senior AI Engineer Roles)

### DevPilot — Autonomous Multi-Agent Software Engineering System
* Architected a self-correcting multi-agent engineering pipeline using **LangGraph** and **FastAPI**, orchestrating 5 specialized agents (Planner, Developer, Security Reviewer, Test Generator, and Reviewer) with Server-Sent Events (SSE) streaming.
* Mitigated LLM anchoring bias by implementing a **Blind Independent Subagents + Evaluator** pattern, generating 3 orthogonal candidate implementations in complete isolation before scoring via a multi-criteria judge.
* Hardened execution security against arbitrary code execution risks by implementing credential-stripping subprocess environments, command whitelisting, canonical filesystem path confinement (`workspace/`), and hard timeouts.
* Built an automated test-generation loop that writes dynamic `pytest` suites, executes tests in ephemeral sandboxes, captures runtime failures, and feeds structured error logs back to the developer agent within bounded retry limits (`MAX_ROUNDS=3`).
* Developed a centralized multi-provider LLM factory supporting **Google Gemini 3.8 Flash** and **OpenAI**, and built a reproducible benchmark suite measuring task completion, test pass, and tool success rates (**38/38 verified tests passing**).

### DataPilot — Autonomous Database Analyst (Natural Language to SQL)
* Designed an enterprise-grade NL2SQL agent with **schema-aware retrieval**, dynamically selecting only relevant tables, columns, foreign keys, and metrics to reduce prompt token overhead and prevent hallucinated joins.
* Built an ensemble of **Blind Independent Subagents** (`Pragmatic`, `Defensive`, `Analytical`) producing candidate SQL queries in information isolation, evaluated by a centralized **Lead Evaluator** performing dry-run scoring (0–100) on disposable dev databases.
* Engineered an **AST SQL Safety Firewall** that parses queries into abstract syntax tree tokens prior to execution, deterministically rejecting destructive operations (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`), multi-statement injection chains (`;`), and unapproved tables while clamping row limits.
* Implemented a **Bounded Query Correction Loop** (`MAX_RETRIES = 3`) that captures database errors, provides surgical diagnostic feedback, and re-validates corrected queries through the safety firewall.
* Developed **Multi-Turn Conversational Memory** supporting contextual drill-downs, filtering refinements, and historical schema reference resolution without cross-contaminating prior sessions.
* Containerized the system into a **production multi-stage Docker build** serving both the compiled React 19 SPA and FastAPI backend on a single port with integrated Docker healthcheck probes (**25/25 verified tests passing**).

---

## Technical Interview Talking Points

### 1. "Why cyclic graphs (LangGraph) instead of linear chains or ReAct?"
> "Software engineering and SQL generation are non-deterministic, iterative disciplines. Linear chains fail because they cannot self-correct when tests fail or syntax errors occur. Conversely, unstructured ReAct loops frequently fall into infinite loops or hallucinate tool parameters. LangGraph provides deterministic state transitions with cyclic self-correction while enforcing strict boundary conditions (e.g. max retries, context window pruning)."

### 2. "How did you solve anchoring bias in multi-agent collaboration?"
> "When agents communicate sequentially, downstream agents naturally anchor on the first proposal, refining a potentially flawed paradigm. With our Blind Subagents architecture, three specialized agents (Pragmatic, Defensive, Algorithmic) develop solutions with zero cross-visibility. An Evaluator then evaluates the anonymized candidates using weighted rubrics against an ephemeral development database to pick or synthesize the optimal result."

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
# 1. Run all 25 verified tests
cd ..\shopkeeper-agent-main
$env:PYTHONPATH="."; .\.venv\Scripts\python.exe -m pytest tests/ -v

# 2. Run benchmark evaluation
$env:PYTHONPATH="."; .\.venv\Scripts\python.exe -c "from app.evaluation.benchmark_evaluator import BenchmarkEvaluator; print(BenchmarkEvaluator().run_benchmark())"

# 3. Start Unified Server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
