from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app
from app import db, bcrypt, mail
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm
from app.models import User, Department, Notes, Task
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from sqlalchemy.orm import joinedload
import os
import secrets
from PIL import Image

users = Blueprint('users', __name__)

# 1. ADMIN REGISTRATION
@users.route("/admin_register", methods=['GET', 'POST'])
def admin_register():
    if current_user.is_authenticated:
        return redirect(url_for('project.projects'))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            account_type='admin' 
        )
        db.session.add(user)
        db.session.commit()
        flash('Admin account created!', 'success')
        return redirect(url_for('auth.login'))
    
    # Points ONLY to the admin template
    return render_template('auth-register-admin.html', title='Register Admin', form=form)

# --- PROFILE & PICTURES ---

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    dirname = os.path.join(current_app.root_path, 'static/profile_pics')
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    picture_path = os.path.join(dirname, picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@users.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateAccountForm()
    
    # Fetch the department name for the current user
    user_dept = Department.query.get(current_user.department_id)
    dept_name = user_dept.department_name if user_dept else "No Department Assigned"
    departments = Department.query.all()
    if form.validate_on_submit():
        if form.picture.data:
            current_user.image_file = save_picture(form.picture.data)
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('users.profile'))
    
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.department.data = current_user.department_id
        # We don't set form.department because you want it to be static text
        
    return render_template('profile.html', form=form, dept_name=dept_name, departments=departments)

# --- MEMBERS LIST (PAGINATED) ---

@users.route("/delete_member/<int:member_id>", methods=['GET','POST'])
@login_required
def delete_member(member_id):
    if current_user.account_type != 'admin':
        flash('Unauthorized.', 'danger_error')
        return redirect(url_for('users.members'))
    
    member = User.query.get_or_404(member_id)

    db.session.delete(member)
    db.session.commit()

    flash('Member deleted.', 'delete_success')
    return redirect(url_for('users.members'))

@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('project.projects'))

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
        return redirect(url_for('auth.login'))

    return render_template('reset_token.html', title='Reset Password', form=form)


# 3. ADMIN UPDATING A MEMBER'S DETAILS
@users.route("/admin/update/member/<int:member_id>", methods=['POST'])
@login_required
def update_member(member_id):
    if current_user.account_type != 'admin':
        flash('Unauthorized!', 'danger_error')
        return redirect(url_for('users.members'))
        
    member = User.query.get_or_404(member_id)
    
    new_username = request.form.get('username')
    new_email = request.form.get('email')

    existing_user = User.query.filter(User.username == new_username, User.member_id != member_id).first()
    if existing_user:
        flash('The username is already taken!', 'modal_error')
        return redirect(url_for('users.members'))

    existing_email = User.query.filter(User.email == new_email, User.member_id != member_id).first()
    if existing_email:
        flash('The email is already in use!', 'modal_error')
        return redirect(url_for('users.members'))

    member.name = request.form.get('name')
    member.username = new_username
    member.email = new_email
    
    dept_id = request.form.get('department')
    if dept_id:
        member.department_id = int(dept_id)

    db.session.commit()
    flash(f'Updated {member.name}!', 'update_success')
    return redirect(url_for('users.members'))
