document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.edit-button').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.getAttribute('data-id'); 
            const form = document.getElementById('editMemberForm');
            
            // Construct the URL 
            const newAction = "/admin/update/member/" + id;
            
            
            form.action = newAction;
            
            // Debugging: This will show up in your F12 Console
            console.log("Form action changed to: " + form.action);

            // Fill the inputs
            document.getElementById('formrow-fullname-input-edit').value = this.getAttribute('data-name');
            document.getElementById('formrow-username-input-edit').value = this.getAttribute('data-username');
            document.getElementById('formrow-email-input-edit').value = this.getAttribute('data-email');
            document.getElementById('formrow-position-input-edit').value = this.getAttribute('data-pos');
            document.getElementById('formrow-department-input-edit').value = this.getAttribute('data-dept');
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
        const messages = document.querySelectorAll('.flash-message');
        
        if (messages.length > 0) {
            setTimeout(function() {
                messages.forEach(function(msg) {
                    msg.style.transition = "opacity 0.5s ease";
                    msg.style.opacity = "0";
                    
                    setTimeout(() => {
                        msg.style.display = "none";
                    }, 500); 
                });
            }, 3000);
        }
    });