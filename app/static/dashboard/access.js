(function () {
  async function unlock(key) {
    const status = document.getElementById("status");
    status.textContent = "Checking passkey…";
    try {
      const response = await fetch("/dashboard", {headers: {"X-Local-API-Key": key}, cache: "no-store"});
      if (!response.ok) {
        sessionStorage.removeItem("smcr_access_key");
        status.textContent = "Passkey not accepted. Check it and try again.";
        return;
      }
      const html = await response.text();
      sessionStorage.setItem("smcr_access_key", key);
      document.open(); document.write(html); document.close();
    } catch (error) { status.textContent = "Could not reach the dashboard. Your passkey has not been changed; try again."; }
  }
  document.getElementById("unlock").addEventListener("submit", function (event) {
    event.preventDefault(); unlock(document.getElementById("passkey").value);
  });
  const key = sessionStorage.getItem("smcr_access_key");
  if (key) unlock(key);
})();
