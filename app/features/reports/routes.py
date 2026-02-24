from flask import render_template, Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, Report, ReportCC, Comment, Project, Task, Deadlines, ProjectMembers, TaskAssignee, SubTask, Notes, Department
from app import db, main 
from datetime import datetime, date, time
from sqlalchemy import or_, text
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.orm import joinedload, selectinload
import json
import random

reports_bp = Blueprint('reports', __name__, template_folder='templates', static_folder='static', static_url_path='/reports/static')


def _format_week_range(week_name):
    """Convert week_name like '2/17/2026 - 2/23/2026' to 'February 17, 2026 – February 23, 2026'."""
    if not week_name or not isinstance(week_name, str):
        return week_name or '—'
    try:
        parts = week_name.split(' - ')
        if len(parts) >= 2:
            d1 = datetime.strptime(parts[0].strip(), '%m/%d/%Y')
            d2 = datetime.strptime(parts[1].strip(), '%m/%d/%Y')
            return f"{d1.strftime('%B %d, %Y')} – {d2.strftime('%B %d, %Y')}"
        elif len(parts) == 1 and parts[0].strip():
            d = datetime.strptime(parts[0].strip(), '%m/%d/%Y')
            return d.strftime('%B %d, %Y')
    except (ValueError, IndexError):
        pass
    return week_name


# ---- Report routes ----
def _report_to_dict(report):

    """Build a dict for one report (list + detail panel)."""
    comments_list = []
    for c in (report.comments or []):
        comment_author = (c.author.name or c.author.username) if c.author else ''
        author_img = getattr(c.author, 'image_file', None) or 'default.jpg'
        comments_list.append({
            'comment_id': c.comment_id,
            'comment_body': c.comment_body or '',
            'created_at': c.created_at.strftime('%m/%d/%Y %H:%M') if c.created_at else '',
            'author_name': comment_author,
            'author_image': author_img,
            'member_id': c.member_id,
            'parent_comment_id': c.parent_comment_id,
            'report_id': report.report_id,
            'week_name': report.week_name,
            'report_content': report.report_content,
            'reviewer_id': report.reviewer_id,
            # This is the crucial line for the CC list populate:
            'cc_member_ids': [cc.member_id for cc in report.cc_entries]
        })

    author_name = (report.author.name or report.author.username) if report.author else ''
    reviewer_name = (report.reviewer_user.name or report.reviewer_user.username) if report.reviewer_user else ''
    cc_names = ', '.join((e.user.name or e.user.username or '') if e.user else '' for e in (report.cc_entries or []))
    dept = getattr(report.author, 'dept_info', None) if report.author else None
    department_name = dept.department_name if dept else ''
    created_str = report.created_on.strftime('%m/%d/%Y %H:%M') if report.created_on else ''

    return {
        'report_id': report.report_id,
        'author_name': author_name,
        'week_name': report.week_name,
        'is_checked': report.is_checked,
        'created_on': created_str,
        'reviewer_name': reviewer_name,
        'cc_names': cc_names,
        'department_name': department_name,
        'report_content': report.report_content or '',
        'is_author': report.member_id == current_user.member_id,
        'is_reviewer': report.reviewer_id == current_user.member_id if report.reviewer_id else False,
        'comments': comments_list,
        'reviewer_id': report.reviewer_id,
        'cc_member_ids': [cc.member_id for cc in (report.cc_entries or [])],
    }

