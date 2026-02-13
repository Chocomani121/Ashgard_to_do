from flask import render_template, Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Department, User, Project, Deadlines, ProjectMembers, Task, TaskAssignee, SubTask,  Report, ReportCC, Comment
from app import db
from datetime import datetime, date, time
from sqlalchemy import or_, text
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.orm import joinedload, selectinload
import json
import random

main = Blueprint('main', __name__)


def _can_edit_task(task, user):
    """Check if user can edit or mark complete a task.
    Returns True if user is project manager OR assigned to the task."""
    if not task or not user:
        return False
    project = Project.query.get(task.project_id) if task.project_id else None
    if project and user.member_id == project.project_manager:
        return True
    try:
        if task.assignees:
            for ta in task.assignees:
                if ta.project_member and ta.project_member.member_id == user.member_id:
                    return True
    except (ProgrammingError, OperationalError):
        pass
    if task.p_members_id:
        pm = ProjectMembers.query.get(task.p_members_id)
        if pm and pm.member_id == user.member_id:
            return True
    return False


@main.route("/all_departments")
@login_required
def all_departments():
    departments = Department.query.all()
    # Get all users (we'll filter unassigned ones in JavaScript for dropdown, but need all for Edit modal)
    users = User.query.all()
    # Build department projects data for the Department Projects table (newest first)
    # Progress = task-based (completed / total), same as projects index
    projects = Project.query.order_by(Project.project_id.desc()).all()
    dept_projects_data = []
    for project in projects:
        dept = Department.query.get(project.department_id) if project.department_id else None
        manager = User.query.get(project.project_manager) if project.project_manager else None
        deadline = Deadlines.query.get(project.deadlines_id) if project.deadlines_id else None
        project_tasks = Task.query.filter_by(project_id=project.project_id).all()
        task_total = len(project_tasks)
        task_completed = sum(1 for t in project_tasks if t.task_status == 'Completed')
        progress_pct = round(task_completed / task_total * 100, 1) if task_total else 0
        latest_task = Task.query.filter_by(project_id=project.project_id).order_by(Task.task_id.desc()).first()
        latest_task_title = latest_task.task_name if latest_task else None
        dept_projects_data.append({
            'project': project,
            'department': dept,
            'manager': manager,
            'deadline': deadline,
            'progress_pct': progress_pct,
            'latest_task_title': latest_task_title,
        })
    # Stats for cards: total, completed, ongoing
    stats = {
        'total': len(departments),
        'completed': len([p for p in projects if p.project_status and p.project_status.lower() == 'completed']),
        'ongoing': len([p for p in projects if p.project_status and p.project_status.lower() == 'ongoing']),
    }
    return render_template('all_departments.html', departments=departments, users=users, stats=stats, dept_projects_data=dept_projects_data, today=date.today())

@main.route("/department/add", methods=['POST'])
@login_required
def add_department():
    name = request.form.get('department_name')
    member_ids = request.form.getlist('member_ids') 
    
    if name:
        new_dept = Department(department_name=name)
        db.session.add(new_dept)
        db.session.flush()
        
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

    department = Department.query.get_or_404(id)
    if request.method == 'POST':
        department.department_name = request.form.get('department_name')
        member_ids = request.form.getlist('member_ids')  

        for user in department.members:
            user.department_id = None
        
        if member_ids:
            for member_id in member_ids:
                try:
                    user = User.query.get(int(member_id))
                    if user:
                        user.department_id = department.department_id
                except (ValueError, TypeError):
                    continue
        
        # Update edited_on when name or members change (onupdate only fires on Dept row changes)
        department.edited_on = datetime.now()
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


@main.route("/approvals")
def approvals():
    return render_template('approvals.html', title="Approvals")

@main.route("/members")
@login_required
def members():
    users = User.query.all()
    return render_template('members.html', title="Members", members=users, total_users=len(users))

@main.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

