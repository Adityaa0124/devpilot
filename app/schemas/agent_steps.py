from pydantic import BaseModel
from datetime import datetime


class AgentStepOut(BaseModel):
    """A single agent message read from the database."""
    id: int
    agent: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
