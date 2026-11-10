from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db

router = APIRouter()


@router.get("/health", tags=["health"], summary="Health check")
def health(db: Session = Depends(get_db)):
    """Returns API status and database connectivity."""
    db_status = "unknown"
    session_to_close = None
    try:
        # If invoked directly outside FastAPI request context where db is the default Depends object
        if not hasattr(db, "execute"):
            from app.db.session import SessionLocal
            db = SessionLocal()
            session_to_close = db
            
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    finally:
        if session_to_close:
            session_to_close.close()

    return {"status": "ok" if db_status == "connected" else "degraded", "database": db_status}
