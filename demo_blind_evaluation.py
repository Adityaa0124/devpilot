"""
Blind Independent Subagents + Evaluator Demonstration Script.

Runs multiple independent ("blind") subagents to solve a coding task in isolation,
then invokes an Evaluator (Judge) agent to score each candidate across standardized
dimensions, select the best solution, and output the final verified result.
"""

import os
import sys
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.graph.state import AppState, CandidateSolution, EvaluatorOut, CandidateScore
from app.agents.planner import planner_agent
from app.agents.blind_subagents import blind_subagents_node, SUBAGENTS_CONFIG
from app.agents.evaluator import evaluator_agent
from app.graph.workflow import build_graph


def run_mock_demonstration(task: str):
    """
    Demonstrates the Blind Independent Subagents + Evaluator workflow
    using simulated independent agents and an evaluator judge.
    Ideal for offline testing, CI, and local inspection.
    """
    print("=" * 80)
    print(f"🎯 TASK: {task}")
    print("=" * 80)
    print("\n[Phase 1] 📋 Planner analyzing task...")
    time.sleep(0.4)
    print("  ✓ Task is well-specified.")
    print("  ✓ Plan formulated:")
    print("    1. Implement algorithm")
    print("    2. Handle input validation & edge cases")
    print("    3. Test with sample inputs and print outputs\n")

    print("[Phase 2] 🤖 Executing Blind Independent Subagents in Isolation...")
    print("  (Each subagent develops and executes without seeing other subagents' code)")

    # Candidate A
    print("\n  ▶ [Subagent A: Pragmatic Pythonist] generating Candidate A...")
    cand_a_code = '''def two_sum(nums, target):
    """Find two numbers that add up to target using hash map."""
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# Test
nums = [2, 7, 11, 15]
target = 9
print("Result:", two_sum(nums, target))
'''
    cand_a_out = "Result: [0, 1]"
    print("    Strategy: Clean hash map lookup with standard enumerate.")
    print(f"    Tool: run_python_code | Output: {cand_a_out}")

    # Candidate B
    print("\n  ▶ [Subagent B: Defensive Systems Engineer] generating Candidate B...")
    cand_b_code = '''def two_sum(nums, target):
    """Robust Two Sum with input validation and comprehensive error handling."""
    if not isinstance(nums, (list, tuple)):
        raise TypeError("nums must be a list or tuple of integers")
    if not isinstance(target, (int, float)):
        raise TypeError("target must be a numeric value")
    if len(nums) < 2:
        return None

    seen = {}
    for i, num in enumerate(nums):
        if not isinstance(num, (int, float)):
            raise TypeError(f"Element at index {i} is not a number: {num}")
        complement = target - num
        if complement in seen:
            return (seen[complement], i)
        seen[num] = i
    return None

# Test with valid and boundary cases
print("Valid:", two_sum([2, 7, 11, 15], 9))
print("Boundary (<2 elements):", two_sum([5], 5))
'''
    cand_b_out = "Valid: (0, 1)\nBoundary (<2 elements): None"
    print("    Strategy: Defensive type checking, bounds checks, and exception safety.")
    print(f"    Tool: run_python_code | Output: {cand_b_out.splitlines()[0]}")

    # Candidate C
    print("\n  ▶ [Subagent C: Algorithmic Specialist] generating Candidate C...")
    cand_c_code = '''def two_sum_optimized(nums, target):
    """Memory-efficient generator-based lookup for large streaming lists."""
    lookup = {}
    for idx, val in enumerate(nums):
        diff = target - val
        if diff in lookup:
            return (lookup[diff], idx)
        lookup[val] = idx
    return ()

# Benchmark test
test_arr = list(range(10000))
print("Benchmark test result:", two_sum_optimized(test_arr, 19997))
'''
    cand_c_out = "Benchmark test result: (9998, 9999)"
    print("    Strategy: Asymptotically optimal O(N) time and space with benchmark verification.")
    print(f"    Tool: run_python_code | Output: {cand_c_out}")

    candidates = [
        CandidateSolution(
            subagent_id="subagent_pragmatic",
            subagent_name="Pragmatic Pythonist",
            candidate_label="Candidate A",
            strategy="Clean hash map lookup with standard enumerate",
            code=cand_a_code,
            tool_used="run_python_code",
            execution_result=cand_a_out,
            execution_success=True,
        ),
        CandidateSolution(
            subagent_id="subagent_defensive",
            subagent_name="Defensive Systems Engineer",
            candidate_label="Candidate B",
            strategy="Defensive type checking, bounds checks, and exception safety",
            code=cand_b_code,
            tool_used="run_python_code",
            execution_result=cand_b_out,
            execution_success=True,
        ),
        CandidateSolution(
            subagent_id="subagent_performance",
            subagent_name="Algorithmic Specialist",
            candidate_label="Candidate C",
            strategy="Asymptotically optimal O(N) time and space with benchmark verification",
            code=cand_c_code,
            tool_used="run_python_code",
            execution_result=cand_c_out,
            execution_success=True,
        ),
    ]

    print("\n[Phase 3] ⚖️ Evaluator Agent performing Blind Evaluation...")
    time.sleep(0.4)
    print("\n" + "=" * 80)
    print("                        EVALUATOR SCORECARD & VERDICT")
    print("=" * 80)
    print(f"{'Candidate':<15} | {'Correctness':<12} | {'Robustness':<12} | {'Efficiency':<12} | {'Quality':<10} | {'Total Score'}")
    print("-" * 80)

    scores = [
        ("Candidate A", 10, 7, 9, 9, 88, "Clear, standard Pythonic approach, but lacks defensive input checks."),
        ("Candidate B", 10, 10, 9, 9, 95, "Flawless validation, explicit error handling, handles edge cases gracefully."),
        ("Candidate C", 10, 7, 10, 9, 91, "High efficiency with benchmark verification, minimal defensive checks."),
    ]

    for label, corr, rob, eff, qual, total, comment in scores:
        print(f"{label:<15} | {corr:<12} | {rob:<12} | {eff:<12} | {qual:<10} | {total}/100")
        print(f"  Critique: {comment}")

    print("=" * 80)
    print("🏆 WINNER: Candidate B (Defensive Systems Engineer)")
    print("Rationale: Candidate B achieved the highest aggregate score (95/100). It pairs the optimal O(N) hash map")
    print("           approach with comprehensive type checking, boundary guards for len < 2, and clean error messages.")
    print("Status: APPROVED (round 1)")
    print("=" * 80)

    print("\n🌟 WINNING CODE SOLUTION:")
    print("```python")
    print(cand_b_code)
    print("```")
    print("Execution Output:")
    print(cand_b_out)


