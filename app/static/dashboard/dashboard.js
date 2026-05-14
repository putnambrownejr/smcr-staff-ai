const state = {
  mode: "demo",
  userKey: "",
  apiKey: "",
};

document.getElementById("load-demo").addEventListener("click", () => {
  state.mode = "demo";
  state.userKey = "";
  state.apiKey = "";
  document.getElementById("user-key").value = "";
  document.getElementById("api-key").value = "";
  loadWorkspace();
});

document.getElementById("load-personal").addEventListener("click", () => {
  state.mode = "personal";
  state.userKey = document.getElementById("user-key").value.trim();
  state.apiKey = document.getElementById("api-key").value.trim();
  loadWorkspace();
});

document.getElementById("personnel-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    product_type: form.get("product_type"),
    title: form.get("title"),
    subject_name: form.get("subject_name") || null,
    occasion: form.get("occasion") || null,
    facts: splitLines(form.get("facts")),
    achievements: splitLines(form.get("achievements")),
  };
  const data = await apiFetch("/personnel/products", { method: "POST", body: JSON.stringify(payload) });
  renderToolOutput("personnel-output", data, ["summary", "routing_steps", "review_points", "required_documents"]);
});

document.getElementById("staff-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    product_type: form.get("product_type"),
    topic: form.get("topic"),
    training_or_fictional: true,
  };
  const data = await apiFetch("/staff-products/draft", { method: "POST", body: JSON.stringify(payload) });
  renderToolOutput("staff-output", data, ["review_checklist", "citations", "warnings"]);
});

async function loadWorkspace() {
  updateModeBanner();
  try {
    if (state.mode === "demo") {
      const workspace = await apiFetch("/demo/dashboard/data");
      renderWorkspace(workspace);
    } else {
      const userKey = state.userKey;
      if (!userKey) {
        setWorkspaceNote("Add a user key to load personal views.");
        return;
      }
      const workspace = await apiFetch(`/dashboard/data/${encodeURIComponent(userKey)}`, { auth: true });
      renderWorkspace(workspace);
    }
    setWorkspaceNote("Workspace refreshed.");
  } catch (error) {
    setWorkspaceNote(error.message, true);
  }
}

function renderWorkspace(payload) {
  renderChief(payload.chief_brief);
  renderCareer(payload.career_watch);
  if (payload.mode === "demo") {
    renderAdmin(payload.admin_readiness);
  } else {
    renderAdmin(payload.admin_readiness);
  }
  renderDocuments(payload.document_summary || payload.chief_brief.document_summary || { records: [] });
  renderOpportunities(payload.tracked_opportunities || payload.career_watch.tracked_opportunities || []);
  renderSourceUpdates(payload.documentation_updates || payload.chief_brief.documentation_updates || []);
}

function renderChief(payload) {
  document.getElementById("chief-count").textContent = String((payload.top_priority_items || []).length);
  renderList("chief-summary", payload.summary_lines || []);
  const items = payload.top_priority_items || payload.action_items || [];
  renderQueue(items);
}

function renderAdmin(payload) {
  document.getElementById("admin-count").textContent = String((payload.items || []).length);
  renderList("admin-summary", payload.summary_lines || []);
}

function renderCareer(payload) {
  const items = payload.watch_items || [];
  document.getElementById("career-count").textContent = String(items.length);
  renderList(
    "career-summary",
    items.slice(0, 4).map((item) => `${item.title}${item.due_date ? ` (${item.due_date})` : ""}`),
  );
}

function renderDocuments(payload) {
  const records = payload.records || [];
  const missing = payload.missing_recommended_types || [];
  const lines = [
    `${payload.total_documents || 0} local document(s) indexed`,
    missing.length ? `Missing recommended: ${missing.join(", ")}` : "Core recommended document types present.",
    payload.review_due_count ? `${payload.review_due_count} document(s) due for review` : "No local reviews due right now.",
  ];
  setDocumentWatch(lines, records);
}

