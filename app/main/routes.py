from flask import render_template, Blueprint
from flask_login import login_required

main = Blueprint('main', __name__)


@main.route("/projects") 
@login_required
def projects():
    return render_template('index.html')

@main.route("/tasks") 
@login_required
def tasks():
    return render_template('tasks.html', title="Tasks Info")

@main.route("/departments") 
@login_required
def departments():
    return render_template('departments.html')

from flask import render_template, Blueprint

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/projects") 
@login_required
def projects():
    return render_template('index.html')

@main.route("/tasks") 
@login_required
def tasks():
    login_required
    return render_template('tasks.html', title="Tasks Info")

@main.route("/all_departments") 
@login_required
def all_departments():
    login_required
    return render_template('all_departments.html')

@main.route("/members")
@login_required
def members():
    return render_template('members.html', title="Members")

@main.route("/project_details")
@login_required
def project_details():
    return render_template('project_details.html')

@main.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@main.route("/task details")
@login_required
def task_details():
    return render_template('task_details.html')

