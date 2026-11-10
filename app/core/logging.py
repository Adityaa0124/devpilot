import logging
from datetime import datetime, timezone


class StructuredFormatter(logging.Formatter):
    """
    Formata cada log record como:
        YYYY-MM-DD HH:MM:SS | LEVEL    | [agent] key=value  key=value ...
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)

        if isinstance(record.msg, dict):
            data = dict(record.msg)
            # Extrai o agent do dict; fallback para o nome do logger (ex: "multi_agent.planner" → "planner")
            agent = data.pop("agent", record.name.split(".")[-1])
            message = "  ".join(f"{k}={v}" for k, v in data.items())
        else:
            agent = record.name.split(".")[-1]
            message = record.getMessage()

        line = f"{timestamp} | {level} | [{agent}] {message}"

        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)

        return line


def get_logger(agent_name: str) -> logging.Logger:
    """
    Returns a logger configured for the given agent.

    Usage:
        logger = get_logger("reviewer")
        logger.info({"round": 1, "approved": True, "latency_ms": 340})
    """
    logger = logging.getLogger(f"multi_agent.{agent_name}")

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False  # Evita duplicação com o root logger

    return logger
