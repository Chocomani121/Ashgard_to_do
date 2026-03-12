"""Helpers for notification display (action URLs, time ago, badges)."""
from datetime import datetime
from flask import url_for

# Import here to avoid circular import
def _get_subtask_parent_task_id(sub_task_id):
    from app.models import SubTask
    st = SubTask.query.get(sub_task_id)
    return st.parent_task_id if st else None


def _get_note_task_and_subtask(notes_id):
    """Return (task_id, sub_task_id) for a note. sub_task_id may be None for task-level notes."""
    from app.models import Notes
    note = Notes.query.get(notes_id)
    if not note:
        return None, None
    task_id = note.task_id
    sub_task_id = getattr(note, 'sub_task_id', None)
    return task_id, sub_task_id


def notification_action_url(n):
    """Build action URL from notification reference_table and reference_id."""
    try:
        if n.reference_table == 'task_tbl':
            return url_for('project.task_details', id=n.reference_id)
        if n.reference_table == 'sub_task_list':
            task_id = _get_subtask_parent_task_id(n.reference_id)
            if task_id is not None:
                return url_for('project.task_details', id=task_id, sub_task_id=n.reference_id)
        if n.reference_table == 'report_tbl':
            return url_for('reports.reports', report_id=n.reference_id)
        if n.reference_table == 'project':
            return url_for('project.project_details', id=n.reference_id)
        if n.reference_table == 'deadlines_tbl':
            from app.models import Task, Project
            t = Task.query.filter_by(deadline_id=n.reference_id).first()
            if t:
                return url_for('project.task_details', id=t.task_id)
            p = Project.query.filter_by(deadlines_id=n.reference_id).first()
            if p:
                return url_for('project.project_details', id=p.project_id)
        if n.reference_table == 'notes_tbl':
            task_id, sub_task_id = _get_note_task_and_subtask(n.reference_id)
            if task_id is not None:
                if sub_task_id is not None:
                    return url_for('project.task_details', id=task_id, sub_task_id=sub_task_id, note_id=n.reference_id)
                return url_for('project.task_details', id=task_id, note_id=n.reference_id)
    except Exception:
        pass
    return url_for('users.notifications')


def notification_link_text(n):
    """Return link text based on module."""
    m = (n.module or '').lower()
    if m in ('project',): return 'View Project'
    if m in ('task',): return 'View Task'
    if m in ('subtask',): return 'View Subtask'
    if m in ('note',): return 'View Note'
    if m in ('report',): return 'View Report'
    if m in ('deadline',): return 'View Task'
    return 'View'


def notification_type_badge(module):
    """Return (badge_label, badge_class) for module."""
    m = (module or '').lower()
    if m == 'project': return ('Project', 'bg-primary')
    if m == 'task': return ('Task', 'bg-info')
    if m == 'subtask': return ('Subtask', 'bg-secondary')
    if m == 'note': return ('Note', 'bg-secondary')
    if m == 'report': return ('Report', 'bg-success')
    if m == 'deadline': return ('Deadline', 'bg-warning')
    return (m or '—', 'bg-secondary')


def time_ago(dt):
    """Return human-readable relative time, e.g. '1 hour ago', 'Yesterday'."""
    if not dt:
        return '—'
    now = datetime.now()
    try:
        dt_naive = dt.replace(tzinfo=None) if hasattr(dt, 'tzinfo') and dt.tzinfo else dt
    except Exception:
        dt_naive = dt
    diff = now - dt_naive if now > dt_naive else dt_naive - now
    secs = diff.total_seconds()
    if secs < 60:
        return 'Just now'
    if secs < 3600:
        m = int(secs / 60)
        return f'{m} minute{"s" if m != 1 else ""} ago'
    if secs < 86400:
        h = int(secs / 3600)
        return f'{h} hour{"s" if h != 1 else ""} ago'
    if secs < 172800:
        return 'Yesterday'
    if secs < 604800:
        d = int(secs / 86400)
        return f'{d} days ago'
    return dt.strftime('%b %d') if hasattr(dt, 'strftime') else str(dt)
