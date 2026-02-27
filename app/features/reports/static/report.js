    
(function () {
  "use strict";

  // --- 1. Helpers ---
  function getInitials(name) {
    if (!name) return "??";
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.substring(0, 2).toUpperCase();
  }

  function getAvatarHtml(user, size = "24px", fontSize = "10px") {
    // Check if user exists and has initials
    const initials = user.initials || "??";
    const bg = user.color || "#6c757d";

    // If there is an image, try to load it, but add an onerror fallback
    if (user.image && user.image !== 'default.jpg' && user.image !== '') {
        return `<img src="/static/profile_pics/${user.image}" 
                     class="rounded-circle shadow-sm" 
                     style="width:${size}; height:${size}; object-fit: cover; flex-shrink: 0;"
                     onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\'rounded-circle d-flex align-items-center justify-content-center text-white shadow-sm\' style=\'width:${size}; height:${size}; background:${bg}; font-size:${fontSize}; flex-shrink: 0;\'>${initials}</div>';">`;
    }
    
    // Default to the initials circle
    return `<div class="rounded-circle d-flex align-items-center justify-content-center text-white shadow-sm" 
                 style="width:${size}; height:${size}; background:${bg}; font-size:${fontSize}; flex-shrink: 0;">
                 ${initials}
            </div>`;
}

  function getCurrentReportWeek() {
    const today = new Date();
    const daysFromMonday = (today.getDay() + 6) % 7;
    const monday = new Date(today);
    monday.setDate(today.getDate() - daysFromMonday);
    const saturday = new Date(monday);
    saturday.setDate(monday.getDate() + 5);
    return { start: monday, end: saturday };
  }

  function fmt(d) {
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return m + "/" + day + "/" + d.getFullYear();
  }

  const colors = ["#6f42c1", "#0d6efd", "#198754", "#dc3545", "#fd7e14", "#20c997", "#ffc107", "#6610f2"];

  // --- 2. Main Logic ---
  document.addEventListener("DOMContentLoaded", function () {
    // A. Setup Date Selector
    const sel = document.getElementById("weekly-report-date");
    if (sel) {
      const { start, end } = getCurrentReportWeek();
      const currentLabel = fmt(start) + " - " + fmt(end);
      sel.innerHTML = "";
      const currentOpt = document.createElement("option");
      currentOpt.value = currentLabel;
      currentOpt.textContent = currentLabel + " (This week)";
      currentOpt.selected = true;
      sel.appendChild(currentOpt);

      for (let i = 1; i <= 12; i++) {
        const nextMon = new Date(start);
        nextMon.setDate(start.getDate() + 7 * i);
        const nextSat = new Date(nextMon);
        nextSat.setDate(nextMon.getDate() + 5);
        const opt = document.createElement("option");
        opt.value = fmt(nextMon) + " - " + fmt(nextSat);
        opt.textContent = opt.value;
        sel.appendChild(opt);
      }
    }

    // B. Setup User Data
    const usersDataElement = document.getElementById("users-data");
    if (!usersDataElement) return;
    const allUsers = JSON.parse(usersDataElement.textContent || "[]").map((user, index) => ({
      ...user,
      initials: getInitials(user.name),
      color: colors[index % colors.length]
    }));

    // C. Setup UI Elements
    const reviewerDisplay = document.getElementById("reportReviewerDisplay");
    const reviewerDropdown = document.getElementById("reportReviewerDropdown");
    const reviewerSearch = document.getElementById("reportReviewerSearch");
    const reviewerList = document.getElementById("reportReviewerList");
    const reviewerIdInput = document.getElementById("selectedReviewerId");
    const ccSearch = document.getElementById("reportCCSearch");
    const ccList = document.getElementById("reportCCList");
    const ccChipsContainer = document.getElementById("reportCCChips");
    const ccIdsContainer = document.getElementById("ccIdsContainer");
    const reportForm = document.getElementById("reportForm");

    let selectedCCMembers = [];

    // D. Reviewer Functions
        function renderReviewers(filter = "") {
        if (!reviewerList) return; 
        reviewerList.innerHTML = "";

        // Ensure allUsers exists before filtering
        const filtered = (allUsers || []).filter(u =>
            (u.name || u.username || "").toLowerCase().includes((filter || "").toLowerCase())
        );

        filtered.forEach(user => {
            const item = document.createElement("a");
            item.className = "list-group-item list-group-item-action border-0 d-flex align-items-center gap-2 small";
            item.style.cursor = "pointer";
            
            // Use a template literal but wrap it in a try-catch if you're still seeing crashes
            try {
                item.innerHTML = `${getAvatarHtml(user)} <span>${user.name}</span>`;
            } catch (err) {
                item.innerHTML = `<span>${user.name}</span>`;
            }

            item.onclick = (e) => {
                e.stopPropagation();
                
                // 1. Update the visible display
                reviewerDisplay.innerHTML = `
                    <div class="d-flex align-items-center gap-2">
                        ${getAvatarHtml(user)}
                        <span class="fw-bold text-primary">${user.name || user.username || ""}</span>
                    </div>`;
                
                // 2. THIS IS THE MOST IMPORTANT PART FOR SAVING
                // It puts the member's ID into the hidden input you just placed
                if (reviewerIdInput) {
                    reviewerIdInput.value = user.member_id;
                }
                
                reviewerDropdown.classList.add("d-none");
            };
            reviewerList.appendChild(item);
        });
    }
    // E. CC Functions
    function renderCC(filter = "") {
      ccList.innerHTML = "";
      allUsers.filter(u => (u.name || u.username || "").toLowerCase().includes((filter || "").toLowerCase())).forEach(user => {
        const isSelected = selectedCCMembers.find(m => m.member_id === user.member_id);
        const item = document.createElement("a");
        item.className = `list-group-item list-group-item-action border-0 d-flex align-items-center gap-2 small ${isSelected ? 'bg-light text-primary' : ''}`;
        item.setAttribute("data-member-id", user.member_id);
        item.innerHTML = `${getAvatarHtml(user)} <span>${user.name || user.username || ""}</span>`;
        item.onclick = () => {
          const index = selectedCCMembers.findIndex(m => m.member_id === user.member_id);
          if (index > -1) selectedCCMembers.splice(index, 1);
          else selectedCCMembers.push(user);
          renderCCChips();
          renderCC(ccSearch.value);
        };
        ccList.appendChild(item);
      });
    }

    function renderCCChips() {
      ccChipsContainer.innerHTML = selectedCCMembers.length === 0 ? '<span class="text-muted small">Click contacts below to add...</span>' : "";
      selectedCCMembers.forEach(user => {
        const chip = document.createElement("div");
        chip.className = "badge bg-white text-dark border p-2 d-flex align-items-center gap-2 shadow-sm";
        chip.style.borderRadius = "50px";
        chip.innerHTML = `${getAvatarHtml(user, "20px", "9px")} ${user.name || user.username || ""} <i class="bx bx-x ms-1" style="cursor:pointer"></i>`;
        chip.onclick = () => {
          selectedCCMembers = selectedCCMembers.filter(m => m.member_id !== user.member_id);
          renderCCChips();
          renderCC(ccSearch.value);
        };
        ccChipsContainer.appendChild(chip);
      });
    }

    // F. Form Submission Bridge (Fixes "Not Saving" issue)
  // Inside your DOMContentLoaded block
      if (reportForm) {
          reportForm.onsubmit = function (e) {
              // 1. Sync CKEditor content
              if (window.reportCKInstance && typeof window.reportCKInstance.getData === 'function') {
                  var reportBodyHidden = document.getElementById('reportBodyHidden');
                  if (reportBodyHidden) reportBodyHidden.value = window.reportCKInstance.getData();
              }

              // 2. Double-check Reviewer ID
              const reviewerId = document.getElementById("selectedReviewerId").value;
              if (!reviewerId) {
                  if (typeof Swal !== "undefined") {
                      Swal.fire({
                          icon: "warning",
                          title: "Reviewer required",
                          text: "Please select a reviewer before submitting."
                      });
                  } else {
                      alert("Please select a reviewer before submitting.");
                  }
                  e.preventDefault();
                  return false;
              }

              // --- NEW SPINNER LOGIC START ---
              const btn = document.getElementById("submitReportBtn");
              const spinner = document.getElementById("submitSpinner");
              const btnText = document.getElementById("submitText");

              if (btn && spinner) {
                  btn.disabled = true;           // Prevent double submission
                  spinner.classList.remove("d-none"); // Show spinner
                  btnText.textContent = " Submitting..."; // Update text
              }
              // --- NEW SPINNER LOGIC END ---

              // 3. Populate CC IDs
              const ccIdsContainer = document.getElementById("ccIdsContainer");
              if (ccIdsContainer) {
                  ccIdsContainer.innerHTML = ""; 
                  selectedCCMembers.forEach(user => {
                      const input = document.createElement("input");
                      input.type = "hidden";
                      input.name = "cc_members";
                      input.value = user.member_id;
                      ccIdsContainer.appendChild(input);
                  });
              }
              
              return true; 
          };
      }
    // G. Event Listeners
    reviewerDisplay.onclick = (e) => { e.stopPropagation(); reviewerDropdown.classList.toggle("d-none"); };
    reviewerSearch.oninput = (e) => renderReviewers(e.target.value);
    ccSearch.oninput = (e) => renderCC(e.target.value);
    document.getElementById("reportCCClear").onclick = () => { selectedCCMembers = []; renderCCChips(); renderCC(); };
    
    renderReviewers();
    renderCC();
  });
})();

