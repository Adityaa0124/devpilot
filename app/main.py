import sys
from app.graph.workflow import build_graph

graph = build_graph()

if len(sys.argv) < 2:
    print("Usage: python -m app.main \"<task description>\"")
    print("Example: python -m app.main \"Write a function that adds two numbers\"")
    sys.exit(1)

task = " ".join(sys.argv[1:])
result = graph.invoke({"task": task})

# --- Final Execution Results ---

print("\n" + "="*60)
print("TASK")
print("="*60)
print(result["task"])

# .get() is used because LangGraph only populates keys that were written or modified.
# Unvisited fields (e.g. plan during immediate clarification) are omitted.
plan = result.get("plan")
code = result.get("code")
execution_result = result.get("execution_result")
feedback = result.get("feedback")
approved = result.get("approved")
needs_clarification = result.get("needs_clarification", False)
clarification_question = result.get("clarification_question")
filename = result.get("filename", "")
round_count = result.get("round", 0)

if plan:
    print("\n" + "="*60)
    print(f"PLAN ({len(plan)} steps)")
    print("="*60)
    for step in plan:
        print(f"  {step}")

if code:
    print("\n" + "="*60)
    print("GENERATED CODE")
    print("="*60)
    print(code)

if execution_result:
    print("\n" + "="*60)
    print("EXECUTION RESULT")
    print("="*60)
    print(execution_result)

if feedback:
    print("\n" + "="*60)
    approved_label = "APPROVED" if approved else "NOT APPROVED"
    print(f"REVIEW — {approved_label} (round {round_count})")
    print("="*60)
    print(feedback)

print("\n" + "="*60)
print("DISCUSSION HISTORY")
print("="*60)
for msg in result.get("discussion", []):
    print(f"\n[{msg.agent.upper()}]")
    print(msg.content)

# --- Final User Summary ---
print("\n" + "="*60)
print("RESULT")
print("="*60)

if needs_clarification:
    print("I need more information before I can complete this task.\n")
    print(f"? {clarification_question}")
elif approved:
    location = f" -> saved to workspace/{filename}" if filename else ""
    print(f"Task completed successfully in {round_count} round(s).{location}")
else:
    print(f"Could not complete the task after {round_count} attempt(s).")
    print("Last reviewer feedback:")
    print(f"  {feedback}")
