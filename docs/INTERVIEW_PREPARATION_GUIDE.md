# DevPilot: AI Engineering Interview Preparation Guide

This guide prepares you to speak authoritatively about **DevPilot**, its multi-agent architecture, security mitigations, and design trade-offs during technical AI Engineering interviews.

---

## Question 1: Why did you use LangGraph instead of linear chains or autonomous ReAct loops?

### **Strong Technical Answer:**
> "Linear orchestration (like basic LangChain LCEL or sequential chains) works well for predictable single-shot prompts, but software engineering is an iterative, state-dependent process requiring self-correction, branching, and review.
>
> On the other hand, purely autonomous ReAct loops (where an agent is given dozens of tools and loops freely) are notoriously non-deterministic, prone to catastrophic hallucination loops, and hard to inspect or debug in production.
>
> We chose **LangGraph** because it models the workflow as a **cyclic finite state machine (FSM)**. It gives us the best of both worlds:
> 1. **Structured control flow:** We enforce distinct stages (Planning → Development → Security Audit → Test Execution → Final Review).
> 2. **Cyclic feedback loops:** If tests fail or the security auditor flags a vulnerability, the state loops back specifically to the developer with targeted context.
> 3. **Observability and state persistence:** Shared state (`AppState`) is strictly validated via Pydantic at every transition and easily streamed to clients using Server-Sent Events (SSE) or saved in PostgreSQL."

---

## Question 2: How do you prevent infinite loops and runaway token costs in multi-agent review cycles?

### **Strong Technical Answer:**
> "We implement a multi-layered guardrail strategy:
> 1. **Strict Retry Budgets (`MAX_ROUNDS`):** The shared state tracks `round: int` and `max_rounds: int = 3`. Every conditional routing edge (`after_security_review`, `after_test_generator`, `after_reviewer`) explicitly checks `state.round < state.max_rounds`. If the budget is exhausted, the graph transitions to `END` with `final_status="failed"` rather than looping forever.
> 2. **Context Pruning (`MAX_CONTEXT_MESSAGES`):** In iterative discussions, LLM context windows can explode. We enforce sliding-window message slicing (`discussion[-MAX_CONTEXT_MESSAGES:]`), ensuring prompt tokens remain bounded.
> 3. **Non-Trivial Rejection Criteria:** We instruct reviewer and security agents to approve code that meets core functionality, preventing subjective stylistic debates between LLMs from triggering unnecessary cycles."

---

## Question 3: How do you secure arbitrary code execution in an autonomous AI agent?

### **Strong Technical Answer:**
> "Running LLM-generated code on a host machine is one of the highest security risks in agentic AI. In our initial audit, we identified that the baseline implementation used `shell=True`, had no execution timeouts, and passed host environment variables directly to subprocesses.
>
> We implemented a defense-in-depth architecture:
> 1. **Environment Credential Isolation:** We implemented `get_sanitized_env()` to strip all sensitive environment variables (`OPENAI_API_KEY`, `DATABASE_URL`, API tokens, cloud keys) before spawning child processes.
> 2. **Temporary Directory Lifecycle:** Code runs inside isolated `tempfile.TemporaryDirectory()` instances managed by Python context managers, guaranteeing complete file cleanup even on unexpected termination.
> 3. **Strict Subprocess Timeouts:** We enforce a 10-second hard timeout (`subprocess.TimeoutExpired`) to prevent infinite loop DoS attacks.
> 4. **Command Whitelisting & Path Confinement:** In `shell_executor.py`, we removed `shell=True`, parse tokens safely via `shlex.split`, and restrict binaries to an explicit whitelist (`python`, `pip`, `pytest`, `git`, `ls`). In `file_system.py`, we canonicalize paths (`os.path.abspath`) to strictly block directory traversal (`../../`).
> 
> *Key Interview Nuance:* We emphasize that host-level subprocess isolation is only heuristic. In a true enterprise production environment, arbitrary untrusted code execution must run inside ephemeral, non-root micro-VMs or dedicated gVisor/Docker sandboxes with network namespace isolation."

---

## Question 4: What is the "Blind Independent Subagents + Evaluator" pattern, and why does it outperform single-agent generation?

### **Strong Technical Answer:**
> "In single-agent or sequential multi-agent architectures, agents suffer from **anchoring bias**: once an initial solution or approach is proposed, subsequent critique or revision tends to cling to the original structure, even if the algorithm is fundamentally suboptimal.
>
> In the **Blind Independent Subagents + Evaluator** pattern:
> 1. **Information Isolation ('Blindness'):** We deploy multiple worker subagents (e.g. Pragmatic Developer, Defensive Systems Engineer, Algorithmic Specialist). Each generates an independent solution in total isolation without seeing other agents' plans, code, or thoughts.
> 2. **Execution Grounding:** Each blind candidate executes their code independently in the sandbox to produce verifiable stdout/stderr.
> 3. **Objective Evaluation & Scoring:** An Evaluator agent receives the candidates anonymized (Candidate A, B, C) and scores them across four weighted rubrics: Correctness (40%), Robustness (25%), Algorithmic Efficiency (15%), and Code Quality (20%).
> 4. **Synthesis:** The evaluator selects the winning solution or synthesizes the best edge-case handling of one with the computational speed of another."

---

## Question 5: How does your system support multiple LLM providers (e.g., OpenAI vs. Google Gemini)?

### **Strong Technical Answer:**
> "We centralized model instantiation into a dedicated factory (`app/core/llm.py`).
> - Instead of instantiating models at module import time (which crashed test runners when environment keys were absent), model creation is deferred and parameterized.
> - The factory reads `LLM_PROVIDER` (defaulting to `openai`), and dynamically initializes `ChatOpenAI` or `ChatGoogleGenerativeAI` (`gemini-1.5-flash`).
> - It validates credentials upfront, returning clean, actionable errors if an API key is missing.
> - For unit tests and offline benchmarking, it supplies mock credentials that allow full test execution and schema validation without external network calls."

---

## Question 6: What metrics do you track in your evaluation benchmark?

### **Strong Technical Answer:**
> "We built a benchmark harness in `evals/evaluator.py` running against a curated dataset (`evals/dataset.json`). We measure five core dimensions:
> 1. **Task Completion Rate:** Percentage of tasks that successfully reach a terminal completion state.
> 2. **Review Approval Rate:** Percentage of code solutions approved by the reviewer.
> 3. **Test Pass Rate:** Percentage of generated pytest test suites that pass on the first or subsequent attempts.
> 4. **Tool Execution Success Rate:** Percentage of tool executions that run without runtime exceptions or syntax errors.
> 5. **Average Retries:** The mean number of revision cycles required before acceptance.
>
> In our verified test suite of 38 unit and integration tests across 10 modules, we achieved a **100% test pass rate** with sub-second execution overhead per unit test."

