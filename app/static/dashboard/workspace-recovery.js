(() => {
  const message = document.getElementById("message");
  if (location.hostname === "127.0.0.1") {
    document.getElementById("old-address").hidden = false;
    document.getElementById("new-address-link").href = `http://localhost:${location.port || "80"}/dashboard/workspace-recovery`;
    const key = localStorage.getItem("smcr_user_key") || "";
    document.getElementById("current-key").textContent = key || "No saved workspace ID was found at this address.";
    document.getElementById("copy-key").disabled = !key;
    document.getElementById("copy-key").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(key);
        message.textContent = "Workspace ID copied.";
      } catch {
        message.textContent = "Copy the ID shown above manually.";
      }
    });
    return;
  }
  if (location.hostname !== "localhost") {
    message.textContent = "Open this page at localhost or 127.0.0.1.";
    return;
  }
  document.getElementById("new-address").hidden = false;
  document.getElementById("recover-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const key = document.getElementById("workspace-key").value.trim();
    if (!key || key.length > 500 || /[\x00-\x1f\x7f]/.test(key)) {
      message.textContent = "Enter the workspace ID copied from the old address.";
      return;
    }
    localStorage.setItem("smcr_user_key", key);
    localStorage.setItem("smcr_workspace_mode", "personal");
    location.assign("/dashboard");
  });
})();
