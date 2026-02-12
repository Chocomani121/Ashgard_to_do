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


project_bp = Blueprint('project', __name__, template_folder='templates', static_folder='static', static_url_path='/project/static')


def _generate_task_code():
    """Return a unique task code in the form TK#### (e.g. TK0001, TK4721)."""
    for _ in range(100):
        code = 'TK{:04d}'.format(random.randint(0, 9999))
        if not Task.query.filter_by(generated_code=code).first():
            return code
    raise ValueError('Could not generate unique task code')


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


@project_bp.route("/")
@project_bp.route("/projects") 
# @cache.cached(timeout=60)
@login_required
def projects():
    # Fetch all projects with related data (newest first)
    projects = Project.query.order_by(Project.project_id.desc()).all()
    departments = Department.query.all()
    users = User.query.all()
    
    # Prepare projects data for template (progress = task-based, same as project details)
    projects_data = []
    for project in projects:
        dept = Department.query.get(project.department_id) if project.department_id else None
        manager = User.query.get(project.project_manager) if project.project_manager else None
        deadline = Deadlines.query.get(project.deadlines_id) if project.deadlines_id else None
        
        # Get priority from project (defaults to 'High' if not set or column doesn't exist)
        try:
            priority_raw = project.priority
            priority = str(priority_raw) if priority_raw else 'High'
        except (AttributeError, KeyError):
            priority = 'High'  # Fallback if column doesn't exist
        
        # Progress from tasks (completed / total), same logic as project details
        project_tasks = Task.query.filter_by(project_id=project.project_id).all()
        task_total = len(project_tasks)
        task_completed = sum(1 for t in project_tasks if t.task_status == 'Completed')
        progress_pct = round(task_completed / task_total * 100, 1) if task_total else 0
        # Latest task (newest by task_id) for "Last Tasks" column
        latest_task = Task.query.filter_by(project_id=project.project_id).order_by(Task.task_id.desc()).first()
        latest_task_title = latest_task.task_name if latest_task else None
        
        projects_data.append({
            'project': project,
            'department': dept,
            'manager': manager,
            'deadline': deadline,
            'priority': priority,
            'progress_pct': progress_pct,
            'latest_task_title': latest_task_title,
        })
    
    # Calculate statistics from projects
    # Count only High priority projects for the Priority card
    # Use the same logic as display: None/null priority defaults to 'High'
    high_priority_count = 0
    for item in projects_data:
        try:
            priority_val = item['priority']  # Use the converted priority from projects_data
            if priority_val and priority_val.lower() == 'high':
                high_priority_count += 1
        except (AttributeError, KeyError):
            pass  # Skip if priority column doesn't exist
    
    stats = {
        'pending': len([p for p in projects if p.project_status and p.project_status.lower() == 'pending']),
        'high_priority': high_priority_count,  # Only count projects with High priority
        'completed': len([p for p in projects if p.project_status and p.project_status.lower() == 'completed']),
        'on_hold': len([p for p in projects if p.project_status and p.project_status.lower() == 'on hold'])
    }
    
    # Convert users to JSON-serializable format for JavaScript
    # Pass as Python list, let Jinja2 handle JSON encoding with |tojson filter
    users_json = [
        {
            'member_id': user.member_id,
            'name': user.name or user.username,
            'username': user.username,
            'department_id': user.department_id
        }
        for user in users
    ]
    
    return render_template('index.html', projects_data=projects_data, departments=departments, users=users, users_json=users_json, stats=stats)

@project_bp.route("/tasks")
@login_required 
def tasks():
    return render_template('tasks.html', title="Tasks Info")

@project_bp.route("/all_departments")
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

# --- Existing Routes ---


