"""Second-generation dashboard repairs, applied after the legacy export patches."""

import re
from pathlib import Path

MARKER = "// Dashboard integrity repair: persisted journal and explicit workspace identity."


def refresh_methods(inner: str) -> str:
    methods = Path(__file__).with_name("dashboard_integrity_methods.js").read_text(encoding="utf-8")
    source_starts = list(re.finditer(r"^  (?:async )?(\w+)\([^\n]*\) \{", methods, re.M))
    for index, match in enumerate(source_starts):
        name = match.group(1)
        body = methods[match.start():source_starts[index + 1].start() if index + 1 < len(source_starts) else len(methods)]
        old_match = re.search(r"^  (?:async )?" + re.escape(name) + r"\([^\n]*\) \{", inner, re.M)
        if old_match:
            next_method = re.search(r"^  (?:(?:async|static) )?\w+\([^\n]*\) \{", inner[old_match.end():], re.M)
            if next_method is None:
                raise ValueError(f"Missing method boundary for {name}")
            end = old_match.end() + next_method.start()
            inner = inner[:old_match.start()] + body + inner[end:]
        else:
            if inner.count("  componentDidMount() {") != 1:
                raise ValueError("Missing component mount anchor")
            inner = inner.replace("  componentDidMount() {", body + "  componentDidMount() {", 1)
    return inner


def hoist_identity_snapshots(inner: str) -> str:
    """Move `const requestKey/modeVersion` to the top of any loader that uses them earlier.

    Older bundles injected the snapshot just before `try {`, which is after a
    leading `this.setState({ ...: "Loading…" })` guard in a few loaders and
    throws "Cannot access 'requestKey' before initialization" at runtime.
    Idempotent: once hoisted, the condition no longer matches.
    """
    decl = "    const requestKey = this.userKey;\n    const modeVersion = this._modeVersion;\n"
    check = "requestKey !== this.userKey"
    for match in reversed(list(re.finditer(r"^  (?:async )?\w+\([^\n]*\) \{\n", inner, re.M))):
        end_match = re.search(r"^  (?:(?:async|static) )?\w+\([^\n]*\) \{", inner[match.end():], re.M)
        end = match.end() + (end_match.start() if end_match else len(inner) - match.end())
        block = inner[match.end():end]
        if block.startswith(decl + _RESOLVE_LINE):
            # An earlier hoist put the snapshot ahead of key resolution; swap them.
            block = _RESOLVE_LINE + decl + block[len(decl) + len(_RESOLVE_LINE):]
            inner = inner[:match.end()] + block + inner[end:]
            continue
        use, declared = block.find(check), block.find(decl)
        if use == -1 or declared == -1 or declared < use:
            continue
        block = block.replace(decl, "", 1)
        # Snapshot identity after the user key is resolved, not before.
        offset = len(_RESOLVE_LINE) if block.startswith(_RESOLVE_LINE) else 0
        block = block[:offset] + decl + block[offset:]
        inner = inner[:match.end()] + block + inner[end:]
    return inner


_RESOLVE_LINE = "    if (!this.userKey) this.userKey = this._resolveUserKey();\n"


def finish_repairs(inner: str) -> str:
    inner = re.sub(r'<sc-raw-select value="{{ f.type }}".*?</sc-raw-select>', '<span>Source URL</span>', inner, count=1, flags=re.S)
    for method, category, next_method in (("createWorkflowDoc", "generations", "linkCounselingToFitrep"), ("newFitrep", "fitreps", "updateFitrepField")):
        start = inner.index(f"  {method}(")
        end = inner.index(f"  {next_method}(", start)
        block = inner[start:end]
        if '      fetch(' in block:
            block = block[:block.index('      fetch(')] + f'      this._createPendingDocument("{category}", tempId);\n    }};\n  }}\n'
            inner = inner[:start] + block + inner[end:]
    inner = inner.replace('>Retry workspace save / load</button>', '>{{ retryEditorLabel }}</button>')
    if 'retryEditorLabel: "Retry workspace save / load"' not in inner:
        inner = inner.replace('      profilePasskey: this.state.profilePasskey,', '      retryEditorLabel: "Retry workspace save / load",\n      profilePasskey: this.state.profilePasskey,', 1)
    for field in ("Title", "Body"):
        old = f'on{field}Change: (e) => this.setState({{ draft{field}: e.target.value }}),'
        new = f'on{field}Change: (e) => {{ this._noteDirty = true; this._documentDirty = true; this.setState({{ draft{field}: e.target.value, documentSaveStatus: "Unsaved note. Choose Save to keep your changes." }}); }},'
        inner = inner.replace(old, new)
    if 'aria-label="Staff editor save status"' not in inner:
        inner = inner.replace('<textarea rows="8" value="{{ staffLaneNote }}"', '<div aria-label="Staff editor save status"><span role="status">{{ editorSaveStatus }}</span><button type="button" sc-camel-on-click="{{ retryEditorSave }}">Retry workspace save / load</button></div>\n            <textarea rows="8" value="{{ staffLaneNote }}"', 1)
    inner = inner.replace('<button type="button" sc-camel-on-click="{{ retryEditorSave }}">', '<button aria-label="Retry workspace save / load" type="button" sc-camel-on-click="{{ retryEditorSave }}">')
    inner = hoist_identity_snapshots(inner)
    if 'documentSaveStatus: this.state.documentSaveStatus' not in inner:
        inner = inner.replace('      profilePasskey: this.state.profilePasskey,', '      documentSaveStatus: this.state.documentSaveStatus || "",\n      retryDocumentSaves: () => this.retryDocumentSaves(),\n      profilePasskey: this.state.profilePasskey,', 1)
    if 'aria-label="Document save status"' not in inner:
        inner = inner.replace('  <!-- ============ LANE NAV ============ -->', '  <div aria-label="Document save status" style="padding:8px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;"><span role="status">{{ documentSaveStatus }}</span><button type="button" sc-camel-on-click="{{ retryDocumentSaves }}">Retry document saves</button></div>\n  <!-- ============ LANE NAV ============ -->', 1)
    mobile_css = Path(__file__).with_name("dashboard_mobile.css").read_text(encoding="utf-8")
    mobile_tag = '<style id="dashboard-mobile-repairs">' + mobile_css + '</style>'
    if '<style id="dashboard-mobile-repairs">' in inner:
        inner = re.sub(r'<style id="dashboard-mobile-repairs">.*?</style>', lambda _: mobile_tag, inner, count=1, flags=re.S)
    else:
        inner = inner.replace('</head>', mobile_tag + '\n</head>', 1)
    inner = inner.replace('if (this.state.handoffDirty) { event.preventDefault();', 'if (this.state.handoffDirty || this._editorDirty || this._documentDirty) { event.preventDefault();')
    anchor = '    if (first) this.setState({ activeNoteId: first.id, draftTitle: first.title, draftBody: first.body });\n'
    if '    this._installEditorPersistence();' not in inner:
        inner = inner.replace(anchor, anchor + '    this._installEditorPersistence();\n', 1)
    if 'editorSaveStatus: this.state.editorSaveStatus' not in inner:
        inner = inner.replace('      profilePasskey: this.state.profilePasskey,', '      editorSaveStatus: this.state.editorSaveStatus || "Loading workspace editors…",\n      retryEditorSave: () => this._editorsLoaded ? this._saveEditorState() : this._loadEditorState(),\n      profilePasskey: this.state.profilePasskey,', 1)
    if 'aria-label="Workspace save status"' not in inner:
        inner = inner.replace('  <!-- ============ LANE NAV ============ -->', '  <div aria-label="Workspace save status" style="padding:8px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;"><span role="status">{{ editorSaveStatus }}</span><button type="button" sc-camel-on-click="{{ retryEditorSave }}">Retry workspace save / load</button></div>\n  <!-- ============ LANE NAV ============ -->', 1)
    inner = inner.replace('profilePasskey: "",', 'profilePasskey: sessionStorage.getItem("smcr_access_key") || "",')
    inner = inner.replace('onPasskeyChange: (e) => this.setState({ profilePasskey: e.target.value }),', 'onPasskeyChange: (e) => { sessionStorage.setItem("smcr_access_key", e.target.value); this.setState({ profilePasskey: e.target.value }); },')
    inner = inner.replace('placeholder="Leave blank for no lock"', 'aria-label="Local access passkey" placeholder="Enter the configured passkey"')
    inner = inner.replace('Local-only, matches the LOCAL_API_KEY in your .env. This does not send data anywhere.', 'Used for requests to this local server. Stored in this tab only; changing it does not change the server passkey. Reload after correcting it.')
    inner = inner.replace('"Updated " + this.state.feedUpdated', 'this.state.feedUpdated === "not refreshed in this session" ? "Not refreshed in this session" : "Updated " + this.state.feedUpdated') if '"Not refreshed in this session"' not in inner else inner
    for field, label in (("Admin", "Admin watch items (one per line)"), ("Drill", "Recurring drill notes (one per line)")):
        old = f'<textarea rows="4" value="{{{{ activeHandoff{field} }}}}"'
        new = f'<textarea aria-label="{label}" rows="4" value="{{{{ activeHandoff{field} }}}}"'
        inner = inner.replace(old, new)
        inner = inner.replace(f'<textarea aria-label="{label}"', f'<textarea disabled="{{{{ handoffUnavailable }}}}" aria-label="{label}"')
    inner = inner.replace('<input aria-label="Handoff title"', '<input disabled="{{ handoffUnavailable }}" aria-label="Handoff title"')
    for binding in ("saveHandoff", "newHandoff", "archiveHandoff", "unarchiveHandoff", "deleteHandoff"):
        old = f'<button type="button" sc-camel-on-click="{{{{ {binding} }}}}"'
        inner = inner.replace(old, f'<button disabled="{{{{ handoffUnavailable }}}}" type="button" sc-camel-on-click="{{{{ {binding} }}}}"')
    # These sample rows must never flash on first render or remain after a load error.
    for field in ("actions", "gearItems"):
        inner = re.sub(rf"^    {field}: \[\n.*?^    \],", f"    {field}: [],", inner, count=1, flags=re.M | re.S)
    # Projects are shared on disk, but demo visibility belongs to the current mode.
    start = inner.index("  async _loadRealProjects(")
    end = inner.index("  async _loadRealAgents(", start)
    block = inner[start:end]
    if "const modeVersion" not in block:
        block = block.replace("    try {", "    const modeVersion = this._modeVersion;\n    try {", 1)
        block = block.replace("this.setState(", "if (modeVersion !== this._modeVersion) return;\n      this.setState(")
        inner = inner[:start] + block + inner[end:]
    # Scope the hero action to its section: another DTS link exists in Profile.
    start = inner.index("      <!-- READINESS HERO -->")
    end = inner.index("      <!-- ACT NOW", start)
    hero = inner[start:end]
    hero = hero.replace('>Readiness posture</div>', '>Workspace summary</div>').replace('>Decisive action now</div>', '>Next action to review</div>')
    hero = re.sub(r'<a href="https://dtsproweb.defensetravel.osd.mil"[^\n]+</a>', '<button type="button" sc-camel-on-click="{{ goWatch }}" style="margin-top:14px;padding:8px 16px;background:#b21f2d;color:#fff;border:0;border-radius:6px;cursor:pointer;">Review tracked actions</button>', hero)
    inner = inner[:start] + hero + inner[end:]
    # Nested options inside sc-raw-select render without labels in this export.
    # The existing API accepts a project name and can create its folder safely.
    inner = re.sub(
        r'<sc-raw-select value="{{ d.moveTarget }}".*?</sc-raw-select>',
        '<input aria-label="Project folder for {{ d.title }}" value="{{ d.moveTarget }}" sc-camel-on-change="{{ d.onMoveTargetChange }}" placeholder="Project name (existing or new)" style="min-width:0;max-width:220px;height:32px;border:1px solid #313844;border-radius:5px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.8rem;">',
        inner, count=1, flags=re.S,
    )
    return inner


