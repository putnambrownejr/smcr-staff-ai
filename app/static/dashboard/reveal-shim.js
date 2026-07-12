// Injected by the /dashboard route (see app/api/routes/dashboard.py).
// The bundled dashboard prototype opens repo files via window.open("file://...."),
// which browsers block from an http page. This shim survives the bundler's
// document swap (documentElement.replaceWith keeps the same window object) and
// reroutes those opens to the backend reveal endpoint, which opens the OS file
// explorer at the requested path. It also auto-answers the prototype's one-time
// "enter your repo root" prompt with the real repo root the server injected.
(function () {
  var ROOT = (window.__SMCR_REPO_ROOT__ || "").replace(/\/+$/, "");
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
      fetch("/dashboard/files/reveal?path=" + encodeURIComponent(path), {
        headers: { "X-SMCR-Dashboard": "1" }
      })
        .then(function (res) {
          return res
            .json()
            .catch(function () { return {}; })
            .then(function (body) { return { ok: res.ok, body: body }; });
        })
        .then(function (r) {
          if (!r.ok) {
            window.alert("Could not open file location: " + (r.body.detail || "unknown error"));
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
