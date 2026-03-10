"""Service for creating notifications on events."""
from datetime import datetime, timedelta
from app import db
from app.models import Notification, Project, ProjectMembers, Task, TaskAssignee, SubTask, Deadlines


def _task_recipient_member_ids(task):
    """Return list of member_ids to notify for task events: assignees + project manager."""
    ids = []
    if not task:
        return ids
    project = Project.query.get(task.project_id) if task.project_id else None
    if project and project.project_manager:
        ids.append(project.project_manager)
    for ta in (task.assignees or []):
        if ta.project_member and ta.project_member.member_id:
            ids.append(ta.project_member.member_id)
    if task.p_members_id:
        pm = ProjectMembers.query.get(task.p_members_id)
        if pm and pm.member_id and pm.member_id not in ids:
            ids.append(pm.member_id)
    return list(set(ids))


def _subtask_recipient_member_ids(task, subtask):
    """Return member_ids: task assignees, project manager, subtask owner."""
    ids = _task_recipient_member_ids(task)
    if subtask and subtask.p_members_id:
        pm = ProjectMembers.query.get(subtask.p_members_id)
        if pm and pm.member_id:
            ids.append(pm.member_id)
    return list(set(ids))


def _project_recipient_member_ids(project):
    """Return member_ids: project manager + all project members."""
    ids = []
    if not project:
        return ids
    if project.project_manager:
        ids.append(project.project_manager)
    for pm in ProjectMembers.query.filter_by(project_id=project.project_id).all():
        if pm.member_id:
            ids.append(pm.member_id)
    return list(set(ids))


def create_notification(recipient_ids, module, event_type, reference_table, reference_id, message, sender_id=None):
    """
    Create notifications for recipients.
    recipient_ids: list of member_id
    sender_id: who triggered (None for system)
    Skips recipients equal to sender_id.
    """
    if not recipient_ids:
        return
    exclude = {sender_id} if sender_id is not None else set()
    for rid in recipient_ids:
        if rid in exclude:
            continue
        n = Notification(
            recipient_id=rid,
            sender_id=sender_id,
            reference_id=reference_id,
            reference_table=reference_table,
            module=module,
            event_type=event_type,
            message=message,
        )
        db.session.add(n)


def create_due_soon_notifications(days_ahead=3):
    """
    Create due_soon notifications for tasks with deadlines in the next days_ahead days.
    Call via cron daily. sender_id=None (system).
    Avoids duplicate notifications: only creates if none exist for this task + due_soon today.
    """
    now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end = now + timedelta(days=days_ahead)
    # Tasks with deadline end_date in the window
    tasks = (Task.query.join(Deadlines, Task.deadline_id == Deadlines.deadlines_id)
             .filter(Deadlines.end_date >= now, Deadlines.end_date <= end)
             .all())
    today_str = now.strftime('%Y-%m-%d')
    for task in tasks:
        dl = Deadlines.query.get(task.deadline_id) if task.deadline_id else None
        if not dl:
            continue
        end_date_str = dl.end_date.strftime('%Y-%m-%d') if hasattr(dl.end_date, 'strftime') else str(dl.end_date)
        project = Project.query.get(task.project_id) if task.project_id else None
        project_name = project.project_name if project else 'project'
        # Avoid duplicate due_soon for same task on same day
        day_start = datetime(now.year, now.month, now.day)
        existing = Notification.query.filter(
            Notification.reference_table == 'task_tbl',
            Notification.reference_id == task.task_id,
            Notification.module == 'deadline',
            Notification.event_type == 'due_soon',
            Notification.created_at >= day_start,
        ).first()
        if existing:
            continue
        recipient_ids = _task_recipient_member_ids(task)
        create_notification(
            recipient_ids=recipient_ids,
            module='deadline',
            event_type='due_soon',
            reference_table='task_tbl',
            reference_id=task.task_id,
            message=f'Task schedule changed Upcoming deadline for **{task.task_name}** on {end_date_str}.',
            sender_id=None
        )


def create_overdue_notifications():
    """
    Create overdue notifications for tasks and projects past their deadline end_date.
    Call via cron daily. sender_id=None (system).
    """
    now = datetime.utcnow()
    # Tasks with deadline end_date in the past
    tasks = (Task.query.join(Deadlines, Task.deadline_id == Deadlines.deadlines_id)
             .filter(Deadlines.end_date < now)
             .all())
    day_start = datetime(now.year, now.month, now.day)
    for task in tasks:
        dl = Deadlines.query.get(task.deadline_id) if task.deadline_id else None
        if not dl:
            continue
        project = Project.query.get(task.project_id) if task.project_id else None
        project_name = project.project_name if project else 'project'
        existing = Notification.query.filter(
            Notification.reference_table == 'task_tbl',
            Notification.reference_id == task.task_id,
            Notification.module == 'deadline',
            Notification.event_type == 'overdue',
            Notification.created_at >= day_start,
        ).first()
        if existing:
            continue
        recipient_ids = _task_recipient_member_ids(task)
        create_notification(
            recipient_ids=recipient_ids,
            module='deadline',
            event_type='overdue',
            reference_table='task_tbl',
            reference_id=task.task_id,
            message=f'Task schedule changed Past the deadline (overdue): **{task.task_name}** in **{project_name}**.',
            sender_id=None
        )
    # Projects with deadline end_date in the past
    projects = (Project.query.join(Deadlines, Project.deadlines_id == Deadlines.deadlines_id)
                .filter(Deadlines.end_date < now)
                .all())
    for project in projects:
        dl = Deadlines.query.get(project.deadlines_id) if project.deadlines_id else None
        if not dl:
            continue
        existing = Notification.query.filter(
            Notification.reference_table == 'project',
            Notification.reference_id == project.project_id,
            Notification.module == 'deadline',
            Notification.event_type == 'overdue',
            Notification.created_at >= day_start,
        ).first()
        if existing:
            continue
        recipient_ids = _project_recipient_member_ids(project)
        create_notification(
            recipient_ids=recipient_ids,
            module='deadline',
            event_type='overdue',
            reference_table='project',
            reference_id=project.project_id,
            message=f'Project schedule changed Past the deadline (overdue): **{project.project_name}**.',
            sender_id=None
        )


def create_project_upcoming_deadline_notifications(days_ahead=3):
    """Create upcoming deadline notifications for projects. Call via cron daily."""
    now = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end = now + timedelta(days=days_ahead)
    projects = (Project.query.join(Deadlines, Project.deadlines_id == Deadlines.deadlines_id)
                .filter(Deadlines.end_date >= now, Deadlines.end_date <= end)
                .all())
    day_start = datetime(now.year, now.month, now.day)
    for project in projects:
        dl = Deadlines.query.get(project.deadlines_id) if project.deadlines_id else None
        if not dl:
            continue
        end_date_str = dl.end_date.strftime('%Y-%m-%d') if hasattr(dl.end_date, 'strftime') else str(dl.end_date)
        existing = Notification.query.filter(
            Notification.reference_table == 'project',
            Notification.reference_id == project.project_id,
            Notification.module == 'deadline',
            Notification.event_type == 'due_soon',
            Notification.created_at >= day_start,
        ).first()
        if existing:
            continue
        recipient_ids = _project_recipient_member_ids(project)
        create_notification(
            recipient_ids=recipient_ids,
            module='deadline',
            event_type='due_soon',
            reference_table='project',
            reference_id=project.project_id,
            message=f'Project schedule changed Upcoming deadline for **{project.project_name}** on {end_date_str}.',
            sender_id=None
        )
