// Initialize owners array from database users
const usersDataElement = document.getElementById('users-data');
const usersData = JSON.parse(usersDataElement.textContent);

// Filter to only include users without a department (for Add/Edit modals dropdown)
const owners = usersData
    .filter(function(user) {
        return user.department_id === null || user.department_id === undefined;
    })
    .map(function(owner) {
        // Generate initials
        if (!owner.initials) {
            const nameParts = owner.name.trim().split(/\s+/);
            if (nameParts.length >= 2) {
                owner.initials = (nameParts[0][0] + nameParts[1][0]).toUpperCase();
            } else {
                owner.initials = owner.name.substring(0, 2).toUpperCase();
            }
        }
        return owner;
    });

// Store all users (including those with departments) for Edit modal pre-selection
const allUsersData = usersData.map(function(owner) {
    // Generate initials
    if (!owner.initials) {
        const nameParts = owner.name.trim().split(/\s+/);
        if (nameParts.length >= 2) {
            owner.initials = (nameParts[0][0] + nameParts[1][0]).toUpperCase();
        } else {
            owner.initials = owner.name.substring(0, 2).toUpperCase();
        }
    }
    return owner;
});

// Override the hardcoded owners array in script.js for the Add Department modal
document.addEventListener('DOMContentLoaded', function() {
    // Re-initialize owner functionality with database users
    const ownerList = document.querySelector(".owner-list");
    const ownerInput = document.getElementById("ownerInput");
    const ownerSearch = document.getElementById("ownerSearch");
    
    if (ownerList && ownerInput && ownerSearch) {
        let selectedOwners = [];
        
        // Generate initials helper function
        function getInitials(name) {
            if (!name) return "??";
            const parts = name.trim().split(/\s+/);
            if (parts.length >= 2) {
                return (parts[0][0] + parts[1][0]).toUpperCase();
            }
            return name.substring(0, 2).toUpperCase();
        }
        
        // Render list
        function renderOwners(filter = "") {
            ownerList.innerHTML = "";
            
            owners
                .filter(o => o.name.toLowerCase().includes(filter.toLowerCase()))
                .forEach(owner => {
                    const item = document.createElement("div");
                    item.className = "list-group-item owner-item";
                    if (selectedOwners.find(o => o.id === owner.id)) {
                        item.classList.add("active");
                    }
                    
                    item.innerHTML = `
                        <div class="owner-avatar" style="background:${owner.color}">
                            ${owner.initials}
                        </div>
                        <span>${owner.name}</span>
                    `;
                    
                    item.onclick = () => toggleOwner(owner);
                    ownerList.appendChild(item);
                });
        }
        
        // Toggle selection
        function toggleOwner(owner) {
            const exists = selectedOwners.find(o => o.id === owner.id);
            
            if (exists) {
                selectedOwners = selectedOwners.filter(o => o.id !== owner.id);
            } else {
                selectedOwners.push(owner);
            }
            
            renderSelected();
            renderOwners(ownerSearch.value);
        }
        
        // Render selected chips
        function renderSelected() {
            ownerInput.innerHTML = "";
            
            if (selectedOwners.length === 0) {
                ownerInput.innerHTML = `<span class="text-muted small">Select owner(s)</span>`;
                return;
            }
            
            selectedOwners.forEach(owner => {
                const chip = document.createElement("div");
                chip.className = "owner-chip";
                chip.innerHTML = `
                    ${owner.name}
                    <span onclick="removeOwner(${owner.id})">&times;</span>
                `;
                ownerInput.appendChild(chip);
            });
        }
        
        // Remove chip
        window.removeOwner = function(id) {
            selectedOwners = selectedOwners.filter(o => o.id !== id);
            renderSelected();
            renderOwners(ownerSearch.value);
        };
        
        // Search
        ownerSearch.addEventListener("input", e => {
            renderOwners(e.target.value);
        });
        
        // Clear
        const clearBtn = document.getElementById("clearOwners");
        if (clearBtn) {
            clearBtn.onclick = () => {
                selectedOwners = [];
                renderSelected();
                renderOwners();
            };
        }
        
        // Handle form submission - add selected member IDs to form
        const addDepartmentForm = document.getElementById("addDepartmentForm");
        if (addDepartmentForm) {
            addDepartmentForm.addEventListener("submit", function(e) {
                // Clear existing hidden inputs
                const container = document.getElementById("memberIdsContainer");
                container.innerHTML = "";
                
                // Add hidden inputs for each selected member
                selectedOwners.forEach(function(owner) {
                    const input = document.createElement("input");
                    input.type = "hidden";
                    input.name = "member_ids";
                    input.value = owner.id;
                    container.appendChild(input);
                });
            });
        }
        
        // Init
        renderOwners();
        renderSelected();
    }
});

