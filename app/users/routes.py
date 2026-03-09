from flask import render_template, url_for, flash, redirect, request, Blueprint, current_app, jsonify
from app import db, bcrypt, mail
from app.users.forms import RegisterForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateAccountForm, ChangePasswordForm
from app.models import User, Department, Notes, Task, Notification
from app.utils.notification_helpers import (
    notification_action_url as _notification_action_url,
    notification_link_text as _notification_link_text,
    notification_type_badge as _notification_type_badge,
    time_ago as _time_ago,
)
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy.orm import joinedload
from datetime import datetime
from flask_mail import Message
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
        current_user.department_id = form.department.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('users.profile'))
    
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.department.data = current_user.department_id

    change_password_form = ChangePasswordForm()
    return render_template('profile.html', form=form, change_password_form=change_password_form, dept_name=dept_name, departments=departments)

@users.route("/profile/change_password", methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
        db.session.commit()
        flash('Your password has been updated.', 'success')
    else:
        for field, errors in form.errors.items():
            for err in errors:
                flash(err, 'danger')
    return redirect(url_for('users.profile'))

# --- MEMBERS LIST (PAGINATED) ---

@users.route("/delete_member/<int:member_id>", methods=['GET','POST'])
@login_required
def delete_member(member_id):
    if current_user.account_type != 'admin':
        flash('Unauthorized.', 'danger_error')
        return redirect(url_for('main.members'))
    
    member = User.query.get_or_404(member_id)

    db.session.delete(member)
    db.session.commit()

    flash('Member deleted.', 'delete_success')
    return redirect(url_for('main.members'))

@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('project.projects'))

    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_request'))

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
        return redirect(url_for('main.members'))
        
    member = User.query.get_or_404(member_id)
    
    new_username = request.form.get('username')
    new_email = request.form.get('email')

    existing_user = User.query.filter(User.username == new_username, User.member_id != member_id).first()
    if existing_user:
        flash('The username is already taken!', 'modal_error')
        return redirect(url_for('main.members'))

    existing_email = User.query.filter(User.email == new_email, User.member_id != member_id).first()
    if existing_email:
        flash('The email is already in use!', 'modal_error')
        return redirect(url_for('main.members'))

    member.name = request.form.get('name')
    member.username = new_username
    member.email = new_email
    
    dept_id = request.form.get('department')
    if dept_id:
        member.department_id = int(dept_id)

    db.session.commit()
    flash(f'Updated {member.name}!', 'update_success')
    return redirect(url_for('main.members'))
@users.route("/reset_password", methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        current_user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.profile'))
    return render_template('profile.html', title='Reset Password', form=form)


# --- NOTIFICATIONS PAGE ---

@users.route("/notifications")
@login_required
def notifications():
    q = (Notification.query
         .filter_by(recipient_id=current_user.member_id)
         .options(joinedload(Notification.sender))
         .order_by(Notification.created_at.desc())
         .limit(100))
    raw = q.all()
    notifications_list = []
    for n in raw:
        badge_label, badge_class = _notification_type_badge(n.module)
        sender_name = (n.sender.name or n.sender.username) if n.sender else 'System'
        notifications_list.append({
            'notif': n,
            'sender_name': sender_name,
            'action_url': _notification_action_url(n),
            'link_text': _notification_link_text(n),
            'badge_label': badge_label,
            'badge_class': badge_class,
            'time_ago': _time_ago(n.created_at),
        })
    return render_template(
        'notifications.html',
        title='Notifications',
        notifications=notifications_list
    )


# --- NOTIFICATION API ---

@users.route("/api/notifications")
@login_required
def api_notifications():
    """JSON: list recent notifications for current user."""
    limit = min(int(request.args.get('limit', 20)), 50)
    q = (Notification.query
         .filter_by(recipient_id=current_user.member_id)
         .options(joinedload(Notification.sender))
         .order_by(Notification.created_at.desc())
         .limit(limit))
    items = []
    for n in q.all():
        sender_name = (n.sender.name or n.sender.username) if n.sender else 'System'
        items.append({
            'notif_id': n.notif_id,
            'module': n.module,
            'event_type': n.event_type,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat() if n.created_at else None,
            'sender_name': sender_name,
            'action_url': _notification_action_url(n),
            'link_text': _notification_link_text(n),
        })
    return jsonify(notifications=items)


@users.route("/api/notifications/unread-count")
@login_required
def api_notifications_unread_count():
    """JSON: unread notification count for current user."""
    count = Notification.query.filter_by(
        recipient_id=current_user.member_id,
        is_read=False
    ).count()
    return jsonify(unread_count=count)


@users.route("/api/notifications/<int:notif_id>/mark-read", methods=['POST'])
@login_required
def api_notification_mark_read(notif_id):
    n = Notification.query.filter_by(
        notif_id=notif_id,
        recipient_id=current_user.member_id
    ).first_or_404()
    n.is_read = True
    n.read_at = datetime.utcnow()
    db.session.commit()
    return jsonify(success=True)


@users.route("/api/notifications/due-soon-check", methods=['POST'])
@login_required
def api_notifications_due_soon_check():
    """Create due_soon and overdue notifications for tasks and projects. Admin only. Call via cron daily."""
    if getattr(current_user, 'account_type', None) != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    from app.services.notification_service import (
        create_due_soon_notifications,
        create_overdue_notifications,
        create_project_upcoming_deadline_notifications,
    )
    create_due_soon_notifications(days_ahead=3)
    create_project_upcoming_deadline_notifications(days_ahead=3)
    create_overdue_notifications()
    db.session.commit()
    return jsonify(success=True)


@users.route("/api/notifications/mark-all-read", methods=['POST'])
@login_required
def api_notifications_mark_all_read():
    Notification.query.filter_by(
        recipient_id=current_user.member_id,
        is_read=False
    ).update({'is_read': True, 'read_at': datetime.utcnow()})
    db.session.commit()
    return jsonify(success=True)
