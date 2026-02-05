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

    // 1. Extract clean data
    const rows = Array.from(tableEl.querySelectorAll('tbody tr.company-wide-report-list-item'));
    const allData = rows.map(tr => ({
        start: tr.getAttribute('data-start'),
        // Store text version for searching
        text: tr.innerText.toLowerCase(),
        cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML))
    }));

    // 2. Initialize Grid.js (Search set to FALSE to prevent focus bug)
    const grid = new gridjs.Grid({
        columns: ["Name", "Start", "End", "Reviewer"],
        data: allData.map(r => r.cells),
        sort: true,
        pagination: { limit: 12 },
        search: false, // We handle search manually now
        style: {
            table: { 'font-size': '0.9rem' },
            th: { 'background-color': '#f8f9fa', 'color': '#495057', 'text-align': 'center' }
        }
    }).render(containerEl);

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

        grid.updateConfig({ data: filtered.map(r => r.cells) }).forceRender();
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