@reports_bp.route("/reports")
@login_required
def reports():
    users = User.query.all()
    users_json = [
        {'member_id': u.member_id, 'name': u.name or u.username, 'username': u.username, 'image': u.image_file}
        for u in users
    ]
    
    report_options = [
        joinedload(Report.author).joinedload(User.dept_info),
        joinedload(Report.reviewer_user),
        selectinload(Report.cc_entries).joinedload(ReportCC.user),
        selectinload(Report.comments).joinedload(Comment.author),
    ]

    if getattr(current_user, 'account_type', None) == 'admin':
        reports_q = (
            Report.query
            .options(*report_options)
            .order_by(Report.created_on.desc())
            .all()
        )
    else:
        reports_q = (
            Report.query
            .options(*report_options)
            .filter(
                or_(
                    Report.member_id == current_user.member_id,
                    Report.reviewer_id == current_user.member_id,
                    Report.report_id.in_(
                        db.session.query(ReportCC.report_id).filter(
                            ReportCC.member_id == current_user.member_id
                        )
                    ),
                )
            )
            .order_by(Report.created_on.desc())
            .all()
        )

    pending_reports = [r for r in reports_q if not r.is_checked]
    reviewed_reports = [r for r in reports_q if r.is_checked]

    if getattr(current_user, 'account_type', None) == 'admin':
        cc_reports = reports_q
        company_wide_reports = reports_q
    else:
        cc_reports = [
            r for r in reports_q
            if r.reviewer_id == current_user.member_id
            or any(cc.member_id == current_user.member_id for cc in (r.cc_entries or []))
        ]
        company_wide_reports = (
            Report.query
            .options(*report_options)
            .order_by(Report.created_on.desc())
            .all()
        )

    reports_json = [_report_to_dict(r) for r in company_wide_reports]

    return render_template(
        'reports.html',
        title="Reports",
        users=users,
        users_json=users_json,
        pending_reports=pending_reports,
        reviewed_reports=reviewed_reports,
        cc_reports=cc_reports,
        company_wide_reports=company_wide_reports,
        reports_json=reports_json,
    )

