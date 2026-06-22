// Module split readiness: when this file exceeds ~4000 lines or a second contributor joins,
// split along these seams: state.js, ui.js, lanes/overview.js, lanes/watch.js,
// lanes/bench.js, lanes/workflows.js, lanes/workspace.js.
// Add type="module" to the <script> tag in index.html — FastAPI static mount already
// serves ES modules correctly. No build step required.

const state = {
  mode: "demo",
  userKey: "",
  apiKey: "",
  activeLane: resolveInitialLane(),
  workspace: null,
  selectedDocumentId: null,
  selectedReadingSlug: "",
  selectedReferenceSlug: "",
  apiBase: resolveApiBase(),
  timezoneOptions: buildTimezoneOptions(),
  selectedTimezoneIds: loadTimezoneSelection(),
  benchSections: [],
  userProfile: null,
  timezonePanelOpen: false,
  clockTimer: null,
  lastUpdatedAt: {
    maradmins: null,
    reading: null,
    sourceWatch: null,
  },
  lastUpdatedTimer: null,
  consecutiveFetchFailures: 0,
  connectionLostDismissed: false,
  firstEmptyOrientationDismissed: false,
  todayInHistory: [],
  historyIndex: 0,
};

const PRELOAD_EMPTY_TEXT = "Load workspace to see this";

function emptyStateHtml(headline, detail) {
  return `<div class="empty-state"><p class="empty-state-headline">${headline}</p><p class="empty-state-detail">${detail}</p></div>`;
}
const DEFAULT_BENCH_SECTIONS = ["S-1/Admin", "S-2/Intel", "S-3", "S-4", "S-6"];
const REFRESH_BUTTON_GROUPS = {
  sourceWatch: [
    "refresh-maradmins",
    "refresh-reading",
    "refresh-navadmins",
    "refresh-alnavs",
    "refresh-dod-watch",
    "refresh-source-watch",
  ],
};

const DOCUMENT_TYPE_OPTIONS = [
  "reference_note",
  "doctrine",
  "admin_reference",
  "training_reference",
  "product_template",
  "training_media",
  "orders",
  "fitrep",
  "other",
];

const MOS_BENCH_CATALOG = [
  {
    id: "mos-adjutant-0102",
    label: "0102 / Adjutant",
    parent: "S-1",
    summary: "Accountability, correspondence, awards, staffing discipline, and reserve admin continuity.",
    starter:
      "Help me tighten accountability and correspondence continuity between drills and show me what an XO will ask first.",
  },
  {
    id: "mos-logistics-0402",
    label: "0402 / Logistics officer",
    parent: "S-4",
    summary: "Supportability, sustainment judgment, lead times, and what breaks the plan first.",
    starter:
      "Help me clean up the logistics estimate for AT and show me the first supportability problem I should brief.",
  },
  {
    id: "mos-supply-3002",
    label: "3002 / Supply officer",
    parent: "S-4",
    summary: "Supply accountability, fiscal discipline, inventory readiness, and command supply risk.",
    starter:
      "Help me think through supply accountability before drill and surface the risks that are easiest to miss.",
  },
  {
    id: "mos-magtf-planner-0511",
    label: "0511 / MAGTF planner",
    parent: "S-3",
    summary: "Mission analysis, planning support, assumption control, and staff-integration discipline.",
    starter:
      "Help me keep mission analysis and staff integration clean so the planning process does not drift into busy slides.",
  },
];

for (const button of document.querySelectorAll(".lane-button")) {
  button.addEventListener("click", () => {
    openLane(button.dataset.lane || "overview");
  });
}

document.querySelector("[role='tablist']")?.addEventListener("keydown", (event) => {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") {
    return;
  }
  const tabs = Array.from(event.currentTarget.querySelectorAll("[role='tab']"));
  if (!tabs.length) {
    return;
  }
  event.preventDefault();
  const currentIndex = Math.max(0, tabs.indexOf(document.activeElement));
  const offset = event.key === "ArrowRight" ? 1 : -1;
  const nextIndex = (currentIndex + offset + tabs.length) % tabs.length;
  const nextTab = tabs[nextIndex];
  nextTab.focus();
  openLane(nextTab.dataset.lane || "overview");
});

document.getElementById("load-demo").addEventListener("click", () => {
  state.mode = "demo";
  state.userKey = "";
  state.apiKey = "";
  document.getElementById("user-key").value = "";
  document.getElementById("api-key").value = "";
  loadWorkspace();
});

// Onboarding: first-run key creation
document.getElementById("onboarding-create-workspace")?.addEventListener("click", () => {
  onboardingCreateWorkspace();
});
document.getElementById("onboarding-key-input")?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { onboardingCreateWorkspace(); }
});

// Advanced workspace settings: apply custom key and/or passkey
document.getElementById("apply-advanced-settings")?.addEventListener("click", () => {
  const customKey = (document.getElementById("custom-profile-key")?.value || "").trim();
  const passkey = (document.getElementById("api-key")?.value || "").trim();

  if (customKey) {
    if (!isValidProfileName(customKey)) {
      setWorkspaceNote("Profile name cannot contain / \\ or < >.");
      return;
    }
    localStorage.setItem(SAVED_KEY_STORAGE, customKey);
    document.getElementById("user-key").value = customKey;
    state.userKey = customKey;
    const idDisplay = document.getElementById("profile-id-display");
    if (idDisplay) { idDisplay.textContent = customKey; }
  }

  if (passkey !== undefined) {
    state.apiKey = passkey;
  }

  state.mode = "personal";
  loadWorkspace();
});

// Advanced workspace settings: copy profile ID to clipboard
document.getElementById("copy-profile-id")?.addEventListener("click", () => {
  const id = document.getElementById("profile-id-display")?.textContent || "";
  if (!id) { return; }
  navigator.clipboard?.writeText(id).then(() => {
    const btn = document.getElementById("copy-profile-id");
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = "Copied!";
      setTimeout(() => { btn.textContent = orig; }, 1500);
    }
  });
});

// Onboarding: return visit — demo button
document.getElementById("onboarding-load-demo-return")?.addEventListener("click", () => {
  state.mode = "demo";
  state.userKey = "";
  state.apiKey = "";
  loadWorkspace();
});

// Onboarding: switch profile — show recovery panel without clearing the current key
document.getElementById("onboarding-switch-profile")?.addEventListener("click", () => {
  document.getElementById("onboarding-welcome-back")?.classList.add("is-hidden");
  document.getElementById("onboarding-first-run")?.classList.remove("is-hidden");
  const msgEl = document.getElementById("onboarding-first-run-msg");
  if (msgEl) { msgEl.textContent = "Select a stored profile or enter a name / ID below."; }
  const recoverDetails = document.getElementById("onboarding-recover-details");
  if (recoverDetails) { recoverDetails.open = true; }
});

// Onboarding: load stored profile list when recovery details opens
document.getElementById("onboarding-recover-details")?.addEventListener("toggle", async (e) => {
  if (!e.target.open) { return; }
  const noteEl = document.getElementById("onboarding-recover-note");
  const listEl = document.getElementById("onboarding-profile-list");
  if (!listEl) { return; }
  // Only fetch once — if list already has items, leave it
  if (listEl.childElementCount > 0) { return; }
  try {
    const keys = await apiFetch("/user-profile", { auth: true });
    if (!keys || keys.length === 0) {
      if (noteEl) { noteEl.textContent = "No saved profiles found on this machine."; }
      return;
    }
    if (noteEl) { noteEl.textContent = "Select a profile to restore it:"; }
    listEl.innerHTML = "";
    for (const key of keys) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "link-button";
      btn.textContent = key;
      btn.addEventListener("click", () => {
        const input = document.getElementById("onboarding-key-input");
        if (input) { input.value = key; }
        const errorEl = document.getElementById("onboarding-key-error");
        if (errorEl) { errorEl.textContent = ""; }
        e.target.open = false;
        input?.focus();
      });
      li.appendChild(btn);
      listEl.appendChild(li);
    }
  } catch (err) {
    if (noteEl) {
      noteEl.textContent = err.isNetworkError
        ? "Server not reachable — start the app first."
        : "Could not load saved profiles.";
    }
  }
});
document.getElementById("retry-workspace-load")?.addEventListener("click", () => loadWorkspace());
document.getElementById("reload-demo-workspace")?.addEventListener("click", () => {
  state.mode = "demo";
  state.userKey = "";
  state.apiKey = "";
  loadWorkspace();
});
document.getElementById("dismiss-connection-lost")?.addEventListener("click", () => {
  state.connectionLostDismissed = true;
  setConnectionLostVisible(false);
});
document.getElementById("dismiss-first-empty-orientation")?.addEventListener("click", () => {
  state.firstEmptyOrientationDismissed = true;
  updateFirstEmptyOrientation(false);
});

window.addEventListener("popstate", (event) => {
  const lane = event.state?.lane || resolveInitialLane();
  openLane(lane, "", { updateHistory: false });
});

document.getElementById("load-personal").addEventListener("click", () => {
  const name = document.getElementById("user-key").value.trim();
  if (!isValidProfileName(name)) {
    setWorkspaceNote(name.length === 0
      ? "Enter a profile name above to open your workspace."
      : "Profile name cannot contain / \\ or < >.", true);
    return;
  }
  state.mode = "personal";
  state.userKey = name;
  state.apiKey = document.getElementById("api-key").value.trim();
  loadWorkspace();
});

document.getElementById("section-memory-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await saveSectionMemoryProfile(event.submitter);
});

document.getElementById("clear-section-memory-form").addEventListener("click", () => {
  clearSectionMemoryForm();
  setWorkspaceNote("Section-memory form cleared.");
});
document.getElementById("manage-bench-sections")?.addEventListener("click", toggleBenchSectionsEditor);
document.getElementById("add-bench-section")?.addEventListener("click", addBenchSectionFromInput);
document.getElementById("save-bench-sections")?.addEventListener("click", saveBenchSections);
document.getElementById("save-handoff")?.addEventListener("click", () => saveHandoff());
document.getElementById("save-profile")?.addEventListener("click", () => saveUserProfile());
document.getElementById("rerun-research")?.addEventListener("click", () => runBilletResearch());
document.getElementById("export-profile")?.addEventListener("click", () => exportUserProfile());
document.getElementById("save-template")?.addEventListener("click", () => saveTemplate());
document.getElementById("bench-section-input")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addBenchSectionFromInput();
  }
});

document.getElementById("battle-rhythm-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await saveBattleRhythmBoard();
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

document.getElementById("brief-clinic-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const briefType = form.get("brief_type");
  const audience = form.get("audience");
  const decisionRequired = form.get("decision_required");
  const currentBrief = form.get("current_brief");
  const input = [
    `Brief type: ${briefType}`,
    `Audience: ${audience}`,
    `Decision required: ${decisionRequired}`,
    "Current brief:",
    String(currentBrief || "").trim(),
  ].join("\n");
  const data = await apiFetch("/agents/writing-briefing-coach/run", {
    method: "POST",
    body: JSON.stringify({
      input,
      context: {
        user_key: state.userKey || undefined,
        request_is_training_or_fictional: true,
        user_role: "SMCR officer",
      },
    }),
  });
  renderBriefClinicOutput("brief-clinic-output", data);
});

document.getElementById("mos-advisor-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await runMosAdvisorFromForm();
});

document.getElementById("staff-cycle-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = {
    title: form.get("title"),
    supported_unit: form.get("supported_unit"),
    supported_echelon: form.get("supported_echelon") || "company", // UX6: from form select
    mission_or_training_goal: form.get("mission_or_training_goal"),
    commander_priorities: splitLines(form.get("commander_priorities")),
    section_updates: parseSectionUpdates(form.get("section_updates")),
    training_only: true,
  };
  const data = await apiFetch("/staff/update-cycle", { method: "POST", body: JSON.stringify(payload) });
  renderStaffUpdateCycleOutput("staff-cycle-output", data);
});

document.getElementById("planning-cell-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = await apiFetch("/staff/planning-cell", {
    method: "POST",
    body: JSON.stringify(buildPlanningCellPayloadFromForm()),
  });
  renderPlanningCellOutput("planning-cell-output", data);
});

document.getElementById("refresh-maradmins").addEventListener("click", (event) => refreshSourceLane("maradmins", event.currentTarget));
document.getElementById("refresh-reading").addEventListener("click", (event) => refreshSourceLane("reading", event.currentTarget));
document.getElementById("refresh-navadmins").addEventListener("click", (event) => refreshSourceLane("navadmins", event.currentTarget));
document.getElementById("refresh-alnavs").addEventListener("click", (event) => refreshSourceLane("alnavs", event.currentTarget));
document.getElementById("refresh-dod-watch").addEventListener("click", (event) => refreshSourceLane("dod", event.currentTarget));
document.getElementById("refresh-source-watch").addEventListener("click", (event) => refreshSourceLane("all", event.currentTarget));
initializeDrawerLabels();
document
  .getElementById("thin-staff-run-lone-planner")
  .addEventListener("click", () => launchThinStaffWorkflow("lone-planner"));
document
  .getElementById("thin-staff-open-mission-analysis")
  .addEventListener("click", () => launchThinStaffWorkflow("mission-analysis"));
document
  .getElementById("thin-staff-open-planning-cell")
  .addEventListener("click", () => launchThinStaffWorkflow("planning-cell"));
document
  .getElementById("thin-staff-open-update-cycle")
  .addEventListener("click", () => launchThinStaffWorkflow("update-cycle"));
document
  .getElementById("thin-staff-open-admin")
  .addEventListener("click", () => launchThinStaffWorkflow("admin"));
document
  .getElementById("walk-in-open-lone-planner")
  .addEventListener("click", () => launchWalkInWorkflow("lone-planner"));
document
  .getElementById("walk-in-open-brief-clinic")
  .addEventListener("click", () => launchWalkInWorkflow("brief-clinic"));
document.getElementById("toggle-timezone-panel").addEventListener("click", toggleTimezonePanel);
document.getElementById("save-planning-cell-board").addEventListener("click", savePlanningCellToBattleRhythm);
document.getElementById("run-lone-planner").addEventListener("click", runLonePlannerMode);
document.getElementById("run-section-gap-cover").addEventListener("click", runSectionGapCover);
document.getElementById("run-staff-package").addEventListener("click", runStaffPlanningPackage);
document.getElementById("reading-book-select").addEventListener("change", (event) => {
  state.selectedReadingSlug = event.target.value || "";
  renderReadingBooks(state.workspace?.reading_books || []);
});
document.getElementById("reference-select").addEventListener("change", (event) => {
  state.selectedReferenceSlug = event.target.value || "";
  renderReferenceLibrary(state.workspace?.reference_library || []);
});
document.getElementById("save-document-type").addEventListener("click", () => {
  saveSelectedDocumentType();
});
document.getElementById("apply-document-suggestion").addEventListener("click", () => {
  applySuggestedDocumentType();
});
document.getElementById("document-select")?.addEventListener("change", (event) => {
  state.selectedDocumentId = event.target.value || null;
  renderDocumentLibrary(state.workspace?.document_details || []);
});
// Onboarding card — demo button (first-run step)
document.getElementById("onboarding-load-demo").addEventListener("click", () => {
  state.mode = "demo";
  state.userKey = "";
  state.apiKey = "";
  document.getElementById("user-key").value = "";
  document.getElementById("api-key").value = "";
  loadWorkspace();
});

// Workflow dialog — close button and backdrop click
document.getElementById("workflow-dialog-close").addEventListener("click", () => {
  document.getElementById("workflow-dialog").close();
});
document.getElementById("workflow-dialog").addEventListener("click", (event) => {
  if (event.target === event.currentTarget) {
    event.currentTarget.close();
  }
});

document.getElementById("quick-open-watch").addEventListener("click", () => openLane("watch", "Opened the watch lane."));
document
  .getElementById("quick-open-library")
  .addEventListener("click", () => openLane("library", "Opened the bench and files lane."));
document
  .getElementById("quick-open-workflows")
  .addEventListener("click", () => openLane("draft", "Opened the workflows lane."));
document.getElementById("quick-run-lone-planner").addEventListener("click", () => {
  openLane("draft");
  runLonePlannerMode();
});
document
  .getElementById("watch-open-workspace")
  .addEventListener("click", () => openLane("configure", "Opened workspace setup from the watch lane."));
document
  .getElementById("library-open-workspace")
  .addEventListener("click", () => openLane("configure", "Opened workspace setup from the bench and files lane."));
document
  .getElementById("handoff-stale-go-workspace")
  .addEventListener("click", () => openLane("configure", "Reopen workspace to refresh the stale handoff."));
document
  .getElementById("draft-open-planning-cell")
  .addEventListener("click", () => launchThinStaffWorkflow("planning-cell"));
document
  .getElementById("draft-open-brief-clinic")
  .addEventListener("click", () => launchWalkInWorkflow("brief-clinic"));
