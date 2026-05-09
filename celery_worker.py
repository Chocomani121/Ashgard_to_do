import os
from dotenv import load_dotenv
from app import create_app

# load_dotenv()

flask_app = create_app()
celery_app = flask_app.extensions["celery"]


# Import tasks so they are registered with Celery (include outbox + enqueue or Beat/worker
# will not know these task names and .delay() from the web app will never execute).
import app.background_tasks.remote_db_connection_task
import app.background_tasks.backup_db_task
import app.background_tasks.enque_event_task
import app.background_tasks.outbox_queue