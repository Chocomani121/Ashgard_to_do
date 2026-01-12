from datetime import datetime
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from app import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    # Matches member_id in MySQL
    return User.query.get(int(user_id))

# --- ORGANIZATION & SUPPORT ---

class Department(db.Model):
    __tablename__   = 'department'
    department_id   = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(255), nullable=False)
    creation_date   = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    members         = db.relationship('User',    backref='dept_info', lazy=True)
    projects        = db.relationship('Project', backref='dept_info', lazy=True)

class Deadlines(db.Model):
    __tablename__   = 'deadlines_tbl'
    deadlines_id    = db.Column(db.Integer, primary_key=True)
    start_date      = db.Column(db.DateTime, nullable=False)
    end_date        = db.Column(db.DateTime, nullable=False)
    create_on       = db.Column(db.DateTime, default=datetime.utcnow)
    flag            = db.Column(db.String(255))
    
    # Relationships
    projects        = db.relationship('Project', backref='deadline_ref', lazy=True)
    tasks           = db.relationship('Task',    backref='deadline_ref', lazy=True)

class PrevDateList(db.Model):
    __tablename__   = 'prev_date_list'
    prev_date_id     = db.Column(db.Integer, primary_key=True)
    deadlines_id     = db.Column(db.Integer, db.ForeignKey('deadlines_tbl.deadlines_id'))
    prev_date_actual = db.Column(db.DateTime)
    created_on       = db.Column(db.DateTime, default=datetime.utcnow)

# --- USER / MEMBERS ---

class User(db.Model, UserMixin):
    __tablename__ = 'members' 
    
    member_id       = db.Column(db.Integer, primary_key=True)
    department_id   = db.Column(db.Integer, db.ForeignKey('department.department_id'))
    
    username        = db.Column(db.String(20),  unique=True, nullable=False)
    email           = db.Column(db.String(120), unique=True, nullable=False)
    password        = db.Column(db.String(255), nullable=False) # Length 255 for MySQL
    name            = db.Column(db.String(255)) 
    account_type    = db.Column(db.String(255), default='user')
    image_file      = db.Column(db.String(20),  nullable=False, default='default.jpg')
    
    # Relationship links
    notes           = db.relationship('Notes',          backref='author', lazy=True)
    managed_projects = db.relationship('Project',       backref='manager', lazy=True)

    # Required for Flask-Login because we renamed 'id' to 'member_id'
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

# --- PROJECTS & TASKS ---

class Project(db.Model):
    __tablename__   = 'project'
    project_id      = db.Column(db.Integer, primary_key=True)
    department_id   = db.Column(db.Integer, db.ForeignKey('department.department_id'))
    project_manager = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    deadlines_id    = db.Column(db.Integer, db.ForeignKey('deadlines_tbl.deadlines_id'))
    
    client_name     = db.Column(db.String(255))
    project_status  = db.Column(db.String(255))
    progress        = db.Column(db.String(255))
    p_members_id    = db.Column(db.Integer) # Reference to group id

    # Relationships
    tasks           = db.relationship('Task', backref='project_info', lazy=True)

class ProjectMembers(db.Model):
    __tablename__   = 'project_members'
    p_members_id    = db.Column(db.Integer, primary_key=True)
    member_id       = db.Column(db.Integer, db.ForeignKey('members.member_id'))
    role            = db.Column(db.String(255))
    generated_code  = db.Column(db.String(255))
    assigned_date   = db.Column(db.DateTime, default=datetime.utcnow)

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
    created_on        = db.Column(db.DateTime, default=datetime.utcnow)

class Notes(db.Model):
    __tablename__ = 'notes_tbl'
    notes_id      = db.Column(db.Integer, primary_key=True)
    note_body     = db.Column(db.Text, nullable=False)
    member_id     = db.Column(db.Integer, db.ForeignKey('members.member_id')) # Added this to track who wrote it
    created_on    = db.Column(db.DateTime, default=datetime.utcnow)

    
# from datetime import datetime
# from itsdangerous import URLSafeTimedSerializer as Serializer
# from flask import current_app
# from app import db, login_manager
# from flask_login import UserMixin

# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(int(user_id))

# # --- ORGANIZATION TABLES ---

# class Department(db.Model):
#     id              = db.Column(db.Integer, primary_key=True)
#     department_name = db.Column(db.String(255), nullable=False)
#     creation_date   = db.Column(db.DateTime, default=datetime.utcnow)
    
#     # Relationships
#     members         = db.relationship('User',    backref='department', lazy=True)
#     projects        = db.relationship('Project', backref='dept',       lazy=True)

# class Deadlines(db.Model):
#     id              = db.Column(db.Integer, primary_key=True)
#     start_date      = db.Column(db.DateTime, nullable=False)
#     end_date        = db.Column(db.DateTime, nullable=False)
#     created_on      = db.Column(db.DateTime, default=datetime.utcnow)
#     flag            = db.Column(db.String(255))
    
