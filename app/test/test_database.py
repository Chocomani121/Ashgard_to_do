from flask import render_template, redirect, url_for, request, flash, jsonify
from . import test_bp
from app.tasks import test_remote_db, backup_db
from celery.result import AsyncResult
from datetime import datetime
import pytz

@test_bp.route('/testtask', methods=['GET', 'POST'])
def test_task():
    # if request.method == 'POST':
    #     testtag = request.form['test_db_connection']
    #     print(f"\n\n\nTest Tag: {testtag}\n\n\n")
    #     flash(f"Test Tag: {testtag}" , "info")

    return render_template('test_page.html')



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

    # return output
    return jsonify(output)




@test_bp.route('/test_remote_db', methods=['GET', 'POST'])
def connect_remote_db():
    if request.method == 'POST':
        task    = test_remote_db.test_remote_db_connection.delay()
        progbar = request.form.get('progbar')

        
        if progbar:
            # ----POLLING/Non-blocking
            print(f"\n\n :D \n\n")
            if "application/json" in (request.headers.get("Accept") or ""):
                return jsonify(task_id=task.id)
            flash(f"Task queued. Task ID: {task.id}", "info")
            
        else:
            # ----Blocking
            result  = task.get(timeout=10)

            if result['success']:
                print(f"\n\n {result} \n\n")
                flash(f"WAITING: {result['message']}", "success")
            else:
                flash(f"Remote DB connection test stopped. Task ID: {task.id}", "danger")
        
        return redirect(url_for("test_bp.connect_remote_db"))

    return render_template('test_page.html')


# -------------------------------------------------------------

@test_bp.route('/trigger_backup', methods=['GET', 'POST'])
def trigger_backup():
    """Trigger a background backup of local DB to remote."""
    if request.method == 'POST':
        tz = pytz.timezone('Asia/Manila')
        t = datetime.datetime.now(tz)
        dt = t.strftime("%m-%d-%Y | %H:%M:%S")


        print(f"\n\n Database backup --- {dt} \n\n")
        task = backup_db.backup_local_to_remote.delay()

        if "application/json" in (request.headers.get("Accept") or ""):
            return jsonify(task_id=task.id)
        flash(f"Backup queued. Task ID: {task.id}", "info")
        return redirect(url_for("test_bp.test_task"))
    
    return render_template('test_page.html')