// Report list click handler
document.addEventListener("DOMContentLoaded", function () {
  var reportsDataEl = document.getElementById("reports-data");
  if (reportsDataEl) {
    var reportsData = JSON.parse(reportsDataEl.textContent || "[]");
    var reportCommentsPollInterval = null;

    var currentUserMemberId = null;
    try {
      var cuEl = document.getElementById("current-user-member-id");
      if (cuEl && cuEl.textContent) currentUserMemberId = parseInt(cuEl.textContent, 10);
    } catch (e) {}

    function buildCommentCard(c, isReply) {
      var imgSrc = "/static/profile_pics/" + (c.author_image || "default.jpg");
      var isOwnComment = (currentUserMemberId != null && c.member_id === currentUserMemberId);
      var bodyEscaped = (c.comment_body || "").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      var authorEscaped = (c.author_name || "Unknown").replace(/"/g, "&quot;");
      var card = document.createElement("div");
      card.className = "list-group-item list-group-item-action border-0 py-2 d-flex gap-2 report-comment-card" + (isReply ? " report-comment-reply" : "");
      card.setAttribute("data-comment-id", c.comment_id);
      card.innerHTML =
        "<img src=\"" + imgSrc + "\" alt=\"\" class=\"rounded-circle border flex-shrink-0\" style=\"width: " + (isReply ? "28" : "32") + "px; height: " + (isReply ? "28" : "32") + "px; object-fit: cover;\" onerror=\"this.src='/static/profile_pics/default.jpg'; this.onerror=null;\">" +
        "<div class=\"flex-grow-1 min-width-0\">" +
          "<div class=\"d-flex justify-content-between align-items-start mb-1\">" +
            "<span class=\"fw-bold small\">" + (c.author_name || "Unknown") + "</span>" +
            "<small class=\"text-muted\">" + (c.created_at || "") + "</small>" +
          "</div>" +
          "<div class=\"d-flex justify-content-between align-items-start gap-2\">" +
            "<div class=\"small report-comment-body flex-grow-1 min-width-0" + (isReply ? " text-muted" : " text-secondary") + "\">" + (c.comment_body || "") + "</div>" +
            "<div class=\"d-flex gap-2 flex-shrink-0\">" +
              "<a href=\"javascript:void(0)\" class=\"comment-reply-link small text-primary text-decoration-none\" data-comment-id=\"" + (c.comment_id || "") + "\" data-author-name=\"" + authorEscaped + "\">Reply</a>" +
              (isOwnComment ? "<a href=\"javascript:void(0)\" class=\"comment-edit-link small text-primary text-decoration-none\" data-comment-id=\"" + (c.comment_id || "") + "\" data-comment-body=\"" + bodyEscaped + "\">Edit</a>" : "") +
            "</div>" +
          "</div>" +
        "</div>";
      return card;
    }

    function renderReportComments(report) {
      var listEl = document.getElementById("reportDetailCommentsList");
      var emptyEl = document.getElementById("reportDetailCommentsEmpty");
      if (!listEl) return;
      var comments = (report && report.comments) ? report.comments : [];
      listEl.innerHTML = "";
      if (comments.length === 0) {
        if (emptyEl) {
          emptyEl.style.display = "block";
        }
        return;
      }

      if (emptyEl) emptyEl.style.display = "none";

      var topLevel = [];
      var repliesByParent = {};
      comments.forEach(function (c) {
        var pid = c.parent_comment_id;
        if (pid == null || pid === "") {
          topLevel.push(c);
        } else {
          if (!repliesByParent[pid]) repliesByParent[pid] = [];
          repliesByParent[pid].push(c);
        }
      });

      function appendReplies(container, parentId, depth) {
        var replies = repliesByParent[parentId] || [];
        replies.forEach(function (r) {
          var replyWrapper = document.createElement("div");
          replyWrapper.className = "report-comment-reply-wrapper";
          replyWrapper.style.marginLeft = depth > 0 ? "24px" : "40px";
          replyWrapper.style.paddingLeft = "12px";
          replyWrapper.style.borderLeft = "2px solid #dee2e6";
          replyWrapper.style.marginTop = "4px";
          replyWrapper.appendChild(buildCommentCard(r, true));
          container.appendChild(replyWrapper);
          appendReplies(replyWrapper, r.comment_id, depth + 1);
        });
      }

      topLevel.forEach(function (c) {
        listEl.appendChild(buildCommentCard(c, false));
        appendReplies(listEl, c.comment_id, 0);
      });
    }

    function refreshReportComments(reportId) {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", "/reports/" + reportId, true);
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
      xhr.onload = function () {
        if (xhr.status !== 200) return;
        try {
          var updated = JSON.parse(xhr.responseText);
          var idx = reportsData.findIndex(function (r) { return r.report_id === reportId; });
          if (idx >= 0 && updated && updated.comments) {
            reportsData[idx].comments = updated.comments;
            var activeIdEl = document.getElementById("commentReportId");
            var activeId = activeIdEl ? activeIdEl.value : null;
            if (activeId && String(activeId) === String(reportId)) {
              renderReportComments(reportsData[idx]);
            }
          }
        } catch (e) {}
      };
      xhr.send();
    }

    function startReportCommentsPolling(reportId) {
      if (reportCommentsPollInterval) clearInterval(reportCommentsPollInterval);
      reportCommentsPollInterval = setInterval(function () { refreshReportComments(reportId); }, 5000);
    }

    function stopReportCommentsPolling() {
      if (reportCommentsPollInterval) {
        clearInterval(reportCommentsPollInterval);
        reportCommentsPollInterval = null;
      }
    }

    document.addEventListener("click", function (e) {
      var replyLink = e.target.closest(".comment-reply-link");
      var editLink = e.target.closest(".comment-edit-link");
      if (replyLink) {
        e.preventDefault();
        var parentId = replyLink.getAttribute("data-comment-id") || "";
        var authorName = replyLink.getAttribute("data-author-name") || "";
        document.dispatchEvent(new CustomEvent("openReportCommentEditor", { detail: { mode: "reply", parentCommentId: parentId, replyToAuthor: authorName } }));
        return;
      }
      if (editLink) {
        e.preventDefault();
        var commentId = editLink.getAttribute("data-comment-id") || "";
        var body = (editLink.getAttribute("data-comment-body") || "").replace(/&quot;/g, '"').replace(/&lt;/g, "<").replace(/&gt;/g, ">");
        document.dispatchEvent(new CustomEvent("openReportCommentEditor", { detail: { mode: "edit", commentId: commentId, commentBody: body } }));
        return;
      }
    });
  
    var listEl = document.getElementById("pendingReportList");
    if (listEl) {
      listEl.addEventListener("click", function (e) {
        var item = e.target.closest(".report-list-item");
        if (!item) return;
        var reportId = parseInt(item.getAttribute("data-report-id"), 10);
        var report = reportsData.find(function (r) { return r.report_id === reportId; });
        if (!report) return;
        document.querySelectorAll(".report-list-item").forEach(function (el) { el.classList.remove("active"); });
        item.classList.add("active");
        var placeholder = document.getElementById("reportDetailPlaceholder");
        var content = document.getElementById("reportDetailContent");
        if (placeholder) placeholder.style.display = "none";
        if (content) content.style.display = "grid";
        var sharedCommentSection = document.getElementById("sharedCommentSection");
        var pendingDetailCol = document.querySelector("#reportDetailContent").closest(".col-md-8");
        if (sharedCommentSection && pendingDetailCol) {
          pendingDetailCol.appendChild(sharedCommentSection);
          sharedCommentSection.style.display = "";
        }
        var titleEl = document.getElementById("reportDetailTitle");
        var reportIdField = document.getElementById("currentActiveReportId");
        if (reportIdField) reportIdField.value = report.report_id;
        var commentReportIdEl = document.getElementById("commentReportId");
        if (commentReportIdEl) commentReportIdEl.value = report.report_id;
        if (titleEl) titleEl.textContent = "Weekly-" + report.author_name + "(" + report.week_name + ")";
        var revEl = document.getElementById("reportDetailReviewer");
        if (revEl) revEl.textContent = report.reviewer_name || "";
        var ccEl = document.getElementById("reportDetailCC");
        if (ccEl) ccEl.textContent = report.cc_names || "";
        var deptEl = document.getElementById("reportDetailDepartment");
        if (deptEl) deptEl.textContent = report.department_name || "";
        var createdEl = document.getElementById("reportDetailCreated");
        if (createdEl) createdEl.textContent = report.created_on || "";
        var bodyEl = document.getElementById("reportDetailBody");
        if (bodyEl) bodyEl.innerHTML = report.report_content || "";
        renderReportComments(report);
        startReportCommentsPolling(report.report_id);
        var actionsEl = document.getElementById("reportDetailActions");
        var authorActions = document.getElementById("reportDetailActionsAuthor");
        var reviewerActions = document.getElementById("reportDetailActionsReviewer");
        if (actionsEl && authorActions && reviewerActions) {
          authorActions.style.display = "none";
          reviewerActions.style.display = "none";
          authorActions.classList.add("d-none");
          reviewerActions.classList.add("d-none");
          if (report.is_author) {
            actionsEl.style.display = "block";
            authorActions.classList.remove("d-none");
            authorActions.style.display = "flex";
          } if (report.is_reviewer && !report.is_checked) {
            actionsEl.style.display = "block";
            reviewerActions.classList.remove("d-none");
            reviewerActions.style.display = "flex";
            var approvedBtn = document.getElementById("reportApprovedBtn");
            if (approvedBtn) approvedBtn.setAttribute("data-report-id", report.report_id);
          } if (!report.is_author && !(report.is_reviewer && !report.is_checked)) {
            actionsEl.style.display = "none";
          }
        }
        });
        }
        var reportDetailCloseBtn = document.getElementById("reportDetailCloseBtn");
        if (reportDetailCloseBtn) {
          reportDetailCloseBtn.addEventListener("click", function () {
            stopReportCommentsPolling();
            var placeholder = document.getElementById("reportDetailPlaceholder");
            var content = document.getElementById("reportDetailContent");
            if (placeholder) placeholder.style.display = "block";
            if (content) content.style.display = "none";
            var sharedCommentSection = document.getElementById("sharedCommentSection");
            if (sharedCommentSection) sharedCommentSection.style.display = "none";
            document.querySelectorAll(".report-list-item.active").forEach(function (el) { el.classList.remove("active"); });
          });
        }
        var approvedBtn = document.getElementById("reportApprovedBtn");
        if (approvedBtn) {
        approvedBtn.addEventListener("click", function () {
        var reportId = this.getAttribute("data-report-id");
        if (!reportId) return;
        var btn = this;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Approving...';
        var form = document.createElement("form");
        form.method = "POST";
        form.action = "/reports/" + reportId + "/approve";
        document.body.appendChild(form);
        form.submit();
        });
        }

        var reviewedListEl = document.getElementById("reviewedReportList");
        if (reviewedListEl) {
        reviewedListEl.addEventListener("click", function (e) {
            var item = e.target.closest(".reviewed-report-list-item");
            if (!item) return;
            var reportId = parseInt(item.getAttribute("data-report-id"), 10);
            var report = reportsData.find(function (r) { return r.report_id === reportId; });
            if (!report) return;
            var commentReportIdEl = document.getElementById("commentReportId");
            if (commentReportIdEl) commentReportIdEl.value = report.report_id;
            document.querySelectorAll("#reviewedReportList .reviewed-report-list-item").forEach(function (el) { el.classList.remove("active"); });
            item.classList.add("active");
            var placeholder = document.getElementById("reviewedDetailPlaceholder");
            var content = document.getElementById("reviewedDetailContent");
            if (placeholder) placeholder.style.display = "none";
            if (content) content.style.display = "block";
            var titleEl = document.getElementById("reviewedDetailTitle");
            if (titleEl) titleEl.textContent = "Weekly-" + report.author_name + "(" + report.week_name + ")";
            var revEl = document.getElementById("reviewedDetailReviewer");
            if (revEl) revEl.textContent = report.reviewer_name || "";
            var ccEl = document.getElementById("reviewedDetailCC");
            if (ccEl) ccEl.textContent = report.cc_names || "";
            var deptEl = document.getElementById("reviewedDetailDepartment");
            if (deptEl) deptEl.textContent = report.department_name || "";
            var createdEl = document.getElementById("reviewedDetailCreated");
            if (createdEl) createdEl.textContent = report.created_on || "";
            var bodyEl = document.getElementById("reviewedDetailBody");
            if (bodyEl) bodyEl.innerHTML = report.report_content || "";
            var sharedCommentSection = document.getElementById("sharedCommentSection");
            var reviewedDetailCol = document.querySelector("#reviewedDetailContent").closest(".col-md-8");
            if (sharedCommentSection && reviewedDetailCol) {
              reviewedDetailCol.appendChild(sharedCommentSection);
              sharedCommentSection.style.display = "";
            }
            var commentReportIdEl = document.getElementById("commentReportId");
            if (commentReportIdEl) commentReportIdEl.value = report.report_id;
            renderReportComments(report);
            startReportCommentsPolling(report.report_id);
        });
        }
           // CC tab click handler
          var ccListEl = document.getElementById("ccReportList");
          if (ccListEl) {
              ccListEl.addEventListener("click", function (e) {
                  var item = e.target.closest(".cc-report-list-item");
                  if (!item) return;
                  var reportId = parseInt(item.getAttribute("data-report-id"), 10);
                  var report = reportsData.find(function (r) { return r.report_id === reportId; });
                  if (!report) return;

                  var commentReportIdEl = document.getElementById("commentReportId");
                  if (commentReportIdEl) commentReportIdEl.value = report.report_id;

                  document.querySelectorAll("#ccReportList .cc-report-list-item").forEach(function (el) { el.classList.remove("active"); });
                  item.classList.add("active");

                  var placeholder = document.getElementById("ccDetailPlaceholder");
                  var content = document.getElementById("ccDetailContent");
                  if (placeholder) placeholder.style.display = "none";
                  if (content) content.style.display = "block";

                  // Move shared comment section into CC detail column so it shows in this tab
                  var sharedCommentSection = document.getElementById("sharedCommentSection");
                  var ccDetailCol = document.getElementById("ccDetailContent") && document.getElementById("ccDetailContent").closest(".col-md-8");
                  if (sharedCommentSection && ccDetailCol) {
                    ccDetailCol.appendChild(sharedCommentSection);
                    sharedCommentSection.style.display = "";
                  }

                  var titleEl = document.getElementById("ccDetailTitle");
                  if (titleEl) titleEl.textContent = "Weekly-" + report.author_name + "(" + report.week_name + ")";
                  var revEl = document.getElementById("ccDetailReviewer");
                  if (revEl) revEl.textContent = report.reviewer_name || "";
                  var ccEl = document.getElementById("ccDetailCC");
                  if (ccEl) ccEl.textContent = report.cc_names || "";
                  var deptEl = document.getElementById("ccDetailDepartment");
                  if (deptEl) deptEl.textContent = report.department_name || "";
                  var createdEl = document.getElementById("ccDetailCreated");
                  if (createdEl) createdEl.textContent = report.created_on || "";
                  var bodyEl = document.getElementById("ccDetailBody");
                  if (bodyEl) bodyEl.innerHTML = report.report_content || "";
                  renderReportComments(report);
                  startReportCommentsPolling(report.report_id);
              });
          }
          // Company-wide tab click handler
          var companyWideListEl = document.getElementById("companyWideReportList");
          if (companyWideListEl) {
              companyWideListEl.addEventListener("click", function (e) {
                  var item = e.target.closest(".company-wide-report-list-item");
                  if (!item) return;
                  var reportId = parseInt(item.getAttribute("data-report-id"), 10);
                  var report = reportsData.find(function (r) { return r.report_id === reportId; });
                  if (!report) return;
                  
                  document.querySelectorAll("#companyWideReportList .company-wide-report-list-item").forEach(function (el) { el.classList.remove("active"); });
                  item.classList.add("active");
                  
                  var placeholder = document.getElementById("companyWideDetailPlaceholder");
                  var content = document.getElementById("companyWideDetailContent");
                  if (placeholder) placeholder.style.display = "none";
                  if (content) content.style.display = "block";
                  
                  var titleEl = document.getElementById("companyWideDetailTitle");
                  if (titleEl) titleEl.textContent = "Weekly-" + report.author_name + "(" + report.week_name + ")";
                  var revEl = document.getElementById("companyWideDetailReviewer");
                  if (revEl) revEl.textContent = report.reviewer_name || "";
                  var ccEl = document.getElementById("companyWideDetailCC");
                  if (ccEl) ccEl.textContent = report.cc_names || "";
                  var deptEl = document.getElementById("companyWideDetailDepartment");
                  if (deptEl) deptEl.textContent = report.department_name || "";
                  var createdEl = document.getElementById("companyWideDetailCreated");
                  if (createdEl) createdEl.textContent = report.created_on || "";
                  var bodyEl = document.getElementById("companyWideDetailBody");
                  if (bodyEl) bodyEl.innerHTML = report.report_content || "";

                  var modal = document.getElementById("companyWideReportModal");
                  if (modal && typeof bootstrap !== "undefined" && bootstrap.Modal) {
                      document.getElementById("companyWideModalTitle").textContent = "Weekly-" + report.author_name + " (" + report.week_name + ")";
                      var mRev = document.getElementById("companyWideModalReviewer");
                      if (mRev) mRev.textContent = report.reviewer_name || "";
                      var mCc = document.getElementById("companyWideModalCC");
                      if (mCc) mCc.textContent = report.cc_names || "";
                      var mDept = document.getElementById("companyWideModalDepartment");
                      if (mDept) mDept.textContent = report.department_name || "";
                      var mCreated = document.getElementById("companyWideModalCreated");
                      if (mCreated) mCreated.textContent = report.created_on || "";
                      var mStatus = document.getElementById("companyWideModalStatus");
                      if (mStatus) mStatus.textContent = report.is_checked ? "Reviewed" : "Pending";
                      var mBody = document.getElementById("companyWideModalBody");
                      if (mBody) mBody.innerHTML = report.report_content || "";
                      var bsModal = new bootstrap.Modal(modal);
                      bsModal.show();
                  }
              });
          }

      // When switching to a tab, re-show the selected report detail if one was already selected (so it doesn't disappear)
      document.addEventListener('shown.bs.tab', function (e) {
          if (!e.target || !e.target.getAttribute || e.target.getAttribute('data-bs-toggle') !== 'tab') return;
          var href = e.target.getAttribute('href') || '';
          var reportId, report, placeholder, content, sharedCommentSection;

          if (href === '#Pending') {
              var activeItem = document.querySelector('#pendingReportList .report-list-item.active');
              if (!activeItem) {
                stopReportCommentsPolling();
                sharedCommentSection = document.getElementById("sharedCommentSection");
                if (sharedCommentSection) sharedCommentSection.style.display = "none";
                return;
              }
              reportId = parseInt(activeItem.getAttribute('data-report-id'), 10);
              report = reportsData.find(function (r) { return r.report_id === reportId; });
              if (!report) return;
              placeholder = document.getElementById("reportDetailPlaceholder");
              content = document.getElementById("reportDetailContent");
              if (placeholder) placeholder.style.display = "none";
              if (content) content.style.display = "grid";
              sharedCommentSection = document.getElementById("sharedCommentSection");
              var pendingDetailCol = document.querySelector("#reportDetailContent").closest(".col-md-8");
              if (sharedCommentSection && pendingDetailCol) {
                pendingDetailCol.appendChild(sharedCommentSection);
                sharedCommentSection.style.display = "";
              }
              var commentReportIdEl = document.getElementById("commentReportId");
              if (commentReportIdEl) commentReportIdEl.value = report.report_id;
              var reportIdField = document.getElementById("currentActiveReportId");
              if (reportIdField) reportIdField.value = report.report_id;
              renderReportComments(report);
              startReportCommentsPolling(report.report_id);
          } else if (href === '#Reviewed') {
              var activeItemRev = document.querySelector('#reviewedReportList .reviewed-report-list-item.active');
              if (!activeItemRev) {
                stopReportCommentsPolling();
                sharedCommentSection = document.getElementById("sharedCommentSection");
                if (sharedCommentSection) sharedCommentSection.style.display = "none";
                return;
              }
              reportId = parseInt(activeItemRev.getAttribute('data-report-id'), 10);
              report = reportsData.find(function (r) { return r.report_id === reportId; });
              if (!report) return;
              placeholder = document.getElementById("reviewedDetailPlaceholder");
              content = document.getElementById("reviewedDetailContent");
              if (placeholder) placeholder.style.display = "none";
              if (content) content.style.display = "block";
              sharedCommentSection = document.getElementById("sharedCommentSection");
              var reviewedDetailCol = document.querySelector("#reviewedDetailContent").closest(".col-md-8");
              if (sharedCommentSection && reviewedDetailCol) {
                reviewedDetailCol.appendChild(sharedCommentSection);
                sharedCommentSection.style.display = "";
              }
              var commentReportIdEl = document.getElementById("commentReportId");
              if (commentReportIdEl) commentReportIdEl.value = report.report_id;
              renderReportComments(report);
              startReportCommentsPolling(report.report_id);
          } else if (href === '#cc') {
              var activeItemCc = document.querySelector('#ccReportList .cc-report-list-item.active');
              if (!activeItemCc) {
                stopReportCommentsPolling();
                sharedCommentSection = document.getElementById("sharedCommentSection");
                if (sharedCommentSection) sharedCommentSection.style.display = "none";
                return;
              }
              reportId = parseInt(activeItemCc.getAttribute('data-report-id'), 10);
              report = reportsData.find(function (r) { return r.report_id === reportId; });
              if (!report) return;
              placeholder = document.getElementById("ccDetailPlaceholder");
              content = document.getElementById("ccDetailContent");
              if (placeholder) placeholder.style.display = "none";
              if (content) content.style.display = "block";
              sharedCommentSection = document.getElementById("sharedCommentSection");
              var ccDetailCol = document.querySelector("#ccDetailContent") && document.querySelector("#ccDetailContent").closest(".col-md-8");
              if (sharedCommentSection && ccDetailCol) {
                ccDetailCol.appendChild(sharedCommentSection);
                sharedCommentSection.style.display = "";
              }
              var commentReportIdEl = document.getElementById("commentReportId");
              if (commentReportIdEl) commentReportIdEl.value = report.report_id;
              renderReportComments(report);
              startReportCommentsPolling(report.report_id);
          }
      });

      // If report_id in URL (e.g. from approvals page link), select that report
      var urlParams = new URLSearchParams(window.location.search);
      var openReportId = urlParams.get('report_id');
      if (openReportId) {
        var rid = parseInt(openReportId, 10);
        if (rid && reportsData.some(function (r) { return r.report_id === rid; })) {
          var pendingItem = document.querySelector('#pendingReportList .report-list-item[data-report-id="' + rid + '"]');
          var reviewedItem = document.querySelector('#reviewedReportList .reviewed-report-list-item[data-report-id="' + rid + '"]');
          var ccItem = document.querySelector('#ccReportList .cc-report-list-item[data-report-id="' + rid + '"]');
          var tabLink, targetItem;
          if (pendingItem) {
            tabLink = document.querySelector('a[href="#Pending"]');
            targetItem = pendingItem;
          } else if (reviewedItem) {
            tabLink = document.querySelector('a[href="#Reviewed"]');
            targetItem = reviewedItem;
          } else if (ccItem) {
            tabLink = document.querySelector('a[href="#cc"]');
            targetItem = ccItem;
          }
          if (tabLink && targetItem) {
            tabLink.click();
            setTimeout(function () { targetItem.click(); }, 100);
          }
        }
      }
    }
});


// report editor JS CKEditor
(function () {
    function initReportCK() {
        if (typeof ClassicEditor === 'undefined') return;
        var el = document.getElementById("reportCKEditor");
        if (!el) return;

        ClassicEditor.create(el, {
            placeholder: "Write your report..."
        }).then(function (editor) {
            window.reportCKInstance = editor;
        }).catch(function () { /* CKEditor init failed */ });
    }
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initReportCK);
    } else {
        initReportCK();
    }
})();

