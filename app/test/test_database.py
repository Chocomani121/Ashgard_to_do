from flask import render_template, redirect, url_for, request, flash
from . import test_bp
from app.tasks.test_remote_db import test_remote_db_connection

@test_bp.route('/testtask', methods=['GET', 'POST'])
def test_task():
    if request.method == 'POST':
        testtag = request.form['test_db_connection']
        print(f"\n\n\nTest Tag: {testtag}\n\n\n")
        flash(f"Test Tag: {testtag}" , "info")

    return render_template('test_page.html')




@test_bp.route('/test_remote_db', methods=['GET', 'POST'])
def connect_remote_db():
    if request.method == 'POST':
        task = test_remote_db_connection.delay()
        # print(f"\n\nRemote DB connection test started. Task ID: [{task.id}] \n\n")
        # flash(f"Remote DB connection test started. Task ID: {task.id}", "info")
        if task:
            print(task)
            flash(f"Remote DB connection test started. Task ID: {task.id}", "info")


        return redirect(url_for("test_bp.test_task"))