#     # Relationships
#     projects        = db.relationship('Project', backref='deadline_info', lazy=True)
#     tasks           = db.relationship('Task',    backref='deadline_info', lazy=True)

# class PrevDateList(db.Model):
#     id                = db.Column(db.Integer, primary_key=True)
#     deadlines_id      = db.Column(db.Integer, db.ForeignKey('deadlines.id'))
#     prev_date_actual  = db.Column(db.DateTime)
#     created_on        = db.Column(db.DateTime, default=datetime.utcnow)

# # --- USER & ACCESS TABLES ---

# class User(db.Model, UserMixin):
#     __tablename__ = 'members' 
    
#     id              = db.Column(db.Integer, primary_key=True)
#     department_id   = db.Column(db.Integer, db.ForeignKey('department.id'))
    
#     username        = db.Column(db.String(20),  unique=True, nullable=False)
#     email           = db.Column(db.String(120), unique=True, nullable=False)
#     password        = db.Column(db.String(60),  nullable=False)
#     name            = db.Column(db.String(255)) 
#     account_type    = db.Column(db.String(255), default='user')
#     image_file      = db.Column(db.String(20),  nullable=False, default='default.jpg')
    
#     # Relationships
#     project_links   = db.relationship('ProjectMembers', backref='member', lazy=True)
#     notes           = db.relationship('Notes',          backref='author', lazy=True)

#     def get_reset_token(self):
#         s = Serializer(current_app.config['SECRET_KEY'])
#         return s.dumps({'user_id': self.id})

#     @staticmethod
#     def verify_reset_token(token, expires_sec=1800):
#         s = Serializer(current_app.config['SECRET_KEY'])
#         try:
#             user_id = s.loads(token, max_age=expires_sec)['user_id']
#         except Exception:
#             return None
#         return User.query.get(user_id)

#     def __repr__(self):
#         return f"User('{self.username}', '{self.email}')"

# # --- PROJECT & TASK TABLES ---

# class Project(db.Model):
#     id                 = db.Column(db.Integer, primary_key=True)
#     department_id      = db.Column(db.Integer, db.ForeignKey('department.id'))
#     project_manager_id = db.Column(db.Integer, db.ForeignKey('members.id'))
#     deadlines_id       = db.Column(db.Integer, db.ForeignKey('deadlines.id'))
    
#     client_name        = db.Column(db.String(255))
#     project_status     = db.Column(db.String(255))
#     progress           = db.Column(db.String(255))
    
#     # Relationships
#     tasks              = db.relationship('Task',           backref='project', lazy=True)
#     members            = db.relationship('ProjectMembers', backref='project', lazy=True)

# class ProjectMembers(db.Model):
#     id             = db.Column(db.Integer, primary_key=True)
#     member_id      = db.Column(db.Integer, db.ForeignKey('members.id'))
#     project_id     = db.Column(db.Integer, db.ForeignKey('project.id'))
    
#     role           = db.Column(db.String(255))
#     generated_code = db.Column(db.String(255))
#     assigned_date  = db.Column(db.DateTime, default=datetime.utcnow)

# class Task(db.Model):
#     __tablename__ = 'task_tbl'
    
#     id               = db.Column(db.Integer, primary_key=True)
#     deadline_id      = db.Column(db.Integer, db.ForeignKey('deadlines.id'))
#     project_id       = db.Column(db.Integer, db.ForeignKey('project.id'))
#     p_members_id     = db.Column(db.Integer, db.ForeignKey('project_members.id'))
    
#     task_name        = db.Column(db.String(255), nullable=False)
#     task_description = db.Column(db.Text)
#     task_status      = db.Column(db.String(255))
    
#     # Relationships
#     subtasks         = db.relationship('SubTask', backref='parent_task', lazy=True)
#     notes            = db.relationship('Notes',   backref='task',        lazy=True)

# class SubTask(db.Model):
#     __tablename__ = 'sub_task_list'
    
#     id             = db.Column(db.Integer, primary_key=True)
#     parent_task_id = db.Column(db.Integer, db.ForeignKey('task_tbl.id'))
    
#     subtask_name   = db.Column(db.String(255))
#     status         = db.Column(db.String(255))
#     is_checked     = db.Column(db.Boolean, default=False)

# class Notes(db.Model):
#     __tablename__ = 'notes_tbl'
    
#     id          = db.Column(db.Integer, primary_key=True)
#     task_id     = db.Column(db.Integer, db.ForeignKey('task_tbl.id'))
#     member_id   = db.Column(db.Integer, db.ForeignKey('members.id'))
    
#     note_body   = db.Column(db.Text, nullable=False)
#     created_on  = db.Column(db.DateTime, default=datetime.utcnow)