//edit report modal
(function () {
    var modal = document.getElementById("newReportModal");
    var modalTitle = document.getElementById("newReportModalLabel");
    if (!modal || !modalTitle) return;

    modal.addEventListener("show.bs.modal", function (e) {
        var form = modal.querySelector("form");
        if (form && form.action && form.action.indexOf("/reports/edit/") !== -1) {
            modalTitle.textContent = "Update Weekly Report";
            return;
        }
        var link = e.relatedTarget;
        if (link && link.classList && link.classList.contains("list-group-item-action")) {
            var name = link.getAttribute("data-report-name") || "";
            var title = link.getAttribute("data-report-title") || "";
            modalTitle.textContent = title ? "Edit: " + title : "Update Weekly Report";
        } else {
            modalTitle.textContent = "Weekly report";
        }
    });
})();

// comment editor
(function () {
    var popover = document.getElementById("commentEditorPopover");
    var cancelBtn = document.getElementById("commentEditorCancel");
    var sendBtn = document.getElementById("commentEditorSend");
    var commentEditorInstance = null;
    var currentPlaceholder = null;
    var commentEditId = null;
    var commentParentId = null;

    document.addEventListener("openReportCommentEditor", function (e) {
        var d = e.detail || {};
        var ph = document.querySelector(".comment-placeholder");
        if (!ph || !popover) return;
        showCommentEditor(ph, d);
    });

    function positionPopover(placeholder) {
        if (!popover || !placeholder) return;
        var rect = placeholder.getBoundingClientRect();
        var gap = 12;
        var viewportWidth = window.innerWidth;
        var viewportHeight = window.innerHeight;
        var popoverHeight = popover.offsetHeight;
        var popoverWidth = popover.offsetWidth;
        var topPosition;
        if (rect.top - popoverHeight - gap >= gap) {
            topPosition = rect.top - popoverHeight - gap;
        } else {
            topPosition = rect.bottom + gap;
        }
        topPosition = Math.max(gap, Math.min(topPosition, viewportHeight - popoverHeight - gap));
        var leftPosition = rect.left;
        if (leftPosition + popoverWidth > viewportWidth - gap) leftPosition = viewportWidth - popoverWidth - gap;
        if (leftPosition < gap) leftPosition = gap;
        popover.style.top = topPosition + "px";
        popover.style.left = leftPosition + "px";
    }

    function showCommentEditor(placeholder, opts) {
        if (!popover || !placeholder) return;
        opts = opts || {};
        commentEditId = (opts.mode === "edit" && opts.commentId) ? opts.commentId : null;
        commentParentId = (opts.mode === "reply" && opts.parentCommentId) ? opts.parentCommentId : null;
        placeholder.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
        currentPlaceholder = placeholder;
        currentPlaceholder.style.visibility = "hidden"; 
        popover.style.display = "block";

        var textarea = document.getElementById("commentreportCKEditor");
        if (!textarea) return;
        var initialBody = (opts.mode === "edit" && opts.commentBody) ? opts.commentBody : "";

        if (typeof ClassicEditor !== "undefined" && !commentEditorInstance) {
            textarea.value = initialBody;
            ClassicEditor.create(textarea, { 
                placeholder: opts.mode === "reply" && opts.replyToAuthor ? "Reply to " + opts.replyToAuthor + "..." : "Write your comment..."
            })
            .then(function (editor) {
                commentEditorInstance = editor;
                if (initialBody) editor.setData(initialBody);
                setTimeout(function () { positionPopover(placeholder); }, 400);
                editor.keystrokes.set("Ctrl+Enter", function () { sendComment(); });
            })
            .catch(function () { /* Comment editor init failed */ });
        } else if (commentEditorInstance) {
            commentEditorInstance.setData(initialBody);
            positionPopover(placeholder);
        } else {
            textarea.value = initialBody;
            positionPopover(placeholder);
        }
    }

    function closeCommentEditor() {
        if (commentEditorInstance) {
            commentEditorInstance.destroy()
                .then(function () { 
                    commentEditorInstance = null; 
                    finalizeClose();
                });
        } else {
            finalizeClose();
        }
    }

    function finalizeClose() {
        popover.style.display = "none";
        commentEditId = null;
        commentParentId = null;
        if (currentPlaceholder) {
            currentPlaceholder.style.visibility = "visible"; 
            currentPlaceholder.style.display = ""; 
            currentPlaceholder = null;
        }
        var textarea = document.getElementById("commentreportCKEditor");
        if (textarea) textarea.value = "";
    }

  //   function showCommentSuccessToast() {
  //     var container = document.getElementById("toastPlacement");
  //     if (!container) return;
  //     var toastEl = document.createElement("div");
  //     toastEl.className = "toast align-items-center text-white bg-success border-0 shadow-lg";
  //     toastEl.setAttribute("role", "alert");
  //     toastEl.setAttribute("aria-live", "assertive");
  //     toastEl.setAttribute("aria-atomic", "true");
  //     toastEl.innerHTML =
  //         "<div class=\"d-flex\">" +
  //         "<div class=\"toast-body\"><i class=\"bx bx-check-circle me-2\"></i>Comment added.</div>" +
  //         "<button type=\"button\" class=\"btn-close btn-close-white me-2 m-auto\" data-bs-dismiss=\"toast\" aria-label=\"Close\"></button>" +
  //         "</div>";
  //     container.appendChild(toastEl);
  //     var toast = new bootstrap.Toast(toastEl, { autohide: true, delay: 5000 });
  //     toast.show();
  //     toastEl.addEventListener("hidden.bs.toast", function () { toastEl.remove(); });
  // }

  function showCommentSuccessToast() {
      if (typeof alertify !== "undefined") {
        alertify.success("Comment added.");
      } else {
        alert("Comment added.");
      }
    }

    function resetCommentSendButton() {
      var btn = document.getElementById("commentEditorSend");
      var spinner = document.getElementById("submitSpinner2");
      var btnText = document.getElementById("submitText2");
      if (btn) btn.disabled = false;
      if (spinner) spinner.classList.add("d-none");
      if (btnText) btnText.textContent = "Send";
    }

    function sendComment() {

      const btn = document.getElementById("commentEditorSend");
      const spinner = document.getElementById("submitSpinner2");
      const btnText = document.getElementById("submitText2");

      if (btn && spinner) {
          btn.disabled = true;
          spinner.classList.remove("d-none");
          if (btnText) btnText.textContent = " Sending...";
      }

      var commentReportIdEl = document.getElementById("commentReportId");
      var reportId = commentReportIdEl ? commentReportIdEl.value : null;
      if (!reportId) {
          resetCommentSendButton();
          alert("Please select a report first.");
          return;
      }
      var body = "";
      if (commentEditorInstance) {
          try { body = commentEditorInstance.getData() || ""; } catch (e) {}
      }
      if (!body) {
          var ta = document.getElementById("commentreportCKEditor");
          if (ta) body = ta.value || "";
      }
      body = (body || "").trim();
      if (!body) {
          resetCommentSendButton();
          alert("Please write a comment.");
          return;
      }
      
      var isEdit = !!commentEditId;
      var xhr = new XMLHttpRequest();
      var url, method;
      if (isEdit) {
          url = "/reports/" + reportId + "/comments/" + commentEditId;
          method = "PATCH";
      } else {
          url = "/reports/" + reportId + "/comment";
          method = "POST";
      }
      var payload = { comment_body: body };
      if (!isEdit && commentParentId) payload.parent_comment_id = commentParentId;
      var bodyJson = JSON.stringify(payload);
      
      xhr.open(method, url);
      xhr.setRequestHeader("Content-Type", "application/json");
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
      xhr.setRequestHeader("Cache-Control", "no-cache");
      xhr.onload = function () {
          if (xhr.status === 200) {
              try {
                  var res = JSON.parse(xhr.responseText);
                  if (res && res.success) {
                      closeCommentEditor();
                      var listEl = document.getElementById("reportDetailCommentsList");
                      var emptyEl = document.getElementById("reportDetailCommentsEmpty");
                      if (isEdit) {
                          var card = listEl ? listEl.querySelector(".report-comment-card[data-comment-id=\"" + commentEditId + "\"]") : null;
                          var bodyEl = card ? card.querySelector(".report-comment-body") : null;
                          if (bodyEl && res.comment_body !== undefined) bodyEl.innerHTML = res.comment_body;
                          if (typeof alertify !== "undefined") alertify.success("Comment updated.");
                          else alert("Comment updated.");
                      } else if (res.author_name !== undefined && listEl) {
                          if (emptyEl) emptyEl.style.display = "none";
                          var cuEl = document.getElementById("current-user-member-id");
                          var curMemberId = (cuEl && cuEl.textContent) ? parseInt(cuEl.textContent, 10) : null;
                          var imgSrc = "/static/profile_pics/" + (res.user_image || "default.jpg");
                          var bodyEsc = (res.comment_body || "").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                          var authorEsc = (res.author_name || "").replace(/"/g, "&quot;");
                          var isReply = !!commentParentId;
                          var card = document.createElement("div");
                          card.className = "list-group-item list-group-item-action border-0 py-2 d-flex gap-2 report-comment-card" + (isReply ? " report-comment-reply" : "");
                          card.setAttribute("data-comment-id", res.comment_id || "");
                          card.innerHTML =
                              "<img src=\"" + imgSrc + "\" alt=\"\" class=\"rounded-circle border flex-shrink-0\" style=\"width: " + (isReply ? "28" : "32") + "px; height: " + (isReply ? "28" : "32") + "px; object-fit: cover;\" onerror=\"this.src='/static/profile_pics/default.jpg'; this.onerror=null;\">" +
                              "<div class=\"flex-grow-1 min-width-0\">" +
                              "<div class=\"d-flex justify-content-between align-items-start mb-1\">" +
                              "<span class=\"fw-bold small\">" + (res.author_name || "Unknown") + "</span>" +
                              "<small class=\"text-muted\">" + (res.created_at || "") + "</small>" +
                              "</div>" +
                              "<div class=\"d-flex justify-content-between align-items-start gap-2\">" +
                              "<div class=\"small report-comment-body flex-grow-1 min-width-0" + (isReply ? " text-muted" : " text-secondary") + "\">" + (res.comment_body || "") + "</div>" +
                              "<div class=\"d-flex gap-2 flex-shrink-0\">" +
                              "<a href=\"javascript:void(0)\" class=\"comment-reply-link small text-primary text-decoration-none\" data-comment-id=\"" + (res.comment_id || "") + "\" data-author-name=\"" + authorEsc + "\">Reply</a>" +
                              (curMemberId ? "<a href=\"javascript:void(0)\" class=\"comment-edit-link small text-primary text-decoration-none\" data-comment-id=\"" + (res.comment_id || "") + "\" data-comment-body=\"" + bodyEsc + "\">Edit</a>" : "") +
                              "</div>" +
                              "</div>" +
                              "</div>";
                          if (isReply) {
                              var parentCard = listEl.querySelector(".report-comment-card[data-comment-id=\"" + commentParentId + "\"]");
                              var wrapper = document.createElement("div");
                              wrapper.className = "report-comment-reply-wrapper";
                              wrapper.style.paddingLeft = "12px";
                              wrapper.style.borderLeft = "2px solid #dee2e6";
                              wrapper.style.marginTop = "4px";
                              wrapper.appendChild(card);
                              if (parentCard) {
                                  var parentWrapper = parentCard.closest(".report-comment-reply-wrapper");
                                  wrapper.style.marginLeft = parentWrapper ? "24px" : "40px";
                                  if (parentWrapper) {
                                      parentWrapper.appendChild(wrapper);
                                  } else {
                                      wrapper.style.marginLeft = "40px";
                                      var sib = parentCard.nextElementSibling;
                                      var insertAfter = parentCard;
                                      while (sib && sib.classList && sib.classList.contains("report-comment-reply-wrapper")) {
                                          insertAfter = sib;
                                          sib = sib.nextElementSibling;
                                      }
                                      listEl.insertBefore(wrapper, insertAfter.nextSibling);
                                  }
                              } else {
                                  wrapper.style.marginLeft = "40px";
                                  listEl.appendChild(wrapper);
                              }
                          } else {
                              listEl.appendChild(card);
                          }
                          if (typeof alertify !== "undefined") alertify.success("Comment added.");
                          else alert("Comment added.");
                      }
                      resetCommentSendButton();
                      return;
                  }
              } catch (e) {}
          }
          resetCommentSendButton();
          alert("Failed to save comment.");
      };
      xhr.onerror = function () {
          resetCommentSendButton();
          alert("Failed to save comment.");
      };
      xhr.send(bodyJson);
  }

    // Event Listeners
    if (cancelBtn) cancelBtn.addEventListener("click", closeCommentEditor);
    if (sendBtn) sendBtn.addEventListener("click", sendComment);

    document.addEventListener("click", function (e) {
        var el = e.target;
        if (el && el.nodeType !== 1) el = el.parentElement; // text node -> parent element
        var ph = el && el.closest ? el.closest(".comment-placeholder") : null;
        
        // If clicking the placeholder
        if (ph) {
            e.preventDefault();
            showCommentEditor(ph);
            return;
        }
        
        // If clicking outside the popover and placeholder, close it
        if (popover && 
            popover.style.display === "block" && 
            !popover.contains(e.target) && 
            (!currentPlaceholder || !currentPlaceholder.contains(e.target))) {
            closeCommentEditor();
        }
    });
})();

// Delete report
function confirmReportDelete() {
    var reportId = document.getElementById("currentActiveReportId").value;
    
    if (!reportId) return;

    Swal.fire({
        title: "Are you sure?",
        text: "This report will be permanently removed!",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#51d28c",
        cancelButtonColor: "#f34e4e",
        confirmButtonText: "Yes, delete it!"
    }).then(function (result) {
        if (result.isConfirmed) {
            // No prefix needed because your blueprint has no url_prefix
            window.location.href = "/reports/delete/" + reportId;
        }
    });
}

// --- 1. THE EDIT FUNCTION ---
function openEditModal() {
  var reportIdField = document.getElementById("currentActiveReportId");
  if (!reportIdField || !reportIdField.value) return;

  var reportId = parseInt(reportIdField.value, 10);
  var reportsDataEl = document.getElementById("reports-data");
  var reportsData = JSON.parse(reportsDataEl.textContent || "[]");

  var report = reportsData.find(function (r) { return r.report_id === reportId; });

  if (report) {
      document.getElementById("newReportModalLabel").textContent = "Update Weekly Report";
      var form = document.querySelector("#newReportModal form");
      form.action = "/reports/edit/" + reportId;

      var submitBtn = document.querySelector("#newReportModal button[type='submit']");
      if (submitBtn) submitBtn.textContent = "Update Report";

      var dateSelect = document.getElementById("weekly-report-date");
      if (dateSelect && report.week_name) {
          // Ensure the report's week exists in the dropdown (it may be a past week not in the default list)
          var hasOption = [].some.call(dateSelect.options, function (opt) { return opt.value === report.week_name; });
          if (!hasOption) {
              var opt = document.createElement("option");
              opt.value = report.week_name;
              opt.textContent = report.week_name;
              dateSelect.insertBefore(opt, dateSelect.options[0]);
          }
          dateSelect.value = report.week_name;
      }

      var reviewerIdInput = document.getElementById("selectedReviewerId");
      var reviewerDisplay = document.getElementById("reportReviewerDisplay");
      if (reviewerIdInput) reviewerIdInput.value = report.reviewer_id || "";
      var usersData = [];
      try {
          var usersEl = document.getElementById("users-data");
          if (usersEl) usersData = JSON.parse(usersEl.textContent || "[]");
      } catch (e) {}
      var reviewerUser = usersData.find(function(u) { return u.member_id === report.reviewer_id; });
      if (reviewerDisplay && reviewerUser) {
          var name = reviewerUser.name || reviewerUser.username || "Unknown";
          reviewerDisplay.innerHTML = "<div class=\"d-flex align-items-center gap-2\"><span class=\"fw-bold text-primary\">" + name + "</span></div>";
      } else if (reviewerDisplay && report.reviewer_name) {
          reviewerDisplay.innerHTML = "<div class=\"d-flex align-items-center gap-2\"><span class=\"fw-bold text-primary\">" + report.reviewer_name + "</span></div>";
      }

      if (window.reportCKInstance && typeof window.reportCKInstance.setData === "function") {
          window.reportCKInstance.setData(report.report_content || "");
      }

      var clearBtn = document.getElementById("reportCCClear");
      var ccSearch = document.getElementById("reportCCSearch");
      if (ccSearch) ccSearch.value = "";
      if (clearBtn) clearBtn.click();

      if (report.cc_member_ids && report.cc_member_ids.length > 0) {
          setTimeout(function() {
              report.cc_member_ids.forEach(function(id) {
                  var contactItem = document.querySelector("#reportCCList [data-member-id=\"" + id + "\"]");
                  if (contactItem) contactItem.click();
              });
          }, 100);
      }

      var modalEl = document.getElementById("newReportModal");
      var modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
      modalInstance.show();
  }
}

// --- 2. THE MODAL RESET ---
document.addEventListener("DOMContentLoaded", function() {
  var modalEl = document.getElementById('newReportModal');
  if (modalEl) {
      modalEl.addEventListener('hidden.bs.modal', function () {
          var form = this.querySelector('form');
          if (form) {
              form.reset();
              form.action = "/reports/create"; 
          }
          document.getElementById("newReportModalLabel").textContent = "Weekly report";
          var submitBtn = this.querySelector("button[type='submit']");
          if (submitBtn) submitBtn.textContent = "Submit Report";
          
          var clearBtn = document.getElementById("reportCCClear");
          if (clearBtn) clearBtn.click();

          if (window.reportCKInstance && typeof window.reportCKInstance.setData === "function") {
              window.reportCKInstance.setData("");
          }
      });
  }
});

// document.addEventListener('DOMContentLoaded', function () {
//     const toastElList = [].slice.call(document.querySelectorAll('.toast'));
//     const toastList = toastElList.map(function (toastEl) {
    
//         const toast = new bootstrap.Toast(toastEl, {
//             autohide: true,
//             delay: 5000 
//         });
//         toast.show();
//         return toast;
//     });
// });


// Comments Section//
function toggleMaximizeComments() {
  const list = document.getElementById('reportDetailCommentsList');
  
  // Check if it's currently at the fixed height
  if (list.style.maxHeight === "350px") {
      list.style.maxHeight = "800px"; // Maximize it
  } else {
      list.style.maxHeight = "350px"; // Back to normal
  }
}

// Update the "Hide/Show" text when the collapse happens
// document.getElementById('commentSectionWrapper').addEventListener('hide.bs.collapse', function () {
//     document.getElementById('toggleText').innerText = 'Show';
// });
// document.getElementById('commentSectionWrapper').addEventListener('show.bs.collapse', function () {
//     document.getElementById('toggleText').innerText = 'Hide';
// });

// function toggleCommentHeight() {
//     const list = document.getElementById('reportDetailCommentsList');
//     const icon = document.getElementById('expandIcon');
  
//     if (list.style.maxHeight === "280px") {
//         list.style.maxHeight = "600px";
//         icon.classList.replace('bi-arrows-angle-expand', 'bi-arrows-angle-contract');
//     } else {
//         list.style.maxHeight = "280px";
//         icon.classList.replace('bi-arrows-angle-contract', 'bi-arrows-angle-expand');
//     }
// }

// Update text when Bootstrap collapse runs
// const wrapper = document.getElementById('commentSectionWrapper');
// wrapper.addEventListener('hide.bs.collapse', () => document.getElementById('toggleLink').innerText = 'Show');
// wrapper.addEventListener('show.bs.collapse', () => document.getElementById('toggleLink').innerText = 'Hide');

function appendComment(comment) {
  const list = document.getElementById('reportDetailCommentsList');
  var imgFile = comment.user_image || comment.author_image || 'default.jpg';
  var imgSrc = '/static/profile_pics/' + imgFile;
  var name = comment.author_name || 'Unknown';
  var time = comment.created_at || comment.timestamp || '';
  var body = comment.comment_body || comment.content || '';
  const commentHtml = `
  <div class="list-group-item border-0 d-flex gap-3 py-2 px-3 bg-transparent">
      <img src="${imgSrc}" alt="" class="rounded-circle border flex-shrink-0" style="width: 32px; height: 32px; object-fit: cover;" onerror="this.src='/static/profile_pics/default.jpg'; this.onerror=null;">
      <div class="flex-grow-1 p-2 rounded-3" style="background-color: #f0f2f5;">
          <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="fw-bold text-dark" style="font-size: 0.85rem;">${name}</span>
              <small class="text-muted" style="font-size: 0.7rem;">${time}</small>
          </div>
          <div class="text-secondary report-comment-body" style="font-size: 0.88rem; line-height: 1.4;">
              ${body}
          </div>
      </div>
  </div>`;
  list.insertAdjacentHTML('beforeend', commentHtml);
}

// Company-wide report modal is opened from gridjs.init.js when clicking the Name link in the grid
