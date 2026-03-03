/*
Page: Project Details
Purpose: Edit Members modal – show all users, prefill selected members, submit project_members
*/

(function () {
  "use strict";

  function getInitials(name) {
    if (!name) return "??";
    const parts = String(name).trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return String(name).substring(0, 2).toUpperCase();
  }

  document.addEventListener("DOMContentLoaded", function () {
    const usersDataEl = document.getElementById("edit-project-users-data");
    const initialMembersEl = document.getElementById("edit-project-initial-members");
    const ownerListEdit = document.querySelector(".owner-list-edit-project");
    const ownerInputEdit = document.getElementById("ownerInputEditProject");
    const ownerSearchEdit = document.getElementById("ownerSearchEditProject");
    const editMembersModal = document.getElementById("editMembersModal");
    const editProjectMembersForm = document.getElementById("editProjectMembersForm");

    if (!ownerListEdit || !ownerInputEdit || !editProjectMembersForm) return;

    let allUsers = [];
    try {
      if (usersDataEl) allUsers = JSON.parse(usersDataEl.textContent || "[]");
    } catch (e) {
      return;
    }

    const colors = ["#6f42c1", "#0d6efd", "#198754", "#dc3545", "#fd7e14", "#20c997", "#ffc107", "#6610f2"];
    const allUsersFormatted = allUsers.map(function (u, i) {
      return {
        id: u.member_id,
        name: u.name || u.username,
        initials: getInitials(u.name || u.username),
        color: colors[i % colors.length]
      };
    });

    let selectedEdit = [];

    function renderListEdit(filter) {
      ownerListEdit.innerHTML = "";
      let list = allUsersFormatted;
      if (filter) {
        const f = String(filter).toLowerCase();
        list = list.filter(function (m) { return (m.name || "").toLowerCase().indexOf(f) !== -1; });
      }
      if (list.length === 0) {
        const msg = document.createElement("div");
        msg.className = "list-group-item text-muted text-center";
        msg.textContent = "No members match your search";
        ownerListEdit.appendChild(msg);
        return;
      }
      list.forEach(function (owner) {
        const item = document.createElement("div");
        item.className = "list-group-item owner-item";
        if (selectedEdit.some(function (o) { return o.id === owner.id; })) item.classList.add("active");
        item.innerHTML = "<div class=\"owner-avatar\" style=\"background:" + owner.color + "\">" + owner.initials + "</div><span class=\"owner-name\">" + owner.name + "</span>";
        item.onclick = function (e) {
          e.preventDefault();
          e.stopPropagation();
          toggleEdit(owner);
        };
        ownerListEdit.appendChild(item);
      });
    }

    function renderSelectedEdit() {
      ownerInputEdit.innerHTML = "";
      if (selectedEdit.length === 0) {
        ownerInputEdit.innerHTML = "<span class=\"text-muted small\">Select member(s)</span>";
        return;
      }
      selectedEdit.forEach(function (owner) {
        const chip = document.createElement("div");
        chip.className = "owner-chip";
        chip.innerHTML = owner.name + " <span data-owner-remove=\"" + owner.id + "\">&times;</span>";
        ownerInputEdit.appendChild(chip);
      });
      ownerInputEdit.querySelectorAll("[data-owner-remove]").forEach(function (el) {
        el.addEventListener("click", function (e) {
          e.preventDefault();
          const id = parseInt(el.getAttribute("data-owner-remove"), 10);
          if (!Number.isFinite(id)) return;
          selectedEdit = selectedEdit.filter(function (o) { return o.id !== id; });
          renderSelectedEdit();
          renderListEdit(ownerSearchEdit ? ownerSearchEdit.value : "");
        });
      });
    }

    function toggleEdit(owner) {
      const idx = selectedEdit.findIndex(function (o) { return o.id === owner.id; });
      if (idx !== -1) selectedEdit.splice(idx, 1);
      else selectedEdit.push(owner);
      renderSelectedEdit();
      renderListEdit(ownerSearchEdit ? ownerSearchEdit.value : "");
    }

    if (editMembersModal) {
      editMembersModal.addEventListener("show.bs.modal", function () {
        selectedEdit = [];
        try {
          if (initialMembersEl) {
            const initial = JSON.parse(initialMembersEl.textContent || "[]");
            initial.forEach(function (m) {
              selectedEdit.push({ id: m.member_id, name: m.name || "" });
            });
          }
        } catch (e) {}
        renderSelectedEdit();
        renderListEdit("");
        if (ownerSearchEdit) ownerSearchEdit.value = "";
      });
// Adjust modal body height based on dropdown height 
      var editMembersDropdown = ownerInputEdit ? ownerInputEdit.closest(".dropdown") : null;
      var editMembersModalBody = editMembersModal ? editMembersModal.querySelector(".modal-body") : null;
      if (editMembersDropdown && editMembersModalBody) {
        editMembersDropdown.addEventListener("show.bs.dropdown", function () {
          var menu = editMembersDropdown.querySelector(".dropdown-menu");
          var minH = 320;
          if (menu) {
            menu.style.visibility = "hidden";
            menu.classList.add("show");
            minH = Math.min(600, Math.max(320, menu.offsetHeight + 120));
            menu.classList.remove("show");
            menu.style.visibility = "";
          }
          editMembersModalBody.style.minHeight = minH + "px";
        });
        editMembersDropdown.addEventListener("hide.bs.dropdown", function () {
          editMembersModalBody.style.minHeight = "";
        });
      }
    }

    if (ownerSearchEdit) {
      ownerSearchEdit.addEventListener("input", function () {
        renderListEdit(this.value);
      });
    }

    var clearBtn = document.getElementById("clearOwnersEditProject");
    if (clearBtn) {
      clearBtn.onclick = function (e) {
        e.preventDefault();
        selectedEdit = [];
        renderSelectedEdit();
        renderListEdit("");
      };
    }

    var confirmBtn = document.getElementById("confirmOwnersEditProject");
    if (confirmBtn && typeof window.bootstrap !== "undefined") {
      confirmBtn.onclick = function () {
        var dd = window.bootstrap.Dropdown.getInstance(ownerInputEdit);
        if (dd) dd.hide();
      };
    }

    editProjectMembersForm.addEventListener("submit", function (e) {
      if (selectedEdit.length === 0) {
        e.preventDefault();
        if (typeof Swal !== "undefined") Swal.fire({ icon: "warning", text: "Please select at least one member." });
        else alert("Please select at least one member.");
        return false;
      }
      var btn = document.getElementById("btn-edit-members");
      if (btn) showSubmitSpinner(btn);
      var container = document.getElementById("editMemberIdsContainer");
      if (!container) return;
      container.innerHTML = "";
      selectedEdit.forEach(function (m) {
        var input = document.createElement("input");
        input.type = "hidden";
        input.name = "project_members";
        input.value = m.id;
        container.appendChild(input);
      });
    });

    renderListEdit("");
    renderSelectedEdit();
  });
})();

