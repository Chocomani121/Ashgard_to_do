    
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
              u.name && u.name.toLowerCase().includes(filter.toLowerCase())
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
                          <span class="fw-bold text-primary">${user.name}</span>
                      </div>`;
                  
                  // 2. THIS IS THE MOST IMPORTANT PART FOR SAVING
                  // It puts the member's ID into the hidden input you just placed
                  if (reviewerIdInput) {
                      reviewerIdInput.value = user.member_id;
                      console.log("ID successfully assigned to form:", reviewerIdInput.value);
                  }
                  
                  reviewerDropdown.classList.add("d-none");
              };
              reviewerList.appendChild(item);
          });
      }
      // E. CC Functions
      function renderCC(filter = "") {
        ccList.innerHTML = "";
        allUsers.filter(u => u.name.toLowerCase().includes(filter.toLowerCase())).forEach(user => {
          const isSelected = selectedCCMembers.find(m => m.member_id === user.member_id);
          const item = document.createElement("a");
          item.className = `list-group-item list-group-item-action border-0 d-flex align-items-center gap-2 small ${isSelected ? 'bg-light text-primary' : ''}`;
          item.innerHTML = `${getAvatarHtml(user)} <span>${user.name}</span>`;
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
          chip.innerHTML = `${getAvatarHtml(user, "20px", "9px")} ${user.name} <i class="bx bx-x ms-1" style="cursor:pointer"></i>`;
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
                    alert("Please select a reviewer before submitting.");
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
                
                console.log("Form is valid. Submitting...");
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
      
      function renderReportComments(comments, listId, emptyId) {
        var listEl = document.getElementById(listId);
        var emptyEl = document.getElementById(emptyId);
        if (!listEl) return;
        listEl.innerHTML = '';
        if (emptyEl) emptyEl.style.display = (comments && comments.length) ? 'none' : 'block';
        if (!comments || !comments.length) return;
        comments.forEach(function (c) {
            var div = document.createElement('div');
            div.className = 'list-group-item list-group-item-action border-0 py-2 px-3';
            div.innerHTML =
                '<div class="d-flex justify-content-between align-items-start small text-muted mb-1">' +
                '<span class="fw-semibold text-dark">' + (c.author_name || '') + '</span>' +
                '<span>' + (c.created_at || '') + '</span></div>' +
                '<div class="small text-secondary">' + (c.comment_body || '').replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>';
            listEl.appendChild(div);
        });
    }
    
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
          if (content) content.style.display = "block";
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
            } else if (report.is_reviewer && !report.is_checked) {
              actionsEl.style.display = "block";
              reviewerActions.classList.remove("d-none");
              reviewerActions.style.display = "flex";
              var approvedBtn = document.getElementById("reportApprovedBtn");
              if (approvedBtn) approvedBtn.setAttribute("data-report-id", report.report_id);
            } else {
              actionsEl.style.display = "none";
            }
          }
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
          });
          }

        // CC tab click handler
        var ccListEl = document.getElementById("ccReportList");
        if (ccListEl) {
            ccListEl.addEventListener("click", function (e) {
                var commentReportIdEl = document.getElementById("commentReportId");
                if (commentReportIdEl) commentReportIdEl.value = reportId;
                var item = e.target.closest(".cc-report-list-item");
                if (!item) return;
                var reportId = parseInt(item.getAttribute("data-report-id"), 10);
                var report = reportsData.find(function (r) { return r.report_id === reportId; });
                if (!report) return;
                
                // Set active state only on CC list items
                document.querySelectorAll("#ccReportList .cc-report-list-item").forEach(function (el) { el.classList.remove("active"); });
                item.classList.add("active");
                
                // Show detail, hide placeholder
                var placeholder = document.getElementById("ccDetailPlaceholder");
                var content = document.getElementById("ccDetailContent");
                if (placeholder) placeholder.style.display = "none";
                if (content) content.style.display = "block";
                
                // Populate detail fields
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
            });
        }

            // Company-wide tab click handler
            var companyWideListEl = document.getElementById("companyWideReportList");
            if (companyWideListEl) {
                var commentReportIdEl = document.getElementById("commentReportId");
                if (commentReportIdEl) commentReportIdEl.value = report.report_id;
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
                });
            }
      }
  });
  
  // function getCurrentReportWeek() {
  //     const today = new Date();
  //     const daysFromMonday = (today.getDay() + 6) % 7;
  //     const monday = new Date(today);
  //     monday.setDate(today.getDate() - daysFromMonday);
  //     const saturday = new Date(monday);
  //     saturday.setDate(monday.getDate() + 5);
  //     return { start: monday, end: saturday };
  // }
  
  // document.addEventListener("DOMContentLoaded", function () {
  //     const sel = document.getElementById("weekly-report-date");
  //     if (!sel) return;
  
  //     function fmt(d) {
  //         const m = String(d.getMonth() + 1).padStart(2, "0");
  //         const day = String(d.getDate()).padStart(2, "0");
  //         return m + "/" + day + "/" + d.getFullYear();
  //     }
  
  //     const { start, end } = getCurrentReportWeek();
  //     const currentLabel = fmt(start) + " - " + fmt(end);
  
  //     sel.innerHTML = "";
  //     const currentOpt = document.createElement("option");
  //     currentOpt.value = currentLabel;
  //     currentOpt.textContent = currentLabel + " (This week)";
  //     currentOpt.selected = true;
  //     sel.appendChild(currentOpt);
  
  //     for (let i = 1; i <= 12; i++) {
  //         const nextMon = new Date(start);
  //         nextMon.setDate(start.getDate() + 7 * i);
  //         const nextSat = new Date(nextMon);
  //         nextSat.setDate(nextMon.getDate() + 5);
  //         const opt = document.createElement("option");
  //         opt.value = fmt(nextMon) + " - " + fmt(nextSat);
  //         opt.textContent = opt.value;
  //         sel.appendChild(opt);
  //     }
  // });
  
  
  // report editor JS
  (function () {
      function initReportCK() {
          if (typeof ClassicEditor === 'undefined') return;
          var el = document.getElementById("reportCKEditor");
          if (!el) return;
  
          ClassicEditor.create(el, {
              placeholder: "Write your report..."
          }).then(function (editor) {
              window.reportCKInstance = editor;
          }).catch(function (err) { console.error(err); });
      }
      if (document.readyState === "loading") {
          document.addEventListener("DOMContentLoaded", initReportCK);
      } else {
          initReportCK();
      }
  })();
  
  (function () {
      var modal = document.getElementById("newReportModal");
      var modalTitle = document.getElementById("newReportModalLabel");
      if (!modal || !modalTitle) return;
  
      modal.addEventListener("show.bs.modal", function (e) {
          var link = e.relatedTarget;
          if (link && link.classList && link.classList.contains("list-group-item-action")) {
              var name = link.getAttribute("data-report-name") || "";
              var title = link.getAttribute("data-report-title") || "";
              modalTitle.textContent = title ? "Edit: " + title : "Edit report";
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
  
      function positionPopover(placeholder) {
      if (!popover || !placeholder) return;
      
      var rect = placeholder.getBoundingClientRect();
      var gap = 10;
      var viewportWidth = window.innerWidth;
      
      // Calculate Top
      var topPosition = rect.top - popover.offsetHeight - gap;
      
      // Calculate Left (Center it to the placeholder, but keep it on screen)
      var leftPosition = rect.left;
      
      // Check if the increased width goes off-screen to the right
      if (leftPosition + popover.offsetWidth > viewportWidth) {
          leftPosition = viewportWidth - popover.offsetWidth - 20; // 20px padding from edge
      }
  
      popover.style.top = topPosition + "px";
      popover.style.left = Math.max(10, leftPosition) + "px";
  }
  
      function showCommentEditor(placeholder) {
          if (!popover || !placeholder) return;
          
          // 1. Hide the placeholder immediately
          currentPlaceholder = placeholder;
          currentPlaceholder.style.visibility = "hidden"; 
  
          // 2. Show the popover container
          popover.style.display = "block";
  
          var textarea = document.getElementById("commentreportCKEditor");
          if (!textarea) return;
  
          if (typeof ClassicEditor !== "undefined" && !commentEditorInstance) {
              ClassicEditor.create(textarea, { 
                  placeholder: "Write your comment..."
              })
              .then(function (editor) {
                  commentEditorInstance = editor;
                  
                  // Reposition once the editor is actually rendered and has height
                  setTimeout(() => positionPopover(placeholder), 50);
  
                  editor.keystrokes.set("Ctrl+Enter", function () { sendComment(); });
              })
              .catch(function (err) { console.error(err); });
          } else {
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
          if (currentPlaceholder) {
              currentPlaceholder.style.visibility = "visible"; // Show it again
              currentPlaceholder.style.display = ""; 
              currentPlaceholder = null;
          }
          var textarea = document.getElementById("commentCKEditor");
          if (textarea) textarea.value = "";
      }
  
      function sendComment() {
        var commentReportIdEl = document.getElementById("commentReportId");
        var reportId = commentReportIdEl ? commentReportIdEl.value : null;
        if (!reportId) {
            alert("Please select a report first.");
            return;
        }
        var body = commentEditorInstance ? commentEditorInstance.getData() : "";
        body = (body || "").trim();
        if (!body) {
            alert("Please write a comment.");
            return;
        }
        var formData = new FormData();
        formData.append("comment_body", body);
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/reports/" + reportId + "/comment");
        xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");
        xhr.setRequestHeader("Cache-Control", "no-cache");
        xhr.onload = function () {
            if (xhr.status === 200) {
                try {
                    var res = JSON.parse(xhr.responseText);
                    if (res && res.success) {
                        closeCommentEditor();
                        if (typeof Swal !== "undefined") {
                            Swal.fire({ title: "Comment added", icon: "success", timer: 1500, showConfirmButton: false });
                        } else {
                            alert("Comment added.");
                        }
                        return;
                    }
                } catch (e) {}
            }
            alert("Failed to save comment.");
        };
        xhr.onerror = function () { alert("Failed to save comment."); };
        xhr.send(formData);
    }
  
      // Event Listeners
      if (cancelBtn) cancelBtn.addEventListener("click", closeCommentEditor);
      if (sendBtn) sendBtn.addEventListener("click", sendComment);
  
      document.addEventListener("click", function (e) {
          var ph = e.target.closest(".comment-placeholder");
          
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
    
    // Find the report data
    var report = reportsData.find(function (r) { return r.report_id === reportId; });
    
    if (report) {
        // Change Modal UI to Edit Mode
        document.getElementById("newReportModalLabel").textContent = "Edit Weekly Report";
        var form = document.querySelector("#newReportModal form");
        form.action = "/reports/edit/" + reportId;
        
        var submitBtn = document.querySelector("#newReportModal button[type='submit']");
        if (submitBtn) submitBtn.textContent = "Update Report";

        // Fill Basic Fields (Ensure these 'name' attributes match your form)
        var dateSelect = document.querySelector("select[name='report_date']");
        if (dateSelect) dateSelect.value = report.week_name;
        
        var revSelect = document.querySelector("select[name='reviewer_id']");
        if (revSelect) revSelect.value = report.reviewer_id;

        // Fill Rich Text (TinyMCE)
        if (window.tinymce && tinymce.get('reportBody')) {
            tinymce.get('reportBody').setContent(report.report_content || "");
        } else {
            var bodyField = document.getElementById("reportBody");
            if (bodyField) bodyField.value = report.report_content || "";
        }

        // Re-populate CC Chips
        // We trigger the 'Clear all' button first to avoid duplicates
        var clearBtn = document.getElementById("reportCCClear");
        if (clearBtn) clearBtn.click();

        // If your Python sends 'cc_member_ids', we 'click' them in the list to recreate chips
        if (report.cc_member_ids && report.cc_member_ids.length > 0) {
            report.cc_member_ids.forEach(function(id) {
                var contactItem = document.querySelector('#reportCCList [data-member-id="' + id + '"]');
                if (contactItem) contactItem.click();
            });
        }

        // Open the Modal
        var modalEl = document.getElementById('newReportModal');
        var modalInstance = bootstrap.Modal.getOrCreateInstance(modalEl);
        modalInstance.show();
    }
}

// --- 2. THE MODAL RESET ---
// This ensures that when you click "+ New", the modal isn't still showing the old "Edit" data
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
            
            if (window.tinymce && tinymce.get('reportBody')) {
                tinymce.get('reportBody').setContent('');
            }
        });
    }
});