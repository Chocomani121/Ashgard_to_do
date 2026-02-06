/*
Template Name: webadmin - Admin & Dashboard Template
Author: Themesdesign
Website: https://Themesdesign.com/
Contact: Themesdesign@gmail.com
File: grid Js File
*/

// 1. Department-Wide Projects Table (with filters)
/*
Template Name: webadmin - Admin & Dashboard Template
*/

document.addEventListener('DOMContentLoaded', function() {
    const tableEl = document.getElementById("companyWideReport");
    const containerEl = document.getElementById("table11-gridjs");
    const dateInput = document.getElementById('datepicker-range');
    const searchInput = document.getElementById('custom-grid-search'); // Our new input

    if (!tableEl || !containerEl) return;

    // 1. Extract clean data (include reportId and nameText for clickable Name)
    const rows = Array.from(tableEl.querySelectorAll('tbody tr.company-wide-report-list-item'));
    const allData = rows.map(tr => {
        const tds = tr.querySelectorAll('td');
        const cells = Array.from(tds).map(td => gridjs.html(td.innerHTML));
        return {
            reportId: tr.getAttribute('data-report-id'),
            start: tr.getAttribute('data-start'),
            text: tr.innerText.toLowerCase(),
            nameText: tds[0] ? tds[0].innerText.trim() : '',
            cells: cells
        };
    });

    // One cell per column: [Name payload, Start, End, Reviewer] so columns align
    function rowToGridData(r) {
        return [[r.reportId, r.nameText], r.cells[1], r.cells[2], r.cells[3]];
    }

    // 2. Initialize Grid.js with clickable Name column
    const grid = new gridjs.Grid({
        columns: [
            {
                name: 'Name',
                formatter: (cell) => {
                    var id = '';
                    var name = '';
                    if (Array.isArray(cell) && cell.length >= 2) {
                        id = cell[0] != null ? String(cell[0]) : '';
                        name = cell[1] != null ? String(cell[1]) : '';
                    }
                    return gridjs.html(
                        '<a href="javascript:void(0)" class="company-wide-report-name-link text-dark text-decoration-none" data-report-id="' + escapeHtml(id) + '">' + escapeHtml(name) + '</a>'
                    );
                }
            },
            'Start',
            'End',
            'Reviewer'
        ],
        data: allData.map(rowToGridData),
        sort: true,
        pagination: { limit: 12 },
        search: false,
        style: {
            table: { 'font-size': '0.9rem' },
            th: { 'background-color': '#f8f9fa', 'color': '#495057', 'text-align': 'center' }
        }
    }).render(containerEl);

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 3. COMBINED FILTER LOGIC (Search + Date)
    function applyFilters() {
        const searchTerm = searchInput.value.toLowerCase();
        let startRange = null;
        let endRange = null;

        // Get dates if flatpickr is active
        if (dateInput._flatpickr && dateInput._flatpickr.selectedDates.length === 2) {
            startRange = dateInput._flatpickr.selectedDates[0].setHours(0,0,0,0);
            endRange = dateInput._flatpickr.selectedDates[1].setHours(23,59,59,999);
        }

        const filtered = allData.filter(row => {
            const matchesSearch = row.text.includes(searchTerm);
            let matchesDate = true;

            if (startRange && endRange) {
                const itemDate = new Date(row.start).getTime();
                matchesDate = itemDate >= startRange && itemDate <= endRange;
            }

            return matchesSearch && matchesDate;
        });

        grid.updateConfig({ data: filtered.map(rowToGridData) }).forceRender();
    }

    // 4. Delegate click on name link -> open report modal
    const reportsDataEl = document.getElementById('reports-data');
    if (reportsDataEl && typeof bootstrap !== 'undefined') {
        const reportsData = JSON.parse(reportsDataEl.textContent);
        const modalEl = document.getElementById('companyWideReportModal');
        const bsModal = modalEl ? new bootstrap.Modal(modalEl) : null;
        containerEl.addEventListener('click', function(e) {
            const link = e.target.closest('.company-wide-report-name-link');
            if (!link || !bsModal) return;
            const reportId = link.getAttribute('data-report-id');
            const report = reportsData.find(function(r) { return r.report_id == reportId; });
            if (!report) return;
            document.getElementById('companyWideModalTitle').textContent = 'Weekly-' + (report.author_name || '') + ' (' + (report.week_name || '') + ')';
            document.getElementById('companyWideModalReviewer').textContent = report.reviewer_name || '—';
            document.getElementById('companyWideModalCC').textContent = report.cc_names || '—';
            document.getElementById('companyWideModalDepartment').textContent = report.department_name || '—';
            document.getElementById('companyWideModalCreated').textContent = report.created_on || '—';
            document.getElementById('companyWideModalBody').innerHTML = report.report_content || '';
            bsModal.show();
        });
    }

    // Listen for typing (Search)
    searchInput.addEventListener('input', applyFilters);

    // Listen for Date changes
    if (dateInput && typeof flatpickr !== 'undefined') {
        flatpickr(dateInput, {
            mode: "range",
            dateFormat: "Y-m-d",
            onChange: applyFilters,
            onClear: applyFilters
        });
    }
});

