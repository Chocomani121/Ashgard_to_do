document.addEventListener('DOMContentLoaded', function() {
    // Use event delegation so it works with GridJS-rendered content
    document.addEventListener('click', function(e) {
        var btn = e.target.closest('.mark-complete-btn');
        if (!btn) return;

        e.preventDefault();
            var taskId = btn.getAttribute('data-task-id');
            if (!taskId) return;
            
            var row = btn.closest('tr');
            var originalBtnHtml = btn.innerHTML;
            
            // Disable button during request
            btn.disabled = true;
            btn.innerHTML = '<i class="mdi mdi-loading mdi-spin"></i> Processing...';
            
            // Send AJAX request to mark task as complete
            fetch(`/task/${taskId}/mark_complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update status badge
                    var statusBadge = row.querySelector('.task-status-badge');
                    if (statusBadge) {
                        statusBadge.textContent = 'Completed';
                        statusBadge.className = 'badge badge-soft-success font-size-12 task-status-badge';
                    }
                    
                    // Update row data attribute
                    row.setAttribute('data-task-status', 'Completed');
                    
                    // Replace button with completed text
                    var actionsCell = btn.parentElement;
                    actionsCell.innerHTML = '<span class="text-muted small">Task Completed</span>';
                    
                    // Show success message
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'success',
                            title: 'Success',
                            text: 'Task marked as completed',
                            timer: 2000,
                            showConfirmButton: false
                        });
                    }
                    
                    // Reload page after a short delay to update progress charts and counts
                    setTimeout(function() {
                        window.location.reload();
                    }, 1500);
                } else {
                    throw new Error(data.error || 'Failed to mark task as complete');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                btn.disabled = false;
                btn.innerHTML = originalBtnHtml;
                
                if (typeof Swal !== 'undefined') {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: error.message || 'Failed to mark task as complete'
                    });
                } else {
                    alert('Error: ' + error.message);
                }
            });
    });
});