// Edit Department Modal - Populate with department data
document.addEventListener('DOMContentLoaded', function() {
    // Store last-clicked edit button data so we can populate the modal even if relatedTarget is not set (e.g. dropdown)
    let lastEditButtonData = null;
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.edit-department-btn');
        if (btn) {
            lastEditButtonData = {
                deptId: btn.getAttribute('data-dept-id'),
                deptName: btn.getAttribute('data-dept-name'),
                deptMembersJson: btn.getAttribute('data-dept-members')
            };
        }
    }, true);
    
    function initEditModalOwners() {
        const editModal = document.getElementById('editDepartmentModal');
        const editDepartmentForm = document.getElementById('editDepartmentForm');
        const ownerListEdit = document.querySelector(".owner-list-edit");
        const ownerInputEdit = document.getElementById("ownerInputEdit");
        const ownerSearchEdit = document.getElementById("ownerSearchEdit");
        
        if (!ownerListEdit || !ownerInputEdit || !ownerSearchEdit) {
            return;
        }
        
        // Do not wait for owners – attach modal handler so department name is always populated when editing
        const ownersList = (typeof owners !== 'undefined' && owners && owners.length) ? owners : [];
        
        let selectedOwnersEdit = [];
        
        // Render list for edit modal
        function renderOwnersEdit(filter = "") {
            ownerListEdit.innerHTML = "";
            
            ownersList
                .filter(o => o.name && o.name.toLowerCase().includes(filter.toLowerCase()))
                .forEach(owner => {
                    const item = document.createElement("div");
                    item.className = "list-group-item owner-item";
                    if (selectedOwnersEdit.find(o => o.id === owner.id)) {
                        item.classList.add("active");
                    }
                    
                    item.innerHTML = `
                        <div class="owner-avatar" style="background:${owner.color}">
                            ${owner.initials}
                        </div>
                        <span>${owner.name}</span>
                    `;
                    
                    item.onclick = () => toggleOwnerEdit(owner);
                    ownerListEdit.appendChild(item);
                });
        }
        
        // Toggle selection for edit modal
        function toggleOwnerEdit(owner) {
            const exists = selectedOwnersEdit.find(o => o.id === owner.id);
            
            if (exists) {
                selectedOwnersEdit = selectedOwnersEdit.filter(o => o.id !== owner.id);
            } else {
                selectedOwnersEdit.push(owner);
            }
            
            renderSelectedEdit();
            renderOwnersEdit(ownerSearchEdit.value);
        }
        
        // Render selected chips for edit modal
        function renderSelectedEdit() {
            if (!ownerInputEdit) return;
            
            ownerInputEdit.innerHTML = "";
            
            if (selectedOwnersEdit.length === 0) {
                ownerInputEdit.innerHTML = `<span class="text-muted small">Select owner(s)</span>`;
                return;
            }
            
            selectedOwnersEdit.forEach(owner => {
                const chip = document.createElement("div");
                chip.className = "owner-chip";
                chip.innerHTML = `
                    ${owner.name}
                    <span onclick="removeOwnerEdit(${owner.id})">&times;</span>
                `;
                ownerInputEdit.appendChild(chip);
            });
        }
        
        // Remove chip for edit modal
        window.removeOwnerEdit = function(id) {
            selectedOwnersEdit = selectedOwnersEdit.filter(o => o.id !== id);
            renderSelectedEdit();
            renderOwnersEdit(ownerSearchEdit.value);
        };
        
        // Search for edit modal
        ownerSearchEdit.addEventListener("input", e => {
            renderOwnersEdit(e.target.value);
        });
        
        // Clear for edit modal
        const clearBtnEdit = document.getElementById("clearOwnersEdit");
        if (clearBtnEdit) {
            clearBtnEdit.onclick = () => {
                selectedOwnersEdit = [];
                renderSelectedEdit();
                renderOwnersEdit();
            };
        }
        
        // Handle edit form submission
        if (editDepartmentForm) {
            editDepartmentForm.addEventListener("submit", function(e) {
                // Clear existing hidden inputs
                const container = document.getElementById("memberIdsContainerEdit");
                container.innerHTML = "";
                
                // Add hidden inputs for each selected member
                selectedOwnersEdit.forEach(function(owner) {
                    const input = document.createElement("input");
                    input.type = "hidden";
                    input.name = "member_ids";
                    input.value = owner.id;
                    container.appendChild(input);
                });
            });
        }
        
        // When edit modal opens, populate it with department data
        if (editModal) {
            editModal.addEventListener('show.bs.modal', function(event) {
                // Prefer data from the button that triggered the modal; fallback to last-clicked edit button (e.g. when opened from dropdown)
                let deptId, deptName, deptMembersJson;
                const button = event.relatedTarget;
                if (button && button.classList.contains('edit-department-btn')) {
                    deptId = button.getAttribute('data-dept-id');
                    deptName = button.getAttribute('data-dept-name');
                    deptMembersJson = button.getAttribute('data-dept-members');
                } else if (lastEditButtonData) {
                    deptId = lastEditButtonData.deptId;
                    deptName = lastEditButtonData.deptName;
                    deptMembersJson = lastEditButtonData.deptMembersJson;
                }
                if (deptId != null || deptName != null) {
                    // Populate department name
                    const nameInput = document.getElementById('formrow-departmentname-input-edit');
                    if (nameInput) {
                        nameInput.value = deptName || '';
                    }
                    
                    // Update form action with correct department ID
                    if (editDepartmentForm && deptId) {
                        const baseUrl = editDepartmentForm.getAttribute('data-base-url') || '';
                        if (baseUrl) {
                            editDepartmentForm.action = baseUrl.replace('/0', '/' + deptId);
                        }
                    }
                    
                    // Reset selected owners
                    selectedOwnersEdit = [];
                    
                    // Parse and populate current members
                    if (deptMembersJson) {
                        try {
                            const currentMemberIds = JSON.parse(deptMembersJson);
                            
                            if (Array.isArray(currentMemberIds) && currentMemberIds.length > 0) {
                                // Convert member IDs to integers for comparison
                                const memberIdsInt = currentMemberIds.map(function(id) {
                                    return parseInt(id);
                                });
                                
                                // Filter allUsersData to find current members (even if they have a department)
                                // This allows pre-selecting current members in Edit modal
                                if (typeof allUsersData !== 'undefined' && allUsersData && allUsersData.length > 0) {
                                    selectedOwnersEdit = allUsersData.filter(function(o) {
                                        const ownerId = parseInt(o.id);
                                        return memberIdsInt.includes(ownerId);
                                    });
                                }
                            }
                        } catch (e) {
                            console.error('Error parsing member IDs:', e, deptMembersJson);
                        }
                    }
                    
                    // Render the selected members and the full list
                    renderSelectedEdit();
                    renderOwnersEdit();
                }
            });
        }
    }
    
    // Initialize after DOM is ready
    initEditModalOwners();
});

// Department deletion with event listeners (avoids inline JavaScript syntax errors)
document.addEventListener('DOMContentLoaded', function() {
    // Attach event listeners to all delete buttons
    document.querySelectorAll('.delete-department-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const departmentName = this.getAttribute('data-dept-name');
            const departmentId = this.getAttribute('data-dept-id');
            const deleteUrl = this.getAttribute('data-delete-url');
            
            Swal.fire({
                title: "Are you sure?",
                text: "You are about to delete \"" + (departmentName || "this department") + "\". You won't be able to revert this!",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#51d28c",
                cancelButtonColor: "#f34e4e",
                confirmButtonText: "Yes, delete it!"
            }).then(function (result) {
                if (result.isConfirmed) {
                    const form = document.getElementById('deleteDepartmentForm');
                    form.action = deleteUrl;
                    form.submit();
                }
            });
        });
    });
});