// Start Here cards: Lone Planner and Staff Package open a dialog (instant results,
// no form input needed). Planning Cell and Brief Clinic open their lane drawers.
document.getElementById("workflow-open-lone-planner").addEventListener("click", () => {
  if (state.workspace) {
    primeThinStaffForms();
    runWorkflowInDialog("Lone Planner Mode", async (outputEl) => {
      const payload = buildPlanningCellPayloadFromForm();
      const data = await apiFetch("/staff/lone-planner", { method: "POST", body: JSON.stringify(payload) });
      renderLonePlannerOutput(outputEl.id, data);
    });
  } else {
    setWorkspaceNote("Load a workspace first so Lone Planner can use your current context.", true);
  }
});
document.getElementById("workflow-open-planning-cell").addEventListener("click", () => {
  openToolDrawer("drawer-planning-cell");
  setWorkspaceNote("Planning cell is open in the Workflows lane.");
});
document.getElementById("workflow-run-staff-package").addEventListener("click", () => {
  if (state.workspace) {
    runWorkflowInDialog("Integrated Staff Package", async (outputEl) => {
      const data = await runStaffPlanningPackageAndReturn();
      renderToolOutput(outputEl.id, data, ["planning_posture", "command_decisions", "section_outputs", "staff_products", "warnings"]);
    });
  } else {
    setWorkspaceNote("Load a workspace first to build a staff package.", true);
  }
});
document.getElementById("workflow-open-brief-clinic").addEventListener("click", () => {
  openToolDrawer("drawer-brief-clinic");
  setWorkspaceNote("Brief Clinic is open in the Workflows lane.");
});
document
  .getElementById("battle-rhythm-open-editor")
  .addEventListener("click", () => openBattleRhythmEditor());
document
  .getElementById("battle-rhythm-open-planning-cell")
  .addEventListener("click", () => launchThinStaffWorkflow("planning-cell"));

document.addEventListener("click", async (event) => {
  const documentButton = event.target.closest("[data-document-id]");
  if (documentButton) {
    state.selectedDocumentId = documentButton.dataset.documentId;
    renderDocumentLibrary(state.workspace?.document_details || []);
    return;
  }

  const sectionMemoryEditButton = event.target.closest("[data-section-memory-edit]");
  if (sectionMemoryEditButton) {
    editSectionMemoryEntry(sectionMemoryEditButton.dataset.sectionMemoryEdit);
    return;
  }

  const sectionMemoryDeleteButton = event.target.closest("[data-section-memory-delete]");
  if (sectionMemoryDeleteButton) {
    await deleteSectionMemoryEntry(sectionMemoryDeleteButton.dataset.sectionMemoryDelete);
    return;
  }

  const sectionMemorySeedButton = event.target.closest("[data-section-memory-seed]");
  if (sectionMemorySeedButton) {
    seedSectionMemoryEntry(sectionMemorySeedButton.dataset.sectionMemorySeed);
    return;
  }

  const benchSectionRemoveButton = event.target.closest("[data-bench-section-remove]");
  if (benchSectionRemoveButton) {
    removeBenchSection(benchSectionRemoveButton.dataset.benchSectionRemove);
    return;
  }

  const mosBenchButton = event.target.closest("[data-mos-bench]");
  if (mosBenchButton) {
    openMosBenchLane(mosBenchButton.dataset.mosBench);
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
    await saveReadingProgress(saveButton.dataset.readingSave, saveButton);
  }

  const timezoneToggle = event.target.closest("[data-timezone-option]");
  if (timezoneToggle) {
    updateTimezoneSelection(timezoneToggle.dataset.timezoneOption, timezoneToggle.checked);
  }
});

async function loadWorkspace() {
  updateModeBanner();
  // UX5: show loading overlay so users know the fetch is in flight
  setLoading(true);
  setServerUnavailableVisible(false);
  setDemoUnavailableVisible(false);
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
      persistUserKey(userKey);
    }
    await loadBenchSections();
    await loadUserProfile();
    await loadHandoff();
    await loadBilletResearch();
    await loadTemplates();
    renderWorkspace(state.workspace);
    openDefaultPanels();
    setOnboardingVisible(false);
    updateFirstEmptyOrientation(isWorkspaceAllEmpty(state.workspace));
    setWorkspaceNote("Workspace refreshed.");
    if (state.mode === "personal" && isMessageFeedsEmpty(state.workspace)) {
      autoPreloadMessageFeeds();
    }
  } catch (error) {
    console.error("Failed to load workspace", error);
    if (error.isNetworkError) {
      setServerUnavailableVisible(true);
      setWorkspaceNote("Cannot reach local server — is the app running? Start it with: uvicorn app.main:app --reload", true);
    } else if (state.mode === "demo") {
      setDemoUnavailableVisible(true);
      setWorkspaceNote("Demo unavailable — try reloading.", true);
    } else {
      setWorkspaceNote(error.message, true);
    }
  } finally {
    setLoading(false);
  }
}

function setLoading(active) {
  const overlay = document.getElementById("dashboard-loading");
  if (overlay) {
    overlay.classList.toggle("is-hidden", !active);
  }
}

function setServerUnavailableVisible(visible) {
  document.getElementById("server-unavailable-banner")?.classList.toggle("is-hidden", !visible);
}

function setDemoUnavailableVisible(visible) {
  document.getElementById("demo-unavailable-banner")?.classList.toggle("is-hidden", !visible);
}

function setConnectionLostVisible(visible) {
  document.getElementById("connection-lost-banner")?.classList.toggle("is-hidden", !visible);
}

async function withButtonFeedback(button, loadingLabel, successMessage, action, options = {}) {
  const originalLabel = button?.textContent || "";
  const originalButtonDisabled = button?.disabled || false;
  const groupedButtons = getRefreshButtonGroup(options.disableButtonGroup);
  const groupedButtonStates = groupedButtons.map((groupButton) => ({
    button: groupButton,
    disabled: groupButton.disabled,
  }));
  if (button) {
    button.disabled = true;
    button.textContent = loadingLabel;
  }
  for (const groupButton of groupedButtons) {
    groupButton.disabled = true;
  }
  const initialStatusTarget =
    typeof options.statusTarget === "function" ? options.statusTarget() : options.statusTarget || button;
  clearPanelStatus(initialStatusTarget);
  try {
    const result = await action();
    const statusTarget =
      typeof options.statusTarget === "function" ? options.statusTarget() : options.statusTarget || button;
    setPanelStatus(statusTarget, successMessage);
    return result;
  } catch (error) {
    console.error(options.errorContext || "Dashboard action failed", error);
    const message = error instanceof Error ? error.message : String(error);
    const statusTarget =
      typeof options.statusTarget === "function" ? options.statusTarget() : options.statusTarget || button;
    setPanelStatus(statusTarget, message, true);
    setWorkspaceNote(message, true);
    return null;
  } finally {
    for (const { button: groupButton, disabled } of groupedButtonStates) {
      groupButton.disabled = disabled;
    }
    if (button) {
      button.disabled = originalButtonDisabled;
      button.textContent = originalLabel;
    }
  }
}

function setPanelStatus(anchor, message, critical = false) {
  const status = getPanelStatusElement(anchor);
  if (!status) {
    return;
  }
  status.textContent = message;
  status.className = critical ? "helper-text panel-feedback critical" : "helper-text panel-feedback";
}

function clearPanelStatus(anchor) {
  const status = getPanelStatusElement(anchor, false);
  if (status) {
    status.textContent = "";
    status.className = "helper-text panel-feedback";
  }
}

function getPanelStatusElement(anchor, create = true) {
  if (!anchor) {
    return null;
  }
  const container =
    anchor.closest("form") ||
    anchor.closest(".reading-item") ||
    anchor.closest(".panel-drawer-body") ||
    anchor.closest(".panel") ||
    anchor.parentElement;
  if (!container) {
    return null;
  }
  let status = container.querySelector(":scope > .panel-feedback");
  if (!status && create) {
    status = document.createElement("p");
    status.className = "helper-text panel-feedback";
    status.setAttribute("aria-live", "polite");
    const buttonRow = anchor.closest(".button-row");
    if (buttonRow && buttonRow.parentElement === container) {
      buttonRow.insertAdjacentElement("afterend", status);
    } else {
      container.append(status);
    }
  }
  return status;
}

function getRefreshButtonGroup(groupName) {
  return (REFRESH_BUTTON_GROUPS[groupName] || [])
    .map((id) => document.getElementById(id))
    .filter(Boolean);
}

function initializeDrawerLabels() {
  for (const details of document.querySelectorAll("details")) {
    updateDrawerLabels(details);
    details.addEventListener("toggle", () => updateDrawerLabels(details));
  }
}

function updateDrawerLabels(details) {
  const label = details.open ? "Close" : "Open";
  const summary = details.querySelector(":scope > summary");
  for (const element of summary?.querySelectorAll(".drawer-label") || []) {
    element.textContent = label;
  }
}

function markLastUpdated(keys) {
  const now = new Date();
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(state.lastUpdatedAt, key)) {
      state.lastUpdatedAt[key] = now;
    }
  }
  renderLastUpdatedStamps();
}

function renderLastUpdatedStamps() {
  const targets = {
    maradmins: "maradmin-last-updated",
    reading: "reading-last-updated",
    sourceWatch: "source-watch-last-updated",
  };
  for (const [key, targetId] of Object.entries(targets)) {
    const target = document.getElementById(targetId);
    if (!target) {
      continue;
    }
    const timestamp = state.lastUpdatedAt[key];
    target.textContent = timestamp ? `Last updated: ${formatElapsedMinutes(timestamp)} ago` : "";
    target.classList.toggle("is-hidden", !timestamp);
  }
}

function formatElapsedMinutes(timestamp) {
  const elapsedMs = Math.max(0, Date.now() - timestamp.getTime());
  const elapsedMinutes = Math.floor(elapsedMs / 60000);
  return elapsedMinutes <= 0 ? "just now" : `${elapsedMinutes} min`;
}

// ------------------------------------------------------------------
// Onboarding: auto-UUID profile key + localStorage persistence
// ------------------------------------------------------------------

const SAVED_KEY_STORAGE = "smcr_user_key";

function generateProfileKey() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);
}

function initOnboardingState() {
  let saved = localStorage.getItem(SAVED_KEY_STORAGE);
  const isFirstVisit = !saved;

  if (isFirstVisit) {
    saved = generateProfileKey();
    localStorage.setItem(SAVED_KEY_STORAGE, saved);
  }

  // Sync the hidden input so loadWorkspace() picks it up
  const keyInput = document.getElementById("user-key");
  if (keyInput) { keyInput.value = saved; }

  // Auto-use personal mode — no button click required
  state.mode = "personal";
  state.userKey = saved;

  // Profile ID display in advanced settings
  const idDisplay = document.getElementById("profile-id-display");
  if (idDisplay) { idDisplay.textContent = saved; }

  if (!isFirstVisit) {
    // Show welcome-back with truncated ID (friendly label)
    const label = saved.length > 20 ? saved.slice(0, 8) + "…" : saved;
    const display = document.getElementById("onboarding-profile-display");
    if (display) { display.textContent = label; }
    document.getElementById("onboarding-first-run")?.classList.add("is-hidden");
    document.getElementById("onboarding-welcome-back")?.classList.remove("is-hidden");
  }
}

function isValidProfileName(name) {
  return name.length > 0 && name.length <= 60 && !/[/\\<>]/.test(name);
}

// Used when manually switching profiles from the onboarding recovery panel
function onboardingCreateWorkspace() {
  const input = document.getElementById("onboarding-key-input");
  const errorEl = document.getElementById("onboarding-key-error");
  const name = (input?.value || "").trim();

  if (!isValidProfileName(name)) {
    if (errorEl) {
      errorEl.textContent = name.length === 0
        ? "Enter a profile name or ID to switch."
        : "Profile name cannot contain / \\ or < >. Keep it short and memorable.";
    }
    input?.focus();
    return;
  }
  if (errorEl) { errorEl.textContent = ""; }

  localStorage.setItem(SAVED_KEY_STORAGE, name);
  document.getElementById("user-key").value = name;
  state.mode = "personal";
  state.userKey = name;
  state.apiKey = document.getElementById("api-key").value.trim();

  const idDisplay = document.getElementById("profile-id-display");
  if (idDisplay) { idDisplay.textContent = name; }

  loadWorkspace();
}

function persistUserKey(key) {
  if (key) { localStorage.setItem(SAVED_KEY_STORAGE, key); }
}

// ------------------------------------------------------------------

// UX4: show onboarding panel when no workspace is loaded, hide it once loaded
function setOnboardingVisible(visible) {
  const panel = document.getElementById("workspace-onboarding");
  if (panel) {
    panel.classList.toggle("is-hidden", !visible);
  }
}

// UX3: open the most operationally relevant panels by default after a workspace load.
// Act Now is now at the top of Overview so no extra scroll is needed to see it.
// Daily Brief auto-opens in Watch lane; Command Snapshots auto-opens for the counts.
function openDefaultPanels() {
  const dailyBrief = document.getElementById("daily-brief-drawer");
  if (dailyBrief) {
    dailyBrief.open = true;
  }
  // Open Command Snapshots so chief/admin/career counts are immediately visible
  const snapshots = document.querySelector(".collapsible-panel.full-span details.panel-drawer");
  if (snapshots && state.workspace) {
    snapshots.open = true;
  }
}

function renderWorkspace(payload) {
  renderWorkspaceSummary(payload.summary_lines || [], payload.warnings || []);
  renderChief(payload.chief_brief);
  renderNextDrillReadiness(payload.chief_brief?.next_drill_readiness || {});
  renderThinStaffAssist(payload.chief_brief?.thin_staff_assist || {});
  renderWalkInBriefPack(payload.chief_brief?.walk_in_brief_pack || {});
  renderBattleRhythmHealth(payload.chief_brief?.battle_rhythm_health || {});
  renderBattleRhythm(payload.battle_rhythm || payload.chief_brief?.battle_rhythm || null);
  renderCareer(payload.career_watch);
  renderAdmin(payload.admin_readiness);
  renderDailyBrief(payload.daily_ops_brief || {});
  renderAnalystBrief(payload.analyst_brief || {});
  renderDocumentsWatch(payload.document_summary || payload.chief_brief?.document_summary || { records: [] });
  renderDocumentLibrary(payload.document_details || []);
  renderTemplateLibrary(payload.template_library || []);
  renderMosBenchLibrary();
  renderSectionMemoryProfile(payload.section_memory_profile || null);
  renderMaradminTicker(payload.maradmin_ticker || []);
  renderTickerStack("navadmin-ticker", payload.navadmin_ticker || [], "No NAVADMINs tracked.");
  renderTickerStack("alnav-ticker", payload.alnav_ticker || [], "No ALNAVs tracked.");
  renderTickerStack("dod-ticker", payload.dod_ticker || [], "No DoD updates tracked.");
  renderCustomWatchFeeds(payload.custom_watch_feeds || []);
  renderHistory(payload.today_in_history || []);
  renderReferenceLibrary(payload.reference_library || []);
  renderReadingBooks(payload.reading_books || []);
  renderTrackedActions(payload.tracked_actions || []);
  renderOpportunities(payload.tracked_opportunities || payload.career_watch?.tracked_opportunities || []);
  renderSourceUpdates(payload.documentation_updates || payload.chief_brief?.documentation_updates || []);
  loadQuickLinks();
  loadGoodLinks();
  renderLastUpdatedStamps();
}

function renderWorkspaceSummary(summaryLines, warnings) {
  const placeholder = document.getElementById("command-preload-placeholder");
  const summary = document.getElementById("workspace-summary");
  const warningList = document.getElementById("workspace-warnings");
  placeholder?.classList.toggle("is-hidden", true);
  summary?.classList.toggle("is-hidden", false);
  warningList?.classList.toggle("is-hidden", false);
  renderList("workspace-summary", summaryLines);
  renderList("workspace-warnings", warnings.slice(0, 4));
}

function updateFirstEmptyOrientation(show) {
  const visible = show && !state.firstEmptyOrientationDismissed;
  const card = document.getElementById("first-empty-orientation");
  const main = document.getElementById("dashboard-main");
  card?.classList.toggle("is-hidden", !visible);
  main?.classList.toggle("all-empty-workspace", visible);
}

function isWorkspaceAllEmpty(payload) {
  const chief = payload?.chief_brief || {};
  const actionItems = [
    ...(chief.top_priority_items || []),
    ...(chief.action_items || []),
    ...(payload?.tracked_actions || []),
  ];
  const sourceWatchItems = [
    ...(payload?.maradmin_ticker || []),
    ...(payload?.navadmin_ticker || []),
    ...(payload?.alnav_ticker || []),
    ...(payload?.dod_ticker || []),
    ...(payload?.custom_watch_feeds || []),
    ...(payload?.documentation_updates || []),
    ...(chief.documentation_updates || []),
  ];
  const sectionMemoryEntries = payload?.section_memory_profile?.entries || [];
  return (
    actionItems.length === 0 &&
    sourceWatchItems.length === 0 &&
    sectionMemoryEntries.length === 0 &&
    !chief.handoff
  );
}

