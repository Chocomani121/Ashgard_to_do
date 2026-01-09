from flask import render_template, Blueprint

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/projects") 
def projects():
    return render_template('index.html')

@main.route("/tasks") 
def tasks():
    return render_template('tasks.html', title="Tasks Info")

@main.route("/departments") 
def all_departments():
    return render_template('all_departments.html')

@main.route("/members")
def members():
    return render_template('members.html', title="Members")

@main.route("/project_details")
def project_details():
    return render_template('project_details.html')

@main.route("/profile")
def profile():
    return render_template('profile.html')

@main.route("/all_departments")
def all_departments():
    return render_template('all_departments.html')

@main.route("/task details")
def task_details():
    return render_template('task_details.html')

@main.route("/department")
def departments():
    return render_template('departments.html')

from flask import render_template, Blueprint

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/projects") 
def projects():
    return render_template('index.html')

@main.route("/tasks") 
def tasks():
    return render_template('tasks.html', title="Tasks Info")

@main.route("/all_departments") 
def all_departments():
    return render_template('all_departments.html', title="All Departments")

@main.route("/members")
def members():
    return render_template('members.html', title="Members")

@main.route("/project_details")
def project_details():
    return render_template('project_details.html')

@main.route("/profile")
def profile():
    return render_template('profile.html')

@main.route("/task details")
def task_details():
    return render_template('task_details.html')