def patch_integrity(inner: str) -> str:
    if MARKER in inner:
        return apply_ai_page_patches(finish_repairs(refresh_methods(inner)))

    def replace(old: str, new: str) -> None:
        nonlocal inner
        if inner.count(old) != 1:
            raise ValueError(f"Dashboard integrity anchor must occur once: {old[:100]!r}")
        inner = inner.replace(old, new, 1)

    # Keep readable method source outside the JSON-encoded export.
    inner = refresh_methods(inner)

    replace('    demoMode: true,\n    demoModeManual: false,', '''    demoMode: (() => { try { return window.localStorage.getItem("smcr_workspace_mode") !== "personal"; } catch (err) { return true; } })(),
    demoModeManual: false,
    handoffLoaded: false,
    handoffDirty: false,
    handoffSaveStatus: "Loading handoffs…",''')
    replace('    feedUpdated: "2 min ago",', '    feedUpdated: "not refreshed in this session",')
    # Seed data comes from the explicit demo workspace, never frontend defaults.
    for field in ("notes", "fitreps", "handoffs"):
        pattern = rf"^    {field}: \[\n.*?^    \],"
        inner, count = re.subn(pattern, f"    {field}: [],", inner, count=1, flags=re.M | re.S)
        if count != 1:
            raise ValueError(f"Missing default array {field}")
    replace('    activeHandoffId: 1,', '    activeHandoffId: null,')
    replace('    profileBillet: "SuppO",', '    profileBillet: "",')

    # Guard every user-keyed async loader against responses from a previous mode.
    starts = list(re.finditer(r"^  async (_load\w+)\([^\n]*\) \{", inner, re.M))
    for match in reversed(starts):
        if match.group(1) == "_loadRealHandoff":
            continue  # It has explicit guards and migration logic above.
        end_match = re.search(r"^  (?:(?:async|static) )?\w+\([^\n]*\) \{", inner[match.end():], re.M)
        if not end_match:
            continue
        end = match.end() + end_match.start()
        block = inner[match.start():end]
        if "this.userKey" not in block:
            continue
        # Declare the identity snapshot at the top of the method so a setState
        # that precedes `try {` (e.g. a "Loading…" status) never references the
        # consts before they exist (a temporal-dead-zone ReferenceError).
        header_end = block.index("{\n") + 2
        if block[header_end:].startswith(_RESOLVE_LINE):
            header_end += len(_RESOLVE_LINE)
        block = (
            block[:header_end]
            + "    const requestKey = this.userKey;\n    const modeVersion = this._modeVersion;\n"
            + block[header_end:]
        )
        # Every setState (including catch paths) checks identity after awaits.
        block = block.replace("this.setState(", "if (requestKey !== this.userKey || modeVersion !== this._modeVersion) return;\n      this.setState(")
        inner = inner[:match.start()] + block + inner[end:]

    replace('      saveHandoff: () => this.forceUpdate(),', '      saveHandoff: () => this._persistHandoffJournal(),')
    replace('      actNow, maradmins, navadmins, feeds, actions, srcUpdates, srcUpdatesEmpty,', '      ...this._overviewIntegrityBindings(),\n      actNow, maradmins, navadmins, feeds, actions, srcUpdates, srcUpdatesEmpty,')
    replace('        this.setState({ demoMode: next, demoModeManual: true });\n        this._switchDemoMode(next);', '''        if (this.state.handoffDirty && !window.confirm("You have unsaved handoff changes. Switch workspace and discard them?")) return;
        this._switchDemoMode(next);''')
    replace('      travelAlertVisible: this.state.travelIsFifty && this.state.travelMode === "flyer" && !this.state.dtsFlightBooked,', '      travelAlertVisible: false, // Booking status is not available from an authenticated travel system.')
    replace('        : "[Rank LName]",', '        : "Marine",')

    # Show actual open tasks, with no inferred portal or invented urgency.
    act_start = inner.index("    const actNow = [")
    act_end = inner.index("    ];", act_start) + len("    ];")
    inner = inner[:act_start] + '''    const actNow = (this.state.workspaceLoaded ? this.state.actions : []).filter((a) => !a.done).slice(0, 3).map((a) => ({
      tag: "Tracked action", tagStyle: tagAttn, rowStyle: rowRoutine,
      due: a.due || "No due date", title: a.title, detail: a.notes || "",
      onOpen: () => this.setState({ lane: "watch" }),
    }));''' + inner[act_end:]
    replace('Next drill · <span style="color:#eef2f6;font-weight:600;">18 days</span> · 09–10 AUG', '{{ nextDrillLabel }}')
    replace('<h3 style="margin:0;font-size:1.3rem;font-weight:700;">Watch</h3>', '<h3 style="margin:0;font-size:1.3rem;font-weight:700;">{{ readinessHeading }}</h3>')
    replace('Two must-do items and one FitRep suspense are open before 09 AUG.', '{{ readinessSummary }}')
    replace('Submit the AT travel claim in DTS. Two reimbursements are pending behind it.', '{{ decisiveAction }}')
    hero_link = re.search(r'            <a href="https://dtsproweb.defensetravel.osd.mil"[^\n]+</a>', inner)
    if not hero_link:
        raise ValueError("Missing hero link")
    replace(hero_link.group(), '            <button type="button" sc-camel-on-click="{{ goWatch }}" style="margin-top:14px;padding:8px 16px;background:#b21f2d;color:#fff;border:0;border-radius:6px;cursor:pointer;">Review tracked actions</button>')
    replace('The three items to work before anything else.', 'Open tracked actions. Review priorities in Watch.')
    row_link = re.search(r' +<a href="{{ item.sysUrl }}"[^\n]+</a>', inner)
    if not row_link:
        raise ValueError("Missing action link")
    replace(row_link.group(), '                 <button type="button" sc-camel-on-click="{{ item.onOpen }}" style="margin-top:8px;padding:6px 10px;background:#1a2027;color:#eef2f6;border:1px solid #313844;border-radius:4px;">Review action</button>')
    replace('          <p style="margin:0 0 14px;color:#8a94a0;font-size:0.82rem;">Open tracked actions. Review priorities in Watch.</p>', '          <p style="margin:0 0 14px;color:#8a94a0;font-size:0.82rem;">Open tracked actions. Review priorities in Watch.</p>\n          <sc-if value="{{ actNowEmpty }}"><p>No open actions tracked yet. Add an action in Watch.</p></sc-if>')
    replace('    const maradmins = !this.state.workspaceLoaded\n      ? demoMaradmins', '    const maradmins = !this.state.workspaceLoaded\n      ? emptyTicker("MARADMIN", MARADMIN_PORTAL)')
    replace('    const navadmins = !this.state.workspaceLoaded\n      ? demoNavadmins', '    const navadmins = !this.state.workspaceLoaded\n      ? emptyTicker("NAVADMIN", NAVADMIN_PORTAL)')
    replace('Continuity carried between drill weekends. Feeds the Act Now queue and readiness posture.', 'Saved continuity between drills. The newest active handoff supplies the session summary; tracked actions are managed in Watch.')
    label_anchor = '              <label style="display:grid;gap:6px;font-size:0.82rem;font-weight:600;color:#c7cfd8;"><span>Admin watch items'
    replace(label_anchor, '              <p role="status" aria-live="polite">{{ handoffSaveStatus }}</p>\n              <label style="display:grid;gap:6px;margin-bottom:12px;">Handoff title<input aria-label="Handoff title" value="{{ handoffLabel }}" sc-camel-on-change="{{ onHandoffLabelChange }}"></label>\n' + label_anchor)
    # Warn on tab close/reload while unsaved journal work exists.
    replace('  componentDidMount() {', '''  componentDidMount() {
    this._beforeUnload = (event) => { if (this.state.handoffDirty) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", this._beforeUnload);''')
    replace('  componentWillUnmount() { clearInterval(this._t); }', '  componentWillUnmount() { clearInterval(this._t); window.removeEventListener("beforeunload", this._beforeUnload); }')
    # Stamp only after every strict replacement succeeds.
    replace('class Component extends DCLogic {', 'class Component extends DCLogic {\n  ' + MARKER)
    return apply_ai_page_patches(finish_repairs(inner))