# ---- create_report routes ----
@reports_bp.route("/reports/create", methods=['POST'])
@login_required
def create_report():
    try:
        # 1. Get Form Data
        # Note: 'report_date' in your HTML maps to 'week_name' in your Model
        week_name = request.form.get('report_date') 
        report_content = request.form.get('reportBody')
        reviewer_id = request.form.get('reviewer_id')
        member_id = current_user.member_id # The Author
        
        # Validation
        if not all([week_name, report_content, reviewer_id]):
            flash('Please complete the report and select a reviewer.', 'danger')
            return redirect(url_for('reports.reports'))

        # 2. Create the Report (report_tbl)
        new_report = Report(
            member_id=int(member_id),
            reviewer_id=int(reviewer_id),
            week_name=week_name,
            report_content=report_content,
            is_checked=False  # Explicitly setting default
        )
        
        db.session.add(new_report)
        db.session.flush()  # Gets the new_report.report_id

        # 3. Create CC Entries (report_cc_tbl)
        cc_member_ids = request.form.getlist('cc_members')
        if cc_member_ids:
            for m_id in cc_member_ids:
                try:
                    cc_entry = ReportCC(
                        report_id=new_report.report_id,
                        member_id=int(m_id)
                    )
                    db.session.add(cc_entry)
                except (ValueError, TypeError):
                    continue

        db.session.commit()
        flash('Weekly report created and sent for review!', 'success')
        return redirect(url_for('reports.reports'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating report: {str(e)}', 'danger')
        return redirect(url_for('reports.reports'))

# ---- Get single report (JSON, for real-time comments polling) ----
@reports_bp.route("/reports/<int:report_id>", methods=['GET'])
@login_required
def get_report(report_id):
    report_options = [
        joinedload(Report.author).joinedload(User.dept_info),
        joinedload(Report.reviewer_user),
        selectinload(Report.cc_entries).joinedload(ReportCC.user),
        selectinload(Report.comments).joinedload(Comment.author),
    ]
    report = Report.query.options(*report_options).filter(Report.report_id == report_id).first()
    if not report:
        return jsonify({'error': 'Report not found'}), 404
    # Same visibility as reports list: author, reviewer, or CC
    if getattr(current_user, 'account_type', None) == 'admin':
        pass
    else:
        is_author = report.member_id == current_user.member_id
        is_reviewer = report.reviewer_id == current_user.member_id
        is_cc = db.session.query(ReportCC).filter(
            ReportCC.report_id == report_id,
            ReportCC.member_id == current_user.member_id
        ).first() is not None
        if not (is_author or is_reviewer or is_cc):
            return jsonify({'error': 'Forbidden'}), 403
    return jsonify(_report_to_dict(report))


# ---- Approve report (reviewer marks as approved) ----
@reports_bp.route("/reports/<int:report_id>/approve", methods=['POST'])
@login_required
def approve_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.reviewer_id != current_user.member_id:
        flash('Only the assigned reviewer can approve this report.', 'danger')
        return redirect(url_for('reports.reports'))
    if report.is_checked:
        flash('This report is already approved.', 'info')
        return redirect(url_for('reports.reports'))
    try:
        report.is_checked = True
        report.checked_at = datetime.utcnow()
        db.session.commit()
        flash('Report approved successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    next_url = request.form.get('next') or request.args.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect(url_for('reports.reports'))


# ---- Add comment to report ----
@reports_bp.route("/reports/<int:report_id>/comment", methods=['POST'])
@login_required
def add_report_comment(report_id):
    report = Report.query.get_or_404(report_id)
    # Optional: restrict to users who can see the report (author, reviewer, or CC)
    data = request.get_json(silent=True) or request.form or {}
    comment_body = data.get('comment_body', '')
    comment_body = (comment_body or '').strip()
    if not comment_body:
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': 'Comment is empty'}), 400
        flash('Comment cannot be empty.', 'warning')
        return redirect(url_for('reports.reports'))
    parent_comment_id = data.get('parent_comment_id')
    if parent_comment_id is not None:
        try:
            parent_comment_id = int(parent_comment_id)
        except (TypeError, ValueError):
            parent_comment_id = None
    if parent_comment_id is not None:
        parent = Comment.query.filter_by(comment_id=parent_comment_id, report_id=report_id).first()
        if not parent:
            parent_comment_id = None
    try:
        comment = Comment(
            report_id=report_id,
            member_id=current_user.member_id,
            comment_body=comment_body,
            parent_comment_id=parent_comment_id
        )
        db.session.add(comment)
        db.session.commit()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            author_name = (current_user.name or current_user.username) or ''
            created_str = comment.created_at.strftime('%m/%d/%Y %H:%M') if comment.created_at else ''
            user_img = getattr(current_user, 'image_file', None) or 'default.jpg'
            return jsonify({
                'success': True,
                'comment_id': comment.comment_id,
                'comment_body': comment.comment_body or '',
                'author_name': author_name,
                'created_at': created_str,
                'user_image': user_img
            })
        flash('Comment added.', 'success')
    except Exception as e:
        db.session.rollback()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 500
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('reports.reports'))


# ---- Update (edit) report comment ----
@reports_bp.route("/reports/<int:report_id>/comments/<int:comment_id>", methods=['PATCH'])
@login_required
def update_report_comment(report_id, comment_id):
    comment = Comment.query.filter_by(comment_id=comment_id, report_id=report_id).first()
    if not comment:
        return jsonify({'success': False, 'error': 'Comment not found'}), 404
    if comment.member_id != current_user.member_id:
        return jsonify({'success': False, 'error': 'You can only edit your own comment'}), 403
    data = request.get_json(silent=True) or {}
    comment_body = (data.get('comment_body') or '').strip()
    if not comment_body:
        return jsonify({'success': False, 'error': 'Comment is empty'}), 400
    try:
        comment.comment_body = comment_body
        db.session.commit()
        return jsonify({
            'success': True,
            'comment_id': comment.comment_id,
            'comment_body': comment.comment_body or ''
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    

# ---- Delete report ----    
@reports_bp.route("/reports/delete/<int:report_id>")
@login_required
def delete_report(report_id):
    
    report = Report.query.get_or_404(report_id)
    
    # Check if the current user is the author
    # Note: current_user works because it's an instance of the User class
    if report.member_id != current_user.member_id:
        flash("You do not have permission to delete this report.", "danger")
        return redirect(url_for('reports.reports'))
    
    try:
        # Since you added cascade="all, delete-orphan" in models.py, 
        # SQLAlchemy will automatically delete CC entries and Comments!
        db.session.delete(report)
        db.session.commit()
        flash("Report deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting report: {str(e)}", "danger")
        
    return redirect(url_for('reports.reports'))

@reports_bp.route("/reports/edit/<int:report_id>", methods=['POST'])
@login_required
def edit_report(report_id):

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

    return redirect(url_for('reports.reports'))


@reports_bp.route("/approvals")
@login_required
def approvals():
    # PENDING reports where current user is reviewer + reports where user is CC
    report_options = [
        joinedload(Report.author).joinedload(User.dept_info),
        joinedload(Report.reviewer_user),
    ]
    # 1. Pending reports where user is reviewer
    reviewer_reports = (
        Report.query
        .options(*report_options)
        .filter(
            Report.reviewer_id == current_user.member_id,
            Report.is_checked == False,
        )
        .order_by(Report.created_on.desc())
        .all()
    )
    # 2. Reports where user is CC (exclude any already in reviewer_reports)
    reviewer_report_ids = {r.report_id for r in reviewer_reports}
    cc_report_ids = (
        db.session.query(ReportCC.report_id)
        .filter(ReportCC.member_id == current_user.member_id)
        .all()
    )
    cc_report_ids = [r[0] for r in cc_report_ids if r[0] not in reviewer_report_ids]
    cc_reports = (
        Report.query.options(*report_options)
        .filter(Report.report_id.in_(cc_report_ids))
        .order_by(Report.created_on.desc())
        .all()
    ) if cc_report_ids else []
    # Combine: reviewer first (with role), then CC (with role)
    reports_with_role = [
        {'report': r, 'role': 'reviewer', 'week_display': _format_week_range(r.week_name)}
        for r in reviewer_reports
    ]
    reports_with_role += [
        {'report': r, 'role': 'cc', 'week_display': _format_week_range(r.week_name)}
        for r in cc_reports
    ]

    users = User.query.all()
    departments = Department.query.all()
    stats = {
        'pending': len(reviewer_reports),
        'high_priority': 0,
        'completed': 0,
        'on_hold': 0,
    }
    users_json = [
        {'member_id': u.member_id, 'name': u.name or u.username, 'username': u.username, 'department_id': u.department_id}
        for u in users
    ]

    return render_template(
        'approvals.html',
        title="Approvals",
        reports_to_review=reports_with_role,
        stats=stats,
        users_json=users_json,
        departments=departments,
        today=date.today(),
    )


@reports_bp.route("/approvals/<int:task_id>/subtask/<int:sub_task_id>/notes", methods=['GET'])
@login_required
def approvals_subtask_notes(task_id, sub_task_id):
    """API: Return notes for a subtask (used by approvals page modal)."""
    task = Task.query.get_or_404(task_id)
    subtask = SubTask.query.filter_by(sub_task_id=sub_task_id, parent_task_id=task_id).first_or_404()
    if not _can_act_on_subtask(subtask, task, current_user):
        return jsonify({'error': 'Permission denied'}), 403
    all_notes = Notes.query.filter_by(task_id=task_id, sub_task_id=sub_task_id).order_by(
        Notes.pin_stat.desc(), Notes.created_on.asc()
    ).all()
    main_notes = [n for n in all_notes if not n.reply_code]
    replies_map = {}
    for n in all_notes:
        if n.reply_code:
            try:
                parent_id = int(n.reply_code)
                if parent_id not in replies_map:
                    replies_map[parent_id] = []
                replies_map[parent_id].append(n)
            except (ValueError, TypeError):
                pass
    member_ids = list({n.member_id for n in all_notes if n.member_id})
    user_by_id = {u.member_id: u for u in User.query.filter(User.member_id.in_(member_ids)).all()} if member_ids else {}
    def _user_display(mid):
        u = user_by_id.get(mid)
        return (u.name or u.username or 'Unknown') if u else 'Unknown'
    def _avatar_file(mid):
        u = user_by_id.get(mid)
        return (u.image_file or 'default.jpg') if u else 'default.jpg'
    out = []
    for n in main_notes:
        replies = replies_map.get(n.notes_id, [])
        out.append({
            'note_body': n.note_body or '',
            'author_name': _user_display(n.member_id),
            'created_on': n.created_on.strftime('%b %d, %Y %H:%M') if n.created_on else '',
            'generated_code': n.generated_code or '',
            'pin_stat': bool(n.pin_stat),
            'image_file': _avatar_file(n.member_id),
            'replies': [
                {'author_name': _user_display(r.member_id), 'created_on': r.created_on.strftime('%H:%M') if r.created_on else '', 'note_body': r.note_body or ''}
                for r in replies
            ],
        })
    return jsonify({'notes': out, 'subtask_name': subtask.subtask_name or 'Subtask'})


@reports_bp.route("/approvals/<int:task_id>/subtask/<int:sub_task_id>/status", methods=['POST'])
@login_required
def update_subtask_status_approvals(task_id, sub_task_id):
    task = Task.query.get_or_404(task_id)
    subtask = SubTask.query.filter_by(sub_task_id=sub_task_id, parent_task_id=task_id).first_or_404()
    if not _can_act_on_subtask(subtask, task, current_user):
        flash('You do not have permission to update this subtask.', 'danger')
        return redirect(url_for('project.approvals'))
    status = (request.form.get('status') or '').strip()
    allowed = ('Ongoing', 'To be reviewed', 'Rejected', 'On Hold', 'Approved')
    if status not in allowed:
        flash('Invalid status.', 'danger')
        return redirect(url_for('project.approvals'))
    # Save note when approving/rejecting (from approvals page modal)
    note_body = (request.form.get('note_body') or '').strip()
    if note_body and status in ('Approved', 'Rejected'):
        pm_entry = ProjectMembers.query.filter_by(project_id=task.project_id, member_id=current_user.member_id).first()
        p_members_id = pm_entry.p_members_id if pm_entry else None
        note = Notes(
            task_id=task_id,
            sub_task_id=sub_task_id,
            member_id=current_user.member_id,
            p_members_id=p_members_id,
            note_body=note_body,
            generated_code=status.lower()
        )
        db.session.add(note)
    subtask.status = status
    if status == 'Approved':
        from datetime import datetime as dt
        subtask.checked_timestamp = dt.utcnow()
        subtask.is_checked = True
        # Do NOT auto-complete task; use Mark Complete button explicitly
    try:
        db.session.commit()
        flash('Subtask updated.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to update subtask.', 'danger')
    return redirect(url_for('project.approvals'))

@reports_bp.route("/approvals/<int:task_id>/subtask/<int:sub_task_id>/note", methods=['POST'])
@login_required
def subtask_note_approvals(task_id, sub_task_id):
    task = Task.query.get_or_404(task_id)
    subtask = SubTask.query.filter_by(sub_task_id=sub_task_id, parent_task_id=task_id).first_or_404()
    if not _can_act_on_subtask(subtask, task, current_user):
        flash('You do not have permission to add a note to this subtask.', 'danger')
        return redirect(url_for('project.task_details', id=task_id))
    note_body = (request.form.get('note_body') or '').strip()
    action = (request.form.get('action') or '').strip().lower()  # submit, resubmit, follow_up
    if not note_body:
        flash('Note is required.', 'danger')
        return redirect(url_for('project.task_details', id=task_id))
    pm_entry = ProjectMembers.query.filter_by(
        project_id=task.project_id,
        member_id=current_user.member_id
    ).first()
    p_members_id = pm_entry.p_members_id if pm_entry else None
    # Submit for review: PM, subtask owner, or any task assignee may submit
    if action == 'submit':
        project = Project.query.get(task.project_id) if task.project_id else None
        is_pm = project and current_user.member_id == project.project_manager
        is_subtask_owner = subtask.p_members_id and pm_entry and subtask.p_members_id == pm_entry.p_members_id
        is_task_assignee = False
        if pm_entry:
            if task.p_members_id == pm_entry.p_members_id:
                is_task_assignee = True
            else:
                for ta in (task.assignees or []):
                    if ta.p_members_id == pm_entry.p_members_id:
                        is_task_assignee = True
                        break
        if not (is_pm or is_subtask_owner or is_task_assignee):
            flash('Only the project manager, subtask owner, or a task assignee can submit for review.', 'danger')
            return redirect(url_for('project.task_details', id=task_id))
    new_note = Notes(
        task_id=task_id,
        sub_task_id=sub_task_id,
        member_id=current_user.member_id,
        p_members_id=p_members_id,
        note_body=note_body,
        generated_code=action or 'note'
    )
    db.session.add(new_note)
    if action == 'submit':
        subtask.status = 'To be reviewed'
    elif action == 'resubmit':
        subtask.status = 'To be reviewed'
    elif action == 'follow_up':
        subtask.status = 'Ongoing'
    try:
        db.session.commit()
        if action == 'submit':
            flash('Subtask submitted for review.', 'success')
        elif action == 'resubmit':
            flash('Re-submitted for review.', 'success')
        else:
            flash('Note saved.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to save note.', 'danger')
    return redirect(url_for('project.approvals', id=task_id))
