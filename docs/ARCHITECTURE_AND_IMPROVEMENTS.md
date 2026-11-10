# DevPilot: Architecture & Production Improvements

**Project:** DevPilot — Multi-Agent AI Software Engineering System  
**System:** `DevPilot (Multi-Agent AI Software Engineering Platform)`  
**Author:** Senior AI Systems & Software Engineer  
**Date:** 2026-11-10  

---

## 1. System Overview & Architecture Evolution

DevPilot is an agentic software engineering platform built on **LangGraph**, **LangChain**, and **FastAPI**. It transforms user programming requests into robust, secure, tested, and validated Python software solutions.

### Before: Sequential 3-Agent Loop
```text
Planner ──(plan)──► Developer ──(code)──► Reviewer ──(feedback loop)──► END
```
*Limitations:* Single-developer bottleneck, anchoring bias, zero automated test verification, arbitrary command execution with `shell=True`, and environment credential exposure.

### After: Multi-Agent Production Architecture
```text
                   ┌───────────────────────────────────────┐
                   │             User Request              │
                   └──────────────────┬────────────────────┘
                                      │
                                      ▼
                   ┌───────────────────────────────────────┐
                   │             Planner Agent             │
                   │    (Ambiguity Check & Step Decomp)    │
                   └─────────┬───────────────────┬─────────┘
        needs_clarification  │                   │ plan_ready
                             ▼                   ▼
                     [Ask User / END]   ┌────────────────────────────────┐
                                        │        Developer Agent         │
                                        │    (or Blind Subagents A/B/C)  │
                                        └───────────────┬────────────────┘
                                                        │
                                                        ▼
                                        ┌────────────────────────────────┐
                                        │    Security Reviewer Agent     │
                                        │  (Heuristic Injection/Secrets) │
                                        └───────┬───────────────┬────────┘
                                      is_secure │               │ high risk
                                                ▼               └──────┐ (retry)
                                        ┌────────────────┐             │
                                        │ Test Generator │             │
                                        │ (Pytest Runner)│             │
                                        └───────┬────────┘             │
                                  tests_passed  │                      │
                                                ▼                      │
                                        ┌────────────────┐             │
                                        │ Reviewer Agent │             │
                                        │  (or Evaluator)│             │
                                        └───────┬────────┘             │
                                                │                      ▼
                             ┌──────────────────┴──────────────────────┴─┐
                             │    Conditional Routing Engine             │
                             │  - If Approved & Tests Pass ──► COMPLETED │
                             │  - If Flaws Found (Rounds < 3) ──► RETRY  │
                             │  - If Max Rounds Exceeded ──► SAFE FAIL   │
                             └───────────────────────────────────────────┘
```

---

## 2. Feature Breakdown & Implementation Details

### Feature A: Structured Agent State (`AppState`)
The central state is validated using **Pydantic v2** (`app/graph/state.py`). It replaces weakly typed dictionaries with a strictly validated, immutable data model tracking:
- `task`: Original user prompt.
- `discussion`: List of `Message(agent, content)` tracking execution traces.
- `plan`: Step-by-step implementation instructions.
- `code`: Active Python or shell solution.
- `files_modified`: List of file paths generated/updated within the workspace.
- `tool_used` / `filename`: Execution tool selected (`run_python_code`, `write_file`, `run_shell_command`).
- `execution_result`: Runtime stdout/stderr or file write confirmations.
- `test_code` / `test_results` / `tests_passed`: Automated unit test artifacts and execution outcomes.
- `security_review`: Structured findings (`SecurityReviewOut`, `SecurityFinding`).
- `candidates`: List of `CandidateSolution` models from blind subagents.
- `evaluation`: Multi-criteria evaluation scorecard (`EvaluatorOut`, `CandidateScore`).
- `current_stage` / `round` / `max_rounds` / `final_status`: Complete lifecycle and safety termination state.

### Feature B: Improved Conditional Routing & Safety Limits
LangGraph conditional edges (`app/graph/workflow.py`) orchestrate state transitions:
1. `after_planner`: Routes to `end` if clarification is required; otherwise advances to `developer`.
2. `after_security_review`: If critical/high security risks are found and `round < max_rounds`, loops back to `developer` with specific remediation feedback. If max rounds are reached, terminates with `final_status="failed"`.
3. `after_test_generator`: If tests fail and iterations remain, routes back to `developer` with tracebacks.
4. `after_reviewer`: Approves clean solutions (`final_status="completed"`), requests user clarification, or manages the retry budget.