function renderChief(payload) {
  document.getElementById("chief-count").textContent = String((payload.top_priority_items || []).length);
  renderList("chief-summary", payload.summary_lines || []);
  const items = payload.top_priority_items || payload.action_items || [];
  renderQueue(items, payload.battle_rhythm_health?.hot_items || []);
}

function renderNextDrillReadiness(payload) {
  // Surface handoff staleness visually — it's buried in brief text without this
  const staleBanner = document.getElementById("handoff-stale-banner");
  if (staleBanner) {
    const isStale = state.workspace?.chief_brief?.handoff_is_stale === true;
    staleBanner.classList.toggle("is-hidden", !isStale);
  }

  document.getElementById("readiness-posture").textContent =
    payload.readiness_posture || "No posture assessed.";
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

function renderThinStaffAssist(payload) {
  renderList("thin-staff-walk-in", payload.walk_in_brief || []);
  renderList("thin-staff-blind-spots", payload.likely_blind_spots || []);
  renderList("thin-staff-questions", payload.missing_section_questions || []);
  renderList("thin-staff-products", payload.recommended_products || []);
  renderList("thin-staff-changes", payload.changes_since_last_time || []);
  renderEntryRows(
    "thin-staff-next-touchpoint",
    payload.next_touchpoint ? [{ title: payload.next_touchpoint, category: "touchpoint" }] : [],
    "No next touchpoint logged.",
  );
}

function renderWalkInBriefPack(payload) {
  renderList("walk-in-current-state", payload.current_state || []);
  renderList("walk-in-delta-drill", payload.delta_since_last_drill || []);
  renderList("walk-in-delta-touch", payload.delta_since_last_touchpoint || []);
  renderList("walk-in-open-decisions", payload.open_decisions || []);
  renderList("walk-in-stale-assumptions", payload.stale_assumptions || []);
  renderList("walk-in-source-hits", payload.source_watch_hits || []);
  renderList("walk-in-before", payload.before_you_walk_in || []);
}

function renderBattleRhythmHealth(payload) {
  const posture = document.getElementById("battle-rhythm-health-posture");
  if (posture) {
    const status = payload.board_status || "uninitialized";
    const age = Number.isInteger(payload.board_age_days) ? `${payload.board_age_days} day(s) old` : "not started";
    const recommendation = payload.refresh_recommendation || "No refresh recommendation yet.";
    posture.textContent = `Continuity watch: ${status}. Board age: ${age}. ${recommendation}`;
  }
  renderList("battle-rhythm-health-summary", payload.summary || []);
  renderList("battle-rhythm-hot-items", payload.hot_items || []);
}

function renderBattleRhythm(payload) {
  populateBattleRhythmForm(payload);
  renderList("battle-rhythm-focus", payload?.focus || []);
  renderEntryRows(
    "battle-rhythm-touchpoint",
    payload?.next_touchpoint ? [{ title: payload.next_touchpoint, category: "touchpoint" }] : [],
    "No next touchpoint stored yet.",
  );
  renderBattleRhythmEntries(
    "battle-rhythm-assumptions",
    payload?.assumption_log || [],
    "No assumptions stored yet.",
  );
  renderBattleRhythmEntries(
    "battle-rhythm-decisions",
    payload?.commander_decision_log || [],
    "No decision items stored yet.",
  );
  renderBattleRhythmEntries(
    "battle-rhythm-questions",
    payload?.question_log || [],
    "No question log stored yet.",
  );
  renderBattleRhythmEntries(
    "battle-rhythm-dueouts",
    payload?.due_out_board || [],
    "No due-outs stored yet.",
  );
}

function renderBattleRhythmEntries(targetId, items, emptyMessage) {
  const target = document.getElementById(targetId);
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = emptyMessage;
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row compact-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.section || "staff")}</span>
            <strong>${escapeHtml(item.text)}</strong>
            <span class="meta-inline">${escapeHtml(item.status || "open")}</span>
          </div>
          <p class="meta-inline">${escapeHtml(formatBattleRhythmMeta(item))}</p>
        </article>
      `,
    )
    .join("");
}

function formatBattleRhythmMeta(item) {
  const parts = [];
  if (item.owner) {
    parts.push(`Owner: ${item.owner}`);
  }
  if (item.suspense_date) {
    parts.push(`Suspense: ${item.suspense_date}`);
  }
  if (item.source) {
    parts.push(`Source: ${item.source}`);
  }
  return parts.join(" | ") || "Open continuity item.";
}

function populateBattleRhythmForm(payload) {
  const form = document.getElementById("battle-rhythm-form");
  if (!form) {
    return;
  }
  const chiefBrief = state.workspace?.chief_brief || {};
  const activeContext = chiefBrief.active_user_context || {};
  const supportedUnit =
    activeContext.unit_name || activeContext.unit_type || activeContext.unit_family || "SMCR unit";
  form.elements.board_title.value =
    payload?.board_title || `Battle rhythm board for ${supportedUnit}`;
  form.elements.next_touchpoint.value = payload?.next_touchpoint || chiefBrief.thin_staff_assist?.next_touchpoint || "";
  form.elements.focus.value = (payload?.focus || []).join("\n");
  form.elements.assumption_log.value = battleRhythmLines(payload?.assumption_log || []);
  form.elements.commander_decision_log.value = battleRhythmLines(payload?.commander_decision_log || []);
  form.elements.question_log.value = battleRhythmLines(payload?.question_log || []);
  form.elements.due_out_board.value = battleRhythmLines(payload?.due_out_board || []);
}

function battleRhythmLines(items) {
  return items
    .map((item) => (item.section ? `${item.section}: ${item.text}` : item.text))
    .join("\n");
}

// Open a tool drawer in the Workflows lane without forcing a scroll jump.
// Switches to the draft lane, expands the target drawer, and lets the user
// scroll at their own pace.
function openToolDrawer(drawerId) {
  openLane("draft");
  const drawer = document.getElementById(drawerId);
  if (drawer) {
    drawer.open = true;
  }
}

async function launchThinStaffWorkflow(mode) {
  if (!state.workspace) {
    setWorkspaceNote("Load a workspace first so the launch can use current context.", true);
    return;
  }

  if (mode === "admin") {
    openLane("overview", "Jumped to admin readiness.");
    return;
  }

  primeThinStaffForms();

  if (mode === "lone-planner") {
    // Lone Planner runs instantly from context — show results in a dialog
    await runWorkflowInDialog("Lone Planner Mode", async (outputEl) => {
      const payload = buildPlanningCellPayloadFromForm();
      const data = await apiFetch("/staff/lone-planner", { method: "POST", body: JSON.stringify(payload) });
      renderLonePlannerOutput(outputEl.id, data);
    });
    return;
  }

  if (mode === "planning-cell") {
    openToolDrawer("drawer-planning-cell");
    setWorkspaceNote("Planning cell is ready in the Workflows lane.");
    return;
  }

  if (mode === "update-cycle") {
    openToolDrawer("drawer-staff-cycle");
    setWorkspaceNote("Staff update cycle is ready in the Workflows lane.");
    return;
  }

  if (mode === "mission-analysis") {
    await runWorkflowInDialog("Mission Analysis", async (outputEl) => {
      const payload = buildPlanningCellPayloadFromForm();
      const data = await apiFetch("/staff/mission-analysis", { method: "POST", body: JSON.stringify(payload) });
      renderMissionAnalysisOutput(outputEl.id, data);
    });
  }
}

function launchWalkInWorkflow(mode) {
  if (mode === "brief-clinic") {
    openToolDrawer("drawer-brief-clinic");
    setWorkspaceNote("Brief Clinic is ready in the Workflows lane.");
    return;
  }
  // Lone planner from walk-in pack
  if (state.workspace) {
    primeThinStaffForms();
    runWorkflowInDialog("Lone Planner Mode", async (outputEl) => {
      const payload = buildPlanningCellPayloadFromForm();
      const data = await apiFetch("/staff/lone-planner", { method: "POST", body: JSON.stringify(payload) });
      renderLonePlannerOutput(outputEl.id, data);
    });
  } else {
    openToolDrawer("drawer-planning-cell");
    setWorkspaceNote("Open your workspace first, then run lone planner mode.");
  }
}

function openBattleRhythmEditor() {
  openToolDrawer("drawer-battle-rhythm");
  setWorkspaceNote("Battle Rhythm Editor is open in the Workflows lane.");
}

// Workflow dialog — shows quick-launch tool output in a floating panel
// without pulling the user away from their current lane.
async function runWorkflowInDialog(title, runFn) {
  const dialog = document.getElementById("workflow-dialog");
  const titleEl = document.getElementById("workflow-dialog-title");
  const body = document.getElementById("workflow-dialog-body");
  if (!dialog || !body) return;

  titleEl.textContent = title;
  body.innerHTML = `
    <div id="workflow-dialog-output" class="tool-output empty-state" aria-live="polite">
      Running ${escapeHtml(title)}…
    </div>
  `;
  dialog.showModal();

  try {
    const outputEl = document.getElementById("workflow-dialog-output");
    outputEl.className = "tool-output";
    await runFn(outputEl);
  } catch (error) {
    console.error("Workflow dialog action failed", error);
    const outputEl = document.getElementById("workflow-dialog-output");
    if (outputEl) {
      outputEl.textContent = `Error: ${error.message}`;
      outputEl.className = "tool-output critical";
    }
  }
}

// Render lone-planner output into a target element (dialog or lane)
function renderLonePlannerOutput(targetId, data) {
  const target = document.getElementById(targetId);
  if (target) {
    renderToolOutput(targetId, data, ["walk_in_brief", "blind_spots", "missing_section_questions", "recommended_products", "immediate_actions"]);
  }
}

function primeThinStaffForms() {
  const chiefBrief = state.workspace?.chief_brief || {};
  const thinStaff = chiefBrief.thin_staff_assist || {};
  const activeContext = chiefBrief.active_user_context || {};
  const handoff = chiefBrief.handoff || {};
  const supportedUnit =
    activeContext.unit_name || activeContext.unit_type || activeContext.unit_family || "SMCR unit";
  const missionGoal =
    thinStaff.walk_in_brief?.[0] ||
    state.workspace?.summary_lines?.[0] ||
    "Refine the next drill concept and keep the staff synchronized on what matters.";
  const priorities = chiefBrief.next_drill_readiness?.this_week_focus || [];
  const blindSpots = thinStaff.likely_blind_spots || [];
  const questions = thinStaff.missing_section_questions || [];

  const planningForm = document.getElementById("planning-cell-form");
  if (planningForm) {
    planningForm.elements.title.value = `Thin-staff planning cell for ${supportedUnit}`;
    planningForm.elements.supported_unit.value = supportedUnit;
    planningForm.elements.mission_or_training_goal.value = missionGoal;
    planningForm.elements.commander_priorities.value = priorities.join("\n");
    planningForm.elements.higher_guidance.value = blindSpots.join("\n");
    planningForm.elements.coordinating_sections.value = "S-3\nS-4\nS-6\nS-1/Admin";
    planningForm.elements.support_requirements.value = questions.join("\n");
    planningForm.elements.section_updates.value = buildSectionUpdateSeed(questions, blindSpots);
    planningForm.elements.time_available.value =
      chiefBrief.next_drill_readiness?.anchor_drill_date
        ? `Before drill anchor ${chiefBrief.next_drill_readiness.anchor_drill_date}`
        : "Before next staff sync";
  }

  const updateCycleForm = document.getElementById("staff-cycle-form");
  if (updateCycleForm) {
    updateCycleForm.elements.title.value = `Thin-staff update cycle for ${supportedUnit}`;
    updateCycleForm.elements.supported_unit.value = supportedUnit;
    updateCycleForm.elements.mission_or_training_goal.value = missionGoal;
    updateCycleForm.elements.commander_priorities.value = priorities.join("\n");
    updateCycleForm.elements.section_updates.value =
      buildSectionUpdateSeed(questions, blindSpots) ||
      (handoff.admin_watch_items || []).slice(0, 3).map((item) => `S-1/Admin: ${item}`).join("\n");
  }
}

function buildPlanningCellPayloadFromForm() {
  const form = new FormData(document.getElementById("planning-cell-form"));
  // BUG1 fix: constraints now read from its own field, not duplicated from higher_guidance
  // BUG2 fix: civil_considerations now read from its own field, not duplicated from support_requirements
  // UX6 fix: supported_echelon now read from the form select, not hard-coded to "company"
  return {
    user_key: state.mode === "personal" && state.userKey ? state.userKey : null,
    title: form.get("title"),
    supported_unit: form.get("supported_unit"),
    supported_echelon: form.get("supported_echelon") || "company",
    event_type: form.get("event_type") || "training_event",
    mission_or_training_goal: form.get("mission_or_training_goal"),
    time_available: form.get("time_available") || null,
    commander_priorities: splitLines(form.get("commander_priorities")),
    higher_guidance: splitLines(form.get("higher_guidance")),
    constraints: splitLines(form.get("constraints")),
    coordinating_sections: splitLines(form.get("coordinating_sections")),
    support_requirements: splitLines(form.get("support_requirements")),
    civil_considerations: splitLines(form.get("civil_considerations")),
    focus_sections: splitLines(form.get("focus_sections")),
    section_updates: parseSectionUpdates(form.get("section_updates")),
    training_only: true,
  };
}

function buildSectionUpdateSeed(questions, blindSpots) {
  const s3 = questions[0] || "What is the real training output or commander decision?";
  const s4 = blindSpots[0] || "Support assumptions still need to be checked honestly.";
  const s6 = questions[2] || "Reporting and access friction still need to be clarified.";
  return [`S-3: ${s3}`, `S-4: ${s4}`, `S-6: ${s6}`].join("\n");
}

function buildBattleRhythmPayloadFromForm() {
  const form = new FormData(document.getElementById("battle-rhythm-form"));
  return {
    board_title: String(form.get("board_title") || "").trim() || "Battle rhythm board",
    source_title: "dashboard_manual_edit",
    focus: splitLines(form.get("focus")),
    assumption_log: parseBattleRhythmEntries(form.get("assumption_log"), "dashboard_manual_edit"),
    commander_decision_log: parseBattleRhythmEntries(
      form.get("commander_decision_log"),
      "dashboard_manual_edit",
      "pending",
    ),
    question_log: parseBattleRhythmEntries(form.get("question_log"), "dashboard_manual_edit"),
    due_out_board: parseBattleRhythmEntries(form.get("due_out_board"), "dashboard_manual_edit"),
    next_touchpoint: String(form.get("next_touchpoint") || "").trim() || null,
    context_note: "Updated from the dashboard battle-rhythm board editor.",
  };
}

function parseBattleRhythmEntries(value, source, status = "open") {
  return splitLines(value).map((line) => {
    const index = line.indexOf(":");
    if (index > 0) {
      const section = line.slice(0, index).trim();
      const text = line.slice(index + 1).trim();
      return {
        text: text || line.trim(),
        section: section || null,
        status,
        source,
      };
    }
    return {
      text: line.trim(),
      section: null,
      status,
      source,
    };
  });
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
  const summary = document.getElementById("document-library-summary");
  const selector = document.getElementById("document-select");
  const typeSelect = document.getElementById("document-type-select");
  const typeButton = document.getElementById("save-document-type");
  const suggestionButton = document.getElementById("apply-document-suggestion");
  const suggestionNote = document.getElementById("document-type-suggestion");
  if (!items.length) {
    target.className = "document-library empty-state";
    if (summary) {
      summary.textContent = state.workspace ? "No documents uploaded." : PRELOAD_EMPTY_TEXT;
    }
    if (selector) {
      selector.innerHTML = `<option value="">${state.workspace ? "No documents uploaded." : PRELOAD_EMPTY_TEXT}</option>`;
      selector.disabled = true;
    }
    if (typeSelect) {
      typeSelect.value = "reference_note";
      typeSelect.disabled = true;
    }
    if (typeButton) {
      typeButton.disabled = true;
    }
    if (suggestionButton) {
      suggestionButton.disabled = true;
    }
    if (suggestionNote) {
      suggestionNote.textContent = "No category suggestion yet.";
    }
    target.innerHTML = state.workspace
      ? emptyStateHtml("No documents in this workspace.", "Orders, BIO data, receipts, and other personal references appear here after upload.")
      : `<p class="empty-state-detail">${PRELOAD_EMPTY_TEXT}</p>`;
    return;
  }
  if (!state.selectedDocumentId || !items.some((item) => item.context_id === state.selectedDocumentId)) {
    state.selectedDocumentId = items[0].context_id;
  }
  const selected = items.find((item) => item.context_id === state.selectedDocumentId) || items[0];
  if (summary) {
    summary.textContent = `${items.length} local file(s) loaded. Showing ${selected.filename}.`;
  }
  if (selector) {
    selector.disabled = false;
    selector.innerHTML = items
      .map(
        (item) =>
          `<option value="${escapeHtml(item.context_id)}" ${item.context_id === state.selectedDocumentId ? "selected" : ""}>${escapeHtml(item.filename)}</option>`,
      )
      .join("");
  }
  if (typeSelect) {
    typeSelect.disabled = false;
    typeSelect.value = DOCUMENT_TYPE_OPTIONS.includes(selected.document_type) ? selected.document_type : "other";
  }
  if (typeButton) {
    typeButton.disabled = state.mode !== "personal";
  }
  const hasSuggestion =
    !!selected.suggested_document_type && selected.suggested_document_type !== selected.document_type;
  if (suggestionButton) {
    suggestionButton.disabled = state.mode !== "personal" || !hasSuggestion;
  }
  if (suggestionNote) {
    suggestionNote.textContent = hasSuggestion
      ? `Suggested: ${selected.suggested_document_type} — ${selected.suggestion_reason || "Based on filename and preview text."}`
      : "No better category suggestion for the selected file.";
  }
  target.className = "document-library";
  target.innerHTML = `
    <div class="document-preview document-preview-full">
      <div class="preview-meta">
        <span class="strip-label">${escapeHtml(selected.document_type)}</span>
        <h3>${escapeHtml(selected.filename)}</h3>
        <p>${escapeHtml(formatDocumentMeta(selected))}</p>
      </div>
      <pre>${escapeHtml(selected.text_preview || "No preview available.")}</pre>
    </div>
  `;
}

async function saveSelectedDocumentType() {
  if (state.mode !== "personal" || !state.selectedDocumentId) {
    setWorkspaceNote("Open your personal workspace to reclassify local files.", true);
    return;
  }
  const typeSelect = document.getElementById("document-type-select");
  const documentType = typeSelect?.value || "";
  if (!DOCUMENT_TYPE_OPTIONS.includes(documentType)) {
    setWorkspaceNote("Choose a valid file category first.", true);
    return;
  }
  try {
    const data = await apiFetch(`/personal-documents/${encodeURIComponent(state.selectedDocumentId)}/type`, {
      method: "PATCH",
      auth: true,
      body: JSON.stringify({ document_type: documentType }),
    });
    // ARCH4: patch local state in-place instead of re-fetching all 14 services
    if (state.workspace?.document_details) {
      state.workspace.document_details = state.workspace.document_details.map((item) =>
        item.context_id === state.selectedDocumentId ? { ...item, document_type: data.record.document_type } : item,
      );
    }
    if (state.workspace?.document_summary?.records) {
      state.workspace.document_summary.records = state.workspace.document_summary.records.map((item) =>
        item.context_id === state.selectedDocumentId ? { ...item, document_type: data.record.document_type } : item,
      );
    }
    renderDocumentLibrary(state.workspace?.document_details || []);
    setWorkspaceNote(data.message || "File category updated.");
  } catch (error) {
    console.error("Failed to save file category", error);
    setWorkspaceNote(error.message, true);
  }
}

function applySuggestedDocumentType() {
  const selected = (state.workspace?.document_details || []).find((item) => item.context_id === state.selectedDocumentId);
  if (!selected?.suggested_document_type) {
    setWorkspaceNote("No category suggestion is available for this file.", true);
    return;
  }
  const typeSelect = document.getElementById("document-type-select");
  if (typeSelect) {
    typeSelect.value = selected.suggested_document_type;
  }
  setWorkspaceNote(`Loaded suggested category: ${selected.suggested_document_type}. Save to apply it.`);
}

function renderTemplateLibrary(items) {
  const target = document.getElementById("template-library");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.innerHTML = state.workspace
      ? emptyStateHtml("No templates saved.", "Brief formats, heading structures, and reusable examples appear here after saving from the form above.")
      : `<p class="empty-state-detail">${PRELOAD_EMPTY_TEXT}</p>`;
    return;
  }
  target.className = "row-stack";
  target.innerHTML = items
    .map(
      (item) => `
        <article class="data-row" data-template-id="${escapeHtml(item.template_id)}">
          <div class="data-row-head">
            <strong>${escapeHtml(item.template_name)}</strong>
            <span class="meta-inline">${escapeHtml(item.template_type)}</span>
          </div>
          <p>${escapeHtml(item.description || item.example_excerpt?.slice(0, 120) || "Reusable structure and tone reference.")}</p>
          <p class="meta-inline">${escapeHtml((item.reusable_headings || []).slice(0, 4).join(" · ") || "")}</p>
          <div class="button-row compact-controls">
            <button class="secondary small delete-template-btn" data-template-id="${escapeHtml(item.template_id)}">Delete</button>
          </div>
        </article>
      `,
    )
    .join("");
  for (const btn of target.querySelectorAll(".delete-template-btn")) {
    btn.addEventListener("click", () => deleteTemplate(btn.dataset.templateId));
  }
}

async function loadTemplates() {
  if (!state.userKey || state.mode !== "personal") {
    return;
  }
  try {
    const response = await apiFetch("/product-templates", { auth: true });
    renderTemplateLibrary(response.records || []);
  } catch (error) {
    console.error("Failed to load templates", error);
  }
}

// ------------------------------------------------------------------
// Module Packs (Bench/Files lane)
// ------------------------------------------------------------------

// Lazy-load the pack list the first time the panel is opened.
document.getElementById("module-packs-panel")?.addEventListener("toggle", async (e) => {
  if (!e.target.open) { return; }
  const listEl = document.getElementById("module-pack-list");
  if (!listEl || listEl.dataset.loaded === "1") { return; }
  await loadModulePacks();
});

async function loadModulePacks() {
  const listEl = document.getElementById("module-pack-list");
  if (!listEl) { return; }
  try {
    const packs = await apiFetch("/modules", { auth: true });
    listEl.dataset.loaded = "1";
    renderModulePackList(packs || []);
  } catch (err) {
    listEl.className = "row-stack empty-state";
    listEl.textContent = err.isNetworkError
      ? "Server not reachable — start the app first."
      : "Could not load module packs.";
  }
}

function renderModulePackList(packs) {
  const listEl = document.getElementById("module-pack-list");
  if (!listEl) { return; }
  if (!packs.length) {
    listEl.className = "row-stack";
    listEl.innerHTML = emptyStateHtml("No module packs found.", "Add a sub-folder to the modules/ directory in the repo to create a pack.");
    return;
  }
  listEl.className = "row-stack";
  listEl.innerHTML = packs.map((pack) => `
    <article class="data-row module-pack-row" data-pack="${escapeHtml(pack.pack_name)}">
      <div class="data-row-head">
        <strong>${escapeHtml(pack.manifest?.title || pack.pack_name)}</strong>
        <span class="meta-inline">${pack.supported_file_count} file${pack.supported_file_count !== 1 ? "s" : ""}</span>
      </div>
      ${pack.manifest?.description ? `<p>${escapeHtml(pack.manifest.description)}</p>` : ""}
      ${pack.manifest?.author ? `<p class="meta-inline">By ${escapeHtml(pack.manifest.author)}${pack.manifest.version ? " · v" + escapeHtml(pack.manifest.version) : ""}</p>` : ""}
      <div class="button-row compact-controls">
        <button class="secondary small module-activate-btn" data-pack="${escapeHtml(pack.pack_name)}">Activate</button>
      </div>
      <p class="module-pack-note helper-text" aria-live="polite"></p>
    </article>
  `).join("");

  for (const btn of listEl.querySelectorAll(".module-activate-btn")) {
    btn.addEventListener("click", () => activateModulePack(btn.dataset.pack, btn));
  }
}

async function activateModulePack(packName, button) {
  if (state.mode !== "personal" || !state.userKey) {
    const noteEl = button?.closest(".module-pack-row")?.querySelector(".module-pack-note");
    if (noteEl) { noteEl.textContent = "Open a personal workspace first."; }
    return;
  }
  const noteEl = button?.closest(".module-pack-row")?.querySelector(".module-pack-note");
  const originalLabel = button?.textContent;
  if (button) { button.disabled = true; button.textContent = "Activating…"; }
  if (noteEl) { noteEl.textContent = ""; }
  try {
    const result = await apiFetch(`/modules/${encodeURIComponent(packName)}/ingest`, {
      method: "POST",
      auth: true,
    });
    if (noteEl) { noteEl.textContent = result.message || "Activated."; }
    if (button) { button.textContent = "Activated ✓"; }

    // If the pack ships a smcr-profile.json, offer to apply the profile defaults
    if (result.profile_seed && state.userKey) {
      const seed = result.profile_seed;
      const fields = Object.entries(seed).filter(([, v]) => v).map(([k]) => k).join(", ");
      if (fields && confirm(`This pack includes profile defaults (${fields}). Apply them to your profile?`)) {
        await applyProfileSeed(seed);
        if (noteEl) { noteEl.textContent += " Profile defaults applied."; }
      }
    }
  } catch (err) {
    if (noteEl) { noteEl.textContent = err.message || "Activation failed."; }
    if (button) { button.textContent = originalLabel; button.disabled = false; }
  }
}

async function applyProfileSeed(seed) {
  if (!state.userKey) { return; }
  // Load current profile to merge (don't overwrite fields the user already set)
  let current = {};
  try {
    current = await apiFetch(`/user-profile/${encodeURIComponent(state.userKey)}`, { auth: true });
  } catch (_) { /* 404 = no profile yet, that's fine */ }
  const merged = {
    billet: current.billet || seed.billet || "",
    unit: current.unit || seed.unit || "",
    mos: current.mos || seed.mos || "",
    format_preference: current.format_preference || seed.format_preference || "bullet",
    style_notes: current.style_notes || seed.style_notes || "",
  };
  await apiFetch(`/user-profile/${encodeURIComponent(state.userKey)}`, {
    method: "PUT",
    auth: true,
    body: JSON.stringify(merged),
  });
}

// Git pull — refresh module packs from remote
document.getElementById("git-pull-modules")?.addEventListener("click", async (e) => {
  await withButtonFeedback(e.currentTarget, "Pulling…", async () => {
    const noteEl = document.getElementById("git-pull-note");
    if (noteEl) { noteEl.style.display = ""; noteEl.textContent = "Running git pull…"; }
    try {
      const result = await apiFetch("/git/pull", { method: "POST", auth: true });
      if (noteEl) {
        noteEl.textContent = result.message + (result.stdout ? ` (${result.stdout})` : "");
      }
      if (result.success) {
        // Reload pack list so newly pulled packs appear
        const listEl = document.getElementById("module-pack-list");
        if (listEl) { delete listEl.dataset.loaded; }
        await loadModulePacks();
      }
    } catch (err) {
      if (noteEl) { noteEl.textContent = err.message || "git pull failed."; }
    }
  });
});

// ------------------------------------------------------------------

async function saveTemplate() {
  const nameInput = document.getElementById("template-name-input");
  const typeSelect = document.getElementById("template-type-select");
  const contentInput = document.getElementById("template-content-input");
  const noteEl = document.getElementById("template-save-note");
  const name = nameInput?.value.trim();
  if (!name) {
    if (noteEl) noteEl.textContent = "Template name is required.";
    return;
  }
  const rawContent = contentInput?.value.trim() || "";
  const headings = rawContent
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0 && l.length < 120);
  const body = {
    template_name: name,
    template_type: typeSelect?.value || "other",
    reusable_headings: headings,
    example_excerpt: rawContent.slice(0, 2000) || null,
  };
  try {
    await apiFetch("/product-templates/manual", { method: "POST", auth: true, body: JSON.stringify(body) });
    if (nameInput) nameInput.value = "";
    if (contentInput) contentInput.value = "";
    if (noteEl) {
      noteEl.textContent = "Template saved.";
      setTimeout(() => { noteEl.textContent = ""; }, 3000);
    }
    const drawer = document.getElementById("add-template-drawer");
    if (drawer) drawer.open = false;
    await loadTemplates();
  } catch (error) {
    if (noteEl) noteEl.textContent = error.message || "Failed to save template.";
    console.error("Failed to save template", error);
  }
}

async function deleteTemplate(templateId) {
  if (!templateId) return;
  try {
    await apiFetch(`/product-templates/${encodeURIComponent(templateId)}`, { method: "DELETE", auth: true });
    await loadTemplates();
  } catch (error) {
    console.error("Failed to delete template", error);
  }
}

function renderMosBenchLibrary() {
  const target = document.getElementById("mos-bench-library");
  target.className = "row-stack";
  target.innerHTML = MOS_BENCH_CATALOG.map(
    (item) => `
      <article class="data-row">
        <div class="data-row-head">
          <span class="strip-label">${escapeHtml(item.parent)}</span>
          <strong>${escapeHtml(item.label)}</strong>
        </div>
        <p>${escapeHtml(item.summary)}</p>
        <div class="button-row compact-controls">
          <button type="button" class="secondary" data-mos-bench="${escapeHtml(item.id)}">Open ${escapeHtml(item.label)} lane</button>
        </div>
      </article>
    `,
  ).join("");
}

function renderSectionMemoryProfile(profile) {
  const target = document.getElementById("section-memory-library");
  const entries = profile?.entries || [];
  if (!entries.length) {
    target.className = "row-stack empty-state";
    target.innerHTML = state.workspace
      ? emptyStateHtml("No section memory logged.", "Staff section gap patterns appear here after the first entry is added. Start with whichever section your bench misses most.")
      : `<p class="empty-state-detail">${PRELOAD_EMPTY_TEXT}</p>`;
    clearSectionMemoryForm();
    return;
  }
  target.className = "row-stack";
  target.innerHTML = entries
    .map((entry) => {
      const entryKey = sectionMemoryEntryKey(entry);
      return `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(entry.section)}</span>
            <strong>${escapeHtml(entry.title)}</strong>
            <span class="meta-inline">${escapeHtml(formatSectionMemoryUpdatedAt(entry.updated_at))}</span>
          </div>
          <p><strong>Questions:</strong> ${escapeHtml((entry.recurring_questions || []).slice(0, 3).join(" | ") || "None stored")}</p>
          <p><strong>Failure modes:</strong> ${escapeHtml((entry.recurring_failure_modes || []).slice(0, 3).join(" | ") || "None stored")}</p>
          <p><strong>Checks:</strong> ${escapeHtml((entry.preferred_checks || []).slice(0, 3).join(" | ") || "None stored")}</p>
          <p class="meta-inline">${escapeHtml((entry.notes || []).slice(0, 3).join(" | ") || "No extra notes stored.")}</p>
          <!-- A10: aria-label disambiguates Edit/Delete when multiple entries exist -->
          <div class="button-row compact-controls">
            <button type="button" class="secondary" data-section-memory-edit="${escapeHtml(entryKey)}"
              aria-label="Edit ${escapeAttribute(entry.section)} — ${escapeAttribute(entry.title)}">Edit</button>
            <button type="button" class="secondary" data-section-memory-delete="${escapeHtml(entryKey)}"
              aria-label="Delete ${escapeAttribute(entry.section)} — ${escapeAttribute(entry.title)}">Delete</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderReferenceLibrary(items) {
  const summary = document.getElementById("reference-summary");
  const selector = document.getElementById("reference-select");
  const target = document.getElementById("reference-library");
  if (!items.length) {
    summary.textContent = state.workspace ? "No reference notes loaded." : PRELOAD_EMPTY_TEXT;
    selector.innerHTML = `<option value="">${state.workspace ? "No reference notes loaded." : PRELOAD_EMPTY_TEXT}</option>`;
    selector.disabled = true;
    target.className = "reading-detail";
    target.innerHTML = state.workspace
      ? emptyStateHtml("No reference notes loaded.", "Curated doctrine and staff-source notes from the active module pack appear here once activated.")
      : `<p class="empty-state-detail">${PRELOAD_EMPTY_TEXT}</p>`;
    return;
  }
  summary.textContent = `${items.length} curated reference note(s) loaded from the repo source bench.`;
  if (!state.selectedReferenceSlug || !items.some((item) => item.slug === state.selectedReferenceSlug)) {
    state.selectedReferenceSlug = items[0].slug;
  }
  selector.disabled = false;
  selector.innerHTML = items
    .map(
      (item) =>
        `<option value="${escapeHtml(item.slug)}" ${item.slug === state.selectedReferenceSlug ? "selected" : ""}>${escapeHtml(item.title)}</option>`,
    )
    .join("");
  const selected = items.find((item) => item.slug === state.selectedReferenceSlug) || items[0];
  const links = Array.isArray(selected.official_links) ? selected.official_links : [];
  target.className = "reading-detail";
  target.innerHTML = `
    <article class="reading-item reading-focus-card">
      <div class="data-row-head">
        <span class="strip-label">Repo note</span>
        <strong>${escapeHtml(selected.title)}</strong>
      </div>
      <p>${escapeHtml(selected.summary)}</p>
      <p class="meta-inline">${escapeHtml(selected.note_path)}</p>
      <div class="row-stack">
        ${
          links.length
            ? links
                .map(
                  (link) => `
                    <article class="data-row">
                      <div class="data-row-head">
                        <span class="strip-label">Official source</span>
                        <strong>${escapeHtml(link.title)}</strong>
                      </div>
                      <p><a href="${escapeHtml(link.url)}" target="_blank" rel="noreferrer">${escapeHtml(link.url)}</a></p>
                    </article>
                  `,
                )
                .join("")
            : '<p class="helper-text">No official source links were extracted from this note yet.</p>'
        }
      </div>
    </article>
  `;
}

