/*
Template Name: webadmin - Admin & Dashboard Template
Author: Themesdesign
Website: https://Themesdesign.com/
Contact: Themesdesign@gmail.com
File: grid Js File
*/

// 1. Department Table
const table1Req = document.getElementById("projectsTable");
const table1Res = document.getElementById("table-gridjs");
if (table1Req && table1Res) {
    new gridjs.Grid({
        from: table1Req,
        pagination: { limit: 5 },
        sort: true,
        search: true,
        className: { table: "table table-centered align-middle" }
    }).render(table1Res);
}

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