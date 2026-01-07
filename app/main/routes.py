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
def departments():
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

@main.route("/all_departments")
@login_required
def all_departments():
    return render_template('all_division.html')

@main.route("/projects")
@login_required
def projects():  # Make sure this name only appears ONCE in this file
    return render_template('layout.html')

@main.route("/dashboard")
@login_required
def dashboard():  # This function must have a different name
    return render_template('layout.html')