# ---------------------------------------------------------------------------
# AI page (2026-09-13): Round table tab, runnable combos, doctrine notes.
# Each entry is (label, marker, old, new). The marker is what proves a patch is
# already applied, so patch_integrity stays idempotent on the committed bundle.
# The JS methods these bindings call (_runRoundtable, _runCombo,
# _roundtableVals) live in dashboard_integrity_methods.js.
# ---------------------------------------------------------------------------
AI_PAGE_PATCHES: list[tuple[str, str, str, str]] = [
    # ------------------------------------------------------------------
    # AI page (2026-09-13): Round table tab (POST /agents/roundtable), runnable
    # combos (POST /agents/chain), and doctrine notes on each agent card
    # (metadata.system_prompt surfaced + copy-as-prompt).
    # ------------------------------------------------------------------
    (
        "aiTabs: add the Round table tab right after Agents",
        '{ id: "roundtable", label: "Round table" }',  # stable marker
        '      { id: "agents", label: "Agents" },\n      { id: "skills", label: "Skills" },\n',
        '      { id: "agents", label: "Agents" },\n'
        '      { id: "roundtable", label: "Round table" },\n'
        '      { id: "skills", label: "Skills" },\n',
    ),
    (
        "aiTab flags: add isAiTabRoundtable",
        "const isAiTabRoundtable =",  # stable marker
        '    const isAiTabAutomations = this.state.aiTab === "automations";\n',
        '    const isAiTabAutomations = this.state.aiTab === "automations";\n'
        '    const isAiTabRoundtable = this.state.aiTab === "roundtable";\n',
    ),
    (
        "vals object: expose round table + combo bindings",
        "...this._roundtableVals(),",  # stable marker
        "      ...this._automationsVals(),\n",
        "      ...this._automationsVals(),\n      isAiTabRoundtable, ...this._roundtableVals(),\n",
    ),
    (
        "state defaults: round table + combo runner fields",
        'roundtableQuestion: ""',  # stable marker
        "    skillNotes: {},\n",
        "    skillNotes: {},\n"
        '    roundtableQuestion: "", roundtablePreset: "full_staff", roundtableRounds: 1, roundtableBusy: false,\n'
        '    roundtableError: "", roundtableResult: null, roundtableCopied: false,\n'
        '    comboQuestion: "", comboBusy: "", comboResults: {},\n',
    ),
    (
        "Round table tab template, inserted before the Automations tab",
        'isAiTabRoundtable }}',  # stable marker
        '      <sc-if value="{{ isAiTabAutomations }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="display:grid;gap:16px;">\n'
        '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:16px 18px;">\n'
        '          <h3 style="margin:0 0 6px;font-size:1rem;font-weight:700;">Set up your Chief of Staff</h3>\n',
        '      <sc-if value="{{ isAiTabRoundtable }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="display:grid;gap:14px;">\n'
        '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:16px 18px;">\n'
        '          <h3 style="margin:0 0 6px;font-size:1rem;font-weight:700;">Round table — ask the whole staff in one go</h3>\n'
        '          <p style="margin:0;color:#c7cfd8;font-size:0.84rem;line-height:1.55;">Type a question, a training idea, or a scenario. Every seat you pick answers at once, then the Chief of Staff pulls the answers together. Without an external AI key the seats answer from their built-in doctrine templates; with a key and your approval they populate the assessment for your scenario. UNCLASSIFIED only — advisory drafts, verify before acting.</p>\n'
        "        </section>\n"
        '        <form sc-camel-on-submit="{{ onRoundtableRun }}" style="display:grid;gap:12px;border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px 20px;">\n'
        '          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Question, task, or scenario\n'
        '            <textarea rows="4" value="{{ roundtableQuestion }}" sc-camel-on-change="{{ onRoundtableQuestion }}" placeholder="e.g. Plan a two-day land navigation and patrolling drill for a comm company with 60 Marines in October." style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.86rem;resize:vertical;"></textarea>\n'
        "          </label>\n"
        '          <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:end;">\n'
        '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Who answers\n'
        '              <sc-raw-select value="{{ roundtablePreset }}" sc-camel-on-change="{{ onRoundtablePreset }}" aria-label="Round table participants" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="full_staff">Full staff (every seat)</option><option value="training">Training team (S-3, XO, S-1, S-4, S-6, SEL, Surgeon, SJA, ORM, AAR, Planning)</option><option value="command_team">Command team (XO, S-3, SEL, S-1, SJA, Chaplain, Planning, Red team)</option><option value="auto">Auto — pick seats from the topic</option></sc-raw-select>\n'
        "            </label>\n"
        '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Rounds\n'
        '              <sc-raw-select value="{{ roundtableRounds }}" sc-camel-on-change="{{ onRoundtableRounds }}" aria-label="Round table rounds" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="1">1 — opening assessments</option><option value="2">2 — add cross-review (needs external AI)</option></sc-raw-select>\n'
        "            </label>\n"
        '            <button type="submit" style="height:38px;padding:0 20px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:700;font-size:0.86rem;cursor:pointer;">{{ roundtableRunLabel }}</button>\n'
        "          </div>\n"
        '          <sc-if value="{{ roundtableHasError }}" hint-placeholder-val="{{ false }}">\n'
        '            <p style="margin:0;color:#e8a0a8;font-size:0.8rem;line-height:1.45;">{{ roundtableError }}</p>\n'
        "          </sc-if>\n"
        "        </form>\n"
        '        <sc-if value="{{ roundtableHasResult }}" hint-placeholder-val="{{ false }}">\n'
        '        <div style="display:grid;gap:12px;">\n'
        '          <div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap;">\n'
        '            <p style="margin:0;color:#8a94a0;font-size:0.78rem;line-height:1.45;"><strong style="color:#aab4bf;">At the table:</strong> {{ roundtableParticipantsLabel }}</p>\n'
        '            <button type="button" sc-camel-on-click="{{ onRoundtableCopy }}" style="flex:0 0 auto;height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ roundtableCopyLabel }}</button>\n'
        "          </div>\n"
        '          <sc-if value="{{ roundtableHasSynthesis }}" hint-placeholder-val="{{ false }}">\n'
        '          <section style="border:1px solid #3a2b2e;border-radius:8px;background:#1b1114;padding:14px 18px;">\n'
        '            <h3 style="margin:0 0 8px;font-size:0.95rem;font-weight:700;">Chief of Staff synthesis</h3>\n'
        '            <pre style="margin:0;white-space:pre-wrap;color:#eef2f6;font-size:0.82rem;line-height:1.5;font-family:inherit;">{{ roundtableSynthesis }}</pre>\n'
        "          </section>\n"
        "          </sc-if>\n"
        '          <sc-for list="{{ roundtableEntries }}" as="e" hint-placeholder-count="3">\n'
        '            <details style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:12px 16px;">\n'
        '              <summary style="cursor:pointer;font-size:0.9rem;font-weight:700;color:#eef2f6;">{{ e.name }} <span style="font-weight:400;color:#8a94a0;font-size:0.76rem;">· confidence {{ e.confidence }}</span></summary>\n'
        '              <pre style="margin:10px 0 0;white-space:pre-wrap;color:#c7cfd8;font-size:0.8rem;line-height:1.5;font-family:inherit;">{{ e.answer }}</pre>\n'
        '              <sc-if value="{{ e.hasQuestions }}" hint-placeholder-val="{{ false }}">\n'
        '              <p style="margin:10px 0 4px;color:#8a94a0;font-size:0.76rem;font-weight:600;">This seat wants to know:</p>\n'
        '              <sc-for list="{{ e.questions }}" as="q" hint-placeholder-count="2">\n'
        '                <p style="margin:0 0 4px;color:#aab4bf;font-size:0.78rem;line-height:1.45;">• {{ q.text }}</p>\n'
        "              </sc-for>\n"
        "              </sc-if>\n"
        "            </details>\n"
        "          </sc-for>\n"
        '          <sc-if value="{{ roundtableHasWarnings }}" hint-placeholder-val="{{ false }}">\n'
        '          <details style="border:1px solid #313844;border-radius:8px;background:#0f1318;padding:10px 16px;">\n'
        '            <summary style="cursor:pointer;color:#8a94a0;font-size:0.76rem;font-weight:600;">Warnings and notes ({{ roundtableWarningCount }})</summary>\n'
        '            <sc-for list="{{ roundtableWarnings }}" as="w" hint-placeholder-count="2">\n'
        '              <p style="margin:6px 0 0;color:#aab4bf;font-size:0.76rem;line-height:1.45;">{{ w.text }}</p>\n'
        "            </sc-for>\n"
        "          </details>\n"
        "          </sc-if>\n"
        "        </div>\n"
        "        </sc-if>\n"
        "      </div>\n"
        "      </sc-if>\n"
        "\n"
        '      <sc-if value="{{ isAiTabAutomations }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="display:grid;gap:16px;">\n'
        '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:16px 18px;">\n'
        '          <h3 style="margin:0 0 6px;font-size:1rem;font-weight:700;">Set up your Chief of Staff</h3>\n',
    ),
    (
        "_loadRealAgents: carry the system prompt as doctrine notes",
        "doctrine: a.system_prompt",  # stable marker
        '        intendedUsers: (a.intended_users || []).join(", "),\n',
        '        intendedUsers: (a.intended_users || []).join(", "),\n'
        '        doctrine: a.system_prompt || "",\n',
    ),
    (
        "agentGroups: carry doctrine notes + copy-as-prompt onto each card",
        "hasDoctrine:",  # stable marker
        "          hasIntendedUsers: !!(a.intendedUsers && a.intendedUsers.length),\n",
        "          hasIntendedUsers: !!(a.intendedUsers && a.intendedUsers.length),\n"
        '          doctrine: a.doctrine || "",\n'
        "          hasDoctrine: !!(a.doctrine && a.doctrine.length),\n"
        '          onCopyDoctrine: () => { navigator.clipboard && navigator.clipboard.writeText("You are the " + a.name + " advisor for a Marine Corps reserve staff. Work from the role notes below, cite publications by number, flag anything that may be out of date with \\"confirm current status\\", and end every answer with: DRAFT — Verify all references against current official sources before acting.\\n\\n" + (a.doctrine || "")); },\n',
    ),
    (
        "Agents tab: doctrine notes details block under Not for",
        "a.hasDoctrine }}",  # stable marker
        '                    <p style="margin:8px 0 0;color:#8a94a0;font-size:0.78rem;line-height:1.45;"><strong style="color:#aab4bf;">Not for:</strong> {{ a.limitations }}</p>\n',
        '                    <p style="margin:8px 0 0;color:#8a94a0;font-size:0.78rem;line-height:1.45;"><strong style="color:#aab4bf;">Not for:</strong> {{ a.limitations }}</p>\n'
        '                    <sc-if value="{{ a.hasDoctrine }}" hint-placeholder-val="{{ true }}">\n'
        '                    <details style="margin-top:8px;">\n'
        '                      <summary style="cursor:pointer;color:#8a94a0;font-size:0.76rem;font-weight:600;">Doctrine notes — what this agent works from</summary>\n'
        '                      <pre style="margin:8px 0 0;white-space:pre-wrap;color:#c7cfd8;font-size:0.78rem;line-height:1.45;font-family:inherit;max-height:320px;overflow:auto;border:1px solid #313844;border-radius:6px;padding:10px;background:#0d1014;">{{ a.doctrine }}</pre>\n'
        '                      <button type="button" sc-camel-on-click="{{ a.onCopyDoctrine }}" style="margin-top:6px;height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">Copy as a chatbot prompt</button>\n'
        "                    </details>\n"
        "                    </sc-if>\n",
    ),
    (
        "combosRendered: runnable combos with results",
        "onRun: () => this._runCombo(c)",  # stable marker
        '      chainLabel: c.chain.map((id) => agentNameById[id] || id).join("  →  "),\n    }));\n',
        '      chainLabel: c.chain.map((id) => agentNameById[id] || id).join("  →  "),\n'
        "      onRun: () => this._runCombo(c),\n"
        '      runLabel: this.state.comboBusy === c.title ? "Running…" : "Run this combo",\n'
        "      hasResult: !!(this.state.comboResults && this.state.comboResults[c.title]),\n"
        "      results: ((this.state.comboResults && this.state.comboResults[c.title]) || []).map((r) => ({ name: agentNameById[r.agent_id] || r.agent_id, answer: r.answer })),\n"
        "    }));\n",
    ),
    (
        "Combos tab: question box, run buttons, and inline results",
        "onComboQuestion }}",  # stable marker
        '      <sc-if value="{{ isAiTabCombos }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="display:grid;gap:10px;">\n'
        '        <sc-for list="{{ combosRendered }}" as="c" hint-placeholder-count="4">\n'
        '          <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:16px 18px;">\n'
        '            <h3 style="margin:0;font-size:0.96rem;font-weight:700;">{{ c.title }}</h3>\n'
        '            <div style="margin-top:6px;font-family:\'IBM Plex Mono\',monospace;font-size:0.78rem;color:#7fae8f;">{{ c.chainLabel }}</div>\n'
        '            <p style="margin:8px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ c.description }}</p>\n'
        "          </section>\n"
        "        </sc-for>\n"
        "      </div>\n"
        "      </sc-if>\n",
        '      <sc-if value="{{ isAiTabCombos }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="display:grid;gap:10px;">\n'
        '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:14px 18px;">\n'
        '          <h3 style="margin:0 0 6px;font-size:0.95rem;font-weight:700;">Combos — agents that hand off to each other</h3>\n'
        '          <p style="margin:0 0 8px;color:#c7cfd8;font-size:0.84rem;line-height:1.55;">Describe the task once, then run any combo below. Each agent in the chain sees the previous agent\'s structured handoff. For the whole staff at once, use the Round table tab.</p>\n'
        '          <textarea rows="3" value="{{ comboQuestion }}" sc-camel-on-change="{{ onComboQuestion }}" placeholder="What should the chain work on? e.g. A battalion FTX at Camp Lejeune in March focused on patrolling and comm." style="width:100%;box-sizing:border-box;border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n'
        "        </section>\n"
        '        <sc-for list="{{ combosRendered }}" as="c" hint-placeholder-count="4">\n'
        '          <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:16px 18px;">\n'
        '            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">\n'
        '              <h3 style="margin:0;font-size:0.96rem;font-weight:700;">{{ c.title }}</h3>\n'
        '              <button type="button" sc-camel-on-click="{{ c.onRun }}" style="flex:0 0 auto;height:28px;padding:0 12px;border:1px solid #b21f2d;border-radius:6px;background:#1b1114;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ c.runLabel }}</button>\n'
        "            </div>\n"
        '            <div style="margin-top:6px;font-family:\'IBM Plex Mono\',monospace;font-size:0.78rem;color:#7fae8f;">{{ c.chainLabel }}</div>\n'
        '            <p style="margin:8px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ c.description }}</p>\n'
        '            <sc-if value="{{ c.hasResult }}" hint-placeholder-val="{{ false }}">\n'
        '            <div style="margin-top:10px;display:grid;gap:8px;">\n'
        '              <sc-for list="{{ c.results }}" as="r" hint-placeholder-count="2">\n'
        '                <details style="border:1px solid #313844;border-radius:6px;background:#0f1318;padding:8px 12px;">\n'
        '                  <summary style="cursor:pointer;font-size:0.84rem;font-weight:600;color:#eef2f6;">{{ r.name }}</summary>\n'
        '                  <pre style="margin:8px 0 0;white-space:pre-wrap;color:#c7cfd8;font-size:0.78rem;line-height:1.45;font-family:inherit;">{{ r.answer }}</pre>\n'
        "                </details>\n"
        "              </sc-for>\n"
        "            </div>\n"
        "            </sc-if>\n"
        "          </section>\n"
        "        </sc-for>\n"
        "      </div>\n"
        "      </sc-if>\n",
    ),
    (
        "AI top intro: point at the Round table tab",
        "Round table</strong> tab",
        "New here? Start on the Automations tab.",
        "Want every seat's view at once? Use the <strong>Round table</strong> tab. New here? Start on the Automations tab.",
    ),
]


