from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app
from app import db, bcrypt, mail
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm
from app.models import User, Department
from flask_login import login_user, current_user, logout_user, login_required
import os
import secrets
from PIL import Image

users = Blueprint('users', __name__)

# --- AUTHENTICATION ---

@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.projects'))
    form = RegisterForm()
    all_departments = Department.query.all()
    form.department.choices = [(d.department_id, d.department_name) for d in all_departments]
    
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            name=form.name.data,
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            department_id=form.department.data,
            account_type='admin'
        )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'success')
        return redirect(url_for('users.login'))
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
        flash('Login Unsuccessful.', 'danger')
    return render_template('auth-login.html', title='Login', form=form)

@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('users.login'))

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
    if form.validate_on_submit():
        if form.picture.data:
            old_pic = current_user.image_file
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
    return render_template('profile.html', form=form)

# --- MEMBERS LIST (PAGINATED) ---

@users.route("/members")
@login_required
def members():
    page = request.args.get('page', 1, type=int)
    # This pagination object contains the logic for your HTML loop
    pagination = User.query.order_by(User.name.asc()).paginate(page=page, per_page=10)
    
    return render_template('members.html', 
                           title='Members',
                           members=pagination.items, 
                           pagination=pagination, 
                           total_users=User.query.count())

@users.route("/delete_member/<int:member_id>", methods=['POST'])
@login_required
def delete_member(member_id):
    if current_user.account_type != 'admin':
        flash('Unauthorized.', 'danger')
        return redirect(url_for('users.members'))
    
    member = User.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted.', 'success')
    return redirect(url_for('users.members'))