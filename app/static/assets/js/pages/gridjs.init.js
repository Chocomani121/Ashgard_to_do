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
/*
Template Name: webadmin - Admin & Dashboard Template
Author: Themesdesign
Website: https://Themesdesign.com/
Contact: Themesdesign@gmail.com
File: grid Js File
*/


// 1. Department-Wide Projects Table (with filters)
document.addEventListener('DOMContentLoaded', function() {
    let grid1 = null;
    let allData1 = [];
    let currentFilters1 = {
        status: 'all',
        priority: 'all',
        dateRange: null,
        search: ''
    };
    
    function initDepartmentWideProjectsGrid() {
        const tableElement = document.getElementById("projectsTable");
        const gridContainer = document.getElementById("table-gridjs");
        
        if (!tableElement || !gridContainer) {
            return false;
        }
        
        if (typeof gridjs === 'undefined') {
            return false;
        }
        
        try {
            // Extract data from table rows with all metadata
            const tableRows = Array.from(tableElement.querySelectorAll('tbody tr'));
            allData1 = tableRows.map(tr => ({
                status: tr.getAttribute('data-status') || '',
                priority: tr.getAttribute('data-priority') || '',
                startDate: tr.getAttribute('data-start-date') || '',
                endDate: tr.getAttribute('data-end-date') || '',
                cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML)),
                searchText: Array.from(tr.querySelectorAll('td')).map(td => td.textContent || '').join(' ').toLowerCase()
            }));
            
            // Filter function
            const getFilteredData = () => {
                return allData1.filter(row => {
                    // Search filter
                    if (currentFilters1.search && !row.searchText.includes(currentFilters1.search.toLowerCase())) {
                        return false;
                    }
                    
                    // Status filter
                    if (currentFilters1.status !== 'all' && row.status !== currentFilters1.status) {
                        return false;
                    }
                    
                    // Priority filter
                    if (currentFilters1.priority !== 'all' && row.priority !== currentFilters1.priority) {
                        return false;
                    }
                    
                    // Date range filter
                    if (currentFilters1.dateRange && currentFilters1.dateRange.length === 2) {
                        const filterStart = new Date(currentFilters1.dateRange[0]);
                        const filterEnd = new Date(currentFilters1.dateRange[1]);
                        filterStart.setHours(0, 0, 0, 0);
                        filterEnd.setHours(23, 59, 59, 999);
                        
                        let hasDateInRange = false;
                        
                        if (row.startDate) {
                            const projectStart = new Date(row.startDate);
                            projectStart.setHours(0, 0, 0, 0);
                            if (projectStart >= filterStart && projectStart <= filterEnd) {
                                hasDateInRange = true;
                            }
                        }
                        
                        if (!hasDateInRange && row.endDate) {
                            const projectEnd = new Date(row.endDate);
                            projectEnd.setHours(23, 59, 59, 999);
                            if (projectEnd >= filterStart && projectEnd <= filterEnd) {
                                hasDateInRange = true;
                            }
                        }
                        
                        if (!hasDateInRange && row.startDate && row.endDate) {
                            const projectStart = new Date(row.startDate);
                            const projectEnd = new Date(row.endDate);
                            projectStart.setHours(0, 0, 0, 0);
                            projectEnd.setHours(23, 59, 59, 999);
                            
                            if ((projectStart <= filterEnd && projectEnd >= filterStart)) {
                                hasDateInRange = true;
                            }
                        }
                        
                        if (!hasDateInRange) {
                            return false;
                        }
                    }
                    
                    return true;
                });
            };
            
            // Initialize Grid.js
            grid1 = new gridjs.Grid({
                columns: ["Project Name", "Priority", "Start Date", "Deadline", "Status", "Progress", "Project Manager", "Client", "Last Tasks"],
                data: getFilteredData().map(row => row.cells),
                pagination: { limit: 10 },
                sort: true,
                search: false, // Disable built-in search, handle manually
                className: { table: "table table-centered align-middle" }
            }).render(gridContainer);
            setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
            
            // Update grid function
            const updateGrid = () => {
                if (grid1) {
                    const filteredData = getFilteredData().map(row => row.cells);
                    grid1.updateConfig({ data: filteredData }).forceRender();
                    setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
                }
            };
            
            // Handle status filter
            const statusFilter = document.getElementById('statusFilter');
            if (statusFilter) {
                statusFilter.addEventListener('change', function() {
                    currentFilters1.status = this.value;
                    updateGrid();
                });
            }
            
            // Handle priority filter
            const priorityFilter = document.getElementById('priorityFilter');
            if (priorityFilter) {
                priorityFilter.addEventListener('change', function() {
                    currentFilters1.priority = this.value;
                    updateGrid();
                });
            }
            
            // Handle search input
            const searchInput1 = document.getElementById('searchDeptProjects');
            if (searchInput1) {
                let searchTimeout1;
                searchInput1.addEventListener('input', function() {
                    clearTimeout(searchTimeout1);
                    searchTimeout1 = setTimeout(() => {
                        currentFilters1.search = this.value.trim();
                        updateGrid();
                    }, 300);
                });
            }
            
            // Initialize Flatpickr date range picker
            const dateRangeInput = document.getElementById('datepicker-range');
            if (dateRangeInput) {
                const initDatePicker = () => {
                    if (typeof flatpickr !== 'undefined') {
                        flatpickr(dateRangeInput, {
                            mode: 'range',
                            dateFormat: 'Y-m-d',
                            placeholder: 'Select Date Range',
                            onChange: function(selectedDates, dateStr, instance) {
                                if (selectedDates.length === 2) {
                                    currentFilters1.dateRange = [
                                        selectedDates[0].toISOString().split('T')[0],
                                        selectedDates[1].toISOString().split('T')[0]
                                    ];
                                    updateGrid();
                                } else if (selectedDates.length === 1) {
                                    // Single date: filter to projects active on that day (same start and end)
                                    const d = selectedDates[0].toISOString().split('T')[0];
                                    currentFilters1.dateRange = [d, d];
                                    updateGrid();
                                } else if (selectedDates.length === 0) {
                                    currentFilters1.dateRange = null;
                                    updateGrid();
                                }
                            }
                        });
                    } else {
                        setTimeout(initDatePicker, 100);
                    }
                };
                initDatePicker();
            }
            
            return true;
        } catch (error) {
            console.error('Department-Wide Projects Grid initialization error:', error);
            return false;
        }
    }
    
    // Try to initialize immediately, then retry if Grid.js not ready
    if (!initDepartmentWideProjectsGrid()) {
        let attempts = 0;
        const checkInterval = setInterval(function() {
            attempts++;
            if (initDepartmentWideProjectsGrid()) {
                clearInterval(checkInterval);
            } else if (attempts >= 50) {
                clearInterval(checkInterval);
                console.warn('Department-Wide Projects: Failed to initialize after 5 seconds');
            }
        }, 100);
    }
});

