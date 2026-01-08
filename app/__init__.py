from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail  # <--- NEW IMPORT

# 1. Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()  # <--- INITIALIZE MAIL EXTENSION HERE

def create_app():
    app = Flask(__name__)
    
    # 2. Configuration
    app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    # --- MAIL CONFIGURATION ---
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'dr.strangex404@gmail.com' # Your email address
    app.config['MAIL_PASSWORD'] = 'iwzt upks azcd laux'     # Your Gmail App Password
    # ---------------------------

    # 3. Link extensions to the app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)  # <--- LINK MAIL TO APP HERE

    @app.after_request
    def add_header(response):
        # This forces the browser to check the server every time the back button is clicked
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # 4. Import and Register Blueprints
    from .users.routes import users as users_blueprint
    from .main.routes import main as main_blueprint
    
    app.register_blueprint(users_blueprint)
    app.register_blueprint(main_blueprint)

    return app