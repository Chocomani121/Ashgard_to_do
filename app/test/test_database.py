import pytz, os
from flask import render_template, redirect, url_for, request, flash, jsonify, session, current_app
from . import test_bp
from app.background_tasks import backup_db_task, remote_db_connection_task
from celery.result import AsyncResult
from datetime import datetime

from app.test.test_table_backup import simulate_project_creation_and_queue_events, drain_outbox_to_remote_simulated, drain_bg_task
from app.background_tasks.modules.compare_local_x_remote import compare_DB
from app.background_tasks import outbox_queue

feature_db_backups = os.getenv("feature_db_backups")


@test_bp.route('/testtask', methods=['GET', 'POST'])
def test_task(): 
    local_url   =   current_app.config.get("SQLALCHEMY_DATABASE_URI")
    remote_url  =   current_app.config.get("REMOTE_DB_URL")
    print(f"\n\nLocal: {local_url}")
    print(f"\nRemote: {str(remote_url)}\n\n")

    return render_template('test_page.html', local_url=local_url, remote_url=remote_url)



# FLAGs FEATURE---------------------------------------
# 
if feature_db_backups == 'ON':
    @test_bp.route('/testtask2', methods=['GET', 'POST'])
    def test_task2():
        return render_template('test_page_2.html')

# Link: https://dev.to/triketora/build-your-own-feature-flags-manager-in-flask-python-1jo0
# ----------------------------------------------------


# POLLING THE RESULT
@test_bp.route('/getres/<task_id>')
def get_result(task_id):
    task  = AsyncResult(task_id)
    ready = task.ready()
    output = {"state" : task.state, "ready" : ready}

    if ready: 
        if task.successful():
            output["result"] = task.result
        else:
            err = task.result
            output["result"] = {"success" : False, "error" : str(err) if err else "Task failed"}
    else: 
        output['result'] = None
        if task.state == "PROGRESS" and isinstance(task.info, dict):
            output["progress"] = task.info

    # return output
    return jsonify(output)



# check remote db connection
@test_bp.route('/test_remote_db', methods=['GET', 'POST'])
def connect_remote_db():
    if request.method == 'POST':
        task    = remote_db_connection_task.test_remote_db_connection.delay()
        progbar = request.form.get('progbar')

        
        if progbar:
            # ----POLLING/Non-blocking
            print(f"\n\n :D \n\n")
            if "application/json" in (request.headers.get("Accept") or ""):
                return jsonify(task_id=task.id)
            flash(f"Task queued. Task ID: {task.id}", "info")
            
        else:
            # ----Blocking
            result  = task.get(timeout=20)

            if result['success']:
                print(f"\n\n {result} \n\n")
                flash(f"BLOCKING: {result['message']}", "success")
            else:
                flash(f"BLOCKING: Remote DB connection test stopped. Task ID: {task.id}", "success")
        
        return redirect(url_for("test_bp.connect_remote_db"))

    return redirect(url_for("test_bp.test_task"))


# -------------------------------------------------------------

# trigger this to MANUALLY activate DB backup (EVERY TABLE)
@test_bp.route('/trigger_backup', methods=['GET', 'POST'])
def trigger_backup():
    if request.method == 'POST':
        tz = pytz.timezone('Asia/Manila')
        t = datetime.now(tz)
        dt = t.strftime("%m-%d-%Y | %H:%M:%S")

        print(f"\n\n\n\n Database backup --- {dt} \n\n\n\n")
        task = backup_db_task.remote_db_backup.delay()

        if "application/json" in (request.headers.get("Accept") or ""):
            return jsonify(task_id=task.id)
        flash(f"Backup queued ({dt}). Task ID: {task.id}", "info")
        return redirect(url_for("test_bp.test_task"))
    
    # return render_template('test_page.html')
    return redirect(url_for("test_bp.test_task"))



# START: SAMPLE entry to Projects table-------------------------------------------

# enter a sample value into Project and ProjectMembers tables
@test_bp.route('/evenquetest', methods=['GET', 'POST'])
def evenquetest():
    if request.method == 'POST':
        print('\n\n\n testing que... \n\n\n')

        simulate_project_creation_and_queue_events(department_id=25, manager_user_id=4, member_user_ids=[2,8,9,4])
        
        flash(f"eventque test done", "info")
        print('\n\n\n eventque test done \n\n\n')

    # return render_template('test_page.html')
    return redirect(url_for("test_bp.test_task"))


# sync the local database to the remote
@test_bp.route('/drainevent', methods=['GET', 'POST'])
def drainevent():
    if request.method == 'POST':
        print('\n\n\n draining que... \n\n\n')

        # drain_outbox_to_remote_simulated()
        task = outbox_queue.drain_outbox.delay()
        result = task.get(timeout=20)

        print(f"\n\n {result} \n\n")
        flash(f"drainque test done: {result}", "success")

        # if "application/json" in (request.headers.get("Accept") or ""):
        #     return jsonify(task_id=task.id)
        # flash(f"Task ID: {task.id}", "info")
        # return redirect(url_for("test_bp.test_task"))


    return redirect(url_for("test_bp.test_task"))

# END: SAMPLE entry to Projects table-------------------------------------------


@test_bp.route("/db-diff", methods=["GET"])
def db_diff():
  data = compare_DB()
  return jsonify(data), (200 if data["success"] else 500)
