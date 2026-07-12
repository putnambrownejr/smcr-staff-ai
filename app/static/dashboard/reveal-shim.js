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
            window.alert("Could not open file location: " + (r.body.detail || "unknown error"));
          } else if (r.body.status === "opened_fallback") {
            window.alert("That exact file/folder doesn't exist yet — opened the nearest folder that does: " + r.body.resolved);
          }
        })
        .catch(function () {
          window.alert("Could not reach the dashboard backend to open the file location.");
        });
      return null;
    }
    return origOpen(url, target, features);
  };
})();
