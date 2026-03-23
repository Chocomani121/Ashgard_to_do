from celery import shared_task
from flask import current_app
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import SQLAlchemyError


@shared_task
def db_backup():
    print("\n\n\nHello World!\n\n\n")
    # return 
    
    local_url   =   current_app.config.get("SQLALCHEMY_DATABASE_URI")
    remote_url  =   current_app.config.get("REMOTE_DB_URL")
    
    if not local_url or not remote_url:
        return {"success"   :   False,
                "tables"    :   {},
                "error"     :   "Local or remote DB URL not configured",
            }
    try:
        local_engine    =   create_engine(local_url)
        remote_engine   =   create_engine(remote_url)
    
        metadata    =   MetaData()
        metadata.reflect(bind=local_engine)

        tables = [t for t in metadata.sorted_tables if t.name != "alembic_version"]
        stats = {}

        with local_engine.connect() as local_conn, remote_engine.connect() as remote_conn:
            remote_conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            remote_conn.commit()

            for table in tables:
                try:
                    rows  = local_conn.execute(table.select()).fetchall()
                    count = len(rows)

                    remote_conn.execute(text(f"TRUNCATE TABLE   `{table.name}`"))

                    if rows:
                        ins = table.insert()
                        for row in rows:
                            remote_conn.execute(ins.values(**row._mapping))
                    
                    remote_conn.commit()
                    stats[table.name] = count
                    
                except SQLAlchemyError as e:
                    remote_conn.rollback()
                    return {
                        "success"   :   False,
                        "tables"    :   stats,
                        "error"     :   f"Table {table.name} : {str(e)}",
                    }
            
            remote_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            remote_conn.commit()
        
        return {"success" : True, "tables" : stats}

    except SQLAlchemyError as e:
        return {"success": False, "tables": {}, "error": str(e)}
    except Exception as e:
        return {"success": False, "tables": {}, "error": str(e)}


