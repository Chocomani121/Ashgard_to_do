import os
import urllib.parse
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_caching import Cache

load_dotenv()

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
login_manager.login_message = None
mail = Mail()
migrate = Migrate()
cache = Cache()

def create_app():
    app = Flask(__name__)


    app.config["CACHE_TYPE"] = "FileSystemCache"
    app.config["CACHE_DIR"] = "flask_cache"  # Folder for cache files
    app.config["CACHE_DEFAULT_TIMEOUT"] = 300 # 5-minute default

    # --- DATABASE CONFIG ---
    user = os.getenv("DB_USER")
    # Force string conversion to handle the special characters in your password safely
    raw_password = str(os.getenv("DB_PASSWORD", "")) 
    password = urllib.parse.quote_plus(raw_password)
    host = os.getenv("DB_HOST")
    
    # Safely handle the Port conversion
    db_port = os.getenv("DB_PORT")
    port = int(db_port) if db_port and db_port.isdigit() else 16751 # Vultr default from your .env
    
    db_name = os.getenv("DB_NAME")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # --- MAIL CONFIG ---
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.googlemail.com")
    
    # Safely handle Mail Port
    m_port = os.getenv("MAIL_PORT")
    app.config["MAIL_PORT"] = int(m_port) if m_port and m_port.isdigit() else 587
    
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")

    db.init_app(app)
    cache.init_app(app)

 
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    @app.after_request
    def add_header(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    from .users.routes import users as users_blueprint
    from .main.routes import main as main_blueprint
    from app.features.reports.routes import reports_bp  as reports_blueprint
    from app.features.projects.routes import project_bp as project_blueprint
    from app.features.department.routes import department_bp as department_blueprint

    app.register_blueprint(users_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(reports_blueprint)
    app.register_blueprint(project_blueprint)
    app.register_blueprint(department_blueprint)
    
    return app
