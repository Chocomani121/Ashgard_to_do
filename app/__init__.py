import os
import urllib.parse
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

load_dotenv()

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
# Changed from 'users.login' to 'auth.login'
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
login_manager.login_message = None
mail = Mail()
migrate = Migrate()

def create_app():
    # Renamed to flask_app to avoid "AttributeError: module 'app' has no attribute..."
    flask_app = Flask(__name__)

    flask_app.config["CACHE_TYPE"] = "FileSystemCache"
    flask_app.config["CACHE_DIR"] = "flask_cache"
    flask_app.config["CACHE_DEFAULT_TIMEOUT"] = 300

    # --- DATABASE CONFIG ---
    user = os.getenv("DB_USER")
    raw_password = str(os.getenv("DB_PASSWORD", "")) 
    password = urllib.parse.quote_plus(raw_password)
    host = os.getenv("DB_HOST")
    
    db_port = os.getenv("DB_PORT")
    port = int(db_port) if db_port and db_port.isdigit() else 16751 
    
    db_name = os.getenv("DB_NAME")

    flask_app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    flask_app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # --- MAIL CONFIG ---
    flask_app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.googlemail.com")
    m_port = os.getenv("MAIL_PORT")
    flask_app.config["MAIL_PORT"] = int(m_port) if m_port and m_port.isdigit() else 587
    
    flask_app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    flask_app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    flask_app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

    db.init_app(flask_app)
    bcrypt.init_app(flask_app)
    login_manager.init_app(flask_app)
    mail.init_app(flask_app)
    migrate.init_app(flask_app, db)

    @flask_app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    # --- CONTEXT PROCESSOR FOR APPROVALS ---
    
    @flask_app.context_processor
    def inject_show_approvals():
        from flask_login import current_user
        from app.models import Project, Task, SubTask
        show_approvals_in_navbar = False
        approvals_pending_count = 0
        if current_user.is_authenticated:
            pm_project_ids = [p.project_id for p in Project.query.filter_by(
                project_manager=current_user.member_id
            ).with_entities(Project.project_id).all()]
            if pm_project_ids:
                show_approvals_in_navbar = True
                task_ids = [t.task_id for t in Task.query.filter(
                    Task.project_id.in_(pm_project_ids)
                ).with_entities(Task.task_id).all()]
                if task_ids:
                    approvals_pending_count = SubTask.query.filter(
                        SubTask.parent_task_id.in_(task_ids),
                        SubTask.status.in_(('To be reviewed', 'On Hold', 'Rejected'))
                    ).count()
        return {
            'show_approvals_in_navbar': show_approvals_in_navbar,
            'approvals_pending_count': approvals_pending_count
        }

    # --- BLUEPRINT REGISTRATION ---
    
    # 1. Import the Blueprint objects first
    from app.login.routes import auth_bp as auth_bp
    from .users.routes import users as users_blueprint
    from .main.routes import main as main_blueprint
    from app.features.reports.routes import reports_bp  as reports_blueprint
    from app.features.projects.routes import project_bp as project_blueprint
    from app.features.department.routes import department_bp as department_blueprint

    # 2. IMPORTANT: Import routes BEFORE registering the blueprint 
    # This prevents the "AssertionError: The setup method 'route' can no longer be called"
    # import app.login.routes 
    
    # 3. Register them on the flask_app instance
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(users_blueprint)
    flask_app.register_blueprint(main_blueprint)
    flask_app.register_blueprint(reports_blueprint)
    flask_app.register_blueprint(project_blueprint)
    flask_app.register_blueprint(department_blueprint)

    return flask_app
