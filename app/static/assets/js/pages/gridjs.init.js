/*
Template Name: webadmin - Admin & Dashboard Template
Author: Themesdesign
Website: https://Themesdesign.com/
Contact: Themesdesign@gmail.com
File: grid Js File
*/

// department Table
new gridjs.Grid({
    from: document.getElementById("projectsTable"),
    pagination: {
        limit: 5
    },
    sort: true,
    search: true,
    className: {
        table: "table table-striped table-centered align-middle"
    }
}).render(document.getElementById("table-gridjs"));

// company Table
new gridjs.Grid({
    from: document.getElementById("projectsTableCompany"),
    pagination: {
        limit: 5
    },
    sort: true,
    search: true,
    className: {
        table: "table table-striped table-centered align-middle"
    }
}).render(document.getElementById("table2-gridjs"));


//task table
new gridjs.Grid({
    from: document.getElementById("projectsTableTask"),
    pagination: {
        limit: 5
    },
    sort: true,
    search: true,
    className: {
        table: "table table-striped table-centered align-middle"
    }
}).render(document.getElementById("table3-gridjs"));

//profile table
new gridjs.Grid({
    from: document.getElementById("projectsTableProfile"),
    pagination: {
        limit: 5
    },
    sort: true,
    search: true,
    className: {
        table: "table table-striped table-centered align-middle"
    }
}).render(document.getElementById("table4-gridjs"));
