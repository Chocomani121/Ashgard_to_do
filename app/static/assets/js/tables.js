// Filtering tables based on dropdown selection
document.addEventListener("DOMContentLoaded", function () {

    // Department table rows
    const deptRows = document.querySelectorAll("#firstRowOnlyTable tbody tr");
    // Projects table rows
    const projectRows = document.querySelectorAll("#itemTable tbody tr");

    // 1️⃣ Department table: show only first row
    deptRows.forEach((row, index) => { 
        if (index > 0) row.style.display = "none"; 
    });

    // 2️⃣ Projects table: show all rows initially (as if "All" is selected)
    projectRows.forEach((row) => { 
        row.style.display = ""; 
    });

    // 3️⃣ Dropdown
    const categorySelect = document.getElementById("categorySelect");

    categorySelect.addEventListener("change", function () {
        const selectedCategory = this.value;

        // Filter Projects table
        projectRows.forEach(row => {
            const rowCategory = row.getAttribute("data-category");
            if (selectedCategory === "All") {
                row.style.display = ""; // show all
            } else {
                row.style.display = (rowCategory === selectedCategory) ? "" : "none";
            }
        });

        // Filter Department table (first-row behavior kept)
        deptRows.forEach((row, index) => {
            const rowCategory = row.getAttribute("data-category");
            if (selectedCategory !== "All" && rowCategory === selectedCategory) {
                row.style.display = "";
            } else if (index === 0 && selectedCategory === "All") {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    });

});


// Initializing DataTable with custom settings  
$(document).ready(function () {

    const table = $('#projectsTable').DataTable({
        paging: true,
        pageLength: 5,
        lengthChange: false,
        ordering: true,
        info: true,
        responsive: true,
        columnDefs: [
            { orderable: false, targets: 0 }
        ],
        dom: 'rt<"d-flex justify-content-between align-items-center mt-2"ip>'
    });

    // Custom search input
    $('.email-search input').on('keyup', function () {
        table.search(this.value).draw();
    });

});
