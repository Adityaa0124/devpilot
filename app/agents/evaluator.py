import time
from typing import List

from langchain_core.messages import HumanMessage

from app.graph.state import AppState, Message, EvaluatorOut, CandidateScore
from app.core.logging import get_logger
from app.core.llm import get_chat_llm

logger = get_logger("evaluator")

llm = get_chat_llm(temperature=0.2)
structured_evaluator_llm = llm.with_structured_output(EvaluatorOut)


def _format_candidates_for_evaluation(state: AppState) -> str:
    """Formats all candidate solutions blindly for the evaluator."""
    if not state.candidates:
        return f"""
Candidate: Candidate A
Tool: {state.tool_used or 'run_python_code'}
Code:
{state.code or 'No code provided.'}
Execution Result:
{state.execution_result or 'No execution result available.'}
"""

    blocks = []
    for c in state.candidates:
        status = "Execution Succeeded (No Errors)" if c.execution_success else "Execution Failed / Threw Error"
        block = f"""
==================================================
CANDIDATE: {c.candidate_label}
Strategy / Stated Approach: {c.strategy}
Tool Selected: {c.tool_used}
Execution Status: {status}

Execution Output (stdout / stderr / confirmation):
{c.execution_result or 'None'}

Source Code:
```python
{c.code}
```
==================================================
"""
        blocks.append(block.strip())

    return "\n\n".join(blocks)


def evaluator_agent(state: AppState) -> AppState:
    """
    Evaluator Agent (Arbiter & Judge).
    Objectively assesses all candidate solutions generated blindly by the independent subagents.
    Scores each candidate across standardized rubrics, selects the winner, and outputs the optimal solution.
    """
    task = state.task
    candidates_text = _format_candidates_for_evaluation(state)

    prompt = f"""
You are the Lead Evaluator and Arbiter for an autonomous multi-agent software engineering system.

Your mission:
Independent, blind subagents have independently generated candidate solutions for the task below.
Each candidate worked in total isolation and executed their code to provide runtime evidence.

Task:
{task}

Candidate Solutions & Execution Results:
{candidates_text}

Evaluation Rubric:
For EACH candidate, score these four dimensions from 0 to 10:
1. Correctness & Execution (Weight: 40%): Did the code execute cleanly? Does the stdout/output prove that it correctly and completely fulfills the user's task?
2. Robustness & Edge Cases (Weight: 25%): Does it defend against bad inputs, empty collections, type mismatches, and unexpected exceptions?
3. Algorithmic Efficiency & Complexity (Weight: 15%): Optimal time/space complexity, appropriate data structures, no redundant work.
4. Code Quality & Standards (Weight: 20%): Readability, clean structure, PEP 8 compliance, clear naming, modern library APIs (e.g. OpenAI v1.x).

Calculate Total Score (0 - 100) using the formula:
Total = (Correctness * 4) + (Robustness * 2.5) + (Efficiency * 1.5) + (Code Quality * 2.0)

Winner Selection:
- Select the overall winning candidate (e.g. "Candidate A", "Candidate B", etc.).
- Provide a clear, evidence-based rationale comparing the strengths and trade-offs of all candidates.
- In `best_code`, provide the winning code. If the winning candidate could benefit from a critical edge-case check found in another candidate, you may synthesize those improvements into the final `best_code`.
- Set `approved=true` if at least one candidate solution is valid, functional, and satisfies the task.
- Set `needs_clarification=true` ONLY if the task itself is missing critical specifications that make all solutions unviable.
"""

    start_time = time.time()
    response = structured_evaluator_llm.invoke([HumanMessage(content=prompt)])
    latency_ms = round((time.time() - start_time) * 1000)

    # Resolve winning candidate metadata if available
    winner_subagent_name = None
    winning_candidate_obj = None
    for c in state.candidates:
        if c.candidate_label.lower() == response.winner_label.lower() or c.candidate_label in response.winner_label:
            winner_subagent_name = c.subagent_name
            winning_candidate_obj = c
            break

    response.winner_subagent_name = winner_subagent_name
    if not response.best_tool and winning_candidate_obj:
        response.best_tool = winning_candidate_obj.tool_used

    # Update state
    state.evaluation = response
    state.winner = f"{response.winner_label} ({winner_subagent_name})" if winner_subagent_name else response.winner_label
    state.evaluation_summary = response.evaluation_summary
    state.approved = response.approved
    state.feedback = response.selection_rationale
    state.needs_clarification = response.needs_clarification
    state.clarification_question = response.clarification_question
    state.current_stage = "evaluated"
    state.final_status = "approved" if response.approved else ("clarification_needed" if response.needs_clarification else "rejected")

    # Update active code and execution result to winning candidate
    state.code = response.best_code
    if response.best_tool:
        state.tool_used = response.best_tool
    if winning_candidate_obj:
        state.filename = winning_candidate_obj.filename
        state.execution_result = winning_candidate_obj.execution_result
        if winning_candidate_obj.filename and winning_candidate_obj.filename not in state.files_modified:
            state.files_modified.append(winning_candidate_obj.filename)

    state.round += 1

    # Record structured message in discussion
    scores_summary = ", ".join(
        f"{s.candidate_label}: {s.total_score}/100" for s in response.candidate_scores
    )
    discussion_content = (
        f"🏆 Evaluation Verdict: Winner is {state.winner}\n"
        f"Scores: {scores_summary}\n"
        f"Rationale: {response.selection_rationale}\n"
        f"Summary: {response.evaluation_summary}"
    )
    state.discussion.append(Message(agent="evaluator", content=discussion_content))

    logger.info({
        "agent": "evaluator",
        "winner": state.winner,
        "approved": response.approved,
        "round": state.round,
        "latency_ms": latency_ms,
    })

    return state
