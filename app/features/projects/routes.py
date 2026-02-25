from flask import render_template, Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Department, User, Project, Deadlines, ProjectMembers, Task, TaskAssignee, SubTask, Notes, Report, ReportCC, Comment
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

@project_bp.route("/department_projects") 
@login_required
def department_projects():
    # Fetch all projects with related data (newest first)
    projects = Project.query.order_by(Project.project_id.desc()).all()
    departments = Department.query.all()
    users = User.query.all()

    # Bulk lookups to avoid N+1
    dept_by_id = {d.department_id: d for d in departments}
    user_by_id = {u.member_id: u for u in users}
    deadline_ids = list({p.deadlines_id for p in projects if p.deadlines_id})
    deadlines_list = Deadlines.query.filter(Deadlines.deadlines_id.in_(deadline_ids)).all() if deadline_ids else []
    deadline_by_id = {d.deadlines_id: d for d in deadlines_list}

    # One query: all tasks for these projects (for progress + latest task)
    project_ids = [p.project_id for p in projects]
    tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    from collections import defaultdict
    task_total_by_project = defaultdict(int)
    task_completed_by_project = defaultdict(int)
    latest_task_by_project = {}
    for t in tasks:
        task_total_by_project[t.project_id] += 1
        if t.task_status == 'Completed':
            task_completed_by_project[t.project_id] += 1
        if t.project_id not in latest_task_by_project or t.task_id > latest_task_by_project[t.project_id][0]:
            latest_task_by_project[t.project_id] = (t.task_id, t.task_name)

    # Prepare projects data for template (no per-row queries)
    projects_data = []
    for project in projects:
        manager = user_by_id.get(project.project_manager) if project.project_manager else None
        department = dept_by_id.get(project.department_id) if project.department_id else None
        deadline = deadline_by_id.get(project.deadlines_id) if project.deadlines_id else None

        try:
            priority_raw = project.priority
            priority = str(priority_raw) if priority_raw else 'High'
        except (AttributeError, KeyError):
            priority = 'High'

        task_total = task_total_by_project.get(project.project_id, 0)
        task_completed = task_completed_by_project.get(project.project_id, 0)
        progress_pct = round(task_completed / task_total * 100, 1) if task_total else 0
        latest_tuple = latest_task_by_project.get(project.project_id)
        latest_task_title = latest_tuple[1] if latest_tuple else None

        projects_data.append({
            'project': project,
            'manager': manager,
            'department': department,
            'deadline': deadline,
            'priority': priority,
            'progress_pct': progress_pct,
            'latest_task_title': latest_task_title,
        })

    # Calculate statistics from projects
    high_priority_count = 0
    for item in projects_data:
        try:
            priority_val = item['priority']
            if priority_val and priority_val.lower() == 'high':
                high_priority_count += 1
        except (AttributeError, KeyError):
            pass

    stats = {
        'pending': len([p for p in projects if p.project_status and p.project_status.lower() == 'pending']),
        'high_priority': high_priority_count,
        'completed': len([p for p in projects if p.project_status and p.project_status.lower() == 'completed']),
        'on_hold': len([p for p in projects if p.project_status and p.project_status.lower() == 'on hold'])
    }

    users_json = [
        {
            'member_id': user.member_id,
            'name': user.name or user.username,
            'username': user.username,
            'department_id': user.department_id
        }
        for user in users
    ]

    return render_template('department.html', title="Department Projects", projects_data=projects_data, departments=departments, users_json=users_json, stats=stats, today=date.today())

