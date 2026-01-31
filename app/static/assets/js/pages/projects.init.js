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

    // Start date / deadline: deadline cannot be earlier than start date
    const startDateEl = document.getElementById("start_date");
    const endDateEl = document.getElementById("end_date");
    if (startDateEl && endDateEl) {
      startDateEl.addEventListener("change", function () {
        endDateEl.min = this.value || "";
      });
    }

    // Handle form submission - add selected member IDs to form + validate dates
    const createProjectForm = document.getElementById("createProjectForm");
    if (createProjectForm) {
      createProjectForm.addEventListener("submit", function (e) {
        if (startDateEl && endDateEl) {
          const start = startDateEl.value;
          const end = endDateEl.value;
          if (start && end && end < start) {
            e.preventDefault();
            if (typeof Swal !== "undefined") {
              Swal.fire({ icon: "warning", title: "Invalid dates", text: "Deadline cannot be earlier than the start date." });
            } else {
              alert("Deadline cannot be earlier than the start date.");
            }
            return false;
          }
        }
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

    // ----- Table pagination (Department-Wide and Company-Wide projects) -----
    const projectsTable = document.getElementById("projectsTable");
    const projectsTablePagination = document.getElementById("projectsTablePagination");
    const projectsTableSummary = document.getElementById("projectsTableSummary");
    const projectsTableCompany = document.getElementById("projectsTableCompany");
    const projectsTableCompanyPagination = document.getElementById("projectsTableCompanyPagination");
    const projectsTableCompanySummary = document.getElementById("projectsTableCompanySummary");

    const PAGE_SIZE = 10;
    let departmentPage = 1;
    let companyPage = 1;

    function getDepartmentDataRows() {
      if (!projectsTable) return [];
      const tbody = projectsTable.querySelector("tbody");
      if (!tbody) return [];
      return Array.from(tbody.querySelectorAll("tr")).filter(function (tr) {
        return tr.getAttribute("data-status") != null;
      });
    }

    function getCompanyDataRows() {
      if (!projectsTableCompany) return [];
      const tbody = projectsTableCompany.querySelector("tbody");
      if (!tbody) return [];
      return Array.from(tbody.querySelectorAll("tr")).filter(function (tr) {
        const td = tr.querySelector("td[colspan]");
        return !td;
      });
    }

    function parseDateRangeInput() {
      const input = document.getElementById("datepicker-range");
      if (!input || !input.value || typeof input.value !== "string") return null;
      const parts = input.value.split(/\s+to\s+|\s+-\s+/).map(function (s) { return s.trim(); });
      if (parts.length !== 2) return null;
      const d1 = new Date(parts[0]);
      const d2 = new Date(parts[1]);
      if (isNaN(d1.getTime()) || isNaN(d2.getTime())) return null;
      return [parts[0], parts[1]];
    }

    function rowMatchesDepartmentFilters(row, statusVal, priorityVal, dateRange) {
      if (statusVal && statusVal !== "all" && (row.getAttribute("data-status") || "") !== statusVal) return false;
      if (priorityVal && priorityVal !== "all" && (row.getAttribute("data-priority") || "") !== priorityVal) return false;
      if (dateRange && dateRange.length === 2) {
        const start = row.getAttribute("data-start-date") || "";
        const end = row.getAttribute("data-end-date") || "";
        const filterStart = new Date(dateRange[0]);
        const filterEnd = new Date(dateRange[1]);
        filterStart.setHours(0, 0, 0, 0);
        filterEnd.setHours(23, 59, 59, 999);
        var inRange = false;
        if (start) {
          var d = new Date(start);
          d.setHours(0, 0, 0, 0);
          if (d >= filterStart && d <= filterEnd) inRange = true;
        }
        if (!inRange && end) {
          var d = new Date(end);
          d.setHours(23, 59, 59, 999);
          if (d >= filterStart && d <= filterEnd) inRange = true;
        }
        if (!inRange && start && end) {
          var ps = new Date(start);
          var pe = new Date(end);
          ps.setHours(0, 0, 0, 0);
          pe.setHours(23, 59, 59, 999);
          if (ps <= filterEnd && pe >= filterStart) inRange = true;
        }
        if (!inRange) return false;
      }
      return true;
    }

    function renderPaginationUl(container, currentPage, totalPages, goToPage) {
      if (!container) return;
      container.innerHTML = "";
      if (totalPages <= 0) return;

      var prevLi = document.createElement("li");
      prevLi.className = "page-item" + (currentPage <= 1 ? " disabled" : "");
      prevLi.innerHTML = '<a class="page-link" href="javascript:void(0);" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>';
      if (currentPage > 1) {
        prevLi.querySelector("a").addEventListener("click", function (e) { e.preventDefault(); goToPage(currentPage - 1); });
      }
      container.appendChild(prevLi);

      var start = Math.max(1, currentPage - 2);
      var end = Math.min(totalPages, currentPage + 2);
      for (var p = start; p <= end; p++) {
        (function (page) {
          var li = document.createElement("li");
          li.className = "page-item" + (page === currentPage ? " active" : "");
          var a = document.createElement("a");
          a.className = "page-link";
          a.href = "javascript:void(0);";
          a.textContent = page;
          a.addEventListener("click", function (e) { e.preventDefault(); goToPage(page); });
          li.appendChild(a);
          container.appendChild(li);
        })(p);
      }

      var nextLi = document.createElement("li");
      nextLi.className = "page-item" + (currentPage >= totalPages ? " disabled" : "");
      nextLi.innerHTML = '<a class="page-link" href="javascript:void(0);" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>';
      if (currentPage < totalPages) {
        nextLi.querySelector("a").addEventListener("click", function (e) { e.preventDefault(); goToPage(currentPage + 1); });
      }
      container.appendChild(nextLi);
    }

    function applyDepartmentPagination() {
      var statusVal = (document.getElementById("statusFilter") && document.getElementById("statusFilter").value) || "all";
      var priorityVal = (document.getElementById("priorityFilter") && document.getElementById("priorityFilter").value) || "all";
      var dateRange = parseDateRangeInput();

      var allRows = getDepartmentDataRows();
      var filtered = allRows.filter(function (row) { return rowMatchesDepartmentFilters(row, statusVal, priorityVal, dateRange); });
      var total = filtered.length;
      var totalPages = total === 0 ? 0 : Math.max(1, Math.ceil(total / PAGE_SIZE));
      departmentPage = totalPages === 0 ? 1 : Math.min(Math.max(1, departmentPage), totalPages);

      var startIdx = (departmentPage - 1) * PAGE_SIZE;
      var endIdx = Math.min(startIdx + PAGE_SIZE, total);

      allRows.forEach(function (row) {
        row.style.display = "none";
      });
      filtered.forEach(function (row, i) {
        if (i >= startIdx && i < endIdx) row.style.display = "";
      });

      if (projectsTableSummary) {
        if (total === 0) {
          projectsTableSummary.textContent = "Showing 0 to 0 of 0 results";
        } else {
          projectsTableSummary.textContent = "Showing " + (startIdx + 1) + " to " + endIdx + " of " + total + " results";
        }
      }
      renderPaginationUl(projectsTablePagination, departmentPage, totalPages, function (p) {
        departmentPage = p;
        applyDepartmentPagination();
      });
    }

    function applyCompanyPagination() {
      var allRows = getCompanyDataRows();
      var total = allRows.length;
      var totalPages = total === 0 ? 0 : Math.max(1, Math.ceil(total / PAGE_SIZE));
      companyPage = totalPages === 0 ? 1 : Math.min(Math.max(1, companyPage), totalPages);

      var startIdx = (companyPage - 1) * PAGE_SIZE;
      var endIdx = Math.min(startIdx + PAGE_SIZE, total);

      allRows.forEach(function (row, i) {
        row.style.display = (i >= startIdx && i < endIdx) ? "" : "none";
      });

      if (projectsTableCompanySummary) {
        if (total === 0) {
          projectsTableCompanySummary.textContent = "Showing 0 to 0 of 0 results";
        } else {
          projectsTableCompanySummary.textContent = "Showing " + (startIdx + 1) + " to " + endIdx + " of " + total + " results";
        }
      }
      renderPaginationUl(projectsTableCompanyPagination, companyPage, totalPages, function (p) {
        companyPage = p;
        applyCompanyPagination();
      });
    }

    if (projectsTable && projectsTablePagination) {
      applyDepartmentPagination();

      var statusFilter = document.getElementById("statusFilter");
      var priorityFilter = document.getElementById("priorityFilter");
      var datepickerRange = document.getElementById("datepicker-range");

      if (statusFilter) {
        statusFilter.addEventListener("change", function () {
          departmentPage = 1;
          applyDepartmentPagination();
        });
      }
      if (priorityFilter) {
        priorityFilter.addEventListener("change", function () {
          departmentPage = 1;
          applyDepartmentPagination();
        });
      }
      if (datepickerRange) {
        datepickerRange.addEventListener("change", function () {
          departmentPage = 1;
          applyDepartmentPagination();
        });
        datepickerRange.addEventListener("input", function () {
          departmentPage = 1;
          applyDepartmentPagination();
        });
      }
    }

    if (projectsTableCompany && projectsTableCompanyPagination) {
      applyCompanyPagination();
    }
  });
})();