@project_bp.route("/project_details")
@project_bp.route("/project_details/<int:id>")
@login_required
def project_details(id=None):
    # If no ID provided, get the first project or handle appropriately
    if id is None:
        project = Project.query.first()
    else:
        project = Project.query.get(id)
    
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('project.projects'))
    
    # Get related data
    manager = User.query.get(project.project_manager) if project.project_manager else None
    deadline = Deadlines.query.get(project.deadlines_id) if project.deadlines_id else None
    department = Department.query.get(project.department_id) if project.department_id else None
    
    # Normalize status: convert Pending/Cancelled to Ongoing
    display_status = project.project_status
    if not display_status or display_status == 'Pending' or display_status == 'Cancelled':
        display_status = 'Ongoing'
    
    # Get assigned members for this project (all members, regardless of department)
    assigned_members = []
    if project:
        project_members = ProjectMembers.query.filter_by(project_id=project.project_id).all()
        for project_member in project_members:
            if project_member.member_id:
                user = User.query.get(project_member.member_id)
                if user:
                    assigned_members.append({
                        'user': user,
                        'role': project_member.role or 'Team Member'
                    })
    
    # Get tasks for this project (newest first)
    tasks = []
    if project:
        project_tasks = Task.query.filter_by(project_id=project.project_id).order_by(Task.task_id.desc()).all()
        for task in project_tasks:
            # Get task assignees (multiple): from TaskAssignee first, then fallback to p_members_id
            assignees = []
            try:
                if task.assignees:
                    for ta in task.assignees:
                        if ta.project_member and ta.project_member.member_id:
                            u = User.query.get(ta.project_member.member_id)
                            if u:
                                assignees.append(u)
            except (ProgrammingError, OperationalError):
                pass
            if not assignees and task.p_members_id:
                pm = ProjectMembers.query.get(task.p_members_id)
                if pm and pm.member_id:
                    u = User.query.get(pm.member_id)
                    if u:
                        assignees.append(u)
            owner = assignees[0] if assignees else None  # legacy single owner for compatibility
            
            # Calculate task progress (completed subtasks / total subtasks)
            subtasks = SubTask.query.filter_by(parent_task_id=task.task_id).all()
            total_subtasks = len(subtasks)
            completed_subtasks = len([st for st in subtasks if st.is_checked])
            progress = f"{completed_subtasks}/{total_subtasks}" if total_subtasks > 0 else "0/0"
            
            # Normalize task status
            task_status = task.task_status or 'Ongoing'
            if task_status == 'Pending' or task_status == 'Cancelled':
                task_status = 'Ongoing'
            
            # Check if current user can edit/mark complete this task
            can_edit = _can_edit_task(task, current_user)
            
            tasks.append({
                'task': task,
                'owner': owner,
                'assignees': assignees,
                'progress': progress,
                'status': task_status,
                'can_edit': can_edit
            })
    
    users = User.query.all()
    users_json = [
        {'member_id': u.member_id, 'name': u.name or u.username, 'username': u.username, 'department_id': u.department_id}
        for u in users
    ]
    # Current assigned member ids/names for edit modal prefill (manager + assigned_members, no duplicate)
    manager_id = manager.member_id if manager else None
    edit_initial = []
    if manager:
        edit_initial.append({'member_id': manager.member_id, 'name': manager.name or manager.username})
    for m in assigned_members:
        uid = m['user'].member_id
        if uid != manager_id:
            edit_initial.append({'member_id': uid, 'name': m['user'].name or m['user'].username})
    edit_initial_members_json = edit_initial
    # For Create Task modal: only project assigned members can be assigned to a task
    task_assignable_members = [
        {'id': m['user'].member_id, 'name': m['user'].name or m['user'].username}
        for m in assigned_members
    ]
    is_project_manager = (current_user.member_id == project.project_manager) if project.project_manager else False

    # Task progress for donut chart: count completed vs ongoing, compute percentages
    task_completed_count = sum(1 for t in tasks if t.get('status') == 'Completed')
    task_ongoing_count = sum(1 for t in tasks if t.get('status') == 'Ongoing')
    task_total = len(tasks)
    task_completed_pct = round(task_completed_count / task_total * 100, 1) if task_total else 0
    task_ongoing_pct = round(task_ongoing_count / task_total * 100, 1) if task_total else 0
    progress_pct = task_completed_pct  # center label: progress = completed %

    return render_template('project_details.html',
                         project=project,
                         manager=manager,
                         deadline=deadline,
                         department=department,
                         display_status=display_status,
                         assigned_members=assigned_members,
                         tasks=tasks,
                         users=users,
                         users_json=users_json,
                         edit_initial_members_json=edit_initial_members_json,
                         task_assignable_members=task_assignable_members,
                         is_project_manager=is_project_manager,
                         task_completed_count=task_completed_count,
                         task_ongoing_count=task_ongoing_count,
                         task_total=task_total,
                         task_completed_pct=task_completed_pct,
                         task_ongoing_pct=task_ongoing_pct,
                         progress_pct=progress_pct)

