const state = {
  mode: "demo",
  userKey: "",
  apiKey: "",
  activeLane: resolveInitialLane(),
  workspace: null,
  selectedDocumentId: null,
  apiBase: resolveApiBase(),
};

for (const button of document.querySelectorAll(".lane-button")) {
  button.addEventListener("click", () => {
    state.activeLane = button.dataset.lane || "overview";
    applyLaneVisibility();
  });
}

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

document.addEventListener("click", async (event) => {
  const documentButton = event.target.closest("[data-document-id]");
  if (documentButton) {
    state.selectedDocumentId = documentButton.dataset.documentId;
    renderDocumentLibrary(state.workspace?.document_details || []);
    return;
  }

  const feedToggle = event.target.closest("[data-feed-toggle]");
  if (feedToggle) {
    await toggleCustomFeed(feedToggle.dataset.feedToggle);
    return;
  }

  const feedRefresh = event.target.closest("[data-feed-refresh]");
  if (feedRefresh) {
    await refreshCustomFeed(feedRefresh.dataset.feedRefresh);
    return;
  }

  const saveButton = event.target.closest("[data-reading-save]");
  if (saveButton) {
    await saveReadingProgress(saveButton.dataset.readingSave);
  }
});

async function loadWorkspace() {
  updateModeBanner();
  try {
    if (state.mode === "demo") {
      state.workspace = await apiFetch("/demo/dashboard/data");
    } else {
      const userKey = state.userKey;
      if (!userKey) {
        setWorkspaceNote("Add a user key to load personal views.");
        return;
      }
      state.workspace = await apiFetch(`/dashboard/data/${encodeURIComponent(userKey)}`, { auth: true });
    }
    renderWorkspace(state.workspace);
    setWorkspaceNote("Workspace refreshed.");
  } catch (error) {
    setWorkspaceNote(error.message, true);
  }
}

function renderWorkspace(payload) {
  renderWorkspaceSummary(payload.summary_lines || [], payload.warnings || []);
  renderChief(payload.chief_brief);
  renderNextDrillReadiness(payload.chief_brief?.next_drill_readiness || {});
  renderCareer(payload.career_watch);
  renderAdmin(payload.admin_readiness);
  renderDailyBrief(payload.daily_ops_brief || {});
  renderAnalystBrief(payload.analyst_brief || {});
  renderDocumentsWatch(payload.document_summary || payload.chief_brief?.document_summary || { records: [] });
  renderDocumentLibrary(payload.document_details || []);
  renderTemplateLibrary(payload.template_library || []);
  renderMaradminTicker(payload.maradmin_ticker || []);
  renderCustomWatchFeeds(payload.custom_watch_feeds || []);
  renderHistory(payload.today_in_history || []);
  renderReadingBooks(payload.reading_books || []);
  renderTrackedActions(payload.tracked_actions || []);
  renderOpportunities(payload.tracked_opportunities || payload.career_watch?.tracked_opportunities || []);
  renderSourceUpdates(payload.documentation_updates || payload.chief_brief?.documentation_updates || []);
}

function renderWorkspaceSummary(summaryLines, warnings) {
  renderList("workspace-summary", summaryLines);
  renderList("workspace-warnings", warnings.slice(0, 4));
}

function renderChief(payload) {
  document.getElementById("chief-count").textContent = String((payload.top_priority_items || []).length);
  renderList("chief-summary", payload.summary_lines || []);
  const items = payload.top_priority_items || payload.action_items || [];
  renderQueue(items);
}