function renderMaradminTicker(items) {
  renderTickerStack("maradmin-ticker", items, "No MARADMINs tracked.");
}

function renderCustomWatchFeeds(items) {
  const target = document.getElementById("custom-feed-watch");
  if (!items.length) {
    target.className = "row-stack";
    target.innerHTML = state.workspace
      ? emptyStateHtml("No custom feeds configured.", "Local RSS watches — unit pages, PME sources, professional feeds — appear here once a feed URL is added.")
      : `<p class="empty-state-detail">${PRELOAD_EMPTY_TEXT}</p>`;
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
  const overviewTarget = document.getElementById("overview-history-fact");
  if (!items.length) {
    target.className = "row-stack";
    target.innerHTML = state.workspace
      ? emptyStateHtml("No history facts loaded.", "Unit and USMC historical facts for this date appear here once sources are checked.")
      : `<p class="empty-state-detail">${PRELOAD_EMPTY_TEXT}</p>`;
    if (overviewTarget) {
      overviewTarget.className = "row-stack";
      overviewTarget.innerHTML = target.innerHTML;
    }
    return;
  }
  state.todayInHistory = items;
  state.historyIndex = Math.min(state.historyIndex, items.length - 1);
  const item = items[state.historyIndex];
  target.className = "row-stack";
  target.innerHTML = renderHistoryFactCard(item, state.historyIndex, items.length);
  if (overviewTarget) {
    overviewTarget.className = "row-stack";
    overviewTarget.innerHTML = renderHistoryFactCard(item, state.historyIndex, items.length);
  }
}

function cycleHistoryFact() {
  if (!state.todayInHistory.length) { return; }
  state.historyIndex = (state.historyIndex + 1) % state.todayInHistory.length;
  renderHistory(state.todayInHistory);
}

function renderHistoryFactCard(item, index = 0, total = 1) {
  const significance = (item.significance || []).slice(0, 2);
  const sourceUrl = (item.references || []).find((r) => r.startsWith("http"));
  const sourceLink = sourceUrl
    ? `<p class="meta-inline"><a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener noreferrer">Source →</a></p>`
    : "";
  const nextBtn = total > 1
    ? `<button type="button" class="secondary small" onclick="cycleHistoryFact()">Next fact (${index + 1}/${total})</button>`
    : "";
  const shortMonths = ["","JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"];
  const dateLabel = `${item.day} ${shortMonths[item.month] || ""} ${item.year_label}`.trim();
  const today = new Date();
  const isToday = item.month === today.getMonth() + 1 && item.day === today.getDate();
  const fallbackNote = !isToday
    ? `<p class="meta-inline" style="color:var(--muted)">No entry for ${today.toLocaleDateString("en-US", { month: "short", day: "numeric" })} — showing a related entry.</p>`
    : "";
  // Nov 10: surface the Commandant's annual birthday message when it's actually the birthday
  const birthdayLink = item.month === 11 && item.day === 10 && isToday
    ? `<p class="meta-inline"><a href="https://www.marines.mil/News/Messages/" target="_blank" rel="noopener noreferrer">Commandant's Birthday Message →</a></p>`
    : "";
  return `
    <article class="data-row">
      <div class="data-row-head">
        <span class="strip-label">${escapeHtml(dateLabel)}</span>
        <strong>${escapeHtml(item.title)}</strong>
      </div>
      <p>${escapeHtml(item.summary)}</p>
      ${significance.length ? `<ul>${significance.map((entry) => `<li>${escapeHtml(entry)}</li>`).join("")}</ul>` : ""}
      ${fallbackNote}
      ${birthdayLink}
      ${sourceLink}
      ${nextBtn ? `<div class="button-row compact-controls">${nextBtn}</div>` : ""}
    </article>
  `;
}


function renderReadingBooks(items) {
  const summary = document.getElementById("reading-summary");
  const selector = document.getElementById("reading-book-select");
  const target = document.getElementById("reading-library");
  if (!items.length) {
    summary.textContent = state.workspace ? "No books loaded." : PRELOAD_EMPTY_TEXT;
    selector.innerHTML = `<option value="">${state.workspace ? "No books loaded." : PRELOAD_EMPTY_TEXT}</option>`;
    selector.disabled = true;
    target.className = "reading-detail";
    target.innerHTML = state.workspace
      ? emptyStateHtml("No reading list loaded.", "PME and Commandant's reading list items appear here once sources are checked.")
      : `<p class="empty-state-detail">${PRELOAD_EMPTY_TEXT}</p>`;
    return;
  }
  const completedCount = items.filter((item) => (item.progress?.status || "not_started") === "completed").length;
  summary.textContent = `${items.length} books loaded. ${completedCount} marked completed${state.mode !== "personal" ? ". Open a personal workspace to save notes." : "."}`;
  if (!state.selectedReadingSlug || !items.some((item) => item.slug === state.selectedReadingSlug)) {
    state.selectedReadingSlug = items[0].slug;
  }
  selector.disabled = false;
  selector.innerHTML = items
    .map((item) => {
      const status = item.progress?.status || "not_started";
      return `<option value="${escapeHtml(item.slug)}" ${item.slug === state.selectedReadingSlug ? "selected" : ""}>${escapeHtml(item.title)} (${escapeHtml(status.replaceAll("_", " "))})</option>`;
    })
    .join("");
  const selected = items.find((item) => item.slug === state.selectedReadingSlug) || items[0];
  const progress = selected.progress || {};
  const notes = Array.isArray(progress.notes) ? progress.notes.join("\n") : "";
  const status = progress.status || "not_started";
  const disabled = state.mode !== "personal" ? "disabled" : "";
  target.className = "reading-detail";
  target.innerHTML = `
    <article class="reading-item reading-focus-card">
      <div class="data-row-head">
        <span class="strip-label">${escapeHtml(status.replaceAll("_", " "))}</span>
        <strong>${escapeHtml(selected.title)}</strong>
      </div>
      <p class="meta-inline">${escapeHtml(selected.author)} | ${escapeHtml((selected.categories || []).slice(0, 3).join(", "))}</p>
      <p>${escapeHtml(selected.summary)}</p>
      <p class="meta-inline">${escapeHtml((selected.key_themes || []).slice(0, 4).join(" | "))}</p>
      <label>
        <span>Status</span>
        <select data-reading-status="${escapeHtml(selected.slug)}" ${disabled}>
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
        <textarea data-reading-notes="${escapeHtml(selected.slug)}" rows="5" ${disabled} placeholder="Thoughts, PME takeaways, or why this matters to your lane.">${escapeHtml(notes)}</textarea>
      </label>
      <div class="button-row">
        <button type="button" class="secondary" data-reading-save="${escapeHtml(selected.slug)}" ${disabled}>Save reading state</button>
      </div>
    </article>
  `;
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
    target.className = "row-stack";
    target.innerHTML = emptyStateHtml("No tracked opportunities.", "Billet and career opportunities appear here once added to the tracker.");
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
    target.className = "row-stack";
    target.innerHTML = emptyStateHtml("No tracked POAM items.", "Open action items and suspenses appear here once added.");
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

function renderTickerStack(targetId, items, emptyText) {
  const target = document.getElementById(targetId);
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.textContent = state.workspace ? emptyText : PRELOAD_EMPTY_TEXT;
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

function renderSourceUpdates(items) {
  const target = document.getElementById("source-updates");
  if (!items.length) {
    target.className = "row-stack";
    target.innerHTML = state.workspace
      ? emptyStateHtml("No source updates detected.", "Changes to tracked doctrine and admin sources appear here after the next source check.")
      : `<p class="empty-state-detail">${PRELOAD_EMPTY_TEXT}</p>`;
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

// ── Quick Links ────────────────────────────────────────────────────────────
const CATEGORY_ORDER = [
  "usmc_official", "admin_pay", "training_pme", "news_info", "benefits", "comms", "reserve", "it_access", "reference", "unit",
];

async function loadQuickLinks() {
  if (!state.userKey) return;
  const listEl = document.getElementById("quick-links-list");
  const filterEl = document.getElementById("quick-links-filter");
  if (!listEl) return;
  listEl.className = "row-stack";
  listEl.textContent = "Loading…";
  try {
    const data = await apiFetch(`/resource-links/${encodeURIComponent(state.userKey)}`);
    renderQuickLinks(data.links || [], data.categories || {}, listEl, filterEl);
  } catch (e) {
    listEl.className = "row-stack empty-state";
    listEl.textContent = "Could not load links.";
  }
}

function renderQuickLinks(links, categoryLabels, listEl, filterEl, onDelete) {
  if (!links.length) {
    listEl.className = "row-stack empty-state";
    listEl.textContent = "No links yet. Add one above.";
    filterEl.style.display = "none";
    return;
  }
  // Collect categories present in this link set
  const usedCats = [...new Set(links.map((l) => l.category))].sort(
    (a, b) => CATEGORY_ORDER.indexOf(a) - CATEGORY_ORDER.indexOf(b),
  );
  // Filter bar
  filterEl.style.display = "flex";
  let activeCat = null;
  const renderLinks = () => {
    const visible = activeCat ? links.filter((l) => l.category === activeCat) : links;
    if (!visible.length) {
      listEl.className = "row-stack empty-state";
      listEl.textContent = "No links in this category.";
      return;
    }
    // Group by category
    const groups = {};
    for (const link of visible) {
      (groups[link.category] = groups[link.category] || []).push(link);
    }
    listEl.className = "row-stack";
    listEl.innerHTML = Object.entries(groups)
      .sort(([a], [b]) => CATEGORY_ORDER.indexOf(a) - CATEGORY_ORDER.indexOf(b))
      .map(
        ([cat, catLinks]) => `
        <div class="ql-category-group">
          <p class="meta-inline" style="margin-bottom:0.3rem;font-weight:600">${escapeHtml(categoryLabels[cat] || cat)}</p>
          <div class="ql-link-grid" style="display:flex;flex-wrap:wrap;gap:0.4rem;">
            ${catLinks
              .map(
                (l) => `
              <div class="ql-link-chip" style="display:flex;align-items:center;gap:0.25rem;">
                <a href="${escapeHtml(l.url)}" target="_blank" rel="noopener noreferrer"
                   class="strip-label" title="${escapeHtml(l.description || l.title)}"
                   style="text-decoration:none">${escapeHtml(l.title)}</a>
                ${!l.is_seed ? `<button type="button" class="ql-delete-btn" data-link-id="${escapeHtml(l.id)}"
                   aria-label="Remove ${escapeHtml(l.title)}" style="background:none;border:none;cursor:pointer;padding:0;line-height:1">✕</button>` : ""}
              </div>`,
              )
              .join("")}
          </div>
        </div>`,
      )
      .join("");
    listEl.querySelectorAll(".ql-delete-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = btn.dataset.linkId;
        if (!state.userKey || !id) return;
        try {
          await apiFetch(`/resource-links/${encodeURIComponent(state.userKey)}/${encodeURIComponent(id)}`, {
            method: "DELETE",
          });
        } catch (_) {}
        await loadQuickLinks();
        if (onDelete) await onDelete();
      });
    });
  };
  // Build filter chips
  filterEl.innerHTML = `
    <button type="button" class="strip-label ql-filter-chip ${!activeCat ? "active" : ""}" data-cat="">All</button>
    ${usedCats
      .map(
        (c) =>
          `<button type="button" class="strip-label ql-filter-chip" data-cat="${escapeHtml(c)}">${escapeHtml(categoryLabels[c] || c)}</button>`,
      )
      .join("")}`;
  filterEl.querySelectorAll(".ql-filter-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      activeCat = chip.dataset.cat || null;
      filterEl.querySelectorAll(".ql-filter-chip").forEach((c) => c.classList.toggle("active", c === chip));
      renderLinks();
    });
  });
  renderLinks();
}

