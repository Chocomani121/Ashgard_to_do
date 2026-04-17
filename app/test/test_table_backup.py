import pytz
import json
from datetime import datetime
from flask import current_app
from sqlalchemy import MetaData, create_engine, text, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.mysql import insert as mysql_insert
from app import db
from app.models import Project, ProjectMembers, OutboxEvents




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


def enqueue_outbox_event(table_name, event_type, pk_dict, payload_dict=None, version_ts=None):
  evt = OutboxEvents(
      status        =   "pending",
      table_name    =   table_name,
      event_type    =   event_type,  # insert/update/delete
      pk_json       =   json.dumps(pk_dict) if pk_dict else None,
      pk_str        =   "|".join([f"{k}={v}" for k, v in (pk_dict or {}).items()]),
      payload_json  =   json.dumps(payload_dict, default=str) if payload_dict else None,
      version_ts    =   version_ts,
  )
  db.session.add(evt)


# *** START ---- simulate creating Project & assinging ProjectMembers
# simulate_project_creation_and_queue_events(department_id=25, manager_user_id=5, member_user_ids=[2,8,9,4])
def simulate_project_creation_and_queue_events(department_id, manager_user_id, member_user_ids):
    """
    Simulate local writes:
        - creates 2 projects
        - creates ProjectMembers rows for each project
        - enqueues outbox events in same transaction
    """
    # 1) Create Project A and B locally
    p1 = Project(
        department_id   =   department_id,
        project_manager =   manager_user_id,
        project_name    =   "TableBackupTest___1",
        client_name     =   "Client Alpha",
        project_status  =   "Ongoing",
        priority        =   "High",
        progress        =   "0%",
        project_desc    =   "Simulation project A"
    )
    p2 = Project(
        department_id   =   department_id,
        project_manager =   manager_user_id,
        project_name    =   "TableBackupTest___2",
        client_name     =   "Client Beta",
        project_status  =   "Ongoing",
        priority        =   "Medium",
        progress        =   "0%",
        project_desc    =   "Simulation project B"
    )
    # db.session.add_all([p1, p2])
    db.session.add_all([p1])
    db.session.flush()  # get project_id

    # 2) Queue outbox events for project inserts
    # for p in (p1, p2):
    #     enqueue_outbox_event(
    #         table_name  =   "project",
    #         event_type  =   "insert",
    #         pk_dict     =   {"project_id": p.project_id},
    #         payload_dict=   _serialize_row(p),
    #         version_ts  =   _pick_version_ts(p),
    #     )
    enqueue_outbox_event(
        table_name   =   "project",
        event_type   =   "insert",
        pk_dict      =   {"project_id": p1.project_id},
        payload_dict =   _serialize_row(p1),
        version_ts   =   _pick_version_ts(p1),
    )

    

    # 3) Create ProjectMembers rows for each project
    pm_rows = []
    for user_id in member_user_ids:
        pm_rows.append(ProjectMembers(project_id=p1.project_id, member_id=user_id, role="Member"))
        # pm_rows.append(ProjectMembers(project_id=p2.project_id, member_id=user_id, role="Member"))
    db.session.add_all(pm_rows)
    db.session.flush()  # get p_members_id

    # 4) Queue outbox events for project_members inserts
    for pm in pm_rows:
        enqueue_outbox_event(
            table_name  =   "project_members",
            event_type  =   "insert",
            pk_dict     =   {"p_members_id": pm.p_members_id},
            payload_dict=   _serialize_row(pm),
            version_ts  =   _pick_version_ts(pm),
        )

    # 5) Commit once: data + outbox atomically
    db.session.commit()

    return {
        # "projects_created": [p1.project_id, p2.project_id],
        "projects_created": [p1.project_id],
        "project_members_created": [pm.p_members_id for pm in pm_rows],
    }


def drain_outbox_to_remote_simulated(batch_size=100):
    """
    Simulate a worker draining pending events and applying to remote.
    This uses prints + pseudo-remote SQL for visualization.
    """

    remote_url  =   current_app.config.get("REMOTE_DB_URL")

    # Claim pending events ordered by event_id
    events = (
        OutboxEvents.query
        .filter_by(status="pending")
        .order_by(OutboxEvents.event_id.asc())
        .limit(batch_size)
        .all()
    )

    if not events:
        print("No pending outbox events.")
        return {"applied": 0}

    # FK-safe processing order for inserts
    table_priority = {"project": 1, "project_members": 2}
    events.sort(key=lambda e: (table_priority.get(e.table_name, 99), e.event_id))

    applied = 0
    for evt in events:
        evt.status = "processing"
        evt.processing_started_at = datetime.now()
    db.session.commit()


    # check remote connection 
    if not remote_url:
        print('------ cant connect to Remote DB')
        return {"success"   :   False,
                "tables"    :   {},
                "error"     :   "cant connect to Remote DB",
            }

    try:
        # Here you would open remote engine/connection and apply SQL.

        remote_engine = create_engine(remote_url)


        # For simulation, we'll print exactly what would happen.
        for evt in events:
            pk = json.loads(evt.pk_json) if evt.pk_json else {}
            payload = json.loads(evt.payload_json) if evt.payload_json else {}
            if evt.event_type in ("insert", "update"):
                print(f"[REMOTE UPSERT] table={evt.table_name} pk={pk} version_ts={evt.version_ts}")
                # Real code would do:
                # INSERT ... ON DUPLICATE KEY UPDATE ... with version gating
            elif evt.event_type == "delete":
                print(f"[REMOTE DELETE] table={evt.table_name} pk={pk}")
                # Real code:
                # DELETE FROM table WHERE pk=...
            else:
                raise ValueError(f"Unknown event_type={evt.event_type}")
            evt.status = "done"
            evt.processing_finished_at = datetime.now()
            evt.remote_applied_at = datetime.now()
            applied += 1
            print(f"\n\n\n")
        db.session.commit()
        return {"applied": applied}
    
    except Exception as ex:
        # Mark all currently processing events back to pending or failed
        for evt in events:
            if evt.status == "processing":
                evt.attempt_count           = (evt.attempt_count or 0) + 1
                evt.last_error              = str(ex)
                evt.status                  = "pending" if evt.attempt_count < 5 else "failed"
                evt.processing_finished_at  = datetime.now()
        db.session.commit()
        return {"applied": applied, "error": str(ex)}
    
# *** END

# ----------


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
            evt.processing_finished_at = datetime.utcnow()
            evt.remote_applied_at = datetime.utcnow()
            evt.last_error = None
            done += 1

        except Exception as exc:
            evt.attempt_count = (evt.attempt_count or 0) + 1
            evt.last_error = str(exc)
            evt.processing_finished_at = datetime.utcnow()
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
