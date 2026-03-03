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


# @main.route("/approvals")
# def approvals():
#     return render_template('approvals.html', title="Approvals")

@main.route("/members")
@login_required
def members():
    users = User.query.all()
    departments = Department.query.all()
    return render_template('members.html', title="Members", members=users, total_users=len(users), departments=departments)

@main.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

