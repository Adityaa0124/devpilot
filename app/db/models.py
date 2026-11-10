from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class AgentRun(Base):
    """Records each complete pipeline execution."""
    __tablename__ = "agent_runs"

    id                     = Column(Integer, primary_key=True, index=True)
    task                   = Column(Text, nullable=False)
    plan                   = Column(JSON)
    code                   = Column(Text)
    execution_result       = Column(Text)
    approved               = Column(Boolean)
    feedback               = Column(Text)
    rounds                 = Column(Integer, default=0)
    needs_clarification    = Column(Boolean, default=False)
    clarification_question = Column(Text)
    filename               = Column(String(255))      # set when tool=write_file
    created_at             = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    steps = relationship("AgentStep", back_populates="run", cascade="all, delete-orphan")


class AgentStep(Base):
    """A single agent message from the discussion log."""
    __tablename__ = "agent_steps"

    id         = Column(Integer, primary_key=True, index=True)
    run_id     = Column(Integer, ForeignKey("agent_runs.id"), nullable=False)
    agent      = Column(String(50), nullable=False)   # "planner", "developer", or "reviewer"
    content    = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    run = relationship("AgentRun", back_populates="steps")
