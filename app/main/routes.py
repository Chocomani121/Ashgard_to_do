from flask import render_template, request, Blueprint

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/login") 
def login():
    return render_template('auth-login.html')

@main.route("/projects") 
def projects():
    return render_template('index.html')

@main.route("/tasks") 
def tasks():
    return render_template('tasks.html', title="Tasks Info")

@main.route("/members")
def members():
    return render_template('members.html', title="Members")


@main.route("/register") 
def register():
    return render_template('auth-register.html')

@main.route("/forgot-password")
def forgot_password():
    return render_template('auth-recoverpw.html')

@main.route("/project_details")
def project_details():
    return render_template('project_details.html')

@main.route("/profile")
def profile():
    return render_template('profile.html')

@main.route("/all_departments")
def all_departments():
    return render_template('all_division.html')
# from flask import render_template, url_for, flash, redirect, request, Blueprint
# from flask_login import login_user, current_user, logout_user, login_required
# from flaskblog import db, bcrypt
# from flaskblog.models import User, Post
# from flaskblog.users.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
#                                    RequestResetForm, ResetPasswordForm)
# from flaskblog.users.utils import save_picture, send_reset_email
