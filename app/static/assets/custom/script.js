// Create Task modal: owners list is populated from project-assigned-members (Project Details) or left empty
let owners = [];
(function () {
    const el = document.getElementById("project-assigned-members-for-task");
    if (el && el.textContent) {
        try {
            const list = JSON.parse(el.textContent);
            const colors = ["#6f42c1", "#0d6efd", "#198754", "#dc3545", "#fd7e14", "#20c997", "#ffc107", "#6610f2"];
            function getInitials(name) {
                if (!name) return "??";
                const parts = String(name).trim().split(/\s+/);
                if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
                return String(name).substring(0, 2).toUpperCase();
            }
            owners = list.map(function (u, i) {
                return {
                    id: u.id,
                    name: u.name || "",
                    initials: getInitials(u.name),
                    color: colors[i % colors.length]
                };
            });
        } catch (e) {}
    }
})();

const ownerList = document.querySelector(".owner-list");
const ownerInput = document.getElementById("ownerInput");
const ownerSearch = document.getElementById("ownerSearch");

let selectedOwners = [];
window.selectedOwners = selectedOwners; // for Create Task form (project_details) to set owner_id

// Only run owner-list UI code when elements exist (e.g. not on project_details)
if (ownerList && ownerInput && ownerSearch) {
    // Render list (no hardcoded data; on Project Details owners come from project-assigned-members)
    function renderOwners(filter = "") {
        ownerList.innerHTML = "";
        const filtered = owners.filter(o => (o.name || "").toLowerCase().includes((filter || "").toLowerCase()));
        if (filtered.length === 0) {
            const empty = document.createElement("div");
            empty.className = "list-group-item text-muted text-center";
            empty.textContent = owners.length === 0 ? "No members available (open from a project to assign)." : "No matching members.";
            ownerList.appendChild(empty);
            return;
        }
        filtered.forEach(owner => {
            const item = document.createElement("div");
            item.className = "list-group-item owner-item";
            if (selectedOwners.find(o => o.id === owner.id)) item.classList.add("active");
            item.innerHTML = `<div class="owner-avatar" style="background:${owner.color}">${owner.initials}</div><span>${owner.name}</span>`;
            item.onclick = () => toggleOwner(owner);
            ownerList.appendChild(item);
        });
    }
    function toggleOwner(owner) {
        const exists = selectedOwners.find(o => o.id === owner.id);
        if (exists) selectedOwners = selectedOwners.filter(o => o.id !== owner.id);
        else selectedOwners.push(owner);
        renderSelected();
        renderOwners(ownerSearch.value);
    }
    function renderSelected() {
        ownerInput.innerHTML = "";
        if (selectedOwners.length === 0) {
            ownerInput.innerHTML = `<span class="text-muted small">Select Members</span>`;
            return;
        }
        selectedOwners.forEach(owner => {
            const chip = document.createElement("div");
            chip.className = "owner-chip";
            chip.innerHTML = `${owner.name} <span onclick="removeOwner(${owner.id})">&times;</span>`;
            ownerInput.appendChild(chip);
        });
    }
    function removeOwner(id) {
        selectedOwners = selectedOwners.filter(o => o.id !== id);
        renderSelected();
        renderOwners(ownerSearch.value);
    }
    window.removeOwner = removeOwner;
    ownerSearch.addEventListener("input", e => { renderOwners(e.target.value); });
    const clearOwners = document.getElementById("clearOwners");
    if (clearOwners) clearOwners.onclick = () => { selectedOwners = []; renderSelected(); renderOwners(); };
    renderOwners();
    renderSelected();
}

// Search – only if this page has the owner/CC block
if (ownerSearch) {
    ownerSearch.addEventListener("input", e => {
        renderOwners(e.target.value);
    });
}

// Clear – only if this page has the block
var clearOwnersBtn = document.getElementById("clearOwners");
if (clearOwnersBtn) {
    clearOwnersBtn.onclick = () => {
        selectedOwners = [];
        renderSelected();
        renderOwners();
    };
}

