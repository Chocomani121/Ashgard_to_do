from flask import render_template, url_for, flash, redirect, request
from app import db, bcrypt, mail
from app.login import auth 
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm
from app.models import User
from flask_login import login_user, current_user, logout_user
from flask_mail import Message


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@ashgard-todo.com', recipients=[user.email])
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    msg.body = f"To reset your password, visit: {reset_url}"
    mail.send(msg)

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.projects'))
        form.email.errors.append('Invalid email or password.')
    return render_template('auth/auth-login.html', title='Login', form=form)

@auth.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, username=form.username.data, email=form.email.data, 
                    password=hashed_password, account_type='user')
        db.session.add(user)
        db.session.commit()
        flash('Account created!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/auth-register.html', title='Register', form=form)

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('An email has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/auth-recoverpw.html', title='Reset Password', form=form)