// 2. Company-Wide Projects (search filter)
document.addEventListener('DOMContentLoaded', function() {
    const tbl = document.getElementById("projectsTableCompany");
    const container = document.getElementById("table2-gridjs");
    if (!tbl || !container || typeof gridjs === 'undefined') return;

    const rows = Array.from(tbl.querySelectorAll('tbody tr'));
    const allData2 = rows.map(tr => ({
        cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML)),
        searchText: Array.from(tr.querySelectorAll('td')).map(td => td.textContent || '').join(' ').toLowerCase()
    }));

    let search2 = '';
    const filtered = () => allData2.filter(row => !search2 || row.searchText.includes(search2.toLowerCase()));
    const grid2 = new gridjs.Grid({
        columns: ["Project Name", "Start Date", "Deadline", "Status", "Progress", "Project Manager", "Client", "Department", "Last Tasks"],
        data: filtered().map(row => row.cells),
        pagination: { limit: 10 },
        sort: true,
        search: false,
        className: { table: "table table-centered align-middle" }
    }).render(container);
    setTimeout(function() { applyProgressBarWidths(container); }, 100);

    const searchEl = document.getElementById('searchCompanyProjects');
    if (searchEl) {
        let t;
        searchEl.addEventListener('input', function() {
            clearTimeout(t);
            t = setTimeout(() => {
                search2 = this.value.trim();
                grid2.updateConfig({ data: filtered().map(row => row.cells) }).forceRender();
                setTimeout(function() { applyProgressBarWidths(container); }, 0);
            }, 300);
        });
    }
});

