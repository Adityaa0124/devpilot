import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_api_key

limiter = Limiter(key_func=get_remote_address)

from app.db.models import AgentRun, AgentStep
from app.db.session import SessionLocal
from app.graph.workflow import build_graph
from app.schemas.task import TaskRequest

router = APIRouter()

graph = build_graph()
_executor = ThreadPoolExecutor()


def _to_dict(obj) -> dict:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, dict):
        return obj
    return dict(obj)


def _build_event(node_name: str, full_state: dict) -> dict | None:
    """Builds the SSE event payload for a completed node."""
    if node_name == "planner":
        if full_state.get("needs_clarification"):
            return {
                "event": "agent_done",
                "agent": "planner",
                "decision": "needs_clarification",
                "clarification_question": full_state.get("clarification_question"),
            }
        plan = full_state.get("plan") or []
        return {
            "event": "agent_done",
            "agent": "planner",
            "decision": "plan_ready",
            "steps_count": len(plan),
            "plan": plan,
        }

    if node_name == "developer":
        return {
            "event": "agent_done",
            "agent": "developer",
            "tool": full_state.get("tool_used"),
            "round": full_state.get("round", 0),
            "code": full_state.get("code"),
            "filename": full_state.get("filename"),
            "execution_result": full_state.get("execution_result"),
        }

    if node_name == "security_reviewer":
        sec = full_state.get("security_review")
        sec_dict = sec.model_dump() if hasattr(sec, "model_dump") else (sec if isinstance(sec, dict) else {})
        return {
            "event": "agent_done",
            "agent": "security_reviewer",
            "is_secure": sec_dict.get("is_secure", True),
            "findings_count": len(sec_dict.get("findings", [])),
            "summary": sec_dict.get("summary", ""),
            "findings": sec_dict.get("findings", []),
        }

    if node_name == "test_generator":
        return {
            "event": "agent_done",
            "agent": "test_generator",
            "tests_passed": full_state.get("tests_passed"),
            "test_file": full_state.get("test_file"),
            "test_results": full_state.get("test_results"),
        }

    if node_name == "reviewer":
        return {
            "event": "agent_done",
            "agent": "reviewer",
            "approved": full_state.get("approved"),
            "round": full_state.get("round", 0),
            "feedback": full_state.get("feedback"),
            "needs_clarification": full_state.get("needs_clarification"),
            "clarification_question": full_state.get("clarification_question"),
        }

    if node_name == "blind_subagents":
        raw_candidates = full_state.get("candidates") or []
        candidates_data = [
            c.model_dump() if hasattr(c, "model_dump") else c
            for c in raw_candidates
        ]
        return {
            "event": "agent_done",
            "agent": "blind_subagents",
            "candidates_count": len(candidates_data),
            "candidates": candidates_data,
            "tool": full_state.get("tool_used"),
            "round": full_state.get("round", 0),
            "code": full_state.get("code"),
            "filename": full_state.get("filename"),
            "execution_result": full_state.get("execution_result"),
        }

    if node_name == "evaluator":
        eval_obj = full_state.get("evaluation")
        eval_dict = eval_obj.model_dump() if hasattr(eval_obj, "model_dump") else (eval_obj if isinstance(eval_obj, dict) else {})
        return {
            "event": "agent_done",
            "agent": "evaluator",
            "winner": full_state.get("winner"),
            "evaluation_summary": full_state.get("evaluation_summary"),
            "evaluation": eval_dict,
            "approved": full_state.get("approved"),
            "round": full_state.get("round", 0),
            "feedback": full_state.get("feedback"),
            "code": full_state.get("code"),
            "tool": full_state.get("tool_used"),
            "execution_result": full_state.get("execution_result"),
        }

    return None


def _run_pipeline(task: str, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue):
    """
    Runs the LangGraph pipeline in a background thread.
    Sends SSE events via asyncio.Queue as each agent completes.
    Persists the result to the database when done.
    """
    db = SessionLocal()
    full_state: dict = {}

    def send(event: dict):
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)

    try:
        for chunk in graph.stream({"task": task}, stream_mode="updates"):
            for node_name, raw_update in chunk.items():
                updates = _to_dict(raw_update)
                full_state.update(updates)

                event = _build_event(node_name, full_state)
                if event:
                    send(event)

        db_run = AgentRun(
            task=task,
            plan=full_state.get("plan"),
            code=full_state.get("code"),
            execution_result=full_state.get("execution_result"),
            approved=full_state.get("approved"),
            feedback=full_state.get("feedback"),
            rounds=full_state.get("round", 0),
            needs_clarification=full_state.get("needs_clarification", False),
            clarification_question=full_state.get("clarification_question"),
            filename=full_state.get("filename"),
        )
        db.add(db_run)
        db.flush()

        for m in full_state.get("discussion", []):
            agent = m.get("agent") if isinstance(m, dict) else m.agent
            content = m.get("content") if isinstance(m, dict) else m.content
            db.add(AgentStep(run_id=db_run.id, agent=agent, content=content))

        db.commit()

        send({"event": "done", "run_id": db_run.id})

    except Exception as e:
        send({"event": "error", "detail": str(e)})

    finally:
        db.close()
        asyncio.run_coroutine_threadsafe(queue.put(None), loop)  # sentinel


@router.post("/run/stream", summary="Run the pipeline with real-time SSE updates", dependencies=[Depends(get_api_key)])
@limiter.limit("10/minute")
async def run_stream(request: Request, task_request: TaskRequest):
    """
    Runs the full DevPilot pipeline and streams SSE events in real-time.
    """
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()

    loop.run_in_executor(_executor, _run_pipeline, task_request.task, loop, queue)

    async def event_stream():
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
