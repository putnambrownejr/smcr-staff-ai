// Injected by the /dashboard route (see app/api/routes/dashboard.py).
// The bundled dashboard prototype opens repo files via window.open("file://...."),
// which browsers block from an http page. This shim survives the bundler's
// document swap (documentElement.replaceWith keeps the same window object) and
// reroutes those opens to the backend reveal endpoint, which opens the OS file
// explorer at the requested path. It also auto-answers the prototype's one-time
// "enter your repo root" prompt with the real repo root the server injected.
(function () {
  var ROOT = (window.__SMCR_REPO_ROOT__ || "").replace(/\/+$/, "");
  var API_KEY = window.__SMCR_API_KEY__ || "";
  var origOpen = window.open.bind(window);
  var origPrompt = window.prompt.bind(window);

  // Non-blocking toast instead of window.alert: a native alert() halts the
  // page's event loop (and has wedged automation/screen readers on this page
  // before), which is overkill for a "opened the nearest folder" notice.
  function showToast(message) {
    try {
      var toast = document.createElement("div");
      toast.setAttribute("role", "status");
      toast.style.cssText =
        "position:fixed;left:50%;bottom:28px;transform:translateX(-50%);" +
        "max-width:min(560px,90vw);padding:10px 16px;border:1px solid #313844;" +
        "border-radius:8px;background:#1a2027;color:#eef2f6;font:500 0.84rem/1.45 " +
        "'IBM Plex Sans','Segoe UI',sans-serif;box-shadow:0 6px 24px rgba(0,0,0,0.45);" +
        "z-index:2147483647;opacity:0;transition:opacity 0.25s;";
      toast.textContent = message;
      (document.body || document.documentElement).appendChild(toast);
      requestAnimationFrame(function () { toast.style.opacity = "1"; });
      setTimeout(function () {
        toast.style.opacity = "0";
        setTimeout(function () { toast.remove(); }, 400);
      }, 6000);
    } catch (err) {
      // Fall back to the console rather than a blocking dialog.
      console.warn("[reveal-shim]", message);
    }
  }

  window.prompt = function (message, defaultValue) {
    if (ROOT && typeof message === "string" && message.indexOf("smcr-staff-ai repo") !== -1) {
      return ROOT;
    }
    return origPrompt(message, defaultValue);
  };

  window.open = function (url, target, features) {
    if (typeof url === "string" && url.indexOf("file://") === 0) {
      var path = url.slice("file://".length);
      var headers = {};
      if (API_KEY) headers["X-Local-API-Key"] = API_KEY;
      fetch("/dashboard/files/reveal?path=" + encodeURIComponent(path), { headers: headers })
        .then(function (res) {
          return res
            .json()
            .catch(function () { return {}; })
            .then(function (body) { return { ok: res.ok, body: body }; });
        })
        .then(function (r) {
          if (!r.ok) {
            showToast("Could not open file location: " + (r.body.detail || "unknown error"));
          } else if (r.body.status === "opened_fallback") {
            showToast("That exact file/folder doesn't exist yet — opened the nearest folder that does: " + r.body.resolved);
          }
        })
        .catch(function () {
          showToast("Could not reach the dashboard backend to open the file location.");
        });
      return null;
    }
    return origOpen(url, target, features);
  };
})();
