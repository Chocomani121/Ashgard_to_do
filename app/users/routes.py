from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app
from app import db, bcrypt, mail, cache
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm
from app.models import User, Department, Notes, Task
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from sqlalchemy.orm import joinedload

# Look for your existing imports at the top of app/users/routes.py


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
        return redirect(url_for('users.login'))
    
    # Points ONLY to the admin template
    return render_template('auth-register-admin.html', title='Register Admin', form=form)

# 2. USER REGISTRATION
@users.route("/register", methods=['GET', 'POST'])
def register():
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
            account_type='user'  # Hardcoded specifically for this route
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('users.login'))
    
    # Points ONLY to the standard user template
    return render_template('auth-register.html', title='Register', form=form)

@users.route("/")
@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('project.projects'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('project.projects'))
        
        form.email.errors.append('Invalid email or password.')
        
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
@cache.cached(timeout=60)
def members():
    members = User.query.order_by(User.name.asc()).all()
    departments = Department.query.order_by(Department.department_name.asc()).all()

    return render_template(
        'members.html',
        title='Members',
        members=members,
        departments=departments,
        total_users=len(members)
    )

@users.route("/delete_member/<int:member_id>", methods=['GET','POST'])
@login_required
def delete_member(member_id):
    if current_user.account_type != 'admin':
        flash('Unauthorized.', 'danger_error')
        return redirect(url_for('users.members'))
    
    member = User.query.get_or_404(member_id)

    db.session.delete(member)
    db.session.commit()

    cache.clear()

    flash('Member deleted.', 'delete_success')
    return redirect(url_for('users.members'))

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
        return redirect(url_for('project.projects'))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))

    return render_template('auth-recoverpw.html', title='Reset Password', form=form)

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
        return redirect(url_for('users.login'))

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


# Project Details Notes_tbl - Reply, Comment, Edit
@users.route("/project/note/add", methods=['POST'])
@login_required
def add_note():
    from app.models import Notes # Plural class name
    
    # 1. Get the data from the HTML form names
    task_id = request.form.get('task_id')
    body = request.form.get('note_body')
    title = request.form.get('note_title')
    
    # 2. Basic validation
    if not body or not task_id:
        flash("Note body cannot be empty.", "danger")
        return redirect(request.referrer)

    # 3. Create the database object
    new_note = Notes(
        task_id=int(task_id),
        member_id=current_user.member_id,
        note_body=body,
        generated_code=title, # Saving 'Notes Title' here
        reply_code=None
    )
    
    try:
        db.session.add(new_note)
        db.session.commit()
        flash("Note added successfully!", "success")
    except Exception as e:
        db.session.rollback()
        print(f"DEBUG ERROR: {e}") # This shows up in your terminal
        flash("Failed to save note.", "danger")

    return redirect(request.referrer)


@users.route("/task_details/<int:task_id>")
@login_required
def task_details(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Fetch all notes for this task
    all_notes = Notes.query.filter_by(task_id=task_id).order_by(Notes.created_on.asc()).all()
    
    # Separate main notes from replies
    # Main notes have no reply_code (or it's empty)
    main_notes = [n for n in all_notes if not n.reply_code]
    
    # Create a dictionary to group replies by their parent_id
    replies_map = {}
    for n in all_notes:
        if n.reply_code:
            parent_id = int(n.reply_code)
            if parent_id not in replies_map:
                replies_map[parent_id] = []
            replies_map[parent_id].append(n)
    
    return render_template('task_details.html', 
                           task=task, 
                           notes=main_notes, 
                           replies_map=replies_map)

@users.route("/task/note/reply/<int:note_id>", methods=['POST'])
@login_required
def reply_note(note_id):
    body = request.form.get('reply_body')
    task_id = request.form.get('task_id')
    
    new_reply = Notes(
        task_id=int(task_id),
        member_id=current_user.member_id,
        note_body=body,
        reply_code=str(note_id)  # Store the parent ID here
    )
    
    db.session.add(new_reply)
    db.session.commit()
    return redirect(request.referrer)