@project_bp.route("/project_details/<int:id>/update_manager", methods=['POST'])
@login_required
def update_project_manager(id):
    project = Project.query.get_or_404(id)
    if current_user.member_id != project.project_manager:
        flash('Only the project manager can perform this action.', 'danger')
        return redirect(url_for('project.projects'))
    project_manager_id = request.form.get('project_manager')
    if not project_manager_id:
        flash('Please select a Project Manager', 'danger')
        return redirect(url_for('project.project_details', id=id))
    try:
        project.project_manager = int(project_manager_id)
        db.session.commit()
        flash('Project manager updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update: {}'.format(str(e)), 'danger')
    return redirect(url_for('project.project_details', id=id))

@project_bp.route("/project_details/<int:id>/update_members", methods=['POST'])
@login_required
def update_project_members(id):
    project = Project.query.get_or_404(id)
    if current_user.member_id != project.project_manager:
        flash('Only the project manager can perform this action.', 'danger')
        return redirect(url_for('project.projects'))
    member_ids = request.form.getlist('project_members')
    if not member_ids:
        flash('Please select at least one member', 'danger')
        return redirect(url_for('project.project_details', id=id))
    try:
        selected_member_ids = set()
        for mid in member_ids:
            if mid and str(mid).isdigit():
                selected_member_ids.add(int(mid))

        current_pms = ProjectMembers.query.filter_by(project_id=project.project_id).all()
        could_not_remove = []

        for pm in current_pms:
            if pm.member_id in selected_member_ids:
                continue
            # Member was deselected — only delete if not referenced by any task
            used_in_task_tbl = Task.query.filter_by(
                project_id=project.project_id, p_members_id=pm.p_members_id
            ).count() > 0
            used_in_assignees = (
                TaskAssignee.query.join(Task)
                .filter(
                    Task.project_id == project.project_id,
                    TaskAssignee.p_members_id == pm.p_members_id,
                )
                .count()
                > 0
            )
            if used_in_task_tbl or used_in_assignees:
                u = User.query.filter_by(member_id=pm.member_id).first()
                could_not_remove.append(u.name or u.username if u else str(pm.member_id))
            else:
                db.session.delete(pm)

        db.session.flush()

        # Add new members (selected but not already in project)
        existing_member_ids = {pm.member_id for pm in current_pms}
        for member_id_int in selected_member_ids:
            if member_id_int in existing_member_ids:
                continue
            user = User.query.get(member_id_int)
            if user:
                pm = ProjectMembers(
                    project_id=project.project_id,
                    member_id=member_id_int,
                    role='Team Member'
                )
                db.session.add(pm)

        db.session.commit()
        if could_not_remove:
            flash(
                'Project members updated. Could not remove: {} (still assigned to tasks).'.format(
                    ', '.join(could_not_remove)
                ),
                'warning',
            )
        else:
            flash('Project members updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update: {}'.format(str(e)), 'danger')
    return redirect(url_for('project.project_details', id=id))