// Search – only if this page has the owner/CC block
if (ownerSearch) {
    ownerSearch.addEventListener("input", e => {
        renderOwners(e.target.value);
    });
}

// Clear – only if this page has the block
var clearOwnersBtn = document.getElementById("clearOwners");
if (clearOwnersBtn) {
    clearOwnersBtn.onclick = () => {
        selectedOwners = [];
        renderSelected();
        renderOwners();
    };
}

// Init – only when both list and input exist (e.g. task/member page with CC dropdown)
if (ownerList && ownerInput) {
    renderOwners();
    renderSelected();
}

// Create Task form (project_details): set owner_id from Assign Members; validate start/end date
document.addEventListener("DOMContentLoaded", function() {
    var createTaskForm = document.getElementById("createTaskForm");
    var createTaskOwnerId = document.getElementById("createTaskOwnerId");
    var startDateInput = document.getElementById("CreateTask-StartDate");
    var endDateInput = document.getElementById("CreateTask-EndDate");

    // End date cannot be before start date: set min/max on date inputs
    if (startDateInput && endDateInput) {
        startDateInput.addEventListener("change", function() {
            endDateInput.min = startDateInput.value || "";
            if (endDateInput.value && endDateInput.value < startDateInput.value) {
                endDateInput.value = startDateInput.value;
            }
        });
        endDateInput.addEventListener("change", function() {
            startDateInput.max = endDateInput.value || "";
            if (startDateInput.value && startDateInput.value > endDateInput.value) {
                startDateInput.value = endDateInput.value;
            }
        });
    }

    if (createTaskForm && createTaskOwnerId) {
        createTaskForm.addEventListener("submit", function(e) {
            var so = window.selectedOwners;
            if (!so || so.length === 0) {
                e.preventDefault();
                if (typeof Swal !== "undefined") {
                    Swal.fire({ icon: "warning", text: "Please select at least one member to assign." });
                } else {
                    alert("Please select at least one member to assign.");
                }
                return false;
            }
            // End date cannot be before start date
            if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
                if (endDateInput.value < startDateInput.value) {
                    e.preventDefault();
                    if (typeof Swal !== "undefined") {
                        Swal.fire({ icon: "warning", text: "End date cannot be before start date." });
                    } else {
                        alert("End date cannot be before start date.");
                    }
                    return false;
                }
            }
            createTaskOwnerId.value = so[0].id;
        });
    }

    // Edit Task form (task_details): end date cannot be before start date
    var editTaskForm = document.getElementById("editTaskForm");
    var editStartDateInput = document.getElementById("editTaskStartDate");
    var editEndDateInput = document.getElementById("editTaskEndDate");
    if (editStartDateInput && editEndDateInput) {
        editStartDateInput.addEventListener("change", function() {
            editEndDateInput.min = editStartDateInput.value || "";
            if (editEndDateInput.value && editEndDateInput.value < editStartDateInput.value) {
                editEndDateInput.value = editStartDateInput.value;
            }
        });
        editEndDateInput.addEventListener("change", function() {
            editStartDateInput.max = editEndDateInput.value || "";
            if (editStartDateInput.value && editStartDateInput.value > editEndDateInput.value) {
                editStartDateInput.value = editEndDateInput.value;
            }
        });
    }
    if (editTaskForm && editStartDateInput && editEndDateInput) {
        editTaskForm.addEventListener("submit", function(e) {
            if (editStartDateInput.value && editEndDateInput.value && editEndDateInput.value < editStartDateInput.value) {
                e.preventDefault();
                if (typeof Swal !== "undefined") {
                    Swal.fire({ icon: "warning", text: "End date cannot be before start date." });
                } else {
                    alert("End date cannot be before start date.");
                }
                return false;
            }
        });
    }
});

function toggleInput(btn, className) {

    const parent = btn.closest('.flex-grow-1');
    
  
    parent.querySelectorAll('.reply-box, .edit-box').forEach(box => {
        if (!box.classList.contains(className.substring(1))) {
            box.classList.add('d-none');
        }
    });

  
    const target = parent.querySelector(className);
    target.classList.toggle('d-none');


    if (!target.classList.contains('d-none')) {
        target.querySelector('input').focus();
    }
}