function renderOpportunities(items) {
  const target = document.getElementById("opportunity-watch");
  if (!items.length) {
    target.className = "stack-list empty-state";
    target.textContent = "No tracked opportunities available yet.";
    return;
  }
  target.className = "stack-list";
  target.innerHTML = items
    .map(
      (item) => `
        <div class="info-card">
          <span class="callout">${escapeHtml(item.opportunity_type || "opportunity")}</span>
          <h3>${escapeHtml(item.title)}</h3>
          <p>${escapeHtml([item.unit, item.location, item.rank, item.mos].filter(Boolean).join(" | ") || "Local tracked opportunity")}</p>
          <p>${escapeHtml(item.description || item.notes || "Review fit, eligibility, and suspense.")}</p>
        </div>
      `,
    )
    .join("");
}

function renderSourceUpdates(items) {
  const target = document.getElementById("source-updates");
  if (!items.length) {
    target.className = "stack-list empty-state";
    target.textContent = "No source updates are currently stored.";
    return;
  }
  target.className = "stack-list";
  target.innerHTML = items
    .map(
      (item) => `
        <div class="info-card">
          <span class="callout">${escapeHtml(item.review_status || "new")}</span>
          <h3>${escapeHtml(item.tracked_title)}</h3>
          <p>${escapeHtml((item.change_signals || []).join(", ") || "Potential source update detected.")}</p>
          <p>${escapeHtml((item.matched_terms || []).join(", ") || "No matched terms recorded.")}</p>
        </div>
      `,
    )
    .join("");
}

function renderQueue(items) {
  const target = document.getElementById("priority-queue");
  if (!items.length) {
    target.className = "stack-list empty-state";
    target.textContent = "No priority items returned yet.";
    return;
  }
  target.className = "stack-list";
  target.innerHTML = items
    .map(
      (item) => `
        <div class="queue-item">
          <span class="callout">${escapeHtml(item.category || "watch")}</span>
          <h3>${escapeHtml(item.title || "Untitled item")}</h3>
          <p>${escapeHtml(item.recommendation || item.notes || "")}</p>
        </div>
      `,
    )
    .join("");
}

function setDocumentWatch(lines, records = []) {
  const target = document.getElementById("document-watch");
  const bullets = Array.isArray(lines) ? lines : [lines];
  const recordMarkup = records.length
    ? `<ul>${records
        .slice(0, 6)
        .map((record) => `<li>${escapeHtml(record.filename)} <span class="callout">${escapeHtml(record.document_type)}</span></li>`)
        .join("")}</ul>`
    : "";
  target.className = "stack-list";
  target.innerHTML = `<ul>${bullets.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>${recordMarkup}`;
}

function renderToolOutput(targetId, payload, listKeys) {
  const target = document.getElementById(targetId);
  const sectionMarkup = [];
  if (payload.sections?.length) {
    sectionMarkup.push(`
      <section>
        <span class="callout">Sections</span>
        ${payload.sections
          .map(
            (section) => `
              <div>
                <h3>${escapeHtml(section.heading)}</h3>
                <ul>${section.prompts.map((prompt) => `<li>${escapeHtml(prompt)}</li>`).join("")}</ul>
              </div>
            `,
          )
          .join("")}
      </section>
    `);
  }
  for (const key of listKeys) {
    if (!payload[key]?.length) {
      continue;
    }
    const label = key.replaceAll("_", " ");
    sectionMarkup.push(`
      <section>
        <span class="callout">${escapeHtml(label)}</span>
        <ul>${payload[key].map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </section>
    `);
  }
  target.className = "tool-output";
  target.innerHTML = sectionMarkup.join("") || "No output returned.";
}

function renderList(targetId, items) {
  const target = document.getElementById(targetId);
  target.innerHTML = items.length ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("") : "<li>No items.</li>";
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  if (options.auth && state.apiKey) {
    headers["X-Local-API-Key"] = state.apiKey;
  }
  const response = await fetch(path, {
    method: options.method || "GET",
    headers,
    body: options.body,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed (${response.status}): ${text}`);
  }
  return response.json();
}

function setWorkspaceNote(message, critical = false) {
  const note = document.getElementById("workspace-note");
  note.textContent = message;
  note.className = critical ? "helper-text critical" : "helper-text";
}

function updateModeBanner() {
  document.getElementById("mode-badge").textContent = state.mode === "demo" ? "Demo mode" : "Personal mode";
}

function splitLines(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

loadWorkspace();
