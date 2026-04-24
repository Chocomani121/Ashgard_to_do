import pytz
import json
from celery import shared_task
from datetime import datetime
from flask import current_app
from sqlalchemy import MetaData, create_engine, text, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.mysql import insert as mysql_insert
from app import db
from app.models import OutboxEvents




def _apply_upsert(remote_conn, table, payload):
  """
  MySQL upsert:
    INSERT ... ON DUPLICATE KEY UPDATE ...
  """
  stmt = mysql_insert(table).values(**payload)
  # Update all non-PK columns on conflict
  update_cols = {
      col.name: stmt.inserted[col.name]
      for col in table.columns
      if not col.primary_key
  }
  if update_cols:
      stmt = stmt.on_duplicate_key_update(**update_cols)
  remote_conn.execute(stmt)


def _apply_delete(remote_conn, table, pk_dict):
  """
  Delete by PK (supports composite PK if pk_dict has multiple keys).
  """
  if not pk_dict:
      raise ValueError(f"Delete event for {table.name} has empty pk_json")
  conditions = [table.c[col_name] == col_value for col_name, col_value in pk_dict.items()]
  del_stmt = table.delete().where(and_(*conditions))
  remote_conn.execute(del_stmt)


@shared_task
def drain_outbox(batch_size=200, max_attempts=10):
    """
    Drain pending outbox events and apply to remote DB.
    Returns:
        {
        "processed": int,
        "done": int,
        "retried": int,
        "failed": int
        }
    """
    remote_url = current_app.config.get("REMOTE_DB_URL")
    if not remote_url:
        raise RuntimeError("REMOTE_DB_URL not configured")
    # 1) Claim pending events from local DB
    events = (
        OutboxEvents.query
        .filter_by(status="pending")
        .order_by(OutboxEvents.event_id.asc())
        .limit(batch_size)
        .all()
    )

    if not events:
      return {"processed": 0, "done": 0, "retried": 0, "failed": 0}
    
    now = datetime.now()
    for evt in events:
        evt.status = "processing"
        evt.processing_started_at = now
    db.session.commit()


    # 2) Prepare remote metadata once
    remote_engine = create_engine(remote_url)
    remote_md = MetaData()
    remote_md.reflect(bind=remote_engine)

    processed = done = retried = failed = 0

    # Optional FK-safe ordering for inserts/updates
    table_priority = {"project": 1, "project_members": 2}
    events.sort(key=lambda e: (table_priority.get(e.table_name, 99), e.event_id))


    # 3) Apply each event independently (better isolation)
    for evt in events:
        processed += 1
        try:
            table = remote_md.tables.get(evt.table_name)
            if table is None:
                raise ValueError(f"Remote table not found: {evt.table_name}")
            
            pk_dict = json.loads(evt.pk_json) if evt.pk_json else {}
            payload = json.loads(evt.payload_json) if evt.payload_json else {}

            with remote_engine.begin() as remote_conn:
                if evt.event_type in ("insert", "update"):
                    if not payload:
                        raise ValueError(f"{evt.event_type} event missing payload_json")
                    _apply_upsert(remote_conn, table, payload)
                elif evt.event_type == "delete":
                    _apply_delete(remote_conn, table, pk_dict)
                else:
                    raise ValueError(f"Unknown event_type: {evt.event_type}")
            
            evt.status = "done"
            evt.processing_finished_at = datetime.now()
            evt.remote_applied_at = datetime.now()
            evt.last_error = None
            done += 1

        except Exception as exc:
            evt.attempt_count = (evt.attempt_count or 0) + 1
            evt.last_error = str(exc)
            evt.processing_finished_at = datetime.now()
            
            if evt.attempt_count >= max_attempts:
                evt.status = "failed"
                failed += 1
            else:
                evt.status = "pending"
                retried += 1
        
        finally:
            db.session.commit()
    
    return {
        "processed" : processed,
        "done"      : done,
        "retried"   : retried,
        "failed"    : failed,
    }