### Feature C: Dedicated Security Reviewer Agent
The `security_reviewer_agent` (`app/agents/security_reviewer.py`) audits code before runtime execution:
- Checks for hardcoded secrets, API tokens, passwords, and private keys.
- Flags command injection (`shell=True`, unsanitized string formatting in `subprocess` or `os.system`).
- Identifies insecure deserialization (`pickle.loads`, `eval`, `exec`).
- Detects path traversal attempts (`../`) and unauthorized filesystem access.
- Employs structured output: `severity` ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"), `line_or_location`, `explanation`, and `suggested_remediation`.
- Explicit Disclaimer: *LLM-based security review provides heuristic vulnerability detection and does not replace sandbox boundary enforcement or containerized isolation.*

### Feature D: Automated Test Generation & Sandboxed Runner
The `test_generator_agent` (`app/agents/test_generator.py`):
1. Analyzes the task and implementation to generate a complete `pytest` unit test file.
2. Generates tests covering happy paths, edge cases (empty strings/lists, negative integers, None), and error handling (`pytest.raises`).
3. Executes the test suite in an isolated temporary directory via subprocess.
4. Captures output and feeds failing test assertions directly back to the Developer agent for targeted self-correction.

### Feature E: Secure Code Execution Hardening
Critical vulnerabilities in the baseline project were remediated across `app/tools/`:
1. **`code_executor.py`:**
   - **Environment Sanitization:** Implemented `get_sanitized_env()` to strip `OPENAI_API_KEY`, `DATABASE_URL`, `API_KEY`, and all tokens/passwords from child processes, preventing credential exfiltration.
   - **Guaranteed Cleanup:** Employs `tempfile.TemporaryDirectory()` in a context manager so no orphaned `.py` files remain on disk.
   - **Execution Timeout:** Enforces `timeout=10` seconds, catching `subprocess.TimeoutExpired` to prevent infinite loop DoS.
2. **`shell_executor.py`:**
   - **Removed `shell=True`:** Replaced shell parsing with `shlex.split()`.
   - **Command Whitelisting:** Enforces `ALLOWED_COMMANDS = {"python", "pip", "pytest", "git", "echo", "cat", "dir", "ls", "mkdir", "type"}`.
   - **Pattern Blacklisting:** Intercepts dangerous patterns (`rm -rf`, `del /`, `format`, `curl`, `wget`, `nc`, `shutdown`).
   - **Policy Toggle:** Execution can be globally disabled via `ALLOW_SHELL_EXECUTION=false`.
3. **`file_system.py`:**
   - **Path Confinement:** Confines all writes to `workspace/` using `os.path.abspath` and boundary checking, completely neutralizing path traversal (`../../`).
   - **Protected Files:** Blocks writing to `.env`, `Dockerfile`, `docker-compose.yml`, `.gitignore`, and executable scripts.

### Feature F: Reproducible Evaluation Benchmark
The `evals/` framework (`evals/dataset.json`, `evals/evaluator.py`, `evals/run_evals.py`) provides automated benchmarking:
- Tracks: Task Completion Rate, Review Approval Rate, Test Pass Rate, Tool Execution Success, and Average Retries.
- Produces `evals/results.json` for reproducible portfolio demonstration.

### Feature G: Centralized LLM Provider Configuration
The centralized factory (`app/core/llm.py`):
- Centralizes model instantiation for OpenAI (`ChatOpenAI`) and Google Gemini (`ChatGoogleGenerativeAI`).
- Replaces brittle module-level imports with lazy, credential-checked factory access.
- Validates missing API keys cleanly with actionable error messages without crashing test runners or offline scripts.

---

## 3. Blind Independent Subagents + Evaluator Pattern

In addition to the sequential loop, DevPilot introduces the **Blind Independent Subagents + Evaluator** paradigm (`app/agents/blind_subagents.py`, `app/agents/evaluator.py`, `demo_blind_evaluation.py`):
1. **Information Isolation ("Blindness"):** Three distinct subagents (Pragmatic Pythonist, Defensive Systems Engineer, Algorithmic Specialist) independently generate solutions without access to each other's code or messages, preventing herd mentality and anchoring bias.
2. **Independent Sandbox Execution:** Each subagent executes its chosen tool in isolation and collects runtime evidence.
3. **Objective Evaluator (Judge):** The Evaluator agent receives anonymized solutions (Candidate A, B, C) and scores them across four weighted dimensions:
   - Correctness & Execution (40%)
   - Robustness & Edge Cases (25%)
   - Algorithmic Efficiency (15%)
   - Code Quality & Standards (20%)
4. **Optimal Synthesis:** Declares a winning candidate with transparent rationale and synthesizes improvements into the final delivered solution.

