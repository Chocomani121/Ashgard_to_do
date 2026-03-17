from celery import shared_task
from celery import Task

from flask import current_app
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import time


@shared_task
def test_remote_db_connection():
    # Background task that tests the connection to the remote MySQL database.
    # Returns a dict with success status and optional error message.
    remote_url = current_app.config.get("REMOTE_DB_URL")
    if not remote_url:
        return {"success": False, "error": "REMOTE_DB_URL is not configured"}
    
    try:
        engine = create_engine(remote_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"success": True, "message": "Remote DB connection OK"}
    except SQLAlchemyError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}
    

# --------------------------------------------------

# @shared_task(ignore_result=False)
# def add(a: int, b: int) -> int:    return a + b

# @shared_task() 
# def block() -> None:    time.sleep(5)

# @shared_task(bind=True, ignore_result=False)
# def process(self: Task, total: int) -> object:
#     for i in range(total):
#         self.update_state(state="PROGESS", meta={"current": i + 1, "total": total})
#         time.sleep(1)

#     return {"current": total, "total": total}