function renderNextDrillReadiness(payload) {
  document.getElementById("readiness-posture").textContent =
    payload.readiness_posture || "No readiness posture loaded yet.";
  document.getElementById("readiness-anchor").textContent = payload.anchor_drill_date
    ? `Anchored to next drill: ${payload.anchor_drill_date}`
    : "No next-drill anchor is currently stored.";
  document.getElementById("readiness-decisive-action").textContent =
    payload.decisive_action || "No decisive action is currently surfaced.";
  document
    .querySelector(".readiness-panel")
    ?.setAttribute("data-posture", normalizePosture(payload.readiness_posture || ""));
  renderList("readiness-focus", payload.this_week_focus || []);
  renderEntryRows("readiness-must-do", payload.must_do_before_drill || [], "No immediate pre-drill actions yet.");
  renderList("readiness-friction", payload.likely_friction_points || []);
  renderList("readiness-foundation", payload.missing_foundation || []);
  renderList("readiness-rhythm", payload.standing_rhythm || []);
  renderList("readiness-summary", payload.summary || []);
  renderList("readiness-ready-if", payload.ready_if || []);
  renderList("readiness-workflows", payload.recommended_follow_on_workflows || []);
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

function renderDocumentsWatch(payload) {
  const records = payload.records || [];
  const missing = payload.missing_recommended_types || [];
  const lines = [
    `${payload.total_documents || 0} local document(s) indexed`,
    missing.length ? `Missing recommended: ${missing.join(", ")}` : "Core recommended document types present.",
    payload.review_due_count ? `${payload.review_due_count} document(s) due for review` : "No local reviews due right now.",
  ];
  setDocumentWatch(lines, records);
}

function renderDocumentLibrary(items) {
  const target = document.getElementById("document-library");
  if (!items.length) {
    target.className = "document-library empty-state";
    target.textContent = "No local document previews loaded yet.";
    return;
  }
  if (!state.selectedDocumentId || !items.some((item) => item.context_id === state.selectedDocumentId)) {
    state.selectedDocumentId = items[0].context_id;
  }
  const selected = items.find((item) => item.context_id === state.selectedDocumentId) || items[0];
  target.className = "document-library";
  target.innerHTML = `
    <div class="document-list">
      ${items
        .map(
          (item) => `
            <button
              type="button"
              class="document-row ${item.context_id === state.selectedDocumentId ? "active" : ""}"
              data-document-id="${escapeHtml(item.context_id)}"
            >
              <span class="document-row-title">${escapeHtml(item.filename)}</span>
              <span class="document-row-meta">${escapeHtml(item.document_type)}${item.contains_pii ? " | PII" : ""}</span>
            </button>
          `,
        )
        .join("")}
    </div>
    <div class="document-preview">
      <div class="preview-meta">
        <span class="strip-label">${escapeHtml(selected.document_type)}</span>
        <h3>${escapeHtml(selected.filename)}</h3>
        <p>${escapeHtml(formatDocumentMeta(selected))}</p>
      </div>
      <pre>${escapeHtml(selected.text_preview || "No preview available.")}</pre>
    </div>
  `;
}

function renderTemplateLibrary(items) {
  const target = document.getElementById("template-library");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No templates are loaded yet.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.template_source)}</span>
            <strong>${escapeHtml(item.template_name)}</strong>
            <span class="meta-inline">${escapeHtml(item.template_type)}</span>
          </div>
          <p>${escapeHtml(item.description || "Reusable structure and tone reference.")}</p>
          <p class="meta-inline">${escapeHtml((item.reusable_headings || []).slice(0, 4).join(" | ") || "No reusable headings stored.")}</p>
        </article>
      `,
    )
    .join("");
}

function renderMaradminTicker(items) {
  const target = document.getElementById("maradmin-ticker");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No source-watch items loaded yet.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.status)}</span>
            <strong>${escapeHtml(item.title)}</strong>
          </div>
          <p>${escapeHtml(item.summary)}</p>
          ${item.source_url ? `<p class="meta-inline">${escapeHtml(item.source_url)}</p>` : ""}
        </article>
      `,
    )
    .join("");
}

