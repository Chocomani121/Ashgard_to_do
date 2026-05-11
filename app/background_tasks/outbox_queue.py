import json
import logging
from urllib.parse import urlparse

from celery import shared_task
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import MetaData, create_engine, and_, or_, inspect
from sqlalchemy.dialects.mysql import insert as mysql_insert
from app import db
from app.models import OutboxEvents

logger = logging.getLogger(__name__)


def _filter_payload_for_table(table, payload):
    """
    Only bind columns that exist on the remote table. Extra keys from ORM serialization
    (e.g. renamed attrs) would otherwise break INSERT or confuse MySQL.
    """
    allowed = {c.name for c in table.columns}
    filtered = {k: v for k, v in payload.items() if k in allowed}
    dropped = sorted(set(payload.keys()) - allowed)
    if dropped:
        logger.warning(
            "Outbox payload keys not present on remote table %s (dropped): %s",
            table.name,
            dropped,
        )
    return filtered

def _resolve_remote_table(remote_md, table_name):
    """
    MetaData.tables keys may be bare names or ``schema.table`` depending on dialect/driver.
    """
    t = remote_md.tables.get(table_name)
    if t is not None:
        return t
    want = table_name.lower()
    for key, tbl in remote_md.tables.items():
        tail = key.split(".")[-1].lower()
        if tail == want:
            return tbl
    return None

def _log_remote_target_once_per_run(remote_url, seen):
    """Log host + database (no password) so Workbench checks match REMOTE_DB_URL."""
    if remote_url in seen:
        return
    seen.add(remote_url)
    try:
        p = urlparse(remote_url)
        dbname = (p.path or "").lstrip("/").split("?")[0] or "(none)"
        logger.info(
            "Outbox drain remote target: scheme=%s host=%s database=%s",
            p.scheme,
            p.hostname,
            dbname,
        )
    except Exception:
        logger.info("Outbox drain: could not parse REMOTE_DB_URL for logging")

# ----------

def _pk_where(table, pk_dict): return and_(*[table.c[k] == v for k, v in pk_dict.items()])

def _find_child_fks(remote_md, parent_table):
    refs = []
    for t in remote_md.tables.values():
        for fk in t.foreign_keys:
            if fk.column.table.name == parent_table.name:
                refs.append((t, fk.parent.name, fk.column.name))  
                # (child_table, child_fk_col, parent_pk_col)
    return refs

def _delete_row_with_children(remote_conn, remote_md, table, pk_dict, visited=None):
    if visited is None:
        visited = set()

    visit_key = (table.name, tuple(sorted(pk_dict.items())))
    if visit_key in visited:
        return
    visited.add(visit_key)

    # delete children first
    for child_table, child_fk_col, parent_pk_col in _find_child_fks(remote_md, table):
        if parent_pk_col not in pk_dict:
            continue  # composite/partial mismatch
        parent_pk_val = pk_dict[parent_pk_col]

        child_rows = remote_conn.execute(
            child_table.select().where(child_table.c[child_fk_col] == parent_pk_val)
        ).fetchall()

        child_pk_cols = [c.name for c in child_table.primary_key.columns]
        for row in child_rows:
            child_pk = {k: row._mapping[k] for k in child_pk_cols}
            _delete_row_with_children(remote_conn, remote_md, child_table, child_pk, visited)
    
    # then parent
    remote_conn.execute(table.delete().where(_pk_where(table, pk_dict)))






def _apply_upsert(remote_conn, table, payload):
    """
    MySQL upsert:
        INSERT ... ON DUPLICATE KEY UPDATE ...
    """
    stmt = mysql_insert(table).values(**payload)

    logger.debug("_apply_upsert table=%s", table.name)

    # Update all non-PK columns on conflict
    update_cols = {
        col.name: stmt.inserted[col.name]
        for col in table.columns
        if not col.primary_key
    }
    if update_cols:
        stmt = stmt.on_duplicate_key_update(**update_cols)
    result = remote_conn.execute(stmt)
    logger.debug(
        "upsert finished table=%s rowcount=%s",
        table.name,
        getattr(result, "rowcount", None),
    )


def _apply_delete(remote_conn, remote_md, table, pk_dict):
    """
    In order to delete rows we need to temporarily disable the Foreign Key check on the database 
    """
    if not pk_dict:
        raise ValueError(f"Delete event for {table.name} has empty pk_json")
    # conditions = [table.c[col_name] == col_value for col_name, col_value in pk_dict.items()]
    # del_stmt = table.delete().where(and_(*conditions))
    # remote_conn.execute(del_stmt)
    _delete_row_with_children(remote_conn, remote_md, table, pk_dict)

@shared_task
def drain_outbox(batch_size=200, max_attempts=10, reclaim_after_minutes=2):
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
        logger.error("REMOTE_DB_URL not configured")
        raise RuntimeError("REMOTE_DB_URL not configured")

    _log_urls = set()
    _log_remote_target_once_per_run(remote_url, _log_urls)

    now = datetime.now()
    stale_cutoff = now - timedelta(minutes=reclaim_after_minutes)


    # 1) pick pending + reclaimable processing
    events = (
        OutboxEvents.query
        .filter(
            or_(
                OutboxEvents.status == "pending",
                and_(
                    OutboxEvents.status == "processing",
                    OutboxEvents.processing_started_at.isnot(None),
                    OutboxEvents.processing_started_at < stale_cutoff
                )
            )
        )
        .order_by(OutboxEvents.event_id.asc())
        .limit(batch_size)
        .all()
    )

    if not events: return {"processed": 0, "done": 0, "retried": 0, "failed": 0}
    

    # 2) claim locally
    for evt in events:
        evt.status = "processing"
        evt.processing_started_at = now
    db.session.commit()


    remote_engine = create_engine(remote_url)
    remote_md = MetaData()
    remote_md.reflect(bind=remote_engine)

    processed = done = retried = failed = 0

    # optional: preserve FK order if needed
    table_priority = {"project": 1, "project_members": 2}
    events.sort(key=lambda e: (table_priority.get(e.table_name, 99), e.event_id))


    # 3) Apply each event independently (better isolation)
    for evt in events:
        processed += 1
        try:
            table = _resolve_remote_table(remote_md, evt.table_name)
            if table is None:
                available = sorted(
                    k.split(".")[-1] for k in list(remote_md.tables.keys())[:80]
                )
                raise ValueError(
                    f"Remote table not found: {evt.table_name!r}. "
                    f"Sample remote table names: {available}"
                )

            pk_dict = json.loads(evt.pk_json) if evt.pk_json else {}
            raw_payload = json.loads(evt.payload_json) if evt.payload_json else {}

            logger.info(
                "[OUTBOX] evt=%s type=%s table=%s",
                evt.event_id,
                evt.event_type,
                evt.table_name,
            )

            with remote_engine.begin() as remote_conn:
                if evt.event_type in ("insert", "update"):
                    if not raw_payload:
                        raise ValueError(f"{evt.event_type} event missing payload_json")
                    payload = _filter_payload_for_table(table, raw_payload)
                    if not payload:
                        raise ValueError(
                            f"{evt.event_type} for {evt.table_name}: after column filter, "
                            f"payload is empty (check table_name and remote schema match local)"
                        )
                    _apply_upsert(remote_conn, table, payload)
                elif evt.event_type == "delete":
                    _apply_delete(remote_conn, remote_md, table, pk_dict)
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
