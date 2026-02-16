from flask import render_template, Blueprint, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models import User, Report, ReportCC, Comment
from app import db, main 
from datetime import datetime, date, time
from sqlalchemy import or_, text
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.orm import joinedload, selectinload
import json
import random

reports_bp = Blueprint('reports', __name__, template_folder='templates', static_folder='static', static_url_path='/reports/static')

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