function renderCustomWatchFeeds(items) {
  const target = document.getElementById("custom-feed-watch");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No custom watch feeds are configured yet.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="feed-card ${item.enabled ? "" : "is-disabled"}">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.trust_level.replaceAll("_", " "))}</span>
            <strong>${escapeHtml(item.name)}</strong>
            <span class="meta-inline">${escapeHtml(item.category)}</span>
          </div>
          <p class="meta-inline">
            ${escapeHtml(item.enabled ? "Enabled" : "Disabled")} |
            ${escapeHtml(item.last_refreshed_at ? `Refreshed ${item.last_refreshed_at}` : "Not refreshed yet")} |
            ${escapeHtml(`${item.last_item_count || 0} item(s)`)}
          </p>
          ${item.last_error ? `<p class="critical">${escapeHtml(item.last_error)}</p>` : ""}
          <p class="meta-inline">${escapeHtml((item.tags || []).join(" | ") || "No extra tags")}</p>
          <div class="button-row">
            <button type="button" class="secondary" data-feed-toggle="${escapeHtml(item.feed_id)}">
              ${item.enabled ? "Disable feed" : "Enable feed"}
            </button>
            <button type="button" class="secondary" data-feed-refresh="${escapeHtml(item.feed_id)}">
              Refresh feed
            </button>
          </div>
          <div class="row-stack">
            ${
              (item.preview_items || []).length
                ? item.preview_items
                    .map(
                      (preview) => `
                        <article class="data-row compact-row">
                          <div class="data-row-head">
                            <span class="strip-label">${escapeHtml(preview.status)}</span>
                            <strong>${escapeHtml(preview.title)}</strong>
                          </div>
                          <p>${escapeHtml(preview.summary)}</p>
                        </article>
                      `,
                    )
                    .join("")
                : `<div class="empty-state">No cached items yet.</div>`
            }
          </div>
        </article>
      `,
    )
    .join("");
}

function renderHistory(items) {
  const target = document.getElementById("history-feed");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No history entry is loaded for today.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.year_label)}</span>
            <strong>${escapeHtml(item.title)}</strong>
          </div>
          <p>${escapeHtml(item.summary)}</p>
          <ul>${(item.significance || []).map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")}</ul>
        </article>
      `,
    )
    .join("");
}

