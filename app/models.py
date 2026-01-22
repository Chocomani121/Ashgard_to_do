from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy import Enum
from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.sql import func

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Department(db.Model):
    __tablename__   = 'department'
    department_id   = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(255), nullable=False)
    creation_date   = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    # This 'members' relationship is what we use in the HTML to count users
    members         = db.relationship('User', backref='dept_info', lazy=True)
    projects        = db.relationship('Project', backref='dept_info', lazy=True)

class Deadlines(db.Model):
    __tablename__   = 'deadlines_tbl'
    deadlines_id    = db.Column(db.Integer, primary_key=True)
    start_date      = db.Column(db.DateTime, nullable=False)
    end_date        = db.Column(db.DateTime, nullable=False)
    create_on       = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    flag            = db.Column(db.String(255))
    
    projects        = db.relationship('Project', backref='deadline_ref', lazy=True)
    tasks           = db.relationship('Task',    backref='deadline_ref', lazy=True)

class PrevDateList(db.Model):
    __tablename__   = 'prev_date_list'
    prev_date_id     = db.Column(db.Integer, primary_key=True)
    deadlines_id     = db.Column(db.Integer, db.ForeignKey('deadlines_tbl.deadlines_id'))
    prev_date_actual = db.Column(db.DateTime)
    created_on       = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class User(db.Model, UserMixin):
    __tablename__ = 'members' 
    
    member_id       = db.Column(db.Integer, primary_key=True)
    # This ForeignKey links back to department_id
    department_id   = db.Column(db.Integer, db.ForeignKey('department.department_id'))
    
    username        = db.Column(db.String(20),  unique=True, nullable=False)
    email           = db.Column(db.String(120), unique=True, nullable=False)
    password        = db.Column(db.String(255), nullable=False) 
    name            = db.Column(db.String(255)) 
    account_type    = db.Column(db.String(255), default='user')
    image_file      = db.Column(db.String(20),  nullable=False, default='default.jpg')
    
    notes            = db.relationship('Notes',   backref='author', lazy=True)
    managed_projects = db.relationship('Project', backref='manager', lazy=True)

    def get_id(self):
        return str(self.member_id)

    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'user_id': self.member_id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, max_age=expires_sec)['user_id']
        except Exception:
            return None
        return User.query.get(user_id)

class Project(db.Model):
    __tablename__   = 'project'
    project_id      = db.Column(db.Integer, primary_key=True)
    department_id   = db.Column(db.Integer, db.ForeignKey('department.department_id'))
    project_manager = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    deadlines_id    = db.Column(db.Integer, db.ForeignKey('deadlines_tbl.deadlines_id'))
    
    # Priority field - ENUM type matching database
    priority        = db.Column(Enum('Low', 'Medium', 'High', name='priority_enum'), default='High')
    project_name    = db.Column(db.String(255), nullable=False)
    client_name     = db.Column(db.String(255))
    project_status  = db.Column(db.String(255))
    progress        = db.Column(db.String(255))
    project_desc    = db.Column(db.Text)

    tasks           = db.relationship('Task', backref='project_info', lazy=True)
    team_members    = db.relationship('ProjectMembers', backref='project_ref', lazy=True)

class ProjectMembers(db.Model):
    __tablename__   = 'project_members'
    p_members_id    = db.Column(db.Integer, primary_key=True)
    project_id      = db.Column(db.Integer, db.ForeignKey('project.project_id')) # Added this
    member_id       = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    role            = db.Column(db.String(255))
    generated_code  = db.Column(db.String(255))
    assigned_date   = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Task(db.Model):
    __tablename__    = 'task_tbl'
    task_id          = db.Column(db.Integer, primary_key=True)
    deadline_id      = db.Column(db.Integer, db.ForeignKey('deadlines_tbl.deadlines_id'))
    project_id       = db.Column(db.Integer, db.ForeignKey('project.project_id'))
    p_members_id     = db.Column(db.Integer, db.ForeignKey('project_members.p_members_id'))
    notes_id         = db.Column(db.Integer, db.ForeignKey('notes_tbl.notes_id'))
    
    priority         = db.Column(db.String(255))
    task_name        = db.Column(db.String(255), nullable=False)
    task_description = db.Column(db.Text)
    task_status      = db.Column(db.String(255))
    category         = db.Column(db.String(255))

class SubTask(db.Model):
    __tablename__     = 'sub_task_list'
    sub_task_id       = db.Column(db.Integer, primary_key=True)
    parent_task_id    = db.Column(db.Integer, db.ForeignKey('task_tbl.task_id'))
    notes_id          = db.Column(db.Integer, db.ForeignKey('notes_tbl.notes_id'))
    subtask_name      = db.Column(db.String(255))
    is_checked        = db.Column(db.Boolean, default=False)
    created_on        = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Notes(db.Model):
    __tablename__ = 'notes_tbl'
    notes_id      = db.Column(db.Integer, primary_key=True)
    task_id       = db.Column(db.Integer, db.ForeignKey('task_tbl.task_id'))
    sub_task_id   = db.Column(db.Integer, db.ForeignKey('sub_task_list.sub_task_id'))
    p_members_id  = db.Column(db.Integer, db.ForeignKey('project_members.p_members_id'))
    reply_code    = db.Column(db.String(255))
    note_body     = db.Column(db.Text, nullable=False)
    created_on    = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    edited_on     = db.Column(db.DateTime)
    pin_stat      = db.Column(db.Boolean, default=False)
    pin_datetime  = db.Column(db.DateTime)
    generated_code = db.Column(db.String(255))
    member_id     = db.Column(db.Integer, db.ForeignKey('members.member_id'))