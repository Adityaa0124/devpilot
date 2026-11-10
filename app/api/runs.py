from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import AgentRun
from app.schemas.agent_runs import RunResponse, RunListItem

router = APIRouter()


@router.get("/runs", response_model=List[RunListItem], summary="List all runs")
def list_runs(
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    limit: int = Query(default=20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
):
    """Returns paginated runs in descending order of creation. Use ?page=2&limit=10 to navigate."""
    offset = (page - 1) * limit
    return (
        db.query(AgentRun)
        .order_by(AgentRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/runs/{run_id}", response_model=RunResponse, summary="Get a run by ID")
def get_run(run_id: int, db: Session = Depends(get_db)):
    """Returns the full run detail including the discussion history."""
    db_run = db.query(AgentRun).filter(AgentRun.id == run_id).first()
    if not db_run:
        raise HTTPException(status_code=404, detail="Run not found")
    return db_run
