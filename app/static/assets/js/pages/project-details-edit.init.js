/*
Page: project_details.html
Purpose: Edit Project modal – Edit Project Manager + Edit Members (chip UI, pre-filled)
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
    const usersEl = document.getElementById("edit-project-users-data");
    const initialEl = document.getElementById("edit-project-initial-members");
    if (!usersEl) return;

    let allUsersData = [];
    let initialMembers = [];
    try {
      allUsersData = JSON.parse(usersEl.textContent || "[]");
    } catch (e) {
      return;
    }
    try {
      if (initialEl) initialMembers = JSON.parse(initialEl.textContent || "[]");
    } catch (e) {}

    const ownerInputEdit = document.getElementById("ownerInputEditProject");
    const ownerListEdit = document.querySelector(".owner-list-edit-project");
    const ownerSearchEdit = document.getElementById("ownerSearchEditProject");
    const clearBtnEdit = document.getElementById("clearOwnersEditProject");
    const confirmBtnEdit = document.getElementById("confirmOwnersEditProject");
    const editForm = document.getElementById("editProjectMembersForm");

    if (!ownerInputEdit || !ownerListEdit) return;

    const colors = ["#6f42c1", "#0d6efd", "#198754", "#dc3545", "#fd7e14", "#20c997", "#ffc107", "#6610f2"];
    const allUsers = allUsersData.map((user, index) => ({
      id: user.member_id,
      name: user.name || user.username,
      initials: getInitials(user.name || user.username),
      color: colors[index % colors.length],
    }));

    let selectedEditMembers = [];

    function renderListEdit(filter) {
      ownerListEdit.innerHTML = "";
      let list = allUsers;
      if (filter) {
        const f = String(filter).toLowerCase();
        list = list.filter((m) => (m.name || "").toLowerCase().includes(f));
      }
      if (list.length === 0) {
        const empty = document.createElement("div");
        empty.className = "list-group-item text-muted text-center";
        empty.textContent = "No members found";
        ownerListEdit.appendChild(empty);
        return;
      }
      list.forEach((owner) => {
        const item = document.createElement("div");
        item.className = "list-group-item owner-item";
        if (selectedEditMembers.some((o) => o.id === owner.id)) item.classList.add("active");
        item.innerHTML =
          `<div class="owner-avatar" style="background:${owner.color}">${owner.initials}</div><span>${owner.name}</span>`;
        item.onclick = function () {
          const i = selectedEditMembers.findIndex((o) => o.id === owner.id);
          if (i >= 0) selectedEditMembers.splice(i, 1);
          else selectedEditMembers.push(owner);
          renderChipsEdit();
          renderListEdit(ownerSearchEdit ? ownerSearchEdit.value : "");
        };
        ownerListEdit.appendChild(item);
      });
    }

    function renderChipsEdit() {
      ownerInputEdit.innerHTML = "";
      if (selectedEditMembers.length === 0) {
        ownerInputEdit.innerHTML = '<span class="text-muted small">Select member(s)</span>';
        return;
      }
      selectedEditMembers.forEach((owner) => {
        const chip = document.createElement("div");
        chip.className = "owner-chip";
        chip.innerHTML = `${owner.name} <span data-owner-remove="${owner.id}">&times;</span>`;
        ownerInputEdit.appendChild(chip);
      });
      ownerInputEdit.querySelectorAll("[data-owner-remove]").forEach((el) => {
        el.addEventListener("click", function (e) {
          e.stopPropagation();
          const id = parseInt(e.currentTarget.getAttribute("data-owner-remove"), 10);
          if (!Number.isFinite(id)) return;
          selectedEditMembers = selectedEditMembers.filter((o) => o.id !== id);
          renderChipsEdit();
          renderListEdit(ownerSearchEdit ? ownerSearchEdit.value : "");
        });
      });
    }

    function prefillFromInitial() {
      selectedEditMembers = initialMembers
        .map((m) => {
          const u = allUsers.find((x) => x.id === m.member_id);
          return u ? { id: u.id, name: u.name, initials: u.initials, color: u.color } : null;
        })
        .filter(Boolean);
      renderChipsEdit();
      renderListEdit("");
    }

    const editMembersModal = document.getElementById("editMembersModal");
    if (editMembersModal) {
      editMembersModal.addEventListener("show.bs.modal", function () {
        prefillFromInitial();
        if (ownerSearchEdit) ownerSearchEdit.value = "";
      });
    }

    if (ownerSearchEdit) {
      ownerSearchEdit.addEventListener("input", function () {
        renderListEdit(this.value);
      });
    }

    if (clearBtnEdit) {
      clearBtnEdit.addEventListener("click", function (e) {
        e.preventDefault();
        selectedEditMembers = [];
        renderChipsEdit();
        renderListEdit(ownerSearchEdit ? ownerSearchEdit.value : "");
      });
    }

    if (confirmBtnEdit) {
      confirmBtnEdit.addEventListener("click", function () {
        const bs = window.bootstrap && window.bootstrap.Dropdown;
        if (bs && ownerInputEdit) {
          const d = bs.getInstance(ownerInputEdit);
          if (d) d.hide();
        }
      });
    }

    if (editForm) {
      editForm.addEventListener("submit", function (e) {
        if (selectedEditMembers.length === 0) {
          e.preventDefault();
          if (typeof Swal !== "undefined") {
            Swal.fire({ icon: "warning", text: "Please select at least one member." });
          } else {
            alert("Please select at least one member.");
          }
          return false;
        }
        const container = document.getElementById("editMemberIdsContainer");
        if (container) {
          container.innerHTML = "";
          selectedEditMembers.forEach(function (member) {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = "project_members";
            input.value = member.id;
            container.appendChild(input);
          });
        }
      });
    }

    renderChipsEdit();
    renderListEdit("");
  });
})();
