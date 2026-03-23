import os
from dotenv import load_dotenv
from app import create_app

# load_dotenv()

flask_app = create_app()
celery_app = flask_app.extensions["celery"]


# Import tasks so they are registered with Celery
import app.tasks.test_remote_db
import app.tasks.backup_db