def apply_ai_page_patches(inner: str) -> str:
    for label, marker, old, new in AI_PAGE_PATCHES:
        if marker in inner:
            continue
        if inner.count(old) != 1:
            raise ValueError(f"AI page patch anchor must occur once ({label}): {old[:100]!r}")
        inner = inner.replace(old, new, 1)
    return inner


# ---------------------------------------------------------------------------
# v2 (2026-09-13, same day): honest modes. The v1 tab rendered template runs as
# seat "answers"; v2 shows a staff call packet unless an external AI is
# configured, and never presents a template as analysis. Each v2 patch takes
# the v1 patch's output as its `old`, so fresh exports and the committed bundle
# both converge on v2.
# ---------------------------------------------------------------------------

def _v1_new(label: str) -> str:
    for entry in AI_PAGE_PATCHES:
        if entry[0] == label:
            return entry[3]
    raise KeyError(label)


_AUTOMATIONS_OPEN = '      <sc-if value="{{ isAiTabAutomations }}" hint-placeholder-val="{{ false }}">\n'
_V1_ROUNDTABLE_BLOCK = _v1_new("Round table tab template, inserted before the Automations tab").split(_AUTOMATIONS_OPEN)[0]
_V1_COMBOS_BLOCK = _v1_new("Combos tab: question box, run buttons, and inline results")
_V1_COMBOS_MAPPING = _v1_new("combosRendered: runnable combos with results")

