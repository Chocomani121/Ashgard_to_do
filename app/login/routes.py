from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app
from app import db, bcrypt, mail
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm
from app.models import User, Department, Notes, Task, Project

from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from sqlalchemy.orm import joinedload

import os
import secrets
from PIL import Image

auth_bp = Blueprint('auth', __name__, template_folder='templates', static_folder='static', static_url_path='/auth/static')


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@ashgard-todo.com', recipients=[user.email])
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    msg.body = f"To reset your password, visit: {reset_url}"
    mail.send(msg)

@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.projects'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('project.projects'))
        form.email.errors.append('Invalid email or password.')

    return render_template('auth/auth-login.html', title='Login', form=form)

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.projects'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, username=form.username.data, email=form.email.data, 
                    password=hashed_password, account_type='user')
        db.session.add(user)
        db.session.commit()
        flash('Account created!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth-register.html', title='Register', form=form)

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('auth.projects'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('An email has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth-recoverpw.html', title='Reset Password', form=form)