// --- Spinner logic for all btn-success form submissions ---
function showSubmitSpinner(btn, loadingText) {
  if (!btn) return;
  var spinner = btn.querySelector(".spinner-border") || btn.querySelector("[id$='Spinner']");
  var btnText = btn.querySelector(".btn-text") || btn.querySelector("[id$='BtnText']");
  var text = loadingText || btn.getAttribute("data-loading-text") || " Saving...";
  if (spinner) {
    btn.disabled = true;
    spinner.classList.remove("d-none");
    if (btnText) btnText.textContent = text;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Edit Project form
  var editProjectForm = document.getElementById("editProjectForm");
  if (editProjectForm) {
    editProjectForm.addEventListener("submit", function () {
      var btn = document.getElementById("btn-edit-project");
      if (btn) showSubmitSpinner(btn, " Saving...");
    });
  }

  // Create Task form
  var createTaskForm = document.getElementById("createTaskForm");
  if (createTaskForm) {
    createTaskForm.addEventListener("submit", function () {
      var btn = document.getElementById("btn-create-task");
      if (btn) showSubmitSpinner(btn, " Creating...");
    });
  }

  // Edit Project Manager form
  var editProjectManagerForm = document.querySelector("#editProjectManagerModal form");
  if (editProjectManagerForm) {
    editProjectManagerForm.addEventListener("submit", function () {
      var btn = document.getElementById("btn-edit-project-manager");
      if (btn) showSubmitSpinner(btn, " Saving...");
    });
  }

  // Edit Members form: spinner shown in editProjectMembersForm validation handler above

  // Edit Description form
  var editDescriptionForm = document.querySelector("#editDescriptionModal form");
  if (editDescriptionForm) {
    editDescriptionForm.addEventListener("submit", function () {
      var btn = document.getElementById("btn-edit-description");
      if (btn) showSubmitSpinner(btn, " Saving...");
    });
  }

   // Delete task button (project details tasks table) - use event delegation for GridJS-rendered table
  var tasksContainer = document.getElementById("project-tasks-table-gridjs");
  (tasksContainer || document).addEventListener("click", function (e) {
    var btn = e.target.closest(".delete-task-btn");
    if (!btn) return;
    e.preventDefault();
    var form = document.getElementById("deleteTaskForm");
    if (!form) return;
    var url = btn.getAttribute("data-delete-url");
    var taskName = btn.getAttribute("data-task-name") || "this task";
    if (url) form.action = url;
    if (typeof confirmDeleteTask === "function") {
      confirmDeleteTask(taskName);
    } else if (window.confirm("Are you sure you want to delete " + taskName + "? This cannot be undone.")) {
      form.submit();
    }
  });
});
