/*
Page: Projects (index.html)
Purpose: Chip-based member selection for Create Project modal
*/

(function () {
  "use strict";

  // Helper function to generate initials
  function getInitials(name) {
    if (!name) return "??";
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.substring(0, 2).toUpperCase();
  }

  // Initialize on page load
  document.addEventListener("DOMContentLoaded", function () {
    const usersDataElement = document.getElementById("users-data");
    if (!usersDataElement) return; // not the projects page / users payload not present

    let allUsersData = [];
    try {
      allUsersData = JSON.parse(usersDataElement.textContent || "[]");
    } catch (e) {
      return;
    }

    // Elements
    const departmentSelect = document.getElementById("department_id");
    const ownerInputProject = document.getElementById("ownerInputProject");
    const ownerListProject = document.querySelector(".owner-list-project");
    const ownerSearchProject = document.getElementById("ownerSearchProject");

    if (!departmentSelect || !ownerInputProject || !ownerListProject) return;

    // Generate colors array
    const colors = ["#6f42c1", "#0d6efd", "#198754", "#dc3545", "#fd7e14", "#20c997", "#ffc107", "#6610f2"];

    // Map users to owner format with colors and initials
    const allUsers = allUsersData.map((user, index) => ({
      id: user.member_id,
      name: user.name || user.username,
      initials: getInitials(user.name || user.username),
      color: colors[index % colors.length],
      department_id: user.department_id || null,
    }));

    // Chip-based member selection for projects
    let selectedOwnersProject = [];

    function renderOwnersProject(filter = "", availableMembers = null) {
      ownerListProject.innerHTML = "";

      let membersToShow = availableMembers || allUsers;

      if (filter) {
        const f = filter.toLowerCase();
        membersToShow = membersToShow.filter((m) => (m.name || "").toLowerCase().includes(f));
      }

      const selectedDeptId = departmentSelect.value ? parseInt(departmentSelect.value, 10) : null;
      if (selectedDeptId && availableMembers === null) {
        membersToShow = membersToShow.filter((m) => m.department_id && parseInt(m.department_id, 10) === selectedDeptId);
      }

      if (membersToShow.length === 0) {
        const emptyMsg = document.createElement("div");
        emptyMsg.className = "list-group-item text-muted text-center";
        emptyMsg.textContent = selectedDeptId ? "No members found in this department" : "Select Department first to see members";
        ownerListProject.appendChild(emptyMsg);
        return;
      }

      membersToShow.forEach((owner) => {
        const item = document.createElement("div");
        item.className = "list-group-item owner-item";
        if (selectedOwnersProject.find((o) => o.id === owner.id)) item.classList.add("active");

        item.innerHTML =
          `<div class="owner-avatar" style="background:${owner.color}">` +
          `${owner.initials}` +
          `</div>` +
          `<span>${owner.name}</span>`;

        item.onclick = function () {
          toggleOwnerProject(owner);
        };
        ownerListProject.appendChild(item);
      });
    }

    function populateAvailableMembers() {
      const selectedDeptId = departmentSelect.value ? parseInt(departmentSelect.value, 10) : null;
      let availableMembers = [];
      if (selectedDeptId) {
        availableMembers = allUsers.filter((user) => user.department_id && parseInt(user.department_id, 10) === selectedDeptId);
      }
      renderOwnersProject(ownerSearchProject ? ownerSearchProject.value : "", availableMembers);
    }

    function renderSelectedProject() {
      ownerInputProject.innerHTML = "";

      if (selectedOwnersProject.length === 0) {
        const selectedDeptId = departmentSelect.value || null;
        ownerInputProject.innerHTML = `<span class="text-muted small">${selectedDeptId ? "Select member(s)" : "Select Department first to see members"}</span>`;
        return;
      }

      selectedOwnersProject.forEach((owner) => {
        const chip = document.createElement("div");
        chip.className = "owner-chip";
        chip.innerHTML = `${owner.name} <span data-owner-remove="${owner.id}">&times;</span>`;
        ownerInputProject.appendChild(chip);
      });

      ownerInputProject.querySelectorAll("[data-owner-remove]").forEach((el) => {
        el.addEventListener("click", function (e) {
          const id = parseInt(e.currentTarget.getAttribute("data-owner-remove"), 10);
          if (!Number.isFinite(id)) return;
          selectedOwnersProject = selectedOwnersProject.filter((o) => o.id !== id);
          renderSelectedProject();
          renderOwnersProject(ownerSearchProject ? ownerSearchProject.value : "");
        });
      });
    }

    function toggleOwnerProject(owner) {
      const exists = selectedOwnersProject.find((o) => o.id === owner.id);
      if (exists) selectedOwnersProject = selectedOwnersProject.filter((o) => o.id !== owner.id);
      else selectedOwnersProject.push(owner);

      renderSelectedProject();
      renderOwnersProject(ownerSearchProject ? ownerSearchProject.value : "");
    }

    // Modal open reset
    const createProjectModal = document.querySelector(".create-task");
    if (createProjectModal) {
      createProjectModal.addEventListener("show.bs.modal", function () {
        selectedOwnersProject = [];
        renderSelectedProject();

        departmentSelect.value = "";
        populateAvailableMembers();

        if (ownerSearchProject) ownerSearchProject.value = "";
      });
    }

    departmentSelect.addEventListener("change", function () {
      selectedOwnersProject = [];
      renderSelectedProject();
      populateAvailableMembers();
    });

    if (ownerSearchProject) {
      ownerSearchProject.addEventListener("input", function (e) {
        renderOwnersProject(e.target.value);
      });
    }

    const clearBtnProject = document.getElementById("clearOwnersProject");
    if (clearBtnProject) {
      clearBtnProject.onclick = function (e) {
        e.preventDefault();
        selectedOwnersProject = [];
        renderSelectedProject();
        renderOwnersProject();
      };
    }

    const confirmBtnProject = document.getElementById("confirmOwnersProject");
    if (confirmBtnProject) {
      confirmBtnProject.onclick = function () {
        // Close dropdown (Bootstrap dropdown)
        if (!window.bootstrap) return;
        const bsDropdown = window.bootstrap.Dropdown.getInstance(ownerInputProject);
        if (bsDropdown) bsDropdown.hide();
      };
    }

    // Handle form submission - add selected member IDs to form
    const createProjectForm = document.getElementById("createProjectForm");
    if (createProjectForm) {
      createProjectForm.addEventListener("submit", function (e) {
        if (selectedOwnersProject.length === 0) {
          e.preventDefault();
          alert("Please select at least one member for the project");
          return false;
        }

        const container = document.getElementById("memberIdsContainerProject");
        if (!container) return;

        container.innerHTML = "";
        selectedOwnersProject.forEach(function (member) {
          const input = document.createElement("input");
          input.type = "hidden";
          input.name = "project_members";
          input.value = member.id;
          container.appendChild(input);
        });
      });
    }

    // initial render
    populateAvailableMembers();
    renderSelectedProject();
  });
})();
