#!/bin/bash



celery -A celery_worker worker --loglevel=info &
gunicorn -w 5 --bind 0.0.0.0:5000 --timeout 120 run:app