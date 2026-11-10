from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.security import get_api_key
from app.db.session import get_db

limiter = Limiter(key_func=get_remote_address)
from app.db.models import AgentRun, AgentStep
from app.graph.workflow import build_graph
from app.schemas.task import TaskRequest
from app.schemas.agent_runs import RunResponse

router = APIRouter()

graph = build_graph()


@router.post("/run", response_model=RunResponse, summary="Run the multi-agent pipeline", dependencies=[Depends(get_api_key)])
@limiter.limit("10/minute")
def run(request: Request, task_request: TaskRequest, db: Session = Depends(get_db)):
    """Runs the Planner → Developer → Reviewer pipeline and persists the result."""
    try:
        result = graph.invoke({"task": task_request.task})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db_run = AgentRun(
        task=result["task"],
        plan=result.get("plan"),
        code=result.get("code"),
        execution_result=result.get("execution_result"),
        approved=result.get("approved"),
        feedback=result.get("feedback"),
        rounds=result.get("round", 0),
        needs_clarification=result.get("needs_clarification", False),
        clarification_question=result.get("clarification_question"),
        filename=result.get("filename"),
    )
    db.add(db_run)
    db.flush()  # get the ID before creating steps

    for m in result.get("discussion", []):
        db.add(AgentStep(run_id=db_run.id, agent=m.agent, content=m.content))

    db.commit()
    db.refresh(db_run)

    return db_run
