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
                pagination: { limit: 5 },
                sort: true,
                search: false, // Disable built-in search, handle manually
                className: { table: "table table-centered align-middle" }
            }).render(gridContainer);
            
            // Update grid function
            const updateGrid = () => {
                if (grid1) {
                    const filteredData = getFilteredData().map(row => row.cells);
                    grid1.updateConfig({ data: filteredData }).forceRender();
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
                                } else if (selectedDates.length === 0) {
                                    currentFilters1.dateRange = null;
                                    updateGrid();
                                }
                            },
                            onClose: function(selectedDates, dateStr, instance) {
                                if (selectedDates.length === 1) {
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

// 2. Company Table
const table2Req = document.getElementById("projectsTableCompany");
const table2Res = document.getElementById("table2-gridjs");
if (table2Req && table2Res) {
    new gridjs.Grid({
        from: table2Req,
        pagination: { limit: 10 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table2Res);
}

// 3. Task Table
const table3Req = document.getElementById("projectsTableTask");
const table3Res = document.getElementById("table3-gridjs");
if (table3Req && table3Res) {
    new gridjs.Grid({
        from: table3Req,
        pagination: { limit: 5 },
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
        pagination: { limit: 5 },
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
        pagination: { limit: 5 },
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
        pagination: { limit: 5 },
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

// 10. Approval Table
const table10Req = document.getElementById("projectsApproval");
const table10Res = document.getElementById("table10-gridjs");
if (table10Req && table10Res) {
    new gridjs.Grid({
        from: table10Req,
        pagination: { limit: 5 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table10Res);
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
            
            // Update grid function
            const updateGrid = () => {
                if (grid) {
                    const filteredData = getFilteredData().map(row => row.cells);
                    grid.updateConfig({ data: filteredData }).forceRender();
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
                                } else if (selectedDates.length === 0) {
                                    currentFilters.dateRange = null;
                                    updateGrid();
                                }
                            },
                            onClose: function(selectedDates, dateStr, instance) {
                                if (selectedDates.length === 1) {
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