_V2_ROUNDTABLE_BLOCK = (
    '      <sc-if value="{{ isAiTabRoundtable }}" hint-placeholder-val="{{ false }}">\n'
    '      <div style="display:grid;gap:14px;">\n'
    '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:16px 18px;">\n'
    '          <h3 style="margin:0 0 6px;font-size:1rem;font-weight:700;">Round table — convene the whole staff</h3>\n'
    '          <p style="margin:0 0 8px;color:#c7cfd8;font-size:0.84rem;line-height:1.55;">Drop in a SITREP, a scenario, a training idea, or a plain staff question. The seats you pick are convened <strong>by an AI</strong> — never by this app on its own.</p>\n'
    '          <p role="status" aria-live="polite" style="margin:0;padding:8px 10px;border:1px solid #3a4450;border-radius:6px;background:#0d1014;color:#e8c27a;font-size:0.8rem;line-height:1.5;">{{ roundtableCapabilityNote }}</p>\n'
    "        </section>\n"
    '        <form sc-camel-on-submit="{{ onRoundtableRun }}" style="display:grid;gap:12px;border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px 20px;">\n'
    '          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">SITREP, question, or task\n'
    '            <textarea rows="5" value="{{ roundtableQuestion }}" sc-camel-on-change="{{ onRoundtableQuestion }}" placeholder="e.g. SITREP: 2/24 conducts a two-day land navigation and patrolling drill at Camp Lejeune, 60 Marines, October. Ranges confirmed, ammo pending, one corpsman on NROWS orders not yet approved." style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.86rem;resize:vertical;"></textarea>\n'
    "          </label>\n"
    '          <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:end;">\n'
    '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Seats to convene\n'
    '              <sc-raw-select value="{{ roundtablePreset }}" sc-camel-on-change="{{ onRoundtablePreset }}" aria-label="Round table participants" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="full_staff">Full staff (every seat)</option><option value="training">Training team (S-3, XO, S-1, S-4, S-6, SEL, Surgeon, SJA, ORM, AAR, Planning)</option><option value="command_team">Command team (XO, S-3, SEL, S-1, SJA, Chaplain, Planning, Red team)</option><option value="auto">Auto — pick seats from the topic</option></sc-raw-select>\n'
    "            </label>\n"
    '            <sc-if value="{{ roundtableExternal }}" hint-placeholder-val="{{ false }}">\n'
    '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Rounds\n'
    '              <sc-raw-select value="{{ roundtableRounds }}" sc-camel-on-change="{{ onRoundtableRounds }}" aria-label="Round table rounds" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="1">1 — opening assessments</option><option value="2">2 — add cross-review</option></sc-raw-select>\n'
    "            </label>\n"
    "            </sc-if>\n"
    '            <sc-if value="{{ roundtablePacketMode }}" hint-placeholder-val="{{ true }}">\n'
    '            <label style="display:flex;gap:7px;align-items:center;font-size:0.76rem;color:#c7cfd8;height:36px;"><input type="checkbox" checked="{{ roundtableRoleNotes }}" sc-camel-on-change="{{ onRoundtableRoleNotes }}"><span>Include each seat\'s doctrine notes (bigger packet, better answers)</span></label>\n'
    "            </sc-if>\n"
    '            <button type="submit" style="height:38px;padding:0 20px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:700;font-size:0.86rem;cursor:pointer;">{{ roundtableRunLabel }}</button>\n'
    '            <sc-if value="{{ roundtableExternal }}" hint-placeholder-val="{{ false }}">\n'
    '            <button type="button" sc-camel-on-click="{{ onRoundtablePacketOnly }}" style="height:38px;padding:0 14px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.8rem;cursor:pointer;">Build packet instead</button>\n'
    "            </sc-if>\n"
    "          </div>\n"
    '          <sc-if value="{{ roundtableHasError }}" hint-placeholder-val="{{ false }}">\n'
    '            <p style="margin:0;color:#e8a0a8;font-size:0.8rem;line-height:1.45;">{{ roundtableError }}</p>\n'
    "          </sc-if>\n"
    '          <sc-if value="{{ roundtablePreviewRequired }}" hint-placeholder-val="{{ false }}">\n'
    '          <div style="padding:12px;border:1px solid #d6bd7a;border-radius:6px;background:#17150e;display:grid;gap:8px;">\n'
    '            <strong style="font-size:0.8rem;color:#f5ebe9;">Approval required · {{ roundtablePreviewCalls }} external AI calls · {{ roundtablePreviewModel }}</strong>\n'
    '            <p style="margin:0;color:#c7cfd8;font-size:0.76rem;line-height:1.45;">Each seat sends its role notes plus your text to the external provider. Findings below are advisory pattern matches, not a classification decision. You are confirming this is UNCLASSIFIED and appropriate for that provider.</p>\n'
    '            <details><summary style="cursor:pointer;color:#8a94a0;font-size:0.76rem;font-weight:600;">What will be sent (your text, sanitized · {{ roundtableRedactedCount }} redactions)</summary><pre style="margin:6px 0 0;white-space:pre-wrap;color:#c7cfd8;font-size:0.76rem;line-height:1.45;font-family:inherit;max-height:220px;overflow:auto;">{{ roundtablePreviewUserText }}</pre></details>\n'
    '            <sc-if value="{{ roundtableHasFindings }}" hint-placeholder-val="{{ false }}">\n'
    '            <sc-for list="{{ roundtablePreviewFindings }}" as="f" hint-placeholder-count="1">\n'
    '              <p style="margin:0;color:#e8c27a;font-size:0.74rem;line-height:1.4;">⚠ {{ f.text }}</p>\n'
    "            </sc-for>\n"
    "            </sc-if>\n"
    '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;max-width:320px;">Disclosure\n'
    '              <sc-raw-select value="{{ roundtableDisclosure }}" sc-camel-on-change="{{ onRoundtableDisclosure }}" aria-label="Disclosure mode" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="sanitized">Sanitized — redact flagged patterns</option><option value="original">Original text</option></sc-raw-select>\n'
    "            </label>\n"
    '            <label style="display:flex;gap:7px;align-items:flex-start;color:#c7cfd8;font-size:0.74rem;"><input type="checkbox" checked="{{ roundtableApproved }}" sc-camel-on-change="{{ onRoundtableApproval }}"><span>I am authorized to send this UNCLASSIFIED text to the configured provider and I reviewed the findings.</span></label>\n'
    '            <div style="display:flex;gap:8px;flex-wrap:wrap;">\n'
    '              <button type="button" disabled="{{ !roundtableApproved }}" sc-camel-on-click="{{ onRoundtableApprove }}" style="height:32px;padding:0 12px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">Convene with external AI</button>\n'
    '              <button type="button" sc-camel-on-click="{{ onRoundtablePacketOnly }}" style="height:32px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">Build a packet for my own AI instead</button>\n'
    '              <button type="button" sc-camel-on-click="{{ onRoundtableCancelPreview }}" style="height:32px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#0d1014;color:#aab4bf;font:inherit;font-size:0.76rem;cursor:pointer;">Cancel</button>\n'
    "            </div>\n"
    "          </div>\n"
    "          </sc-if>\n"
    "        </form>\n"
    '        <sc-if value="{{ roundtableHasPacket }}" hint-placeholder-val="{{ false }}">\n'
    '        <section style="border:1px solid #d6bd7a;border-radius:8px;background:#17150e;padding:14px 18px;display:grid;gap:10px;">\n'
    '          <div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap;">\n'
    '            <h3 style="margin:0;font-size:0.95rem;font-weight:700;color:#f5ebe9;">Staff call packet built — no analysis was performed</h3>\n'
    '            <div style="display:flex;gap:8px;flex-wrap:wrap;">\n'
    '              <button type="button" sc-camel-on-click="{{ onRoundtablePacketCopy }}" style="height:28px;padding:0 12px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ roundtablePacketCopyLabel }}</button>\n'
    '              <button type="button" disabled="{{ roundtablePacketSaved }}" sc-camel-on-click="{{ onRoundtablePacketSave }}" style="height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ roundtablePacketSaveLabel }}</button>\n'
    "            </div>\n"
    "          </div>\n"
    '          <p style="margin:0;color:#c7cfd8;font-size:0.8rem;line-height:1.5;">{{ roundtablePacketNote }} Paste it into Claude, ChatGPT, or Gemini — or into Claude Code / Codex with this repo open — and the AI will answer as each seat, synthesize as the Chief of Staff, and draft the products. Saved packets land in Drafted files (Workflows lane) where you can move them into a project folder your AI can search.</p>\n'
    '          <p style="margin:0;color:#8a94a0;font-size:0.76rem;line-height:1.45;"><strong style="color:#aab4bf;">Seats in this packet:</strong> {{ roundtablePacketSeats }}</p>\n'
    '          <details><summary style="cursor:pointer;color:#8a94a0;font-size:0.76rem;font-weight:600;">Show packet</summary><pre style="margin:8px 0 0;white-space:pre-wrap;color:#c7cfd8;font-size:0.78rem;line-height:1.45;font-family:inherit;max-height:480px;overflow:auto;border:1px solid #313844;border-radius:6px;padding:10px;background:#0d1014;">{{ roundtablePacketText }}</pre></details>\n'
    "        </section>\n"
    "        </sc-if>\n"
    '        <sc-if value="{{ roundtableHasResult }}" hint-placeholder-val="{{ false }}">\n'
    '        <div style="display:grid;gap:12px;">\n'
    '          <div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap;">\n'
    '            <p style="margin:0;color:#8a94a0;font-size:0.78rem;line-height:1.45;"><strong style="color:#aab4bf;">AI round table · at the table:</strong> {{ roundtableParticipantsLabel }}</p>\n'
    '            <button type="button" sc-camel-on-click="{{ onRoundtableCopy }}" style="flex:0 0 auto;height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ roundtableCopyLabel }}</button>\n'
    "          </div>\n"
    '          <sc-if value="{{ roundtableHasSynthesis }}" hint-placeholder-val="{{ false }}">\n'
    '          <section style="border:1px solid #3a2b2e;border-radius:8px;background:#1b1114;padding:14px 18px;">\n'
    '            <h3 style="margin:0 0 8px;font-size:0.95rem;font-weight:700;">Chief of Staff synthesis</h3>\n'
    '            <pre style="margin:0;white-space:pre-wrap;color:#eef2f6;font-size:0.82rem;line-height:1.5;font-family:inherit;">{{ roundtableSynthesis }}</pre>\n'
    "          </section>\n"
    "          </sc-if>\n"
    '          <sc-for list="{{ roundtableEntries }}" as="e" hint-placeholder-count="3">\n'
    '            <details style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:12px 16px;">\n'
    '              <summary style="cursor:pointer;font-size:0.9rem;font-weight:700;color:#eef2f6;">{{ e.name }} <span style="font-weight:400;color:#8a94a0;font-size:0.76rem;">· confidence {{ e.confidence }}</span></summary>\n'
    '              <pre style="margin:10px 0 0;white-space:pre-wrap;color:#c7cfd8;font-size:0.8rem;line-height:1.5;font-family:inherit;">{{ e.answer }}</pre>\n'
    '              <sc-if value="{{ e.hasQuestions }}" hint-placeholder-val="{{ false }}">\n'
    '              <p style="margin:10px 0 4px;color:#8a94a0;font-size:0.76rem;font-weight:600;">This seat wants to know:</p>\n'
    '              <sc-for list="{{ e.questions }}" as="q" hint-placeholder-count="2">\n'
    '                <p style="margin:0 0 4px;color:#aab4bf;font-size:0.78rem;line-height:1.45;">• {{ q.text }}</p>\n'
    "              </sc-for>\n"
    "              </sc-if>\n"
    "            </details>\n"
    "          </sc-for>\n"
    '          <sc-if value="{{ roundtableHasWarnings }}" hint-placeholder-val="{{ false }}">\n'
    '          <details style="border:1px solid #313844;border-radius:8px;background:#0f1318;padding:10px 16px;">\n'
    '            <summary style="cursor:pointer;color:#8a94a0;font-size:0.76rem;font-weight:600;">Warnings and notes ({{ roundtableWarningCount }})</summary>\n'
    '            <sc-for list="{{ roundtableWarnings }}" as="w" hint-placeholder-count="2">\n'
    '              <p style="margin:6px 0 0;color:#aab4bf;font-size:0.76rem;line-height:1.45;">{{ w.text }}</p>\n'
    "            </sc-for>\n"
    "          </details>\n"
    "          </sc-if>\n"
    "        </div>\n"
    "        </sc-if>\n"
    "      </div>\n"
    "      </sc-if>\n"
    "\n"
)