@project_bp.route("/")
@project_bp.route("/projects") 
# @cache.cached(timeout=60)
@login_required
def projects():
  # Project IDs where current user is a member (participant)
    member_project_ids = ProjectMembers.query.filter(
        ProjectMembers.member_id == current_user.member_id
    ).with_entities(ProjectMembers.project_id)

    # Only projects where user is manager or a project member
    projects = Project.query.filter(
        or_(
            Project.project_manager == current_user.member_id,
            Project.project_id.in_(member_project_ids)
        )
    ).order_by(Project.project_id.desc()).all()

    departments = Department.query.all()
    users = User.query.all()

    # Bulk lookups to avoid N+1
    dept_by_id = {d.department_id: d for d in departments}
    user_by_id = {u.member_id: u for u in users}
    deadline_ids = list({p.deadlines_id for p in projects if p.deadlines_id})
    deadlines_list = Deadlines.query.filter(Deadlines.deadlines_id.in_(deadline_ids)).all() if deadline_ids else []
    deadline_by_id = {d.deadlines_id: d for d in deadlines_list}

    # One query: all tasks for these projects (for progress + latest task)
    project_ids = [p.project_id for p in projects]
    tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    from collections import defaultdict
    task_total_by_project = defaultdict(int)
    task_completed_by_project = defaultdict(int)
    latest_task_by_project = {}
    for t in tasks:
        task_total_by_project[t.project_id] += 1
        if t.task_status == 'Completed':
            task_completed_by_project[t.project_id] += 1
        if t.project_id not in latest_task_by_project or t.task_id > latest_task_by_project[t.project_id][0]:
            latest_task_by_project[t.project_id] = (t.task_id, t.task_name)

    # Prepare projects data for template (no per-row queries)
    projects_data = []
    for project in projects:
        manager = user_by_id.get(project.project_manager) if project.project_manager else None
        deadline = deadline_by_id.get(project.deadlines_id) if project.deadlines_id else None

        try:
            priority_raw = project.priority
            priority = str(priority_raw) if priority_raw else 'High'
        except (AttributeError, KeyError):
            priority = 'High'

        task_total = task_total_by_project.get(project.project_id, 0)
        task_completed = task_completed_by_project.get(project.project_id, 0)
        progress_pct = round(task_completed / task_total * 100, 1) if task_total else 0
        latest_tuple = latest_task_by_project.get(project.project_id)
        latest_task_title = latest_tuple[1] if latest_tuple else None

        projects_data.append({
            'project': project,
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
    
    return render_template('index.html', title="My Projects", projects_data=projects_data, users=users, users_json=users_json, stats=stats, today=date.today())

@project_bp.route("/all_projects") 
@login_required
def all_projects():
    # Fetch all projects with related data (newest first)
    projects = Project.query.order_by(Project.project_id.desc()).all()
    users = User.query.all()

    # Bulk lookups to avoid N+1
    departments = Department.query.all()
    dept_by_id = {d.department_id: d for d in departments}
    user_by_id = {u.member_id: u for u in users}
    deadline_ids = list({p.deadlines_id for p in projects if p.deadlines_id})
    deadlines_list = Deadlines.query.filter(Deadlines.deadlines_id.in_(deadline_ids)).all() if deadline_ids else []
    deadline_by_id = {d.deadlines_id: d for d in deadlines_list}

    # One query: all tasks for these projects (for progress + latest task)
    project_ids = [p.project_id for p in projects]
    tasks = Task.query.filter(Task.project_id.in_(project_ids)).all() if project_ids else []
    from collections import defaultdict
    task_total_by_project = defaultdict(int)
    task_completed_by_project = defaultdict(int)
    latest_task_by_project = {}
    for t in tasks:
        task_total_by_project[t.project_id] += 1
        if t.task_status == 'Completed':
            task_completed_by_project[t.project_id] += 1
        if t.project_id not in latest_task_by_project or t.task_id > latest_task_by_project[t.project_id][0]:
            latest_task_by_project[t.project_id] = (t.task_id, t.task_name)

    # Prepare projects data for template (no per-row queries)
    projects_data = []
    for project in projects:
        dept = dept_by_id.get(project.department_id) if project.department_id else None
        manager = user_by_id.get(project.project_manager) if project.project_manager else None
        deadline = deadline_by_id.get(project.deadlines_id) if project.deadlines_id else None

        try:
            priority_raw = project.priority
            priority = str(priority_raw) if priority_raw else 'High'
        except (AttributeError, KeyError):
            priority = 'High'

        task_total = task_total_by_project.get(project.project_id, 0)
        task_completed = task_completed_by_project.get(project.project_id, 0)
        progress_pct = round(task_completed / task_total * 100, 1) if task_total else 0
        latest_tuple = latest_task_by_project.get(project.project_id)
        latest_task_title = latest_tuple[1] if latest_tuple else None

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
    high_priority_count = 0
    for item in projects_data:
        try:
            priority_val = item['priority']
            if priority_val and priority_val.lower() == 'high':
                high_priority_count += 1
        except (AttributeError, KeyError):
            pass

    stats = {
        'pending': len([p for p in projects if p.project_status and p.project_status.lower() == 'pending']),
        'high_priority': high_priority_count,
        'completed': len([p for p in projects if p.project_status and p.project_status.lower() == 'completed']),
        'on_hold': len([p for p in projects if p.project_status and p.project_status.lower() == 'on hold'])
    }

    users_json = [
        {
            'member_id': user.member_id,
            'name': user.name or user.username,
            'username': user.username,
            'department_id': user.department_id
        }
        for user in users
    ]

    return render_template('all_projects.html', title="All Projects", projects_data=projects_data, users=users, users_json=users_json, stats=stats, today=date.today())

#My Tasks
@project_bp.route("/my_tasks")
@login_required
def my_tasks():
    # My ProjectMembers rows (I'm in these projects)
    my_pm_rows = ProjectMembers.query.filter_by(member_id=current_user.member_id).all()
    my_p_members_ids = [pm.p_members_id for pm in my_pm_rows]

    if not my_p_members_ids:
        return render_template('my_task.html', title="My Tasks", tasks_data=[], today=date.today())

    # Task IDs where I'm an assignee (TaskAssignee table)
    task_ids_from_assignees = TaskAssignee.query.filter(
        TaskAssignee.p_members_id.in_(my_p_members_ids)
    ).with_entities(TaskAssignee.task_id).distinct()

    # All tasks assigned to me: via assignees OR legacy single p_members_id
    tasks = Task.query.filter(
        or_(
            Task.task_id.in_(task_ids_from_assignees),
            Task.p_members_id.in_(my_p_members_ids)
        )
    ).order_by(Task.task_id.desc()).all()

    if not tasks:
        return render_template('my_task.html', title="My Tasks", tasks_data=[], today=date.today())

    # Bulk lookups to avoid N+1
    project_ids = list({t.project_id for t in tasks if t.project_id})
    projects = Project.query.filter(Project.project_id.in_(project_ids)).all()
    project_by_id = {p.project_id: p for p in projects}

    user_ids = list({p.project_manager for p in projects if p.project_manager})
    users = User.query.filter(User.member_id.in_(user_ids)).all()
    user_by_id = {u.member_id: u for u in users}

    deadline_ids = list({t.deadline_id for t in tasks if t.deadline_id})
    deadlines_list = Deadlines.query.filter(Deadlines.deadlines_id.in_(deadline_ids)).all() if deadline_ids else []
    deadline_by_id = {d.deadlines_id: d for d in deadlines_list}

    task_ids = [t.task_id for t in tasks]
    subtasks = SubTask.query.filter(SubTask.parent_task_id.in_(task_ids)).all()
    from collections import defaultdict
    subtasks_by_task = defaultdict(list)
    for s in subtasks:
        subtasks_by_task[s.parent_task_id].append(s)

    # Build list for template (no per-row queries)
    tasks_data = []
    for task in tasks:
        project = project_by_id.get(task.project_id) if task.project_id else None
        manager = user_by_id.get(project.project_manager) if project and project.project_manager else None
        deadline = deadline_by_id.get(task.deadline_id) if task.deadline_id else None
        st_list = subtasks_by_task.get(task.task_id, [])
        st_total = len(st_list)
        st_done = sum(1 for s in st_list if s.is_checked)
        progress_pct = f"{st_done}/{st_total}" if st_total > 0 else "0/0"
        # progress_pct = round(st_done / st_total * 100, 1) if st_total else 0
        tasks_data.append({
            'task': task,
            'project': project,
            'manager': manager,
            'deadline': deadline,
            'progress_pct': progress_pct,
            'sub_total': st_total,
        })

    return render_template('my_task.html', title="My Tasks", tasks_data=tasks_data, today=date.today())

#Department-Wide Tasks
@project_bp.route("/dept_tasks")
@login_required
def dept_tasks():
    # All tasks from all projects (no department filter)
    tasks = Task.query.order_by(Task.task_id.desc()).all()
    # if not current_user.department_id:
    #     tasks = []
    # else:
    #         project_ids = [
    #             p.project_id
    #             for p in Project.query.filter_by(department_id=current_user.department_id).all()
    #         ]
    #         tasks = (
    #             Task.query.filter(Task.project_id.in_(project_ids))
    #             .order_by(Task.task_id.desc())
    #             .all()
    #         ) if project_ids else []

    if not tasks:
        users = User.query.all()
        departments = Department.query.all()
        stats = {'pending': 0, 'high_priority': 0, 'completed': 0, 'on_hold': 0}
        users_json = [
            {'member_id': u.member_id, 'name': u.name or u.username, 'username': u.username, 'department_id': u.department_id}
            for u in users
        ]
        return render_template('dept_task.html', title="Tasks Info", tasks_data=[], stats=stats, users_json=users_json, departments=departments, today=date.today())

    # Bulk lookups to avoid N+1
    project_ids = list({t.project_id for t in tasks if t.project_id})
    projects = Project.query.filter(Project.project_id.in_(project_ids)).all()
    project_by_id = {p.project_id: p for p in projects}

    user_ids = list({p.project_manager for p in projects if p.project_manager})
    users = User.query.all()
    user_by_id = {u.member_id: u for u in users}

    deadline_ids = list({t.deadline_id for t in tasks if t.deadline_id})
    deadlines_list = Deadlines.query.filter(Deadlines.deadlines_id.in_(deadline_ids)).all() if deadline_ids else []
    deadline_by_id = {d.deadlines_id: d for d in deadlines_list}

    department_ids = list({p.department_id for p in projects if p.department_id})
    departments = Department.query.all()
    dept_by_id = {d.department_id: d for d in departments}

    task_ids = [t.task_id for t in tasks]
    subtasks = SubTask.query.filter(SubTask.parent_task_id.in_(task_ids)).all()
    from collections import defaultdict
    subtasks_by_task = defaultdict(list)
    for s in subtasks:
        subtasks_by_task[s.parent_task_id].append(s)

    # Build list for template (no per-row queries)
    tasks_data = []
    for task in tasks:
        project = project_by_id.get(task.project_id) if task.project_id else None
        manager = user_by_id.get(project.project_manager) if project and project.project_manager else None
        deadline = deadline_by_id.get(task.deadline_id) if task.deadline_id else None
        department = dept_by_id.get(project.department_id) if project and project.department_id else None
        st_list = subtasks_by_task.get(task.task_id, [])
        st_total = len(st_list)
        st_done = sum(1 for s in st_list if s.is_checked)
        progress_pct = f"{st_done}/{st_total}" if st_total > 0 else "0/0"
        tasks_data.append({
            'task': task,
            'project': project,
            'department': department,
            'manager': manager,
            'deadline': deadline,
            'progress_pct': progress_pct,
            'sub_total': st_total,
        })

    # Calculate statistics from tasks
    stats = {
        'pending': len([t for t in tasks if (t.task_status or '').lower() in ('pending', 'ongoing', '') or not t.task_status]),
        'high_priority': len([t for t in tasks if (t.priority or '').lower() == 'high']),
        'completed': len([t for t in tasks if (t.task_status or '').lower() == 'completed']),
        'on_hold': len([t for t in tasks if (t.task_status or '').lower() == 'on hold'])
    }

    users_json = [
        {'member_id': u.member_id, 'name': u.name or u.username, 'username': u.username, 'department_id': u.department_id}
        for u in users
    ]

    return render_template('dept_task.html', title="Department Tasks", tasks_data=tasks_data, stats=stats, users_json=users_json, departments=departments, today=date.today())
    
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
    # Department for display: project manager's department, or project's department as fallback
    manager_department = Department.query.get(manager.department_id) if manager and manager.department_id else department

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
            # Completed = status == 'Approved' (canonical); is_checked kept for legacy
            subtasks = SubTask.query.filter_by(parent_task_id=task.task_id).all()
            total_subtasks = len(subtasks)
            completed_subtasks = len([st for st in subtasks if st.status == 'Approved' or st.is_checked])
            progress = f"{completed_subtasks}/{total_subtasks}" if total_subtasks > 0 else "0/0"

            # Use actual task status (no auto-complete from subtasks; Mark Complete button is explicit)
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
                         manager_department=manager_department,
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
    
    # MODIFIED: Changed .asc() to .desc() to show newest notes first
    all_notes = Notes.query.filter_by(task_id=task.task_id).order_by(
        Notes.pin_stat.desc(), 
        Notes.created_on.desc()
    ).all()
    
    main_notes = [n for n in all_notes if not n.reply_code]

    replies_map = {}
    for n in all_notes:
        if n.reply_code:
            try:
                parent_id = int(n.reply_code)
                if parent_id not in replies_map:
                    replies_map[parent_id] = []
                
                # Keep replies in chronological order (Oldest at top of thread)
                # Since all_notes is descending, we insert at the end to keep them 0, 1, 2...
                replies_map[parent_id].append(n) 
            except (ValueError, TypeError):
                pass
    
    # Assignees for this task
    task_assignees = []
    try:
        if task.assignees:
            for ta in task.assignees:
                if ta.project_member and ta.project_member.member_id:
                    u = User.query.get(ta.project_member.member_id)
                    if u:
                        task_assignees.append(u)
    except (Exception):
        pass 
        
    if not task_assignees and task.p_members_id:
        pm = ProjectMembers.query.get(task.p_members_id)
        if pm and pm.member_id:
            u = User.query.get(pm.member_id)
            if u:
                task_assignees.append(u)
    
    # Project members logic
    task_project_members = []
    if task.project_id:
        project = Project.query.get(task.project_id)
        pms = ProjectMembers.query.filter_by(project_id=task.project_id).all()
        for pm in pms:
            if pm.member_id:
                u = User.query.get(pm.member_id)
                if u:
                    task_project_members.append({'p_members_id': pm.p_members_id, 'name': u.name or u.username})
        
        if project and project.project_manager:
            pm_member_ids = [pm.member_id for pm in pms if pm.member_id]
            if project.project_manager not in pm_member_ids:
                manager_user = User.query.get(project.project_manager)
                if manager_user:
                    pm_row = ProjectMembers.query.filter_by(project_id=task.project_id, member_id=project.project_manager).first()
                    if not pm_row:
                        pm_row = ProjectMembers(project_id=task.project_id, member_id=project.project_manager, role='Project Manager')
                        db.session.add(pm_row)
                        try:
                            db.session.commit()
                        except Exception:
                            db.session.rollback()
                            pm_row = ProjectMembers.query.filter_by(project_id=task.project_id, member_id=project.project_manager).first()
                    if pm_row:
                        task_project_members.append({'p_members_id': pm_row.p_members_id, 'name': manager_user.name or manager_user.username})
    
    # Role flags
    project = Project.query.get(task.project_id) if task.project_id else None
    is_project_manager = (project and current_user.member_id == project.project_manager)
    is_project_member = False
    if project:
        if is_project_manager:
            is_project_member = True
        else:
            pm_entry = ProjectMembers.query.filter_by(project_id=task.project_id, member_id=current_user.member_id).first()
            is_project_member = pm_entry is not None
    # Assigned to this task (via TaskAssignee or task.p_members_id) – required to see member subtask view
    is_assigned_to_task = False
    if task_assignees:
        for u in task_assignees:
            if u.member_id == current_user.member_id:
                is_assigned_to_task = True
                break
    if not is_assigned_to_task and task.p_members_id:
        pm_owner = ProjectMembers.query.get(task.p_members_id)
        if pm_owner and pm_owner.member_id == current_user.member_id:
            is_assigned_to_task = True
    # Show member subtask block only if project member AND assigned to this task (PM always sees PM block)
    can_see_member_subtask = is_project_member and not is_project_manager and is_assigned_to_task

    # Check if user can edit/mark complete this task
    can_edit_task = _can_edit_task(task, current_user)
    
    # p_members_id of current assignees
    assignee_p_members_ids = []
    try:
        if task.assignees:
            for ta in task.assignees:
                if ta.project_member:
                    assignee_p_members_ids.append(ta.project_member.p_members_id)
    except (Exception):
        pass
    if not assignee_p_members_ids and task.p_members_id:
        assignee_p_members_ids.append(task.p_members_id)

    # Department for display: project manager's department, or project's department as fallback
    manager_user = User.query.get(project.project_manager) if project and project.project_manager else None
    manager_department = None
    if manager_user and manager_user.department_id:
        manager_department = Department.query.get(manager_user.department_id)
    elif project and project.department_id:
        manager_department = Department.query.get(project.department_id)

    # Build subtask_list for template (SubTask with owner_name, notes_preview)
    from collections import defaultdict
    subtasks = SubTask.query.filter_by(parent_task_id=task.task_id).all()
    p_member_ids = list({s.p_members_id for s in subtasks if s.p_members_id})
    pm_to_user = {}
    if p_member_ids:
        for pm in ProjectMembers.query.filter(ProjectMembers.p_members_id.in_(p_member_ids)).all():
            if pm.member_id:
                u = User.query.get(pm.member_id)
                if u:
                    pm_to_user[pm.p_members_id] = u.name or u.username
    sub_note_ids = [s.sub_task_id for s in subtasks]
    notes_by_sub = defaultdict(list)
    if sub_note_ids:
        for n in Notes.query.filter(Notes.sub_task_id.in_(sub_note_ids)).order_by(Notes.created_on.desc()).all():
            notes_by_sub[n.sub_task_id].append(n.note_body or '')
    subtask_list = []
    for st in subtasks:
        owner_name = pm_to_user.get(st.p_members_id, '—') if st.p_members_id else '—'
        previews = notes_by_sub.get(st.sub_task_id, [])
        notes_preview = (previews[0][:80] + '…') if previews and previews[0] else '—'
        subtask_list.append(type('SubtaskRow', (), {
            'sub_task_id': st.sub_task_id, 'generated_code': st.generated_code or '—',
            'subtask_name': st.subtask_name or '—', 'owner_name': owner_name,
            'status': st.status or 'Ongoing', 'checked_timestamp': st.checked_timestamp,
            'notes_preview': notes_preview
        })())
    task_assignees_for_subtask = [m for m in task_project_members if m['p_members_id'] in assignee_p_members_ids]

    # Current user's p_members_id (for member-owned subtask actions: Resume, Edit on On Hold)
    current_user_pm = ProjectMembers.query.filter_by(
        project_id=task.project_id, member_id=current_user.member_id
    ).first() if task.project_id else None
    current_user_p_members_id = current_user_pm.p_members_id if current_user_pm else None

    subtask_list = []
    for st in subtasks:
        owner_name = pm_to_user.get(st.p_members_id, '—') if st.p_members_id else '—'
        previews = notes_by_sub.get(st.sub_task_id, [])
        notes_preview = (previews[0][:80] + '…') if previews and previews[0] else '—'
        is_owner = bool(st.p_members_id and current_user_p_members_id and st.p_members_id == current_user_p_members_id)
        subtask_list.append(type('SubtaskRow', (), {
            'sub_task_id': st.sub_task_id, 'generated_code': st.generated_code or '—',
            'subtask_name': st.subtask_name or '—', 'owner_name': owner_name,
            'status': st.status or 'Ongoing', 'checked_timestamp': st.checked_timestamp,
            'notes_preview': notes_preview, 'is_owner': is_owner
        })())

    return render_template('task_details.html',
        task=task,
        project=project,
        task_assignees=task_assignees,
        task_project_members=task_project_members,
        assignee_p_members_ids=assignee_p_members_ids,
        is_project_manager=is_project_manager,
        is_project_member=is_project_member,
        can_edit_task=can_edit_task,
        notes=main_notes,
        replies_map=replies_map,
        manager_department=manager_department,
        subtask_list=subtask_list,
        task_assignees_for_subtask=task_assignees_for_subtask,
    )


@project_bp.route("/task_details/<int:id>/create_subtask", methods=['POST'])
@login_required
def create_subtask(id):
    task = Task.query.get_or_404(id)
    project = Project.query.get(task.project_id) if task.project_id else None
    is_pm = bool(project and current_user.member_id == project.project_manager)
    is_member = False
    if project:
        is_member = is_pm or (ProjectMembers.query.filter_by(project_id=task.project_id, member_id=current_user.member_id).first() is not None)
    if not (is_pm or is_member):
        flash('Only project members can add subtasks.', 'danger')
        return redirect(url_for('project.task_details', id=id))

    assignee_p_members_ids = []
    try:
        for ta in (task.assignees or []):
            if ta.project_member:
                assignee_p_members_ids.append(ta.project_member.p_members_id)
    except (ProgrammingError, OperationalError):
        pass
    if not assignee_p_members_ids and task.p_members_id:
        assignee_p_members_ids.append(task.p_members_id)

    subtask_name = (request.form.get('subtask_name') or '').strip()
    if not subtask_name:
        flash('Sub-task name is required.', 'danger')
        return redirect(url_for('project.task_details', id=id))

    owner_p_members_id = request.form.get('owner')
    if owner_p_members_id:
        try:
            owner_p_members_id = int(owner_p_members_id)
            if owner_p_members_id not in assignee_p_members_ids:
                flash('Owner must be a member assigned to this task.', 'danger')
                return redirect(url_for('project.task_details', id=id))
        except (ValueError, TypeError):
            owner_p_members_id = None
    else:
        owner_p_members_id = None

    # New subtasks default to Ongoing (status field removed from form)
    status = 'Ongoing'

    count = SubTask.query.filter_by(parent_task_id=task.task_id).count()
    generated_code = f"ST{task.task_id}-{count + 1}"

    st = SubTask(
        parent_task_id=task.task_id,
        subtask_name=subtask_name,
        generated_code=generated_code,
        p_members_id=owner_p_members_id,
        status=status,
    )
    db.session.add(st)
    # If task was Completed, adding a subtask makes it Ongoing again
    if task.task_status == 'Completed':
        task.task_status = 'Ongoing'
    try:
        db.session.commit()
        flash('Sub-task created.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to create sub-task.', 'danger')
    return redirect(url_for('project.task_details', id=id))


def _can_act_on_subtask(subtask, task, current_user):
    """True if current user is PM of task's project or a project member (for member actions)."""
    if not task or not task.project_id:
        return False
    project = Project.query.get(task.project_id)
    if not project:
        return False
    if current_user.member_id == project.project_manager:
        return True
    pm_entry = ProjectMembers.query.filter_by(
        project_id=task.project_id,
        member_id=current_user.member_id
    ).first()
    return pm_entry is not None


@project_bp.route("/task_details/<int:task_id>/subtask/<int:sub_task_id>/status", methods=['POST'])
@login_required
def update_subtask_status(task_id, sub_task_id):
    task = Task.query.get_or_404(task_id)
    subtask = SubTask.query.filter_by(sub_task_id=sub_task_id, parent_task_id=task_id).first_or_404()
    if not _can_act_on_subtask(subtask, task, current_user):
        flash('You do not have permission to update this subtask.', 'danger')
        return redirect(url_for('project.task_details', id=task_id))
    status = (request.form.get('status') or '').strip()
    allowed = ('Ongoing', 'To be reviewed', 'Rejected', 'On Hold', 'Approved')
    if status not in allowed:
        flash('Invalid status.', 'danger')
        return redirect(url_for('project.task_details', id=task_id))
    subtask.status = status
    if status == 'Approved':
        from datetime import datetime as dt
        subtask.checked_timestamp = dt.utcnow()
        subtask.is_checked = True
        # Do NOT auto-complete task; use Mark Complete button explicitly
    try:
        db.session.commit()
        flash('Subtask updated.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to update subtask.', 'danger')
    return redirect(url_for('project.task_details', id=task_id))


@project_bp.route("/task_details/<int:task_id>/subtask/<int:sub_task_id>/delete", methods=['POST'])
@login_required
def delete_subtask(task_id, sub_task_id):
    task = Task.query.get_or_404(task_id)
    subtask = SubTask.query.filter_by(sub_task_id=sub_task_id, parent_task_id=task_id).first_or_404()
    if not _can_act_on_subtask(subtask, task, current_user):
        flash('You do not have permission to delete this subtask.', 'danger')
        return redirect(url_for('project.task_details', id=task_id))
    try:
        db.session.delete(subtask)
        db.session.commit()
        flash('Subtask deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to delete subtask.', 'danger')
    return redirect(url_for('project.task_details', id=task_id))


@project_bp.route("/task_details/<int:task_id>/subtask/<int:sub_task_id>/note", methods=['POST'])
@login_required
def subtask_note(task_id, sub_task_id):
    task = Task.query.get_or_404(task_id)
    subtask = SubTask.query.filter_by(sub_task_id=sub_task_id, parent_task_id=task_id).first_or_404()
    if not _can_act_on_subtask(subtask, task, current_user):
        flash('You do not have permission to add a note to this subtask.', 'danger')
        return redirect(url_for('project.task_details', id=task_id))
    note_body = (request.form.get('note_body') or '').strip()
    action = (request.form.get('action') or '').strip().lower()  # submit, resubmit, follow_up
    if not note_body:
        flash('Note is required.', 'danger')
        return redirect(url_for('project.task_details', id=task_id))
    pm_entry = ProjectMembers.query.filter_by(
        project_id=task.project_id,
        member_id=current_user.member_id
    ).first()
    p_members_id = pm_entry.p_members_id if pm_entry else None
    # Submit for review: PM, subtask owner, or any task assignee may submit
    if action == 'submit':
        project = Project.query.get(task.project_id) if task.project_id else None
        is_pm = project and current_user.member_id == project.project_manager
        is_subtask_owner = subtask.p_members_id and pm_entry and subtask.p_members_id == pm_entry.p_members_id
        is_task_assignee = False
        if pm_entry:
            if task.p_members_id == pm_entry.p_members_id:
                is_task_assignee = True
            else:
                for ta in (task.assignees or []):
                    if ta.p_members_id == pm_entry.p_members_id:
                        is_task_assignee = True
                        break
        if not (is_pm or is_subtask_owner or is_task_assignee):
            flash('Only the project manager, subtask owner, or a task assignee can submit for review.', 'danger')
            return redirect(url_for('project.task_details', id=task_id))
    new_note = Notes(
        task_id=task_id,
        sub_task_id=sub_task_id,
        member_id=current_user.member_id,
        p_members_id=p_members_id,
        note_body=note_body,
        generated_code=action or 'note'
    )
    db.session.add(new_note)
    if action == 'submit':
        subtask.status = 'To be reviewed'
    elif action == 'resubmit':
        subtask.status = 'To be reviewed'
    elif action == 'follow_up':
        pass  # note only, PM can resume later
    try:
        db.session.commit()
        if action == 'submit':
            flash('Subtask submitted for review.', 'success')
        elif action == 'resubmit':
            flash('Re-submitted for review.', 'success')
        else:
            flash('Note saved.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to save note.', 'danger')
    return redirect(url_for('project.task_details', id=task_id))


@project_bp.route("/task_details/<int:task_id>/subtask/<int:sub_task_id>/edit", methods=['POST'])
@login_required
def edit_subtask(task_id, sub_task_id):
    task = Task.query.get_or_404(task_id)
    subtask = SubTask.query.filter_by(sub_task_id=sub_task_id, parent_task_id=task_id).first_or_404()
    if not _can_act_on_subtask(subtask, task, current_user):
        flash('You do not have permission to edit this subtask.', 'danger')
        return redirect(url_for('project.task_details', id=task_id))
    name = (request.form.get('subtask_name') or '').strip()
    if name:
        subtask.subtask_name = name
    try:
        db.session.commit()
        flash('Subtask updated.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to update subtask.', 'danger')
    return redirect(url_for('project.task_details', id=task_id))

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


# Project Details Notes_tbl - Reply, Comment, Edit
@project_bp.route("/task/<int:task_id>/add_note", methods=['POST'])
@login_required
def add_note(task_id):
    # 1. Ensure the task exists
    task = Task.query.get_or_404(task_id)
    
    # 2. Get data from the form
    title = request.form.get('note_title')
    content = request.form.get('note_content')

    if not content:
        flash('Note content is required', 'warning')
        return redirect(url_for('project.task_details', id=task_id))

    try:
        new_note = Notes(
            task_id=task_id,
            member_id=current_user.member_id,
            note_body=content,          # Ensure this matches your Model
            generated_code=title,       # This stores your title
            created_on=datetime.now(),
            pin_stat=0
        )
        
        db.session.add(new_note)
        db.session.commit()
        flash('Note submitted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Database Error: {str(e)}', 'danger')

    # Redirect using 'id' because your task_details route likely expects 'id'
    return redirect(url_for('project.task_details', id=task_id))

# Updated Reply Route
@project_bp.route("/task/note/reply/<int:note_id>", methods=['POST'])
@login_required
def reply_note(note_id):
    body = request.form.get('reply_body')
    task_id = request.form.get('task_id')
    
    if not body or not task_id:
        flash('Reply content is required', 'warning')
        return redirect(request.referrer)

    try:
        new_reply = Notes(  
            task_id=int(task_id),
            member_id=current_user.member_id,
            note_body=body,
            reply_code=str(note_id),  # Parent Note ID
            created_on=datetime.now(),
            pin_stat=0
        )
        db.session.add(new_reply)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')

    return redirect(url_for('project.task_details', id=task_id))


@project_bp.route("/task/note/edit/<int:note_id>", methods=['GET', 'POST'])
@login_required
def edit_note(note_id):
    note = Notes.query.get_or_404(note_id)
    
    # 1. GET: This fixes the 'undefined' error by sending data to the modal
    if request.method == 'GET':
        return jsonify({
            'note_id': note.note_id,
            'note_title': note.generated_code, # Your title is stored here
            'note_content': note.note_body
        })

    # 2. POST: This handles the actual save/update
    # Security check: only author can edit
    if note.member_id != current_user.member_id:
        flash('Unauthorized', 'danger')
        return redirect(request.referrer)

    # Update fields
    note.generated_code = request.form.get('note_title')
    note.note_body = request.form.get('note_content')
    
    try:
        db.session.commit()
        flash('Note updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
        
    return redirect(request.referrer)

@project_bp.route("/all_task")
@login_required
def all_task():
    # All tasks from all projects (no department filter)
    tasks = Task.query.order_by(Task.task_id.desc()).all()

    if not tasks:
        users = User.query.all()
        departments = Department.query.all()
        stats = {'pending': 0, 'high_priority': 0, 'completed': 0, 'on_hold': 0}
        users_json = [
            {'member_id': u.member_id, 'name': u.name or u.username, 'username': u.username, 'department_id': u.department_id}
            for u in users
        ]
        return render_template('all_task.html', title="All Info", tasks_data=[], stats=stats, users_json=users_json, departments=departments, today=date.today())

    # Bulk lookups to avoid N+1
    project_ids = list({t.project_id for t in tasks if t.project_id})
    projects = Project.query.filter(Project.project_id.in_(project_ids)).all()
    project_by_id = {p.project_id: p for p in projects}

    user_ids = list({p.project_manager for p in projects if p.project_manager})
    users = User.query.all()
    user_by_id = {u.member_id: u for u in users}

    deadline_ids = list({t.deadline_id for t in tasks if t.deadline_id})
    deadlines_list = Deadlines.query.filter(Deadlines.deadlines_id.in_(deadline_ids)).all() if deadline_ids else []
    deadline_by_id = {d.deadlines_id: d for d in deadlines_list}

    department_ids = list({p.department_id for p in projects if p.department_id})
    departments = Department.query.all()
    dept_by_id = {d.department_id: d for d in departments}

    task_ids = [t.task_id for t in tasks]
    subtasks = SubTask.query.filter(SubTask.parent_task_id.in_(task_ids)).all()
    from collections import defaultdict
    subtasks_by_task = defaultdict(list)
    for s in subtasks:
        subtasks_by_task[s.parent_task_id].append(s)

    # Build list for template (no per-row queries)
    tasks_data = []
    for task in tasks:
        project = project_by_id.get(task.project_id) if task.project_id else None
        manager = user_by_id.get(project.project_manager) if project and project.project_manager else None
        deadline = deadline_by_id.get(task.deadline_id) if task.deadline_id else None
        department = dept_by_id.get(project.department_id) if project and project.department_id else None
        st_list = subtasks_by_task.get(task.task_id, [])
        st_total = len(st_list)
        st_done = sum(1 for s in st_list if s.is_checked)
        progress_pct = f"{st_done}/{st_total}" if st_total > 0 else "0/0"
        tasks_data.append({
            'task': task,
            'project': project,
            'department': department,
            'manager': manager,
            'deadline': deadline,
            'progress_pct': progress_pct,
            'sub_total': st_total,
        })

    # Calculate statistics from tasks
    stats = {
        'pending': len([t for t in tasks if (t.task_status or '').lower() in ('pending', 'ongoing', '') or not t.task_status]),
        'high_priority': len([t for t in tasks if (t.priority or '').lower() == 'high']),
        'completed': len([t for t in tasks if (t.task_status or '').lower() == 'completed']),
        'on_hold': len([t for t in tasks if (t.task_status or '').lower() == 'on hold'])
    }

    users_json = [
        {'member_id': u.member_id, 'name': u.name or u.username, 'username': u.username, 'department_id': u.department_id}
        for u in users
    ]

    return render_template('all_task.html', title="All Task", tasks_data=tasks_data, stats=stats, users_json=users_json, departments=departments, today=date.today())
    
@project_bp.route("/toggle_pin/<int:note_id>")
@login_required
def toggle_pin(note_id):
    # 1. Find the specific note
    note = Notes.query.get_or_404(note_id)
    
    # 2. Toggle the status
    note.pin_stat = not note.pin_stat
    
    # 3. If you want to track WHEN it was pinned (for better sorting)
    if note.pin_stat:
        note.pin_datetime = datetime.now()
    else:
        note.pin_datetime = None
        
    # 4. Save to database
    db.session.commit()
    
    # 5. Go back to where you were
    return redirect(request.referrer or url_for('project.projects'))


@project_bp.route("/task/<int:task_id>/add_note", methods=['POST'])
@login_required
def add_task_note(task_id):
    content = request.form.get('note_content')
    if not content:
        flash('Note content cannot be empty.', 'danger')
        return redirect(url_for('project.task_details', task_id=task_id))

    # Get the project_member_id for the current user in this project
    task = Task.query.get_or_404(task_id)
    project_member = ProjectMembers.query.filter_by(
        project_id=task.project_id, 
        member_id=current_user.member_id
    ).first()

    if not project_member:
        flash('You must be a member of this project to add notes.', 'danger')
        return redirect(url_for('project.task_details', task_id=task_id))

    new_note = Notes(
        task_id=task_id,
        p_members_id=project_member.p_members_id,
        note_content=content,
        date_added=datetime.now()
    )
    
    db.session.add(new_note)
    db.session.commit()
    flash('Note added successfully!', 'success')
    return redirect(url_for('project.task_details', task_id=task_id))

@project_bp.route("/task/note/<int:note_id>/reply", methods=['POST'])
@login_required
def add_reply(note_id):
    parent_note = Notes.query.get_or_404(note_id)
    content = request.form.get('reply_content')
    
    if not content:
        flash('Reply cannot be empty.', 'danger')
        return redirect(url_for('project.task_details', task_id=parent_note.task_id))

    project_member = ProjectMembers.query.filter_by(
        project_id=parent_note.task.project_id, 
        member_id=current_user.member_id
    ).first()

    new_reply = Notes(
        task_id=parent_note.task_id,
        parent_note_id=note_id,
        p_members_id=project_member.p_members_id,
        note_content=content,
        date_added=datetime.now()
    )
    
    db.session.add(new_reply)
    db.session.commit()
    return redirect(url_for('project.task_details', task_id=parent_note.task_id))


@project_bp.route("/task/<int:task_id>/submit_subtask", methods=['POST'])
@login_required
def submit_subtask_for_review(task_id):
    sub_task_id = request.form.get('sub_task_id')
    action_type = request.form.get('action_type')  # e.g., 'submit', 'approve', 'reject'
    note_content = request.form.get('note_content')

    subtask = SubTask.query.get_or_404(sub_task_id)
    
    # Update subtask status based on action
    if action_type == 'submit':
        subtask.status = 'Under Review'
    elif action_type == 'approve':
        subtask.status = 'Approved'
        subtask.is_checked = True
    elif action_type == 'reject':
        subtask.status = 'Ongoing'
        subtask.is_checked = False

    # Optional: If you have a system for logging notes on subtask changes
    if note_content:
        # Example: Log the note in your Notes table or a specific SubTask log
        pass

    db.session.commit()
    flash(f'Sub-task updated successfully!', 'success')
    return redirect(url_for('project.task_details', task_id=task_id))

# @project_bp.route("/get_note/<int:note_id>")
# @login_required
# def get_note(note_id):
#     note = Notes.query.get_or_404(note_id)
#     # The keys here MUST match your JavaScript data properties
#     return jsonify({
#         'note_id': note.note_id,
#         'note_title': note.note_title,
#         'note_content': note.note_body, # Mapping 'note_body' from DB to 'note_content' for the modal
#         'success': True
#     })

# @project_bp.route("/update_note", methods=['POST'])
# @login_required
# def update_note():
#     note_id = request.form.get('note_id')
#     note = Notes.query.get_or_404(note_id)
    
#     note.note_title = request.form.get('note_title')
#     note.note_body = request.form.get('note_content')
#     note.date_updated = datetime.now()
    
#     db.session.commit()
#     flash('Note updated!', 'success')
#     return redirect(url_for('project.project_details', id=note.project_id))