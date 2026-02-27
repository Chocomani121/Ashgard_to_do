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


department_bp = Blueprint('department', __name__, template_folder='templates', static_folder='static', static_url_path='/department/static')


@department_bp.route("/all_departments")
@login_required
def all_departments():
    departments = Department.query.options(selectinload(Department.members)).all()
    # Get all users (we'll filter unassigned ones in JavaScript for dropdown, but need all for Edit modal)
    users = User.query.with_entities(User.member_id, User.name, User.username, User.department_id).all()

    return render_template('all_departments.html', departments=departments, users=users, today=date.today())

@department_bp.route("/department/add", methods=['POST'])
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
    return redirect(url_for('department.all_departments'))

@department_bp.route("/department/edit/<int:id>", methods=['GET', 'POST'])
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
        return redirect(url_for('department.all_departments'))
    return render_template('edit_department.html', department=department)

@department_bp.route("/department/delete/<int:id>", methods=['POST'])
@login_required
def delete_department(id):
    department = Department.query.get_or_404(id)
    try:
        db.session.delete(department)
        db.session.commit()
        flash('Department deleted!', 'success')
    except Exception:
        db.session.rollback()
        flash('Cannot delete department. It may have users assigned to it.', 'danger')
        
    return redirect(url_for('department.all_departments'))
