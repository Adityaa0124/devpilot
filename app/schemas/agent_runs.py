from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.schemas.agent_steps import AgentStepOut


class RunListItem(BaseModel):
    """Summary item for GET /runs."""
    id: int
    task: str
    approved: Optional[bool] = None
    rounds: int = 0
    needs_clarification: bool = False
    filename: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RunResponse(BaseModel):
    """Full run detail including code, feedback, and discussion history."""
    id: int
    task: str
    plan: Optional[List[str]] = None
    code: Optional[str] = None
    execution_result: Optional[str] = None
    approved: Optional[bool] = None
    feedback: Optional[str] = None
    rounds: int = 0
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    filename: Optional[str] = None
    created_at: datetime
    steps: List[AgentStepOut] = []

    model_config = {"from_attributes": True}
