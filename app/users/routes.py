from flask import render_template, url_for, flash, redirect, request, Blueprint
from app import db, bcrypt, mail
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from app.models import Department, User 

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))

    form = RegisterForm()
    
    # Refresh choices from the DB so the list is never empty
    all_departments = Department.query.all()
    form.department.choices = [(d.department_id, d.department_name) for d in all_departments]

    if form.validate_on_submit():
        # 1. Hash the password for security
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        # 2. Create the User instance matching your models.py columns
        user = User(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            department_id=form.department.data,
            account_type='user' # Defaulting as per your model
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('users.login'))
        except Exception as e:
            db.session.rollback()
            # This will show you if there's a specific DB error like a duplicate email
            print(f"DATABASE ERROR: {e}")
            flash('An error occurred. Please try a different username or email.', 'danger')

    # This handles the 'silent refresh' by showing you errors in the terminal
    if request.method == 'POST' and not form.validate():
        print(f"DEBUG - Form Validation Failed: {form.errors}")

    return render_template('auth-register.html', title='Register', form=form)
    
# @users.route("/register", methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('users.login'))

#     form = RegisterForm()
#     departments = Department.query.all()
#     form.department.choices = [(d.department_id, d.department_name) for d in departments]

#     if form.validate_on_submit():
        
#         try:
#             db.session.add(user)
#             db.session.commit()
#             flash('Your account has been created!', 'success')
#             return redirect(url_for('users.login'))
#         except Exception as e:
#             db.session.rollback()
#             print(f"Database Error: {e}")
#             flash('Database Error', 'danger')

    
#     if form.errors:
#         print(f"DEBUG - Form Errors: {form.errors}")

    # return render_template('auth-register.html', title='Register', form=form)

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

# -------------------- LOGOUT --------------------
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
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
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