function initQuickLinksForm() {
  const addBtn = document.getElementById("quick-links-add-btn");
  const cancelBtn = document.getElementById("quick-links-cancel-btn");
  const form = document.getElementById("quick-links-add-form");
  if (!addBtn || !form) return;
  addBtn.addEventListener("click", () => {
    form.classList.toggle("is-hidden", false);
    addBtn.disabled = true;
    document.getElementById("ql-title")?.focus();
  });
  cancelBtn?.addEventListener("click", () => {
    form.classList.add("is-hidden");
    form.reset();
    addBtn.disabled = false;
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.userKey) return;
    const title = document.getElementById("ql-title")?.value.trim();
    const url = document.getElementById("ql-url")?.value.trim();
    const description = document.getElementById("ql-description")?.value.trim() || null;
    const category = document.getElementById("ql-category")?.value || "unit";
    if (!title || !url) return;
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving…";
    try {
      await apiFetch(`/resource-links/${encodeURIComponent(state.userKey)}`, {
        method: "POST",
        body: JSON.stringify({ title, url, description, category, tags: [] }),
      });
      form.classList.add("is-hidden");
      form.reset();
      addBtn.disabled = false;
      await loadQuickLinks();
    } catch (_) {
      submitBtn.textContent = "Error — retry";
    } finally {
      submitBtn.disabled = false;
      if (submitBtn.textContent === "Saving…") submitBtn.textContent = "Save link";
    }
  });
}
// ── A Few Good Links tab (reuses renderQuickLinks) ────────────────────────
async function loadGoodLinks() {
  if (!state.userKey) return;
  const listEl = document.getElementById("good-links-grid");
  const filterEl = document.getElementById("good-links-filters");
  if (!listEl) return;
  listEl.className = "row-stack";
  listEl.textContent = "Loading…";
  try {
    const data = await apiFetch(`/resource-links/${encodeURIComponent(state.userKey)}`);
    renderQuickLinks(data.links || [], data.categories || {}, listEl, filterEl, loadGoodLinks);
  } catch (_) {
    listEl.className = "row-stack empty-state";
    listEl.textContent = "Could not load links.";
  }
}

function initGoodLinksForm() {
  const form = document.getElementById("good-links-add-form");
  const cancelBtn = document.getElementById("good-links-cancel");
  const drawer = document.getElementById("good-links-add-drawer");
  const catSelect = document.getElementById("good-links-category-select");
  if (!form || !catSelect) return;
  catSelect.innerHTML = CATEGORY_ORDER.map(
    (c) => `<option value="${c}">${escapeHtml(c.replace(/_/g, " "))}</option>`,
  ).join("");
  cancelBtn?.addEventListener("click", () => {
    drawer.removeAttribute("open");
    form.reset();
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.userKey) return;
    const fd = new FormData(form);
    const title = fd.get("title")?.toString().trim();
    const url = fd.get("url")?.toString().trim();
    const description = fd.get("description")?.toString().trim() || null;
    const category = fd.get("category")?.toString() || "unit";
    if (!title || !url) return;
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.disabled = true;
    submitBtn.textContent = "Saving…";
    try {
      await apiFetch(`/resource-links/${encodeURIComponent(state.userKey)}`, {
        method: "POST",
        body: JSON.stringify({ title, url, description, category, tags: [] }),
      });
      drawer.removeAttribute("open");
      form.reset();
      await loadGoodLinks();
      await loadQuickLinks();
    } catch (_) {
      submitBtn.textContent = "Error — retry";
    } finally {
      submitBtn.disabled = false;
      if (submitBtn.textContent === "Saving…") submitBtn.textContent = "Save link";
    }
  });
}
initGoodLinksForm();
// ── End Good Links ────────────────────────────────────────────────────────

function renderQueue(items, hotItems = []) {
  const target = document.getElementById("priority-queue");
  const normalizedItems = Array.isArray(items) ? items : [];
  const normalizedHotItems = Array.isArray(hotItems) ? hotItems : [];
  const combined = buildActionStack(normalizedItems, normalizedHotItems);
  if (!combined.length) {
    target.className = "row-stack";
    target.innerHTML = emptyStateHtml("No action brief for this drill period.", "Build a brief to compile obligations, deadlines, and source updates before next drill.");
    return;
  }
  target.className = "row-stack";
  target.innerHTML = combined
    .map(
      (item) => `
        <article class="data-row ${queueSeverityClass(item.severity)}">
          <div class="data-row-head">
            <span class="strip-label ${queueSeverityBadgeClass(item.severity)}">${escapeHtml(item.category || "watch")}</span>
            <strong>${escapeHtml(item.title || "Untitled item")}</strong>
            <span class="meta-inline">${escapeHtml(queueSeverityLabel(item.severity))}</span>
          </div>
          <p>${escapeHtml(item.recommendation || item.notes || item.detail || "")}</p>
        </article>
      `,
    )
    .join("");
}

