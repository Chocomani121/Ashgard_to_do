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


// 1.  Projects Table (with filters)
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

//  13 Department-Wide Projects Table (with filters)
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
        const tableElement = document.getElementById("projectsDeptTable");
        const gridContainer = document.getElementById("table13-gridjs");
        
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
                columns: ["Project Name", "Priority", "Start Date", "Deadline", "Status", "Progress", "Project Manager", "Client", "Department", "Last Tasks"],
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
            const statusFilter = document.getElementById('statusFilterDeptProjects');
            if (statusFilter) {
                statusFilter.addEventListener('change', function() {
                    currentFilters1.status = this.value;
                    updateGrid();
                });
            }
            
            // Handle priority filter
            const priorityFilter = document.getElementById('priorityFilterDeptProjects');
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
            const dateRangeInput = document.getElementById('datepicker-range-deptprojects');
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
    let grid1 = null;
    let allData1 = [];
    let currentFilters1 = {
        status: 'all',
        priority: 'all',
        dateRange: null,
        search: ''
    };
    
    function initDepartmentWideProjectsGrid() {
        const tableElement = document.getElementById("projectsTableCompany");
        const gridContainer = document.getElementById("table2-gridjs");
        
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
                columns: ["Project Name", "Start Date", "Deadline", "Status", "Progress", "Project Manager", "Client", "Department", "Last Tasks"],
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
            const statusFilter = document.getElementById('statusCompanyFilter');
            if (statusFilter) {
                statusFilter.addEventListener('change', function() {
                    currentFilters1.status = this.value;
                    updateGrid();
                });
            }
            
            // Handle priority filter
            const priorityFilter = document.getElementById('priorityCompanyFilter');
            if (priorityFilter) {
                priorityFilter.addEventListener('change', function() {
                    currentFilters1.priority = this.value;
                    updateGrid();
                });
            }
            
            // Handle search input
            const searchInput1 = document.getElementById('searchCompanyProjects');
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
            const dateRangeInput = document.getElementById('datepicker-range-company');
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

// 2b. Project Details Tasks Table (responsive with search)
document.addEventListener('DOMContentLoaded', function() {
    const tbl = document.getElementById("projectTasksTable");
    const container = document.getElementById("project-tasks-table-gridjs");
    if (!tbl || !container || typeof gridjs === 'undefined') return;

    const rows = Array.from(tbl.querySelectorAll('tbody tr'));
    const allData = rows.map(tr => ({
        cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML)),
        searchText: Array.from(tr.querySelectorAll('td')).map(td => td.textContent || '').join(' ').toLowerCase()
    }));

    let searchVal = '';
    const filtered = () => allData.filter(row => !searchVal || row.searchText.includes(searchVal.toLowerCase()));
    const grid = new gridjs.Grid({
        columns: ["Task Name", "Owner", "Deadline", "Status", "Sub Task", "Actions"],
        data: filtered().map(row => row.cells),
        pagination: { limit: 10 },
        sort: true,
        search: false,
        className: { table: "table table-centered align-middle mb-0" }
    }).render(container);

    const searchEl = document.getElementById('taskSearchInput');
    if (searchEl) {
        let t;
        searchEl.addEventListener('input', function() {
            clearTimeout(t);
            t = setTimeout(() => {
                searchVal = this.value.trim();
                grid.updateConfig({ data: filtered().map(row => row.cells) }).forceRender();
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

// Department table
const table15Req = document.getElementById("projectsTableDept");
const table15Res = document.getElementById("table15-gridjs");
if (table15Req && table15Res) {
    new gridjs.Grid({
        from: table15Req,
        pagination: { limit: 10 },
        sort: true,
        search: false,
        className: { table: "table table-centered align-middle" }
    }).render(table15Res);
}

// 8 my task table
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
    
    function initMyTasksGrid() {
        const tableElement = document.getElementById('projectsTableMyTasks');
        const gridContainer = document.getElementById("table8-gridjs");
        const dropdownButton = document.getElementById('categorySelect');
        const dropdownMenu = dropdownButton ? dropdownButton.closest('.btn-group')?.querySelectorAll('.dropdown-item') || [] : [];
        
        // Must have table and grid container; categorySelect/dropdown are optional (for Dept Tasks page)
        if (!tableElement || !gridContainer) {
            return false;
        }
        
        if (typeof gridjs === 'undefined') {
            return false;
        }
        
        try {
            const tableRows = Array.from(tableElement.querySelectorAll('tbody tr'));
            allData = tableRows.map(tr => ({
                task_name: tr.getAttribute('data-task-name') || '',
                category: tr.getAttribute('data-category') || '',
                status: tr.getAttribute('data-status') || '',
                priority: tr.getAttribute('data-priority') || '',
                startDate: tr.getAttribute('data-start-date') || '',
                endDate: tr.getAttribute('data-end-date') || '',
                cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML)),
                searchText: Array.from(tr.querySelectorAll('td')).map(td => td.textContent || '').join(' ').toLowerCase()
            }));
            
            const getFilteredData = () => {
                return allData.filter(row => {
                    if (currentFilters.search && !row.searchText.includes(currentFilters.search.toLowerCase())) {
                        return false;
                    }
                    if (currentFilters.department !== 'All' && row.category && row.category !== currentFilters.department) {
                        return false;
                    }
                    if (currentFilters.status !== 'all' && row.status !== currentFilters.status) {
                        return false;
                    }
                    if (currentFilters.priority !== 'all' && row.priority !== currentFilters.priority) {
                        return false;
                    }
                    if (currentFilters.dateRange && currentFilters.dateRange.length === 2) {
                        const filterStart = new Date(currentFilters.dateRange[0]);
                        const filterEnd = new Date(currentFilters.dateRange[1]);
                        filterStart.setHours(0, 0, 0, 0);
                        filterEnd.setHours(23, 59, 59, 999);
                        let hasDateInRange = false;
                        if (row.startDate) {
                            const projectStart = new Date(row.startDate);
                            projectStart.setHours(0, 0, 0, 0);
                            if (projectStart >= filterStart && projectStart <= filterEnd) hasDateInRange = true;
                        }
                        if (!hasDateInRange && row.endDate) {
                            const projectEnd = new Date(row.endDate);
                            projectEnd.setHours(23, 59, 59, 999);
                            if (projectEnd >= filterStart && projectEnd <= filterEnd) hasDateInRange = true;
                        }
                        if (!hasDateInRange && row.startDate && row.endDate) {
                            const projectStart = new Date(row.startDate);
                            const projectEnd = new Date(row.endDate);
                            projectStart.setHours(0, 0, 0, 0);
                            projectEnd.setHours(23, 59, 59, 999);
                            if (projectStart <= filterEnd && projectEnd >= filterStart) hasDateInRange = true;
                        }
                        if (!hasDateInRange) return false;
                    }
                    return true;
                });
            };
            
            grid = new gridjs.Grid({
                columns: ["Task Name", "Project", "Project Manager", "Priority", "Status", "Start Date", "Deadline", "Progress", "Sub Tasks"],
                data: getFilteredData().map(row => row.cells),
                pagination: { limit: 10 },
                sort: true,
                search: false,
                className: { table: 'table table-bordered' }
            }).render(gridContainer);
            setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
            
            const updateGrid = () => {
                if (grid) {
                    grid.updateConfig({ data: getFilteredData().map(row => row.cells) }).forceRender();
                    setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
                }
            };
            
            // Use My Tasks filter IDs first, fallback to Dept IDs for shared pages
            const searchInput = document.getElementById('searchMyTaskProjects') || document.getElementById('searchDeptProjects');
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
            
            dropdownMenu.forEach(item => {
                item.addEventListener('click', function(event) {
                    event.preventDefault();
                    const selectedValue = this.getAttribute('data-value');
                    dropdownButton.innerHTML = `${this.textContent} <i class="mdi mdi-chevron-down"></i>`;
                    currentFilters.department = selectedValue || "All";
                    updateGrid();
                });
            });
            
            const statusFilter = document.getElementById('statusFilter-mytask') || document.getElementById('statusFilterDept');
            if (statusFilter) {
                statusFilter.addEventListener('change', function() {
                    currentFilters.status = this.value;
                    updateGrid();
                });
            }
            
            const priorityFilter = document.getElementById('priorityFilter-mytask') || document.getElementById('priorityFilterDept');
            if (priorityFilter) {
                priorityFilter.addEventListener('change', function() {
                    currentFilters.priority = this.value;
                    updateGrid();
                });
            }
            
            const dateRangeInput = document.getElementById('datepicker-range-mytask') || document.getElementById('datepicker-range-dept');
            if (dateRangeInput) {
                const initDatePicker = () => {
                    if (typeof flatpickr !== 'undefined') {
                        flatpickr(dateRangeInput, {
                            mode: 'range',
                            dateFormat: 'Y-m-d',
                            placeholder: 'Select Date Range',
                            onChange: function(selectedDates) {
                                if (selectedDates.length === 2) {
                                    currentFilters.dateRange = [
                                        selectedDates[0].toISOString().split('T')[0],
                                        selectedDates[1].toISOString().split('T')[0]
                                    ];
                                    updateGrid();
                                } else if (selectedDates.length === 1) {
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
            console.error('My Tasks Grid initialization error:', error);
            return false;
        }
    }
    
    if (!initMyTasksGrid()) {
        let attempts = 0;
        const checkInterval = setInterval(function() {
            attempts++;
            if (initMyTasksGrid()) {
                clearInterval(checkInterval);
            } else if (attempts >= 50) {
                clearInterval(checkInterval);
                console.warn('My Tasks: Failed to initialize after 5 seconds');
            }
        }, 100);
    }
});

    
// 9 Dept Task table
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
    
    function initMyTasksGrid() {
        const tableElement = document.getElementById('projectsTableDeptTasks');
        const gridContainer = document.getElementById("table9-gridjs");
        const dropdownButton = document.getElementById('categorySelect');
        const dropdownMenu = dropdownButton ? dropdownButton.closest('.btn-group')?.querySelectorAll('.dropdown-item') || [] : [];
        
        // Must have table and grid container; categorySelect/dropdown are optional (for Dept Tasks page)
        if (!tableElement || !gridContainer) {
            return false;
        }
        
        if (typeof gridjs === 'undefined') {
            return false;
        }
        
        try {
            const tableRows = Array.from(tableElement.querySelectorAll('tbody tr'));
            allData = tableRows.map(tr => ({
                task_name: tr.getAttribute('data-task-name') || '',
                category: tr.getAttribute('data-category') || '',
                status: tr.getAttribute('data-status') || '',
                priority: tr.getAttribute('data-priority') || '',
                startDate: tr.getAttribute('data-start-date') || '',
                endDate: tr.getAttribute('data-end-date') || '',
                cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML)),
                searchText: Array.from(tr.querySelectorAll('td')).map(td => td.textContent || '').join(' ').toLowerCase()
            }));
            
            const getFilteredData = () => {
                return allData.filter(row => {
                    if (currentFilters.search && !row.searchText.includes(currentFilters.search.toLowerCase())) {
                        return false;
                    }
                    if (currentFilters.department !== 'All' && row.category && row.category !== currentFilters.department) {
                        return false;
                    }
                    if (currentFilters.status !== 'all' && row.status !== currentFilters.status) {
                        return false;
                    }
                    if (currentFilters.priority !== 'all' && row.priority !== currentFilters.priority) {
                        return false;
                    }
                    if (currentFilters.dateRange && currentFilters.dateRange.length === 2) {
                        const filterStart = new Date(currentFilters.dateRange[0]);
                        const filterEnd = new Date(currentFilters.dateRange[1]);
                        filterStart.setHours(0, 0, 0, 0);
                        filterEnd.setHours(23, 59, 59, 999);
                        let hasDateInRange = false;
                        if (row.startDate) {
                            const projectStart = new Date(row.startDate);
                            projectStart.setHours(0, 0, 0, 0);
                            if (projectStart >= filterStart && projectStart <= filterEnd) hasDateInRange = true;
                        }
                        if (!hasDateInRange && row.endDate) {
                            const projectEnd = new Date(row.endDate);
                            projectEnd.setHours(23, 59, 59, 999);
                            if (projectEnd >= filterStart && projectEnd <= filterEnd) hasDateInRange = true;
                        }
                        if (!hasDateInRange && row.startDate && row.endDate) {
                            const projectStart = new Date(row.startDate);
                            const projectEnd = new Date(row.endDate);
                            projectStart.setHours(0, 0, 0, 0);
                            projectEnd.setHours(23, 59, 59, 999);
                            if (projectStart <= filterEnd && projectEnd >= filterStart) hasDateInRange = true;
                        }
                        if (!hasDateInRange) return false;
                    }
                    return true;
                });
            };
            
            grid = new gridjs.Grid({
                columns: ["Task Name", "Project", "Department", "Project Manager", "Priority", "Status", "Start Date", "Deadline", "Progress", "Sub Tasks"],
                data: getFilteredData().map(row => row.cells),
                pagination: { limit: 10 },
                sort: true,
                search: false,
                className: { table: 'table table-bordered' }
            }).render(gridContainer);
            setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
            
            const updateGrid = () => {
                if (grid) {
                    grid.updateConfig({ data: getFilteredData().map(row => row.cells) }).forceRender();
                    setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
                }
            };
            
            // Dept Task filter IDs (from dept_task.html)
            const searchInput = document.getElementById('searchDeptTaskProjects');
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
            
            dropdownMenu.forEach(item => {
                item.addEventListener('click', function(event) {
                    event.preventDefault();
                    const selectedValue = this.getAttribute('data-value');
                    dropdownButton.innerHTML = `${this.textContent} <i class="mdi mdi-chevron-down"></i>`;
                    currentFilters.department = selectedValue || "All";
                    updateGrid();
                });
            });
            
            const statusFilter = document.getElementById('statusFilter-Depttask');
            if (statusFilter) {
                statusFilter.addEventListener('change', function() {
                    currentFilters.status = this.value;
                    updateGrid();
                });
            }
            
            const priorityFilter = document.getElementById('priorityFilter-Depttask');
            if (priorityFilter) {
                priorityFilter.addEventListener('change', function() {
                    currentFilters.priority = this.value;
                    updateGrid();
                });
            }
            
            const dateRangeInput = document.getElementById('datepicker-range-Depttask');
            if (dateRangeInput) {
                const initDatePicker = () => {
                    if (typeof flatpickr !== 'undefined') {
                        flatpickr(dateRangeInput, {
                            mode: 'range',
                            dateFormat: 'Y-m-d',
                            placeholder: 'Select Date Range',
                            onChange: function(selectedDates) {
                                if (selectedDates.length === 2) {
                                    currentFilters.dateRange = [
                                        selectedDates[0].toISOString().split('T')[0],
                                        selectedDates[1].toISOString().split('T')[0]
                                    ];
                                    updateGrid();
                                } else if (selectedDates.length === 1) {
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
            console.error('Dept Tasks Grid initialization error:', error);
            return false;
        }
    }
    
    if (!initMyTasksGrid()) {
        let attempts = 0;
        const checkInterval = setInterval(function() {
            attempts++;
            if (initMyTasksGrid()) {
                clearInterval(checkInterval);
            } else if (attempts >= 50) {
                clearInterval(checkInterval);
                console.warn('Dept Tasks: Failed to initialize after 5 seconds');
            }
        }, 100);
    }
});


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

// 10. Approval Table (approvals.html - Task Name, Project, Department, etc. with filters)
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
    
    function initApprovalGrid() {
        const tableElement = document.getElementById('projectsApproval');
        const gridContainer = document.getElementById("table10-gridjs");
        const dropdownButton = document.getElementById('categorySelect');
        const dateInputApproval = document.getElementById('datepicker-range-approval');
        const dropdownMenu = dropdownButton ? dropdownButton.closest('.btn-group')?.querySelectorAll('.dropdown-item') || [] : [];
        
        // Must have table and grid container; dropdown optional (approvals page has no category dropdown)
        if (!tableElement || !gridContainer) {
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
            

            // Initialize Grid.js - columns match approvals.html: Report Owner, Week Range, Status
            grid = new gridjs.Grid({
                columns: ["Report Owner", "Week Range", "Status", "Reviewer"],
                data: getFilteredData().map(row => row.cells),
                pagination: { limit: 15 },
                sort: true,
                search: false, // Disable built-in search, handle manually
                className: {
                    table: 'table table-bordered'
                },
                style: {
                    th: { 'background-color': '#f8f9fa', 'color': '#495057', 'text-align': 'center' },
                    td: { 'text-align': 'center' }
                }
            }).render(gridContainer);
            setTimeout(function() { if (typeof applyProgressBarWidths === 'function') applyProgressBarWidths(gridContainer); }, 100);
            
            // Update grid function
            const updateGrid = () => {
                if (grid) {
                    const filteredData = getFilteredData().map(row => row.cells);
                    grid.updateConfig({ data: filteredData }).forceRender();
                    setTimeout(function() { if (typeof applyProgressBarWidths === 'function') applyProgressBarWidths(gridContainer); }, 100);
                }
            };
            
            // Handle search input
            const searchInput = document.getElementById('searchApprovalProjects');
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
            
            // Handle department dropdown filtering (optional - approvals page may not have category dropdown)
            if (dropdownButton && dropdownMenu.length > 0) {
                dropdownMenu.forEach(item => {
                    item.addEventListener('click', function(event) {
                        event.preventDefault();
                        const selectedValue = this.getAttribute('data-value');
                        dropdownButton.innerHTML = `${this.textContent} <i class="mdi mdi-chevron-down"></i>`;
                        currentFilters.department = selectedValue || "All";
                        updateGrid();
                    });
                });
            }
            
            // Handle status filter
            const statusFilter = document.getElementById('statusFilterApprovalProjects');
            if (statusFilter) {
                statusFilter.addEventListener('change', function() {
                    currentFilters.status = this.value;
                    updateGrid();
                });
            }
            
            // Handle priority filter
            const priorityFilter = document.getElementById('priorityFilterDeptApprovalProjects');
            if (priorityFilter) {
                priorityFilter.addEventListener('change', function() {
                    currentFilters.priority = this.value;
                    updateGrid();
                });
            }
            
            // Initialize Flatpickr date range picker
            const dateRangeInput = document.getElementById('datepicker-range-approval');
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
            console.error('Approvals Grid initialization error:', error);
            return false;
        }
    }
    
    // Try to initialize immediately, then retry if Grid.js not ready
    if (!initApprovalGrid()) {
        let attempts = 0;
        const checkInterval = setInterval(function() {
            attempts++;
            if (initApprovalGrid()) {
                clearInterval(checkInterval);
            } else if (attempts >= 50) {
                clearInterval(checkInterval);
                console.warn('Approvals: Failed to initialize after 5 seconds');
            }
        }, 100);
    }
});

// 11. Company-Wide Report Table
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
            statusText: tds[3] ? tds[3].textContent.trim() : '',
            cells: cells
        };
    });

    // One cell per column: [Name payload, Start, End, Reviewer] so columns align
    function rowToGridData(r) {
        return [[r.reportId, r.nameText], r.cells[1], r.cells[2], r.statusText || '', r.cells[4]];
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
            {
                name: 'Status',
                formatter: (cell) => {
                    const s = (cell || '').trim();
                    const isReviewed = s.toLowerCase() === 'reviewed';
                    const cls = isReviewed ? 'bg-secondary bg-opacity-75' : 'bg-danger bg-opacity-75';
                    return gridjs.html('<span class="badge ' + cls + ' px-2 py-1">' + escapeHtml(s) + '</span>');
                }
            },
            'Reviewer'
        ],
        data: allData.map(rowToGridData),
        sort: true,
        pagination: { limit: 12 },
        search: false,
        style: {
            table: { 'font-size': '0.9rem' },
            th: { 'background-color': '#f8f9fa', 'color': '#495057', 'text-align': 'center' },
            td: { 'text-align': 'center' }
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

    // 4. Company-wide report modal: open, comment, reply, edit
    const reportsDataEl = document.getElementById('reports-data');
    if (reportsDataEl && typeof bootstrap !== 'undefined') {
        const reportsData = JSON.parse(reportsDataEl.textContent);
        const modalEl = document.getElementById('companyWideReportModal');
        const bsModal = modalEl ? new bootstrap.Modal(modalEl) : null;

        function renderModalComments(reportData) {
            var listEl = document.getElementById('companyWideModalCommentsList');
            var emptyEl = document.getElementById('companyWideModalCommentsEmpty');
            var comments = (reportData && reportData.comments) || [];
            var topLevel = [], repliesByParent = {};
            comments.forEach(function(c) {
                var pid = c.parent_comment_id;
                if (pid == null || pid === '') topLevel.push(c);
                else { if (!repliesByParent[pid]) repliesByParent[pid] = []; repliesByParent[pid].push(c); }
            });
            var curMemberId = null;
            try { var cuEl = document.getElementById('current-user-member-id'); if (cuEl && cuEl.textContent) curMemberId = parseInt(cuEl.textContent, 10); } catch (e) {}
            function esc(s) { return (s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
            function cardHtml(c, isReply) {
                var imgSrc = '/static/profile_pics/' + (c.author_image || 'default.jpg');
                var isOwn = curMemberId != null && c.member_id === curMemberId;
                var authorEsc = esc(c.author_name || 'Unknown');
                var bodyEsc = esc(c.comment_body);
                var replyLink = '<a href="javascript:void(0)" class="company-wide-modal-reply-link small text-primary text-decoration-none" data-comment-id="' + (c.comment_id || '') + '" data-author-name="' + authorEsc + '">Reply</a>';
                var editLink = isOwn ? '<a href="javascript:void(0)" class="company-wide-modal-edit-link small text-primary text-decoration-none ms-2" data-comment-id="' + (c.comment_id || '') + '" data-comment-body="' + bodyEsc + '">Edit</a>' : '';
                return '<div class="d-flex gap-2"><img src="' + imgSrc + '" alt="" class="rounded-circle flex-shrink-0" style="width:' + (isReply ? 28 : 32) + 'px;height:' + (isReply ? 28 : 32) + 'px;object-fit:cover" onerror="this.src=\'/static/profile_pics/default.jpg\'"><div class="flex-grow-1" style="min-width:0"><div class="d-flex justify-content-between align-items-start"><span class="fw-semibold small">' + (c.author_name || 'Unknown') + '</span><small class="text-muted">' + (c.created_at || '') + '</small></div><div class="small text-secondary report-comment-body">' + (c.comment_body || '').replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div><div class="mt-1">' + replyLink + editLink + '</div></div></div>';
            }
            function appendReplies(container, parentId, depth) {
                var replies = repliesByParent[parentId] || [];
                replies.forEach(function(r) {
                    var wrap = document.createElement('div');
                    wrap.className = 'company-wide-modal-reply-wrapper border-bottom pb-2 mb-2';
                    wrap.style.marginLeft = (depth > 0 ? 24 : 40) + 'px';
                    wrap.style.paddingLeft = '12px';
                    wrap.style.borderLeft = '2px solid #dee2e6';
                    wrap.style.marginTop = '4px';
                    wrap.setAttribute('data-comment-id', r.comment_id);
                    wrap.innerHTML = cardHtml(r, true);
                    container.appendChild(wrap);
                    appendReplies(wrap, r.comment_id, depth + 1);
                });
            }
            if (listEl) {
                listEl.innerHTML = '';
                if (topLevel.length === 0) {
                    listEl.style.display = 'none';
                    if (emptyEl) emptyEl.style.display = 'block';
                } else {
                    listEl.style.display = 'block';
                    if (emptyEl) emptyEl.style.display = 'none';
                    topLevel.forEach(function(c) {
                        var card = document.createElement('div');
                        card.className = 'company-wide-modal-comment-card border-bottom pb-2 mb-2';
                        card.setAttribute('data-comment-id', c.comment_id);
                        card.innerHTML = cardHtml(c, false);
                        listEl.appendChild(card);
                        appendReplies(listEl, c.comment_id, 0);
                    });
                }
            }
        }

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
            var mStatus = document.getElementById('companyWideModalStatus');
            if (mStatus) {
              var label = report.is_checked ? 'Reviewed' : 'Pending';
              var cls = report.is_checked ? 'badge bg-secondary bg-opacity-75 px-2 py-1' : 'badge bg-danger bg-opacity-75 px-2 py-1';
              mStatus.innerHTML = '<span class="' + cls + '">' + label + '</span>';
            }
            document.getElementById('companyWideModalBody').innerHTML = report.report_content || '';

            document.getElementById('companyWideModalReportId').value = report.report_id;
            document.getElementById('companyWideModalParentCommentId').value = '';
            var replyingTo = document.getElementById('companyWideModalReplyingTo');
            if (replyingTo) replyingTo.style.display = 'none';
            document.getElementById('companyWideModalCommentInput').value = '';
            renderModalComments(report);
            bsModal.show();
        });

        if (modalEl) {
            modalEl.addEventListener('click', function(e) {
                var replyLink = e.target.closest('.company-wide-modal-reply-link');
                if (replyLink) {
                    e.preventDefault();
                    var cid = replyLink.getAttribute('data-comment-id');
                    var author = replyLink.getAttribute('data-author-name') || '';
                    document.getElementById('companyWideModalParentCommentId').value = cid || '';
                    var replyingToEl = document.getElementById('companyWideModalReplyingTo');
                    var nameSpan = document.getElementById('companyWideModalReplyingToName');
                    if (replyingToEl) { if (nameSpan) nameSpan.textContent = author; replyingToEl.style.display = 'block'; }
                    document.getElementById('companyWideModalCommentInput').focus();
                }
                var editLink = e.target.closest('.company-wide-modal-edit-link');
                if (editLink) {
                    e.preventDefault();
                    var cid = editLink.getAttribute('data-comment-id');
                    var body = (editLink.getAttribute('data-comment-body') || '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&amp;/g, '&');
                    var card = editLink.closest('.company-wide-modal-comment-card, .company-wide-modal-reply-wrapper');
                    var bodyDiv = card ? card.querySelector('.report-comment-body') : null;
                    if (!bodyDiv) return;
                    var reportId = document.getElementById('companyWideModalReportId').value;
                    var origHtml = bodyDiv.innerHTML;
                    bodyDiv.innerHTML = '<textarea class="form-control form-control-sm mb-1" rows="2" style="resize:none">' + (body.replace(/</g, '&lt;').replace(/>/g, '&gt;')) + '</textarea><div><button type="button" class="btn btn-sm btn-primary company-wide-modal-edit-save" data-comment-id="' + cid + '">Save</button> <button type="button" class="btn btn-sm btn-secondary company-wide-modal-edit-cancel">Cancel</button></div>';
                    var cancelBtn = bodyDiv.querySelector('.company-wide-modal-edit-cancel');
                    if (cancelBtn) cancelBtn.onclick = function() { bodyDiv.innerHTML = origHtml; };
                    var saveBtn = bodyDiv.querySelector('.company-wide-modal-edit-save');
                    if (saveBtn) saveBtn.onclick = function() {
                        var newBody = (bodyDiv.querySelector('textarea').value || '').trim();
                        if (!newBody) return;
                        saveBtn.disabled = true;
                        var xhr = new XMLHttpRequest();
                        xhr.open('PATCH', '/reports/' + reportId + '/comments/' + cid);
                        xhr.setRequestHeader('Content-Type', 'application/json');
                        xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                        xhr.onload = function() {
                            if (xhr.status === 200) {
                                try {
                                    var res = JSON.parse(xhr.responseText);
                                    if (res && res.success) {
                                        bodyDiv.innerHTML = (res.comment_body || '').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                                        var idx = reportsData.findIndex(function(r) { return r.report_id == reportId; });
                                        if (idx >= 0 && reportsData[idx].comments) {
                                            var cc = reportsData[idx].comments.find(function(c) { return c.comment_id == cid; });
                                            if (cc) cc.comment_body = res.comment_body;
                                        }
                                    }
                                } catch (err) {}
                            }
                        };
                        xhr.send(JSON.stringify({ comment_body: newBody }));
                    };
                }
            });
        }

        var cancelReply = document.getElementById('companyWideModalCancelReply');
        if (cancelReply) cancelReply.addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('companyWideModalParentCommentId').value = '';
            document.getElementById('companyWideModalReplyingTo').style.display = 'none';
        });

        var submitBtn = document.getElementById('companyWideModalCommentSubmit');
        if (submitBtn) submitBtn.addEventListener('click', function() {
            var reportId = document.getElementById('companyWideModalReportId').value;
            var parentId = document.getElementById('companyWideModalParentCommentId').value;
            var input = document.getElementById('companyWideModalCommentInput');
            var spinner = document.getElementById('companyWideModalCommentSpinner');
            var btnText = document.getElementById('companyWideModalCommentBtnText');
            var body = (input && input.value || '').trim();
            if (!reportId || !body) { if (!body) alert('Please write a comment.'); return; }
            submitBtn.disabled = true;
            if (spinner) spinner.classList.remove('d-none');
            if (btnText) btnText.textContent = 'Sending...';
            var payload = { comment_body: body };
            if (parentId) payload.parent_comment_id = parseInt(parentId, 10);
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/reports/' + reportId + '/comment');
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.onload = function() {
                submitBtn.disabled = false;
                if (spinner) spinner.classList.add('d-none');
                if (btnText) btnText.textContent = 'Send';
                if (xhr.status === 200) {
                    try {
                        var res = JSON.parse(xhr.responseText);
                        if (res && res.success) {
                            input.value = '';
                            document.getElementById('companyWideModalParentCommentId').value = '';
                            document.getElementById('companyWideModalReplyingTo').style.display = 'none';
                            var refreshXhr = new XMLHttpRequest();
                            refreshXhr.open('GET', '/reports/' + reportId);
                            refreshXhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                            refreshXhr.onload = function() {
                                if (refreshXhr.status === 200) {
                                    try {
                                        var updated = JSON.parse(refreshXhr.responseText);
                                        var idx = reportsData.findIndex(function(r) { return r.report_id == reportId; });
                                        if (idx >= 0) reportsData[idx] = updated;
                                        renderModalComments(updated);
                                    } catch (err) {}
                                }
                            };
                            refreshXhr.send();
                            if (typeof alertify !== 'undefined') alertify.success('Comment added.'); else alert('Comment added.');
                        }
                    } catch (err) {}
                } else {
                    if (typeof alertify !== 'undefined') alertify.error('Failed to add comment.'); else alert('Failed to add comment.');
                }
            };
            xhr.onerror = function() { submitBtn.disabled = false; if (spinner) spinner.classList.add('d-none'); if (btnText) btnText.textContent = 'Send'; };
            xhr.send(JSON.stringify(payload));
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

// 12. All task Table
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
    
    function initMyTasksGrid() {
        const tableElement = document.getElementById('projectsTableAllTasks');
        const gridContainer = document.getElementById("table12-gridjs");
        const dropdownButton = document.getElementById('categorySelect');
        const dropdownMenu = dropdownButton ? dropdownButton.closest('.btn-group')?.querySelectorAll('.dropdown-item') || [] : [];
        
        // Must have table and grid container; categorySelect/dropdown are optional (for Dept Tasks page)
        if (!tableElement || !gridContainer) {
            return false;
        }
        
        if (typeof gridjs === 'undefined') {
            return false;
        }
        
        try {
            const tableRows = Array.from(tableElement.querySelectorAll('tbody tr'));
            allData = tableRows.map(tr => ({
                task_name: tr.getAttribute('data-task-name') || '',
                category: tr.getAttribute('data-category') || '',
                status: tr.getAttribute('data-status') || '',
                priority: tr.getAttribute('data-priority') || '',
                startDate: tr.getAttribute('data-start-date') || '',
                endDate: tr.getAttribute('data-end-date') || '',
                cells: Array.from(tr.querySelectorAll('td')).map(td => gridjs.html(td.innerHTML)),
                searchText: Array.from(tr.querySelectorAll('td')).map(td => td.textContent || '').join(' ').toLowerCase()
            }));
            
            const getFilteredData = () => {
                return allData.filter(row => {
                    if (currentFilters.search && !row.searchText.includes(currentFilters.search.toLowerCase())) {
                        return false;
                    }
                    if (currentFilters.department !== 'All' && row.category && row.category !== currentFilters.department) {
                        return false;
                    }
                    if (currentFilters.status !== 'all' && row.status !== currentFilters.status) {
                        return false;
                    }
                    if (currentFilters.priority !== 'all' && row.priority !== currentFilters.priority) {
                        return false;
                    }
                    if (currentFilters.dateRange && currentFilters.dateRange.length === 2) {
                        const filterStart = new Date(currentFilters.dateRange[0]);
                        const filterEnd = new Date(currentFilters.dateRange[1]);
                        filterStart.setHours(0, 0, 0, 0);
                        filterEnd.setHours(23, 59, 59, 999);
                        let hasDateInRange = false;
                        if (row.startDate) {
                            const projectStart = new Date(row.startDate);
                            projectStart.setHours(0, 0, 0, 0);
                            if (projectStart >= filterStart && projectStart <= filterEnd) hasDateInRange = true;
                        }
                        if (!hasDateInRange && row.endDate) {
                            const projectEnd = new Date(row.endDate);
                            projectEnd.setHours(23, 59, 59, 999);
                            if (projectEnd >= filterStart && projectEnd <= filterEnd) hasDateInRange = true;
                        }
                        if (!hasDateInRange && row.startDate && row.endDate) {
                            const projectStart = new Date(row.startDate);
                            const projectEnd = new Date(row.endDate);
                            projectStart.setHours(0, 0, 0, 0);
                            projectEnd.setHours(23, 59, 59, 999);
                            if (projectStart <= filterEnd && projectEnd >= filterStart) hasDateInRange = true;
                        }
                        if (!hasDateInRange) return false;
                    }
                    return true;
                });
            };
            
            grid = new gridjs.Grid({
                columns: ["Task Name", "Project", "Department", "Project Manager", "Priority", "Status", "Start Date", "Deadline", "Progress", "Sub Tasks"],
                data: getFilteredData().map(row => row.cells),
                pagination: { limit: 10 },
                sort: true,
                search: false,
                className: { table: 'table table-bordered' }
            }).render(gridContainer);
            setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
            
            const updateGrid = () => {
                if (grid) {
                    grid.updateConfig({ data: getFilteredData().map(row => row.cells) }).forceRender();
                    setTimeout(function() { applyProgressBarWidths(gridContainer); }, 100);
                }
            };
            
            // Use My Tasks filter IDs first, fallback to Dept IDs for shared pages
            const searchInput = document.getElementById('searchAllTaskProjects') || document.getElementById('searchDeptProjects');
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
            
            dropdownMenu.forEach(item => {
                item.addEventListener('click', function(event) {
                    event.preventDefault();
                    const selectedValue = this.getAttribute('data-value');
                    dropdownButton.innerHTML = `${this.textContent} <i class="mdi mdi-chevron-down"></i>`;
                    currentFilters.department = selectedValue || "All";
                    updateGrid();
                });
            });
            
            const statusFilter = document.getElementById('statusFilter-Alltask') || document.getElementById('statusFilterDept');
            if (statusFilter) {
                statusFilter.addEventListener('change', function() {
                    currentFilters.status = this.value;
                    updateGrid();
                });
            }
            
            const priorityFilter = document.getElementById('priorityFilter-Alltask') || document.getElementById('priorityFilterDept');
            if (priorityFilter) {
                priorityFilter.addEventListener('change', function() {
                    currentFilters.priority = this.value;
                    updateGrid();
                });
            }
            
            const dateRangeInput = document.getElementById('datepicker-range-Alltask') || document.getElementById('datepicker-range-dept');
            if (dateRangeInput) {
                const initDatePicker = () => {
                    if (typeof flatpickr !== 'undefined') {
                        flatpickr(dateRangeInput, {
                            mode: 'range',
                            dateFormat: 'Y-m-d',
                            placeholder: 'Select Date Range',
                            onChange: function(selectedDates) {
                                if (selectedDates.length === 2) {
                                    currentFilters.dateRange = [
                                        selectedDates[0].toISOString().split('T')[0],
                                        selectedDates[1].toISOString().split('T')[0]
                                    ];
                                    updateGrid();
                                } else if (selectedDates.length === 1) {
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
            console.error('All Tasks Grid initialization error:', error);
            return false;
        }
    }
    
    if (!initMyTasksGrid()) {
        let attempts = 0;
        const checkInterval = setInterval(function() {
            attempts++;
            if (initMyTasksGrid()) {
                clearInterval(checkInterval);
            } else if (attempts >= 50) {
                clearInterval(checkInterval);
                console.warn('All Tasks: Failed to initialize after 5 seconds');
            }
        }, 100);
    }
});
