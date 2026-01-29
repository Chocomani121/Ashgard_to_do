from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from app import db, login_manager
from flask_login import UserMixin
from sqlalchemy import Enum

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ORGANIZATION & USERS ---

class Department(db.Model):
    __tablename__   = 'department'
    department_id   = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(255), nullable=False)
    creation_date   = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    edited_on       = db.Column(db.DateTime(timezone=True), onupdate=db.func.now())

    members         = db.relationship('User', backref='dept_info', lazy=True)
    projects        = db.relationship('Project', backref='dept_info', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'members' 
    member_id       = db.Column(db.Integer, primary_key=True)
    department_id   = db.Column(db.Integer, db.ForeignKey('department.department_id'))
    username        = db.Column(db.String(20),  unique=True, nullable=False)
    email           = db.Column(db.String(120), unique=True, nullable=False)
    password        = db.Column(db.String(255), nullable=False) 
    name            = db.Column(db.String(255)) 
    account_type    = db.Column(db.String(255), default='user')
    image_file      = db.Column(db.String(20),  nullable=False, default='default.jpg')
    
    # Relationships
    notes_written    = db.relationship('Notes', backref='author', lazy=True)
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

# --- PROJECTS & DEADLINES ---

class Deadlines(db.Model):
    __tablename__   = 'deadlines_tbl'
    deadlines_id    = db.Column(db.Integer, primary_key=True)
    start_date      = db.Column(db.DateTime, nullable=False)
    end_date        = db.Column(db.DateTime, nullable=False)
    create_on       = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    flag            = db.Column(db.String(255))
    
    projects        = db.relationship('Project', backref='deadline_ref', lazy=True)
    tasks           = db.relationship('Task', backref='deadline_ref', lazy=True)
    history         = db.relationship('PrevDateList', backref='main_deadline', lazy=True)

class PrevDateList(db.Model):
    __tablename__    = 'prev_date_list'
    prev_date_id     = db.Column(db.Integer, primary_key=True)
    deadlines_id     = db.Column(db.Integer, db.ForeignKey('deadlines_tbl.deadlines_id'))
    prev_date_actual = db.Column(db.DateTime)
    created_on       = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

class Project(db.Model):
    __tablename__   = 'project'
    project_id      = db.Column(db.Integer, primary_key=True)
    department_id   = db.Column(db.Integer, db.ForeignKey('department.department_id'))
    project_manager = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    deadlines_id    = db.Column(db.Integer, db.ForeignKey('deadlines_tbl.deadlines_id'))
    
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
    project_id      = db.Column(db.Integer, db.ForeignKey('project.project_id'))
    member_id       = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    role            = db.Column(db.String(255))
    generated_code  = db.Column(db.String(255))
    assigned_date   = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    user = db.relationship('User', backref='project_assignments', lazy=True)

# --- TASKS & NOTES (Constraint Fix Applied) ---

class Task(db.Model):
    __tablename__    = 'task_tbl'
    task_id          = db.Column(db.Integer, primary_key=True)
    deadline_id      = db.Column(db.Integer, db.ForeignKey('deadlines_tbl.deadlines_id'))
    project_id       = db.Column(db.Integer, db.ForeignKey('project.project_id'))
    p_members_id     = db.Column(db.Integer, db.ForeignKey('project_members.p_members_id'))

    priority         = db.Column(db.String(255))
    task_name        = db.Column(db.String(255), nullable=False)
    task_description = db.Column(db.Text)
    task_status      = db.Column(db.String(255))
    category         = db.Column(db.String(255))

class SubTask(db.Model):
    __tablename__     = 'sub_task_list'
    sub_task_id       = db.Column(db.Integer, primary_key=True)
    parent_task_id    = db.Column(db.Integer, db.ForeignKey('task_tbl.task_id'))
    # notes_id removed here to break circular dependency
    subtask_name      = db.Column(db.String(255))
    is_checked        = db.Column(db.Boolean, default=False)
    created_on        = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    notes = db.relationship('Notes', backref='parent_subtask', lazy=True)

class Notes(db.Model):
    __tablename__ = 'notes_tbl'
    notes_id      = db.Column(db.Integer, primary_key=True)
    task_id       = db.Column(db.Integer, db.ForeignKey('task_tbl.task_id'))
    sub_task_id   = db.Column(db.Integer, db.ForeignKey('sub_task_list.sub_task_id'))
    p_members_id  = db.Column(db.Integer, db.ForeignKey('project_members.p_members_id'))
    member_id     = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    
    reply_code     = db.Column(db.String(255))
    note_body      = db.Column(db.Text, nullable=False)
    created_on     = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    edited_on      = db.Column(db.DateTime)
    pin_stat       = db.Column(db.Boolean, default=False)
    pin_datetime   = db.Column(db.DateTime)
    generated_code = db.Column(db.String(255))

# --- REPORTS & COMMENTS SYSTEM ---

class Report(db.Model):
    __tablename__ = 'report_tbl'
    report_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.project_id'))
    reviewer_id = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    
    is_checked = db.Column(db.Boolean, default=False) # The "Stamp"
    checked_at = db.Column(db.DateTime)
    week_name = db.Column(db.String(100), nullable=False)
    report_content = db.Column(db.Text, nullable=False)
    created_on = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    
    # Use foreign_keys for multiple links to 'members' table
    author = db.relationship('User', foreign_keys=[member_id], backref='my_reports')
    reviewer_user = db.relationship('User', foreign_keys=[reviewer_id], backref='reports_to_review')
    cc_entries = db.relationship('ReportCC', backref='report', cascade="all, delete-orphan")
    comments = db.relationship('Comment', backref='report', cascade="all, delete-orphan", lazy=True)

class ReportCC(db.Model):
    __tablename__ = 'report_cc_tbl'
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('report_tbl.report_id'))
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    user = db.relationship('User', backref='cc_reports')

class Comment(db.Model):
    __tablename__ = 'comments_tbl'
    comment_id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('report_tbl.report_id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.member_id'), nullable=False)
    
    # parent_comment_id allows for threaded replies
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comments_tbl.comment_id'))
    
    comment_body = db.Column(db.Text, nullable=False)
    updated_on = db.Column(db.DateTime, onupdate=db.func.now())
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

    author = db.relationship('User', backref='my_comments', lazy=True)
    replies = db.relationship(
        'Comment', 
        backref=db.backref('parent', remote_side=[comment_id]),
        cascade="all, delete-orphan"
    )
