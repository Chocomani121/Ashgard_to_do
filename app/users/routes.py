from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app
from app import db, bcrypt, mail
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm
from app.models import User
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from app.models import Department, User 
import os
import secrets
from PIL import Image


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
            print(f"DATABASE ERROR: {e}")
            flash('An error occurred. Please try a different username or email.', 'danger')

    # This handles the 'silent refresh' by showing you errors in the terminal
    if request.method == 'POST' and not form.validate():
        print(f"DEBUG - Form Validation Failed: {form.errors}")

    return render_template('auth-register.html', title='Register', form=form)
    
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

@users.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # Update user info (Note: we usually don't update department here if it's seeded/fixed)
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
            
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('users.profile'))
    
    elif request.method == 'GET':
        # Pre-fill the form
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.email.data = current_user.email
        
        # Pull the seeded department name from your relationship
        if current_user.dept_info:
            form.department.data = current_user.dept_info.department_name
            
    return render_template('profile.html', form=form)
    

@users.route("/profile/update", methods=['POST'])
@login_required
def update_profile():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # Alter the database record for the logged-in user
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        # If you have the save_picture function ready:
        # if form.picture.data:
        #     picture_file = save_picture(form.picture.data)
        #     current_user.image_file = picture_file

        db.session.commit() 
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('users.profile'))
    
    # Show validation errors (like "Username already taken")
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", 'danger')

    return redirect(url_for('users.profile'))

@users.route("/members")
@login_required
def members():
    # Fetch all users from the 'members' table
    all_members = User.query.all()
    return render_template('members.html', title='Members', members=all_members)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    # Define folder path
    dirname = os.path.join(current_app.root_path, 'static/profile_pics',)
    
    # Create the directory if it doesn't exist
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        
    picture_path = os.path.join(dirname, picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@login_required
def update_profile():
    form = UpdateAccountForm() # Ensure this matches your Form class name
    if form.validate_on_submit():
        if form.picture.data:
            # Save the new picture and get the filename
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        
        # Update text fields
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.name = form.name.data
        
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.profile'))
    
    # If validation fails
    flash('Update failed. Please check your data.', 'danger')
    return redirect(url_for('users.profile'))