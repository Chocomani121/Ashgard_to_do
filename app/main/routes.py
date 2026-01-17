from flask import render_template, Blueprint, redirect, url_for, flash, request
from flask_login import login_required
from app.models import Department, User
from app import db # Required for committing changes

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/projects") 
@login_required
def projects():
    return render_template('index.html')

@main.route("/tasks")
@login_required 
def tasks():
    return render_template('tasks.html', title="Tasks Info")

@main.route("/all_departments")
@login_required
def all_departments():
    departments = Department.query.all()
    users = User.query.all()  # Get all users from database
    stats = {'total': len(departments)}
    return render_template('all_departments.html', departments=departments, users=users, stats=stats)

@main.route("/department/add", methods=['POST'])
@login_required
def add_department():
    name = request.form.get('department_name')
    member_ids = request.form.getlist('member_ids')  # Get list of selected member IDs
    
    if name:
        new_dept = Department(department_name=name)
        db.session.add(new_dept)
        db.session.flush()  # Flush to get the department_id
        
        # Assign selected members to the new department
        if member_ids:
            for member_id in member_ids:
                try:
                    user = User.query.get(int(member_id))
                    if user:
                        user.department_id = new_dept.department_id
                except (ValueError, TypeError):
                    continue
        
        db.session.commit()
        flash('Department added successfully!', 'success')
    return redirect(url_for('main.all_departments'))

@main.route("/department/edit/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_department(id):
    # This 'id' comes from the URL and is used to find the department
    department = Department.query.get_or_404(id)
    if request.method == 'POST':
        department.department_name = request.form.get('department_name')
        member_ids = request.form.getlist('member_ids')  # Get list of selected member IDs
        
        # Update department members
        # First, remove all current members from this department
        for user in department.members:
            user.department_id = None
        
        # Then assign new members to the department
        if member_ids:
            for member_id in member_ids:
                try:
                    user = User.query.get(int(member_id))
                    if user:
                        user.department_id = department.department_id
                except (ValueError, TypeError):
                    continue
        
        db.session.commit()
        flash('Department updated!', 'success')
        return redirect(url_for('main.all_departments'))
    return render_template('edit_department.html', department=department)

@main.route("/department/delete/<int:id>", methods=['POST'])
@login_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    try:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted!', 'warning')
    except Exception:
        db.session.rollback()
        flash('Cannot delete department. It may have users assigned to it.', 'danger')
        
    return redirect(url_for('main.all_departments'))

# --- Existing Routes ---

@main.route("/members")
@login_required
def members():
    users = User.query.all()
    return render_template('members.html', title="Members", users=users)

@main.route("/project_details")
@login_required
def project_details():
    return render_template('project_details.html')

@main.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@main.route("/task_details")
@login_required
def task_details():
    return render_template('task_details.html')