// Department projects filter using dropdown
document.addEventListener("DOMContentLoaded", function() {
    const dropdownButton = document.getElementById('categorySelect');
    const dropdownMenu = dropdownButton?.closest('.btn-group')?.querySelectorAll('.dropdown-item') || [];
    const tableElement = document.getElementById('projectsTableDept');

    if (!dropdownButton || dropdownMenu.length === 0 || !tableElement) return;

    // Extract data and wrap HTML strings in gridjs.html()
    const tableRows = Array.from(tableElement.querySelectorAll('tbody tr'));
    const allData = tableRows.map(tr => ({
        category: tr.getAttribute('data-category'),
        cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML))
    }));

    const grid = new gridjs.Grid({
        columns: ["ID", "Projects", "Department", "Client", "Deadline", "Status"],
        data: allData.map(row => row.cells),
        pagination: { limit: 10 },
        sort: true,
        className: {
            table: 'table table-bordered'
        }
    }).render(document.getElementById("tableDept-gridjs"));

    const updateGrid = (selectedValue) => {
        const filteredData = allData.filter(row => selectedValue === "All" ? true : row.category === selectedValue);
        grid.updateConfig({ data: filteredData.map(row => row.cells) }).forceRender();
    };

    dropdownMenu.forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault();
            const selectedValue = this.getAttribute('data-value');
            dropdownButton.innerHTML = `${this.textContent} <i class="mdi mdi-chevron-down"></i>`;
            updateGrid(selectedValue || "All");
        });
    });
});

//Delete sweet Alert
// Delete SweetAlert for Members
function confirmDelete(memberName, memberId) {
    Swal.fire({
        title: "Are you sure?",
        text: "You are about to delete " + memberName + ". You won't be able to revert this!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#51d28c",
        cancelButtonColor: "#f34e4e",
        confirmButtonText: "Yes, delete it!"
    }).then(function (result) {
        if (result.isConfirmed) {
            // Redirect to the Flask route you created
            window.location.href = "/delete_member/" + memberId;
        }
    });
}

// Delete SweetAlert for Task (submits hidden form to delete_task route)
function confirmDeleteTask(taskName) {
    var form = document.getElementById("deleteTaskForm");
    if (!form) return;
    if (typeof Swal === "undefined") {
        if (window.confirm("Are you sure you want to delete " + (taskName || "this task") + "? You won't be able to revert this!")) {
            form.submit();
        }
        return;
    }
    Swal.fire({
        title: "Are you sure?",
        text: "You are about to delete " + (taskName || "this task") + ". You won't be able to revert this!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#51d28c",
        cancelButtonColor: "#f34e4e",
        confirmButtonText: "Yes, delete it!"
    }).then(function (result) {
        if (result.isConfirmed) {
            form.submit();
        }
    });
}

// Delete SweetAlert for Projects (redirects to dashboard after delete)
function confirmDeleteProject(projectId, projectName) {
    if (typeof Swal === "undefined") {
        if (window.confirm("Are you sure you want to delete " + (projectName || "this project") + "? You won't be able to revert this!")) {
            window.location.href = "/project_details/" + projectId + "/delete";
        }
        return;
    }
    Swal.fire({
        title: "Are you sure?",
        text: "You are about to delete " + (projectName || "this project") + ". You won't be able to revert this!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#51d28c",
        cancelButtonColor: "#f34e4e",
        confirmButtonText: "Yes, delete it!"
    }).then(function (result) {
        if (result.isConfirmed) {
            window.location.href = "/project_details/" + projectId + "/delete";
        }
    });
}


// notes view modal
function prepareNoteModal(taskId, description, footer) {
    // Update the title
    document.getElementById('preview-note-title').innerText = "Details for " + taskId;
    
    // Update the description/body
    document.getElementById('preview-note-body').innerText = description;
    
    // Update the footer
    document.getElementById('preview-note-footer').innerText = footer;
}