@project_bp.route("/project_details/<int:id>/update", methods=['POST'])
@login_required
def update_project(id):
    project = Project.query.get_or_404(id)
    if current_user.member_id != project.project_manager:
        flash('Only the project manager can perform this action.', 'danger')
        return redirect(url_for('project.projects'))
    project_name = request.form.get('project_name', '').strip()
    if not project_name:
        flash('Project name is required', 'danger')
        return redirect(url_for('project.project_details', id=id))
    try:
        project.project_name = project_name
        project.priority = request.form.get('priority') or project.priority
        project.project_status = request.form.get('project_status') or project.project_status
        project.client_name = request.form.get('client_name') or None
        start_str = request.form.get('start_date')
        end_str = request.form.get('end_date')
        if start_str and end_str:
            start_date = datetime.strptime(start_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_str, '%Y-%m-%d')
            if end_date < start_date:
                flash('Deadline cannot be earlier than the start date.', 'danger')
                return redirect(url_for('project.project_details', id=id))
            if project.deadlines_id:
                dl = Deadlines.query.get(project.deadlines_id)
                if dl:
                    dl.start_date = start_date
                    dl.end_date = end_date
            else:
                dl = Deadlines(start_date=start_date, end_date=end_date)
                db.session.add(dl)
                db.session.flush()
                project.deadlines_id = dl.deadlines_id
        db.session.commit()
        flash('Project updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update: {}'.format(str(e)), 'danger')
    return redirect(url_for('project.project_details', id=id))

@project_bp.route("/project_details/<int:id>/update_description", methods=['POST'])
@login_required
def update_project_description(id):
    project = Project.query.get_or_404(id)
    if current_user.member_id != project.project_manager:
        flash('Only the project manager can perform this action.', 'danger')
        return redirect(url_for('project.projects'))
    project_desc = request.form.get('project_desc', '').strip() or None
    try:
        project.project_desc = project_desc
        db.session.commit()
        flash('Description updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update: {}'.format(str(e)), 'danger')
    return redirect(url_for('project.project_details', id=id))

@project_bp.route("/project_details/<int:id>/delete", methods=['GET', 'POST'])
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
    if current_user.member_id != project.project_manager:
        flash('Only the project manager can perform this action.', 'danger')
        return redirect(url_for('project.projects'))
    try:
        ProjectMembers.query.filter_by(project_id=project.project_id).delete()
        tasks = Task.query.filter_by(project_id=project.project_id).all()
        for task in tasks:
            SubTask.query.filter_by(parent_task_id=task.task_id).delete()
        Task.query.filter_by(project_id=project.project_id).delete()
        deadlines_id = project.deadlines_id
        db.session.delete(project)
        if deadlines_id:
            dl = Deadlines.query.get(deadlines_id)
            if dl:
                db.session.delete(dl)
        db.session.commit()
        flash('Project deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete project: {}'.format(str(e)), 'danger')
    return redirect(url_for('project.projects'))

@project_bp.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@project_bp.route("/task_details")
@project_bp.route("/task_details/<int:id>")
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
    can_edit_task_flag = _can_edit_task(task, current_user)
    
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
    
    return render_template('task_details.html', task=task, project=project, task_assignees=task_assignees, task_project_members=task_project_members, assignee_p_members_ids=assignee_p_members_ids, is_project_manager=is_project_manager, is_project_member=is_project_member, can_edit_task=can_edit_task_flag)

