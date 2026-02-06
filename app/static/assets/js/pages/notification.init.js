(function () {
  function bind(id, handler) {
    var el = document.getElementById(id);
    if (el) el.addEventListener("click", handler);
  }

  function showFlashedMessages() {
    var el = document.getElementById("flashed-messages");
    if (!el) return;
    var messages;
    try {
      messages = JSON.parse(el.textContent || "[]");
    } catch (e) {
      return;
    }
    if (!messages.length) return;
    messages.forEach(function (item) {
      var category = (item[0] || "message").toLowerCase();
      var text = item[1] || "";
      if (category === "success") alertify.success(text);
      else if (category === "error" || category === "danger") alertify.error(text);
      else if (category === "warning") alertify.warning(text);
      else alertify.message(text);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", showFlashedMessages);
  } else {
    showFlashedMessages();
  }

  bind("alert", function () {
    alertify.alert("Alert Title", "Alert Message!", function () { alertify.success("Ok"); });
  });
  bind("alert-confirm", function () {
    alertify.confirm("This is a confirm dialog.", function () { alertify.success("Ok"); }, function () { alertify.error("Cancel"); });
  });
  bind("alert-prompt", function () {
    alertify.prompt("This is a prompt dialog.", "Default value", function (e, t) { alertify.success("Ok: " + t); }, function () { alertify.error("Cancel"); });
  });
  bind("alert-success", function () { alertify.success("Success message"); });
  bind("alert-error", function () { alertify.error("Error message"); });
  bind("alert-warning", function () { alertify.warning("Warning message"); });
  bind("alert-message", function () { alertify.message("Normal message"); });
})();
