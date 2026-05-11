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

# Enque function
# from ...background_tasks.modules.enque_event import enqueue_outbox_event, _pick_version_ts, _serialize_row
from ...background_tasks.enque_event_task import enqueue_task, _pick_version_ts, _serialize_row



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


        # Outbox : write new Department to Outbox
        desc = f"new Dept: '{new_dept.department_name}'"


        add_dept = enqueue_task.delay(
            table_name   =   "department",
            event_type   =   "insert",
            pk_dict      =   {"department_id": new_dept.department_id},
            payload_dict =   _serialize_row(new_dept),
            version_ts   =   _pick_version_ts(new_dept),
            outbox_desc  =   desc
        )

        # enqueue_task(
        #     table_name   =   "department",
        #     event_type   =   "insert",
        #     pk_dict      =   {"department_id": new_dept.department_id},
        #     payload_dict =   _serialize_row(new_dept),
        #     version_ts   =   _pick_version_ts(new_dept),
        #     outbox_desc  =   desc
        # )

        
        # Assign selected members to the new department
        if member_ids:
            for member_id in member_ids:
                user = ''
                try:
                    user = User.query.get(int(member_id))
                    if user:
                        user.department_id = new_dept.department_id

                        # Outbox : record Members to Outbox 
                        desc = f"addded User ID: '{user.member_id}' to this new Dept: '{new_dept.department_name}'"
                        member_add = enqueue_task.delay(
                            table_name   =   "members",
                            event_type   =   "update",
                            pk_dict      =   {"member_id": user.member_id},
                            payload_dict =   _serialize_row(user),
                            version_ts   =   _pick_version_ts(user),
                            outbox_desc  =   desc
                        )
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

        # write the update to Outbox
        desc = f"updated Dept name to: '{department.department_name}'"
        edit_dept = enqueue_task.delay(
            table_name   =   "department",
            event_type   =   "update",
            pk_dict      =   {"department_id": department.department_id},
            payload_dict =   _serialize_row(department),
            version_ts   =   _pick_version_ts(department),
            outbox_desc  =   desc
        )

        for user in department.members:
            user.department_id = None

            # Outbox : update on Members when are unassigned from a Department  
            desc = f"removed User: {user.name} ({user.username}) to this Dept: {department.department_name}"
            member_remove = enqueue_task.delay(
                table_name   =   "members",
                event_type   =   "update",
                pk_dict      =   {"member_id": user.member_id},
                payload_dict =   _serialize_row(user),
                version_ts   =   _pick_version_ts(user),
                outbox_desc  =   desc
            )
        
        if member_ids:
            for member_id in member_ids:
                try:
                    user = User.query.get(int(member_id))
                    if user:
                        user.department_id = department.department_id

                        # Outbox : record update on Members  
                        desc = f"addded User: '{user.name}' ({user.username}) to Dept: '{department.department_name}'"
                        member_add = enqueue_task.delay(
                            table_name   =   "members",
                            event_type   =   "update",
                            pk_dict      =   {"member_id": user.member_id},
                            payload_dict =   _serialize_row(user),
                            version_ts   =   _pick_version_ts(user),
                            outbox_desc  =   desc
                        )
                        
                except (ValueError, TypeError):
                    print(f"\n\n \n\n")
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

        # Outbox : record delete on Members  
        desc = f"{department.department_name} has been deleted"
        del_dept = enqueue_task.delay(
            table_name   =   "department",
            event_type   =   "delete",
            pk_dict      =   {"department_id": department.department_id},
            payload_dict =   None,
            version_ts   =   None,
            outbox_desc  =   desc
        )


        db.session.commit()
        flash('Department deleted!', 'success')
    except Exception:
        db.session.rollback()
        flash('Cannot delete department. It may have users assigned to it.', 'danger')
        
    return redirect(url_for('department.all_departments'))