@project_bp.route("/task_details/<int:id>/update", methods=['POST'])
@login_required
def update_task(id):
    task = Task.query.get_or_404(id)
    
    # Check permissions - only project manager or assigned member can edit
    if not _can_edit_task(task, current_user):
        flash('You do not have permission to edit this task. Only the project manager or assigned member can edit it.', 'danger')
        return redirect(url_for('project.task_details', id=id))
    
    task_name = request.form.get('task_name', '').strip()
    if not task_name:
        flash('Task name is required.', 'danger')
        return redirect(url_for('project.task_details', id=id))
    task.task_name = task_name
    task.priority = request.form.get('priority') or task.priority
    task.task_status = request.form.get('task_status') or 'Ongoing'
    task.task_description = request.form.get('task_description', '').strip() or None

    # Update assigned members (multiple allowed)
    owner_ids = request.form.getlist('owner_id')  # p_members_id or member_id
    if owner_ids:
        try:
            # Resolve to p_members_id list (form may send p_members_id or member_id)
            p_members_ids = []
            for oid in owner_ids:
                try:
                    oid_int = int(oid)
                    pm = ProjectMembers.query.filter_by(project_id=task.project_id).filter(
                        (ProjectMembers.p_members_id == oid_int) | (ProjectMembers.member_id == oid_int)
                    ).first()
                    if pm and pm.p_members_id not in p_members_ids:
                        p_members_ids.append(pm.p_members_id)
                except (ValueError, TypeError):
                    continue
            if p_members_ids:
                task.p_members_id = p_members_ids[0]
                try:
                    TaskAssignee.query.filter_by(task_id=task.task_id).delete()
                    db.session.flush()
                    for pid in p_members_ids:
                        ta = TaskAssignee(task_id=task.task_id, p_members_id=pid)
                        db.session.add(ta)
                except (ProgrammingError, OperationalError):
                    pass
        except (ValueError, TypeError):
            pass

    start_date_str = request.form.get('start_date', '').strip()
    end_date_str = request.form.get('end_date', '').strip()
    if start_date_str and end_date_str:
        try:
            start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
            if end_dt < start_dt:
                flash('End date cannot be before start date.', 'danger')
                return redirect(url_for('project.task_details', id=id))
            if task.deadline_id:
                deadline = Deadlines.query.get(task.deadline_id)
                if deadline:
                    deadline.start_date = start_dt
                    deadline.end_date = end_dt
                else:
                    deadline = Deadlines(start_date=start_dt, end_date=end_dt, flag='active')
                    db.session.add(deadline)
                    db.session.flush()
                    task.deadline_id = deadline.deadlines_id
            else:
                deadline = Deadlines(start_date=start_dt, end_date=end_dt, flag='active')
                db.session.add(deadline)
                db.session.flush()
                task.deadline_id = deadline.deadlines_id
        except ValueError:
            pass
    elif not start_date_str and not end_date_str:
        task.deadline_id = None

    try:
        db.session.commit()
        flash('Task updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update task: {}'.format(str(e)), 'danger')
    return redirect(url_for('project.task_details', id=id))

@project_bp.route("/task_details/<int:id>/delete", methods=['POST'])
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    
    # Only project manager can delete tasks
    project = Project.query.get(task.project_id) if task.project_id else None
    if not project or current_user.member_id != project.project_manager:
        flash('Only the project manager can delete tasks.', 'danger')
        return redirect(url_for('project.task_details', id=id))
    
    project_id = task.project_id
    task_id = task.task_id
    try:
        try:
            TaskAssignee.query.filter_by(task_id=task_id).delete()
        except Exception:
            pass  # task_assignees table may not exist
        SubTask.query.filter_by(parent_task_id=task_id).delete()
        db.session.delete(task)
        db.session.commit()
        flash('Task deleted successfully.', 'success')
    except (ProgrammingError, OperationalError) as e:
        # task_assignees table may not exist; db.session.delete(task) loads assignees and fails
        if 'task_assignees' in str(e) or '1146' in str(e):
            db.session.rollback()
            try:
                SubTask.query.filter_by(parent_task_id=task_id).delete()
                db.session.execute(text('DELETE FROM task_tbl WHERE task_id = :id'), {'id': task_id})
                db.session.commit()
                flash('Task deleted successfully.', 'success')
            except Exception as e2:
                db.session.rollback()
                flash('Failed to delete task: {}'.format(str(e2)), 'danger')
        else:
            db.session.rollback()
            flash('Failed to delete task: {}'.format(str(e)), 'danger')
    except Exception as e:
        db.session.rollback()
        flash('Failed to delete task: {}'.format(str(e)), 'danger')
    return redirect(url_for('project.project_details', id=project_id))