_V2_COMBOS_MAPPING = (
    '      chainLabel: c.chain.map((id) => agentNameById[id] || id).join("  →  "),\n'
    "      onRun: () => this._runCombo(c),\n"
    '      runLabel: this.state.comboBusy === c.title ? "Building packet…" : "Build packet for this chain",\n'
    "      hasResult: !!(this.state.comboResults && this.state.comboResults[c.title]),\n"
    '      packet: (this.state.comboResults && this.state.comboResults[c.title]) || "",\n'
    '      onCopyPacket: () => { navigator.clipboard && navigator.clipboard.writeText((this.state.comboResults && this.state.comboResults[c.title]) || ""); },\n'
    "    }));\n"
)

_V2_COMBOS_BLOCK = (
    '      <sc-if value="{{ isAiTabCombos }}" hint-placeholder-val="{{ false }}">\n'
    '      <div style="display:grid;gap:10px;">\n'
    '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:14px 18px;">\n'
    '          <h3 style="margin:0 0 6px;font-size:0.95rem;font-weight:700;">Combos — agents that hand off to each other</h3>\n'
    '          <p style="margin:0 0 8px;color:#c7cfd8;font-size:0.84rem;line-height:1.55;">Describe the task once, then build a packet for any chain below. The packet lists the agents in order with their lenses and doctrine notes and tells your AI to run them as a chain, each reading the previous one\'s output. This app does not run the analysis itself.</p>\n'
    '          <textarea rows="3" value="{{ comboQuestion }}" sc-camel-on-change="{{ onComboQuestion }}" placeholder="What should the chain work on? e.g. A battalion FTX at Camp Lejeune in March focused on patrolling and comm." style="width:100%;box-sizing:border-box;border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n'
    "        </section>\n"
    '        <sc-for list="{{ combosRendered }}" as="c" hint-placeholder-count="4">\n'
    '          <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:16px 18px;">\n'
    '            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">\n'
    '              <h3 style="margin:0;font-size:0.96rem;font-weight:700;">{{ c.title }}</h3>\n'
    '              <button type="button" sc-camel-on-click="{{ c.onRun }}" style="flex:0 0 auto;height:28px;padding:0 12px;border:1px solid #b21f2d;border-radius:6px;background:#1b1114;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ c.runLabel }}</button>\n'
    "            </div>\n"
    '            <div style="margin-top:6px;font-family:\'IBM Plex Mono\',monospace;font-size:0.78rem;color:#7fae8f;">{{ c.chainLabel }}</div>\n'
    '            <p style="margin:8px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ c.description }}</p>\n'
    '            <sc-if value="{{ c.hasResult }}" hint-placeholder-val="{{ false }}">\n'
    '            <div style="margin-top:10px;padding:10px;border:1px solid #d6bd7a;border-radius:6px;background:#17150e;display:grid;gap:6px;">\n'
    '              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;"><strong style="font-size:0.78rem;color:#f5ebe9;">Chain packet built — no analysis was performed</strong><button type="button" sc-camel-on-click="{{ c.onCopyPacket }}" style="height:26px;padding:0 10px;border:1px solid #313844;border-radius:5px;background:#1a2027;color:#eef2f6;font:inherit;font-size:0.72rem;font-weight:600;cursor:pointer;">Copy packet</button></div>\n'
    '              <details><summary style="cursor:pointer;color:#8a94a0;font-size:0.74rem;font-weight:600;">Show packet</summary><pre style="margin:6px 0 0;white-space:pre-wrap;color:#c7cfd8;font-size:0.76rem;line-height:1.45;font-family:inherit;max-height:360px;overflow:auto;">{{ c.packet }}</pre></details>\n'
    "            </div>\n"
    "            </sc-if>\n"
    "          </section>\n"
    "        </sc-for>\n"
    "      </div>\n"
    "      </sc-if>\n"
)

AI_PAGE_PATCHES.extend(
    [
        (
            "Round table tab v2: packet mode unless an external AI is configured",
            "roundtableCapabilityNote }}",
            _V1_ROUNDTABLE_BLOCK,
            _V2_ROUNDTABLE_BLOCK,
        ),
        (
            "combosRendered v2: chain packets instead of template runs",
            "onCopyPacket: () =>",
            _V1_COMBOS_MAPPING,
            _V2_COMBOS_MAPPING,
        ),
        (
            "Combos tab v2: build chain packets",
            "Chain packet built",
            _V1_COMBOS_BLOCK,
            _V2_COMBOS_BLOCK,
        ),
        (
            "state defaults v2: round table capability + packet fields",
            "roundtableCapability: undefined",
            '    comboQuestion: "", comboBusy: "", comboResults: {},\n',
            '    comboQuestion: "", comboBusy: "", comboResults: {},\n'
            '    roundtableCapability: undefined, roundtablePacket: null, roundtablePacketSavedId: null, roundtablePacketCopied: false,\n'
            '    roundtablePreview: null, roundtableApproved: false, roundtableDisclosure: "sanitized", roundtableRoleNotes: true,\n',
        ),
        (
            "AI top intro v2: honest round table wording",
            "convene the staff through your own AI",
            "Want every seat's view at once? Use the <strong>Round table</strong> tab. New here? Start on the Automations tab.",
            "Want the whole staff on a SITREP? The <strong>Round table</strong> tab builds a packet you convene the staff through your own AI (or runs live when an external AI is configured). New here? Start on the Automations tab.",
        ),
    ]
)


# ---------------------------------------------------------------------------
# v3 (2026-09-13): user-built automations under the Chief of Staff setup.
# ---------------------------------------------------------------------------

