from celery import shared_task
from flask import current_app
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime
import pytz


@shared_task(bind=True)
def remote_db_backup(self):
    tz = pytz.timezone('Asia/Manila')
    t = datetime.now(tz)
    dt = t.strftime("%m-%d-%Y | %H:%M:%S")

    print(f"\n\n\n[{dt}]\t\t\t--- Backing up Local DB to remote... \n")
    # return 
    
    local_url   =   current_app.config.get("SQLALCHEMY_DATABASE_URI")
    remote_url  =   current_app.config.get("REMOTE_DB_URL")
    
    if not local_url or not remote_url:
        print(f"\n[{dt}]\t--- Can't connect to database\n")
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
        total = len(tables)

        for idx, table in enumerate(tables, start=1):
            # Before work on this table
            self.update_state(
                state="PROGRESS",
                meta={
                    "phase"     : "sync_table",
                    "table"     : table.name,
                    "status"    : "processing",
                    "index"     : idx,
                    "total"     : total,
                    "completed" : list(stats.keys()),
                },
            )

            with local_engine.connect() as local_conn, remote_engine.connect() as remote_conn:
                remote_conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                remote_conn.commit()
                try:
                    rows = local_conn.execute(table.select()).fetchall()
                    count = len(rows)
                    print(f"\n[{dt}]\t\t\t--- Truncating table: {table.name}")
                    remote_conn.execute(text(f"TRUNCATE TABLE `{table.name}`"))
                    if rows:
                        ins = table.insert()
                        for row in rows:
                            remote_conn.execute(ins.values(**row._mapping))
                    remote_conn.commit()
                    stats[table.name] = count
                except SQLAlchemyError as e:
                    remote_conn.rollback()
                    return {
                        "success": False,
                        "tables": stats,
                        "error": f"Table {table.name} : {str(e)}",
                        "message": f"Rolling back truncate table: {table.name}",
                    }
                finally:
                    remote_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                    remote_conn.commit()
            
            # After this table succeeds
            self.update_state(
                state="PROGRESS",
                meta={
                    "phase"         : "sync_table",
                    "table"         : table.name,
                    "status"        : "done",
                    "rows_copied"   : stats[table.name],
                    "index"         : idx,
                    "total"         : total,
                    "completed"     : list(stats.keys()),
                },
            )

        # --------------------------

        # with local_engine.connect() as local_conn, remote_engine.connect() as remote_conn:
        #     remote_conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        #     remote_conn.commit()

        #     for table in tables:
        #         try:
        #             rows  = local_conn.execute(table.select()).fetchall()
        #             count = len(rows)

        #             print(f"\n[{dt}]\t\t\t--- Truncating table: {table.name}")
        #             remote_conn.execute(text(f"TRUNCATE TABLE `{table.name}`"))

        #             if rows:
        #                 ins = table.insert()
        #                 for row in rows:
        #                     remote_conn.execute(ins.values(**row._mapping))
                    
        #             remote_conn.commit()
        #             stats[table.name] = count

        #         except SQLAlchemyError as e:
        #             print(f"\n[{dt}]\t\t\t--- Rolling back truncate table: {table.name} ")
        #             remote_conn.rollback()
        #             return {
        #                 "success"   :   False,
        #                 "tables"    :   stats,
        #                 "error"     :   f"Table {table.name} : {str(e)}",
        #                 "message"   :   f"Rolling back truncate table: {table.name}"
        #             }
            
        #     remote_conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        #     remote_conn.commit()
        
        print(f"\n[{dt}]\t--- Backup complete ")
        return {"success" : True, "tables" : stats, "message" : "Backup database complete"}

    except SQLAlchemyError as e:
        print(f"\n[{dt}]\t\t\t--- Backup SQL error ")
        return {"success": False, "tables": {}, "error": str(e), "message" : "Backup SQL error"}
    except Exception as e:
        print(f"\n[{dt}]\t\t\t--- Backup error ")
        return {"success": False, "tables": {}, "error": str(e), "message" : "Backup error"}