function buildActionStack(items, hotItems) {
  const combined = [];
  const seen = new Set();

  for (const item of items.slice(0, 6)) {
    const key = `${item.category || "watch"}::${item.title || ""}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    combined.push({
      ...item,
      severity: prioritySeverity(item.priority, item.category),
    });
  }

  for (const hotItem of hotItems.slice(0, 4)) {
    const title = String(hotItem || "").trim();
    if (!title) {
      continue;
    }
    const key = `continuity::${title}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    combined.push({
      category: "continuity",
      title,
      detail: "Continuity drift from the battle rhythm board needs a direct look.",
      severity: "attention",
    });
  }

  return combined.sort((left, right) => queueSeverityRank(right.severity) - queueSeverityRank(left.severity));
}

function prioritySeverity(priority, category) {
  const normalizedPriority = String(priority || "").toLowerCase();
  const normalizedCategory = String(category || "").toLowerCase();
  if (normalizedPriority === "high") {
    return "critical";
  }
  if (normalizedCategory === "source_updates" || normalizedCategory === "pme" || normalizedCategory === "admin") {
    return "attention";
  }
  return "routine";
}

function queueSeverityRank(severity) {
  switch (severity) {
    case "critical":
      return 3;
    case "attention":
      return 2;
    default:
      return 1;
  }
}

function queueSeverityLabel(severity) {
  switch (severity) {
    case "critical":
      return "Critical";
    case "attention":
      return "Attention";
    default:
      return "Routine";
  }
}

function queueSeverityClass(severity) {
  switch (severity) {
    case "critical":
      return "queue-item queue-item-critical";
    case "attention":
      return "queue-item queue-item-attention";
    default:
      return "queue-item queue-item-routine";
  }
}

function queueSeverityBadgeClass(severity) {
  switch (severity) {
    case "critical":
      return "strip-critical";
    case "attention":
      return "strip-attention";
    default:
      return "strip-routine";
  }
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

function renderStaffUpdateCycleOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  const runningEstimate = payload.running_estimate || {};
  const cub = payload.cub || {};
  const cpb = payload.cpb || {};
  const estimateRows = (runningEstimate.running_estimates || [])
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.section || "section")}</span>
            <strong>${escapeHtml((item.current_situation || [])[0] || "No summary")}</strong>
          </div>
          <p>${escapeHtml((item.risks || [])[0] || (item.supportability || [])[0] || "No immediate friction recorded.")}</p>
        </article>
      `,
    )
    .join("");
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">Command summary</span>
      <ul>${(runningEstimate.command_summary || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>
    <section>
      <span class="strip-label">Running estimates</span>
      <div class="row-stack">${estimateRows || "<div class=\"empty-state\">No section estimates returned.</div>"}</div>
    </section>
    <section>
      <span class="strip-label">CUB</span>
      <ul>${(cub.commander_decisions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No commander decisions surfaced.</li>"}</ul>
      <p class="meta-inline">Due-outs: ${escapeHtml((cub.due_outs || []).slice(0, 3).join(" | ") || "None recorded.")}</p>
    </section>
    <section>
      <span class="strip-label">CPB (Civil Affairs)</span>
      <ul>${(cpb.decision_points || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No civil-prep decision points surfaced.</li>"}</ul>
      <p class="meta-inline">Branches/sequels: ${escapeHtml((cpb.branches_and_sequels || []).slice(0, 2).join(" | ") || "None recorded.")}</p>
    </section>
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>
  `;
}

function renderPlanningCellOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  const missionAnalysis = payload.mission_analysis || {};
  const planningApproach = payload.planning_approach || {};
  const updateCycle = payload.update_cycle || {};
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">Planning approach</span>
      <h3>${escapeHtml((planningApproach.recommended_method || "planning").toUpperCase())}</h3>
      <p>${escapeHtml(planningApproach.decision || "No planning approach decision returned.")}</p>
      <ul>${(planningApproach.why || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>
    <section>
      <span class="strip-label">Mission analysis</span>
      <p><strong>Mission statement:</strong> ${escapeHtml(missionAnalysis.mission_statement || "No mission statement returned.")}</p>
      <p class="meta-inline">Specified tasks: ${escapeHtml((missionAnalysis.specified_tasks || []).slice(0, 3).join(" | ") || "None")}</p>
      <p class="meta-inline">Implied tasks: ${escapeHtml((missionAnalysis.implied_tasks || []).slice(0, 3).join(" | ") || "None")}</p>
      <p class="meta-inline">Information requirements: ${escapeHtml((missionAnalysis.information_requirements || []).slice(0, 3).join(" | ") || "None")}</p>
    </section>
    <section>
      <span class="strip-label">Assumption log</span>
      <ul>${(payload.assumption_log || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No assumptions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Commander decision log</span>
      <ul>${(payload.commander_decision_log || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No commander decisions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Due-out board</span>
      <ul>${(payload.due_out_board || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No due-outs returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Red-team focus</span>
      <ul>${(payload.red_team_focus || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No red-team focus returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Linked update cycle</span>
      <p class="meta-inline">CUB decisions: ${escapeHtml(((updateCycle.cub || {}).commander_decisions || []).slice(0, 3).join(" | ") || "None")}</p>
      <p class="meta-inline">Civil-prep branches: ${escapeHtml(((updateCycle.cpb || {}).branches_and_sequels || []).slice(0, 2).join(" | ") || "None")}</p>
      <p class="meta-inline">Next OPT actions: ${escapeHtml((payload.next_opt_actions || []).slice(0, 3).join(" | ") || "None")}</p>
    </section>
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>
  `;
}

function renderBriefClinicOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">Coach answer</span>
      <p>${escapeHtml(payload.answer || "No answer returned.")}</p>
    </section>
    <section>
      <span class="strip-label">Follow-up questions</span>
      <ul>${(payload.follow_up_questions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No follow-up questions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No warnings returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Citations</span>
      <ul>${(payload.citations || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No citations returned.</li>"}</ul>
    </section>
  `;
}

function renderAgentAdvisoryOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">Advisor answer</span>
      <p>${escapeHtml(payload.answer || "No answer returned.")}</p>
    </section>
    <section>
      <span class="strip-label">Follow-up questions</span>
      <ul>${(payload.follow_up_questions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No follow-up questions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No warnings returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Citations</span>
      <ul>${(payload.citations || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No citations returned.</li>"}</ul>
    </section>
  `;
}

function renderLonePlannerOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  const planningCell = payload.planning_cell || {};
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">Posture</span>
      <h3>${escapeHtml(payload.posture || "No lone-planner posture returned.")}</h3>
      <ul>${(payload.walk_in_brief || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No walk-in brief returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Likely blind spots</span>
      <ul>${(payload.likely_blind_spots || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No blind spots returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Missing section questions</span>
      <ul>${(payload.missing_section_questions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No section questions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Cross-lane asks</span>
      <ul>${(payload.cross_lane_asks || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No cross-lane asks returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Recommended products</span>
      <ul>${(payload.recommended_products || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No products returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Immediate actions</span>
      <ul>${(payload.immediate_actions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No immediate actions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Linked planning cell</span>
      <p class="meta-inline">Approach: ${escapeHtml((planningCell.planning_approach || {}).recommended_method || "Not stated")}</p>
      <p class="meta-inline">Top decision: ${escapeHtml(((planningCell.commander_decision_log || [])[0]) || "None")}</p>
      <p class="meta-inline">Top due-out: ${escapeHtml(((planningCell.due_out_board || [])[0]) || "None")}</p>
    </section>
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>
  `;
}

function renderSectionGapCoverOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">Posture</span>
      <h3>${escapeHtml(payload.posture || "No section gap-cover posture returned.")}</h3>
      <p class="meta-inline">Focus sections: ${escapeHtml((payload.focus_sections || []).join(" | ") || "None stated")}</p>
    </section>
    <section>
      <span class="strip-label">XO walk-in lines</span>
      <ul>${(payload.xo_walk_in_lines || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No walk-in lines returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Cross-lane risks</span>
      <ul>${(payload.cross_lane_risks || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No cross-lane risks returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Recommended products</span>
      <ul>${(payload.recommended_products || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No products returned.</li>"}</ul>
    </section>
    ${(payload.section_estimates || [])
      .map(
        (item) => `
          <section>
            <span class="strip-label">${escapeHtml(item.section_status || "section")}</span>
            <h3>${escapeHtml(item.section)}</h3>
            <p class="meta-inline">${escapeHtml(item.confidence_note || "")}</p>
            <p><strong>Known inputs:</strong> ${escapeHtml((item.known_inputs || []).join(" | ") || "None stated")}</p>
            <p><strong>Likely questions:</strong> ${escapeHtml((item.likely_questions || []).join(" | ") || "None stated")}</p>
            <p><strong>Support facts:</strong> ${escapeHtml((item.likely_support_facts || []).join(" | ") || "None stated")}</p>
            <p><strong>Coordination:</strong> ${escapeHtml((item.likely_coordination || []).join(" | ") || "None stated")}</p>
            <ul>${(item.draft_estimate_lines || []).map((line) => `<li>${escapeHtml(line)}</li>`).join("") || "<li>No draft estimate lines returned.</li>"}</ul>
            <div class="button-row compact-controls">
              <button
                type="button"
                class="secondary"
                data-section-memory-seed="${escapeHtml(
                  encodeSectionMemorySeed({
                    section: item.section,
                    title: `${item.section} recurring estimate checks`,
                    recurring_questions: item.likely_questions || [],
                    recurring_failure_modes: item.confidence_note ? [item.confidence_note] : [],
                    preferred_checks: item.likely_coordination || [],
                    notes: item.likely_support_facts || [],
                  }),
                )}"
              >
                Save as section memory starter
              </button>
            </div>
          </section>
        `,
      )
      .join("")}
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>
  `;
}

function renderStaffPlanningPackageOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  const planningApproach = payload.planning_approach || {};
  const productPackage = payload.product_package || [];
  const commandCell = payload.command_cell || {};
  const xoSync = payload.xo_sync || {};
  const s1Readiness = payload.s1_readiness || {};
  const safetyPlan = payload.safety_plan || {};
  const selPlan = payload.sel_plan || {};
  const medicalPlan = payload.medical_plan || {};
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">Package posture</span>
      <h3>${escapeHtml(payload.title || "No staff package title returned.")}</h3>
      <p class="meta-inline">Approach: ${escapeHtml(planningApproach.recommended_method || "Not stated")}</p>
      <p class="meta-inline">Decision: ${escapeHtml(planningApproach.decision || "Not stated")}</p>
      <ul>${(payload.summary || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No package summary returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Commander decisions now</span>
      <ul>${(payload.commander_decisions_now || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No commander decisions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Top risks and cuts</span>
      <p><strong>Top risks:</strong> ${escapeHtml((payload.top_risks || []).join(" | ") || "None returned")}</p>
      <p><strong>Cuts / deferments:</strong> ${escapeHtml((payload.cuts_and_deferments || []).join(" | ") || "None returned")}</p>
      <p><strong>Recommended actions:</strong> ${escapeHtml((payload.recommended_actions || []).join(" | ") || "None returned")}</p>
    </section>
    <section>
      <span class="strip-label">Command cell and XO</span>
      <p><strong>XO sync:</strong> ${escapeHtml((xoSync.command_sync_frame || []).join(" | ") || "None returned")}</p>
      <p><strong>Decision support:</strong> ${escapeHtml((xoSync.decision_support_matrix || []).join(" | ") || "None returned")}</p>
      <p><strong>Chief focus:</strong> ${escapeHtml((commandCell.chief_focus_board || []).join(" | ") || "None returned")}</p>
      <p><strong>Battle captain watch:</strong> ${escapeHtml((commandCell.battle_captain_watchboard || []).join(" | ") || "None returned")}</p>
    </section>
    <section>
      <span class="strip-label">Admin, safety, SEL, and medical</span>
      <p><strong>S-1 readiness:</strong> ${escapeHtml((s1Readiness.readiness_estimate || []).join(" | ") || "None returned")}</p>
      <p><strong>Safety plan:</strong> ${escapeHtml((safetyPlan.no_go_criteria || []).join(" | ") || "None returned")}</p>
      <p><strong>SEL plan:</strong> ${escapeHtml((selPlan.leader_touchpoints || []).join(" | ") || "None returned")}</p>
      <p><strong>Medical plan:</strong> ${escapeHtml((medicalPlan.medical_decision_points || []).join(" | ") || "None returned")}</p>
    </section>
    <section>
      <span class="strip-label">Linked staff products</span>
      <ul>${productPackage.map((item) => `<li>${escapeHtml(item.title || item.product_type || "product")}</li>`).join("") || "<li>No staff products returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).slice(0, 6).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No warnings returned.</li>"}</ul>
    </section>
  `;
}

function renderMissionAnalysisOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">Mission analysis</span>
      <p><strong>Mission statement:</strong> ${escapeHtml(payload.mission_statement || "No mission statement returned.")}</p>
      <p class="meta-inline">Supported unit: ${escapeHtml(payload.supported_unit || "Not stated")}</p>
    </section>
    <section>
      <span class="strip-label">Tasks</span>
      <ul>${(payload.specified_tasks || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      <p class="meta-inline">Implied: ${escapeHtml((payload.implied_tasks || []).slice(0, 3).join(" | ") || "None")}</p>
      <p class="meta-inline">Essential: ${escapeHtml((payload.essential_tasks || []).slice(0, 3).join(" | ") || "None")}</p>
    </section>
    <section>
      <span class="strip-label">Assumptions and requirements</span>
      <ul>${(payload.assumptions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      <p class="meta-inline">Information requirements: ${escapeHtml((payload.information_requirements || []).slice(0, 3).join(" | ") || "None")}</p>
      <p class="meta-inline">Staff estimates: ${escapeHtml((payload.staff_estimate_requirements || []).slice(0, 4).join(" | ") || "None")}</p>
    </section>
    <section>
      <span class="strip-label">Commander decisions</span>
      <ul>${(payload.commander_decisions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No commander decisions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>
  `;
}

function renderList(targetId, items) {
  const target = document.getElementById(targetId);
  target.innerHTML = items.length ? items.map((item) => `<li>${escapeHtml(item)}</li>`).join("") : "<li>No items.</li>";
}

async function saveReadingProgress(slug, button = null) {
  if (state.mode !== "personal" || !state.userKey) {
    setWorkspaceNote("Switch to personal mode to save reading state.", true);
    setPanelStatus(button, "Switch to personal mode to save reading state.", true);
    return;
  }
  await withButtonFeedback(
    button,
    "Saving...",
    "Reading state saved.",
    async () => {
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
    },
    {
      errorContext: "Failed to save reading state",
      statusTarget: () => document.querySelector(`[data-reading-save="${CSS.escape(slug)}"]`) || button,
    },
  );
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

async function savePlanningCellToBattleRhythm() {
  if (state.mode !== "personal" || !state.userKey) {
    setWorkspaceNote("Open your personal workspace first so the battle rhythm board can stay local to your profile.", true);
    return;
  }
  try {
    const payload = buildPlanningCellPayloadFromForm();
    const board = await apiFetch(
      `/staff/battle-rhythm/${encodeURIComponent(state.userKey)}/from-planning-cell`,
      {
        method: "POST",
        auth: true,
        body: JSON.stringify(payload),
      },
    );
    renderBattleRhythm(board);
    await loadWorkspace();
    setWorkspaceNote("Battle rhythm board saved from the current planning cell.");
  } catch (error) {
    console.error("Failed to save planning cell to battle rhythm", error);
    setWorkspaceNote(error.message, true);
  }
}

async function runLonePlannerMode() {
  try {
    const payload = buildPlanningCellPayloadFromForm();
    const data = await apiFetch("/staff/lone-planner", { method: "POST", body: JSON.stringify(payload) });
    renderLonePlannerOutput("lone-planner-output", data);
    openLane("draft", "Lone planner mode ran against the current planning context.");
  } catch (error) {
    console.error("Failed to run lone planner mode", error);
    setWorkspaceNote(error.message, true);
  }
}

async function runSectionGapCover() {
  try {
    const payload = buildPlanningCellPayloadFromForm();
    const data = await apiFetch("/staff/assisted-section-estimates", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    renderSectionGapCoverOutput("section-gap-cover-output", data);
    openLane("draft", "Built assisted section estimates from the current planning context.");
  } catch (error) {
    console.error("Failed to build section gap cover", error);
    setWorkspaceNote(error.message, true);
  }
}

async function runStaffPlanningPackageAndReturn() {
  const planning = buildPlanningCellPayloadFromForm();
  const payload = {
    title: planning.title,
    event_type: planning.event_type,
    mission_or_training_goal: planning.mission_or_training_goal,
    audience: planning.supported_unit,
    timeframe: planning.time_available,
    constraints: planning.constraints || [],
    coordinating_sections: planning.coordinating_sections || [],
    support_requirements: planning.support_requirements || [],
    civil_considerations: planning.civil_considerations || [],
    include_g9: (planning.civil_considerations || []).length > 0,
    product_types: ["warno", "frago", "aar"],
    training_only: true,
  };
  return apiFetch("/planning/staff-package", { method: "POST", body: JSON.stringify(payload) });
}

async function runStaffPlanningPackage() {
  // Used by the in-lane planning cell button — renders into the lane output div
  try {
    const data = await runStaffPlanningPackageAndReturn();
    renderStaffPlanningPackageOutput("staff-package-output", data);
    setWorkspaceNote("Built the integrated staff package.");
  } catch (error) {
    console.error("Failed to build staff planning package", error);
    setWorkspaceNote(error.message, true);
  }
}

function openMosBenchLane(agentId) {
  const item = MOS_BENCH_CATALOG.find((entry) => entry.id === agentId);
  if (!item) {
    setWorkspaceNote("That MOS lane is not available.", true);
    return;
  }
  const form = document.getElementById("mos-advisor-form");
  form.elements.mos_tool.value = item.id;
  form.elements.prompt.value = item.starter;
  openToolDrawer("drawer-mos-advisor");
  setWorkspaceNote(`MOS Advisor is open — ${item.label} lane loaded.`);
}

function openLane(lane, message = "", options = {}) {
  const updateHistory = options.updateHistory !== false;
  state.activeLane = lane;
  applyLaneVisibility(true);
  if (updateHistory) {
    pushLaneHistory(lane);
  }
  if (message) {
    setWorkspaceNote(message);
  }
}

async function runMosAdvisorFromForm() {
  const form = document.getElementById("mos-advisor-form");
  const toolId = form.elements.mos_tool.value;
  const prompt = String(form.elements.prompt.value || "").trim();
  const audience = String(form.elements.audience.value || "SMCR officer").trim();
  if (!prompt) {
    setWorkspaceNote("Add a prompt before running the MOS advisor.", true);
    return;
  }
  const data = await apiFetch(`/agents/${encodeURIComponent(toolId)}/run`, {
    method: "POST",
    body: JSON.stringify({
      input: prompt,
      context: {
        user_key: state.userKey || undefined,
        request_is_training_or_fictional: true,
        user_role: audience,
      },
    }),
  });
  renderAgentAdvisoryOutput("mos-advisor-output", data);
}

async function saveBattleRhythmBoard() {
  if (state.mode !== "personal" || !state.userKey) {
    setWorkspaceNote("Open your personal workspace first so board edits stay local to your profile.", true);
    return;
  }
  try {
    const payload = buildBattleRhythmPayloadFromForm();
    const board = await apiFetch(`/staff/battle-rhythm/${encodeURIComponent(state.userKey)}`, {
      method: "PUT",
      auth: true,
      body: JSON.stringify(payload),
    });
    renderBattleRhythm(board);
    await loadWorkspace();
    setWorkspaceNote("Battle rhythm board updated.");
  } catch (error) {
    console.error("Failed to save battle rhythm board", error);
    setWorkspaceNote(error.message, true);
  }
}

function isMessageFeedsEmpty(workspace) {
  return (
    !workspace?.maradmin_ticker?.length &&
    !workspace?.navadmin_ticker?.length &&
    !workspace?.alnav_ticker?.length
  );
}

async function autoPreloadMessageFeeds() {
  try {
    await Promise.all([
      apiFetch("/maradmins/refresh", { method: "POST", auth: true }),
      apiFetch("/message-watch/navadmins/refresh", { method: "POST", auth: true }),
      apiFetch("/message-watch/alnavs/refresh", { method: "POST", auth: true }),
      apiFetch("/message-watch/dod/refresh", { method: "POST", auth: true }),
      apiFetch("/history/seed", { method: "POST", auth: true }),
      apiFetch("/history/refresh", { method: "POST", auth: true }),
    ]);
    state.workspace = await apiFetch(
      `/dashboard/data/${encodeURIComponent(state.userKey)}`,
      { auth: true },
    );
    renderWorkspace(state.workspace);
    markLastUpdated(["maradmins", "sourceWatch"]);
  } catch {
    // silent — user can manually refresh if auto-preload fails
  }
}

async function refreshSourceLane(lane, button = null) {
  if (state.mode !== "personal") {
    setWorkspaceNote("Open your personal workspace to refresh local source watches.", true);
    setPanelStatus(button, "Open your personal workspace to refresh local source watches.", true);
    return;
  }
  const refreshers = {
    maradmins: [["/maradmins/refresh", "POST"]],
    reading: [["/reading-list/refresh", "POST"]],
    navadmins: [["/message-watch/navadmins/refresh", "POST"]],
    alnavs: [["/message-watch/alnavs/refresh", "POST"]],
    dod: [["/message-watch/dod/refresh", "POST"]],
    all: [
      ["/maradmins/refresh", "POST"],
      ["/reading-list/refresh", "POST"],
      ["/message-watch/navadmins/refresh", "POST"],
      ["/message-watch/alnavs/refresh", "POST"],
      ["/message-watch/dod/refresh", "POST"],
    ],
  };
  const sequence = refreshers[lane] || [];
  const successMessage = lane === "all" ? "Source-watch stack refreshed." : `${lane.replaceAll("-", " ")} refreshed.`;
  const timestampKeys = {
    maradmins: ["maradmins"],
    reading: ["reading"],
    navadmins: ["sourceWatch"],
    alnavs: ["sourceWatch"],
    dod: ["sourceWatch"],
    all: ["maradmins", "reading", "sourceWatch"],
  };
  await withButtonFeedback(
    button,
    "Refreshing...",
    successMessage,
    async () => {
      for (const [path, method] of sequence) {
        await apiFetch(path, { method, auth: true });
      }
      markLastUpdated(timestampKeys[lane] || []);
      setWorkspaceNote(successMessage);
      await loadWorkspace();
    },
    { disableButtonGroup: "sourceWatch", errorContext: `Failed to refresh source lane: ${lane}` },
  );
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  if (options.auth && state.apiKey) {
    headers["X-Local-API-Key"] = state.apiKey;
  }
  let response;
  try {
    response = await fetch(`${state.apiBase}${path}`, {
      method: options.method || "GET",
      headers,
      body: options.body,
    });
  } catch (error) {
    recordFetchFailure();
    const networkError = new Error("Cannot reach local server.");
    networkError.isNetworkError = true;
    networkError.cause = error;
    throw networkError;
  }
  if (!response.ok) {
    const text = await response.text();
    recordFetchFailure();
    const httpError = new Error(`Request failed (${response.status}): ${text}`);
    httpError.status = response.status;
    httpError.responseText = text;
    throw httpError;
  }
  if (options.text) {
    const text = await response.text();
    recordFetchSuccess();
    return text;
  }
  if (options.blob) {
    const blob = await response.blob();
    recordFetchSuccess();
    return blob;
  }
  try {
    const data = await response.json();
    recordFetchSuccess();
    return data;
  } catch (error) {
    recordFetchFailure();
    throw error;
  }
}

function recordFetchSuccess() {
  state.consecutiveFetchFailures = 0;
  state.connectionLostDismissed = false;
  setConnectionLostVisible(false);
}

function recordFetchFailure() {
  state.consecutiveFetchFailures += 1;
  if (state.consecutiveFetchFailures >= 3 && !state.connectionLostDismissed) {
    setConnectionLostVisible(true);
  }
}

function setWorkspaceNote(message, critical = false) {
  const note = document.getElementById("workspace-note");
  note.textContent = message;
  note.className = critical ? "helper-text critical" : "helper-text";
}

function updateModeBanner() {
  // A5: mode-badge element is now present in HTML; keep data-mode in sync for CSS
  const badge = document.getElementById("mode-badge");
  if (badge) {
    badge.textContent = state.mode === "demo" ? "Demo mode" : "Personal mode";
    badge.setAttribute("data-mode", state.mode);
  }
}

function toggleTimezonePanel() {
  state.timezonePanelOpen = !state.timezonePanelOpen;
  // A8: keep aria-expanded in sync with open state
  const btn = document.getElementById("toggle-timezone-panel");
  if (btn) {
    btn.setAttribute("aria-expanded", state.timezonePanelOpen ? "true" : "false");
  }
  renderTimezoneControls();
}

function renderTimezoneStrip() {
  const target = document.getElementById("timezone-display");
  if (!target) {
    return;
  }
  const selected = getSelectedTimezoneOptions();
  const now = new Date();
  target.innerHTML = selected
    .map((option) => {
      const snapshot = formatTimezoneSnapshot(option, now);
      return `
        <article class="timezone-card">
          <span class="timezone-card-label">${escapeHtml(snapshot.label)}</span>
          <strong class="timezone-card-time">${escapeHtml(snapshot.time)}</strong>
          <span class="timezone-card-meta">${escapeHtml(snapshot.meta)}</span>
        </article>
      `;
    })
    .join("");
}

function renderTimezoneControls() {
  const panel = document.getElementById("timezone-controls");
  const target = document.getElementById("timezone-option-list");
  if (!panel || !target) {
    return;
  }
  panel.classList.toggle("is-hidden", !state.timezonePanelOpen);
  target.innerHTML = state.timezoneOptions
    .map(
      (option) => `
        <label class="timezone-option">
          <input
            type="checkbox"
            data-timezone-option="${escapeHtml(option.id)}"
            ${state.selectedTimezoneIds.includes(option.id) ? "checked" : ""}
          />
          <span class="timezone-option-text">
            <strong>${escapeHtml(option.label)}</strong>
            <span>${escapeHtml(option.description)}</span>
          </span>
        </label>
      `,
    )
    .join("");
}

function startLastUpdatedClock() {
  renderLastUpdatedStamps();
  if (state.lastUpdatedTimer) {
    clearInterval(state.lastUpdatedTimer);
  }
  state.lastUpdatedTimer = setInterval(renderLastUpdatedStamps, 60000);
}

function updateTimezoneSelection(optionId, checked) {
  const next = checked
    ? [...new Set([...state.selectedTimezoneIds, optionId])]
    : state.selectedTimezoneIds.filter((id) => id !== optionId);
  state.selectedTimezoneIds = next.length ? next : ["local", "zulu", "quantico"];
  try {
    window.localStorage.setItem("smcr.dashboard.timezones", JSON.stringify(state.selectedTimezoneIds));
  } catch (_error) {
    console.error("Failed to save timezone selection", _error);
    // Keep the current in-memory preference if browser storage is unavailable.
  }
  renderTimezoneStrip();
  renderTimezoneControls();
}

function buildTimezoneOptions() {
  return [
    {
      id: "local",
      label: "Local",
      description: "Your browser's current local time zone.",
      timeZone: null,
    },
    {
      id: "zulu",
      label: "Zulu",
      description: "UTC / Z time for common planning reference.",
      timeZone: "UTC",
    },
    {
      id: "quantico",
      label: "Quantico",
      description: "Eastern Time reference for Quantico-area working hours.",
      timeZone: "America/New_York",
    },
    {
      id: "central",
      label: "Central",
      description: "Useful if your local browser is not already on Central.",
      timeZone: "America/Chicago",
    },
    {
      id: "pacific",
      label: "Pacific",
      description: "West Coast coordination reference.",
      timeZone: "America/Los_Angeles",
    },
    {
      id: "okinawa",
      label: "Okinawa",
      description: "Japan Standard Time reference.",
      timeZone: "Asia/Tokyo",
    },
  ];
}

function loadTimezoneSelection() {
  try {
    const raw = window.localStorage.getItem("smcr.dashboard.timezones");
    if (!raw) {
      return ["local", "zulu", "quantico"];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length ? parsed : ["local", "zulu", "quantico"];
  } catch (_error) {
    console.error("Failed to load timezone selection", _error);
    return ["local", "zulu", "quantico"];
  }
}

function getSelectedTimezoneOptions() {
  const selected = state.timezoneOptions.filter((option) => state.selectedTimezoneIds.includes(option.id));
  return selected.length ? selected : state.timezoneOptions.filter((option) => ["local", "zulu", "quantico"].includes(option.id));
}

function formatTimezoneSnapshot(option, now) {
  const resolvedLocalZone = new Intl.DateTimeFormat().resolvedOptions().timeZone || "Local";
  const zone = option.timeZone || resolvedLocalZone;
  const parts = new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: false,
    timeZone: zone,
    timeZoneName: "short",
  }).formatToParts(now);
  const time = `${findDatePart(parts, "hour")}:${findDatePart(parts, "minute")}`;
  const zoneName = findDatePart(parts, "timeZoneName") || zone;
  return {
    label: option.label,
    time,
    meta: option.id === "local" ? `${zoneName} | ${resolvedLocalZone}` : `${zoneName} | ${zone}`,
  };
}

function findDatePart(parts, type) {
  return parts.find((part) => part.type === type)?.value || "";
}

function startTimezoneClock() {
  renderTimezoneStrip();
  renderTimezoneControls();
  if (state.clockTimer) {
    window.clearInterval(state.clockTimer);
  }
  state.clockTimer = window.setInterval(renderTimezoneStrip, 30000);
}

function resolveApiBase() {
  if (window.location.protocol === "file:") {
    return "http://127.0.0.1:8000";
  }
  return "";
}

function resolveInitialLane() {
  // UX8: restore last-used lane from localStorage, then URL hash, then default
  const hash = window.location.hash.replace("#", "").trim().toLowerCase();
  if (hash) {
    return hash;
  }
  try {
    const saved = window.localStorage.getItem("smcr.dashboard.lane");
    if (saved) {
      return saved;
    }
  } catch (_e) {
    console.error("Failed to load saved dashboard lane", _e);
    // storage unavailable
  }
  return "overview";
}

function applyLaneVisibility(moveFocus = false) {
  const active = state.activeLane;

  // A1: aria-selected is valid on role="tab" (which the buttons now have)
  // A2: aria-labelledby on the tabpanel updated to match the active tab id
  for (const button of document.querySelectorAll(".lane-button[role='tab']")) {
    const isActive = button.dataset.lane === active;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  }

  const main = document.getElementById("dashboard-main");
  if (main) {
    main.setAttribute("aria-labelledby", `tab-${active}`);
  }

  for (const section of document.querySelectorAll("[data-section-group]")) {
    const group = section.dataset.sectionGroup;
    const show = group === "global" || group === active;
    section.classList.toggle("is-hidden", !show);
  }

  // UX8: persist active lane across sessions
  try {
    window.localStorage.setItem("smcr.dashboard.lane", active);
  } catch (_e) {
    console.error("Failed to save active dashboard lane", _e);
    // storage unavailable
  }

  // A3: move focus into the panel content on explicit tab switch
  if (moveFocus && main) {
    main.focus();
  }

}

function initializeLaneHistory() {
  const lane = state.activeLane || "overview";
  if (window.history?.replaceState) {
    window.history.replaceState({ lane }, "", laneUrl(lane));
  }
}

function pushLaneHistory(lane) {
  if (!window.history?.pushState) {
    return;
  }
  const currentLane = window.history.state?.lane;
  if (currentLane === lane && window.location.hash === laneUrl(lane)) {
    return;
  }
  window.history.pushState({ lane }, "", laneUrl(lane));
}

function laneUrl(lane) {
  return `#${lane || "overview"}`;
}

function splitLines(value) {
  return String(value || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseSectionUpdates(value) {
  return splitLines(value)
    .map((line) => {
      const index = line.indexOf(":");
      if (index <= 0) {
        return null;
      }
      const section = line.slice(0, index).trim();
      const summary = line.slice(index + 1).trim();
      if (!section || !summary) {
        return null;
      }
      return { section, summary };
    })
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

function escapeAttribute(value) {
  return escapeHtml(value);
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

function currentSectionMemoryEntries() {
  return state.workspace?.section_memory_profile?.entries || [];
}

function sectionMemoryEntryKey(entry) {
  return `${String(entry.section || "").trim().toLowerCase()}::${String(entry.title || "").trim().toLowerCase()}`;
}

function formatSectionMemoryUpdatedAt(value) {
  if (!value) {
    return "Not yet updated";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "Update time unavailable";
  }
  return `Updated ${parsed.toLocaleDateString()}`;
}

function populateSectionMemoryForm(entry = null) {
  const form = document.getElementById("section-memory-form");
  if (!form) {
    return;
  }
  form.dataset.entryKey = entry ? sectionMemoryEntryKey(entry) : "";
  const selectedSection = entry?.section || state.benchSections[0] || DEFAULT_BENCH_SECTIONS[0];
  if (selectedSection && !state.benchSections.includes(selectedSection)) {
    state.benchSections = dedupeBenchSections([...state.benchSections, selectedSection]);
    renderBenchSectionsSelect(selectedSection);
    renderBenchSectionsEditor();
  }
  form.elements.section.value = selectedSection;
  form.elements.title.value = entry?.title || "";
  form.elements.recurring_questions.value = (entry?.recurring_questions || []).join("\n");
  form.elements.recurring_failure_modes.value = (entry?.recurring_failure_modes || []).join("\n");
  form.elements.preferred_checks.value = (entry?.preferred_checks || []).join("\n");
  form.elements.notes.value = (entry?.notes || []).join("\n");
}

async function loadBenchSections() {
  if (state.mode !== "personal" || !state.userKey) {
    state.benchSections = [...DEFAULT_BENCH_SECTIONS];
    renderBenchSectionsSelect();
    renderBenchSectionsEditor();
    return;
  }
  try {
    const config = await apiFetch(`/bench-sections/${encodeURIComponent(state.userKey)}`, { auth: true });
    state.benchSections = dedupeBenchSections(config.sections?.length ? config.sections : DEFAULT_BENCH_SECTIONS);
  } catch (error) {
    if (error.status === 404) {
      state.benchSections = [...DEFAULT_BENCH_SECTIONS];
    } else {
      console.error("Failed to load bench sections", error);
      state.benchSections = [...DEFAULT_BENCH_SECTIONS];
      setWorkspaceNote(error.message, true);
    }
  }
  renderBenchSectionsSelect();
  renderBenchSectionsEditor();
}

async function loadUserProfile() {
  if (state.mode !== "personal" || !state.userKey) {
    return;
  }
  try {
    const profile = await apiFetch(`/user-profile/${encodeURIComponent(state.userKey)}`, { auth: true });
    state.userProfile = profile;
    document.getElementById("profile-billet").value = profile.billet || "";
    document.getElementById("profile-unit").value = profile.unit || "";
    document.getElementById("profile-mos").value = profile.mos || "";
    document.getElementById("profile-format").value = profile.format_preference || "naval_letter";
    document.getElementById("profile-one-priority").checked = profile.one_number_one_rule ?? true;
    document.getElementById("profile-style-notes").value = profile.style_notes || "";
    const exportBtn = document.getElementById("export-profile");
    if (exportBtn) { exportBtn.hidden = false; }
  } catch (error) {
    if (error.status !== 404) {
      console.error("Failed to load user profile", error);
    } else {
      maybePromptFirstRunProfile();
    }
  }
}

function maybePromptFirstRunProfile() {
  const key = `profile_prompted_${state.userKey}`;
  if (localStorage.getItem(key)) {
    return;
  }
  localStorage.setItem(key, "1");
  const drawer = document.getElementById("profile-settings");
  if (drawer && !drawer.open) {
    drawer.open = true;
  }
  const noteEl = document.getElementById("profile-note");
  if (noteEl) {
    noteEl.textContent = "Welcome! Tell us about your billet and unit so we can personalize outputs for you.";
  }
  openLane("configure", "");
}

async function loadHandoff() {
  if (state.mode !== "personal" || !state.userKey) { return; }
  try {
    const handoff = await apiFetch(`/handoffs/${encodeURIComponent(state.userKey)}`, { auth: true });
    document.getElementById("handoff-display-name").value = handoff.display_name || "";
    document.getElementById("handoff-rank").value = handoff.rank || "";
    document.getElementById("handoff-admin-watch").value = (handoff.admin_watch_items || []).join("\n");
    document.getElementById("handoff-drill-notes").value = (handoff.recurring_drill_notes || []).join("\n");
  } catch (err) {
    if (err.status !== 404) { console.error("Failed to load handoff", err); }
    // 404 = no handoff yet, form stays blank — that's the prompt to fill it in
  }
}

async function saveHandoff() {
  if (!state.userKey || state.mode !== "personal") { return; }
  const noteEl = document.getElementById("handoff-note");
  const toLines = (id) => document.getElementById(id).value
    .split("\n").map(s => s.trim()).filter(Boolean);
  const body = {
    user_key: state.userKey,
    display_name: document.getElementById("handoff-display-name").value.trim() || null,
    rank: document.getElementById("handoff-rank").value.trim() || null,
    admin_watch_items: toLines("handoff-admin-watch"),
    recurring_drill_notes: toLines("handoff-drill-notes"),
  };
  try {
    await apiFetch(`/handoffs/${encodeURIComponent(state.userKey)}`, {
      method: "PUT",
      auth: true,
      body: JSON.stringify(body),
    });
    if (noteEl) { noteEl.textContent = "Handoff saved."; setTimeout(() => { noteEl.textContent = ""; }, 3000); }
  } catch (err) {
    if (noteEl) { noteEl.textContent = err.message || "Failed to save handoff."; }
  }
}

async function saveUserProfile() {
  if (!state.userKey || state.mode !== "personal") {
    return;
  }
  const noteEl = document.getElementById("profile-note");
  const body = {
    billet: document.getElementById("profile-billet").value.trim(),
    unit: document.getElementById("profile-unit").value.trim(),
    mos: document.getElementById("profile-mos").value.trim(),
    format_preference: document.getElementById("profile-format").value,
    one_number_one_rule: document.getElementById("profile-one-priority").checked,
    style_notes: document.getElementById("profile-style-notes").value.trim(),
  };
  try {
    const response = await apiFetch(`/user-profile/${encodeURIComponent(state.userKey)}`, {
      method: "PUT",
      auth: true,
      body: JSON.stringify(body),
    });
    state.userProfile = response.profile;
    if (noteEl) { noteEl.textContent = "Preferences saved."; }
    if (body.billet || body.unit || body.mos) {
      if (noteEl) { noteEl.textContent = "Preferences saved. Compiling billet reference…"; }
      await runBilletResearch();
    } else {
      setTimeout(() => { if (noteEl) { noteEl.textContent = ""; } }, 3000);
    }
  } catch (error) {
    if (noteEl) {
      noteEl.textContent = error.message || "Failed to save preferences.";
    }
    console.error("Failed to save user profile", error);
  }
}

async function exportUserProfile() {
  if (!state.userKey || state.mode !== "personal") { return; }
  const noteEl = document.getElementById("profile-note");
  try {
    const blob = await apiFetch(`/user-profile/${encodeURIComponent(state.userKey)}/export`, {
      auth: true,
      blob: true,
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "smcr-profile.json";
    a.click();
    URL.revokeObjectURL(url);
    if (noteEl) { noteEl.textContent = "Profile exported."; setTimeout(() => { noteEl.textContent = ""; }, 3000); }
  } catch (err) {
    if (noteEl) { noteEl.textContent = err.message || "Export failed."; }
  }
}

async function runBilletResearch() {
  const noteEl = document.getElementById("profile-note");
  try {
    const markdown = await apiFetch(`/user-profile/${encodeURIComponent(state.userKey)}/research`, {
      method: "POST",
      auth: true,
      text: true,
    });
    renderBilletResearch(markdown);
    if (noteEl) {
      noteEl.textContent = "Preferences saved. Billet reference compiled.";
      setTimeout(() => { noteEl.textContent = ""; }, 4000);
    }
  } catch (error) {
    console.error("Billet research failed", error);
    if (noteEl) {
      noteEl.textContent = "Preferences saved. (Billet reference unavailable.)";
      setTimeout(() => { noteEl.textContent = ""; }, 4000);
    }
  }
}

async function loadBilletResearch() {
  if (state.mode !== "personal" || !state.userKey) { return; }
  try {
    const markdown = await apiFetch(`/user-profile/${encodeURIComponent(state.userKey)}/research`, {
      auth: true,
      text: true,
    });
    renderBilletResearch(markdown);
  } catch (error) {
    if (error.status !== 404) {
      console.error("Failed to load billet research", error);
    }
  }
}

function renderBilletResearch(markdown) {
  const container = document.getElementById("billet-research-result");
  if (!container) { return; }
  container.innerHTML = simpleMarkdownToHtml(markdown);
  container.hidden = false;
  const rerunBtn = document.getElementById("rerun-research");
  if (rerunBtn) { rerunBtn.hidden = false; }
  const exportBtn = document.getElementById("export-profile");
  if (exportBtn) { exportBtn.hidden = false; }
}

function applyInlineMarkdown(escapedText) {
  return escapedText
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function simpleMarkdownToHtml(markdown) {
  const lines = markdown.split("\n");
  let html = "";
  let inList = false;

  for (const line of lines) {
    if (line.startsWith("# ")) {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<h2 class="research-h1">${escapeHtml(line.slice(2))}</h2>`;
    } else if (line.startsWith("## ")) {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<h3 class="research-h2">${escapeHtml(line.slice(3))}</h3>`;
    } else if (line.startsWith("- ")) {
      if (!inList) { html += "<ul>"; inList = true; }
      html += `<li>${applyInlineMarkdown(escapeHtml(line.slice(2)))}</li>`;
    } else if (line.trim() === "") {
      if (inList) { html += "</ul>"; inList = false; }
    } else {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<p>${applyInlineMarkdown(escapeHtml(line))}</p>`;
    }
  }
  if (inList) { html += "</ul>"; }
  return html;
}

function renderBenchSectionsSelect(selectedValue = "") {
  const select = document.getElementById("bench-section-select");
  if (!select) {
    return;
  }
  const currentValue = selectedValue || select.value;
  const sections = state.benchSections.length ? state.benchSections : DEFAULT_BENCH_SECTIONS;
  select.innerHTML = sections
    .map((section) => `<option value="${escapeAttribute(section)}">${escapeHtml(section)}</option>`)
    .join("");
  select.value = sections.includes(currentValue) ? currentValue : sections[0] || "";
}

function renderBenchSectionsEditor() {
  const target = document.getElementById("bench-sections-list");
  if (!target) {
    return;
  }
  const sections = state.benchSections.length ? state.benchSections : DEFAULT_BENCH_SECTIONS;
  target.classList.toggle("empty-state", sections.length === 0);
  target.innerHTML = sections.length
    ? sections
        .map(
          (section) => `
            <article class="brief-card compact-card">
              <div>
                <strong>${escapeHtml(section)}</strong>
              </div>
              <button type="button" class="secondary" data-bench-section-remove="${escapeAttribute(section)}">Remove</button>
            </article>
          `,
        )
        .join("")
    : "No sections configured.";
}

function toggleBenchSectionsEditor() {
  const editor = document.getElementById("bench-sections-editor");
  const button = document.getElementById("manage-bench-sections");
  if (!editor || !button) {
    return;
  }
  const nextVisible = editor.classList.contains("is-hidden");
  editor.classList.toggle("is-hidden", !nextVisible);
  button.setAttribute("aria-expanded", nextVisible ? "true" : "false");
  renderBenchSectionsEditor();
}

function addBenchSectionFromInput() {
  const input = document.getElementById("bench-section-input");
  const value = input?.value.trim() || "";
  if (!value) {
    setPanelStatus(document.getElementById("bench-sections-editor"), "Add a section label first.", true);
    return;
  }
  state.benchSections = dedupeBenchSections([...state.benchSections, value]);
  if (input) {
    input.value = "";
  }
  renderBenchSectionsSelect(value);
  renderBenchSectionsEditor();
}

async function saveBenchSections(event) {
  const button = event?.currentTarget || document.getElementById("save-bench-sections");
  if (state.mode !== "personal" || !state.userKey) {
    setWorkspaceNote("Open your personal workspace first so section choices stay local to your profile.", true);
    setPanelStatus(document.getElementById("bench-sections-editor"), "Open your personal workspace first.", true);
    return;
  }
  const sections = dedupeBenchSections(state.benchSections);
  await withButtonFeedback(
    button,
    "Saving...",
    "Saved bench sections.",
    async () => {
      const response = await apiFetch(`/bench-sections/${encodeURIComponent(state.userKey)}`, {
        method: "PUT",
        auth: true,
        body: JSON.stringify({ sections }),
      });
      state.benchSections = dedupeBenchSections(response.config?.sections || sections);
      renderBenchSectionsSelect();
      renderBenchSectionsEditor();
      setWorkspaceNote("Bench sections updated.");
    },
    { errorContext: "Failed to save bench sections", statusTarget: document.getElementById("bench-sections-editor") },
  );
}

function removeBenchSection(section) {
  state.benchSections = state.benchSections.filter((item) => item !== section);
  renderBenchSectionsSelect();
  renderBenchSectionsEditor();
}

function dedupeBenchSections(sections) {
  const seen = new Set();
  const result = [];
  for (const section of sections || []) {
    const cleaned = String(section || "").trim();
    const key = cleaned.toLowerCase();
    if (!cleaned || seen.has(key)) {
      continue;
    }
    seen.add(key);
    result.push(cleaned);
  }
  return result;
}

function clearSectionMemoryForm() {
  populateSectionMemoryForm();
}

function editSectionMemoryEntry(entryKey) {
  const entry = currentSectionMemoryEntries().find((item) => sectionMemoryEntryKey(item) === entryKey);
  if (!entry) {
    setWorkspaceNote("Could not find that section-memory entry in the current workspace.", true);
    return;
  }
  populateSectionMemoryForm(entry);
  openLane("library", `Editing section memory for ${entry.section}.`);
}

async function deleteSectionMemoryEntry(entryKey) {
  if (state.mode !== "personal" || !state.userKey) {
    setWorkspaceNote("Open your personal workspace first so section memory stays local to your profile.", true);
    return;
  }
  const nextEntries = currentSectionMemoryEntries().filter((item) => sectionMemoryEntryKey(item) !== entryKey);
  try {
    await apiFetch(`/section-memory/${encodeURIComponent(state.userKey)}`, {
      method: "PUT",
      auth: true,
      body: JSON.stringify({ entries: nextEntries }),
    });
    await loadWorkspace();
    clearSectionMemoryForm();
    setWorkspaceNote("Section-memory entry removed.");
  } catch (error) {
    console.error("Failed to delete section-memory entry", error);
    setWorkspaceNote(error.message, true);
  }
}

function buildSectionMemoryEntryFromForm() {
  const form = new FormData(document.getElementById("section-memory-form"));
  return {
    section: String(form.get("section") || "").trim(),
    title: String(form.get("title") || "").trim(),
    recurring_questions: splitLines(form.get("recurring_questions")),
    recurring_failure_modes: splitLines(form.get("recurring_failure_modes")),
    preferred_checks: splitLines(form.get("preferred_checks")),
    notes: splitLines(form.get("notes")),
  };
}

async function saveSectionMemoryProfile(button = null) {
  if (state.mode !== "personal" || !state.userKey) {
    setWorkspaceNote("Open your personal workspace first so section memory stays local to your profile.", true);
    setPanelStatus(button || document.getElementById("section-memory-form"), "Open your personal workspace first so section memory stays local to your profile.", true);
    return;
  }
  const form = document.getElementById("section-memory-form");
  const entry = buildSectionMemoryEntryFromForm();
  if (!entry.section || !entry.title) {
    setWorkspaceNote("Section lane and memory title are required.", true);
    setPanelStatus(button || form, "Section lane and memory title are required.", true);
    return;
  }
  const currentEntries = currentSectionMemoryEntries();
  const existingKey = form.dataset.entryKey || "";
  const nextEntries = currentEntries.filter((item) => sectionMemoryEntryKey(item) !== existingKey);
  nextEntries.push(entry);
  await withButtonFeedback(
    button,
    "Saving...",
    `Saved section memory for ${entry.section}.`,
    async () => {
      await apiFetch(`/section-memory/${encodeURIComponent(state.userKey)}`, {
        method: "PUT",
        auth: true,
        body: JSON.stringify({ entries: nextEntries }),
      });
      await loadWorkspace();
      populateSectionMemoryForm(entry);
      setWorkspaceNote(`Saved section memory for ${entry.section}.`);
    },
    { errorContext: "Failed to save section memory", statusTarget: form },
  );
}

function encodeSectionMemorySeed(seed) {
  return encodeURIComponent(JSON.stringify(seed));
}

function decodeSectionMemorySeed(value) {
  return JSON.parse(decodeURIComponent(value));
}

function seedSectionMemoryEntry(encodedSeed) {
  try {
    const seed = decodeSectionMemorySeed(encodedSeed);
    populateSectionMemoryForm(seed);
    openLane("library", `Loaded a section-memory starter for ${seed.section}.`);
  } catch (_error) {
    console.error("Failed to decode section-memory starter", _error);
    setWorkspaceNote("Could not load that section-memory starter.", true);
  }
}

applyLaneVisibility();
initializeLaneHistory();
initOnboardingState();
initQuickLinksForm();
loadWorkspace();
startTimezoneClock();
startLastUpdatedClock();