def run_live_pipeline(task: str):
    """Runs the live LangGraph pipeline with OpenAI LLMs."""
    print(f"🚀 Running Live LangGraph Blind Multi-Agent Pipeline for task:\n'{task}'\n")
    graph = build_graph()
    state_input = {"task": task}

    for chunk in graph.stream(state_input, stream_mode="updates"):
        for node_name, state_update in chunk.items():
            print(f"\n--- [Node Completed: {node_name}] ---")
            if node_name == "planner":
                plan = state_update.get("plan", [])
                print(f"Plan ({len(plan)} steps):")
                for s in plan:
                    print(f"  - {s}")
            elif node_name == "blind_subagents":
                candidates = state_update.get("candidates", [])
                print(f"Generated {len(candidates)} Blind Candidate Solutions:")
                for c in candidates:
                    print(f"  • {c.candidate_label} ({c.subagent_name}): {c.strategy}")
                    print(f"    Tool: {c.tool_used} | Success: {c.execution_success}")
            elif node_name == "evaluator":
                eval_res = state_update.get("evaluation")
                print(f"🏆 Winner: {state_update.get('winner')}")
                print(f"Approved: {state_update.get('approved')}")
                if eval_res and hasattr(eval_res, "candidate_scores"):
                    for sc in eval_res.candidate_scores:
                        print(f"  Score for {sc.candidate_label}: {sc.total_score}/100 - {sc.verdict}")
                print(f"Rationale: {state_update.get('feedback')}")
                print("\nFinal Code:\n", state_update.get("code"))


if __name__ == "__main__":
    task = "Write a Python function to solve the Two-Sum problem efficiently and handle edge cases."
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])

    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not api_key.startswith("sk-..."):
        run_live_pipeline(task)
    else:
        run_mock_demonstration(task)

