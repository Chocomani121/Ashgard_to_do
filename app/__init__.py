from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# 1. Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__)
    
    # 2. Configuration
    app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    # 3. Link extensions to the app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # 4. Import and Register Blueprints (Crucial step!)
    from .users.routes import users as users_blueprint
    from .main.routes import main as main_blueprint
    
    app.register_blueprint(users_blueprint)
    app.register_blueprint(main_blueprint)

    return app

    