// 3. Task Table
const table3Req = document.getElementById("projectsTableTask");
const table3Res = document.getElementById("table3-gridjs");
if (table3Req && table3Res) {
    new gridjs.Grid({
        from: table3Req,
        pagination: { limit: 10 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table3Res);
}

// 4. Profile Table
const table4Req = document.getElementById("projectsTableProfile");
const table4Res = document.getElementById("table4-gridjs");
if (table4Req && table4Res) {
    new gridjs.Grid({
        from: table4Req,
        pagination: { limit: 10 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table4Res);
}

// 5. Task Details Table
const table5Req = document.getElementById("projectsTableTaskDetails");
const table5Res = document.getElementById("table5-gridjs");
if (table5Req && table5Res) {
    new gridjs.Grid({
        from: table5Req,
        pagination: { limit: 10 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table5Res);
}

// 5. Task Details Table PM
const table6Req = document.getElementById("projectsTableTaskDetailsPM");
const table6Res = document.getElementById("table6-gridjs");
if (table6Req && table6Res) {
    new gridjs.Grid({
        from: table6Req,
        pagination: { limit: 10 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table6Res);
}

//Members table
const table7Req = document.getElementById("projectsTableMembers");
const table7Res = document.getElementById("table7-gridjs");
if (table7Req && table7Res) {
    new gridjs.Grid({
        from: table7Req,
        pagination: { limit: 10 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table7Res);
}

// 6. Department Projects Table (from all_departments.html)
document.addEventListener('DOMContentLoaded', function() {
    let grid = null;
    let allData = [];
    let currentFilters = {
        department: 'All',
        status: 'all',
        priority: 'all',
        dateRange: null,
        search: ''
    };
    
    function initDeptProjectsGrid() {
        const tableElement = document.getElementById('projectsTableDept');
        const gridContainer = document.getElementById("tableDept-gridjs");
        const dropdownButton = document.getElementById('categorySelect');
        const dropdownMenu = dropdownButton?.closest('.btn-group')?.querySelectorAll('.dropdown-item') || [];
        
        // Check if elements exist and Grid.js is available
        if (!tableElement || !gridContainer || !dropdownButton || dropdownMenu.length === 0) {
            return false;
        }
        
        if (typeof gridjs === 'undefined') {
            return false;
        }
        
        try {
            // Extract data from table rows with all metadata
            const tableRows = Array.from(tableElement.querySelectorAll('tbody tr'));
            allData = tableRows.map(tr => ({
                category: tr.getAttribute('data-category') || '',
                status: tr.getAttribute('data-status') || '',
                priority: tr.getAttribute('data-priority') || '',
                startDate: tr.getAttribute('data-start-date') || '',
                endDate: tr.getAttribute('data-end-date') || '',
                cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML)),
                searchText: Array.from(tr.querySelectorAll('td')).map(td => td.textContent || '').join(' ').toLowerCase()
            }));
            
            // Filter function
            const getFilteredData = () => {
                return allData.filter(row => {
                    // Search filter
                    if (currentFilters.search && !row.searchText.includes(currentFilters.search.toLowerCase())) {
                        return false;
                    }
                    
                    // Department filter
                    if (currentFilters.department !== 'All' && row.category !== currentFilters.department) {
                        return false;
                    }
                    
                    // Status filter
                    if (currentFilters.status !== 'all' && row.status !== currentFilters.status) {
                        return false;
                    }
                    
                    // Priority filter
                    if (currentFilters.priority !== 'all' && row.priority !== currentFilters.priority) {
                        return false;
                    }
                    
                    // Date range filter
                    if (currentFilters.dateRange && currentFilters.dateRange.length === 2) {
                        const filterStart = new Date(currentFilters.dateRange[0]);
                        const filterEnd = new Date(currentFilters.dateRange[1]);
                        filterStart.setHours(0, 0, 0, 0);
                        filterEnd.setHours(23, 59, 59, 999);
                        
                        let hasDateInRange = false;
                        
                        if (row.startDate) {
                            const projectStart = new Date(row.startDate);
                            projectStart.setHours(0, 0, 0, 0);
                            if (projectStart >= filterStart && projectStart <= filterEnd) {
                                hasDateInRange = true;
                            }
                        }
                        
                        if (!hasDateInRange && row.endDate) {
                            const projectEnd = new Date(row.endDate);
                            projectEnd.setHours(23, 59, 59, 999);
                            if (projectEnd >= filterStart && projectEnd <= filterEnd) {
                                hasDateInRange = true;
                            }
                        }
                        
                        if (!hasDateInRange && row.startDate && row.endDate) {
                            const projectStart = new Date(row.startDate);
                            const projectEnd = new Date(row.endDate);
                            projectStart.setHours(0, 0, 0, 0);
                            projectEnd.setHours(23, 59, 59, 999);
                            
                            if ((projectStart <= filterEnd && projectEnd >= filterStart)) {
                                hasDateInRange = true;
                            }
                        }
                        
                        if (!hasDateInRange) {
                            return false;
                        }
                    }
                    
                    return true;
                });
            };
            
            // Initialize Grid.js
            grid = new gridjs.Grid({
                columns: ["Project Name", "Priority", "Start Date", "Deadline", "Status", "Progress", "Project Manager", "Client", "Last Tasks"],
                data: getFilteredData().map(row => row.cells),
                pagination: { limit: 10 },
                sort: true,
                search: false, // Disable built-in search, handle manually
                className: {
                    table: 'table table-bordered'
                }
            }).render(gridContainer);
            setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
            
            // Update grid function
            const updateGrid = () => {
                if (grid) {
                    const filteredData = getFilteredData().map(row => row.cells);
                    grid.updateConfig({ data: filteredData }).forceRender();
                    setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
                }
            };
            
            // Handle search input
            const searchInput = document.getElementById('searchDeptProjects');
            if (searchInput) {
                let searchTimeout;
                searchInput.addEventListener('input', function() {
                    clearTimeout(searchTimeout);
                    searchTimeout = setTimeout(() => {
                        currentFilters.search = this.value;
                        updateGrid();
                    }, 300);
                });
            }
            
            // Handle department dropdown filtering
            dropdownMenu.forEach(item => {
                item.addEventListener('click', function(event) {
                    event.preventDefault();
                    const selectedValue = this.getAttribute('data-value');
                    dropdownButton.innerHTML = `${this.textContent} <i class="mdi mdi-chevron-down"></i>`;
                    currentFilters.department = selectedValue || "All";
                    updateGrid();
                });
            });
            
            // Handle status filter
            const statusFilter = document.getElementById('statusFilterDept');
            if (statusFilter) {
                statusFilter.addEventListener('change', function() {
                    currentFilters.status = this.value;
                    updateGrid();
                });
            }
            
            // Handle priority filter
            const priorityFilter = document.getElementById('priorityFilterDept');
            if (priorityFilter) {
                priorityFilter.addEventListener('change', function() {
                    currentFilters.priority = this.value;
                    updateGrid();
                });
            }
            
            // Initialize Flatpickr date range picker
            const dateRangeInput = document.getElementById('datepicker-range-dept');
            if (dateRangeInput) {
                // Wait for flatpickr to be available
                const initDatePicker = () => {
                    if (typeof flatpickr !== 'undefined') {
                        flatpickr(dateRangeInput, {
                            mode: 'range',
                            dateFormat: 'Y-m-d',
                            placeholder: 'Select Date Range',
                            onChange: function(selectedDates, dateStr, instance) {
                                if (selectedDates.length === 2) {
                                    currentFilters.dateRange = [
                                        selectedDates[0].toISOString().split('T')[0],
                                        selectedDates[1].toISOString().split('T')[0]
                                    ];
                                    updateGrid();
                                } else if (selectedDates.length === 1) {
                                    // Single date: filter to projects active on that day (same start and end)
                                    const d = selectedDates[0].toISOString().split('T')[0];
                                    currentFilters.dateRange = [d, d];
                                    updateGrid();
                                } else if (selectedDates.length === 0) {
                                    currentFilters.dateRange = null;
                                    updateGrid();
                                }
                            }
                        });
                    } else {
                        setTimeout(initDatePicker, 100);
                    }
                };
                initDatePicker();
            }
            
            return true;
        } catch (error) {
            console.error('Department Projects Grid initialization error:', error);
            return false;
        }
    }
    
    // Try to initialize immediately, then retry if Grid.js not ready
    if (!initDeptProjectsGrid()) {
        let attempts = 0;
        const checkInterval = setInterval(function() {
            attempts++;
            if (initDeptProjectsGrid()) {
                clearInterval(checkInterval);
            } else if (attempts >= 50) {
                clearInterval(checkInterval);
                console.warn('Department Projects: Failed to initialize after 5 seconds');
            }
        }, 100);
    }
});

// ------Company-wide Reports Table-------
document.addEventListener('DOMContentLoaded', function() {
    const tableEl = document.getElementById("companyWideReport");
    const containerEl = document.getElementById("table11-gridjs");
    const dateInput = document.getElementById('datepicker-range');
    const searchInput = document.getElementById('custom-grid-search');

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

// 10. Approval Table
const table10Req = document.getElementById("projectsApproval");
const table10Res = document.getElementById("table10-gridjs");
if (table10Req && table10Res) {
    new gridjs.Grid({
        from: table10Req,
        pagination: { limit: 10 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table10Res);
}

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