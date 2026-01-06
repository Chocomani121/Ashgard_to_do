from app import db, login_manager # Import the manager you just set up
from flask_login import UserMixin
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer 
from flask import current_app
from app import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), default='user')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

# --- Supporting Tables ---

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(255), nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    members = db.relationship('User', backref='department', lazy=True)
    projects = db.relationship('Project', backref='dept', lazy=True)

class Deadlines(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    flag = db.Column(db.String(255))
    # Relationships
    projects = db.relationship('Project', backref='deadline_info', lazy=True)
    tasks = db.relationship('Task', backref='deadline_info', lazy=True)

class PrevDateList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deadlines_id = db.Column(db.Integer, db.ForeignKey('deadlines.id'))
    prev_date_actual = db.Column(db.DateTime)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

# --- Main Tables ---

class User(db.Model, UserMixin):
    __tablename__ = 'members' # Matching your 'members' table name
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # Added for login
    password = db.Column(db.String(60), nullable=False)           # Added for login
    account_type = db.Column(db.String(255), default='user')
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    # Relationships
    project_links = db.relationship('ProjectMembers', backref='member', lazy=True)
    notes = db.relationship('Notes', backref='author', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    project_manager_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    deadlines_id = db.Column(db.Integer, db.ForeignKey('deadlines.id'))
    client_name = db.Column(db.String(255))
    project_status = db.Column(db.String(255))
    progress = db.Column(db.String(255))
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True)
    members = db.relationship('ProjectMembers', backref='project', lazy=True)

class ProjectMembers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    role = db.Column(db.String(255))
    generated_code = db.Column(db.String(255))
    assigned_date = db.Column(db.DateTime, default=datetime.utcnow)
    removed_date = db.Column(db.DateTime)
    re_assigned_date = db.Column(db.DateTime)

class Task(db.Model):
    __tablename__ = 'task_tbl'
    id = db.Column(db.Integer, primary_key=True)
    deadline_id = db.Column(db.Integer, db.ForeignKey('deadlines.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    p_members_id = db.Column(db.Integer, db.ForeignKey('project_members.id'))
    priority = db.Column(db.String(255))
    task_name = db.Column(db.String(255), nullable=False)
    task_description = db.Column(db.Text)
    task_status = db.Column(db.String(255))
    generated_code = db.Column(db.String(255))
    category = db.Column(db.String(255))
    progress = db.Column(db.String(255))
    # Relationships
    subtasks = db.relationship('SubTask', backref='parent_task', lazy=True)
    notes = db.relationship('Notes', backref='task', lazy=True)

class SubTask(db.Model):
    __tablename__ = 'sub_task_list'
    id = db.Column(db.Integer, primary_key=True)
    parent_task_id = db.Column(db.Integer, db.ForeignKey('task_tbl.id'))
    p_members_id = db.Column(db.Integer, db.ForeignKey('project_members.id'))
    subtask_name = db.Column(db.String(255))
    generated_code = db.Column(db.String(255))
    checked_timestamp = db.Column(db.DateTime)
    status = db.Column(db.String(255))
    is_checked = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)

class Notes(db.Model):
    __tablename__ = 'notes_tbl'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task_tbl.id'))
    sub_task_id = db.Column(db.Integer, db.ForeignKey('sub_task_list.id'))
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'))
    reply_code = db.Column(db.String(255))
    note_body = db.Column(db.Text, nullable=False)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    edited_on = db.Column(db.DateTime)
    pin_stat = db.Column(db.Boolean, default=False)
    pin_datetime = db.Column(db.DateTime)

