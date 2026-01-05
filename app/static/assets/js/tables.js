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
