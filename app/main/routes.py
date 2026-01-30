from flask import render_template, Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Department, User, Project, Deadlines, ProjectMembers, Task, SubTask
from app import db 
from datetime import datetime
import json

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/projects") 
# @cache.cached(timeout=60)
@login_required
def projects():
    # Fetch all projects with related data
    
    projects = Project.query.all()
    departments = Department.query.all()
    users = User.query.all()
    
    # Prepare projects data for template
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
        
        projects_data.append({
            'project': project,
            'department': dept,
            'manager': manager,
            'deadline': deadline,
            'priority': priority
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

@main.route("/tasks")
@login_required 
def tasks():
    return render_template('tasks.html', title="Tasks Info")

@main.route("/all_departments")
@login_required
def all_departments():
    departments = Department.query.all()
    # Get all users (we'll filter unassigned ones in JavaScript for dropdown, but need all for Edit modal)
    users = User.query.all()
    projects = Project.query.all()
    # Build department projects data for the Department Projects table
    dept_projects_data = []
    for project in projects:
        dept = Department.query.get(project.department_id) if project.department_id else None
        manager = User.query.get(project.project_manager) if project.project_manager else None
        deadline = Deadlines.query.get(project.deadlines_id) if project.deadlines_id else None
        
        dept_projects_data.append({
            'project': project,
            'department': dept,
            'manager': manager,
            'deadline': deadline,
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

@main.route("/approvals")
def approvals():
    return render_template('approvals.html', title="Approvals")

@main.route("/reports")
def reports():
    return render_template('reports.html', title="Reports")

@main.route("/members")
@login_required
def members():
    users = User.query.all()
    return render_template('members.html', title="Members", users=users)

@main.route("/project_details")
@main.route("/project_details/<int:id>")
@login_required
def project_details(id=None):
    # If no ID provided, get the first project or handle appropriately
    if id is None:
        project = Project.query.first()
    else:
        project = Project.query.get(id)
    
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('main.projects'))
    
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
    
    # Get tasks for this project
    tasks = []
    if project:
        project_tasks = Task.query.filter_by(project_id=project.project_id).all()
        for task in project_tasks:
            # Get task owner
            owner = None
            if task.p_members_id:
                project_member = ProjectMembers.query.get(task.p_members_id)
                if project_member and project_member.member_id:
                    owner = User.query.get(project_member.member_id)
            
            # Calculate task progress (completed subtasks / total subtasks)
            subtasks = SubTask.query.filter_by(parent_task_id=task.task_id).all()
            total_subtasks = len(subtasks)
            completed_subtasks = len([st for st in subtasks if st.is_checked])
            progress = f"{completed_subtasks}/{total_subtasks}" if total_subtasks > 0 else "0/0"
            
            # Normalize task status
            task_status = task.task_status or 'Ongoing'
            if task_status == 'Pending' or task_status == 'Cancelled':
                task_status = 'Ongoing'
            
            tasks.append({
                'task': task,
                'owner': owner,
                'progress': progress,
                'status': task_status
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
                         edit_initial_members_json=edit_initial_members_json)

@main.route("/project_details/<int:id>/update_manager", methods=['POST'])
@login_required
def update_project_manager(id):
    project = Project.query.get_or_404(id)
    project_manager_id = request.form.get('project_manager')
    if not project_manager_id:
        flash('Please select a Project Manager', 'danger')
        return redirect(url_for('main.project_details', id=id))
    try:
        project.project_manager = int(project_manager_id)
        db.session.commit()
        flash('Project manager updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update: {}'.format(str(e)), 'danger')
    return redirect(url_for('main.project_details', id=id))

@main.route("/project_details/<int:id>/update_members", methods=['POST'])
@login_required
def update_project_members(id):
    project = Project.query.get_or_404(id)
    member_ids = request.form.getlist('project_members')
    if not member_ids:
        flash('Please select at least one member', 'danger')
        return redirect(url_for('main.project_details', id=id))
    try:
        # Delete all existing project members
        ProjectMembers.query.filter_by(project_id=project.project_id).delete()
        db.session.flush()  # Ensure delete is processed before adding new ones
        
        # Add all selected members (from any department)
        for mid in member_ids:
            if mid and str(mid).isdigit():
                member_id_int = int(mid)
                user = User.query.get(member_id_int)
                if user:
                    pm = ProjectMembers(
                        project_id=project.project_id,
                        member_id=member_id_int,
                        role='Team Member'
                    )
                    db.session.add(pm)
        
        db.session.commit()
        flash('Project members updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update: {}'.format(str(e)), 'danger')
    return redirect(url_for('main.project_details', id=id))

@main.route("/project_details/<int:id>/update", methods=['POST'])
@login_required
def update_project(id):
    project = Project.query.get_or_404(id)
    project_name = request.form.get('project_name', '').strip()
    if not project_name:
        flash('Project name is required', 'danger')
        return redirect(url_for('main.project_details', id=id))
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
                return redirect(url_for('main.project_details', id=id))
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
    return redirect(url_for('main.project_details', id=id))

@main.route("/project_details/<int:id>/update_description", methods=['POST'])
@login_required
def update_project_description(id):
    project = Project.query.get_or_404(id)
    project_desc = request.form.get('project_desc', '').strip() or None
    try:
        project.project_desc = project_desc
        db.session.commit()
        flash('Description updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to update: {}'.format(str(e)), 'danger')
    return redirect(url_for('main.project_details', id=id))

@main.route("/project_details/<int:id>/delete", methods=['GET', 'POST'])
@login_required
def delete_project(id):
    project = Project.query.get_or_404(id)
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
    return redirect(url_for('main.projects'))

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
        return redirect(url_for('main.projects'))
    
    return render_template('task_details.html', task=task)

@main.route("/project_details/<int:id>/task/create", methods=['POST'])
@login_required
def create_task(id):
    try:
        # Get the project
        project = Project.query.get_or_404(id)
        
        # Get form data
        task_name = request.form.get('task_name')
        owner_id = request.form.get('owner_id')
        task_description = request.form.get('task_description', '')
        
        # Validate required fields
        if not task_name or not owner_id:
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('main.project_details', id=id))
        
        # Verify that the owner is assigned to this project
        project_member = ProjectMembers.query.filter_by(
            project_id=project.project_id,
            member_id=int(owner_id)
        ).first()
        
        if not project_member:
            flash('Selected owner must be assigned to this project', 'danger')
            return redirect(url_for('main.project_details', id=id))
        
        # Create the task
        task = Task(
            project_id=project.project_id,
            p_members_id=project_member.p_members_id,
            task_name=task_name,
            task_description=task_description.strip() if task_description else None,
            task_status='Ongoing',
            priority='Medium'
        )
        
        db.session.add(task)
        db.session.commit()
        
        flash('Task created successfully!', 'success')
        return redirect(url_for('main.project_details', id=id))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating task: {str(e)}', 'danger')
        return redirect(url_for('main.project_details', id=id))

@main.route("/project/create", methods=['POST'])
@login_required
def create_project():
    try:
        # Get form data
        project_name = request.form.get('project_name')
        priority = request.form.get('priority', 'High')
        client_name = request.form.get('client_name')
        department_id = request.form.get('department_id')
        # Project manager is automatically set to the current user
        project_manager = current_user.member_id
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        # New projects default to Ongoing (not shown in UI)
        project_status = 'Ongoing'
        progress = request.form.get('progress', '0%')
        project_description = request.form.get('topicDescription', '')
        
        # Validate required fields
        if not all([project_name, priority, client_name, department_id, start_date_str, end_date_str]):
            flash('Please fill in all required fields', 'danger')
            return redirect(url_for('main.projects'))
        
        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('main.projects'))
        if end_date < start_date:
            flash('Deadline cannot be earlier than the start date.', 'danger')
            return redirect(url_for('main.projects'))

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
            department_id=int(department_id),
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
        
        # Get assigned members from form
        member_ids = request.form.getlist('project_members')
        
        # Create ProjectMembers entries for assigned members using project_id
        if member_ids:
            for member_id in member_ids:
                try:
                    member_id_int = int(member_id)
                    # Check if ProjectMembers entry already exists for this member and project
                    existing = ProjectMembers.query.filter_by(
                        member_id=member_id_int,
                        project_id=project.project_id
                    ).first()
                    
                    # Only create if it doesn't exist
                    if not existing:
                        project_member = ProjectMembers(
                            project_id=project.project_id,
                            member_id=member_id_int,
                            role='Team Member',  # Default role, can be updated later
                            generated_code=str(project.project_id)  # Keep for backward compatibility if needed
                        )
                        db.session.add(project_member)
                except (ValueError, TypeError):
                    continue
        
        db.session.commit()
        
        flash('Project created successfully!', 'success')
        return redirect(url_for('main.projects'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating project: {str(e)}', 'danger')
        return redirect(url_for('main.projects'))
