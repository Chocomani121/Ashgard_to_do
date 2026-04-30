import time
from flask import current_app
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError


def compare_DB():
    """
    Returns:
    {
        "success": bool,
        "connection": {"local": bool, "remote": bool, "error": str|None},
        "tables": {
        "local_only": [..],
        "remote_only": [..],
        "common": [..]
        },
        "columns": {
        "table_name": {
            "local_only": [..],
            "remote_only": [..],
            "type_mismatch": [{"column": "...", "local": "...", "remote": "..."}]
        }
        },
        "row_counts": {
        "table_name": {"local": int, "remote": int, "delta": int}
        }
    }
    """
    started_at = time.perf_counter()
    started_at_specifically = time.strftime("%Y-%m-%d %H:%M:%S")

    local_url  = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    remote_url = current_app.config.get("REMOTE_DB_URL")

    result = {
        "success"    : False,
        "connection" : {
                "local"     : False, 
                "remote"    : False, 
                
                "local_connect_ms"  : None,
                "remote_connect_ms" : None,
                "checked_at"        : None,          # human-readable timestamp
                "total_elapsed_ms"  : None,
                "error"             : None
            },
        "tables"     : {"local_only": [], "remote_only": [], "common": []},
        "columns"    : {},
        "row_counts" : {},
    }
  
    if not local_url or not remote_url:
        result["connection"]["error"] = "Missing SQLALCHEMY_DATABASE_URI or REMOTE_DB_URL"
        return result

    try:
        local_engine = create_engine(local_url)
        remote_engine = create_engine(remote_url)

        # 1) Connection checks
        t0 = time.perf_counter()
        with local_engine.connect() as lc:
            lc.execute(text("SELECT 1"))
        result["connection"]["local"] = True
        result["connection"]["local_connect_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        t1 = time.perf_counter()
        with remote_engine.connect() as rc:
            rc.execute(text("SELECT 1"))
        result["connection"]["remote"] = True
        result["connection"]["remote_connect_ms"] = round((time.perf_counter() - t1) * 1000, 2)

        local_inspector  = inspect(local_engine)
        remote_inspector = inspect(remote_engine)

        local_tables  = set(local_inspector.get_table_names())
        remote_tables = set(remote_inspector.get_table_names())
        # local_tables  = set(local_inspector.get_table_names()) - {"alembic_version"}
        # remote_tables = set(remote_inspector.get_table_names()) - {"alembic_version"}


        # ignore migration table if you want
        ignored = {"alembic_version"}
        local_tables -= ignored
        remote_tables -= ignored

        common = sorted(local_tables & remote_tables)
        result["tables"]["local_only"] = sorted(local_tables - remote_tables)
        result["tables"]["remote_only"] = sorted(remote_tables - local_tables)
        result["tables"]["common"] = common

        # 2) Per-table column + row count comparison
        with local_engine.connect() as lc, remote_engine.connect() as rc:
            for table_name in common:
                l_cols = {c["name"]: str(c["type"]) for c in local_inspector.get_columns(table_name)}
                r_cols = {c["name"]: str(c["type"]) for c in remote_inspector.get_columns(table_name)}
                
                l_only_cols = sorted(set(l_cols) - set(r_cols))
                r_only_cols = sorted(set(r_cols) - set(l_cols))

                mismatches = []
                for col in sorted(set(l_cols) & set(r_cols)):
                    if l_cols[col] != r_cols[col]:
                        mismatches.append({
                            "column" : col,
                            "local"  : l_cols[col],
                            "remote" : r_cols[col],
                        })
                
                if l_only_cols or r_only_cols or mismatches:
                    result["columns"][table_name] = {
                        "local_only"    : l_only_cols,
                        "remote_only"   : r_only_cols,
                        "type_mismatch" : mismatches,
                    }

                l_count = lc.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar() or 0
                r_count = rc.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar() or 0
                result["row_counts"][table_name] = {
                    "local"  : int(l_count),
                    "remote" : int(r_count),
                    "delta"  : int(l_count) - int(r_count),
                }

        # result["tables"]["local_only"]  = sorted(local_tables - remote_tables)
        # result["tables"]["remote_only"] = sorted(remote_tables - local_tables)
        # result["tables"]["common"]      = sorted(local_tables & remote_tables)


        result["success"] = True
        return result
    
    except SQLAlchemyError as e:
        result["connection"]["error"] = str(e)
        return result
    except Exception as e:
        result["connection"]["error"] = str(e)
        return result
    finally:
        result["connection"]["started_at"] = started_at_specifically
        result["connection"]["checked_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        result["connection"]["total_elapsed_ms"] = round((time.perf_counter() - started_at) * 1000, 2)
