import urllib.parse 
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate 


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
login_manager.login_message = None
mail = Mail()
migrate = Migrate() 

def create_app():
    app = Flask(__name__)
    
   
    user = 'testman'
   
    password = urllib.parse.quote_plus('Jhayg3309]]:P') 
    mysql_url = 'vultr-prod-85f8d360-5bbf-4d05-ad2d-01cc47768728-vultr-prod-995c.vultrdb.com'
    port_num = '16751'
    db_name = 'sample_crud'

    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{user}:{password}@{mysql_url}:{port_num}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    

    app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'

    
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'dr.strangex404@gmail.com'
    app.config['MAIL_PASSWORD'] = 'iwzt upks azcd laux'

    
    db.init_app(app)
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
    
    app.register_blueprint(users_blueprint)
    app.register_blueprint(main_blueprint)

    return app