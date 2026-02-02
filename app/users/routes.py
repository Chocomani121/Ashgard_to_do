from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app
from app import db, bcrypt, mail, cache
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm
from app.models import User, Department, Report
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
        return redirect(url_for('main.projects'))

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
        return redirect(url_for('main.projects'))

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
        return redirect(url_for('main.projects'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.projects'))
        
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
        return redirect(url_for('main.projects'))

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


@users.route("/reports/delete/<int:report_id>")
@login_required
def delete_report(report_id):
    # Import inside to prevent circular dependency
    from app.models import Report, ReportCC 
    
    report = Report.query.get_or_404(report_id)
    
    # Check if the current user is the author
    # Note: current_user works because it's an instance of the User class
    if report.member_id != current_user.member_id:
        flash("You do not have permission to delete this report.", "danger")
        return redirect(url_for('main.reports'))
    
    try:
        # Since you added cascade="all, delete-orphan" in models.py, 
        # SQLAlchemy will automatically delete CC entries and Comments!
        db.session.delete(report)
        db.session.commit()
        flash("Report deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting report: {str(e)}", "danger")
        
    return redirect(url_for('main.reports'))

def _report_to_dict(report):
    return {
        'report_id': report.report_id,
        'week_name': report.week_name,
        'report_content': report.report_content,
        'reviewer_id': report.reviewer_id,
        'author_name': report.author.name,
        # This is the crucial line for the CC list populate:
        'cc_member_ids': [cc.member_id for cc in report.cc_entries]
    }

@users.route("/reports/edit/<int:report_id>", methods=['POST'])
@login_required
def edit_report(report_id):
    from app.models import Report, ReportCC
    
    # 1. Fetch the existing report
    report = Report.query.get_or_404(report_id)

    # 2. Security: Ensure the user is actually the author
    if report.member_id != current_user.member_id:
        flash("You do not have permission to edit this report.", "danger")
        return redirect(url_for('main.reports'))

    try:
        # 3. Update the main fields from the form
        report.week_name = request.form.get('report_date')
        report.report_content = request.form.get('reportBody')
        report.reviewer_id = request.form.get('reviewer_id')
        
        # Optional: Reset "checked" status so it needs new approval after edit
        report.is_checked = False 

        # 4. Update CC Members (Delete old ones and add new ones)
        ReportCC.query.filter_by(report_id=report_id).delete()
        cc_ids = request.form.getlist('cc_members')
        for m_id in cc_ids:
            if m_id:
                new_cc = ReportCC(report_id=report_id, member_id=int(m_id))
                db.session.add(new_cc)

        db.session.commit()
        flash("Report updated successfully!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating report: {str(e)}", "danger")

    return redirect(url_for('main.reports'))