_AUTOMATIONS_TAIL_ANCHOR = (
    "      </div>\n"
    "      </sc-if>\n"
    "    </div>\n"
    "    </sc-if>\n"
    "\n"
    "    <!-- ==================== LINKS LANE ==================== -->\n"
)

_AUTOMATIONS_BLOCK = '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:16px 18px;margin-top:6px;">\n          <h3 style="margin:0 0 6px;font-size:1rem;font-weight:700;">Your automations</h3>\n          <p style="margin:0;color:#c7cfd8;font-size:0.84rem;line-height:1.55;">Build standing routines beyond the Chief of Staff — a post-drill admin sweep, a MARADMIN watch, a range day package. Each one saves here and renders into a copy-paste block for any chatbot, and each run wraps your input into a packet for your AI. <strong>The app never runs them itself and produces no analysis.</strong></p>\n        </section>\n        <sc-if value="{{ hasAutomations }}" hint-placeholder-val="{{ false }}">\n        <sc-for list="{{ automationsRendered }}" as="au" hint-placeholder-count="2">\n          <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:14px 18px;display:grid;gap:8px;">\n            <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">\n              <h4 style="margin:0;font-size:0.95rem;font-weight:700;">{{ au.name }}</h4>\n              <div style="display:flex;gap:6px;flex-wrap:wrap;">\n                <button type="button" sc-camel-on-click="{{ au.onCopy }}" style="height:28px;padding:0 12px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ au.copyLabel }}</button>\n                <button type="button" sc-camel-on-click="{{ au.onEdit }}" style="height:28px;padding:0 10px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-size:0.74rem;cursor:pointer;">Edit</button>\n                <button type="button" sc-camel-on-click="{{ au.onDelete }}" style="height:28px;padding:0 10px;border:1px solid #3a2226;border-radius:6px;background:#1b1114;color:#d8a0a5;font:inherit;font-size:0.74rem;cursor:pointer;">Delete</button>\n              </div>\n            </div>\n            <p style="margin:0;color:#8a94a0;font-size:0.76rem;line-height:1.45;"><strong style="color:#aab4bf;">When:</strong> {{ au.when }} · <strong style="color:#aab4bf;">Seats:</strong> {{ au.seats }} · <strong style="color:#aab4bf;">Steps:</strong> {{ au.stepCount }}</p>\n            <sc-if value="{{ au.hasPurpose }}" hint-placeholder-val="{{ true }}">\n            <p style="margin:0;color:#c7cfd8;font-size:0.82rem;line-height:1.5;">{{ au.purpose }}</p>\n            </sc-if>\n            <details><summary style="cursor:pointer;color:#8a94a0;font-size:0.76rem;font-weight:600;">Show the standing-instruction block</summary><pre style="margin:6px 0 0;white-space:pre-wrap;word-break:break-word;font-family:\'IBM Plex Mono\',monospace;font-size:0.76rem;line-height:1.5;color:#c7cfd8;background:#0b0e12;border:1px solid #313844;border-radius:6px;padding:10px 12px;max-height:300px;overflow:auto;">{{ au.block }}</pre></details>\n            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Run it: paste this occurrence\'s input\n              <textarea rows="3" value="{{ au.runInput }}" sc-camel-on-change="{{ au.onRunInput }}" placeholder="e.g. Drill was 12–13 SEP. Travelers: 14. Two Marines missed muster Saturday…" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.82rem;resize:vertical;"></textarea>\n            </label>\n            <div style="display:flex;gap:8px;flex-wrap:wrap;">\n              <button type="button" sc-camel-on-click="{{ au.onRun }}" style="height:30px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ au.runLabel }}</button>\n              <button type="button" sc-camel-on-click="{{ au.onRunSave }}" style="height:30px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#0d1014;color:#aab4bf;font:inherit;font-size:0.76rem;cursor:pointer;">Build and save to my files</button>\n            </div>\n            <sc-if value="{{ au.hasResult }}" hint-placeholder-val="{{ false }}">\n            <div style="padding:10px;border:1px solid #d6bd7a;border-radius:6px;background:#17150e;display:grid;gap:6px;">\n              <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;"><strong style="font-size:0.78rem;color:#f5ebe9;">Run packet built — no analysis was performed</strong><button type="button" sc-camel-on-click="{{ au.onResultCopy }}" style="height:26px;padding:0 10px;border:1px solid #b21f2d;border-radius:5px;background:#b21f2d;color:#f5ebe9;font:inherit;font-size:0.72rem;font-weight:600;cursor:pointer;">{{ au.resultCopyLabel }}</button></div>\n              <sc-if value="{{ au.resultSaved }}" hint-placeholder-val="{{ false }}"><p style="margin:0;color:#8a94a0;font-size:0.74rem;">Saved to Drafted files (Workflows lane).</p></sc-if>\n              <details><summary style="cursor:pointer;color:#8a94a0;font-size:0.74rem;font-weight:600;">Show run packet</summary><pre style="margin:6px 0 0;white-space:pre-wrap;color:#c7cfd8;font-size:0.76rem;line-height:1.45;font-family:inherit;max-height:360px;overflow:auto;">{{ au.resultPacket }}</pre></details>\n            </div>\n            </sc-if>\n          </section>\n        </sc-for>\n        </sc-if>\n        <form sc-camel-on-submit="{{ onAutoSave }}" style="display:grid;gap:12px;border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px 20px;">\n          <div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap;">\n            <h3 style="margin:0;font-size:0.95rem;font-weight:700;">{{ autoFormTitle }}</h3>\n            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;min-width:260px;">Start from a template\n              <sc-raw-select value="{{ autoTemplate }}" sc-camel-on-change="{{ onAutoTemplate }}" aria-label="Automation template" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="">Blank</option><sc-for list="{{ automationTemplateOptions }}" as="opt" hint-placeholder-count="3"><option value="{{ opt.value }}">{{ opt.label }}</option></sc-for></sc-raw-select>\n            </label>\n          </div>\n          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">\n            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Name\n              <input value="{{ autoName }}" sc-camel-on-change="{{ onAutoName }}" placeholder="e.g. Post-drill admin sweep" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n            </label>\n            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Purpose\n              <input value="{{ autoPurpose }}" sc-camel-on-change="{{ onAutoPurpose }}" placeholder="What this routine is for" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n            </label>\n            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">When (trigger)\n              <input value="{{ autoTrigger }}" sc-camel-on-change="{{ onAutoTrigger }}" placeholder="e.g. Within 5 days after drill" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n            </label>\n            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Cadence\n              <input value="{{ autoCadence }}" sc-camel-on-change="{{ onAutoCadence }}" placeholder="e.g. Monthly" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n            </label>\n          </div>\n          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Steps (one per line, in order)\n            <textarea rows="4" value="{{ autoSteps }}" sc-camel-on-change="{{ onAutoSteps }}" placeholder="Check every traveler\'s DTS voucher status…" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n          </label>\n          <div style="display:grid;gap:6px;">\n            <span style="font-size:0.74rem;font-weight:600;color:#8a94a0;">Staff seats to consult</span>\n            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:4px 12px;max-height:220px;overflow:auto;border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;">\n              <sc-for list="{{ autoSeatOptions }}" as="seat" hint-placeholder-count="6">\n                <label style="display:flex;gap:6px;align-items:center;font-size:0.76rem;color:#c7cfd8;"><input type="checkbox" checked="{{ seat.checked }}" sc-camel-on-change="{{ seat.onToggle }}"><span>{{ seat.name }}</span></label>\n              </sc-for>\n            </div>\n          </div>\n          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Inputs I will give it each run (one per line)\n            <textarea rows="2" value="{{ autoInputs }}" sc-camel-on-change="{{ onAutoInputs }}" placeholder="Drill dates&#10;Known travel claims" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n          </label>\n          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">\n            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Output format\n              <input value="{{ autoFormat }}" sc-camel-on-change="{{ onAutoFormat }}" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n            </label>\n            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Tone\n              <input value="{{ autoTone }}" sc-camel-on-change="{{ onAutoTone }}" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n            </label>\n          </div>\n          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Standing notes\n            <textarea rows="2" value="{{ autoNotes }}" sc-camel-on-change="{{ onAutoNotes }}" placeholder="Anything this routine should always keep in mind…" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n          </label>\n          <sc-if value="{{ autoHasError }}" hint-placeholder-val="{{ false }}"><p style="margin:0;color:#e8a0a8;font-size:0.8rem;">{{ autoError }}</p></sc-if>\n          <div style="display:flex;gap:8px;flex-wrap:wrap;">\n            <button type="submit" style="height:38px;padding:0 20px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:700;font-size:0.86rem;cursor:pointer;">{{ autoSaveLabel }}</button>\n            <sc-if value="{{ autoEditing }}" hint-placeholder-val="{{ false }}"><button type="button" sc-camel-on-click="{{ onAutoCancel }}" style="height:38px;padding:0 14px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-size:0.8rem;cursor:pointer;">Cancel edit</button></sc-if>\n          </div>\n        </form>\n'

