from pydantic import BaseModel


class TaskRequest(BaseModel):
    """Request body for POST /run."""
    task: str
