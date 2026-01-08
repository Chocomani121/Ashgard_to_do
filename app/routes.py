from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from .. import db, bcrypt, login_manager
from ..models import User
from .forms import RegistrationForm, LoginForm # Ensure this matches your forms.py

users = Blueprint('users', __name__)

@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))
    
    # FIX 1: Initialize the form class correctly
    form = RegistrationForm() 
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # FIX 2: Added name=form.username.data to satisfy your DB constraint
        user = User(
            name=form.username.data, 
            username=form.username.data, 
            email=form.email.data, 
            password=hashed_password
        )
        
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    
    return render_template('auth-register.html', title='Register', form=form)

@users.route("/login", methods=['GET', 'POST'])
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
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth-login.html', title='Login', form=form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('users.login'))

@users.route("/account")
@login_required  # This forces a redirect to 'login' if user isn't logged in
def account():
    # Fixed the typo in your render_template call (removed double title and wrong template)
    return render_template('account.html', title='Account')