//approve notes modal
function approveNoteModal(taskId, description, footer) {
    // Updates the <h5> title
    document.getElementById('approve-note-title').innerText = "Approve Sub-Task: " + taskId;
    
    // Updates the <p> description
    document.getElementById('approve-note-body').innerText = description;
    
    // Updates the <footer>
    document.getElementById('approve-note-footer').innerText = footer;
}

//JS for PIN in Project details
// document.querySelectorAll('.pin-btn').forEach(btn => {
//     btn.addEventListener('click', e => {
//         e.stopPropagation();

//         const box = btn.closest('.message-box');
//         box.classList.toggle('pinned');

//         const icon = btn.querySelector('i');
//         icon.classList.toggle('mdi-pin-outline');
//         icon.classList.toggle('mdi-pin');
//     });
// });

document.querySelectorAll('.pin-btn').forEach(btn => {
    btn.addEventListener('click', e => {
        e.stopPropagation();

        const box = btn.closest('.message-box');
        if (!box) return;

        box.classList.toggle('pinned');

        const icon = btn.querySelector('i');
        if (!icon) return;

        icon.classList.toggle('mdi-pin-outline');
        icon.classList.toggle('mdi-pin');
    });
});

// This ensures the calendar works even if the .init.js misses it
    document.addEventListener("DOMContentLoaded", function() {
        if (typeof flatpickr !== 'undefined') {
            flatpickr("#datepicker-range", {
                mode: "range",
                dateFormat: "Y-m-d",
                altInput: true,
                altFormat: "F j, Y"
            });
        }
    });

// Generate options for the weekly report date dropdown
function getCurrentReportWeek() {
    const today = new Date();
    const daysFromMonday = (today.getDay() + 6) % 7;
    const monday = new Date(today);
    monday.setDate(today.getDate() - daysFromMonday);
    const saturday = new Date(monday);
    saturday.setDate(monday.getDate() + 5);
    return { start: monday, end: saturday };
}

document.addEventListener("DOMContentLoaded", function () {
    const sel = document.getElementById("weekly-report-date");
    if (!sel) return;

    function fmt(d) {
        const m = String(d.getMonth() + 1).padStart(2, "0");
        const day = String(d.getDate()).padStart(2, "0");
        return m + "/" + day + "/" + d.getFullYear();
    }

    const { start, end } = getCurrentReportWeek();
    const currentLabel = fmt(start) + " - " + fmt(end);

    // Clear placeholder, add "This week" as first and selected
    sel.innerHTML = "";
    const currentOpt = document.createElement("option");
    currentOpt.value = currentLabel;
    currentOpt.textContent = currentLabel + " (This week)";
    currentOpt.selected = true;
    sel.appendChild(currentOpt);

    // Only future report weeks (ahead)
    for (let i = 1; i <= 12; i++) {
        const nextMon = new Date(start);
        nextMon.setDate(start.getDate() + 7 * i);
        const nextSat = new Date(nextMon);
        nextSat.setDate(nextMon.getDate() + 5);
        const opt = document.createElement("option");
        opt.value = fmt(nextMon) + " - " + fmt(nextSat);
        opt.textContent = opt.value;
        sel.appendChild(opt);
    }
});

// Mark Complete Button
(function() {
    var btn = document.getElementById('markCompleteBtn');
    if (btn) {
    btn.addEventListener('click', function() {
        var isCompleted = btn.querySelector('.btn-text').textContent.trim() === 'Completed';
        if (isCompleted) {
        btn.innerHTML = '<i class="mdi mdi-check"></i> <span class="btn-text">Mark Complete</span>';
        btn.classList.remove('btn-outline-success', 'bg-soft-success');
        btn.classList.add('btn-outline-primary');
        } else {
        btn.innerHTML = '<i class="mdi mdi-check"></i> <span class="btn-text">Completed</span>';
        btn.classList.remove('btn-outline-primary');
        btn.classList.add('btn-outline-success', 'bg-soft-success');
        }
    });
    }
})();
