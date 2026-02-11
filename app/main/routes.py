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
    return render_template('all_departments.html', departments=departments, users=users, stats=stats, dept_projects_data=dept_projects_data)

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
    return render_template('members.html', title="Members", users=users)

@main.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@main.route("/task_details")
@main.route("/task_details/<int:id>")
@login_required
def task_details(id=None):
    # If no ID provided, get the first task or handle appropriately
    if id is None:
        task = Task.query.first()
    else:
        task = Task.query.get(id)
    
    if not task:
        flash('Task not found', 'error')
        return redirect(url_for('project.projects'))
    
    # Assignees for this task (from TaskAssignee or fallback to single owner from p_members_id)
    task_assignees = []
    try:
        if task.assignees:
            for ta in task.assignees:
                if ta.project_member and ta.project_member.member_id:
                    u = User.query.get(ta.project_member.member_id)
                    if u:
                        task_assignees.append(u)
    except (ProgrammingError, OperationalError):
        pass  # task_assignees table may not exist yet
    if not task_assignees and task.p_members_id:
        pm = ProjectMembers.query.get(task.p_members_id)
        if pm and pm.member_id:
            u = User.query.get(pm.member_id)
            if u:
                task_assignees.append(u)
    
    # Project members (for Edit Task "Assigned member" dropdown: project members + project manager if not already a member)
    task_project_members = []
    if task.project_id:
        project = Project.query.get(task.project_id)
        pms = ProjectMembers.query.filter_by(project_id=task.project_id).all()
        for pm in pms:
            if pm.member_id:
                u = User.query.get(pm.member_id)
                if u:
                    task_project_members.append({'p_members_id': pm.p_members_id, 'name': u.name or u.username})
        # Ensure project manager is in the list (PM can assign tasks to themselves)
        if project and project.project_manager:
            pm_member_ids = [pm.member_id for pm in pms if pm.member_id]
            if project.project_manager not in pm_member_ids:
                manager_user = User.query.get(project.project_manager)
                if manager_user:
                    pm_row = ProjectMembers.query.filter_by(
                        project_id=task.project_id,
                        member_id=project.project_manager
                    ).first()
                    if not pm_row:
                        pm_row = ProjectMembers(
                            project_id=task.project_id,
                            member_id=project.project_manager,
                            role='Project Manager'
                        )
                        db.session.add(pm_row)
                        try:
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                            pm_row = ProjectMembers.query.filter_by(
                                project_id=task.project_id,
                                member_id=project.project_manager
                            ).first()
                    if pm_row:
                        task_project_members.append({
                            'p_members_id': pm_row.p_members_id,
                            'name': manager_user.name or manager_user.username
                        })
    
    # Role flags for subtask views: PM sees "Subtask (Project Manager)", other project members see "Subtask"
    project = Project.query.get(task.project_id) if task.project_id else None
    is_project_manager = (project and current_user.member_id == project.project_manager)
    is_project_member = False
    if project:
        if is_project_manager:
            is_project_member = True
        else:
            pm_entry = ProjectMembers.query.filter_by(
                project_id=task.project_id,
                member_id=current_user.member_id
            ).first()
            is_project_member = pm_entry is not None
    
    # Check if user can edit/mark complete this task
    can_edit_task = _can_edit_task(task, current_user)
    
    # Get project for delete permission check
    project = Project.query.get(task.project_id) if task.project_id else None
    
    # p_members_id of current assignees (for edit task multi-select)
    assignee_p_members_ids = []
    try:
        if task.assignees:
            for ta in task.assignees:
                if ta.project_member:
                    assignee_p_members_ids.append(ta.project_member.p_members_id)
    except (ProgrammingError, OperationalError):
        pass
    if not assignee_p_members_ids and task.p_members_id:
        assignee_p_members_ids.append(task.p_members_id)
    
    return render_template('task_details.html', task=task, project=project, task_assignees=task_assignees, task_project_members=task_project_members, assignee_p_members_ids=assignee_p_members_ids, is_project_manager=is_project_manager, is_project_member=is_project_member, can_edit_task=can_edit_task)