AI_PAGE_PATCHES.extend(
    [
        (
            "Automations tab v3: user-built automations list + builder",
            "automationsRendered }}",
            _AUTOMATIONS_TAIL_ANCHOR,
            _AUTOMATIONS_BLOCK + _AUTOMATIONS_TAIL_ANCHOR,
        ),
        (
            "vals object v3: automation bindings",
            "...this._automationVals(),",
            "      isAiTabRoundtable, ...this._roundtableVals(),\n",
            "      isAiTabRoundtable, ...this._roundtableVals(),\n      ...this._automationVals(),\n",
        ),
        (
            "state defaults v3: automation fields",
            "automationTemplates: [],",
            '    roundtablePreview: null, roundtableApproved: false, roundtableDisclosure: "sanitized", roundtableRoleNotes: true,\n',
            '    roundtablePreview: null, roundtableApproved: false, roundtableDisclosure: "sanitized", roundtableRoleNotes: true,\n'
            '    automations: [], automationTemplates: [], automationsLoaded: false, autoEditingId: null, autoName: "", autoPurpose: "",\n'
            '    autoTrigger: "", autoCadence: "", autoSteps: "", autoInputs: "", autoFormat: "Bullet summary with a table of actions",\n'
            '    autoTone: "Direct and professional", autoNotes: "", autoAgents: {}, autoTemplate: "", autoSaving: false, autoSaved: false,\n'
            '    autoError: "", autoCopiedId: null, autoResultCopiedId: null, autoRunInput: {}, autoRunResult: {}, autoBusy: "",\n',
        ),
        (
            "Automations intro v3: mention your own automations",
            "beyond the Chief of Staff",
            "Fill this in once. The app remembers your context, and you get a copy-paste <strong>Chief of Staff</strong> block you can drop into ChatGPT, Claude, Gemini — any chatbot — to get an advisor that already knows your unit, priorities, and battle rhythm. UNCLASSIFIED only.",
            "Fill this in once. The app remembers your context, and you get a copy-paste <strong>Chief of Staff</strong> block you can drop into ChatGPT, Claude, Gemini — any chatbot — to get an advisor that already knows your unit, priorities, and battle rhythm. Below it, build your own automations beyond the Chief of Staff. UNCLASSIFIED only.",
        ),
    ]
)

# ---------------------------------------------------------------------------
# v4 (2026-09-13): ALMAR replaces the NAVADMIN feed. NAVADMIN and ALNAV have
# no public RSS or API and MyNavyHR blocks automated pulls, so the card was
# "live" with nothing behind it. ALMARs ride the same marines.mil RSS as
# MARADMINs; NAVADMIN/ALNAV stay on the Watch page as portal links only.
# ---------------------------------------------------------------------------

_V4_LINK_ROW_NOTE = "official · Navy · portal link, no public feed"

AI_PAGE_PATCHES.extend(
    [
        (
            "Watch v4: overview source watch intro names ALMAR",
            "MARADMIN and ALMAR feeds are connected",
            "MARADMIN and NAVADMIN feeds are connected by default. Newest messages that may change your prep.",
            "MARADMIN and ALMAR feeds are connected by default. Newest messages that may change your prep. NAVADMIN and ALNAV have no public feed; open them from the Watch page.",
        ),
        (
            "Watch v4: connected feeds intro names ALMAR and the portal links",
            "MARADMIN and ALMAR are hooked",
            "MARADMIN and NAVADMIN are hooked by default. Add unit or PME feeds below.",
            "MARADMIN and ALMAR are hooked by default. NAVADMIN and ALNAV have no public RSS or API, so they are portal links here, not feeds. Add unit or PME feeds below.",
        ),
        (
            "Watch v4: overview card header ALMAR",
            'letter-spacing:0.04em;">ALMAR</span>',
            'letter-spacing:0.04em;">NAVADMIN</span>',
            'letter-spacing:0.04em;">ALMAR</span>',
        ),
        (
            "Watch v4: overview card iterates almars",
            '<sc-for list="{{ almars }}"',
            '<sc-for list="{{ navadmins }}" as="m" hint-placeholder-count="3">',
            '<sc-for list="{{ almars }}" as="m" hint-placeholder-count="3">',
        ),
        (
            "Watch v4: portal consts and drop the canned NAVADMIN demo rows",
            "const ALMAR_PORTAL =",
            '    const NAVADMIN_PORTAL = "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN/";\n'
            "    const demoMaradmins = [\n"
            '      { id: "MARADMIN 312/26", title: "FY27 Reserve Component AT budget guidance and submission windows", url: MARADMIN_PORTAL },\n'
            '      { id: "MARADMIN 305/26", title: "Update to FitRep reporting occasions for SMCR reporting seniors", url: MARADMIN_PORTAL },\n'
            '      { id: "MARADMIN 298/26", title: "Revised PME completion requirements for promotion eligibility", url: MARADMIN_PORTAL },\n'
            "    ];\n"
            "    const demoNavadmins = [\n"
            '      { id: "NAVADMIN 148/26", title: "Reserve pay and MROWS processing schedule for Q4 FY26", url: NAVADMIN_PORTAL },\n'
            '      { id: "NAVADMIN 141/26", title: "DTS travel policy change — lodging receipt thresholds", url: NAVADMIN_PORTAL },\n'
            '      { id: "NAVADMIN 136/26", title: "Updated guidance on reserve retirement point capture", url: NAVADMIN_PORTAL },\n'
            "    ];\n",
            '    const ALMAR_PORTAL = "https://www.marines.mil/News/Messages/ALMARS/";\n'
            '    const NAVADMIN_PORTAL = "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN/";\n'
            '    const ALNAV_PORTAL = "https://www.mynavyhr.navy.mil/References/Messages/ALNAV/";\n',
        ),
        (
            "Watch v4: almars ticker const",
            "this.state.realAlmars",
            "    const navadmins = !this.state.workspaceLoaded\n"
            '      ? emptyTicker("NAVADMIN", NAVADMIN_PORTAL)\n'
            '      : ((this.state.realNavadmins || []).length ? this.state.realNavadmins.slice(0, 4) : emptyTicker("NAVADMIN", NAVADMIN_PORTAL));\n',
            "    const almars = !this.state.workspaceLoaded\n"
            '      ? emptyTicker("ALMAR", ALMAR_PORTAL)\n'
            '      : ((this.state.realAlmars || []).length ? this.state.realAlmars.slice(0, 4) : emptyTicker("ALMAR", ALMAR_PORTAL));\n',
        ),
        (
            "Watch v4: static feed items for ALMAR plus honest portal rows",
            "navadmin_portal:",
            "      navadmin: navadmins.map(tickerFeedItem),\n",
            "      almar: almars.map(tickerFeedItem),\n"
            '      navadmin_portal: [{ text: "No public RSS or API, and MyNavyHR blocks automated pulls — nothing is fetched here. Open the portal for the current-year NAVADMIN list.", url: NAVADMIN_PORTAL }],\n'
            '      alnav_portal: [{ text: "No public RSS or API — nothing is fetched here. Open the portal for the current-year ALNAV list.", url: ALNAV_PORTAL }],\n',
        ),
        (
            "Watch v4: unknown static keys render empty instead of throwing",
            "(staticFeedItems[f.staticItems] || [])",
            "? staticFeedItems[f.staticItems]",
            "? (staticFeedItems[f.staticItems] || [])",
        ),
        (
            "Watch v4: feed rows — ALMAR RSS replaces NAVADMIN RSS; NAVADMIN/ALNAV become portal links",
            'staticItems: "almar"',
            '      { id: 2, name: "NAVADMIN RSS", meta: "official · Navy", trust: "Official", type: "rss", url: "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN/", staticItems: "navadmin", editOpen: false },\n',
            '      { id: 2, name: "ALMAR RSS", meta: "official · HQMC", trust: "Official", type: "rss", url: "https://www.marines.mil/News/Messages/ALMARS/", staticItems: "almar", editOpen: false },\n'
            '      { id: 5, name: "NAVADMIN portal", meta: "official · Navy · portal link, no public feed", trust: "Official", type: "url", url: "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN/", staticItems: "navadmin_portal", editOpen: false },\n'
            '      { id: 6, name: "ALNAV portal", meta: "official · Navy · portal link, no public feed", trust: "Official", type: "url", url: "https://www.mynavyhr.navy.mil/References/Messages/ALNAV/", staticItems: "alnav_portal", editOpen: false },\n',
        ),
        (
            "Watch v4: refresh targets pull ALMAR, not NAVADMIN/ALNAV",
            '/message-watch/almars/refresh" }',
            '      { label: "NAVADMIN", url: "/message-watch/navadmins/refresh" },\n'
            '      { label: "ALNAV", url: "/message-watch/alnavs/refresh" },\n',
            '      { label: "ALMAR", url: "/message-watch/almars/refresh" },\n',
        ),
        (
            "Watch v4: row refresh for the ALMAR feed",
            'staticItems === "almar"',
            '    else if (feed.staticItems === "navadmin") url = "/message-watch/navadmins/refresh";\n',
            '    else if (feed.staticItems === "almar") url = "/message-watch/almars/refresh";\n',
        ),
        (
            "Watch v4: workspace payload carries almar_ticker",
            "realAlmars: mapTicker",
            "        realNavadmins: mapTicker(data.navadmin_ticker),\n",
            "        realAlmars: mapTicker(data.almar_ticker),\n",
        ),
        (
            "Watch v4: vals expose almars",
            "actNow, maradmins, almars,",
            "      actNow, maradmins, navadmins, feeds, actions, srcUpdates, srcUpdatesEmpty,\n",
            "      actNow, maradmins, almars, feeds, actions, srcUpdates, srcUpdatesEmpty,\n",
        ),
    ]
)
