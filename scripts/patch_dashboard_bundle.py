"""Apply textual patches to the compiled dashboard bundle's embedded app logic.

`app/static/dashboard/index.html` is a Claude-design-tool export: a self-contained
HTML document whose `<script type="__bundler/template">` tag holds a JSON-encoded
string of the *entire* app (markup + a `<script type="text/x-dc" data-dc-script="">`
block containing a plain, readable `class Component extends DCLogic { ... }`).

That component logic is genuinely hand-editable JS, not a minified/obfuscated
blob -- but it only exists inside a JSON string inside index.html, so a normal
text editor can't safely touch it (escaping, byte offsets shift, etc). This
script does the decode -> patch -> re-encode cycle safely: every patch is an
exact-match find/replace against the *decoded* component source, and the
script fails loudly if a patch's target text doesn't appear exactly once, so a
future re-export from the design tool (which will change unrelated demo data,
whitespace, etc) can't silently corrupt a patch or apply it twice.

Patches live in PATCHES below as (label, old, new) tuples, applied in order.

Usage:
    uv run python scripts/patch_dashboard_bundle.py            # apply and write
    uv run python scripts/patch_dashboard_bundle.py --check    # dry run, no write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BUNDLE_PATH = Path(__file__).resolve().parents[1] / "app" / "static" / "dashboard" / "index.html"
TEMPLATE_OPEN = '<script type="__bundler/template">'
TEMPLATE_CLOSE = "</script>"


def load_bundle(path: Path) -> tuple[str, int, int, str]:
    """Return (full_html, json_start, json_end, decoded_inner_html)."""
    html = path.read_text(encoding="utf-8")
    start = html.find(TEMPLATE_OPEN)
    if start == -1:
        raise SystemExit(f"Could not find {TEMPLATE_OPEN!r} in {path}")
    json_start = start + len(TEMPLATE_OPEN)
    json_end = html.find(TEMPLATE_CLOSE, json_start)
    if json_end == -1:
        raise SystemExit("Could not find the closing </script> for __bundler/template")
    inner = json.loads(html[json_start:json_end].strip())
    return html, json_start, json_end, inner


def apply_patches(inner_html: str, patches: list[tuple[str, ...]]) -> str:
    # Idempotent by design: this script runs against whatever is CURRENTLY in
    # index.html, which after the first run is already-patched. A patch is
    # treated as already-applied and skipped when its marker is present, so
    # the full PATCHES list stays safely re-runnable both against a fresh
    # design-tool re-export (nothing applied yet) and against the current
    # committed bundle (some/all already applied).
    #
    # Each entry is (label, old, new) or (label, marker, old, new). The
    # marker -- not `new` -- is what's checked for "already applied". Plain
    # 3-tuples use `new` as their own marker, which is correct UNLESS this
    # patch inserts a multi-method block immediately before a stable anchor
    # (e.g. "before go(lane)") that a LATER patch in the list also inserts
    # before: once that later patch runs, it sits between this patch's
    # insertion and the anchor, so this patch's exact `new` text (which ends
    # at the anchor) stops matching verbatim even though it's still fully
    # present earlier in the file. That happened twice already (see git
    # history) before markers were introduced -- multi-method "add X helpers"
    # patches MUST pass an explicit, stable marker (e.g. one method's def
    # line) that no other patch's inserted text will ever sit inside of.
    for entry in patches:
        if len(entry) == 4:
            label, marker, old, new = entry
        else:
            label, old, new = entry
            marker = new
        if inner_html.count(marker) >= 1:
            print(f"already applied, skipping: {label}")
            continue
        old_count = inner_html.count(old)
        if old_count == 0:
            raise SystemExit(
                f"Patch {label!r} target text not found -- the bundle was likely "
                "re-exported and this patch needs updating. Aborting without writing."
            )
        if old_count > 1:
            raise SystemExit(
                f"Patch {label!r} target text matched {old_count} times (expected 1) -- "
                "make the search text more specific. Aborting without writing."
            )
        inner_html = inner_html.replace(old, new, 1)
        print(f"applied: {label}")
    return inner_html


def write_bundle(path: Path, html: str, json_start: int, json_end: int, new_inner: str) -> None:
    new_json = json.dumps(new_inner)
    # The original export escapes every "</" as "</" so the embedded HTML's
    # closing tags (</script>, </head>, ...) can never be mistaken by the outer
    # HTML parser for the real end of this <script type="__bundler/template">
    # element. json.dumps does not do this by default -- without it, the first
    # literal "</script>" inside the JSON string (e.g. the React CDN script ref)
    # terminates the outer script tag early and corrupts everything after it.
    new_json = new_json.replace("</", "<\\u002F")
    new_html = html[:json_start] + new_json + html[json_end:]
    path.write_text(new_html, encoding="utf-8", newline="\n")


# ---------------------------------------------------------------------------
# Patches
# ---------------------------------------------------------------------------
#
# Step 2 (dashboard bundle remediation) -- wire the Actions tracker to the
# real /dashboard/data and /actions APIs instead of in-memory demo state.
# See docs/superpowers/plans/2026-07-12-dashboard-bundle-remediation.md.

PATCHES: list[tuple[str, ...]] = [
    (
        "componentDidMount: kick off real workspace load",
        "  componentDidMount() {\n"
        "    this._t = setInterval(() => this.setState({ now: new Date() }), 1000 * 30);",
        "  componentDidMount() {\n"
        "    this._t = setInterval(() => this.setState({ now: new Date() }), 1000 * 30);\n"
        "    this._loadRealWorkspace();",
    ),
    (
        "add _resolveUserKey/_apiHeaders/_loadRealWorkspace helpers",
        "  _resolveUserKey() {",  # stable marker -- see apply_patches docstring
        "  componentWillUnmount() { clearInterval(this._t); }\n",
        "  componentWillUnmount() { clearInterval(this._t); }\n\n"
        "  // --- Real backend wiring (dashboard bundle remediation, step 2) ---\n"
        "  // localStorage key matches the pre-bundle dashboard.js exactly, so a\n"
        "  // browser that already used this app reaches the same stored data.\n"
        "  _resolveUserKey() {\n"
        "    const STORAGE_KEY = \"smcr_user_key\";\n"
        "    let key = null;\n"
        "    try { key = window.localStorage.getItem(STORAGE_KEY); } catch (err) {}\n"
        "    if (!key) {\n"
        "      key = (typeof crypto !== \"undefined\" && crypto.randomUUID)\n"
        "        ? crypto.randomUUID()\n"
        "        : Date.now().toString(36) + \"-\" + Math.random().toString(36).slice(2, 10);\n"
        "      try { window.localStorage.setItem(STORAGE_KEY, key); } catch (err) {}\n"
        "    }\n"
        "    return key;\n"
        "  }\n"
        "  _apiHeaders(extra) {\n"
        "    const headers = Object.assign({}, extra || {});\n"
        "    if (window.__SMCR_API_KEY__) headers[\"X-Local-API-Key\"] = window.__SMCR_API_KEY__;\n"
        "    return headers;\n"
        "  }\n"
        "  async _loadRealWorkspace() {\n"
        "    this.userKey = this._resolveUserKey();\n"
        "    try {\n"
        "      const res = await fetch(\"/dashboard/data/\" + encodeURIComponent(this.userKey), {\n"
        "        headers: this._apiHeaders(),\n"
        "      });\n"
        "      if (!res.ok) throw new Error(\"workspace fetch failed: \" + res.status);\n"
        "      const data = await res.json();\n"
        "      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n"
        "      this.setState({ actions, workspaceLoaded: true, workspaceLoadError: null });\n"
        "    } catch (err) {\n"
        "      this.setState({ workspaceLoadError: String((err && err.message) || err) });\n"
        "    }\n"
        "  }\n",
        # NOTE: _mapRealAction is intentionally NOT defined here -- it's its own
        # patch below ("add _mapRealAction helper"), inserted right after
        # _apiHeaders. Defining it here too would embed its body as a substring
        # of *this* patch's `new` text; the due-date patch that edits
        # _mapRealAction's body would then make this patch's `new` text stop
        # matching (idempotency check fails on substring, not method identity),
        # causing this whole block to be silently re-inserted and duplicated on
        # a second run. Learned this the hard way -- see git history.
    ),
    (
        "add _mapRealAction helper (with due-date round-trip already applied)",
        "  _apiHeaders(extra) {\n"
        "    const headers = Object.assign({}, extra || {});\n"
        "    if (window.__SMCR_API_KEY__) headers[\"X-Local-API-Key\"] = window.__SMCR_API_KEY__;\n"
        "    return headers;\n"
        "  }\n"
        "  async _loadRealWorkspace() {\n",
        "  _apiHeaders(extra) {\n"
        "    const headers = Object.assign({}, extra || {});\n"
        "    if (window.__SMCR_API_KEY__) headers[\"X-Local-API-Key\"] = window.__SMCR_API_KEY__;\n"
        "    return headers;\n"
        "  }\n"
        '  _mapRealAction(a) {\n'
        '    // addAction stashes free-text "due" as "Due: <text>\\n<rest>" in notes\n'
        '    // (ActionRecord has no matching free-text field -- suspense_date is a\n'
        '    // strict date and the UI supports non-date values like "overdue" or\n'
        '    // "before drill"). Parse it back out here so it survives a reload\n'
        '    // instead of only showing up in the Notes field.\n'
        '    const notes = a.notes || "";\n'
        '    const dueMatch = /^Due: ([^\\n]+)\\n?([\\s\\S]*)$/.exec(notes);\n'
        '    return {\n'
        '      id: a.action_id,\n'
        '      title: a.title,\n'
        '      owner: a.owner || "Unassigned",\n'
        '      due: a.suspense_date || (dueMatch ? dueMatch[1] : "unscheduled"),\n'
        '      done: a.status === "closed" || a.status === "complete",\n'
        '      notes: dueMatch ? dueMatch[2] : notes,\n'
        '      editOpen: false,\n'
        '    };\n'
        '  }\n'
        "  async _loadRealWorkspace() {\n",
    ),
    (
        "toggleActionDone: PATCH /actions/{id} with optimistic update + rollback",
        "  toggleActionDone(id) {\n"
        "    return () => this.setState((s) => ({ actions: s.actions.map((a) => (a.id === id ? { ...a, done: !a.done } : a)) }));\n"
        "  }\n",
        "  toggleActionDone(id) {\n"
        "    return () => {\n"
        "      const current = this.state.actions.find((a) => a.id === id);\n"
        "      if (!current) return;\n"
        "      const nextDone = !current.done;\n"
        "      this.setState((s) => ({ actions: s.actions.map((a) => (a.id === id ? { ...a, done: nextDone } : a)) }));\n"
        "      fetch(\"/actions/\" + encodeURIComponent(id), {\n"
        "        method: \"PATCH\",\n"
        "        headers: this._apiHeaders({ \"Content-Type\": \"application/json\" }),\n"
        "        body: JSON.stringify({ status: nextDone ? \"closed\" : \"open\" }),\n"
        "      })\n"
        "        .then((res) => { if (!res.ok) throw new Error(\"update failed: \" + res.status); })\n"
        "        .catch(() => {\n"
        "          this.setState((s) => ({ actions: s.actions.map((a) => (a.id === id ? { ...a, done: !nextDone } : a)) }));\n"
        "          window.alert(\"Could not save that change to the server. Reverted.\");\n"
        "        });\n"
        "    };\n"
        "  }\n",
    ),
    (
        "deleteAction: DELETE /actions/{id} with optimistic remove + rollback",
        "  deleteAction(id) {\n"
        "    return () => this.setState((s) => ({ actions: s.actions.filter((a) => a.id !== id) }));\n"
        "  }\n",
        "  deleteAction(id) {\n"
        "    return () => {\n"
        "      const removed = this.state.actions.find((a) => a.id === id);\n"
        "      this.setState((s) => ({ actions: s.actions.filter((a) => a.id !== id) }));\n"
        "      fetch(\"/actions/\" + encodeURIComponent(id), { method: \"DELETE\", headers: this._apiHeaders() })\n"
        "        .then((res) => { if (res.status !== 204 && !res.ok) throw new Error(\"delete failed: \" + res.status); })\n"
        "        .catch(() => {\n"
        "          if (removed) this.setState((s) => ({ actions: [...s.actions, removed] }));\n"
        "          window.alert(\"Could not delete that action on the server. Restored.\");\n"
        "        });\n"
        "    };\n"
        "  }\n",
    ),
    (
        "addAction: POST /actions/track, replace local temp entry with server response",
        "  addAction(e) {\n"
        "    e.preventDefault();\n"
        "    const title = (this.state.draftActionTitle || \"\").trim();\n"
        "    if (!title) return;\n"
        "    const owner = (this.state.draftActionOwner || \"\").trim() || \"You\";\n"
        "    const due = (this.state.draftActionDue || \"\").trim() || \"unscheduled\";\n"
        "    this.setState((s) => ({\n"
        "      actions: [...s.actions, { id: Date.now(), title, owner, due, done: false, notes: \"\", editOpen: false }],\n"
        "      addActionOpen: false,\n"
        "      draftActionTitle: \"\",\n"
        "      draftActionOwner: \"\",\n"
        "      draftActionDue: \"\",\n"
        "    }));",
        "  addAction(e) {\n"
        "    e.preventDefault();\n"
        "    const title = (this.state.draftActionTitle || \"\").trim();\n"
        "    if (!title) return;\n"
        "    const owner = (this.state.draftActionOwner || \"\").trim() || \"You\";\n"
        "    const due = (this.state.draftActionDue || \"\").trim() || \"unscheduled\";\n"
        "    const tempId = \"pending-\" + Date.now();\n"
        "    this.setState((s) => ({\n"
        "      actions: [...s.actions, { id: tempId, title, owner, due, done: false, notes: \"\", editOpen: false, saving: true }],\n"
        "      addActionOpen: false,\n"
        "      draftActionTitle: \"\",\n"
        "      draftActionOwner: \"\",\n"
        "      draftActionDue: \"\",\n"
        "    }));\n"
        "    const notes = due && due !== \"unscheduled\" ? \"Due: \" + due : \"\";\n"
        "    fetch(\"/actions/track\", {\n"
        "      method: \"POST\",\n"
        "      headers: this._apiHeaders({ \"Content-Type\": \"application/json\" }),\n"
        "      body: JSON.stringify({ actions: [{ user_key: this.userKey, title, owner, notes, status: \"open\" }] }),\n"
        "    })\n"
        "      .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n"
        "      .then(({ ok, body }) => {\n"
        "        const tracked = ok && body.tracked && body.tracked[0];\n"
        "        if (!tracked) throw new Error(\"save failed\");\n"
        "        this.setState((s) => ({ actions: s.actions.map((a) => (a.id === tempId ? this._mapRealAction(tracked) : a)) }));\n"
        "      })\n"
        "      .catch(() => {\n"
        "        this.setState((s) => ({ actions: s.actions.filter((a) => a.id !== tempId) }));\n"
        "        window.alert(\"Could not save this action to the server. It was not added.\");\n"
        "      });",
    ),
    (
        "componentDidMount: also load real feeds, links, and handoff/profile",
        "  componentDidMount() {\n"
        "    this._t = setInterval(() => this.setState({ now: new Date() }), 1000 * 30);\n"
        "    this._loadRealWorkspace();",
        "  componentDidMount() {\n"
        "    this._t = setInterval(() => this.setState({ now: new Date() }), 1000 * 30);\n"
        "    this._loadRealWorkspace();\n"
        "    this._loadRealFeeds();\n"
        "    this._loadRealLinks();\n"
        "    this._loadRealHandoff();",
    ),
    (
        "add _loadRealFeeds/_loadRealLinks/_loadRealHandoff helpers",
        "  async _loadRealFeeds() {",  # stable marker -- see apply_patches docstring
        '  async _loadRealWorkspace() {\n'
        '    this.userKey = this._resolveUserKey();\n'
        '    try {\n'
        '      const res = await fetch("/dashboard/data/" + encodeURIComponent(this.userKey), {\n'
        '        headers: this._apiHeaders(),\n'
        '      });\n'
        '      if (!res.ok) throw new Error("workspace fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n'
        '      this.setState({ actions, workspaceLoaded: true, workspaceLoadError: null });\n'
        '    } catch (err) {\n'
        '      this.setState({ workspaceLoadError: String((err && err.message) || err) });\n'
        '    }\n'
        '  }\n'
        '\n'
        '  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n',
        '  async _loadRealWorkspace() {\n'
        '    this.userKey = this._resolveUserKey();\n'
        '    try {\n'
        '      const res = await fetch("/dashboard/data/" + encodeURIComponent(this.userKey), {\n'
        '        headers: this._apiHeaders(),\n'
        '      });\n'
        '      if (!res.ok) throw new Error("workspace fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n'
        '      this.setState({ actions, workspaceLoaded: true, workspaceLoadError: null });\n'
        '    } catch (err) {\n'
        '      this.setState({ workspaceLoadError: String((err && err.message) || err) });\n'
        '    }\n'
        '  }\n'
        '\n'
        '  // --- Feeds: real backend wiring. Custom watch feeds are global (no\n'
        '  // per-user scoping on the backend), so the built-in demo feeds\n'
        '  // (MARADMIN/NAVADMIN/etc, which have no backend record at all) stay\n'
        '  // local and only real ones (marked isReal) round-trip through the API.\n'
        '  _feedTrustToLevel(trust) {\n'
        '    const MAP = { Official: "official", Professional: "professional", Unit: "unit_local", Custom: "personal_watch" };\n'
        '    return MAP[trust] || "personal_watch";\n'
        '  }\n'
        '  _mapRealFeed(f) {\n'
        '    const REVERSE = { official: "Official", professional: "Professional", unit_local: "Unit", personal_watch: "Custom", low_trust: "Custom" };\n'
        '    return {\n'
        '      id: f.feed_id,\n'
        '      name: f.name,\n'
        '      meta: f.category || "",\n'
        '      trust: REVERSE[f.trust_level] || "Custom",\n'
        '      type: "url",\n'
        '      url: f.url,\n'
        '      staticItems: null,\n'
        '      editOpen: false,\n'
        '      isReal: true,\n'
        '    };\n'
        '  }\n'
        '  async _loadRealFeeds() {\n'
        '    try {\n'
        '      const res = await fetch("/custom-watch-feeds", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("feeds fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      const realFeeds = (data || []).map((f) => this._mapRealFeed(f));\n'
        '      this.setState((s) => ({ feeds: [...s.feeds.filter((f) => !f.isReal), ...realFeeds] }));\n'
        '    } catch (err) {\n'
        '      // Keep the built-in demo feeds visible even if this fails.\n'
        '    }\n'
        '  }\n'
        '\n'
        '  // --- Links: real backend wiring. Unlike feeds, the backend seed set\n'
        '  // (data/seed/resource_links.json) serves the same "always show curated\n'
        '  // links" purpose as the bundle\'s hardcoded linkGroups, so this fully\n'
        '  // replaces linkGroups from the real fetch rather than merging.\n'
        '  _mapRealLinkGroups(response) {\n'
        '    const categories = response.categories || {};\n'
        '    const order = [];\n'
        '    const groups = {};\n'
        '    (response.links || []).forEach((l) => {\n'
        '      const label = categories[l.category] || l.category;\n'
        '      if (!groups[label]) { groups[label] = { title: label, links: [] }; order.push(label); }\n'
        '      let host = l.url;\n'
        '      try { host = new URL(l.url).hostname.replace(/^www\\./, ""); } catch (err) {}\n'
        '      groups[label].links.push({ name: l.title, host, url: l.url, id: l.id, isSeed: l.is_seed });\n'
        '    });\n'
        '    return order.map((label) => groups[label]);\n'
        '  }\n'
        '  _categoryKeyForLabel(label) {\n'
        '    const dict = this._resourceLinkCategories || {};\n'
        '    const target = (label || "").trim().toLowerCase();\n'
        '    for (const key in dict) { if (dict[key].toLowerCase() === target) return key; }\n'
        '    return "unit";\n'
        '  }\n'
        '  async _loadRealLinks() {\n'
        '    try {\n'
        '      const res = await fetch("/resource-links/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("links fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      this._resourceLinkCategories = data.categories || {};\n'
        '      this.setState({ linkGroups: this._mapRealLinkGroups(data) });\n'
        '    } catch (err) {\n'
        '      // Keep the built-in demo link groups visible if this fails.\n'
        '    }\n'
        '  }\n'
        '\n'
        '  // --- Profile / handoff: real backend wiring. rank/display_name/\n'
        '  // billet/unit_id live on UserSessionHandoff (not /user-profile, which\n'
        '  // is a separate format-preference concept). No explicit Save button\n'
        '  // exists in this drawer, so field edits debounce into a PUT.\n'
        '  async _loadRealHandoff() {\n'
        '    try {\n'
        '      const res = await fetch("/handoffs/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) return; // 404 is normal for a brand-new profile -- keep blank fields.\n'
        '      const handoff = await res.json();\n'
        '      this._handoffData = handoff;\n'
        '      const rank = handoff.rank || "";\n'
        '      let lastName = "";\n'
        '      if (handoff.display_name) {\n'
        '        lastName = rank && handoff.display_name.indexOf(rank + " ") === 0\n'
        '          ? handoff.display_name.slice(rank.length + 1)\n'
        '          : handoff.display_name;\n'
        '      }\n'
        '      this.setState((s) => ({\n'
        '        profileRank: rank,\n'
        '        profileLastName: lastName,\n'
        '        profileBillet: handoff.billet || "",\n'
        '        profileUnit: handoff.unit_id || "",\n'
        '        demoModeManual: true,\n'
        '        demoMode: !(rank.trim() || lastName.trim()) && s.demoMode,\n'
        '      }));\n'
        '    } catch (err) {\n'
        '      // Keep whatever is already in state if this fails.\n'
        '    }\n'
        '  }\n'
        '  _scheduleHandoffSave() {\n'
        '    clearTimeout(this._handoffSaveTimer);\n'
        '    this._handoffSaveTimer = setTimeout(() => this._saveHandoff(), 800);\n'
        '  }\n'
        '  _saveHandoff() {\n'
        '    if (!this.userKey) return;\n'
        '    const base = this._handoffData || { user_key: this.userKey };\n'
        '    const payload = Object.assign({}, base, {\n'
        '      user_key: this.userKey,\n'
        '      rank: this.state.profileRank || null,\n'
        '      display_name: [this.state.profileRank, this.state.profileLastName].filter(Boolean).join(" ") || null,\n'
        '      billet: this.state.profileBillet || null,\n'
        '      unit_id: this.state.profileUnit || null,\n'
        '    });\n'
        '    fetch("/handoffs/" + encodeURIComponent(this.userKey), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '      body: JSON.stringify(payload),\n'
        '    })\n'
        '      .then((res) => { if (!res.ok) throw new Error("save failed: " + res.status); return res.json(); })\n'
        '      .then((body) => { this._handoffData = body.handoff; })\n'
        '      .catch(() => {});\n'
        '  }\n'
        '\n'
        '  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n',
    ),
    (
        "onSubmitFeed: POST /custom-watch-feeds for real feeds, keep manual/no-URL feeds local",
        '    const onSubmitFeed = (e) => {\n'
        '      e.preventDefault();\n'
        '      const name = (this.state.draftFeedName || "").trim();\n'
        '      if (!name) return;\n'
        '      const meta = (this.state.draftFeedMeta || "").trim();\n'
        '      const type = this.state.draftFeedType;\n'
        '      let url = (this.state.draftFeedUrl || "").trim();\n'
        '      if (type !== "manual" && url && !/^https?:\\/\\//i.test(url)) url = "https://" + url;\n'
        '      const trust = this.state.draftFeedTrust;\n'
        '      this.setState((s) => ({\n'
        '        feeds: [...s.feeds, { id: Date.now(), name, meta, type, url: type === "manual" ? "" : url, trust, staticItems: null, editOpen: false }],\n'
        '        addFeedOpen: false, draftFeedName: "", draftFeedMeta: "", draftFeedUrl: "", draftFeedType: "rss", draftFeedTrust: "Unit",\n'
        '      }));\n'
        '    };\n',
        '    const onSubmitFeed = (e) => {\n'
        '      e.preventDefault();\n'
        '      const name = (this.state.draftFeedName || "").trim();\n'
        '      if (!name) return;\n'
        '      const meta = (this.state.draftFeedMeta || "").trim();\n'
        '      const type = this.state.draftFeedType;\n'
        '      let url = (this.state.draftFeedUrl || "").trim();\n'
        '      if (type !== "manual" && url && !/^https?:\\/\\//i.test(url)) url = "https://" + url;\n'
        '      const trust = this.state.draftFeedTrust;\n'
        '      this.setState({ addFeedOpen: false, draftFeedName: "", draftFeedMeta: "", draftFeedUrl: "", draftFeedType: "rss", draftFeedTrust: "Unit" });\n'
        '      if (type === "manual" || !url) {\n'
        '        // No backend field for manual/no-URL feeds -- keep it local, matching the prior behavior.\n'
        '        this.setState((s) => ({ feeds: [...s.feeds, { id: Date.now(), name, meta, type, url: "", trust, staticItems: null, editOpen: false }] }));\n'
        '        return;\n'
        '      }\n'
        '      fetch("/custom-watch-feeds", {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify({ name, url, category: meta || "unit", trust_level: this._feedTrustToLevel(trust) }),\n'
        '      })\n'
        '        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n'
        '        .then(({ ok, body }) => {\n'
        '          if (!ok) throw new Error("save failed");\n'
        '          this.setState((s) => ({ feeds: [...s.feeds, this._mapRealFeed(body)] }));\n'
        '        })\n'
        '        .catch(() => window.alert("Could not save this feed to the server. It was not added."));\n'
        '    };\n',
    ),
    (
        "removeFeed: DELETE /custom-watch-feeds/{id} for real feeds only",
        '  removeFeed(id) {\n'
        '    return (e) => {\n'
        '      if (e) { e.preventDefault(); e.stopPropagation(); }\n'
        '      if (!window.confirm("Remove this feed?")) return;\n'
        '      this.setState((s) => ({ feeds: s.feeds.filter((f) => f.id !== id) }));\n'
        '    };\n'
        '  }\n',
        '  removeFeed(id) {\n'
        '    return (e) => {\n'
        '      if (e) { e.preventDefault(); e.stopPropagation(); }\n'
        '      if (!window.confirm("Remove this feed?")) return;\n'
        '      const removed = this.state.feeds.find((f) => f.id === id);\n'
        '      this.setState((s) => ({ feeds: s.feeds.filter((f) => f.id !== id) }));\n'
        '      if (!removed || !removed.isReal) return;\n'
        '      fetch("/custom-watch-feeds/" + encodeURIComponent(id), { method: "DELETE", headers: this._apiHeaders() })\n'
        '        .then((res) => { if (res.status !== 204 && !res.ok) throw new Error("delete failed: " + res.status); })\n'
        '        .catch(() => {\n'
        '          this.setState((s) => ({ feeds: [...s.feeds, removed] }));\n'
        '          window.alert("Could not delete that feed on the server. Restored.");\n'
        '        });\n'
        '    };\n'
        '  }\n',
    ),
    (
        "addLink: POST /resource-links/{userKey}",
        '  addLink(e) {\n'
        '    e.preventDefault();\n'
        '    const category = (this.state.newLinkCategory || "Custom links").trim() || "Custom links";\n'
        '    const name = (this.state.newLinkName || "").trim();\n'
        '    let url = (this.state.newLinkUrl || "").trim();\n'
        '    if (!name || !url) return;\n'
        '    if (!/^https?:\\/\\//i.test(url)) url = "https://" + url;\n'
        '    let host = url;\n'
        '    try { host = new URL(url).hostname.replace(/^www\\./, ""); } catch (e2) { /* keep raw */ }\n'
        '    this.setState((s) => {\n'
        '      const groups = s.linkGroups.map((g) => ({ ...g, links: g.links.slice() }));\n'
        '      const existing = groups.find((g) => g.title.toLowerCase() === category.toLowerCase());\n'
        '      if (existing) {\n'
        '        existing.links.push({ name, host, url });\n'
        '      } else {\n'
        '        groups.push({ title: category, links: [{ name, host, url }] });\n'
        '      }\n'
        '      return { linkGroups: groups, newLinkCategory: "", newLinkName: "", newLinkUrl: "" };\n'
        '    });\n'
        '  }\n',
        '  addLink(e) {\n'
        '    e.preventDefault();\n'
        '    const categoryLabel = (this.state.newLinkCategory || "Custom links").trim() || "Custom links";\n'
        '    const name = (this.state.newLinkName || "").trim();\n'
        '    let url = (this.state.newLinkUrl || "").trim();\n'
        '    if (!name || !url) return;\n'
        '    if (!/^https?:\\/\\//i.test(url)) url = "https://" + url;\n'
        '    this.setState({ newLinkCategory: "", newLinkName: "", newLinkUrl: "" });\n'
        '    const category = this._categoryKeyForLabel(categoryLabel);\n'
        '    fetch("/resource-links/" + encodeURIComponent(this.userKey), {\n'
        '      method: "POST",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '      body: JSON.stringify({ title: name, url, category, tags: [] }),\n'
        '    })\n'
        '      .then((res) => { if (!res.ok) throw new Error("save failed: " + res.status); })\n'
        '      .then(() => this._loadRealLinks())\n'
        '      .catch(() => window.alert("Could not save this link to the server. It was not added."));\n'
        '  }\n',
    ),
    (
        "profile field handlers: debounce a PUT /handoffs/{userKey} on every change",
        '      onBilletChange: (e) => this.setState({ profileBillet: e.target.value }),\n'
        '      onUnitChange: (e) => this.setState({ profileUnit: e.target.value }),\n'
        '      profilePasskey: this.state.profilePasskey,\n'
        '      onRankChange: (e) => {\n'
        '        const v = e.target.value;\n'
        '        this.setState((s) => ({ profileRank: v, demoMode: s.demoModeManual ? s.demoMode : !(v.trim() || s.profileLastName.trim()) }));\n'
        '      },\n'
        '      onLastNameChange: (e) => {\n'
        '        const v = e.target.value;\n'
        '        this.setState((s) => ({ profileLastName: v, demoMode: s.demoModeManual ? s.demoMode : !(v.trim() || s.profileRank.trim()) }));\n'
        '      },\n',
        '      onBilletChange: (e) => { this.setState({ profileBillet: e.target.value }); this._scheduleHandoffSave(); },\n'
        '      onUnitChange: (e) => { this.setState({ profileUnit: e.target.value }); this._scheduleHandoffSave(); },\n'
        '      profilePasskey: this.state.profilePasskey,\n'
        '      onRankChange: (e) => {\n'
        '        const v = e.target.value;\n'
        '        this.setState((s) => ({ profileRank: v, demoMode: s.demoModeManual ? s.demoMode : !(v.trim() || s.profileLastName.trim()) }));\n'
        '        this._scheduleHandoffSave();\n'
        '      },\n'
        '      onLastNameChange: (e) => {\n'
        '        const v = e.target.value;\n'
        '        this.setState((s) => ({ profileLastName: v, demoMode: s.demoModeManual ? s.demoMode : !(v.trim() || s.profileRank.trim()) }));\n'
        '        this._scheduleHandoffSave();\n'
        '      },\n',
    ),
    (
        "componentDidMount: also load real notebook, fitreps, generations, and project list",
        "  componentDidMount() {\n"
        "    this._t = setInterval(() => this.setState({ now: new Date() }), 1000 * 30);\n"
        "    this._loadRealWorkspace();\n"
        "    this._loadRealFeeds();\n"
        "    this._loadRealLinks();\n"
        "    this._loadRealHandoff();",
        "  componentDidMount() {\n"
        "    this._t = setInterval(() => this.setState({ now: new Date() }), 1000 * 30);\n"
        "    this._loadRealWorkspace();\n"
        "    this._loadRealFeeds();\n"
        "    this._loadRealLinks();\n"
        "    this._loadRealHandoff();\n"
        "    this._loadRealNotes();\n"
        "    this._loadRealFitreps();\n"
        "    this._loadRealGenerations();\n"
        "    this._loadRealProjects();",
    ),
    (
        "add User Docs helpers: notebook/fitreps/generations load + project list",
        "  async _loadRealNotes() {",  # stable marker -- see apply_patches docstring
        '  _saveHandoff() {\n'
        '    if (!this.userKey) return;\n'
        '    const base = this._handoffData || { user_key: this.userKey };\n'
        '    const payload = Object.assign({}, base, {\n'
        '      user_key: this.userKey,\n'
        '      rank: this.state.profileRank || null,\n'
        '      display_name: [this.state.profileRank, this.state.profileLastName].filter(Boolean).join(" ") || null,\n'
        '      billet: this.state.profileBillet || null,\n'
        '      unit_id: this.state.profileUnit || null,\n'
        '    });\n'
        '    fetch("/handoffs/" + encodeURIComponent(this.userKey), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '      body: JSON.stringify(payload),\n'
        '    })\n'
        '      .then((res) => { if (!res.ok) throw new Error("save failed: " + res.status); return res.json(); })\n'
        '      .then((body) => { this._handoffData = body.handoff; })\n'
        '      .catch(() => {});\n'
        '  }\n'
        '\n'
        '  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n',
        '  _saveHandoff() {\n'
        '    if (!this.userKey) return;\n'
        '    const base = this._handoffData || { user_key: this.userKey };\n'
        '    const payload = Object.assign({}, base, {\n'
        '      user_key: this.userKey,\n'
        '      rank: this.state.profileRank || null,\n'
        '      display_name: [this.state.profileRank, this.state.profileLastName].filter(Boolean).join(" ") || null,\n'
        '      billet: this.state.profileBillet || null,\n'
        '      unit_id: this.state.profileUnit || null,\n'
        '    });\n'
        '    fetch("/handoffs/" + encodeURIComponent(this.userKey), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '      body: JSON.stringify(payload),\n'
        '    })\n'
        '      .then((res) => { if (!res.ok) throw new Error("save failed: " + res.status); return res.json(); })\n'
        '      .then((body) => { this._handoffData = body.handoff; })\n'
        '      .catch(() => {});\n'
        '  }\n'
        '\n'
        '  // --- User Docs: real backend wiring for the personal notebook, FitRep\n'
        '  // writer, and staff-product generations from the Bench/Files workflow\n'
        '  // tiles. Each category is a real markdown file under settings.user_docs_dir\n'
        '  // (see app/services/user_docs/store.py), not a JSON blob like the other\n'
        '  // domains above -- so these can also be moved into a real project folder.\n'
        '  _isPending(id) {\n'
        '    return typeof id === "string" && id.indexOf("pending-") === 0;\n'
        '  }\n'
        '\n'
        '  // Notebook\n'
        '  _mapRealNote(entry) {\n'
        '    return { id: entry.id, title: entry.title, date: entry.updated_at.slice(0, 10), body: entry.body, archived: !!(entry.fields || {}).archived };\n'
        '  }\n'
        '  async _loadRealNotes() {\n'
        '    try {\n'
        '      const res = await fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("notebook fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      const notes = data.map((entry) => this._mapRealNote(entry));\n'
        '      const first = notes.find((n) => !n.archived) || notes[0];\n'
        '      this.setState({ notes, activeNoteId: first ? first.id : null, draftTitle: first ? first.title : "", draftBody: first ? first.body : "" });\n'
        '    } catch (err) {\n'
        '      // Keep the built-in demo notes visible if this fails.\n'
        '    }\n'
        '  }\n'
        '\n'
        '  // FitReps\n'
        '  _mapRealFitrep(entry) {\n'
        '    return Object.assign({ id: entry.id, name: entry.title, archived: false }, entry.fields || {});\n'
        '  }\n'
        '  _fitrepPayload(f) {\n'
        '    const fields = Object.assign({}, f);\n'
        '    delete fields.id;\n'
        '    delete fields.name;\n'
        '    return { title: f.name, fields };\n'
        '  }\n'
        '  async _loadRealFitreps() {\n'
        '    try {\n'
        '      const res = await fetch("/user-docs/fitreps/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("fitreps fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      const fitreps = data.map((entry) => this._mapRealFitrep(entry));\n'
        '      this.setState((s) => ({ fitreps, activeFitrepId: fitreps[0] ? fitreps[0].id : s.activeFitrepId }));\n'
        '    } catch (err) {\n'
        '      // Keep the built-in demo fitreps visible if this fails.\n'
        '    }\n'
        '  }\n'
        '  _scheduleFitrepSave(id) {\n'
        '    if (!id || this._isPending(id)) return;\n'
        '    this._fitrepSaveTimers = this._fitrepSaveTimers || {};\n'
        '    clearTimeout(this._fitrepSaveTimers[id]);\n'
        '    this._fitrepSaveTimers[id] = setTimeout(() => this._saveFitrep(id), 800);\n'
        '  }\n'
        '  _saveFitrep(id) {\n'
        '    const f = this.state.fitreps.find((x) => x.id === id);\n'
        '    if (!f) return;\n'
        '    fetch("/user-docs/fitreps/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), {\n'
        '      method: "PATCH",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '      body: JSON.stringify(this._fitrepPayload(f)),\n'
        '    }).catch(() => {});\n'
        '  }\n'
        '\n'
        '  // Generations (workflow-drafted staff products)\n'
        '  _mapRealGeneration(entry) {\n'
        '    const fields = entry.fields || {};\n'
        '    return {\n'
        '      id: entry.id,\n'
        '      title: entry.title,\n'
        '      templateType: fields.templateType,\n'
        '      kind: fields.kind,\n'
        '      path: fields.path || "",\n'
        '      receiptsFolder: fields.receiptsFolder || "",\n'
        '      receipts: fields.receipts || [],\n'
        '      created: entry.created_at.slice(0, 10),\n'
        '      data: fields.data || {},\n'
        '    };\n'
        '  }\n'
        '  _generationPayload(d) {\n'
        '    return {\n'
        '      title: d.title,\n'
        '      fields: {\n'
        '        templateType: d.templateType,\n'
        '        kind: d.kind,\n'
        '        path: d.path,\n'
        '        receiptsFolder: d.receiptsFolder,\n'
        '        receipts: d.receipts,\n'
        '        data: d.data,\n'
        '      },\n'
        '    };\n'
        '  }\n'
        '  async _loadRealGenerations() {\n'
        '    try {\n'
        '      const res = await fetch("/user-docs/generations/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("generations fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      this.setState({ workflowDocs: data.map((entry) => this._mapRealGeneration(entry)) });\n'
        '    } catch (err) {\n'
        '      // Keep whatever local drafts exist if this fails.\n'
        '    }\n'
        '  }\n'
        '  _scheduleGenerationSave(id) {\n'
        '    if (!id || this._isPending(id)) return;\n'
        '    this._generationSaveTimers = this._generationSaveTimers || {};\n'
        '    clearTimeout(this._generationSaveTimers[id]);\n'
        '    this._generationSaveTimers[id] = setTimeout(() => this._saveGeneration(id), 800);\n'
        '  }\n'
        '  _saveGeneration(id) {\n'
        '    const d = this.state.workflowDocs.find((x) => x.id === id);\n'
        '    if (!d) return;\n'
        '    fetch("/user-docs/generations/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), {\n'
        '      method: "PATCH",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '      body: JSON.stringify(this._generationPayload(d)),\n'
        '    }).catch(() => {});\n'
        '  }\n'
        '\n'
        '  // Real project folder names, for the "Save to project" dropdown\n'
        '  async _loadRealProjects() {\n'
        '    try {\n'
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        '      this._realProjectNames = await res.json();\n'
        '      this.forceUpdate();\n'
        '    } catch (err) {\n'
        '      this._realProjectNames = [];\n'
        '    }\n'
        '  }\n'
        '\n'
        '  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n',
    ),
    (
        "newNote: POST /user-docs/notebook",
        '  newNote() {\n'
        '    return () => {\n'
        '      const id = Date.now();\n'
        '      const n = { id, title: "Untitled note", date: "today", body: "", archived: false };\n'
        '      this.setState((s) => ({ notes: [n, ...s.notes], activeNoteId: id, draftTitle: n.title, draftBody: "" }));\n'
        '    };\n'
        '  }\n',
        '  newNote() {\n'
        '    return () => {\n'
        '      const tempId = "pending-" + Date.now();\n'
        '      const n = { id: tempId, title: "Untitled note", date: "today", body: "", archived: false };\n'
        '      this.setState((s) => ({ notes: [n, ...s.notes], activeNoteId: tempId, draftTitle: n.title, draftBody: "" }));\n'
        '      fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey), {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify({ title: n.title, body: "" }),\n'
        '      })\n'
        '        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n'
        '        .then(({ ok, body }) => {\n'
        '          if (!ok) throw new Error("save failed");\n'
        '          const real = this._mapRealNote(body);\n'
        '          this.setState((s) => ({\n'
        '            notes: s.notes.map((x) => (x.id === tempId ? real : x)),\n'
        '            activeNoteId: s.activeNoteId === tempId ? real.id : s.activeNoteId,\n'
        '          }));\n'
        '        })\n'
        '        .catch(() => {\n'
        '          this.setState((s) => ({ notes: s.notes.filter((x) => x.id !== tempId) }));\n'
        '          window.alert("Could not save this note to the server. It was not added.");\n'
        '        });\n'
        '    };\n'
        '  }\n',
    ),
    (
        "saveNote: PATCH /user-docs/notebook/{id}",
        '  saveNote() {\n'
        '    return () => {\n'
        '      this.setState((s) => ({\n'
        '        notes: s.notes.map((n) => (n.id === s.activeNoteId ? { ...n, title: s.draftTitle || "Untitled note", body: s.draftBody } : n)),\n'
        '      }));\n'
        '    };\n'
        '  }\n',
        '  saveNote() {\n'
        '    return () => {\n'
        '      const id = this.state.activeNoteId;\n'
        '      const title = this.state.draftTitle || "Untitled note";\n'
        '      const body = this.state.draftBody;\n'
        '      this.setState((s) => ({ notes: s.notes.map((n) => (n.id === id ? { ...n, title, body } : n)) }));\n'
        '      if (this._isPending(id)) return;\n'
        '      fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), {\n'
        '        method: "PATCH",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify({ title, body }),\n'
        '      }).catch(() => window.alert("Could not save this note to the server."));\n'
        '    };\n'
        '  }\n',
    ),
    (
        "deleteNote: DELETE /user-docs/notebook/{id}",
        '  deleteNote() {\n'
        '    return () => {\n'
        '      const n = this.state.notes.find((x) => x.id === this.state.activeNoteId);\n'
        '      if (!window.confirm(`Permanently delete "${n ? n.title : "this note"}"? This cannot be undone.`)) return;\n'
        '      this.setState((s) => {\n'
        '        const notes = s.notes.filter((x) => x.id !== s.activeNoteId);\n'
        '        const next = notes[0];\n'
        '        return { notes, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" };\n'
        '      });\n'
        '    };\n'
        '  }\n',
        '  deleteNote() {\n'
        '    return () => {\n'
        '      const n = this.state.notes.find((x) => x.id === this.state.activeNoteId);\n'
        '      if (!window.confirm(`Permanently delete "${n ? n.title : "this note"}"? This cannot be undone.`)) return;\n'
        '      const deletedId = this.state.activeNoteId;\n'
        '      this.setState((s) => {\n'
        '        const notes = s.notes.filter((x) => x.id !== s.activeNoteId);\n'
        '        const next = notes[0];\n'
        '        return { notes, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" };\n'
        '      });\n'
        '      if (!this._isPending(deletedId)) {\n'
        '        fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(deletedId), { method: "DELETE", headers: this._apiHeaders() }).catch(() => {});\n'
        '      }\n'
        '    };\n'
        '  }\n',
    ),
    (
        "archiveNote: persist the archived flag",
        '  archiveNote(archived) {\n'
        '    return () => {\n'
        '      this.setState((s) => {\n'
        '        const notes = s.notes.map((n) => (n.id === s.activeNoteId ? { ...n, archived } : n));\n'
        '        const pool = notes.filter((n) => !!n.archived === (s.noteView === "archived"));\n'
        '        const next = pool[0] || null;\n'
        '        return { notes, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" };\n'
        '      });\n'
        '    };\n'
        '  }\n',
        '  archiveNote(archived) {\n'
        '    return () => {\n'
        '      const targetId = this.state.activeNoteId;\n'
        '      this.setState((s) => {\n'
        '        const notes = s.notes.map((n) => (n.id === s.activeNoteId ? { ...n, archived } : n));\n'
        '        const pool = notes.filter((n) => !!n.archived === (s.noteView === "archived"));\n'
        '        const next = pool[0] || null;\n'
        '        return { notes, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" };\n'
        '      });\n'
        '      if (!this._isPending(targetId)) {\n'
        '        fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(targetId), {\n'
        '          method: "PATCH",\n'
        '          headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '          body: JSON.stringify({ fields: { archived } }),\n'
        '        }).catch(() => {});\n'
        '      }\n'
        '    };\n'
        '  }\n',
    ),
    (
        "newFitrep: POST /user-docs/fitreps",
        '  newFitrep() {\n'
        '    return () => {\n'
        '      const id = Date.now();\n'
        '      const f = { id, name: "New Marine", rank: "", unit: "", period: "", role: "RS", scores: { mission: 4, individual: 4, leadership: 4, intellect: 4, fitness: 4 }, statement: "", notes: "", tree: 0, roComments: "", archived: false };\n'
        '      this.setState((s) => ({ fitreps: [f, ...s.fitreps], activeFitrepId: id }));\n'
        '    };\n'
        '  }\n',
        '  newFitrep() {\n'
        '    return () => {\n'
        '      const tempId = "pending-" + Date.now();\n'
        '      const f = { id: tempId, name: "New Marine", rank: "", unit: "", period: "", role: "RS", scores: { mission: 4, individual: 4, leadership: 4, intellect: 4, fitness: 4 }, statement: "", notes: "", tree: 0, roComments: "", archived: false };\n'
        '      this.setState((s) => ({ fitreps: [f, ...s.fitreps], activeFitrepId: tempId }));\n'
        '      fetch("/user-docs/fitreps/" + encodeURIComponent(this.userKey), {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify(this._fitrepPayload(f)),\n'
        '      })\n'
        '        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n'
        '        .then(({ ok, body }) => {\n'
        '          if (!ok) throw new Error("save failed");\n'
        '          const real = this._mapRealFitrep(body);\n'
        '          this.setState((s) => ({\n'
        '            fitreps: s.fitreps.map((x) => (x.id === tempId ? real : x)),\n'
        '            activeFitrepId: s.activeFitrepId === tempId ? real.id : s.activeFitrepId,\n'
        '          }));\n'
        '        })\n'
        '        .catch(() => {\n'
        '          this.setState((s) => ({ fitreps: s.fitreps.filter((x) => x.id !== tempId) }));\n'
        '          window.alert("Could not save this report to the server. It was not added.");\n'
        '        });\n'
        '    };\n'
        '  }\n',
    ),
    (
        "updateFitrepField: debounce a PATCH /user-docs/fitreps/{id}",
        '  updateFitrepField(field) {\n'
        '    return (e) => {\n'
        '      const val = e.target.value;\n'
        '      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, [field]: val } : f)) }));\n'
        '    };\n'
        '  }\n',
        '  updateFitrepField(field) {\n'
        '    return (e) => {\n'
        '      const val = e.target.value;\n'
        '      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, [field]: val } : f)) }));\n'
        '      this._scheduleFitrepSave(this.state.activeFitrepId);\n'
        '    };\n'
        '  }\n',
    ),
    (
        "setFitrepRole: debounce a PATCH /user-docs/fitreps/{id}",
        '  setFitrepRole(role) {\n'
        '    return () => this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, role } : f)) }));\n'
        '  }\n',
        '  setFitrepRole(role) {\n'
        '    return () => {\n'
        '      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, role } : f)) }));\n'
        '      this._scheduleFitrepSave(this.state.activeFitrepId);\n'
        '    };\n'
        '  }\n',
    ),
    (
        "updateFitrepScore: debounce a PATCH /user-docs/fitreps/{id}",
        '  updateFitrepScore(traitId) {\n'
        '    return (e) => {\n'
        '      const val = parseInt(e.target.value, 10);\n'
        '      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, scores: { ...f.scores, [traitId]: val } } : f)) }));\n'
        '    };\n'
        '  }\n',
        '  updateFitrepScore(traitId) {\n'
        '    return (e) => {\n'
        '      const val = parseInt(e.target.value, 10);\n'
        '      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, scores: { ...f.scores, [traitId]: val } } : f)) }));\n'
        '      this._scheduleFitrepSave(this.state.activeFitrepId);\n'
        '    };\n'
        '  }\n',
    ),
    (
        "deleteFitrep: DELETE /user-docs/fitreps/{id}",
        '  deleteFitrep() {\n'
        '    return () => {\n'
        '      const active = this.state.fitreps.find((f) => f.id === this.state.activeFitrepId);\n'
        '      const name = active ? active.name : "this report";\n'
        '      if (!window.confirm(`Permanently delete the tracked report for ${name}? This cannot be undone. Consider Archive instead if you just want it out of the active list.`)) return;\n'
        '      this.setState((s) => {\n'
        '        const fitreps = s.fitreps.filter((f) => f.id !== s.activeFitrepId);\n'
        '        const visible = fitreps.filter((f) => !f.archived);\n'
        '        return { fitreps, activeFitrepId: visible[0] ? visible[0].id : (fitreps[0] ? fitreps[0].id : null) };\n'
        '      });\n'
        '    };\n'
        '  }\n',
        '  deleteFitrep() {\n'
        '    return () => {\n'
        '      const active = this.state.fitreps.find((f) => f.id === this.state.activeFitrepId);\n'
        '      const name = active ? active.name : "this report";\n'
        '      if (!window.confirm(`Permanently delete the tracked report for ${name}? This cannot be undone. Consider Archive instead if you just want it out of the active list.`)) return;\n'
        '      const deletedId = this.state.activeFitrepId;\n'
        '      this.setState((s) => {\n'
        '        const fitreps = s.fitreps.filter((f) => f.id !== s.activeFitrepId);\n'
        '        const visible = fitreps.filter((f) => !f.archived);\n'
        '        return { fitreps, activeFitrepId: visible[0] ? visible[0].id : (fitreps[0] ? fitreps[0].id : null) };\n'
        '      });\n'
        '      if (!this._isPending(deletedId)) {\n'
        '        fetch("/user-docs/fitreps/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(deletedId), { method: "DELETE", headers: this._apiHeaders() }).catch(() => {});\n'
        '      }\n'
        '    };\n'
        '  }\n',
    ),
    (
        "archiveFitrep: persist the archived flag",
        '  archiveFitrep(archived) {\n'
        '    return () => {\n'
        '      this.setState((s) => {\n'
        '        const fitreps = s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, archived } : f));\n'
        '        const pool = fitreps.filter((f) => !!f.archived === (s.fitrepView === "archived"));\n'
        '        return { fitreps, activeFitrepId: pool[0] ? pool[0].id : null };\n'
        '      });\n'
        '    };\n'
        '  }\n',
        '  archiveFitrep(archived) {\n'
        '    return () => {\n'
        '      const targetId = this.state.activeFitrepId;\n'
        '      this.setState((s) => {\n'
        '        const fitreps = s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, archived } : f));\n'
        '        const pool = fitreps.filter((f) => !!f.archived === (s.fitrepView === "archived"));\n'
        '        return { fitreps, activeFitrepId: pool[0] ? pool[0].id : null };\n'
        '      });\n'
        '      this._scheduleFitrepSave(targetId);\n'
        '    };\n'
        '  }\n',
    ),
    (
        "setTree: debounce a PATCH /user-docs/fitreps/{id}",
        '  setTree(n) {\n'
        '    return () => this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, tree: n } : f)) }));\n'
        '  }\n',
        '  setTree(n) {\n'
        '    return () => {\n'
        '      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, tree: n } : f)) }));\n'
        '      this._scheduleFitrepSave(this.state.activeFitrepId);\n'
        '    };\n'
        '  }\n',
    ),
    (
        "createWorkflowDoc: POST /user-docs/generations",
        '  createWorkflowDoc(w) {\n'
        '    return () => {\n'
        '      const id = Date.now();\n'
        '      const slug = w.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");\n'
        '      const tpl = Component.WORKFLOW_TEMPLATES[w.templateType];\n'
        '      const data = {};\n'
        '      tpl.fields.forEach((f) => { data[f.key] = ""; });\n'
        '      if (w.templateType === "awards") data.awardType = Component.AWARD_TYPES[0].value;\n'
        '      const doc = {\n'
        '        id, title: w.title, templateType: w.templateType, kind: w.kind,\n'
        '        path: `projects/_drafts/${slug}-${id}.md`,\n'
        '        receiptsFolder: `projects/_drafts/${slug}-${id}-receipts/`,\n'
        '        receipts: [],\n'
        '        created: "today",\n'
        '        data,\n'
        '      };\n'
        '      this.setState((s) => ({ workflowDocs: [doc, ...s.workflowDocs], workflowEditorId: id }));\n'
        '    };\n'
        '  }\n',
        '  createWorkflowDoc(w) {\n'
        '    return () => {\n'
        '      const tempId = "pending-" + Date.now();\n'
        '      const slug = w.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");\n'
        '      const tpl = Component.WORKFLOW_TEMPLATES[w.templateType];\n'
        '      const data = {};\n'
        '      tpl.fields.forEach((f) => { data[f.key] = ""; });\n'
        '      if (w.templateType === "awards") data.awardType = Component.AWARD_TYPES[0].value;\n'
        '      const doc = {\n'
        '        id: tempId, title: w.title, templateType: w.templateType, kind: w.kind,\n'
        '        path: `User Docs/Generations/${slug}-${tempId}.md`,\n'
        '        receiptsFolder: `projects/_drafts/${slug}-${tempId}-receipts/`,\n'
        '        receipts: [],\n'
        '        created: "today",\n'
        '        data,\n'
        '      };\n'
        '      this.setState((s) => ({ workflowDocs: [doc, ...s.workflowDocs], workflowEditorId: tempId }));\n'
        '      fetch("/user-docs/generations/" + encodeURIComponent(this.userKey), {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify(this._generationPayload(doc)),\n'
        '      })\n'
        '        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n'
        '        .then(({ ok, body }) => {\n'
        '          if (!ok) throw new Error("save failed");\n'
        '          const real = this._mapRealGeneration(body);\n'
        '          this.setState((s) => ({\n'
        '            workflowDocs: s.workflowDocs.map((x) => (x.id === tempId ? real : x)),\n'
        '            workflowEditorId: s.workflowEditorId === tempId ? real.id : s.workflowEditorId,\n'
        '          }));\n'
        '        })\n'
        '        .catch(() => {\n'
        '          this.setState((s) => ({ workflowDocs: s.workflowDocs.filter((x) => x.id !== tempId) }));\n'
        '          window.alert("Could not save this draft to the server. It was not added.");\n'
        '        });\n'
        '    };\n'
        '  }\n',
    ),
    (
        "updateWorkflowField: debounce a PATCH /user-docs/generations/{id}",
        '  updateWorkflowField(id, field) {\n'
        '    return (e) => {\n'
        '      const val = e.target.value;\n'
        '      this.setState((s) => ({ workflowDocs: s.workflowDocs.map((d) => (d.id === id ? { ...d, data: { ...d.data, [field]: val } } : d)) }));\n'
        '    };\n'
        '  }\n',
        '  updateWorkflowField(id, field) {\n'
        '    return (e) => {\n'
        '      const val = e.target.value;\n'
        '      this.setState((s) => ({ workflowDocs: s.workflowDocs.map((d) => (d.id === id ? { ...d, data: { ...d.data, [field]: val } } : d)) }));\n'
        '      this._scheduleGenerationSave(id);\n'
        '    };\n'
        '  }\n',
    ),
    (
        "deleteWorkflowDoc: DELETE /user-docs/generations/{id}",
        '  deleteWorkflowDoc(id) {\n'
        '    return () => {\n'
        '      if (!window.confirm("Delete this draft? This cannot be undone.")) return;\n'
        '      this.setState((s) => ({ workflowDocs: s.workflowDocs.filter((d) => d.id !== id), workflowEditorId: s.workflowEditorId === id ? null : s.workflowEditorId }));\n'
        '    };\n'
        '  }\n',
        '  deleteWorkflowDoc(id) {\n'
        '    return () => {\n'
        '      if (!window.confirm("Delete this draft? This cannot be undone.")) return;\n'
        '      this.setState((s) => ({ workflowDocs: s.workflowDocs.filter((d) => d.id !== id), workflowEditorId: s.workflowEditorId === id ? null : s.workflowEditorId }));\n'
        '      if (!this._isPending(id)) {\n'
        '        fetch("/user-docs/generations/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), { method: "DELETE", headers: this._apiHeaders() }).catch(() => {});\n'
        '      }\n'
        '    };\n'
        '  }\n',
    ),
    (
        "moveWorkflowDocToProject: real POST /user-docs/generations/{id}/save-to-project",
        '  moveWorkflowDocToProject(docId) {\n'
        '    return () => {\n'
        '      const folder = this.state.draftMoveTarget[docId];\n'
        '      if (!folder) return;\n'
        '      this.setState((s) => {\n'
        '        const doc = s.workflowDocs.find((d) => d.id === docId);\n'
        '        if (!doc) return null;\n'
        '        const slug = doc.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");\n'
        '        const newPath = `projects/${folder}/${slug}.md`;\n'
        '        const benchCards = s.benchCards.map((c) => (c.title !== "Project files" ? c : {\n'
        '          ...c,\n'
        '          items: [...c.items, { name: doc.title, meta: "moved draft", path: newPath }],\n'
        '        }));\n'
        '        return {\n'
        '          benchCards,\n'
        '          workflowDocs: s.workflowDocs.filter((d) => d.id !== docId),\n'
        '          workflowEditorId: s.workflowEditorId === docId ? null : s.workflowEditorId,\n'
        '        };\n'
        '      });\n'
        '    };\n'
        '  }\n',
        '  moveWorkflowDocToProject(docId) {\n'
        '    return () => {\n'
        '      const folder = this.state.draftMoveTarget[docId];\n'
        '      if (!folder) return;\n'
        '      const doc = this.state.workflowDocs.find((d) => d.id === docId);\n'
        '      if (!doc) return;\n'
        '      const finish = (newPath) => {\n'
        '        this.setState((s) => {\n'
        '          const benchCards = s.benchCards.map((c) => (c.title !== "Project files" ? c : {\n'
        '            ...c,\n'
        '            items: [...c.items, { name: doc.title, meta: "moved draft", path: newPath }],\n'
        '          }));\n'
        '          return {\n'
        '            benchCards,\n'
        '            workflowDocs: s.workflowDocs.filter((d) => d.id !== docId),\n'
        '            workflowEditorId: s.workflowEditorId === docId ? null : s.workflowEditorId,\n'
        '          };\n'
        '        });\n'
        '      };\n'
        '      if (this._isPending(docId)) {\n'
        '        const slug = doc.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");\n'
        '        finish(`projects/${folder}/${slug}.md`);\n'
        '        return;\n'
        '      }\n'
        '      fetch("/user-docs/generations/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(docId) + "/save-to-project", {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify({ project: folder }),\n'
        '      })\n'
        '        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n'
        '        .then(({ ok, body }) => {\n'
        '          if (!ok) throw new Error("save failed");\n'
        '          finish(body.path);\n'
        '          this._loadRealProjects();\n'
        '        })\n'
        '        .catch(() => window.alert("Could not save this draft to the project. It is still in Drafted files."));\n'
        '    };\n'
        '  }\n',
    ),
    (
        "projectFolderNames: include real project folders alongside the local bench card list",
        '    const projectFolderNames = ((this.state.benchCards.find((c) => c.title === "Project files") || { items: [] }).items || []).map((it) => it.name);\n',
        '    const projectFolderNames = Array.from(new Set([\n'
        '      ...((this.state.benchCards.find((c) => c.title === "Project files") || { items: [] }).items || []).map((it) => it.name),\n'
        '      ...(this._realProjectNames || []),\n'
        '    ]));\n',
    ),
    (
        "componentDidMount: also load the real agent/skill catalog, prompt packs, and agent notes",
        "    this._loadRealNotes();\n"
        "    this._loadRealFitreps();\n"
        "    this._loadRealGenerations();\n"
        "    this._loadRealProjects();\n",
        "    this._loadRealNotes();\n"
        "    this._loadRealFitreps();\n"
        "    this._loadRealGenerations();\n"
        "    this._loadRealProjects();\n"
        "    this._loadRealAgents();\n"
        "    this._loadRealSkills();\n"
        "    this._loadRealPromptPacks();\n"
        "    this._loadRealAgentNotes();\n",
    ),
    (
        "add AI-page helpers: real agents/skills/prompt-packs catalog + notes",
        "  async _loadRealAgents() {",  # stable marker -- see apply_patches docstring
        '  // Real project folder names, for the "Save to project" dropdown\n'
        '  async _loadRealProjects() {\n'
        '    try {\n'
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        '      this._realProjectNames = await res.json();\n'
        '      this.forceUpdate();\n'
        '    } catch (err) {\n'
        '      this._realProjectNames = [];\n'
        '    }\n'
        '  }\n'
        '\n'
        '  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n',
        '  // Real project folder names, for the "Save to project" dropdown\n'
        '  async _loadRealProjects() {\n'
        '    try {\n'
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        '      this._realProjectNames = await res.json();\n'
        '      this.forceUpdate();\n'
        '    } catch (err) {\n'
        '      this._realProjectNames = [];\n'
        '    }\n'
        '  }\n'
        '\n'
        '  // --- AI page: real agent/skill catalog + notes backend wiring.\n'
        '  // AGENTS_CATALOG/SKILLS_CATALOG are static class fields the demo bundle\n'
        '  // hardcoded; reassigning them at runtime (then forceUpdate) is far less\n'
        '  // invasive than converting every render-time reference to state.\n'
        '  async _loadRealAgents() {\n'
        '    try {\n'
        '      const res = await fetch("/agents", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("agents fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      Component.AGENTS_CATALOG = data.map((a) => ({\n'
        '        id: a.id,\n'
        '        name: a.name,\n'
        '        category: a.domain,\n'
        '        description: a.description,\n'
        '        limitations: (a.disallowed_inputs || []).join(", ") || "None listed.",\n'
        '      }));\n'
        '      this.forceUpdate();\n'
        '    } catch (err) {\n'
        '      // Keep the built-in demo catalog visible if this fails.\n'
        '    }\n'
        '  }\n'
        '  async _loadRealSkills() {\n'
        '    try {\n'
        '      const res = await fetch("/skills", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("skills fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      Component.SKILLS_CATALOG = (data.skills || []).map((s) => ({ slug: s.name, name: s.name, description: s.description }));\n'
        '      this.forceUpdate();\n'
        '    } catch (err) {\n'
        '      // Keep the built-in demo catalog visible if this fails.\n'
        '    }\n'
        '  }\n'
        '  async _loadRealPromptPacks() {\n'
        '    try {\n'
        '      const res = await fetch("/prompt-packs", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("prompt packs fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      this._repoPromptPacks = data.packs || [];\n'
        '      this.forceUpdate();\n'
        '    } catch (err) {\n'
        '      this._repoPromptPacks = [];\n'
        '    }\n'
        '  }\n'
        '  copyRepoPromptPack(content) {\n'
        '    return () => { navigator.clipboard && navigator.clipboard.writeText(content); };\n'
        '  }\n'
        '  async _loadRealAgentNotes() {\n'
        '    try {\n'
        '      const res = await fetch("/agent-notes/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("agent notes fetch failed: " + res.status);\n'
        '      const data = await res.json();\n'
        '      this.setState({ agentNotes: data.agent_notes || {}, skillNotes: data.skill_notes || {} });\n'
        '    } catch (err) {\n'
        '      // Keep whatever notes are already in state if this fails.\n'
        '    }\n'
        '  }\n'
        '  _scheduleAgentNoteSave(kind, id) {\n'
        '    this._agentNoteSaveTimers = this._agentNoteSaveTimers || {};\n'
        '    const key = kind + ":" + id;\n'
        '    clearTimeout(this._agentNoteSaveTimers[key]);\n'
        '    this._agentNoteSaveTimers[key] = setTimeout(() => this._saveAgentNote(kind, id), 800);\n'
        '  }\n'
        '  _saveAgentNote(kind, id) {\n'
        '    const note = kind === "agent" ? (this.state.agentNotes[id] || "") : (this.state.skillNotes[id] || "");\n'
        '    fetch("/agent-notes/" + encodeURIComponent(this.userKey) + "/" + kind + "/" + encodeURIComponent(id), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '      body: JSON.stringify({ note }),\n'
        '    }).catch(() => {});\n'
        '  }\n'
        '\n'
        '  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n',
    ),
    (
        "updateAgentNote: debounce a PUT /agent-notes/{userKey}/agent/{id}",
        '  updateAgentNote(id) {\n'
        '    return (e) => {\n'
        '      const val = e.target.value;\n'
        '      this.setState((s) => ({ agentNotes: { ...s.agentNotes, [id]: val } }));\n'
        '    };\n'
        '  }\n',
        '  updateAgentNote(id) {\n'
        '    return (e) => {\n'
        '      const val = e.target.value;\n'
        '      this.setState((s) => ({ agentNotes: { ...s.agentNotes, [id]: val } }));\n'
        '      this._scheduleAgentNoteSave("agent", id);\n'
        '    };\n'
        '  }\n',
    ),
    (
        "updateSkillNote: debounce a PUT /agent-notes/{userKey}/skill/{id}",
        '  updateSkillNote(slug) {\n'
        '    return (e) => {\n'
        '      const val = e.target.value;\n'
        '      this.setState((s) => ({ skillNotes: { ...s.skillNotes, [slug]: val } }));\n'
        '    };\n'
        '  }\n',
        '  updateSkillNote(slug) {\n'
        '    return (e) => {\n'
        '      const val = e.target.value;\n'
        '      this.setState((s) => ({ skillNotes: { ...s.skillNotes, [slug]: val } }));\n'
        '      this._scheduleAgentNoteSave("skill", slug);\n'
        '    };\n'
        '  }\n',
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Dry run: apply patches in memory, don't write the file.")
    args = parser.parse_args()

    html, json_start, json_end, inner = load_bundle(BUNDLE_PATH)
    patched = apply_patches(inner, PATCHES)

    if args.check:
        print(f"OK: all {len(PATCHES)} patches apply cleanly (dry run, no file written).")
        return 0

    write_bundle(BUNDLE_PATH, html, json_start, json_end, patched)
    print(f"Wrote {BUNDLE_PATH}")

    # Self-check: re-read what we just wrote and confirm the JSON string still
    # round-trips to exactly the patched content, so a broken write is caught
    # here instead of as a runtime "Bundle unpack error" in the browser.
    _, _, _, reread_inner = load_bundle(BUNDLE_PATH)
    if reread_inner != patched:
        raise SystemExit("Post-write verification failed: re-decoded content does not match what was patched.")
    print("Post-write verification OK: re-decoded bundle matches the patched content exactly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