@project_bp.route("/task/<int:task_id>/mark_complete", methods=['POST'])
@login_required
def mark_task_complete(task_id):
    """Mark a task as completed - only project manager or assigned member can do this"""
    try:
        task = Task.query.get_or_404(task_id)
        
        # Check permissions
        if not _can_edit_task(task, current_user):
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'error': 'You do not have permission to mark this task as complete. Only the project manager or assigned member can do this.'}), 403
            flash('You do not have permission to mark this task as complete. Only the project manager or assigned member can do this.', 'danger')
            return redirect(url_for('project.task_details', id=task_id))
        
        # Update task status to Completed
        task.task_status = 'Completed'
        db.session.commit()
        
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': 'Task marked as completed',
                'task_id': task.task_id,
                'task_status': task.task_status
            })
        
        flash('Task marked as completed', 'success')
        return redirect(url_for('project.task_details', id=task_id))
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('project.task_details', id=task_id))

@project_bp.route("/project_details/<int:id>/task/create", methods=['POST'])
@login_required
def create_task(id):
    project = Project.query.get_or_404(id)
    if current_user.member_id != project.project_manager:
        flash('Only the project manager can create tasks.', 'danger')
        return redirect(url_for('project.projects'))
    try:
        # Get form data - support multiple assignees (owner_id can be multiple)
        task_name = request.form.get('task_name')
        owner_ids = request.form.getlist('owner_id')  # list of member_ids
        task_description = request.form.get('task_description', '')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        
        # Validate required fields - at least one assignee
        if not task_name or not owner_ids:
            flash('Please fill in task name and assign at least one member.', 'danger')
            return redirect(url_for('project.project_details', id=id))
        
        # Resolve each owner (member_id) to project_member; collect valid p_members_id
        project_member_ids = []
        for mid in owner_ids:
            try:
                pm = ProjectMembers.query.filter_by(
                    project_id=project.project_id,
                    member_id=int(mid)
                ).first()
                if pm and pm.p_members_id not in project_member_ids:
                    project_member_ids.append(pm.p_members_id)
            except (ValueError, TypeError):
                continue
        if not project_member_ids:
            flash('Selected members must be assigned to this project.', 'danger')
            return redirect(url_for('project.project_details', id=id))
        
        # First assignee for legacy single-owner field
        project_member = ProjectMembers.query.get(project_member_ids[0])
        
        # Optional: create a deadline in deadlines_tbl and get FK for task
        deadline_id = None
        if start_date_str and end_date_str:
            try:
                start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
                if end_dt < start_dt:
                    flash('End date cannot be before start date.', 'danger')
                    return redirect(url_for('project.project_details', id=id))
                deadline = Deadlines(start_date=start_dt, end_date=end_dt, flag='active')
                db.session.add(deadline)
                db.session.flush()
                deadline_id = deadline.deadlines_id
            except ValueError:
                pass
        
        # Create the task (with unique generated code TK####; deadline_id links to deadlines_tbl)
        task = Task(
            project_id=project.project_id,
            p_members_id=project_member.p_members_id,
            task_name=task_name,
            task_description=task_description.strip() if task_description else None,
            task_status='Ongoing',
            priority='Medium',
            generated_code=_generate_task_code(),
            deadline_id=deadline_id
        )
        
        db.session.add(task)
        db.session.flush()  # get task.task_id
        
        # Add all assignees to task_assignees
        try:
            for p_members_id in project_member_ids:
                ta = TaskAssignee(task_id=task.task_id, p_members_id=p_members_id)
                db.session.add(ta)
        except (ProgrammingError, OperationalError):
            pass
        
        db.session.commit()
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('project.project_details', id=id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating task: {str(e)}', 'danger')
        return redirect(url_for('project.project_details', id=id))

@project_bp.route("/project/create", methods=['POST'])
@login_required
def create_project():
    try:
        # Get form data
        project_name = request.form.get('project_name')
        priority = request.form.get('priority', 'High')
        client_name = request.form.get('client_name')
        # Project manager is automatically set to the current user
        project_manager = current_user.member_id
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        # New projects default to Ongoing (not shown in UI)
        project_status = 'Ongoing'
        progress = request.form.get('progress', '0%')
        project_description = request.form.get('topicDescription', '')
        member_ids = request.form.getlist('project_members')
        
        # Validate required fields (department removed; at least one member required)
        if not all([project_name, priority, client_name, start_date_str, end_date_str]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('project.projects'))
        if not member_ids:
            flash('Please select at least one member for the project', 'danger')
            return redirect(url_for('project.projects'))
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('project.projects'))
        if end_date < start_date:
            flash('Deadline cannot be earlier than the start date.', 'danger')
            return redirect(url_for('project.projects'))

        # Derive department from first selected member, else current user's department
        department_id = None
        try:
            first_member_id = int(member_ids[0])
            first_user = User.query.get(first_member_id)
            if first_user and first_user.department_id:
                department_id = first_user.department_id
        except (ValueError, TypeError, IndexError):
            pass
        if department_id is None and current_user.department_id:
            department_id = current_user.department_id

        # Create deadline entry first
        deadline = Deadlines(
            start_date=start_date,
            end_date=end_date,
            flag='active'
        )
        db.session.add(deadline)
        db.session.flush()  # Get the deadlines_id
        
        # Create project entry
        project = Project(
            department_id=department_id,
            project_manager=int(project_manager),
            deadlines_id=deadline.deadlines_id,
            priority=priority,
            project_name=project_name,
            client_name=client_name,
            project_status=project_status,
            progress=progress,
            project_desc=project_description
        )
        
        db.session.add(project)
        db.session.flush()  # Get the project_id
        
        # Create ProjectMembers entries: always add project manager, then selected members
        member_ids_set = {int(m) for m in member_ids if m and str(m).isdigit()}
        # Ensure project manager is a project member (so they can be assigned tasks)
        if project_manager not in member_ids_set:
            existing_pm = ProjectMembers.query.filter_by(
                project_id=project.project_id,
                member_id=int(project_manager)
            ).first()
            if not existing_pm:
                db.session.add(ProjectMembers(
                    project_id=project.project_id,
                    member_id=int(project_manager),
                    role='Project Manager',
                    generated_code=str(project.project_id)
                ))
                db.session.flush()
        for member_id in member_ids:
            try:
                member_id_int = int(member_id)
                existing = ProjectMembers.query.filter_by(
                    member_id=member_id_int,
                    project_id=project.project_id
                ).first()
                if not existing:
                    db.session.add(ProjectMembers(
                        project_id=project.project_id,
                        member_id=member_id_int,
                        role='Team Member',
                        generated_code=str(project.project_id)
                    ))
            except (ValueError, TypeError):
                continue
        
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('project.projects'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating project: {str(e)}', 'danger')
        return redirect(url_for('project.projects'))

@project_bp.route("/approvals")
def approvals():
    return render_template('approvals.html', title="Approvals")


# @project_bp.route("/task_details/<int:task_id>")
# @login_required
# def task_details(task_id):
#     # 1. Fetch the task
#     task = Task.query.get_or_404(task_id)
    
#     # 2. Fetch all notes (Now that parent_id is gone from models.py, this won't crash!)
#     all_notes = Notes.query.filter_by(task_id=task_id).order_by(Notes.created_on.asc()).all()
    
#     # --- PASTE THE LOGIC HERE ---
    
#     # Separate main notes from replies
#     main_notes = [n for n in all_notes if not n.reply_code]

#     # Group replies by the ID stored in reply_code
#     replies_map = {}
#     for n in all_notes:
#         if n.reply_code:
#             try:
#                 parent_id = int(n.reply_code)
#                 if parent_id not in replies_map:
#                     replies_map[parent_id] = []
#                 replies_map[parent_id].append(n)
#             except (ValueError, TypeError):
#                 continue # Skip if reply_code isn't a valid number
                
#     # --- END OF LOGIC ---

#     # 3. Pass everything to the template
#     return render_template('task_details.html', 
#                            task=task, 
#                            notes=main_notes, 
#                            replies_map=replies_map)