function renderReadingBooks(items) {
  const target = document.getElementById("reading-library");
  if (!items.length) {
    target.className = "reading-grid empty-state";
    target.textContent = "No reading-list entries loaded yet.";
    return;
  }
  target.className = "reading-grid";
  target.innerHTML = items
    .map((item) => {
      const progress = item.progress || {};
      const notes = Array.isArray(progress.notes) ? progress.notes.join("\n") : "";
      const status = progress.status || "not_started";
      const disabled = state.mode !== "personal" ? "disabled" : "";
      return `
        <article class="reading-item">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(status.replaceAll("_", " "))}</span>
            <strong>${escapeHtml(item.title)}</strong>
          </div>
          <p class="meta-inline">${escapeHtml(item.author)} | ${escapeHtml((item.categories || []).slice(0, 3).join(", "))}</p>
          <p>${escapeHtml(item.summary)}</p>
          <p class="meta-inline">${escapeHtml((item.key_themes || []).slice(0, 4).join(" | "))}</p>
          <label>
            <span>Status</span>
            <select data-reading-status="${escapeHtml(item.slug)}" ${disabled}>
              ${["not_started", "in_progress", "completed"]
                .map(
                  (value) =>
                    `<option value="${value}" ${value === status ? "selected" : ""}>${value.replaceAll("_", " ")}</option>`,
                )
                .join("")}
            </select>
          </label>
          <label>
            <span>Notes</span>
            <textarea data-reading-notes="${escapeHtml(item.slug)}" rows="4" ${disabled} placeholder="Thoughts, PME takeaways, or why this matters to your lane.">${escapeHtml(notes)}</textarea>
          </label>
          <div class="button-row">
            <button type="button" class="secondary" data-reading-save="${escapeHtml(item.slug)}" ${disabled}>Save reading state</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderDailyBrief(payload) {
  renderList("daily-executive", payload.executive_snapshot || []);
  renderEntryRows("daily-must-do", payload.must_do || [], "No must-do items.");
  renderEntryRows("daily-should-do", payload.should_do || [], "No should-do items.");
  renderEntryRows("daily-can-defer", payload.can_defer || [], "No defer candidates.");
  renderList("daily-waiting", payload.waiting_on || []);
  renderList("daily-blockers", payload.blockers || []);
  renderList("daily-leverage", payload.leverage_actions || []);
  renderList("daily-followups", payload.prep_follow_ups || []);
}

function renderAnalystBrief(payload) {
  renderList("analyst-executive", payload.executive_summary || []);
  renderList("analyst-data-quality", payload.data_quality_notes || []);
  renderList("analyst-kpis", payload.kpi_summary || []);
  renderList("analyst-anomalies", payload.anomalies || []);
  renderList("analyst-causes", payload.likely_causes || []);
  renderList("analyst-assumptions", payload.assumptions || []);
  renderList("analyst-followups", payload.follow_up_checks || []);
}

function renderOpportunities(items) {
  const target = document.getElementById("opportunity-watch");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No tracked opportunities available yet.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.opportunity_type || "opportunity")}</span>
            <strong>${escapeHtml(item.title)}</strong>
          </div>
          <p>${escapeHtml([item.unit, item.location, item.rank, item.mos].filter(Boolean).join(" | ") || "Local tracked opportunity")}</p>
          <p>${escapeHtml(item.description || item.notes || "Review fit, eligibility, and suspense.")}</p>
        </article>
      `,
    )
    .join("");
}

function renderTrackedActions(items) {
  const target = document.getElementById("action-watch");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No tracked POAM items available yet.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.status || "open")}</span>
            <strong>${escapeHtml(item.title)}</strong>
          </div>
          <p>${escapeHtml(item.owner ? `Owner: ${item.owner}` : "Owner not assigned")}</p>
          <p class="meta-inline">${escapeHtml([item.category, item.priority, item.suspense_date ? `Due ${item.suspense_date}` : ""].filter(Boolean).join(" | "))}</p>
          <p>${escapeHtml(item.description || item.notes || "No additional notes yet.")}</p>
        </article>
      `,
    )
    .join("");
}

function renderSourceUpdates(items) {
  const target = document.getElementById("source-updates");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No source updates are currently stored.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.review_status || "new")}</span>
            <strong>${escapeHtml(item.tracked_title)}</strong>
          </div>
          <p>${escapeHtml((item.change_signals || []).join(", ") || "Potential source update detected.")}</p>
          <p class="meta-inline">${escapeHtml((item.matched_terms || []).join(", ") || "No matched terms recorded.")}</p>
        </article>
      `,
    )
    .join("");
}

function renderQueue(items) {
  const target = document.getElementById("priority-queue");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No priority items returned yet.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.category || "watch")}</span>
            <strong>${escapeHtml(item.title || "Untitled item")}</strong>
          </div>
          <p>${escapeHtml(item.recommendation || item.notes || "")}</p>
        </article>
      `,
    )
    .join("");
}

function renderEntryRows(targetId, items, emptyText) {
  const target = document.getElementById(targetId);
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = emptyText;
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.category || item.priority || "watch")}</span>
            <strong>${escapeHtml(item.title || "Untitled item")}</strong>
            ${item.due_date ? `<span class="meta-inline">${escapeHtml(`Due ${item.due_date}`)}</span>` : ""}
          </div>
          <p>${escapeHtml(item.detail || "")}</p>
        </article>
      `,
    )
    .join("");
}

function setDocumentWatch(lines, records = []) {
  const target = document.getElementById("document-watch");
  const bullets = Array.isArray(lines) ? lines : [lines];
  const recordsMarkup = records.length
    ? `<ul>${records
        .slice(0, 6)
        .map((record) => `<li>${escapeHtml(record.filename)} <span class="meta-inline">${escapeHtml(record.document_type)}</span></li>`)
        .join("")}</ul>`
    : "";
  target.className = "row-stack";
  target.innerHTML = `<ul>${bullets.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>${recordsMarkup}`;
}

