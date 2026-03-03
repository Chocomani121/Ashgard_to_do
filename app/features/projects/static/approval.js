document.addEventListener('DOMContentLoaded', function() {
    // Notes cell click: open modal and load notes via API
    document.addEventListener('click', function(e) {
        var el = e.target.closest('.notes-preview-clickable');
        if (!el) return;
        e.preventDefault();
        var taskId = el.getAttribute('data-task-id');
        var subTaskId = el.getAttribute('data-sub-task-id');
        var subtaskName = el.getAttribute('data-subtask-name') || 'Subtask';
        if (!taskId || !subTaskId) return;
        var apiBase = typeof window.APPROVALS_NOTES_API !== 'undefined' ? window.APPROVALS_NOTES_API : '/approvals/0/subtask/0/notes';
        var url = apiBase.replace(/\/0\/subtask\/0\//, '/' + taskId + '/subtask/' + subTaskId + '/');
        var titleEl = document.getElementById('subtaskNotesSubtaskName');
        var listEl = document.querySelector('#subtaskNotesModalBody .subtask-notes-list');
        if (titleEl) titleEl.textContent = 'Notes: ' + subtaskName;
        if (listEl) listEl.innerHTML = '<div class="text-center py-4"><span class="spinner-border spinner-border-sm me-2"></span>Loading notes...</div>';
        var modalEl = document.getElementById('subtaskNotesModal');
        if (modalEl && typeof bootstrap !== 'undefined') {
            var modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        }
        fetch(url, { headers: { 'Accept': 'application/json' } })
            .then(function(r) { return r.ok ? r.json() : Promise.reject(new Error('Failed to load notes')); })
            .then(function(data) {
                if (!listEl) return;
                if (!data.notes || data.notes.length === 0) {
                    listEl.innerHTML = '<p class="text-muted mb-0">No notes yet.</p>';
                    return;
                }
                var html = data.notes.map(function(n) {
                    var badge = n.generated_code ? '<span class="badge badge-soft-secondary font-size-11 me-2">' + (n.generated_code.charAt(0).toUpperCase() + n.generated_code.slice(1)) + '</span>' : '';
                    return '<div class="border-bottom pb-3 mb-3"><div class="d-flex justify-content-between align-items-start mb-1"><span class="fw-medium small">' + (n.author_name || 'Unknown') + ' ' + badge + '</span><span class="text-muted small">' + (n.created_on || '') + '</span></div><p class="mb-0 small">' + (n.note_body || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>') + '</p></div>';}).join('');
                listEl.innerHTML = html;
            })
            .catch(function() {
                if (listEl) listEl.innerHTML = '<p class="text-danger mb-0">Failed to load notes.</p>';
            });
    });

    // Approve/Reject modal: set form action, status, title when opened
    var approveRejectModalEl = document.getElementById('approveRejectModal');
    if (approveRejectModalEl) {
        approveRejectModalEl.addEventListener('show.bs.modal', function(e) {
            var trigger = e.relatedTarget;
            if (!trigger || !trigger.classList.contains('approve-reject-btn')) return;
            var form = document.getElementById('approveRejectForm');
            var statusInput = document.getElementById('approveRejectStatus');
            var titleEl = document.getElementById('approveRejectModalTitle');
            var bodyInput = document.getElementById('approveRejectNoteBody');
            var submitBtn = document.getElementById('approveRejectSubmitBtn');
            var btnText = document.getElementById('approveRejectBtnText');
            var spinner = document.getElementById('approveRejectSpinner');
            var status = trigger.dataset.status || '';
            var subtaskName = trigger.dataset.subtaskName || '';
            if (trigger.dataset.formAction) form.action = trigger.dataset.formAction;
            if (statusInput) statusInput.value = status;
            if (bodyInput) bodyInput.value = '';
            if (submitBtn) submitBtn.disabled = false;
            if (spinner) spinner.classList.add('d-none');
            var namePart = subtaskName ? ': ' + subtaskName : '';
            if (status === 'Approved') {
                if (titleEl) titleEl.textContent = 'Approve' + namePart + ' – Add Note';
                if (btnText) btnText.textContent = 'Confirm Approval';
                if (submitBtn) { submitBtn.classList.remove('btn-danger'); submitBtn.classList.add('btn-success'); }
            } else if (status === 'Rejected') {
                if (titleEl) titleEl.textContent = 'Reject' + namePart + ' – Add Note';
                if (btnText) btnText.textContent = 'Confirm Rejection';
                if (submitBtn) { submitBtn.classList.remove('btn-success'); submitBtn.classList.add('btn-danger'); }
            } else if (status === 'On Hold') {
                if (titleEl) titleEl.textContent = 'Add Note';
                if (btnText) btnText.textContent = 'Confirm';
                if (submitBtn) { submitBtn.classList.remove('btn-success'); submitBtn.classList.add('btn-secondary'); }
            } else {
                if (titleEl) titleEl.textContent = 'Add Note';
                if (btnText) btnText.textContent = 'Confirm';
            }
        });
    }

    // Approve/Reject form submit: show loading spinner
    var approveRejectForm = document.getElementById('approveRejectForm');
    if (approveRejectForm) {
        approveRejectForm.addEventListener('submit', function() {
            var submitBtn = document.getElementById('approveRejectSubmitBtn');
            var btnText = document.getElementById('approveRejectBtnText');
            var spinner = document.getElementById('approveRejectSpinner');
            if (submitBtn) submitBtn.disabled = true;
            if (spinner) spinner.classList.remove('d-none');
            if (btnText) btnText.textContent = 'Loading...';
        });
    }

    var subtaskNoteModalEl = document.getElementById('subtaskNoteModal');
    if (subtaskNoteModalEl) {
        subtaskNoteModalEl.addEventListener('show.bs.modal', function(e) {
            var trigger = e.relatedTarget;
            if (!trigger) return;
            var form = document.getElementById('subtaskNoteForm');
            var titleEl = document.getElementById('subtaskNoteModalTitle');
            var actionInput = document.getElementById('subtaskNoteAction');
            var bodyInput = document.getElementById('subtaskNoteBody');
            var helpEl = document.getElementById('subtaskNoteHelp');
            var submitBtn = document.getElementById('subtaskNoteSubmitBtn');
            if (trigger.dataset.noteFormAction) form.action = trigger.dataset.noteFormAction;
            if (trigger.dataset.modalTitle) titleEl.textContent = trigger.dataset.modalTitle;
            var action = (trigger.dataset.noteAction || '').toLowerCase();
            if (action) actionInput.value = action;
            if (bodyInput) bodyInput.value = '';
            if (action === 'submit') {
                if (submitBtn) submitBtn.textContent = 'Submit';
                if (bodyInput) bodyInput.placeholder = 'Add a note and submit for review...';
                if (helpEl) helpEl.textContent = 'Your note will be saved and the subtask will move to To be reviewed.';
            } else if (action === 'resubmit') {
                if (submitBtn) submitBtn.textContent = 'Re-Submit';
                if (helpEl) helpEl.textContent = 'State the reason for resubmit; it will appear in subtask notes.';
            } else if (action === 'follow_up') {
                if (submitBtn) submitBtn.textContent = 'Follow Up';
                if (helpEl) helpEl.textContent = 'State the reason for follow up; it will appear in subtask notes.';
            } else {
                if (submitBtn) submitBtn.textContent = 'Save';
                if (helpEl) helpEl.textContent = '';
            }
        });
    }

    var editSubtaskModalEl = document.getElementById('editSubtaskModal');
    if (editSubtaskModalEl) {
        editSubtaskModalEl.addEventListener('show.bs.modal', function(e) {
            var trigger = e.relatedTarget;
            if (!trigger) return;
            var form = document.getElementById('editSubtaskForm');
            var nameInput = document.getElementById('editSubtaskNameInput');
            if (trigger.dataset.editFormAction) form.action = trigger.dataset.editFormAction;
            if (trigger.dataset.subtaskName !== undefined) nameInput.value = trigger.dataset.subtaskName || '';
        });
    }
    document.addEventListener('click', function(e) {
        var link = e.target.closest('.subtask-status-link');
        if (link) {
            e.preventDefault();
            var url = link.getAttribute('data-url');
            var status = link.getAttribute('data-status');
            if (url && status) {
                var form = document.getElementById('subtaskStatusForm');
                if (form) { form.action = url; document.getElementById('subtaskStatusFormStatus').value = status; form.submit(); }
            }
        }
        var delLink = e.target.closest('.subtask-delete-link');
        if (delLink) {
            e.preventDefault();
            var url = delLink.getAttribute('data-url');
            var name = delLink.getAttribute('data-subtask-name') || 'this subtask';
            if (url && typeof confirmDeleteSubtask === 'function') {
                confirmDeleteSubtask(url, name);
            } else if (url && confirm('Delete sub-task ' + name + '?')) {
                var form = document.getElementById('subtaskDeleteForm');
                if (form) { form.action = url; form.submit(); }
            }
        }
    });
});