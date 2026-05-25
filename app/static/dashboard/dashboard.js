const state = {
  mode: "demo",
  userKey: "",
  apiKey: "",
  activeLane: resolveInitialLane(),
  workspace: null,
  selectedDocumentId: null,
  selectedReadingSlug: "",
  selectedReferenceSlug: "",
  historyLibrary: [],
  selectedHistoryMonth: "",
  selectedHistoryDay: "",
  apiBase: resolveApiBase(),
  timezoneOptions: buildTimezoneOptions(),
  selectedTimezoneIds: loadTimezoneSelection(),
  timezonePanelOpen: false,
  clockTimer: null,
};

const DOCUMENT_TYPE_OPTIONS = [
  "reference_note",
  "doctrine",
  "admin_reference",
  "training_reference",
  "uniform_photo",
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

document.getElementById("section-memory-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await saveSectionMemoryProfile();
});

document.getElementById("clear-section-memory-form").addEventListener("click", () => {
  clearSectionMemoryForm();
  setWorkspaceNote("Section-memory form cleared.");
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

document.getElementById("uniform-photo-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await runUniformPhotoReview(event.currentTarget);
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
    supported_echelon: "company",
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
  const form = new FormData(event.currentTarget);
  const supportAndCivil = splitLines(form.get("support_requirements"));
  const payload = {
    title: form.get("title"),
    supported_unit: form.get("supported_unit"),
    supported_echelon: "company",
    event_type: form.get("event_type") || "training_event",
    mission_or_training_goal: form.get("mission_or_training_goal"),
    time_available: form.get("time_available") || null,
    commander_priorities: splitLines(form.get("commander_priorities")),
    higher_guidance: splitLines(form.get("higher_guidance")),
    constraints: splitLines(form.get("higher_guidance")),
    coordinating_sections: splitLines(form.get("coordinating_sections")),
    support_requirements: supportAndCivil,
    civil_considerations: supportAndCivil,
    section_updates: parseSectionUpdates(form.get("section_updates")),
    training_only: true,
  };
  const data = await apiFetch("/staff/planning-cell", { method: "POST", body: JSON.stringify(payload) });
  renderPlanningCellOutput("planning-cell-output", data);
});

document.getElementById("refresh-maradmins").addEventListener("click", () => refreshSourceLane("maradmins"));
document.getElementById("refresh-reading").addEventListener("click", () => refreshSourceLane("reading"));
document.getElementById("refresh-navadmins").addEventListener("click", () => refreshSourceLane("navadmins"));
document.getElementById("refresh-alnavs").addEventListener("click", () => refreshSourceLane("alnavs"));
document.getElementById("refresh-dod-watch").addEventListener("click", () => refreshSourceLane("dod"));
document.getElementById("refresh-source-watch").addEventListener("click", () => refreshSourceLane("all"));
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
document.getElementById("reading-book-select").addEventListener("change", (event) => {
  state.selectedReadingSlug = event.target.value || "";
  renderReadingBooks(state.workspace?.reading_books || []);
});
document.getElementById("reference-select").addEventListener("change", (event) => {
  state.selectedReferenceSlug = event.target.value || "";
  renderReferenceLibrary(state.workspace?.reference_library || []);
});
document.getElementById("history-library-show-date").addEventListener("click", () => {
  renderHistoryLibrary(state.historyLibrary);
});
document.getElementById("history-library-use-today").addEventListener("click", () => {
  setHistoryLibraryToToday();
});
document.getElementById("save-document-type").addEventListener("click", () => {
  saveSelectedDocumentType();
});
document.getElementById("apply-document-suggestion").addEventListener("click", () => {
  applySuggestedDocumentType();
});
document.getElementById("history-library-month").addEventListener("change", (event) => {
  state.selectedHistoryMonth = event.target.value || "";
});
document.getElementById("history-library-day").addEventListener("change", (event) => {
  state.selectedHistoryDay = event.target.value || "";
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
  .getElementById("draft-open-planning-cell")
  .addEventListener("click", () => launchThinStaffWorkflow("planning-cell"));
document
  .getElementById("draft-open-brief-clinic")
  .addEventListener("click", () => launchWalkInWorkflow("brief-clinic"));
document
  .getElementById("workflow-open-lone-planner")
  .addEventListener("click", () => launchThinStaffWorkflow("lone-planner"));
document
  .getElementById("workflow-open-planning-cell")
  .addEventListener("click", () => launchThinStaffWorkflow("planning-cell"));
document
  .getElementById("workflow-open-brief-clinic")
  .addEventListener("click", () => launchWalkInWorkflow("brief-clinic"));
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
    await saveReadingProgress(saveButton.dataset.readingSave);
  }

  const timezoneToggle = event.target.closest("[data-timezone-option]");
  if (timezoneToggle) {
    updateTimezoneSelection(timezoneToggle.dataset.timezoneOption, timezoneToggle.checked);
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
  renderTickerStack("navadmin-ticker", payload.navadmin_ticker || [], "No NAVADMIN items loaded yet.");
  renderTickerStack("alnav-ticker", payload.alnav_ticker || [], "No ALNAV items loaded yet.");
  renderTickerStack("dod-ticker", payload.dod_ticker || [], "No DoD watch items loaded yet.");
  renderCustomWatchFeeds(payload.custom_watch_feeds || []);
  renderHistory(payload.today_in_history || []);
  renderHistoryLibrary(payload.history_library || []);
  renderReferenceLibrary(payload.reference_library || []);
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
  renderQueue(items, payload.battle_rhythm_health?.hot_items || []);
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

function renderThinStaffAssist(payload) {
  renderList("thin-staff-walk-in", payload.walk_in_brief || []);
  renderList("thin-staff-blind-spots", payload.likely_blind_spots || []);
  renderList("thin-staff-questions", payload.missing_section_questions || []);
  renderList("thin-staff-products", payload.recommended_products || []);
  renderList("thin-staff-changes", payload.changes_since_last_time || []);
  renderEntryRows(
    "thin-staff-next-touchpoint",
    payload.next_touchpoint ? [{ title: payload.next_touchpoint, category: "touchpoint" }] : [],
    "No touchpoint loaded yet.",
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

async function launchThinStaffWorkflow(mode) {
  if (!state.workspace) {
    setWorkspaceNote("Load a workspace first so the launch can use current context.", true);
    return;
  }

  if (mode === "admin") {
    state.activeLane = "overview";
    applyLaneVisibility();
    document.getElementById("admin-summary")?.scrollIntoView({ behavior: "smooth", block: "start" });
    setWorkspaceNote("Jumped to admin readiness.");
    return;
  }

  primeThinStaffForms();
  state.activeLane = "draft";
  applyLaneVisibility();

  if (mode === "update-cycle") {
    document.getElementById("staff-cycle-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
    setWorkspaceNote("Opened the staff update cycle with current workspace context.");
    return;
  }

  document.getElementById("planning-cell-form")?.scrollIntoView({ behavior: "smooth", block: "start" });

  if (mode === "planning-cell") {
    setWorkspaceNote("Opened the planning cell with current workspace context.");
    return;
  }

  if (mode === "lone-planner") {
    await runLonePlannerMode();
    setWorkspaceNote("Ran lone planner mode from the thin-staff assist lane.");
    return;
  }

  if (mode === "mission-analysis") {
    const payload = buildPlanningCellPayloadFromForm();
    const data = await apiFetch("/staff/mission-analysis", { method: "POST", body: JSON.stringify(payload) });
    renderMissionAnalysisOutput("planning-cell-output", data);
    setWorkspaceNote("Ran mission analysis from the thin-staff assist lane.");
  }
}

function launchWalkInWorkflow(mode) {
  state.activeLane = "draft";
  applyLaneVisibility();
  if (mode === "brief-clinic") {
    document.getElementById("brief-clinic-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
    setWorkspaceNote("Opened brief clinic from the walk-in brief pack.");
    return;
  }
  document.getElementById("run-lone-planner")?.scrollIntoView({ behavior: "smooth", block: "start" });
  setWorkspaceNote("Opened lone planner mode from the walk-in brief pack.");
}

function openBattleRhythmEditor() {
  state.activeLane = "draft";
  applyLaneVisibility();
  document.getElementById("battle-rhythm-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
  setWorkspaceNote("Opened the battle rhythm editor.");
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
  const supportAndCivil = splitLines(form.get("support_requirements"));
  return {
    user_key: state.mode === "personal" && state.userKey ? state.userKey : null,
    title: form.get("title"),
    supported_unit: form.get("supported_unit"),
    supported_echelon: "company",
    event_type: form.get("event_type") || "training_event",
    mission_or_training_goal: form.get("mission_or_training_goal"),
    time_available: form.get("time_available") || null,
    commander_priorities: splitLines(form.get("commander_priorities")),
    higher_guidance: splitLines(form.get("higher_guidance")),
    constraints: splitLines(form.get("higher_guidance")),
    coordinating_sections: splitLines(form.get("coordinating_sections")),
    support_requirements: supportAndCivil,
    civil_considerations: supportAndCivil,
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
  const typeSelect = document.getElementById("document-type-select");
  const typeButton = document.getElementById("save-document-type");
  const suggestionButton = document.getElementById("apply-document-suggestion");
  const suggestionNote = document.getElementById("document-type-suggestion");
  if (!items.length) {
    target.className = "document-library empty-state";
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
    target.innerHTML = `
      <p>No local document previews loaded yet.</p>
      <p class="helper-text">Open your personal workspace to review orders, BIO, RQS, receipts, and other local references here.</p>
    `;
    return;
  }
  if (!state.selectedDocumentId || !items.some((item) => item.context_id === state.selectedDocumentId)) {
    state.selectedDocumentId = items[0].context_id;
  }
  const selected = items.find((item) => item.context_id === state.selectedDocumentId) || items[0];
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
    setWorkspaceNote(data.message || "File category updated.");
    await loadWorkspace();
  } catch (error) {
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
    target.innerHTML = `
      <p>No templates are loaded yet.</p>
      <p class="helper-text">User-saved examples and reusable staff scaffolds will appear here once you promote them into the local template repo.</p>
    `;
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
    target.innerHTML = `
      <p>No recurring section memory is stored yet.</p>
      <p class="helper-text">Start with the section your reserve bench misses most often. This is meant to sharpen lone-planner and gap-cover outputs over time.</p>
    `;
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
          <div class="button-row compact-controls">
            <button type="button" class="secondary" data-section-memory-edit="${escapeHtml(entryKey)}">Edit</button>
            <button type="button" class="secondary" data-section-memory-delete="${escapeHtml(entryKey)}">Delete</button>
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
    summary.textContent = "No reference notes loaded yet.";
    selector.innerHTML = '<option value="">No reference notes loaded yet.</option>';
    selector.disabled = true;
    target.className = "reading-detail empty-state";
    target.innerHTML = `
      <p>No reference notes loaded yet.</p>
      <p class="helper-text">Curated doctrine and staff-source notes from the repo will appear here.</p>
    `;
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
  renderTickerStack("maradmin-ticker", items, "No source-watch items loaded yet.");
}

function renderCustomWatchFeeds(items) {
  const target = document.getElementById("custom-feed-watch");
  if (!items.length) {
    target.className = "row-stack empty-state";
    target.innerHTML = `
      <p>No custom watch feeds are configured yet.</p>
      <p class="helper-text">This lane is for local-only RSS watches like unit pages, PME sources, or professional feeds you want to keep in your off-drill scan.</p>
    `;
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

function renderHistoryLibrary(items) {
  state.historyLibrary = Array.isArray(items) ? items : [];
  const monthSelect = document.getElementById("history-library-month");
  const daySelect = document.getElementById("history-library-day");
  const summary = document.getElementById("history-library-summary");
  const target = document.getElementById("history-library-results");
  const today = new Date();

  if (!state.selectedHistoryMonth) {
    state.selectedHistoryMonth = String(today.getMonth() + 1);
  }
  if (!state.selectedHistoryDay) {
    state.selectedHistoryDay = String(today.getDate());
  }

  populateHistoryMonthOptions(monthSelect, state.selectedHistoryMonth);
  populateHistoryDayOptions(daySelect, state.selectedHistoryDay);

  if (!state.historyLibrary.length) {
    summary.textContent = "No history library entries loaded yet.";
    target.className = "row-stack empty-state";
    target.textContent = "No history library entries loaded yet.";
    return;
  }

  const month = Number(state.selectedHistoryMonth || today.getMonth() + 1);
  const day = Number(state.selectedHistoryDay || today.getDate());
  const filtered = state.historyLibrary.filter((item) => item.month === month && item.day === day);
  summary.textContent = `${state.historyLibrary.length} history item(s) loaded. Showing ${filtered.length} for ${formatHistoryMonth(month)} ${day}.`;
  if (!filtered.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No history entries are stored for that date yet.";
    return;
  }
  target.className = "row-stack";
  target.innerHTML = filtered
    .map(
      (item) => `
        <article class="data-row">
          <div class="data-row-head">
            <span class="strip-label">${escapeHtml(item.year_label)}</span>
            <strong>${escapeHtml(item.title)}</strong>
          </div>
          <p>${escapeHtml(item.summary)}</p>
          ${
            (item.references || []).length
              ? `<p class="meta-inline">${escapeHtml(item.references[0])}</p>`
              : ""
          }
        </article>
      `,
    )
    .join("");
}

function renderReadingBooks(items) {
  const summary = document.getElementById("reading-summary");
  const selector = document.getElementById("reading-book-select");
  const target = document.getElementById("reading-library");
  if (!items.length) {
    summary.textContent = "No reading-list entries loaded yet.";
    selector.innerHTML = '<option value="">No reading-list entries loaded yet.</option>';
    selector.disabled = true;
    target.className = "reading-detail empty-state";
    target.textContent = "No reading-list entries loaded yet.";
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

function populateHistoryMonthOptions(select, selectedValue) {
  const months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  select.innerHTML = months
    .map(
      (label, index) =>
        `<option value="${index + 1}" ${String(index + 1) === String(selectedValue) ? "selected" : ""}>${escapeHtml(label)}</option>`,
    )
    .join("");
}

function populateHistoryDayOptions(select, selectedValue) {
  select.innerHTML = Array.from({ length: 31 }, (_, index) => index + 1)
    .map(
      (day) =>
        `<option value="${day}" ${String(day) === String(selectedValue) ? "selected" : ""}>${day}</option>`,
    )
    .join("");
}

function setHistoryLibraryToToday() {
  const today = new Date();
  state.selectedHistoryMonth = String(today.getMonth() + 1);
  state.selectedHistoryDay = String(today.getDate());
  renderHistoryLibrary(state.historyLibrary);
  setWorkspaceNote("History library set to today.");
}

function formatHistoryMonth(month) {
  const months = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  return months[month] || "Unknown";
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

function renderTickerStack(targetId, items, emptyText) {
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

function renderQueue(items, hotItems = []) {
  const target = document.getElementById("priority-queue");
  const normalizedItems = Array.isArray(items) ? items : [];
  const normalizedHotItems = Array.isArray(hotItems) ? hotItems : [];
  const combined = buildActionStack(normalizedItems, normalizedHotItems);
  if (!combined.length) {
    target.className = "row-stack empty-state";
    target.textContent = "No priority items returned yet.";
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

function renderUniformPhotoReviewOutput(targetId, payload) {
  const target = document.getElementById(targetId);
  target.className = "tool-output";
  target.innerHTML = `
    <section>
      <span class="strip-label">${escapeHtml(payload.review_posture || "Uniform review")}</span>
      <h3>${escapeHtml(payload.filename || "Uploaded photo")}</h3>
      <p>${escapeHtml(`Uniform type: ${payload.uniform_type || "unknown"}${payload.event_context ? ` | Event: ${payload.event_context}` : ""}`)}</p>
      <p class="meta-inline">Local context ID: ${escapeHtml(payload.photo_context_id || "not stored")}</p>
    </section>
    <section>
      <span class="strip-label">Summary</span>
      <ul>${(payload.summary_lines || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No summary returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">What to verify in the image</span>
      <ul>${(payload.what_to_verify_in_image || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No verification items returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Grooming checks</span>
      <ul>${(payload.grooming_checks || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No grooming checks returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Likely issue areas</span>
      <ul>${(payload.likely_issue_areas || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No issue areas returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Follow-up actions</span>
      <ul>${(payload.follow_up_actions || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No follow-up actions returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Warnings</span>
      <ul>${(payload.warnings || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>No warnings returned.</li>"}</ul>
    </section>
    <section>
      <span class="strip-label">Official sources</span>
      <ul>${(payload.structured_citations || [])
        .map(
          (item) =>
            `<li><a href="${escapeAttribute(item.url || "#")}" target="_blank" rel="noreferrer">${escapeHtml(item.title || item.url || "Source")}</a></li>`,
        )
        .join("") || "<li>No sources returned.</li>"}</ul>
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
    setWorkspaceNote(error.message, true);
  }
}

async function runLonePlannerMode() {
  try {
    const payload = buildPlanningCellPayloadFromForm();
    const data = await apiFetch("/staff/lone-planner", { method: "POST", body: JSON.stringify(payload) });
    renderLonePlannerOutput("lone-planner-output", data);
    state.activeLane = "draft";
    applyLaneVisibility();
    document.getElementById("lone-planner-output")?.scrollIntoView({ behavior: "smooth", block: "start" });
    setWorkspaceNote("Lone planner mode ran against the current planning context.");
  } catch (error) {
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
    state.activeLane = "draft";
    applyLaneVisibility();
    document.getElementById("section-gap-cover-output")?.scrollIntoView({ behavior: "smooth", block: "start" });
    setWorkspaceNote("Built assisted section estimates from the current planning context.");
  } catch (error) {
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
  state.activeLane = "draft";
  applyLaneVisibility();
  form.scrollIntoView({ behavior: "smooth", block: "start" });
  setWorkspaceNote(`Opened the ${item.label} lane.`);
}

function openLane(lane, message = "") {
  state.activeLane = lane;
  applyLaneVisibility();
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
    setWorkspaceNote(error.message, true);
  }
}

async function refreshSourceLane(lane) {
  if (state.mode !== "personal") {
    setWorkspaceNote("Open your personal workspace to refresh local source watches.", true);
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
  try {
    for (const [path, method] of sequence) {
      await apiFetch(path, { method, auth: true });
    }
    setWorkspaceNote(
      lane === "all" ? "Source-watch stack refreshed." : `${lane.replaceAll("-", " ")} refreshed.`,
    );
    await loadWorkspace();
  } catch (error) {
    setWorkspaceNote(error.message, true);
  }
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

async function runUniformPhotoReview(formElement) {
  if (state.mode !== "personal") {
    setWorkspaceNote("Open your personal workspace to upload and review a uniform photo.", true);
    return;
  }
  const form = new FormData(formElement);
  const photo = form.get("uniform_photo");
  if (!(photo instanceof File) || !photo.name) {
    setWorkspaceNote("Choose a uniform photo first.", true);
    return;
  }
  const headers = {};
  if (state.apiKey) {
    headers["X-Local-API-Key"] = state.apiKey;
  }
  try {
    const response = await fetch(`${state.apiBase}/uniform/photo-review`, {
      method: "POST",
      headers,
      body: form,
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`Request failed (${response.status}): ${text}`);
    }
    const data = await response.json();
    renderUniformPhotoReviewOutput("uniform-photo-output", data);
    setWorkspaceNote("Uniform photo review completed and stored as local context.");
    await loadWorkspace();
  } catch (error) {
    setWorkspaceNote(error.message, true);
  }
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

function toggleTimezonePanel() {
  state.timezonePanelOpen = !state.timezonePanelOpen;
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

function updateTimezoneSelection(optionId, checked) {
  const next = checked
    ? [...new Set([...state.selectedTimezoneIds, optionId])]
    : state.selectedTimezoneIds.filter((id) => id !== optionId);
  state.selectedTimezoneIds = next.length ? next : ["local", "zulu", "quantico"];
  try {
    window.localStorage.setItem("smcr.dashboard.timezones", JSON.stringify(state.selectedTimezoneIds));
  } catch (_error) {
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
  const lane = window.location.hash.replace("#", "").trim().toLowerCase();
  return lane || "overview";
}

function applyLaneVisibility() {
  const active = state.activeLane;
  for (const button of document.querySelectorAll(".lane-button")) {
    const isActive = button.dataset.lane === active;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
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
  form.elements.section.value = entry?.section || "S-1/Admin";
  form.elements.title.value = entry?.title || "";
  form.elements.recurring_questions.value = (entry?.recurring_questions || []).join("\n");
  form.elements.recurring_failure_modes.value = (entry?.recurring_failure_modes || []).join("\n");
  form.elements.preferred_checks.value = (entry?.preferred_checks || []).join("\n");
  form.elements.notes.value = (entry?.notes || []).join("\n");
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
  state.activeLane = "library";
  applyLaneVisibility();
  document.getElementById("section-memory-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
  setWorkspaceNote(`Editing section memory for ${entry.section}.`);
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

async function saveSectionMemoryProfile() {
  if (state.mode !== "personal" || !state.userKey) {
    setWorkspaceNote("Open your personal workspace first so section memory stays local to your profile.", true);
    return;
  }
  const form = document.getElementById("section-memory-form");
  const entry = buildSectionMemoryEntryFromForm();
  if (!entry.section || !entry.title) {
    setWorkspaceNote("Section lane and memory title are required.", true);
    return;
  }
  const currentEntries = currentSectionMemoryEntries();
  const existingKey = form.dataset.entryKey || "";
  const nextEntries = currentEntries.filter((item) => sectionMemoryEntryKey(item) !== existingKey);
  nextEntries.push(entry);
  try {
    await apiFetch(`/section-memory/${encodeURIComponent(state.userKey)}`, {
      method: "PUT",
      auth: true,
      body: JSON.stringify({ entries: nextEntries }),
    });
    await loadWorkspace();
    populateSectionMemoryForm(entry);
    setWorkspaceNote(`Saved section memory for ${entry.section}.`);
  } catch (error) {
    setWorkspaceNote(error.message, true);
  }
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
    state.activeLane = "library";
    applyLaneVisibility();
    document.getElementById("section-memory-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
    setWorkspaceNote(`Loaded a section-memory starter for ${seed.section}.`);
  } catch (_error) {
    setWorkspaceNote("Could not load that section-memory starter.", true);
  }
}

loadWorkspace();
applyLaneVisibility();
startTimezoneClock();
