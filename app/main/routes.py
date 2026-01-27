from flask import render_template, Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import Department, User, Project, Deadlines, ProjectMembers, Task, SubTask
from app import db # Required for committing changes
from datetime import datetime
import json

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/projects") 
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
        
        # Calculate manhours (hours between start_date and end_date)
        manhours = None
        if deadline and deadline.start_date and deadline.end_date:
            time_diff = deadline.end_date - deadline.start_date
            # Convert to hours (total_seconds() / 3600)
            manhours = int(time_diff.total_seconds() / 3600)
        
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
            'manhours': manhours,
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
        
        # Calculate manhours (hours between start_date and end_date)
        manhours = None
        if deadline and deadline.start_date and deadline.end_date:
            try:
                time_diff = deadline.end_date - deadline.start_date
                manhours = int(time_diff.total_seconds() / 3600)  # Convert to hours
            except:
                manhours = None
        
        dept_projects_data.append({
            'project': project,
            'department': dept,
            'manager': manager,
            'deadline': deadline,
            'manhours': manhours,
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
    
    # Calculate manhours
    manhours = None
    if deadline and deadline.start_date and deadline.end_date:
        try:
            time_diff = deadline.end_date - deadline.start_date
            manhours = int(time_diff.total_seconds() / 3600)  # Convert to hours
        except:
            manhours = None
    
    # Normalize status: convert Pending/Cancelled to Ongoing
    display_status = project.project_status
    if not display_status or display_status == 'Pending' or display_status == 'Cancelled':
        display_status = 'Ongoing'
    
    # Get assigned members for this project using project_id
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
    
    return render_template('project_details.html', 
                         project=project, 
                         manager=manager, 
                         deadline=deadline,
                         department=department,
                         manhours=manhours,
                         display_status=display_status,
                         assigned_members=assigned_members,
                         tasks=tasks)

@main.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@main.route("/task_details")
@login_required
def task_details():
    return render_template('task_details.html')

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
        project_status = request.form.get('project_status', 'Ongoing')
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
