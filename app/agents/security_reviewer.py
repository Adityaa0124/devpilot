import time
from langchain_core.messages import HumanMessage

from app.graph.state import AppState, Message, SecurityReviewOut, SecurityFinding
from app.core.logging import get_logger
from app.core.llm import get_chat_llm

logger = get_logger("security_reviewer")

llm = get_chat_llm(temperature=0.1)
structured_security_llm = llm.with_structured_output(SecurityReviewOut)


def security_reviewer_agent(state: AppState) -> AppState:
    """
    Dedicated Security Reviewer Agent.
    Audits generated code for common vulnerabilities, injection flaws,
    hardcoded secrets, dangerous execution patterns, and missing validation.
    """
    task = state.task
    code = state.code or ""
    tool_used = state.tool_used
    filename = state.filename or "solution.py"

    prompt = f"""
You are a Principal Application Security Engineer performing a strict code security review.

Task:
{task}

Target File:
{filename} (Executed via: {tool_used})

Source Code to Audit:
```python
{code}
```

Audit the code for the following vulnerability categories:
1. Hardcoded Secrets & Credentials: API keys, tokens, passwords, private keys, connection strings.
2. Command Injection & Unsafe Shell: Use of `shell=True`, unescaped string formatting in `subprocess`, `os.system`, `os.popen`.
3. Insecure Deserialization & Code Execution: Use of `pickle.loads`, `eval()`, `exec()`, `yaml.load` without safe loader.
4. Path Traversal & Arbitrary File Access: Reading/writing outside allowed directories without path canonicalization.
5. SQL Injection: Raw string formatting in database queries instead of parameterized statements.
6. Missing Input Validation: Lack of type or boundary checks on untrusted input causing denial of service or overflows.
7. Information Disclosure: Uncaught exceptions printing raw environment variables or internal credentials.

Rules for Findings:
- Assign severity: "CRITICAL", "HIGH", "MEDIUM", "LOW", or "INFO".
- Mark `is_secure=false` if ANY CRITICAL or HIGH vulnerability is detected.
- Mark `is_secure=true` if code has only minor/no findings and is safe to execute.
- Include actionable remediation advice for each finding.
- Remember: LLM-based security review is a heuristic static analysis and does not replace penetration testing.
"""

    start_time = time.time()
    response = structured_security_llm.invoke([HumanMessage(content=prompt)])
    latency_ms = round((time.time() - start_time) * 1000)

    # Double check is_secure consistency with findings
    has_critical_or_high = any(
        f.severity.upper() in ("CRITICAL", "HIGH") for f in response.findings
    )
    if has_critical_or_high:
        response.is_secure = False

    state.security_review = response
    state.current_stage = "security_reviewed"

    # Record message in discussion
    if not response.is_secure:
        findings_summary = "; ".join(
            f"[{f.severity}] {f.explanation}" for f in response.findings
        )
        msg_content = f"🛡️ Security Review: BLOCKED (Vulnerabilities detected: {findings_summary})"
    else:
        msg_content = f"🛡️ Security Review: PASSED. {response.summary}"

    state.discussion.append(Message(agent="security_reviewer", content=msg_content))

    logger.info({
        "agent": "security_reviewer",
        "is_secure": response.is_secure,
        "findings_count": len(response.findings),
        "latency_ms": latency_ms,
    })

    return state

