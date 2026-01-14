const owners = [
    { id: 1, name: "Kathrina Mirasol", initials: "KM", color: "#6f42c1" },
    { id: 2, name: "Windyl Orbeta", initials: "WO", color: "#0d6efd" },
    { id: 3, name: "Patrick Genon", initials: "PG", color: "#198754" },
    { id: 4, name: "Neil Javerle", initials: "NJ", color: "#dc3545" },
    { id: 5, name: "Lurs Lastimosa", initials: "LL", color: "#fd7e14" }
];

const ownerList = document.querySelector(".owner-list");
const ownerInput = document.getElementById("ownerInput");
const ownerSearch = document.getElementById("ownerSearch");

let selectedOwners = [];

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
        ownerInput.innerHTML = `<span class="text-muted small">Select Members</span>`;
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
function removeOwner(id) {
    selectedOwners = selectedOwners.filter(o => o.id !== id);
    renderSelected();
    renderOwners(ownerSearch.value);
}

// Search
ownerSearch.addEventListener("input", e => {
    renderOwners(e.target.value);
});

// Clear
document.getElementById("clearOwners").onclick = () => {
    selectedOwners = [];
    renderSelected();
    renderOwners();
};

// Init
renderOwners();
renderSelected();



// Note Reply and Edit Functionality//
function toggleInput(btn, className) {
    // 1. Find the parent container for this specific thread item
    const parent = btn.closest('.flex-grow-1');
    
    // 2. Hide any other open boxes in this specific item
    parent.querySelectorAll('.reply-box, .edit-box').forEach(box => {
        if (!box.classList.contains(className.substring(1))) {
            box.classList.add('d-none');
        }
    });

    // 3. Toggle the box we want
    const target = parent.querySelector(className);
    target.classList.toggle('d-none');

    // 4. Auto-focus the input if it's now visible
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
function confirmDelete(taskId) {
 Swal.fire({
        title: "Are you sure?",
        text: "You won't be able to revert this!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#51d28c",
        cancelButtonColor: "#f34e4e",
        confirmButtonText: "Yes, delete it!"
      }).then(function (result) {
        if (result.value) {
          Swal.fire("Deleted!", "Deleted Successfully.", "success"
          );
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

//JS for PIN in activity threads
document.querySelectorAll('.pin-btn').forEach(btn => {
    btn.addEventListener('click', e => {
        e.stopPropagation();

        const box = btn.closest('.message-box');
        box.classList.toggle('pinned');

        const icon = btn.querySelector('i');
        icon.classList.toggle('mdi-pin-outline');
        icon.classList.toggle('mdi-pin');
    });
});