function renderToolOutput(targetId, payload, listKeys) {
  const target = document.getElementById(targetId);
  const sectionMarkup = [];
  if (payload.sections?.length) {
    sectionMarkup.push(`
      <section>
        <span class="strip-label">Sections</span>
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
        <span class="strip-label">${escapeHtml(label)}</span>
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

async function saveReadingProgress(slug) {
  if (state.mode !== "personal" || !state.userKey) {
    setWorkspaceNote("Switch to personal mode to save reading state.", true);
    return;
  }
  const status = document.querySelector(`[data-reading-status="${CSS.escape(slug)}"]`)?.value || "not_started";
  const notesValue = document.querySelector(`[data-reading-notes="${CSS.escape(slug)}"]`)?.value || "";
  await apiFetch(`/reading-list/state/${encodeURIComponent(state.userKey)}/${encodeURIComponent(slug)}`, {
    method: "PUT",
    auth: true,
    body: JSON.stringify({
      status,
      notes: splitLines(notesValue),
    }),
  });
  setWorkspaceNote("Reading state saved.");
  await loadWorkspace();
}

async function toggleCustomFeed(feedId) {
  const feed = (state.workspace?.custom_watch_feeds || []).find((item) => item.feed_id === feedId);
  if (!feed) {
    setWorkspaceNote("Could not find that custom feed in the current workspace.", true);
    return;
  }
  await apiFetch(`/custom-watch-feeds/${encodeURIComponent(feedId)}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify({ enabled: !feed.enabled }),
  });
  setWorkspaceNote(`Feed ${feed.enabled ? "disabled" : "enabled"}.`);
  await loadWorkspace();
}

async function refreshCustomFeed(feedId) {
  await apiFetch(`/custom-watch-feeds/${encodeURIComponent(feedId)}/refresh`, {
    method: "POST",
    auth: true,
  });
  setWorkspaceNote("Custom feed refreshed.");
  await loadWorkspace();
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  if (options.auth && state.apiKey) {
    headers["X-Local-API-Key"] = state.apiKey;
  }
  const response = await fetch(`${state.apiBase}${path}`, {
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
  const badge = document.getElementById("mode-badge");
  if (badge) {
    badge.textContent = state.mode === "demo" ? "Demo mode" : "Personal mode";
  }
}

function resolveApiBase() {
  if (window.location.protocol === "file:") {
    return "http://127.0.0.1:8000";
  }
  return "";
}

function resolveInitialLane() {
  const lane = window.location.hash.replace("#", "").trim().toLowerCase();
  return lane || "overview";
}

function applyLaneVisibility() {
  const active = state.activeLane;
  for (const button of document.querySelectorAll(".lane-button")) {
    button.classList.toggle("active", button.dataset.lane === active);
  }
  for (const section of document.querySelectorAll("[data-section-group]")) {
    const group = section.dataset.sectionGroup;
    const show = group === "global" || active === "all" || group === active;
    section.classList.toggle("is-hidden", !show);
  }
  window.location.hash = active === "overview" ? "" : active;
}

function splitLines(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatDocumentMeta(item) {
  const parts = [];
  if (item.review_date) {
    parts.push(`Review ${item.review_date}`);
  }
  if (item.expiration_date) {
    parts.push(`Expires ${item.expiration_date}`);
  }
  if (item.contains_pii) {
    parts.push("PII flagged");
  }
  return parts.join(" | ") || "Local advisory reference.";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function normalizePosture(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized.includes("weak") || normalized.includes("degraded")) {
    return "critical";
  }
  if (normalized.includes("active") || normalized.includes("partially")) {
    return "watch";
  }
  if (normalized.includes("track")) {
    return "steady";
  }
  return "default";
}

loadWorkspace();
applyLaneVisibility();
