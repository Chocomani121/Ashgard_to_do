import json
from celery import shared_task
from datetime import datetime
from flask import current_app
from sqlalchemy import MetaData, create_engine, text, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.mysql import insert as mysql_insert
from app import db
from app.models import OutboxEvents




def _pick_version_ts(row_obj):
    """Best-effort timestamp picker for versioning."""
    for name in ("updated_on", "edited_on", "created_at", "created_on", "creation_date"):
        if hasattr(row_obj, name):
            val = getattr(row_obj, name)
            if val is not None:
                return val
    return datetime.now()

def _serialize_row(model_obj):
    """Serialize SQLAlchemy model row to plain dict."""
    data = {}
    for col in model_obj.__table__.columns:
        data[col.name] = getattr(model_obj, col.name)
    return data

def enqueue_outbox_event(table_name, event_type, pk_dict, payload_dict=None, version_ts=None, outbox_desc=None):
  print("\n\n\n Outbox triggered!! \n\n\n")
  evt = OutboxEvents(
      status        =   "pending",
      table_name    =   table_name,
      event_type    =   event_type,  # insert/update/delete
      pk_json       =   json.dumps(pk_dict) if pk_dict else None,
      pk_str        =   "|".join([f"{k}={v}" for k, v in (pk_dict or {}).items()]),
      payload_json  =   json.dumps(payload_dict, default=str) if payload_dict else None,
      version_ts    =   version_ts,
      outbox_desc   =   outbox_desc,
  )
  db.session.add(evt)


@shared_task
def enqueue_task(table_name, event_type, pk_dict, payload_dict=None, version_ts=None, outbox_desc=None):
    try:
        enqueue_outbox_event(table_name, event_type, pk_dict, payload_dict, version_ts, outbox_desc)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise