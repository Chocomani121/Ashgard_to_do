
document.addEventListener('DOMContentLoaded', () => {
    const tableData = [];
    const rows = document.querySelectorAll('#projectsTable tbody tr');

    // Extract data from hidden table
    rows.forEach(row => {
        const category = row.getAttribute('data-category');
        const cells = row.querySelectorAll('td');
        tableData.push([
            cells[0].innerText.trim(),  // Department Name
            cells[1].innerText.trim(),  // Total Members
            cells[2].innerText.trim(),  // Created On
            cells[3].innerHTML.trim(),  // Action buttons
            category                    // for filtering
        ]);
    });

    // Initialize Grid.js
    const grid = new gridjs.Grid({
        columns: ["Department Name", "Total Members", "Created On", "Action"],
        data: tableData,
        search: true,
        pagination: {
            enabled: true,
            limit: 5
        },
        sort: true,
        style: {
            table: { 'width': '100%' },
            th: { 'text-align': 'left' }
        }
    }).render(document.getElementById("table-gridjs"));

    // Filter by dropdown
    const select = document.getElementById('categorySelect');
    select.addEventListener('change', () => {
        const selected = select.value;

        grid.updateConfig({
            data: tableData.filter(row => selected === "All" || row[4] === selected)
        }).forceRender();
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
