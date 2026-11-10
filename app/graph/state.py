from pydantic import BaseModel, Field
from typing import List, Optional

# Structured output schemas — each agent is forced to return one of these via .with_structured_output()

class PlannerOut(BaseModel):
    steps: List[str]
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class DeveloperOut(BaseModel):
    code: str
    tool: Optional[str] = "run_python_code"  # "run_python_code", "write_file", or "run_shell_command"
    filename: Optional[str] = None           # only set when tool="write_file"


class SubagentOut(BaseModel):
    strategy: str                            # Summary of the independent perspective and strategy taken
    code: str                                # Complete, executable Python or shell solution
    tool: Optional[str] = "run_python_code"  # "run_python_code", "write_file", or "run_shell_command"
    filename: Optional[str] = None           # only set when tool="write_file"


class CandidateSolution(BaseModel):
    """An independent candidate solution generated blindly by a subagent."""
    subagent_id: str                         # e.g., "subagent_pragmatic", "subagent_defensive", "subagent_performance"
    subagent_name: str                       # e.g., "Pragmatic Pythonist", "Defensive Systems Engineer", "Algorithmic Specialist"
    candidate_label: str                     # Anonymized label: "Candidate A", "Candidate B", "Candidate C"
    strategy: str                            # Technical approach summary
    code: str                                # Source code
    tool_used: Optional[str] = None          # Execution tool selected
    filename: Optional[str] = None           # Filename if write_file was used
    execution_result: Optional[str] = None   # stdout/stderr or confirmation message
    execution_success: bool = True           # Whether tool executed without runtime crash


class CandidateScore(BaseModel):
    """Multi-criteria scorecard for an individual candidate solution."""
    candidate_label: str                     # "Candidate A", "Candidate B", etc.
    correctness_score: int                   # 0-10: Does it solve the task and run without error?
    robustness_score: int                    # 0-10: How well does it handle edge cases and invalid inputs?
    efficiency_score: int                    # 0-10: Time and space complexity, computational overhead
    code_quality_score: int                  # 0-10: Cleanliness, readability, adherence to PEP 8, modern APIs
    total_score: int                         # 0-100: Weighted aggregate score
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    verdict: str = ""


class EvaluatorOut(BaseModel):
    """Evaluation verdict and comparative analysis from the Evaluator agent."""
    candidate_scores: List[CandidateScore] = Field(default_factory=list)
    winner_label: str                        # Selected winning candidate: "Candidate A", "Candidate B", etc.
    winner_subagent_name: Optional[str] = None
    selection_rationale: str
    evaluation_summary: str
    best_code: str                           # The winning code (or synthesized optimal solution)
    best_tool: Optional[str] = None
    approved: bool = True
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class SecurityFinding(BaseModel):
    """Specific security vulnerability or risk identified in generated code."""
    severity: str                            # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    file_name: str
    line_or_location: str
    explanation: str
    suggested_remediation: str


class SecurityReviewOut(BaseModel):
    """Structured security review findings."""
    is_secure: bool                          # False if CRITICAL or HIGH findings exist
    findings: List[SecurityFinding] = Field(default_factory=list)
    summary: str
    disclaimer: str = "LLM-based security review provides heuristic vulnerability detection and does not guarantee complete security."


class TestGenerationOut(BaseModel):
    """Automated unit test generation schema."""
    test_code: str                           # Pytest unit tests for the generated solution
    test_file: str = "test_generated.py"
    test_description: str
    framework: str = "pytest"


class ReviewerOut(BaseModel):
    approved: bool
    feedback: str
    needs_clarification: bool = False
    clarification_question: Optional[str] = None


class Message(BaseModel):
    agent: str   # "planner", "developer", "reviewer", "security_reviewer", "test_generator", "evaluator"
    content: str


# Shared state passed between all agents by LangGraph.
class AppState(BaseModel):
    """
    Central shared state flowing across all LangGraph nodes in DevPilot.
    Tracks task specifications, plans, code artifacts, execution outputs,
    automated tests, security audits, and lifecycle metrics.
    """
    # Core Task & Context
    task: str
    discussion: List[Message] = Field(default_factory=list)
    plan: Optional[List[str]] = None

    # Code Artifacts & File Tracking
    code: Optional[str] = None
    files_modified: List[str] = Field(default_factory=list)
    tool_used: Optional[str] = None
    filename: Optional[str] = None          # set when tool_used="write_file"
    execution_result: Optional[str] = None  # stdout/stderr or confirmation message

    # Automated Testing
    test_code: Optional[str] = None
    test_file: Optional[str] = None
    test_results: Optional[str] = None
    tests_passed: Optional[bool] = None

    # Dedicated Security Review
    security_review: Optional[SecurityReviewOut] = None

    # Reviewer Feedback & Approval
    feedback: Optional[str] = None
    approved: Optional[bool] = None

    # Blind Subagents & Evaluator Candidates
    candidates: List[CandidateSolution] = Field(default_factory=list)
    evaluation: Optional[EvaluatorOut] = None
    winner: Optional[str] = None
    evaluation_summary: Optional[str] = None

    # Workflow Routing & Lifecycle State
    current_stage: str = "initialized"      # "initialized", "planned", "developed", "tested", "security_reviewed", "reviewed", "completed", "failed", "clarification_needed"
    round: int = 0                          # Iteration counter
    max_rounds: int = 3                     # Safety termination limit
    final_status: str = "pending"           # "pending", "completed", "failed", "clarification_needed"

    needs_clarification: bool = False
    clarification_question: Optional[str] = None
