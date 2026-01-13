from flask import render_template, url_for, flash, redirect, request, Blueprint
from app import db, bcrypt, mail
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm
from app.models import User, Department 
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

users = Blueprint('users', __name__)

# -------------------- REGISTER --------------------
@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))

    form = RegisterForm()

    # 1. Fetch the departments from the DB
    all_depts = Department.query.all()
    
    # 2. Populate the dropdown choices
    if not all_depts:
        # Fallback in case seed.py wasn't run
        form.department.choices = [(0, "No Departments Found - Run seed.py")]
    else:
        # This creates a list of tuples: (ID, Name) for the dropdown
        form.department.choices = [(d.department_id, d.department_name) for d in all_depts]

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        user = User(
            name=form.name.data, 
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            department_id=form.department.data, # This takes the ID from the selected option
            account_type='user',
            image_file='default.jpg'
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created!', 'success')
            return redirect(url_for('users.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Database Error: {e}")
            flash('An error occurred while saving to the database.', 'danger')

    return render_template('auth-register.html', title='Register', form=form)

# -------------------- LOGIN --------------------
@users.route("/")
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

# -------------------- LOGOUT (ADDED THIS BACK) --------------------
@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('users.login'))

# -------------------- PROFILE --------------------
@users.route("/profile")
@login_required
def profile():
    return render_template('profile.html', title='Profile')

# -------------------- PASSWORD RESET --------------------
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message(
        'Password Reset Request',
        sender='noreply@ashgard-todo.com',
        recipients=[user.email]
    )
    reset_url = url_for('users.reset_token', token=token, _external=True)
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email and no changes will be made.
'''
    mail.send(msg)

@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('If an account with that email exists, an email has been sent.', 'info')
        return redirect(url_for('users.login'))

    return render_template('auth-recoverpw.html', title='Reset Password', form=form)

@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))

    return render_template('reset_token.html', title='Reset Password', form=form)