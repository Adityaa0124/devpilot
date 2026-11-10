import os
from dotenv import load_dotenv

load_dotenv()

# LLM Provider Configuration
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()

# OpenAI Settings
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Gemini Settings
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

# Agent Context & Routing Settings
MAX_CONTEXT_MESSAGES: int = int(os.getenv("MAX_CONTEXT_MESSAGES", "6"))
MAX_ROUNDS: int = int(os.getenv("MAX_ROUNDS", "3"))

# Database Configuration (Defaults to SQLite for seamless local dev; supports PostgreSQL)
DATABASE_URL: str = os.getenv("DATABASE_URL") or "sqlite:///./devpilot.db"

# API Authentication (Optional — leave empty to disable in dev)
API_KEY: str = os.getenv("API_KEY", "")

# Sandbox / Execution Security
EXECUTION_TIMEOUT_SECONDS: int = int(os.getenv("EXECUTION_TIMEOUT_SECONDS", "10"))
ALLOW_SHELL_EXECUTION: bool = os.getenv("ALLOW_SHELL_EXECUTION", "true").lower() == "true"
