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


@main.route("/members")
@login_required
def members():
    users = User.query.all()
    return render_template('members.html', title="Members", members=users, total_users=len(users))

@main.route("/profile")
@login_required
def profile():
    return render_template('profile.html')
