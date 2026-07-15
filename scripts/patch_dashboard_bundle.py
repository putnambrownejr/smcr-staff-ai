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
        "  componentDidMount() {\n    this._t = setInterval(() => this.setState({ now: new Date() }), 1000 * 30);",
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
        '    const STORAGE_KEY = "smcr_user_key";\n'
        "    let key = null;\n"
        "    try { key = window.localStorage.getItem(STORAGE_KEY); } catch (err) {}\n"
        "    if (!key) {\n"
        '      key = (typeof crypto !== "undefined" && crypto.randomUUID)\n'
        "        ? crypto.randomUUID()\n"
        '        : Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 10);\n'
        "      try { window.localStorage.setItem(STORAGE_KEY, key); } catch (err) {}\n"
        "    }\n"
        "    return key;\n"
        "  }\n"
        "  _apiHeaders(extra) {\n"
        "    const headers = Object.assign({}, extra || {});\n"
        '    if (window.__SMCR_API_KEY__) headers["X-Local-API-Key"] = window.__SMCR_API_KEY__;\n'
        "    return headers;\n"
        "  }\n"
        "  async _loadRealWorkspace() {\n"
        "    this.userKey = this._resolveUserKey();\n"
        "    try {\n"
        '      const res = await fetch("/dashboard/data/" + encodeURIComponent(this.userKey), {\n'
        "        headers: this._apiHeaders(),\n"
        "      });\n"
        '      if (!res.ok) throw new Error("workspace fetch failed: " + res.status);\n'
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
        '    if (window.__SMCR_API_KEY__) headers["X-Local-API-Key"] = window.__SMCR_API_KEY__;\n'
        "    return headers;\n"
        "  }\n"
        "  async _loadRealWorkspace() {\n",
        "  _apiHeaders(extra) {\n"
        "    const headers = Object.assign({}, extra || {});\n"
        '    if (window.__SMCR_API_KEY__) headers["X-Local-API-Key"] = window.__SMCR_API_KEY__;\n'
        "    return headers;\n"
        "  }\n"
        "  _mapRealAction(a) {\n"
        '    // addAction stashes free-text "due" as "Due: <text>\\n<rest>" in notes\n'
        "    // (ActionRecord has no matching free-text field -- suspense_date is a\n"
        '    // strict date and the UI supports non-date values like "overdue" or\n'
        '    // "before drill"). Parse it back out here so it survives a reload\n'
        "    // instead of only showing up in the Notes field.\n"
        '    const notes = a.notes || "";\n'
        "    const dueMatch = /^Due: ([^\\n]+)\\n?([\\s\\S]*)$/.exec(notes);\n"
        "    return {\n"
        "      id: a.action_id,\n"
        "      title: a.title,\n"
        '      owner: a.owner || "Unassigned",\n'
        '      due: a.suspense_date || (dueMatch ? dueMatch[1] : "unscheduled"),\n'
        '      done: a.status === "closed" || a.status === "complete",\n'
        "      notes: dueMatch ? dueMatch[2] : notes,\n"
        "      editOpen: false,\n"
        "    };\n"
        "  }\n"
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
        '      fetch("/actions/" + encodeURIComponent(id), {\n'
        '        method: "PATCH",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify({ status: nextDone ? "closed" : "open" }),\n'
        "      })\n"
        '        .then((res) => { if (!res.ok) throw new Error("update failed: " + res.status); })\n'
        "        .catch(() => {\n"
        "          this.setState((s) => ({ actions: s.actions.map((a) => (a.id === id ? { ...a, done: !nextDone } : a)) }));\n"
        '          window.alert("Could not save that change to the server. Reverted.");\n'
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
        '      fetch("/actions/" + encodeURIComponent(id), { method: "DELETE", headers: this._apiHeaders() })\n'
        '        .then((res) => { if (res.status !== 204 && !res.ok) throw new Error("delete failed: " + res.status); })\n'
        "        .catch(() => {\n"
        "          if (removed) this.setState((s) => ({ actions: [...s.actions, removed] }));\n"
        '          window.alert("Could not delete that action on the server. Restored.");\n'
        "        });\n"
        "    };\n"
        "  }\n",
    ),
    (
        "addAction: POST /actions/track, replace local temp entry with server response",
        "  addAction(e) {\n"
        "    e.preventDefault();\n"
        '    const title = (this.state.draftActionTitle || "").trim();\n'
        "    if (!title) return;\n"
        '    const owner = (this.state.draftActionOwner || "").trim() || "You";\n'
        '    const due = (this.state.draftActionDue || "").trim() || "unscheduled";\n'
        "    this.setState((s) => ({\n"
        '      actions: [...s.actions, { id: Date.now(), title, owner, due, done: false, notes: "", editOpen: false }],\n'
        "      addActionOpen: false,\n"
        '      draftActionTitle: "",\n'
        '      draftActionOwner: "",\n'
        '      draftActionDue: "",\n'
        "    }));",
        "  addAction(e) {\n"
        "    e.preventDefault();\n"
        '    const title = (this.state.draftActionTitle || "").trim();\n'
        "    if (!title) return;\n"
        '    const owner = (this.state.draftActionOwner || "").trim() || "You";\n'
        '    const due = (this.state.draftActionDue || "").trim() || "unscheduled";\n'
        '    const tempId = "pending-" + Date.now();\n'
        "    this.setState((s) => ({\n"
        '      actions: [...s.actions, { id: tempId, title, owner, due, done: false, notes: "", editOpen: false, saving: true }],\n'
        "      addActionOpen: false,\n"
        '      draftActionTitle: "",\n'
        '      draftActionOwner: "",\n'
        '      draftActionDue: "",\n'
        "    }));\n"
        '    const notes = due && due !== "unscheduled" ? "Due: " + due : "";\n'
        '    fetch("/actions/track", {\n'
        '      method: "POST",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '      body: JSON.stringify({ actions: [{ user_key: this.userKey, title, owner, notes, status: "open" }] }),\n'
        "    })\n"
        "      .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n"
        "      .then(({ ok, body }) => {\n"
        "        const tracked = ok && body.tracked && body.tracked[0];\n"
        '        if (!tracked) throw new Error("save failed");\n'
        "        this.setState((s) => ({ actions: s.actions.map((a) => (a.id === tempId ? this._mapRealAction(tracked) : a)) }));\n"
        "      })\n"
        "      .catch(() => {\n"
        "        this.setState((s) => ({ actions: s.actions.filter((a) => a.id !== tempId) }));\n"
        '        window.alert("Could not save this action to the server. It was not added.");\n'
        "      });",
    ),
    (
        "componentDidMount: also load real feeds, links, and handoff/profile",
        "    this._loadRealLinks();\n"
        "    this._loadRealHandoff();",
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
        "  async _loadRealWorkspace() {\n"
        "    this.userKey = this._resolveUserKey();\n"
        "    try {\n"
        '      const res = await fetch("/dashboard/data/" + encodeURIComponent(this.userKey), {\n'
        "        headers: this._apiHeaders(),\n"
        "      });\n"
        '      if (!res.ok) throw new Error("workspace fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n"
        "      this.setState({ actions, workspaceLoaded: true, workspaceLoadError: null });\n"
        "    } catch (err) {\n"
        "      this.setState({ workspaceLoadError: String((err && err.message) || err) });\n"
        "    }\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        "  async _loadRealWorkspace() {\n"
        "    this.userKey = this._resolveUserKey();\n"
        "    try {\n"
        '      const res = await fetch("/dashboard/data/" + encodeURIComponent(this.userKey), {\n'
        "        headers: this._apiHeaders(),\n"
        "      });\n"
        '      if (!res.ok) throw new Error("workspace fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n"
        "      this.setState({ actions, workspaceLoaded: true, workspaceLoadError: null });\n"
        "    } catch (err) {\n"
        "      this.setState({ workspaceLoadError: String((err && err.message) || err) });\n"
        "    }\n"
        "  }\n"
        "\n"
        "  // --- Feeds: real backend wiring. Custom watch feeds are global (no\n"
        "  // per-user scoping on the backend), so the built-in demo feeds\n"
        "  // (MARADMIN/NAVADMIN/etc, which have no backend record at all) stay\n"
        "  // local and only real ones (marked isReal) round-trip through the API.\n"
        "  _feedTrustToLevel(trust) {\n"
        '    const MAP = { Official: "official", Professional: "professional", Unit: "unit_local", Custom: "personal_watch" };\n'
        '    return MAP[trust] || "personal_watch";\n'
        "  }\n"
        "  _mapRealFeed(f) {\n"
        '    const REVERSE = { official: "Official", professional: "Professional", unit_local: "Unit", personal_watch: "Custom", low_trust: "Custom" };\n'
        "    return {\n"
        "      id: f.feed_id,\n"
        "      name: f.name,\n"
        '      meta: f.category || "",\n'
        '      trust: REVERSE[f.trust_level] || "Custom",\n'
        '      type: "url",\n'
        "      url: f.url,\n"
        "      staticItems: null,\n"
        "      editOpen: false,\n"
        "      isReal: true,\n"
        "    };\n"
        "  }\n"
        "  async _loadRealFeeds() {\n"
        "    try {\n"
        '      const res = await fetch("/custom-watch-feeds", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("feeds fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      const realFeeds = (data || []).map((f) => this._mapRealFeed(f));\n"
        "      this.setState((s) => ({ feeds: [...s.feeds.filter((f) => !f.isReal), ...realFeeds] }));\n"
        "    } catch (err) {\n"
        "      // Keep the built-in demo feeds visible even if this fails.\n"
        "    }\n"
        "  }\n"
        "\n"
        "  // --- Links: real backend wiring. Unlike feeds, the backend seed set\n"
        '  // (data/seed/resource_links.json) serves the same "always show curated\n'
        "  // links\" purpose as the bundle's hardcoded linkGroups, so this fully\n"
        "  // replaces linkGroups from the real fetch rather than merging.\n"
        "  _mapRealLinkGroups(response) {\n"
        "    const categories = response.categories || {};\n"
        "    const order = [];\n"
        "    const groups = {};\n"
        "    (response.links || []).forEach((l) => {\n"
        "      const label = categories[l.category] || l.category;\n"
        "      if (!groups[label]) { groups[label] = { title: label, links: [] }; order.push(label); }\n"
        "      let host = l.url;\n"
        '      try { host = new URL(l.url).hostname.replace(/^www\\./, ""); } catch (err) {}\n'
        "      groups[label].links.push({ name: l.title, host, url: l.url, id: l.id, isSeed: l.is_seed });\n"
        "    });\n"
        "    return order.map((label) => groups[label]);\n"
        "  }\n"
        "  _categoryKeyForLabel(label) {\n"
        "    const dict = this._resourceLinkCategories || {};\n"
        '    const target = (label || "").trim().toLowerCase();\n'
        "    for (const key in dict) { if (dict[key].toLowerCase() === target) return key; }\n"
        '    return "unit";\n'
        "  }\n"
        "  async _loadRealLinks() {\n"
        "    try {\n"
        '      const res = await fetch("/resource-links/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("links fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      this._resourceLinkCategories = data.categories || {};\n"
        "      this.setState({ linkGroups: this._mapRealLinkGroups(data) });\n"
        "    } catch (err) {\n"
        "      // Keep the built-in demo link groups visible if this fails.\n"
        "    }\n"
        "  }\n"
        "\n"
        "  // --- Profile / handoff: real backend wiring. rank/display_name/\n"
        "  // billet/unit_id live on UserSessionHandoff (not /user-profile, which\n"
        "  // is a separate format-preference concept). No explicit Save button\n"
        "  // exists in this drawer, so field edits debounce into a PUT.\n"
        "  async _loadRealHandoff() {\n"
        "    try {\n"
        '      const res = await fetch("/handoffs/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        "      if (!res.ok) return; // 404 is normal for a brand-new profile -- keep blank fields.\n"
        "      const handoff = await res.json();\n"
        "      this._handoffData = handoff;\n"
        '      const rank = handoff.rank || "";\n'
        '      let lastName = "";\n'
        "      if (handoff.display_name) {\n"
        '        lastName = rank && handoff.display_name.indexOf(rank + " ") === 0\n'
        "          ? handoff.display_name.slice(rank.length + 1)\n"
        "          : handoff.display_name;\n"
        "      }\n"
        "      this.setState((s) => ({\n"
        "        profileRank: rank,\n"
        "        profileLastName: lastName,\n"
        '        profileBillet: handoff.billet || "",\n'
        '        profileUnit: handoff.unit_id || "",\n'
        "        demoModeManual: true,\n"
        "        demoMode: !(rank.trim() || lastName.trim()) && s.demoMode,\n"
        "      }));\n"
        "    } catch (err) {\n"
        "      // Keep whatever is already in state if this fails.\n"
        "    }\n"
        "  }\n"
        "  _scheduleHandoffSave() {\n"
        "    clearTimeout(this._handoffSaveTimer);\n"
        "    this._handoffSaveTimer = setTimeout(() => this._saveHandoff(), 800);\n"
        "  }\n"
        "  _saveHandoff() {\n"
        "    if (!this.userKey) return;\n"
        "    const base = this._handoffData || { user_key: this.userKey };\n"
        "    const payload = Object.assign({}, base, {\n"
        "      user_key: this.userKey,\n"
        "      rank: this.state.profileRank || null,\n"
        '      display_name: [this.state.profileRank, this.state.profileLastName].filter(Boolean).join(" ") || null,\n'
        "      billet: this.state.profileBillet || null,\n"
        "      unit_id: this.state.profileUnit || null,\n"
        "    });\n"
        '    fetch("/handoffs/" + encodeURIComponent(this.userKey), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "      body: JSON.stringify(payload),\n"
        "    })\n"
        '      .then((res) => { if (!res.ok) throw new Error("save failed: " + res.status); return res.json(); })\n'
        "      .then((body) => { this._handoffData = body.handoff; })\n"
        "      .catch(() => {});\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "onSubmitFeed: POST /custom-watch-feeds for real feeds, keep manual/no-URL feeds local",
        "    const onSubmitFeed = (e) => {\n"
        "      e.preventDefault();\n"
        '      const name = (this.state.draftFeedName || "").trim();\n'
        "      if (!name) return;\n"
        '      const meta = (this.state.draftFeedMeta || "").trim();\n'
        "      const type = this.state.draftFeedType;\n"
        '      let url = (this.state.draftFeedUrl || "").trim();\n'
        '      if (type !== "manual" && url && !/^https?:\\/\\//i.test(url)) url = "https://" + url;\n'
        "      const trust = this.state.draftFeedTrust;\n"
        "      this.setState((s) => ({\n"
        '        feeds: [...s.feeds, { id: Date.now(), name, meta, type, url: type === "manual" ? "" : url, trust, staticItems: null, editOpen: false }],\n'
        '        addFeedOpen: false, draftFeedName: "", draftFeedMeta: "", draftFeedUrl: "", draftFeedType: "rss", draftFeedTrust: "Unit",\n'
        "      }));\n"
        "    };\n",
        "    const onSubmitFeed = (e) => {\n"
        "      e.preventDefault();\n"
        '      const name = (this.state.draftFeedName || "").trim();\n'
        "      if (!name) return;\n"
        '      const meta = (this.state.draftFeedMeta || "").trim();\n'
        "      const type = this.state.draftFeedType;\n"
        '      let url = (this.state.draftFeedUrl || "").trim();\n'
        '      if (type !== "manual" && url && !/^https?:\\/\\//i.test(url)) url = "https://" + url;\n'
        "      const trust = this.state.draftFeedTrust;\n"
        '      this.setState({ addFeedOpen: false, draftFeedName: "", draftFeedMeta: "", draftFeedUrl: "", draftFeedType: "rss", draftFeedTrust: "Unit" });\n'
        '      if (type === "manual" || !url) {\n'
        "        // No backend field for manual/no-URL feeds -- keep it local, matching the prior behavior.\n"
        '        this.setState((s) => ({ feeds: [...s.feeds, { id: Date.now(), name, meta, type, url: "", trust, staticItems: null, editOpen: false }] }));\n'
        "        return;\n"
        "      }\n"
        '      fetch("/custom-watch-feeds", {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify({ name, url, category: meta || "unit", trust_level: this._feedTrustToLevel(trust) }),\n'
        "      })\n"
        "        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n"
        "        .then(({ ok, body }) => {\n"
        '          if (!ok) throw new Error("save failed");\n'
        "          this.setState((s) => ({ feeds: [...s.feeds, this._mapRealFeed(body)] }));\n"
        "        })\n"
        '        .catch(() => window.alert("Could not save this feed to the server. It was not added."));\n'
        "    };\n",
    ),
    (
        "removeFeed: DELETE /custom-watch-feeds/{id} for real feeds only",
        "  removeFeed(id) {\n"
        "    return (e) => {\n"
        "      if (e) { e.preventDefault(); e.stopPropagation(); }\n"
        '      if (!window.confirm("Remove this feed?")) return;\n'
        "      this.setState((s) => ({ feeds: s.feeds.filter((f) => f.id !== id) }));\n"
        "    };\n"
        "  }\n",
        "  removeFeed(id) {\n"
        "    return (e) => {\n"
        "      if (e) { e.preventDefault(); e.stopPropagation(); }\n"
        '      if (!window.confirm("Remove this feed?")) return;\n'
        "      const removed = this.state.feeds.find((f) => f.id === id);\n"
        "      this.setState((s) => ({ feeds: s.feeds.filter((f) => f.id !== id) }));\n"
        "      if (!removed || !removed.isReal) return;\n"
        '      fetch("/custom-watch-feeds/" + encodeURIComponent(id), { method: "DELETE", headers: this._apiHeaders() })\n'
        '        .then((res) => { if (res.status !== 204 && !res.ok) throw new Error("delete failed: " + res.status); })\n'
        "        .catch(() => {\n"
        "          this.setState((s) => ({ feeds: [...s.feeds, removed] }));\n"
        '          window.alert("Could not delete that feed on the server. Restored.");\n'
        "        });\n"
        "    };\n"
        "  }\n",
    ),
    (
        "addLink: POST /resource-links/{userKey}",
        "  addLink(e) {\n"
        "    e.preventDefault();\n"
        '    const category = (this.state.newLinkCategory || "Custom links").trim() || "Custom links";\n'
        '    const name = (this.state.newLinkName || "").trim();\n'
        '    let url = (this.state.newLinkUrl || "").trim();\n'
        "    if (!name || !url) return;\n"
        '    if (!/^https?:\\/\\//i.test(url)) url = "https://" + url;\n'
        "    let host = url;\n"
        '    try { host = new URL(url).hostname.replace(/^www\\./, ""); } catch (e2) { /* keep raw */ }\n'
        "    this.setState((s) => {\n"
        "      const groups = s.linkGroups.map((g) => ({ ...g, links: g.links.slice() }));\n"
        "      const existing = groups.find((g) => g.title.toLowerCase() === category.toLowerCase());\n"
        "      if (existing) {\n"
        "        existing.links.push({ name, host, url });\n"
        "      } else {\n"
        "        groups.push({ title: category, links: [{ name, host, url }] });\n"
        "      }\n"
        '      return { linkGroups: groups, newLinkCategory: "", newLinkName: "", newLinkUrl: "" };\n'
        "    });\n"
        "  }\n",
        "  addLink(e) {\n"
        "    e.preventDefault();\n"
        '    const categoryLabel = (this.state.newLinkCategory || "Custom links").trim() || "Custom links";\n'
        '    const name = (this.state.newLinkName || "").trim();\n'
        '    let url = (this.state.newLinkUrl || "").trim();\n'
        "    if (!name || !url) return;\n"
        '    if (!/^https?:\\/\\//i.test(url)) url = "https://" + url;\n'
        '    this.setState({ newLinkCategory: "", newLinkName: "", newLinkUrl: "" });\n'
        "    const category = this._categoryKeyForLabel(categoryLabel);\n"
        '    fetch("/resource-links/" + encodeURIComponent(this.userKey), {\n'
        '      method: "POST",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "      body: JSON.stringify({ title: name, url, category, tags: [] }),\n"
        "    })\n"
        '      .then((res) => { if (!res.ok) throw new Error("save failed: " + res.status); })\n'
        "      .then(() => this._loadRealLinks())\n"
        '      .catch(() => window.alert("Could not save this link to the server. It was not added."));\n'
        "  }\n",
    ),
    (
        "profile field handlers: debounce a PUT /handoffs/{userKey} on every change",
        "      onBilletChange: (e) => this.setState({ profileBillet: e.target.value }),\n"
        "      onUnitChange: (e) => this.setState({ profileUnit: e.target.value }),\n"
        "      profilePasskey: this.state.profilePasskey,\n"
        "      onRankChange: (e) => {\n"
        "        const v = e.target.value;\n"
        "        this.setState((s) => ({ profileRank: v, demoMode: s.demoModeManual ? s.demoMode : !(v.trim() || s.profileLastName.trim()) }));\n"
        "      },\n"
        "      onLastNameChange: (e) => {\n"
        "        const v = e.target.value;\n"
        "        this.setState((s) => ({ profileLastName: v, demoMode: s.demoModeManual ? s.demoMode : !(v.trim() || s.profileRank.trim()) }));\n"
        "      },\n",
        "      onBilletChange: (e) => { this.setState({ profileBillet: e.target.value }); this._scheduleHandoffSave(); },\n"
        "      onUnitChange: (e) => { this.setState({ profileUnit: e.target.value }); this._scheduleHandoffSave(); },\n"
        "      profilePasskey: this.state.profilePasskey,\n"
        "      onRankChange: (e) => {\n"
        "        const v = e.target.value;\n"
        "        this.setState((s) => ({ profileRank: v, demoMode: s.demoModeManual ? s.demoMode : !(v.trim() || s.profileLastName.trim()) }));\n"
        "        this._scheduleHandoffSave();\n"
        "      },\n"
        "      onLastNameChange: (e) => {\n"
        "        const v = e.target.value;\n"
        "        this.setState((s) => ({ profileLastName: v, demoMode: s.demoModeManual ? s.demoMode : !(v.trim() || s.profileRank.trim()) }));\n"
        "        this._scheduleHandoffSave();\n"
        "      },\n",
    ),
    (
        "componentDidMount: also load real notebook, fitreps, generations, and project list",
        "    this._loadRealGenerations();",
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
        "  _saveHandoff() {\n"
        "    if (!this.userKey) return;\n"
        "    const base = this._handoffData || { user_key: this.userKey };\n"
        "    const payload = Object.assign({}, base, {\n"
        "      user_key: this.userKey,\n"
        "      rank: this.state.profileRank || null,\n"
        '      display_name: [this.state.profileRank, this.state.profileLastName].filter(Boolean).join(" ") || null,\n'
        "      billet: this.state.profileBillet || null,\n"
        "      unit_id: this.state.profileUnit || null,\n"
        "    });\n"
        '    fetch("/handoffs/" + encodeURIComponent(this.userKey), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "      body: JSON.stringify(payload),\n"
        "    })\n"
        '      .then((res) => { if (!res.ok) throw new Error("save failed: " + res.status); return res.json(); })\n'
        "      .then((body) => { this._handoffData = body.handoff; })\n"
        "      .catch(() => {});\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        "  _saveHandoff() {\n"
        "    if (!this.userKey) return;\n"
        "    const base = this._handoffData || { user_key: this.userKey };\n"
        "    const payload = Object.assign({}, base, {\n"
        "      user_key: this.userKey,\n"
        "      rank: this.state.profileRank || null,\n"
        '      display_name: [this.state.profileRank, this.state.profileLastName].filter(Boolean).join(" ") || null,\n'
        "      billet: this.state.profileBillet || null,\n"
        "      unit_id: this.state.profileUnit || null,\n"
        "    });\n"
        '    fetch("/handoffs/" + encodeURIComponent(this.userKey), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "      body: JSON.stringify(payload),\n"
        "    })\n"
        '      .then((res) => { if (!res.ok) throw new Error("save failed: " + res.status); return res.json(); })\n'
        "      .then((body) => { this._handoffData = body.handoff; })\n"
        "      .catch(() => {});\n"
        "  }\n"
        "\n"
        "  // --- User Docs: real backend wiring for the personal notebook, FitRep\n"
        "  // writer, and staff-product generations from the Bench/Files workflow\n"
        "  // tiles. Each category is a real markdown file under settings.user_docs_dir\n"
        "  // (see app/services/user_docs/store.py), not a JSON blob like the other\n"
        "  // domains above -- so these can also be moved into a real project folder.\n"
        "  _isPending(id) {\n"
        '    return typeof id === "string" && id.indexOf("pending-") === 0;\n'
        "  }\n"
        "\n"
        "  // Notebook\n"
        "  _mapRealNote(entry) {\n"
        "    return { id: entry.id, title: entry.title, date: entry.updated_at.slice(0, 10), body: entry.body, archived: !!(entry.fields || {}).archived };\n"
        "  }\n"
        "  async _loadRealNotes() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("notebook fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      const notes = data.map((entry) => this._mapRealNote(entry));\n"
        "      const first = notes.find((n) => !n.archived) || notes[0];\n"
        '      this.setState({ notes, activeNoteId: first ? first.id : null, draftTitle: first ? first.title : "", draftBody: first ? first.body : "" });\n'
        "    } catch (err) {\n"
        "      // Keep the built-in demo notes visible if this fails.\n"
        "    }\n"
        "  }\n"
        "\n"
        "  // FitReps\n"
        "  _mapRealFitrep(entry) {\n"
        "    return Object.assign({ id: entry.id, name: entry.title, archived: false }, entry.fields || {});\n"
        "  }\n"
        "  _fitrepPayload(f) {\n"
        "    const fields = Object.assign({}, f);\n"
        "    delete fields.id;\n"
        "    delete fields.name;\n"
        "    return { title: f.name, fields };\n"
        "  }\n"
        "  async _loadRealFitreps() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/fitreps/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("fitreps fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      const fitreps = data.map((entry) => this._mapRealFitrep(entry));\n"
        "      this.setState((s) => ({ fitreps, activeFitrepId: fitreps[0] ? fitreps[0].id : s.activeFitrepId }));\n"
        "    } catch (err) {\n"
        "      // Keep the built-in demo fitreps visible if this fails.\n"
        "    }\n"
        "  }\n"
        "  _scheduleFitrepSave(id) {\n"
        "    if (!id || this._isPending(id)) return;\n"
        "    this._fitrepSaveTimers = this._fitrepSaveTimers || {};\n"
        "    clearTimeout(this._fitrepSaveTimers[id]);\n"
        "    this._fitrepSaveTimers[id] = setTimeout(() => this._saveFitrep(id), 800);\n"
        "  }\n"
        "  _saveFitrep(id) {\n"
        "    const f = this.state.fitreps.find((x) => x.id === id);\n"
        "    if (!f) return;\n"
        '    fetch("/user-docs/fitreps/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), {\n'
        '      method: "PATCH",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "      body: JSON.stringify(this._fitrepPayload(f)),\n"
        "    }).catch(() => {});\n"
        "  }\n"
        "\n"
        "  // Generations (workflow-drafted staff products)\n"
        "  _mapRealGeneration(entry) {\n"
        "    const fields = entry.fields || {};\n"
        "    return {\n"
        "      id: entry.id,\n"
        "      title: entry.title,\n"
        "      templateType: fields.templateType,\n"
        "      kind: fields.kind,\n"
        '      path: fields.path || "",\n'
        '      receiptsFolder: fields.receiptsFolder || "",\n'
        "      receipts: fields.receipts || [],\n"
        "      created: entry.created_at.slice(0, 10),\n"
        "      data: fields.data || {},\n"
        "    };\n"
        "  }\n"
        "  _generationPayload(d) {\n"
        "    return {\n"
        "      title: d.title,\n"
        "      fields: {\n"
        "        templateType: d.templateType,\n"
        "        kind: d.kind,\n"
        "        path: d.path,\n"
        "        receiptsFolder: d.receiptsFolder,\n"
        "        receipts: d.receipts,\n"
        "        data: d.data,\n"
        "      },\n"
        "    };\n"
        "  }\n"
        "  async _loadRealGenerations() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/generations/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("generations fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      this.setState({ workflowDocs: data.map((entry) => this._mapRealGeneration(entry)) });\n"
        "    } catch (err) {\n"
        "      // Keep whatever local drafts exist if this fails.\n"
        "    }\n"
        "  }\n"
        "  _scheduleGenerationSave(id) {\n"
        "    if (!id || this._isPending(id)) return;\n"
        "    this._generationSaveTimers = this._generationSaveTimers || {};\n"
        "    clearTimeout(this._generationSaveTimers[id]);\n"
        "    this._generationSaveTimers[id] = setTimeout(() => this._saveGeneration(id), 800);\n"
        "  }\n"
        "  _saveGeneration(id) {\n"
        "    const d = this.state.workflowDocs.find((x) => x.id === id);\n"
        "    if (!d) return;\n"
        '    fetch("/user-docs/generations/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), {\n'
        '      method: "PATCH",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "      body: JSON.stringify(this._generationPayload(d)),\n"
        "    }).catch(() => {});\n"
        "  }\n"
        "\n"
        '  // Real project folder names, for the "Save to project" dropdown\n'
        "  async _loadRealProjects() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        "      this._realProjectNames = await res.json();\n"
        "      this.forceUpdate();\n"
        "    } catch (err) {\n"
        "      this._realProjectNames = [];\n"
        "    }\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "newNote: POST /user-docs/notebook",
        "  newNote() {\n"
        "    return () => {\n"
        "      const id = Date.now();\n"
        '      const n = { id, title: "Untitled note", date: "today", body: "", archived: false };\n'
        '      this.setState((s) => ({ notes: [n, ...s.notes], activeNoteId: id, draftTitle: n.title, draftBody: "" }));\n'
        "    };\n"
        "  }\n",
        "  newNote() {\n"
        "    return () => {\n"
        '      const tempId = "pending-" + Date.now();\n'
        '      const n = { id: tempId, title: "Untitled note", date: "today", body: "", archived: false };\n'
        '      this.setState((s) => ({ notes: [n, ...s.notes], activeNoteId: tempId, draftTitle: n.title, draftBody: "" }));\n'
        '      fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey), {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        '        body: JSON.stringify({ title: n.title, body: "" }),\n'
        "      })\n"
        "        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n"
        "        .then(({ ok, body }) => {\n"
        '          if (!ok) throw new Error("save failed");\n'
        "          const real = this._mapRealNote(body);\n"
        "          this.setState((s) => ({\n"
        "            notes: s.notes.map((x) => (x.id === tempId ? real : x)),\n"
        "            activeNoteId: s.activeNoteId === tempId ? real.id : s.activeNoteId,\n"
        "          }));\n"
        "        })\n"
        "        .catch(() => {\n"
        "          this.setState((s) => ({ notes: s.notes.filter((x) => x.id !== tempId) }));\n"
        '          window.alert("Could not save this note to the server. It was not added.");\n'
        "        });\n"
        "    };\n"
        "  }\n",
    ),
    (
        "saveNote: PATCH /user-docs/notebook/{id}",
        "  saveNote() {\n"
        "    return () => {\n"
        "      this.setState((s) => ({\n"
        '        notes: s.notes.map((n) => (n.id === s.activeNoteId ? { ...n, title: s.draftTitle || "Untitled note", body: s.draftBody } : n)),\n'
        "      }));\n"
        "    };\n"
        "  }\n",
        "  saveNote() {\n"
        "    return () => {\n"
        "      const id = this.state.activeNoteId;\n"
        '      const title = this.state.draftTitle || "Untitled note";\n'
        "      const body = this.state.draftBody;\n"
        "      this.setState((s) => ({ notes: s.notes.map((n) => (n.id === id ? { ...n, title, body } : n)) }));\n"
        "      if (this._isPending(id)) return;\n"
        '      fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), {\n'
        '        method: "PATCH",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "        body: JSON.stringify({ title, body }),\n"
        '      }).catch(() => window.alert("Could not save this note to the server."));\n'
        "    };\n"
        "  }\n",
    ),
    (
        "deleteNote: DELETE /user-docs/notebook/{id}",
        "  deleteNote() {\n"
        "    return () => {\n"
        "      const n = this.state.notes.find((x) => x.id === this.state.activeNoteId);\n"
        '      if (!window.confirm(`Permanently delete "${n ? n.title : "this note"}"? This cannot be undone.`)) return;\n'
        "      this.setState((s) => {\n"
        "        const notes = s.notes.filter((x) => x.id !== s.activeNoteId);\n"
        "        const next = notes[0];\n"
        '        return { notes, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" };\n'
        "      });\n"
        "    };\n"
        "  }\n",
        "  deleteNote() {\n"
        "    return () => {\n"
        "      const n = this.state.notes.find((x) => x.id === this.state.activeNoteId);\n"
        '      if (!window.confirm(`Permanently delete "${n ? n.title : "this note"}"? This cannot be undone.`)) return;\n'
        "      const deletedId = this.state.activeNoteId;\n"
        "      this.setState((s) => {\n"
        "        const notes = s.notes.filter((x) => x.id !== s.activeNoteId);\n"
        "        const next = notes[0];\n"
        '        return { notes, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" };\n'
        "      });\n"
        "      if (!this._isPending(deletedId)) {\n"
        '        fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(deletedId), { method: "DELETE", headers: this._apiHeaders() }).catch(() => {});\n'
        "      }\n"
        "    };\n"
        "  }\n",
    ),
    (
        "archiveNote: persist the archived flag",
        "  archiveNote(archived) {\n"
        "    return () => {\n"
        "      this.setState((s) => {\n"
        "        const notes = s.notes.map((n) => (n.id === s.activeNoteId ? { ...n, archived } : n));\n"
        '        const pool = notes.filter((n) => !!n.archived === (s.noteView === "archived"));\n'
        "        const next = pool[0] || null;\n"
        '        return { notes, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" };\n'
        "      });\n"
        "    };\n"
        "  }\n",
        "  archiveNote(archived) {\n"
        "    return () => {\n"
        "      const targetId = this.state.activeNoteId;\n"
        "      this.setState((s) => {\n"
        "        const notes = s.notes.map((n) => (n.id === s.activeNoteId ? { ...n, archived } : n));\n"
        '        const pool = notes.filter((n) => !!n.archived === (s.noteView === "archived"));\n'
        "        const next = pool[0] || null;\n"
        '        return { notes, activeNoteId: next ? next.id : null, draftTitle: next ? next.title : "", draftBody: next ? next.body : "" };\n'
        "      });\n"
        "      if (!this._isPending(targetId)) {\n"
        '        fetch("/user-docs/notebook/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(targetId), {\n'
        '          method: "PATCH",\n'
        '          headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "          body: JSON.stringify({ fields: { archived } }),\n"
        "        }).catch(() => {});\n"
        "      }\n"
        "    };\n"
        "  }\n",
    ),
    (
        "newFitrep: POST /user-docs/fitreps",
        "  newFitrep() {\n"
        "    return () => {\n"
        "      const id = Date.now();\n"
        '      const f = { id, name: "New Marine", rank: "", unit: "", period: "", role: "RS", scores: { mission: 4, individual: 4, leadership: 4, intellect: 4, fitness: 4 }, statement: "", notes: "", tree: 0, roComments: "", archived: false };\n'
        "      this.setState((s) => ({ fitreps: [f, ...s.fitreps], activeFitrepId: id }));\n"
        "    };\n"
        "  }\n",
        "  newFitrep() {\n"
        "    return () => {\n"
        '      const tempId = "pending-" + Date.now();\n'
        '      const f = { id: tempId, name: "New Marine", rank: "", unit: "", period: "", role: "RS", scores: { mission: 4, individual: 4, leadership: 4, intellect: 4, fitness: 4 }, statement: "", notes: "", tree: 0, roComments: "", archived: false };\n'
        "      this.setState((s) => ({ fitreps: [f, ...s.fitreps], activeFitrepId: tempId }));\n"
        '      fetch("/user-docs/fitreps/" + encodeURIComponent(this.userKey), {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "        body: JSON.stringify(this._fitrepPayload(f)),\n"
        "      })\n"
        "        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n"
        "        .then(({ ok, body }) => {\n"
        '          if (!ok) throw new Error("save failed");\n'
        "          const real = this._mapRealFitrep(body);\n"
        "          this.setState((s) => ({\n"
        "            fitreps: s.fitreps.map((x) => (x.id === tempId ? real : x)),\n"
        "            activeFitrepId: s.activeFitrepId === tempId ? real.id : s.activeFitrepId,\n"
        "          }));\n"
        "        })\n"
        "        .catch(() => {\n"
        "          this.setState((s) => ({ fitreps: s.fitreps.filter((x) => x.id !== tempId) }));\n"
        '          window.alert("Could not save this report to the server. It was not added.");\n'
        "        });\n"
        "    };\n"
        "  }\n",
    ),
    (
        "updateFitrepField: debounce a PATCH /user-docs/fitreps/{id}",
        "  updateFitrepField(field) {\n"
        "    return (e) => {\n"
        "      const val = e.target.value;\n"
        "      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, [field]: val } : f)) }));\n"
        "    };\n"
        "  }\n",
        "  updateFitrepField(field) {\n"
        "    return (e) => {\n"
        "      const val = e.target.value;\n"
        "      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, [field]: val } : f)) }));\n"
        "      this._scheduleFitrepSave(this.state.activeFitrepId);\n"
        "    };\n"
        "  }\n",
    ),
    (
        "setFitrepRole: debounce a PATCH /user-docs/fitreps/{id}",
        "  setFitrepRole(role) {\n"
        "    return () => this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, role } : f)) }));\n"
        "  }\n",
        "  setFitrepRole(role) {\n"
        "    return () => {\n"
        "      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, role } : f)) }));\n"
        "      this._scheduleFitrepSave(this.state.activeFitrepId);\n"
        "    };\n"
        "  }\n",
    ),
    (
        "updateFitrepScore: debounce a PATCH /user-docs/fitreps/{id}",
        "  updateFitrepScore(traitId) {\n"
        "    return (e) => {\n"
        "      const val = parseInt(e.target.value, 10);\n"
        "      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, scores: { ...f.scores, [traitId]: val } } : f)) }));\n"
        "    };\n"
        "  }\n",
        "  updateFitrepScore(traitId) {\n"
        "    return (e) => {\n"
        "      const val = parseInt(e.target.value, 10);\n"
        "      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, scores: { ...f.scores, [traitId]: val } } : f)) }));\n"
        "      this._scheduleFitrepSave(this.state.activeFitrepId);\n"
        "    };\n"
        "  }\n",
    ),
    (
        "deleteFitrep: DELETE /user-docs/fitreps/{id}",
        "  deleteFitrep() {\n"
        "    return () => {\n"
        "      const active = this.state.fitreps.find((f) => f.id === this.state.activeFitrepId);\n"
        '      const name = active ? active.name : "this report";\n'
        "      if (!window.confirm(`Permanently delete the tracked report for ${name}? This cannot be undone. Consider Archive instead if you just want it out of the active list.`)) return;\n"
        "      this.setState((s) => {\n"
        "        const fitreps = s.fitreps.filter((f) => f.id !== s.activeFitrepId);\n"
        "        const visible = fitreps.filter((f) => !f.archived);\n"
        "        return { fitreps, activeFitrepId: visible[0] ? visible[0].id : (fitreps[0] ? fitreps[0].id : null) };\n"
        "      });\n"
        "    };\n"
        "  }\n",
        "  deleteFitrep() {\n"
        "    return () => {\n"
        "      const active = this.state.fitreps.find((f) => f.id === this.state.activeFitrepId);\n"
        '      const name = active ? active.name : "this report";\n'
        "      if (!window.confirm(`Permanently delete the tracked report for ${name}? This cannot be undone. Consider Archive instead if you just want it out of the active list.`)) return;\n"
        "      const deletedId = this.state.activeFitrepId;\n"
        "      this.setState((s) => {\n"
        "        const fitreps = s.fitreps.filter((f) => f.id !== s.activeFitrepId);\n"
        "        const visible = fitreps.filter((f) => !f.archived);\n"
        "        return { fitreps, activeFitrepId: visible[0] ? visible[0].id : (fitreps[0] ? fitreps[0].id : null) };\n"
        "      });\n"
        "      if (!this._isPending(deletedId)) {\n"
        '        fetch("/user-docs/fitreps/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(deletedId), { method: "DELETE", headers: this._apiHeaders() }).catch(() => {});\n'
        "      }\n"
        "    };\n"
        "  }\n",
    ),
    (
        "archiveFitrep: persist the archived flag",
        "  archiveFitrep(archived) {\n"
        "    return () => {\n"
        "      this.setState((s) => {\n"
        "        const fitreps = s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, archived } : f));\n"
        '        const pool = fitreps.filter((f) => !!f.archived === (s.fitrepView === "archived"));\n'
        "        return { fitreps, activeFitrepId: pool[0] ? pool[0].id : null };\n"
        "      });\n"
        "    };\n"
        "  }\n",
        "  archiveFitrep(archived) {\n"
        "    return () => {\n"
        "      const targetId = this.state.activeFitrepId;\n"
        "      this.setState((s) => {\n"
        "        const fitreps = s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, archived } : f));\n"
        '        const pool = fitreps.filter((f) => !!f.archived === (s.fitrepView === "archived"));\n'
        "        return { fitreps, activeFitrepId: pool[0] ? pool[0].id : null };\n"
        "      });\n"
        "      this._scheduleFitrepSave(targetId);\n"
        "    };\n"
        "  }\n",
    ),
    (
        "setTree: debounce a PATCH /user-docs/fitreps/{id}",
        "  setTree(n) {\n"
        "    return () => this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, tree: n } : f)) }));\n"
        "  }\n",
        "  setTree(n) {\n"
        "    return () => {\n"
        "      this.setState((s) => ({ fitreps: s.fitreps.map((f) => (f.id === s.activeFitrepId ? { ...f, tree: n } : f)) }));\n"
        "      this._scheduleFitrepSave(this.state.activeFitrepId);\n"
        "    };\n"
        "  }\n",
    ),
    (
        "createWorkflowDoc: POST /user-docs/generations",
        # stable marker -- later patches ("adopt the real server path",
        # "receipts folder under User Docs") edit this method's inserted body,
        # so the full `new` text stops matching verbatim after they run.
        '  createWorkflowDoc(w) {\n    return () => {\n      const tempId = "pending-" + Date.now();',
        "  createWorkflowDoc(w) {\n"
        "    return () => {\n"
        "      const id = Date.now();\n"
        '      const slug = w.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");\n'
        "      const tpl = Component.WORKFLOW_TEMPLATES[w.templateType];\n"
        "      const data = {};\n"
        '      tpl.fields.forEach((f) => { data[f.key] = ""; });\n'
        '      if (w.templateType === "awards") data.awardType = Component.AWARD_TYPES[0].value;\n'
        "      const doc = {\n"
        "        id, title: w.title, templateType: w.templateType, kind: w.kind,\n"
        "        path: `projects/_drafts/${slug}-${id}.md`,\n"
        "        receiptsFolder: `projects/_drafts/${slug}-${id}-receipts/`,\n"
        "        receipts: [],\n"
        '        created: "today",\n'
        "        data,\n"
        "      };\n"
        "      this.setState((s) => ({ workflowDocs: [doc, ...s.workflowDocs], workflowEditorId: id }));\n"
        "    };\n"
        "  }\n",
        "  createWorkflowDoc(w) {\n"
        "    return () => {\n"
        '      const tempId = "pending-" + Date.now();\n'
        '      const slug = w.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");\n'
        "      const tpl = Component.WORKFLOW_TEMPLATES[w.templateType];\n"
        "      const data = {};\n"
        '      tpl.fields.forEach((f) => { data[f.key] = ""; });\n'
        '      if (w.templateType === "awards") data.awardType = Component.AWARD_TYPES[0].value;\n'
        "      const doc = {\n"
        "        id: tempId, title: w.title, templateType: w.templateType, kind: w.kind,\n"
        "        path: `User Docs/Generations/${slug}-${tempId}.md`,\n"
        "        receiptsFolder: `projects/_drafts/${slug}-${tempId}-receipts/`,\n"
        "        receipts: [],\n"
        '        created: "today",\n'
        "        data,\n"
        "      };\n"
        "      this.setState((s) => ({ workflowDocs: [doc, ...s.workflowDocs], workflowEditorId: tempId }));\n"
        '      fetch("/user-docs/generations/" + encodeURIComponent(this.userKey), {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "        body: JSON.stringify(this._generationPayload(doc)),\n"
        "      })\n"
        "        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n"
        "        .then(({ ok, body }) => {\n"
        '          if (!ok) throw new Error("save failed");\n'
        "          const real = this._mapRealGeneration(body);\n"
        "          this.setState((s) => ({\n"
        "            workflowDocs: s.workflowDocs.map((x) => (x.id === tempId ? real : x)),\n"
        "            workflowEditorId: s.workflowEditorId === tempId ? real.id : s.workflowEditorId,\n"
        "          }));\n"
        "        })\n"
        "        .catch(() => {\n"
        "          this.setState((s) => ({ workflowDocs: s.workflowDocs.filter((x) => x.id !== tempId) }));\n"
        '          window.alert("Could not save this draft to the server. It was not added.");\n'
        "        });\n"
        "    };\n"
        "  }\n",
    ),
    (
        "updateWorkflowField: debounce a PATCH /user-docs/generations/{id}",
        "  updateWorkflowField(id, field) {\n"
        "    return (e) => {\n"
        "      const val = e.target.value;\n"
        "      this.setState((s) => ({ workflowDocs: s.workflowDocs.map((d) => (d.id === id ? { ...d, data: { ...d.data, [field]: val } } : d)) }));\n"
        "    };\n"
        "  }\n",
        "  updateWorkflowField(id, field) {\n"
        "    return (e) => {\n"
        "      const val = e.target.value;\n"
        "      this.setState((s) => ({ workflowDocs: s.workflowDocs.map((d) => (d.id === id ? { ...d, data: { ...d.data, [field]: val } } : d)) }));\n"
        "      this._scheduleGenerationSave(id);\n"
        "    };\n"
        "  }\n",
    ),
    (
        "deleteWorkflowDoc: DELETE /user-docs/generations/{id}",
        "  deleteWorkflowDoc(id) {\n"
        "    return () => {\n"
        '      if (!window.confirm("Delete this draft? This cannot be undone.")) return;\n'
        "      this.setState((s) => ({ workflowDocs: s.workflowDocs.filter((d) => d.id !== id), workflowEditorId: s.workflowEditorId === id ? null : s.workflowEditorId }));\n"
        "    };\n"
        "  }\n",
        "  deleteWorkflowDoc(id) {\n"
        "    return () => {\n"
        '      if (!window.confirm("Delete this draft? This cannot be undone.")) return;\n'
        "      this.setState((s) => ({ workflowDocs: s.workflowDocs.filter((d) => d.id !== id), workflowEditorId: s.workflowEditorId === id ? null : s.workflowEditorId }));\n"
        "      if (!this._isPending(id)) {\n"
        '        fetch("/user-docs/generations/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(id), { method: "DELETE", headers: this._apiHeaders() }).catch(() => {});\n'
        "      }\n"
        "    };\n"
        "  }\n",
    ),
    (
        "moveWorkflowDocToProject: real POST /user-docs/generations/{id}/save-to-project",
        "  moveWorkflowDocToProject(docId) {\n"
        "    return () => {\n"
        "      const folder = this.state.draftMoveTarget[docId];\n"
        "      if (!folder) return;\n"
        "      this.setState((s) => {\n"
        "        const doc = s.workflowDocs.find((d) => d.id === docId);\n"
        "        if (!doc) return null;\n"
        '        const slug = doc.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");\n'
        "        const newPath = `projects/${folder}/${slug}.md`;\n"
        '        const benchCards = s.benchCards.map((c) => (c.title !== "Project files" ? c : {\n'
        "          ...c,\n"
        '          items: [...c.items, { name: doc.title, meta: "moved draft", path: newPath }],\n'
        "        }));\n"
        "        return {\n"
        "          benchCards,\n"
        "          workflowDocs: s.workflowDocs.filter((d) => d.id !== docId),\n"
        "          workflowEditorId: s.workflowEditorId === docId ? null : s.workflowEditorId,\n"
        "        };\n"
        "      });\n"
        "    };\n"
        "  }\n",
        "  moveWorkflowDocToProject(docId) {\n"
        "    return () => {\n"
        "      const folder = this.state.draftMoveTarget[docId];\n"
        "      if (!folder) return;\n"
        "      const doc = this.state.workflowDocs.find((d) => d.id === docId);\n"
        "      if (!doc) return;\n"
        "      const finish = (newPath) => {\n"
        "        this.setState((s) => {\n"
        '          const benchCards = s.benchCards.map((c) => (c.title !== "Project files" ? c : {\n'
        "            ...c,\n"
        '            items: [...c.items, { name: doc.title, meta: "moved draft", path: newPath }],\n'
        "          }));\n"
        "          return {\n"
        "            benchCards,\n"
        "            workflowDocs: s.workflowDocs.filter((d) => d.id !== docId),\n"
        "            workflowEditorId: s.workflowEditorId === docId ? null : s.workflowEditorId,\n"
        "          };\n"
        "        });\n"
        "      };\n"
        "      if (this._isPending(docId)) {\n"
        '        const slug = doc.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");\n'
        "        finish(`projects/${folder}/${slug}.md`);\n"
        "        return;\n"
        "      }\n"
        '      fetch("/user-docs/generations/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(docId) + "/save-to-project", {\n'
        '        method: "POST",\n'
        '        headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "        body: JSON.stringify({ project: folder }),\n"
        "      })\n"
        "        .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n"
        "        .then(({ ok, body }) => {\n"
        '          if (!ok) throw new Error("save failed");\n'
        "          finish(body.path);\n"
        "          this._loadRealProjects();\n"
        "        })\n"
        '        .catch(() => window.alert("Could not save this draft to the project. It is still in Drafted files."));\n'
        "    };\n"
        "  }\n",
    ),
    (
        "projectFolderNames: include real project folders alongside the local bench card list",
        '    const projectFolderNames = ((this.state.benchCards.find((c) => c.title === "Project files") || { items: [] }).items || []).map((it) => it.name);\n',
        "    const projectFolderNames = Array.from(new Set([\n"
        '      ...((this.state.benchCards.find((c) => c.title === "Project files") || { items: [] }).items || []).map((it) => it.name),\n'
        "      ...(this._realProjectNames || []),\n"
        "    ]));\n",
    ),
    (
        "componentDidMount: also load the real agent/skill catalog, prompt packs, and agent notes",
        "    this._loadRealAgents();",
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
        "  async _loadRealProjects() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        "      this._realProjectNames = await res.json();\n"
        "      this.forceUpdate();\n"
        "    } catch (err) {\n"
        "      this._realProjectNames = [];\n"
        "    }\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        '  // Real project folder names, for the "Save to project" dropdown\n'
        "  async _loadRealProjects() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        "      this._realProjectNames = await res.json();\n"
        "      this.forceUpdate();\n"
        "    } catch (err) {\n"
        "      this._realProjectNames = [];\n"
        "    }\n"
        "  }\n"
        "\n"
        "  // --- AI page: real agent/skill catalog + notes backend wiring.\n"
        "  // AGENTS_CATALOG/SKILLS_CATALOG are static class fields the demo bundle\n"
        "  // hardcoded; reassigning them at runtime (then forceUpdate) is far less\n"
        "  // invasive than converting every render-time reference to state.\n"
        "  async _loadRealAgents() {\n"
        "    try {\n"
        '      const res = await fetch("/agents", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("agents fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      Component.AGENTS_CATALOG = data.map((a) => ({\n"
        "        id: a.id,\n"
        "        name: a.name,\n"
        "        category: a.domain,\n"
        "        description: a.description,\n"
        '        limitations: (a.disallowed_inputs || []).join(", ") || "None listed.",\n'
        "      }));\n"
        "      this.forceUpdate();\n"
        "    } catch (err) {\n"
        "      // Keep the built-in demo catalog visible if this fails.\n"
        "    }\n"
        "  }\n"
        "  async _loadRealSkills() {\n"
        "    try {\n"
        '      const res = await fetch("/skills", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("skills fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      Component.SKILLS_CATALOG = (data.skills || []).map((s) => ({ slug: s.name, name: s.name, description: s.description }));\n"
        "      this.forceUpdate();\n"
        "    } catch (err) {\n"
        "      // Keep the built-in demo catalog visible if this fails.\n"
        "    }\n"
        "  }\n"
        "  async _loadRealPromptPacks() {\n"
        "    try {\n"
        '      const res = await fetch("/prompt-packs", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("prompt packs fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      this._repoPromptPacks = data.packs || [];\n"
        "      this.forceUpdate();\n"
        "    } catch (err) {\n"
        "      this._repoPromptPacks = [];\n"
        "    }\n"
        "  }\n"
        "  copyRepoPromptPack(content) {\n"
        "    return () => { navigator.clipboard && navigator.clipboard.writeText(content); };\n"
        "  }\n"
        "  async _loadRealAgentNotes() {\n"
        "    try {\n"
        '      const res = await fetch("/agent-notes/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("agent notes fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      this.setState({ agentNotes: data.agent_notes || {}, skillNotes: data.skill_notes || {} });\n"
        "    } catch (err) {\n"
        "      // Keep whatever notes are already in state if this fails.\n"
        "    }\n"
        "  }\n"
        "  _scheduleAgentNoteSave(kind, id) {\n"
        "    this._agentNoteSaveTimers = this._agentNoteSaveTimers || {};\n"
        '    const key = kind + ":" + id;\n'
        "    clearTimeout(this._agentNoteSaveTimers[key]);\n"
        "    this._agentNoteSaveTimers[key] = setTimeout(() => this._saveAgentNote(kind, id), 800);\n"
        "  }\n"
        "  _saveAgentNote(kind, id) {\n"
        '    const note = kind === "agent" ? (this.state.agentNotes[id] || "") : (this.state.skillNotes[id] || "");\n'
        '    fetch("/agent-notes/" + encodeURIComponent(this.userKey) + "/" + kind + "/" + encodeURIComponent(id), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "      body: JSON.stringify({ note }),\n"
        "    }).catch(() => {});\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "updateAgentNote: debounce a PUT /agent-notes/{userKey}/agent/{id}",
        "  updateAgentNote(id) {\n"
        "    return (e) => {\n"
        "      const val = e.target.value;\n"
        "      this.setState((s) => ({ agentNotes: { ...s.agentNotes, [id]: val } }));\n"
        "    };\n"
        "  }\n",
        "  updateAgentNote(id) {\n"
        "    return (e) => {\n"
        "      const val = e.target.value;\n"
        "      this.setState((s) => ({ agentNotes: { ...s.agentNotes, [id]: val } }));\n"
        '      this._scheduleAgentNoteSave("agent", id);\n'
        "    };\n"
        "  }\n",
    ),
    (
        "updateSkillNote: debounce a PUT /agent-notes/{userKey}/skill/{id}",
        "  updateSkillNote(slug) {\n"
        "    return (e) => {\n"
        "      const val = e.target.value;\n"
        "      this.setState((s) => ({ skillNotes: { ...s.skillNotes, [slug]: val } }));\n"
        "    };\n"
        "  }\n",
        "  updateSkillNote(slug) {\n"
        "    return (e) => {\n"
        "      const val = e.target.value;\n"
        "      this.setState((s) => ({ skillNotes: { ...s.skillNotes, [slug]: val } }));\n"
        '      this._scheduleAgentNoteSave("skill", slug);\n'
        "    };\n"
        "  }\n",
    ),
    (
        "Prompts tab HTML: add a read-only 'Repo prompt packs' section above the editable ones",
        # Explicit marker: a LATER patch ("collapse the build-your-own editable
        # packs") inserts a <details> right before <sc-for promptPacksRendered>,
        # which sits inside this patch's `new` text and would break a plain
        # new-as-marker idempotency check on re-run.
        '<h3 style="margin:0 0 4px;font-size:0.96rem;font-weight:700;">Repo prompt packs</h3>',
        '      <sc-if value="{{ isAiTabPrompts }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="display:grid;gap:16px;">\n'
        '        <sc-for list="{{ promptPacksRendered }}" as="pack" hint-placeholder-count="4">\n',
        '      <sc-if value="{{ isAiTabPrompts }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="display:grid;gap:16px;">\n'
        '        <sc-if value="{{ hasRepoPromptPacks }}" hint-placeholder-val="{{ false }}">\n'
        '        <section style="border:1px solid #313844;border-radius:8px;background:#0f1318;padding:16px 18px;">\n'
        '          <h3 style="margin:0 0 4px;font-size:0.96rem;font-weight:700;">Repo prompt packs</h3>\n'
        '          <p style="margin:0 0 12px;color:#8a94a0;font-size:0.8rem;line-height:1.4;">Read-only copies of the packs in <span style="font-family:\'IBM Plex Mono\',monospace;">prompt-packs/</span> — paste the full text into any AI chat.</p>\n'
        '          <div style="display:grid;gap:8px;">\n'
        '            <sc-for list="{{ repoPromptPacksRendered }}" as="rp" hint-placeholder-count="4">\n'
        '              <div style="padding:10px 11px;border:1px solid #313844;border-radius:6px;background:#0d1014;">\n'
        '                <div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;">\n'
        '                  <div style="font-size:0.85rem;font-weight:600;">{{ rp.title }}</div>\n'
        '                  <button type="button" sc-camel-on-click="{{ rp.onCopy }}" style="flex:0 0 auto;height:24px;padding:0 8px;border:1px solid #313844;border-radius:5px;background:#1a2027;color:#aab4bf;font:inherit;font-size:0.7rem;font-weight:600;cursor:pointer;">{{ rp.copyLabel }}</button>\n'
        "                </div>\n"
        '                <p style="margin:5px 0 0;font-size:0.79rem;color:#aab4bf;line-height:1.4;">{{ rp.summary }}</p>\n'
        "              </div>\n"
        "            </sc-for>\n"
        "          </div>\n"
        "        </section>\n"
        "        </sc-if>\n"
        '        <sc-for list="{{ promptPacksRendered }}" as="pack" hint-placeholder-count="4">\n',
    ),
    (
        "computed vals: repoPromptPacksRendered from the real /prompt-packs fetch",
        "    const promptPacksRendered = this.state.promptPacks.map((pack) => ({\n"
        "      id: pack.id,\n"
        "      title: pack.title,\n"
        "      onAddItem: this.addPackItem(pack.id),\n",
        "    const repoPromptPacksRendered = (this._repoPromptPacks || []).map((rp) => ({\n"
        "      slug: rp.slug,\n"
        "      title: rp.title,\n"
        "      summary: rp.summary,\n"
        '      copyLabel: this.state.copiedPackSlug === rp.slug ? "Copied" : "Copy",\n'
        "      onCopy: () => {\n"
        "        navigator.clipboard && navigator.clipboard.writeText(rp.content);\n"
        "        this.setState({ copiedPackSlug: rp.slug });\n"
        "        clearTimeout(this._copiedPackTimer);\n"
        "        this._copiedPackTimer = setTimeout(() => this.setState({ copiedPackSlug: null }), 1500);\n"
        "      },\n"
        "    }));\n"
        "    const hasRepoPromptPacks = repoPromptPacksRendered.length > 0;\n"
        "    const promptPacksRendered = this.state.promptPacks.map((pack) => ({\n"
        "      id: pack.id,\n"
        "      title: pack.title,\n"
        "      onAddItem: this.addPackItem(pack.id),\n",
    ),
    (
        "vals object: expose repoPromptPacksRendered/hasRepoPromptPacks to the template",
        "      skillsRendered, promptPacksRendered, combosRendered,\n",
        "      skillsRendered, promptPacksRendered, combosRendered,\n"
        "      repoPromptPacksRendered, hasRepoPromptPacks,\n",
    ),
    # ------------------------------------------------------------------
    # Validation-pass fixes (2026-07-12): real feed tickers, real personal
    # files, real project folders, and correct drafted-file paths/copy.
    # ------------------------------------------------------------------
    (
        "workspace load: capture real tickers and personal files from /dashboard/data",
        "      const mapTicker = (items)",  # stable marker
        '      if (!res.ok) throw new Error("workspace fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n"
        "      this.setState({ actions, workspaceLoaded: true, workspaceLoadError: null });\n",
        '      if (!res.ok) throw new Error("workspace fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n"
        "      // Ticker items and personal documents ride along on the same payload.\n"
        '      const mapTicker = (items) => (items || []).map((t) => ({ id: t.summary || "", title: t.title, url: t.source_url || "" }));\n'
        "      const personalItems = (data.document_details || []).map((doc) => ({\n"
        "        name: doc.filename,\n"
        '        meta: doc.document_type || "file",\n'
        '        path: "local_context/files/" + doc.context_id + "-" + doc.filename,\n'
        "      }));\n"
        "      this.setState((s) => ({\n"
        "        actions,\n"
        "        realMaradmins: mapTicker(data.maradmin_ticker),\n"
        "        realNavadmins: mapTicker(data.navadmin_ticker),\n"
        '        benchCards: s.benchCards.map((c) => (c.title !== "Personal files" ? c : { ...c, items: personalItems })),\n'
        "        workspaceLoaded: true,\n"
        "        workspaceLoadError: null,\n"
        "      }));\n",
    ),
    (
        "overview ticker consts: prefer real feed items once the workspace loads",
        "    const demoMaradmins = [",  # stable marker
        "    const maradmins = [\n"
        '      { id: "MARADMIN 312/26", title: "FY27 Reserve Component AT budget guidance and submission windows" },\n'
        '      { id: "MARADMIN 305/26", title: "Update to FitRep reporting occasions for SMCR reporting seniors" },\n'
        '      { id: "MARADMIN 298/26", title: "Revised PME completion requirements for promotion eligibility" },\n'
        "    ];\n"
        "    const navadmins = [\n"
        '      { id: "NAVADMIN 148/26", title: "Reserve pay and MROWS processing schedule for Q4 FY26" },\n'
        '      { id: "NAVADMIN 141/26", title: "DTS travel policy change — lodging receipt thresholds" },\n'
        '      { id: "NAVADMIN 136/26", title: "Updated guidance on reserve retirement point capture" },\n'
        "    ];\n",
        "    // Demo ticker items only show until the real /dashboard/data load\n"
        "    // succeeds; after that the live feed items (or an honest empty notice)\n"
        '    // replace them, so the "live" badge never sits on top of canned data.\n'
        '    const MARADMIN_PORTAL = "https://www.marines.mil/News/Messages/MARADMINS/";\n'
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
        "    ];\n"
        '    const emptyTicker = (label, url) => [{ id: "—", title: "No " + label + " messages pulled yet — refresh feeds to pull from the live source.", url }];\n'
        "    const maradmins = !this.state.workspaceLoaded\n"
        "      ? demoMaradmins\n"
        '      : ((this.state.realMaradmins || []).length ? this.state.realMaradmins.slice(0, 4) : emptyTicker("MARADMIN", MARADMIN_PORTAL));\n'
        "    const navadmins = !this.state.workspaceLoaded\n"
        "      ? demoNavadmins\n"
        '      : ((this.state.realNavadmins || []).length ? this.state.realNavadmins.slice(0, 4) : emptyTicker("NAVADMIN", NAVADMIN_PORTAL));\n',
    ),
    (
        "overview MARADMIN card: link each item to its own message",
        '              <sc-for list="{{ maradmins }}" as="m" hint-placeholder-count="3">\n'
        '                <a href="https://www.marines.mil/News/Messages/MARADMINS/" target="_blank" rel="noopener" style="display:block;padding:11px 12px;border:1px solid #313844;border-radius:6px;background:#0d1014;">\n',
        '              <sc-for list="{{ maradmins }}" as="m" hint-placeholder-count="3">\n'
        '                <a href="{{ m.url }}" target="_blank" rel="noopener" style="display:block;padding:11px 12px;border:1px solid #313844;border-radius:6px;background:#0d1014;">\n',
    ),
    (
        "overview NAVADMIN card: link each item to its own message",
        '              <sc-for list="{{ navadmins }}" as="m" hint-placeholder-count="3">\n'
        '                <a href="https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN/" target="_blank" rel="noopener" style="display:block;padding:11px 12px;border:1px solid #313844;border-radius:6px;background:#0d1014;">\n',
        '              <sc-for list="{{ navadmins }}" as="m" hint-placeholder-count="3">\n'
        '                <a href="{{ m.url }}" target="_blank" rel="noopener" style="display:block;padding:11px 12px;border:1px solid #313844;border-radius:6px;background:#0d1014;">\n',
    ),
    (
        "watch feed accordions: use each ticker item's own url",
        "const tickerFeedItem = (m) =>",
        "    const staticFeedItems = {\n"
        '      maradmin: maradmins.map((m) => ({ text: `${m.id} — ${m.title}`, url: "https://www.marines.mil/News/Messages/MARADMINS/" })),\n'
        '      navadmin: navadmins.map((m) => ({ text: `${m.id} — ${m.title}`, url: "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN/" })),\n',
        '    const tickerFeedItem = (m) => ({ text: (m.id ? m.id + " — " : "") + m.title, url: m.url });\n'
        "    const staticFeedItems = {\n"
        "      maradmin: maradmins.map(tickerFeedItem),\n"
        "      navadmin: navadmins.map(tickerFeedItem),\n",
    ),
    (
        "feed list metas: drop the canned new-today counts",
        '      { id: 1, name: "MARADMIN RSS", meta: "official · HQMC · 3 new today", trust: "Official", type: "rss", url: "https://www.marines.mil/News/Messages/MARADMINS/", staticItems: "maradmin", editOpen: false },\n'
        '      { id: 2, name: "NAVADMIN RSS", meta: "official · Navy · 2 new today", trust: "Official", type: "rss", url: "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN/", staticItems: "navadmin", editOpen: false },\n',
        '      { id: 1, name: "MARADMIN RSS", meta: "official · HQMC", trust: "Official", type: "rss", url: "https://www.marines.mil/News/Messages/MARADMINS/", staticItems: "maradmin", editOpen: false },\n'
        '      { id: 2, name: "NAVADMIN RSS", meta: "official · Navy", trust: "Official", type: "rss", url: "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN/", staticItems: "navadmin", editOpen: false },\n',
    ),
    (
        "Personal files bench card: start empty instead of demo files",
        '      { title: "Personal files", desc: "Local-only orders, RQS, BIO, receipts — yours alone, never mixed with project or template files.", items: [ { name: "AT orders — FY26.pdf", meta: "orders", path: "personal/AT-orders-FY26.pdf" }, { name: "RQS roster — JUL.xlsx", meta: "reference", path: "personal/RQS-roster-JUL.xlsx" }, { name: "Officer BIO.docx", meta: "bio", path: "personal/Officer-BIO.docx" } ], addOpen: false, draftName: "", draftMeta: "" },\n',
        '      { title: "Personal files", desc: "Local-only orders, RQS, BIO, receipts — yours alone, never mixed with project or template files.", items: [], addOpen: false, draftName: "", draftMeta: "" },\n',
    ),
    (
        "Project files bench card: start empty instead of demo folders",
        '      { title: "Project files", desc: "Scenario and exercise folders under projects/ in the repo, plus loose drafts you\'ve started before sorting them into one. Open the path to reach subfiles.", items: [ { name: "4thCAGFEX042027", meta: "project folder", path: "projects/4thCAGFEX042027/" }, { name: "repo-maintenance", meta: "project folder", path: "projects/repo-maintenance/" } ], addOpen: false, draftName: "", draftMeta: "" },\n',
        '      { title: "Project files", desc: "Scenario and exercise folders under projects/ in the repo, plus loose drafts you\'ve started before sorting them into one. Open the path to reach subfiles.", items: [], addOpen: false, draftName: "", draftMeta: "" },\n',
    ),
    (
        "_loadRealProjects: rebuild the Project files card from the real folders",
        "      this._realProjectNames = visible.map((project) => project.name);",  # preserved by the later demo filter patch
        "  async _loadRealProjects() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        "      this._realProjectNames = await res.json();\n"
        "      this.forceUpdate();\n"
        "    } catch (err) {\n"
        "      this._realProjectNames = [];\n"
        "    }\n"
        "  }\n",
        "  async _loadRealProjects() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        "      this._realProjectNames = await res.json();\n"
        "      // The Project files bench card starts empty; fill it with the real\n"
        "      // folders under projects/ so no phantom demo folders are shown.\n"
        '      const items = (this._realProjectNames || []).map((n) => ({ name: n, meta: "project folder", path: "projects/" + n + "/" }));\n'
        '      this.setState((s) => ({ benchCards: s.benchCards.map((c) => (c.title !== "Project files" ? c : { ...c, items })) }));\n'
        "    } catch (err) {\n"
        "      this._realProjectNames = [];\n"
        "    }\n"
        "  }\n",
    ),
    (
        "createWorkflowDoc: adopt the real server path after create",
        "          real.path = ",  # stable marker
        "          const real = this._mapRealGeneration(body);\n"
        "          this.setState((s) => ({\n"
        "            workflowDocs: s.workflowDocs.map((x) => (x.id === tempId ? real : x)),\n"
        "            workflowEditorId: s.workflowEditorId === tempId ? real.id : s.workflowEditorId,\n"
        "          }));\n",
        "          const real = this._mapRealGeneration(body);\n"
        "          // The optimistic doc carried a pending filename; the store wrote\n"
        "          // the entry as <id>.md (see app/services/user_docs/store.py), so\n"
        "          // adopt the real path and persist it back into the entry fields.\n"
        '          real.path = "User Docs/Generations/" + real.id + ".md";\n'
        '          real.receiptsFolder = "User Docs/Generations/" + real.id + "-receipts/";\n'
        "          this.setState((s) => ({\n"
        "            workflowDocs: s.workflowDocs.map((x) => (x.id === tempId ? real : x)),\n"
        "            workflowEditorId: s.workflowEditorId === tempId ? real.id : s.workflowEditorId,\n"
        "          }));\n"
        "          this._scheduleGenerationSave(real.id);\n",
    ),
    (
        "createWorkflowDoc: receipts folder lives under User Docs, not projects/_drafts",
        "        receiptsFolder: `projects/_drafts/${slug}-${tempId}-receipts/`,\n",
        "        receiptsFolder: `User Docs/Generations/${slug}-${tempId}-receipts/`,\n",
    ),
    (
        "drafted files copy: name the real User Docs holding location",
        'Every file you start above lands here in <span style="font-family:\'IBM Plex Mono\',monospace;">projects/_drafts/</span> — a holding folder, not a project. Nothing here is committed until you pick a project and click "Save to project."',
        'Every file you start above is saved to your local <span style="font-family:\'IBM Plex Mono\',monospace;">User Docs/Generations/</span> folder — a holding area, not a project. Nothing lands in a project until you pick one and click "Save to project."',
    ),
    (
        "personal files modal note: these are local app files, not repo files",
        '        benchModalNote = `Local repo file: ${item.path || "(no path set)"} — open it at that location in your file explorer, or replace it with a new upload from there.`;\n',
        '        benchModalNote = `Local file: ${item.path || "(no path set)"} — open it at that location in your file explorer, or replace it with a new upload from there.`;\n',
    ),
    # ------------------------------------------------------------------
    # Demo mode baseline files (2026-07-12): toggling demo on re-seeds the
    # shared demo user key on the backend and points the app at it, so demo
    # mode shows working, disposable content instead of being badge-only.
    # ------------------------------------------------------------------
    (
        "add _switchDemoMode: seed + swap user key when demo mode toggles",
        "  async _switchDemoMode(on, opts) {",  # stable marker
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        "  // --- Demo mode: baseline demo files. Switching to demo points the app\n"
        "  // at a shared demo user key and seeds it on the backend (POST\n"
        "  // /demo/workspace/seed writes real files under User Docs plus tracked\n"
        "  // actions, so sliders, saves, and open-location all genuinely work);\n"
        "  // switching off returns to the personal key. opts.seed controls the\n"
        '  // seeding: "reset" (default, explicit toggle) always restores a known\n'
        '  // baseline; "ifEmpty" (initial page load) only populates a first-ever\n'
        "  // demo so a refresh mid-demo keeps your edits; false skips seeding.\n"
        "  async _switchDemoMode(on, opts) {\n"
        "    if (on) {\n"
        "      if (!this._realUserKey) this._realUserKey = this.userKey;\n"
        '      let demoKey = "demo-smcr-officer";\n'
        '      const seedMode = opts && "seed" in opts ? opts.seed : "reset";\n'
        "      try {\n"
        "        if (seedMode) {\n"
        '          const q = seedMode === "ifEmpty" ? "?only_if_empty=true" : "";\n'
        '          const res = await fetch("/demo/workspace/seed" + q, { method: "POST", headers: this._apiHeaders() });\n'
        "          if (res.ok) { const body = await res.json(); demoKey = body.user_key || demoKey; }\n"
        "        }\n"
        "      } catch (err) { /* seed failure still leaves demo mode usable, just empty */ }\n"
        "      this.userKey = demoKey;\n"
        '      this.setState({ profileRank: "Capt", profileLastName: "Schmuckatelli", profileBillet: "S-4A", profileUnit: "4th CAG" });\n'
        "    } else {\n"
        "      this.userKey = this._realUserKey || this._resolveUserKey();\n"
        "      // Clear the demo profile fields; _loadRealHandoff refills them from\n"
        "      // the real personal handoff, or leaves them blank if none is saved.\n"
        '      this.setState({ profileRank: "", profileLastName: "", profileBillet: "", profileUnit: "" });\n'
        "      this._loadRealHandoff();\n"
        "    }\n"
        "    this._loadRealWorkspace();\n"
        "    this._loadRealNotes();\n"
        "    this._loadRealFitreps();\n"
        "    this._loadRealGenerations();\n"
        "    this._loadRealAgentNotes();\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "onToggleDemoMode: seed and reload through _switchDemoMode",
        "      onToggleDemoMode: () => this.setState((s) => ({ demoMode: !s.demoMode, demoModeManual: true })),\n",
        "      onToggleDemoMode: () => {\n"
        "        const next = !this.state.demoMode;\n"
        "        this.setState({ demoMode: next, demoModeManual: true });\n"
        "        this._switchDemoMode(next);\n"
        "      },\n",
    ),
    (
        "_loadRealHandoff: reconcile an initial demo-mode load onto the demo key (no handoff)",
        'if (!this.state.demoModeManual && this.state.demoMode) this._switchDemoMode(true, { seed: "ifEmpty" });',  # stable marker
        "      if (!res.ok) return; // 404 is normal for a brand-new profile -- keep blank fields.\n",
        "      if (!res.ok) {\n"
        "        // 404 is normal for a brand-new profile -- keep blank fields. A\n"
        "        // brand-new profile also means demo mode stays on, so point the\n"
        "        // app at the demo key (seed only if the demo workspace is empty).\n"
        '        if (!this.state.demoModeManual && this.state.demoMode) this._switchDemoMode(true, { seed: "ifEmpty" });\n'
        "        return;\n"
        "      }\n",
    ),
    (
        "_loadRealWorkspace: don't clobber a userKey that demo-mode switching set",
        # Runs after the "add _resolveUserKey/_apiHeaders/_loadRealWorkspace"
        # patch inserts this method. _switchDemoMode sets this.userKey to the
        # demo (or restored personal) key, then calls the loaders; this method's
        # original first line reset it straight back to the localStorage key, so
        # demo reads went to the wrong key. Only resolve when nothing is set yet.
        "    this.userKey = this.userKey || this._resolveUserKey();\n",
        "  async _loadRealWorkspace() {\n    this.userKey = this._resolveUserKey();\n",
        "  async _loadRealWorkspace() {\n    this.userKey = this.userKey || this._resolveUserKey();\n",
    ),
    (
        "_loadRealHandoff: reconcile an initial demo-mode load onto the demo key (blank profile)",
        '      if (firstResolve && stillDemo) this._switchDemoMode(true, { seed: "ifEmpty" });\n',  # stable marker
        "      this.setState((s) => ({\n"
        "        profileRank: rank,\n"
        "        profileLastName: lastName,\n"
        '        profileBillet: handoff.billet || "",\n'
        '        profileUnit: handoff.unit_id || "",\n'
        "        demoModeManual: true,\n"
        "        demoMode: !(rank.trim() || lastName.trim()) && s.demoMode,\n"
        "      }));\n",
        "      const stillDemo = !(rank.trim() || lastName.trim()) && this.state.demoMode;\n"
        "      const firstResolve = !this.state.demoModeManual;\n"
        "      this.setState((s) => ({\n"
        "        profileRank: rank,\n"
        "        profileLastName: lastName,\n"
        '        profileBillet: handoff.billet || "",\n'
        '        profileUnit: handoff.unit_id || "",\n'
        "        demoModeManual: true,\n"
        "        demoMode: !(rank.trim() || lastName.trim()) && s.demoMode,\n"
        "      }));\n"
        "      // A load that lands with demo mode still on switches to the demo\n"
        "      // key, seeding only if empty so refreshing mid-demo keeps edits.\n"
        '      if (firstResolve && stillDemo) this._switchDemoMode(true, { seed: "ifEmpty" });\n',
    ),
    # ------------------------------------------------------------------
    # AI page redesign (2026-07-13): curated agent categories + richer cards,
    # staff-only skills, real prompt packs as the hero, expanded combos, and a
    # new Automations tab that sets up the user's Chief of Staff.
    # ------------------------------------------------------------------
    (
        "_loadRealAgents: use curated category + carry intended users",
        '        category: a.category || a.domain || "Other Advisors",\n',
        "      Component.AGENTS_CATALOG = data.map((a) => ({\n"
        "        id: a.id,\n"
        "        name: a.name,\n"
        "        category: a.domain,\n"
        "        description: a.description,\n"
        '        limitations: (a.disallowed_inputs || []).join(", ") || "None listed.",\n'
        "      }));\n",
        "      Component.AGENTS_CATALOG = data.map((a) => ({\n"
        "        id: a.id,\n"
        "        name: a.name,\n"
        '        category: a.category || a.domain || "Other Advisors",\n'
        "        description: a.description,\n"
        '        intendedUsers: (a.intended_users || []).join(", "),\n'
        '        limitations: (a.disallowed_inputs || []).join(", ") || "None listed.",\n'
        "      }));\n",
    ),
    (
        "_loadRealSkills: carry audience so the page can show staff skills only",
        'Component.SKILLS_CATALOG = (data.skills || []).map((s) => ({ slug: s.name, name: s.name, description: s.description, audience: s.audience || "staff" }));',
        "Component.SKILLS_CATALOG = (data.skills || []).map((s) => ({ slug: s.name, name: s.name, description: s.description }));",
        'Component.SKILLS_CATALOG = (data.skills || []).map((s) => ({ slug: s.name, name: s.name, description: s.description, audience: s.audience || "staff" }));',
    ),
    (
        "aiTabs: add the Automations tab",
        '      { id: "combos", label: "Combos" },\n'
        '      { id: "automations", label: "Automations" },\n'
        "    ].map((t) => ({\n",
        '      { id: "combos", label: "Combos" },\n    ].map((t) => ({\n',
        '      { id: "combos", label: "Combos" },\n'
        '      { id: "automations", label: "Automations" },\n'
        "    ].map((t) => ({\n",
    ),
    (
        "aiTab flags: add isAiTabAutomations",
        '    const isAiTabCombos = this.state.aiTab === "combos";\n'
        '    const isAiTabAutomations = this.state.aiTab === "automations";\n',
        '    const isAiTabCombos = this.state.aiTab === "combos";\n',
        '    const isAiTabCombos = this.state.aiTab === "combos";\n'
        '    const isAiTabAutomations = this.state.aiTab === "automations";\n',
    ),
    (
        "agentGroups: carry intended users onto each agent card",
        "        agents: agentsFiltered.filter((a) => a.category === cat).map((a) => ({\n"
        "          id: a.id,\n"
        "          name: a.name,\n"
        "          description: a.description,\n"
        "          limitations: a.limitations,\n",
        "        agents: agentsFiltered.filter((a) => a.category === cat).map((a) => ({\n"
        "          id: a.id,\n"
        "          name: a.name,\n"
        "          description: a.description,\n"
        '          intendedUsers: a.intendedUsers || "",\n'
        "          hasIntendedUsers: !!(a.intendedUsers && a.intendedUsers.length),\n"
        "          limitations: a.limitations,\n",
    ),
    (
        "agent note toggle label: clearer wording",
        '          noteToggleLabel: agentNotesOpen[a.id] ? "Collapse" : "Expand",\n',
        '          noteToggleLabel: agentNotesOpen[a.id] ? "Close notes" : "+ Notes",\n',
    ),
    (
        "skillsRendered: show staff skills only, count hidden dev skills",
        '    const staffSkills = Component.SKILLS_CATALOG.filter((sk) => (sk.audience || "staff") !== "development");\n'
        "    const hiddenDevSkillCount = Component.SKILLS_CATALOG.length - staffSkills.length;\n"
        "    const skillsRendered = staffSkills.map((sk) => ({\n",
        "    const skillsRendered = Component.SKILLS_CATALOG.map((sk) => ({\n",
        '    const staffSkills = Component.SKILLS_CATALOG.filter((sk) => (sk.audience || "staff") !== "development");\n'
        "    const hiddenDevSkillCount = Component.SKILLS_CATALOG.length - staffSkills.length;\n"
        "    const skillsRendered = staffSkills.map((sk) => ({\n",
    ),
    (
        "vals object: expose isAiTabAutomations + hiddenDevSkillCount + automations bindings",
        "      aiTabs, isAiTabAgents, isAiTabSkills, isAiTabPrompts, isAiTabCombos,\n",
        "      aiTabs, isAiTabAgents, isAiTabSkills, isAiTabPrompts, isAiTabCombos, isAiTabAutomations,\n"
        "      hiddenDevSkillCount, hasHiddenDevSkills: hiddenDevSkillCount > 0,\n"
        "      ...this._automationsVals(),\n",
    ),
    (
        "componentDidMount: also load the Chief of Staff setup",
        "    this._loadRealPromptPacks();\n    this._loadRealAgentNotes();\n    this._loadRealChiefSetup();\n",
        "    this._loadRealPromptPacks();\n    this._loadRealAgentNotes();\n",
        "    this._loadRealPromptPacks();\n    this._loadRealAgentNotes();\n    this._loadRealChiefSetup();\n",
    ),
    (
        "_switchDemoMode: also reload the Chief of Staff setup on key switch",
        # Anchor on the _switchDemoMode-unique preceding line (_loadRealGenerations
        # then _loadRealAgentNotes); componentDidMount instead precedes
        # _loadRealAgentNotes with _loadRealPromptPacks. Do NOT reach to go(lane):
        # a later patch inserts methods between this method and go(lane).
        "    this._loadRealGenerations();\n    this._loadRealAgentNotes();\n    this._loadRealChiefSetup();\n  }\n",
        "    this._loadRealGenerations();\n    this._loadRealAgentNotes();\n  }\n",
        "    this._loadRealGenerations();\n    this._loadRealAgentNotes();\n    this._loadRealChiefSetup();\n  }\n",
    ),
    (
        "add Chief of Staff setup helpers: load, save, and the automations vals",
        "  _automationsVals() {",  # stable marker
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        "  // --- Automations tab: the user's Chief of Staff setup. Saved per user to\n"
        '  // /chief-setup and rendered by the backend into a portable "Chief of\n'
        '  // Staff" block the user can paste into any chatbot.\n'
        "  async _loadRealChiefSetup() {\n"
        "    try {\n"
        '      const res = await fetch("/chief-setup/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        "      if (!res.ok) return;\n"
        "      const data = await res.json();\n"
        "      const s = data.setup || {};\n"
        "      this.setState({\n"
        '        chiefUnit: s.unit || "", chiefBillet: s.billet || "", chiefEchelon: s.echelon || "",\n'
        '        chiefDrill: s.drill_schedule || "", chiefIntent: s.commander_intent || "",\n'
        '        chiefPriorities: (s.priorities || []).join("\\n"),\n'
        '        chiefRhythm: (s.battle_rhythm || []).join("\\n"),\n'
        '        chiefWatch: (s.watch_items || []).join("\\n"),\n'
        '        chiefFormat: s.output_format || "Naval letter", chiefTone: s.tone || "Direct and professional",\n'
        '        chiefNotes: s.standing_notes || "",\n'
        '        chiefBriefingBlock: data.briefing_block || "", chiefConfigured: !!data.is_configured,\n'
        "      });\n"
        "    } catch (err) { /* keep whatever is in state */ }\n"
        "  }\n"
        "  _saveChiefSetup() {\n"
        '    const splitLines = (t) => (t || "").split("\\n").map((x) => x.trim()).filter(Boolean);\n'
        "    const payload = {\n"
        '      unit: this.state.chiefUnit || "", billet: this.state.chiefBillet || "", echelon: this.state.chiefEchelon || "",\n'
        '      drill_schedule: this.state.chiefDrill || "", commander_intent: this.state.chiefIntent || "",\n'
        "      priorities: splitLines(this.state.chiefPriorities),\n"
        "      battle_rhythm: splitLines(this.state.chiefRhythm),\n"
        "      watch_items: splitLines(this.state.chiefWatch),\n"
        '      output_format: this.state.chiefFormat || "Naval letter", tone: this.state.chiefTone || "Direct and professional",\n'
        '      standing_notes: this.state.chiefNotes || "",\n'
        "    };\n"
        "    this.setState({ chiefSaving: true });\n"
        '    fetch("/chief-setup/" + encodeURIComponent(this.userKey), {\n'
        '      method: "PUT",\n'
        '      headers: this._apiHeaders({ "Content-Type": "application/json" }),\n'
        "      body: JSON.stringify(payload),\n"
        "    })\n"
        "      .then((res) => res.json().then((body) => ({ ok: res.ok, body })))\n"
        "      .then(({ ok, body }) => {\n"
        '        if (!ok) throw new Error("save failed");\n'
        '        this.setState({ chiefBriefingBlock: body.briefing_block || "", chiefConfigured: !!body.is_configured, chiefSaving: false, chiefSaved: true });\n'
        "        clearTimeout(this._chiefSavedTimer);\n"
        "        this._chiefSavedTimer = setTimeout(() => this.setState({ chiefSaved: false }), 2000);\n"
        "      })\n"
        '      .catch(() => { this.setState({ chiefSaving: false }); window.alert("Could not save your Chief of Staff setup to the server."); });\n'
        "  }\n"
        "  _automationsVals() {\n"
        "    const bind = (key) => (e) => this.setState({ [key]: e.target.value });\n"
        "    return {\n"
        '      chiefUnit: this.state.chiefUnit || "", onChiefUnit: bind("chiefUnit"),\n'
        '      chiefBillet: this.state.chiefBillet || "", onChiefBillet: bind("chiefBillet"),\n'
        '      chiefEchelon: this.state.chiefEchelon || "", onChiefEchelon: bind("chiefEchelon"),\n'
        '      chiefDrill: this.state.chiefDrill || "", onChiefDrill: bind("chiefDrill"),\n'
        '      chiefIntent: this.state.chiefIntent || "", onChiefIntent: bind("chiefIntent"),\n'
        '      chiefPriorities: this.state.chiefPriorities || "", onChiefPriorities: bind("chiefPriorities"),\n'
        '      chiefRhythm: this.state.chiefRhythm || "", onChiefRhythm: bind("chiefRhythm"),\n'
        '      chiefWatch: this.state.chiefWatch || "", onChiefWatch: bind("chiefWatch"),\n'
        '      chiefFormat: this.state.chiefFormat || "Naval letter", onChiefFormat: bind("chiefFormat"),\n'
        '      chiefTone: this.state.chiefTone || "Direct and professional", onChiefTone: bind("chiefTone"),\n'
        '      chiefNotes: this.state.chiefNotes || "", onChiefNotes: bind("chiefNotes"),\n'
        '      chiefBriefingBlock: this.state.chiefBriefingBlock || "",\n'
        "      chiefHasBlock: !!(this.state.chiefBriefingBlock && this.state.chiefBriefingBlock.length),\n"
        "      chiefConfigured: !!this.state.chiefConfigured,\n"
        '      chiefSaveLabel: this.state.chiefSaving ? "Saving…" : (this.state.chiefSaved ? "Saved ✓" : "Save setup"),\n'
        "      onChiefSave: (e) => { if (e) e.preventDefault(); this._saveChiefSetup(); },\n"
        '      chiefCopyLabel: this.state.chiefCopiedBlock ? "Copied" : "Copy Chief of Staff block",\n'
        '      onChiefCopy: () => { navigator.clipboard && navigator.clipboard.writeText(this.state.chiefBriefingBlock || ""); this.setState({ chiefCopiedBlock: true }); clearTimeout(this._chiefCopyTimer); this._chiefCopyTimer = setTimeout(() => this.setState({ chiefCopiedBlock: false }), 1500); },\n'
        "    };\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "state defaults: Chief of Staff setup fields",
        '    chiefFormat: "Naval letter",',  # stable marker
        "    skillNotes: {},\n",
        "    skillNotes: {},\n"
        '    chiefUnit: "", chiefBillet: "", chiefEchelon: "", chiefDrill: "", chiefIntent: "",\n'
        '    chiefPriorities: "", chiefRhythm: "", chiefWatch: "",\n'
        '    chiefFormat: "Naval letter", chiefTone: "Direct and professional", chiefNotes: "",\n'
        '    chiefBriefingBlock: "", chiefConfigured: false,\n',
    ),
    (
        "AI top intro: mention setting up your Chief of Staff",
        '<strong style="color:#eef2f6;">Use this page to</strong> understand what each agent/skill actually does, leave notes to feed back into their files, keep editable prompt packs for any chatbot, and see suggested agent combinations for common situations.',
        '<strong style="color:#eef2f6;">Use this page to</strong> understand what each agent and skill does, set up your own Chief of Staff, keep copy-paste prompt packs for any chatbot, and see suggested agent combinations for common situations. New here? Start on the Automations tab.',
    ),
    (
        "Agents tab: add a what/why/how-to-call explainer block",
        '<h3 style="margin:0 0 6px;font-size:0.95rem;font-weight:700;">What these agents are</h3>',  # stable marker
        '      <sc-if value="{{ isAiTabAgents }}" hint-placeholder-val="{{ true }}">\n'
        '      <div style="display:grid;gap:16px;">\n'
        '        <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;max-width:260px;">Category\n',
        '      <sc-if value="{{ isAiTabAgents }}" hint-placeholder-val="{{ true }}">\n'
        '      <div style="display:grid;gap:16px;">\n'
        '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:14px 18px;">\n'
        '          <h3 style="margin:0 0 6px;font-size:0.95rem;font-weight:700;">What these agents are</h3>\n'
        '          <p style="margin:0 0 8px;color:#c7cfd8;font-size:0.84rem;line-height:1.55;">Each agent is a <strong>role-tuned AI advisor</strong> defined in this repo — a Chief of Staff, a Planning Advisor, a full virtual staff council, and more. Each carries its own doctrine references, guardrails, and a job it is good at, and produces advisory drafts you verify — never authoritative products.</p>\n'
        '          <p style="margin:0 0 6px;color:#c7cfd8;font-size:0.84rem;line-height:1.55;"><strong style="color:#eef2f6;">Agentic AI</strong> means the AI does not just answer once — it works a task: it takes your inputs, applies a role’s judgment and references, and can hand off to another agent (see the Combos tab).</p>\n'
        '          <p style="margin:0;color:#8a94a0;font-size:0.8rem;line-height:1.5;"><strong style="color:#aab4bf;">How to call one:</strong> open this repo in an AI code assistant (Claude Code, Codex) and ask for that role by name, or copy a Prompt pack into any chatbot. To ground your Chief of Staff first, use the <strong>Automations</strong> tab.</p>\n'
        "        </section>\n"
        '        <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;max-width:260px;">Category\n',
    ),
    (
        "Agents tab: description + who-for always visible, limitations under notes",
        '                  <p style="margin:8px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ a.description }}</p>\n'
        '                  <sc-if value="{{ a.hasIntendedUsers }}" hint-placeholder-val="{{ true }}">',  # stable marker
        '                  <sc-if value="{{ a.noteOpen }}" hint-placeholder-val="{{ false }}">\n'
        '                    <p style="margin:10px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ a.description }}</p>\n'
        '                    <p style="margin:6px 0 0;color:#8a94a0;font-size:0.78rem;line-height:1.45;"><strong style="color:#aab4bf;">Limitations:</strong> {{ a.limitations }}</p>\n',
        '                  <p style="margin:8px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ a.description }}</p>\n'
        '                  <sc-if value="{{ a.hasIntendedUsers }}" hint-placeholder-val="{{ true }}">\n'
        '                  <p style="margin:6px 0 0;color:#8a94a0;font-size:0.78rem;line-height:1.45;"><strong style="color:#aab4bf;">Who it\'s for:</strong> {{ a.intendedUsers }}</p>\n'
        "                  </sc-if>\n"
        '                  <sc-if value="{{ a.noteOpen }}" hint-placeholder-val="{{ false }}">\n'
        '                    <p style="margin:8px 0 0;color:#8a94a0;font-size:0.78rem;line-height:1.45;"><strong style="color:#aab4bf;">Not for:</strong> {{ a.limitations }}</p>\n',
    ),
    (
        "expand AGENT_COMBOS with more, richer plays",
        '  static AGENT_COMBOS = [\n    {\n      title: "Building a training progression",',
        '  static AGENT_COMBOS = [\n    {\n      title: "Building a training progression",\n'
        '      chain: ["planning-advisor", "staff-products", "assessment-learning-advisor"],\n'
        "      description: \"Set the planning tempo and OPT structure first, draft the actual training/OPORD scaffold, then close the loop by wiring the next AAR's measures back into the next cycle's plan.\",\n"
        "    },",
        "  static AGENT_COMBOS = [\n"
        "    {\n"
        '      title: "Set up your Chief of Staff, then work",\n'
        '      chain: ["chief-of-staff", "planning-advisor", "staff-products"],\n'
        '      description: "Start in the Automations tab to give your Chief of Staff your unit, priorities, and battle rhythm. Then it frames the drill period, the Planning Advisor sets tempo, and Staff Products drafts what\'s due.",\n'
        "    },\n"
        "    {\n"
        '      title: "Building a training progression",\n'
        '      chain: ["planning-advisor", "staff-products", "assessment-learning-advisor"],\n'
        "      description: \"Set the planning tempo and OPT structure first, draft the actual training/OPORD scaffold, then close the loop by wiring the next AAR's measures back into the next cycle's plan.\",\n"
        "    },",
    ),
    (
        "add three more combos before the closing bracket of AGENT_COMBOS",
        '      description: "Draft the report scaffold and comments, then run it through the writing coach to make sure the narrative tone matches the marks before it\'s submitted.",\n'
        "    },\n"
        "  ];",
        '      description: "Draft the report scaffold and comments, then run it through the writing coach to make sure the narrative tone matches the marks before it\'s submitted.",\n'
        "    },\n"
        "    {\n"
        '      title: "MAGTF cross-talk on a scheme of maneuver",\n'
        '      chain: ["gce", "fires-advisor", "ace", "lce"],\n'
        '      description: "Walk a concept around the MAGTF: GCE frames the ground scheme, Fires integrates fire support, ACE checks air-ground support and airspace, and LCE pressure-tests whether sustainment actually supports it.",\n'
        "    },\n"
        "    {\n"
        '      title: "Full staff estimate before a decision brief",\n'
        '      chain: ["staff-opso", "staff-s2", "staff-s4", "red-team-assumptions-challenge", "staff-products"],\n'
        '      description: "Run the idea past the OpsO, Intel, and Logistics seats of the Virtual Staff Council, red-team the assumptions, then have Staff Products assemble the decision brief from what survived.",\n'
        "    },\n"
        "    {\n"
        '      title: "New-join in-processing sprint",\n'
        '      chain: ["unit-checkin", "pki-cac-troubleshooter", "chief-of-staff"],\n'
        '      description: "Unit Check-In lays out the admin and reporting path, the PKI/CAC troubleshooter clears the inevitable access blocker, and the Chief of Staff folds the follow-ups into your running action list.",\n'
        "    },\n"
        "  ];",
    ),
    (
        "Skills tab: intro, condensed cards (notes collapsed), hidden-dev note",
        '          <h3 style="margin:0 0 6px;font-size:0.95rem;font-weight:700;">Skills — staff shortcuts</h3>',  # stable marker
        '      <div style="display:grid;gap:10px;">\n'
        '        <sc-for list="{{ skillsRendered }}" as="s" hint-placeholder-count="4">\n'
        '          <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:16px 18px;">\n'
        "            <h3 style=\"margin:0;font-size:0.96rem;font-weight:700;font-family:'IBM Plex Mono',monospace;\">{{ s.name }}</h3>\n"
        '            <p style="margin:8px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ s.description }}</p>\n'
        '            <textarea rows="2" value="{{ s.note }}" sc-camel-on-change="{{ s.onNoteChange }}" placeholder="Notes to feed back into this skill\'s file…" style="margin-top:10px;width:100%;box-sizing:border-box;border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.82rem;resize:vertical;"></textarea>\n'
        '            <button type="button" sc-camel-on-click="{{ s.onCopyNote }}" style="margin-top:6px;height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">Copy note for repo</button>\n'
        "          </section>\n"
        "        </sc-for>\n"
        "      </div>\n",
        '      <div style="display:grid;gap:10px;">\n'
        '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:14px 18px;">\n'
        '          <h3 style="margin:0 0 6px;font-size:0.95rem;font-weight:700;">Skills — staff shortcuts</h3>\n'
        '          <p style="margin:0;color:#c7cfd8;font-size:0.84rem;line-height:1.55;">Skills are pre-packaged procedures an AI assistant follows for a recurring staff task — build a brief, turn a meeting into action items, write a session handoff. In an AI code assistant working this repo, name the skill or just describe the task. Showing staff-work skills only.</p>\n'
        "        </section>\n"
        '        <sc-for list="{{ skillsRendered }}" as="s" hint-placeholder-count="4">\n'
        '          <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:13px 16px;">\n'
        "            <h3 style=\"margin:0;font-size:0.9rem;font-weight:700;font-family:'IBM Plex Mono',monospace;\">{{ s.name }}</h3>\n"
        '            <p style="margin:6px 0 0;color:#c7cfd8;font-size:0.83rem;line-height:1.5;">{{ s.description }}</p>\n'
        '            <details style="margin-top:8px;">\n'
        '              <summary style="cursor:pointer;color:#8a94a0;font-size:0.76rem;font-weight:600;">Add a note for this skill\'s file</summary>\n'
        '              <textarea rows="2" value="{{ s.note }}" sc-camel-on-change="{{ s.onNoteChange }}" placeholder="Notes to feed back into this skill\'s file…" style="margin-top:8px;width:100%;box-sizing:border-box;border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.82rem;resize:vertical;"></textarea>\n'
        '              <button type="button" sc-camel-on-click="{{ s.onCopyNote }}" style="margin-top:6px;height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">Copy note for repo</button>\n'
        "            </details>\n"
        "          </section>\n"
        "        </sc-for>\n"
        '        <sc-if value="{{ hasHiddenDevSkills }}" hint-placeholder-val="{{ false }}">\n'
        '          <p style="margin:0;color:#5a6572;font-size:0.76rem;line-height:1.45;">Some repo-development skills are hidden here — they are for contributors building the app, not staff work. See <span style="font-family:\'IBM Plex Mono\',monospace;">skills/README.md</span>.</p>\n'
        "        </sc-if>\n"
        "      </div>\n",
    ),
    (
        "Prompt packs: stronger repo-pack intro (pseudo staff agent)",
        "pseudo staff section in a tool you already have",  # stable marker (new-text fragment)
        "Read-only copies of the packs in <span style=\"font-family:'IBM Plex Mono',monospace;\">prompt-packs/</span> — paste the full text into any AI chat.",
        "Each pack turns any chatbot (ChatGPT, Claude, Gemini) into a Marine staff advisor for that lane — a pseudo staff section in a tool you already have. Copy the whole pack and paste it as your first message, then ask your question.",
    ),
    (
        "Prompt packs: collapse the build-your-own editable packs below the repo packs",
        '<details style="border:1px solid #313844;border-radius:8px;background:#0f1318;">\n'
        '          <summary style="cursor:pointer;list-style:none;padding:12px 16px;font-size:0.9rem;font-weight:700;color:#eef2f6;">Build your own quick prompts (optional)</summary>\n'
        '          <div style="padding:0 16px 16px;display:grid;gap:16px;">\n'
        '        <sc-for list="{{ promptPacksRendered }}" as="pack" hint-placeholder-count="4">\n',
        '        <sc-for list="{{ promptPacksRendered }}" as="pack" hint-placeholder-count="4">\n',
        '        <details style="border:1px solid #313844;border-radius:8px;background:#0f1318;">\n'
        '          <summary style="cursor:pointer;list-style:none;padding:12px 16px;font-size:0.9rem;font-weight:700;color:#eef2f6;">Build your own quick prompts (optional)</summary>\n'
        '          <div style="padding:0 16px 16px;display:grid;gap:16px;">\n'
        '        <sc-for list="{{ promptPacksRendered }}" as="pack" hint-placeholder-count="4">\n',
    ),
    (
        "Prompt packs: close the build-your-own details wrapper after the add-pack form",
        '<button type="submit" style="height:36px;padding:0 16px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:600;font-size:0.84rem;cursor:pointer;">+ Add pack</button>\n'
        "        </form>\n"
        "        </div>\n"
        "        </details>\n"
        "      </div>\n"
        "      </sc-if>\n",
        '<button type="submit" style="height:36px;padding:0 16px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:600;font-size:0.84rem;cursor:pointer;">+ Add pack</button>\n'
        "        </form>\n"
        "      </div>\n"
        "      </sc-if>\n",
        '<button type="submit" style="height:36px;padding:0 16px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:600;font-size:0.84rem;cursor:pointer;">+ Add pack</button>\n'
        "        </form>\n"
        "        </div>\n"
        "        </details>\n"
        "      </div>\n"
        "      </sc-if>\n",
    ),
    (
        "Automations tab: Chief of Staff setup wizard template",
        '<sc-if value="{{ isAiTabAutomations }}" hint-placeholder-val="{{ false }}">',  # stable marker
        "      </sc-if>\n"
        "    </div>\n"
        "    </sc-if>\n"
        "\n"
        "    <!-- ==================== LINKS LANE ==================== -->\n",
        "      </sc-if>\n"
        "\n"
        '      <sc-if value="{{ isAiTabAutomations }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="display:grid;gap:16px;">\n'
        '        <section style="border:1px solid #2a3c4a;border-radius:8px;background:#0f1620;padding:16px 18px;">\n'
        '          <h3 style="margin:0 0 6px;font-size:1rem;font-weight:700;">Set up your Chief of Staff</h3>\n'
        '          <p style="margin:0;color:#c7cfd8;font-size:0.84rem;line-height:1.55;">Fill this in once. The app remembers your context, and you get a copy-paste <strong>Chief of Staff</strong> block you can drop into ChatGPT, Claude, Gemini — any chatbot — to get an advisor that already knows your unit, priorities, and battle rhythm. UNCLASSIFIED only.</p>\n'
        "        </section>\n"
        '        <form sc-camel-on-submit="{{ onChiefSave }}" style="display:grid;gap:14px;border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px 20px;">\n'
        '          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">\n'
        '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Unit\n'
        '              <input value="{{ chiefUnit }}" sc-camel-on-change="{{ onChiefUnit }}" placeholder="e.g. 4th CAG" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n'
        "            </label>\n"
        '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Billet\n'
        '              <input value="{{ chiefBillet }}" sc-camel-on-change="{{ onChiefBillet }}" placeholder="e.g. S-4A" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n'
        "            </label>\n"
        '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Echelon\n'
        '              <input value="{{ chiefEchelon }}" sc-camel-on-change="{{ onChiefEchelon }}" placeholder="e.g. Battalion" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n'
        "            </label>\n"
        '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Next drill / schedule\n'
        '              <input value="{{ chiefDrill }}" sc-camel-on-change="{{ onChiefDrill }}" placeholder="e.g. 09–10 AUG" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n'
        "            </label>\n"
        "          </div>\n"
        '          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Commander\'s intent / your focus\n'
        '            <textarea rows="2" value="{{ chiefIntent }}" sc-camel-on-change="{{ onChiefIntent }}" placeholder="What matters most right now…" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n'
        "          </label>\n"
        '          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Current priorities (one per line)\n'
        '            <textarea rows="3" value="{{ chiefPriorities }}" sc-camel-on-change="{{ onChiefPriorities }}" placeholder="e.g. Close RQS gaps" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n'
        "          </label>\n"
        '          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Recurring battle rhythm (one per line)\n'
        '            <textarea rows="3" value="{{ chiefRhythm }}" sc-camel-on-change="{{ onChiefRhythm }}" placeholder="e.g. 0730 COC sync" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n'
        "          </label>\n"
        '          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Watch items — keep me ahead of these (one per line)\n'
        '            <textarea rows="2" value="{{ chiefWatch }}" sc-camel-on-change="{{ onChiefWatch }}" placeholder="e.g. AT budget MARADMIN" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n'
        "          </label>\n"
        '          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">\n'
        '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Default output format\n'
        '              <input value="{{ chiefFormat }}" sc-camel-on-change="{{ onChiefFormat }}" placeholder="Naval letter / Bullet / SMEAC" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n'
        "            </label>\n"
        '            <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Tone\n'
        '              <input value="{{ chiefTone }}" sc-camel-on-change="{{ onChiefTone }}" placeholder="Direct and professional" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;">\n'
        "            </label>\n"
        "          </div>\n"
        '          <label style="display:grid;gap:4px;font-size:0.74rem;font-weight:600;color:#8a94a0;">Standing notes\n'
        '            <textarea rows="2" value="{{ chiefNotes }}" sc-camel-on-change="{{ onChiefNotes }}" placeholder="Anything your Chief of Staff should always keep in mind…" style="border:1px solid #313844;border-radius:6px;padding:8px 10px;background:#0d1014;color:#eef2f6;font:inherit;font-size:0.84rem;resize:vertical;"></textarea>\n'
        "          </label>\n"
        '          <button type="submit" style="justify-self:start;height:38px;padding:0 20px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:700;font-size:0.86rem;cursor:pointer;">{{ chiefSaveLabel }}</button>\n'
        "        </form>\n"
        '        <sc-if value="{{ chiefHasBlock }}" hint-placeholder-val="{{ false }}">\n'
        '        <section style="border:1px solid #313844;border-radius:8px;background:#0f1318;padding:16px 18px;">\n'
        '          <div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;margin-bottom:8px;">\n'
        '            <h3 style="margin:0;font-size:0.95rem;font-weight:700;">Your Chief of Staff block</h3>\n'
        '            <button type="button" sc-camel-on-click="{{ onChiefCopy }}" style="flex:0 0 auto;height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">{{ chiefCopyLabel }}</button>\n'
        "          </div>\n"
        '          <p style="margin:0 0 8px;color:#8a94a0;font-size:0.78rem;line-height:1.45;">Paste this as your first message in any chatbot. Update the fields above and save to regenerate it.</p>\n'
        "          <pre style=\"margin:0;white-space:pre-wrap;word-break:break-word;font-family:'IBM Plex Mono',monospace;font-size:0.78rem;line-height:1.5;color:#c7cfd8;background:#0b0e12;border:1px solid #313844;border-radius:6px;padding:12px 14px;max-height:340px;overflow:auto;\">{{ chiefBriefingBlock }}</pre>\n"
        "        </section>\n"
        "        </sc-if>\n"
        "      </div>\n"
        "      </sc-if>\n"
        "    </div>\n"
        "    </sc-if>\n"
        "\n"
        "    <!-- ==================== LINKS LANE ==================== -->\n",
    ),
    # ------------------------------------------------------------------
    # In-dash shutdown (2026-07-14): a power button in the top bar replaces
    # the separate "Stop SMCR Staff AI" desktop shortcut, so one icon (plus
    # this button) covers the whole lifecycle.
    # ------------------------------------------------------------------
    (
        "top bar: add a power (shut down) button next to the profile button",
        'title="Shut down SMCR Staff AI"',  # stable marker
        '      <button type="button" sc-camel-on-click="{{ toggleProfile }}" title="Profile &amp; preferences" style="width:30px;height:30px;border-radius:50%;border:1px solid #313844;background:#1a2027;color:#aab4bf;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;flex:0 0 auto;">\n'
        '        <svg width="16" height="16" sc-camel-view-box="0 0 24 24" fill="currentColor"><circle cx="12" cy="8" r="4"></circle><path d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7"></path></svg>\n'
        "      </button>\n",
        '      <button type="button" sc-camel-on-click="{{ toggleProfile }}" title="Profile &amp; preferences" style="width:30px;height:30px;border-radius:50%;border:1px solid #313844;background:#1a2027;color:#aab4bf;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;flex:0 0 auto;">\n'
        '        <svg width="16" height="16" sc-camel-view-box="0 0 24 24" fill="currentColor"><circle cx="12" cy="8" r="4"></circle><path d="M4 20c0-4.4 3.6-7 8-7s8 2.6 8 7"></path></svg>\n'
        "      </button>\n"
        '      <button type="button" sc-camel-on-click="{{ onShutdown }}" title="Shut down SMCR Staff AI" style="width:30px;height:30px;border-radius:50%;border:1px solid #3a2226;background:#1b1114;color:#d8a0a5;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;flex:0 0 auto;">\n'
        '        <svg width="15" height="15" sc-camel-view-box="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M12 3v9"></path><path d="M6 6.2a8 8 0 1 0 12 0"></path></svg>\n'
        "      </button>\n",
    ),
    (
        "header: add the powered-down overlay before the profile drawer",
        "SMCR Staff AI is shut down.",  # stable marker
        '  <sc-if value="{{ profileOpen }}" hint-placeholder-val="{{ false }}">\n',
        '  <sc-if value="{{ shutdownDone }}" hint-placeholder-val="{{ false }}">\n'
        '  <div style="position:fixed;inset:0;z-index:100;background:#0b0e12;display:flex;align-items:center;justify-content:center;">\n'
        '    <div style="max-width:420px;text-align:center;padding:24px;">\n'
        '      <div style="font-size:2rem;margin-bottom:12px;color:#4a9e6a;">⏻</div>\n'
        '      <h2 style="margin:0 0 10px;font-size:1.1rem;font-weight:700;color:#eef2f6;">SMCR Staff AI is shut down.</h2>\n'
        '      <p style="margin:0;color:#8a94a0;font-size:0.9rem;line-height:1.6;">You can close this tab. To start it again, double-click the <strong style="color:#aab4bf;">SMCR Staff AI</strong> icon on your desktop (or run start.bat).</p>\n'
        "    </div>\n"
        "  </div>\n"
        "  </sc-if>\n"
        "\n"
        '  <sc-if value="{{ profileOpen }}" hint-placeholder-val="{{ false }}">\n',
    ),
    (
        "vals: shutdownDone flag + onShutdown handler (confirm, POST, overlay)",
        "      onShutdown: () => {",  # stable marker
        "      profileOpen: this.state.profileOpen,\n"
        "      toggleProfile: () => this.setState((s) => ({ profileOpen: !s.profileOpen })),\n",
        "      profileOpen: this.state.profileOpen,\n"
        "      shutdownDone: !!this.state.shutdownDone,\n"
        "      onShutdown: () => {\n"
        '        if (!window.confirm("Shut down SMCR Staff AI? The dashboard goes offline until you start it again from the desktop icon (or start.bat).")) return;\n'
        '        fetch("/dashboard/shutdown", { method: "POST", headers: this._apiHeaders() })\n'
        "          .then(() => this.setState({ shutdownDone: true }))\n"
        "          .catch(() => this.setState({ shutdownDone: true }));\n"
        "      },\n"
        "      toggleProfile: () => this.setState((s) => ({ profileOpen: !s.profileOpen })),\n",
    ),
    (
        "_switchDemoMode: wipe demo files from disk when toggling off",
        'fetch("/demo/workspace", { method: "DELETE", headers: this._apiHeaders() }).catch(() => {});',  # stable marker
        "    } else {\n"
        "      this.userKey = this._realUserKey || this._resolveUserKey();\n"
        "      // Clear the demo profile fields; _loadRealHandoff refills them from\n"
        "      // the real personal handoff, or leaves them blank if none is saved.\n"
        '      this.setState({ profileRank: "", profileLastName: "", profileBillet: "", profileUnit: "" });\n'
        "      this._loadRealHandoff();\n"
        "    }\n",
        "    } else {\n"
        "      this.userKey = this._realUserKey || this._resolveUserKey();\n"
        "      // Toggling off is an explicit exit from demo mode, so remove the\n"
        "      // disposable demo files from disk instead of leaving them under the\n"
        "      // shared demo key. Targets the demo key server-side; no-op if absent.\n"
        '      fetch("/demo/workspace", { method: "DELETE", headers: this._apiHeaders() }).catch(() => {});\n'
        "      // Clear the demo profile fields; _loadRealHandoff refills them from\n"
        "      // the real personal handoff, or leaves them blank if none is saved.\n"
        '      this.setState({ profileRank: "", profileLastName: "", profileBillet: "", profileUnit: "" });\n'
        "      this._loadRealHandoff();\n"
        "    }\n",
    ),
    # ------------------------------------------------------------------
    # Today in history (2026-07-14): replace the design export's hardcoded
    # 11 July card with the real workspace payload. Sparse seed data still
    # supplies a deterministic fallback, but the API tells the UI whether
    # the item truly matches today's local date so the label stays honest.
    # ------------------------------------------------------------------
    (
        "workspace load: map history spotlight and exact-date flag",
        "const historySpotlight = (data.today_in_history || [])[0] || null;",  # stable marker
        "      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n"
        "      // Ticker items and personal documents ride along on the same payload.\n",
        "      const actions = (data.tracked_actions || []).map((a) => this._mapRealAction(a));\n"
        "      const historySpotlight = (data.today_in_history || [])[0] || null;\n"
        "      // Ticker items and personal documents ride along on the same payload.\n",
    ),
    (
        "workspace load: store history spotlight and exact-date flag",
        "historyIsToday: !!data.history_is_today,",  # stable marker
        "      this.setState((s) => ({\n        actions,\n        realMaradmins: mapTicker(data.maradmin_ticker),\n",
        "      this.setState((s) => ({\n"
        "        actions,\n"
        "        historySpotlight,\n"
        "        historyIsToday: !!data.history_is_today,\n"
        "        realMaradmins: mapTicker(data.maradmin_ticker),\n",
    ),
    (
        "vals: format the history spotlight from workspace data",
        "const historySpotlight = this.state.historySpotlight;",  # stable marker
        "    const onOpenReceiptsFolder = activeWorkflowDoc ? this.openFileLocation(activeWorkflowDoc.receiptsFolder) : () => {};\n\n"
        "    return {\n",
        "    const onOpenReceiptsFolder = activeWorkflowDoc ? this.openFileLocation(activeWorkflowDoc.receiptsFolder) : () => {};\n"
        "    const historySpotlight = this.state.historySpotlight;\n"
        '    const historyMonths = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];\n'
        '    const historyReference = historySpotlight && historySpotlight.references && historySpotlight.references[0] || "";\n'
        "    const historySourceIsLink = /^https?:\\/\\//i.test(historyReference);\n"
        "    const historyHeadline = historySpotlight\n"
        '      ? String(historySpotlight.day).padStart(2, "0") + " " + (historyMonths[historySpotlight.month - 1] || "") + " " + historySpotlight.year_label + " — " + historySpotlight.title\n'
        '      : "";\n\n'
        "    return {\n",
    ),
    (
        "vals: expose history spotlight bindings",
        'historyLabel: this.state.historyIsToday ? "Today in history" : "History spotlight",',  # stable marker
        '      quote: this.state.quote,\n      goWatch: this.go("watch"),\n',
        "      quote: this.state.quote,\n"
        "      historyVisible: !!historySpotlight,\n"
        '      historyLabel: this.state.historyIsToday ? "Today in history" : "History spotlight",\n'
        "      historyHeadline,\n"
        '      historyDetails: historySpotlight ? historySpotlight.summary : "",\n'
        "      historySourceIsLink,\n"
        "      historySourceIsText: !!historyReference && !historySourceIsLink,\n"
        '      historySourceUrl: historySourceIsLink ? historyReference : "",\n'
        '      historySourceLabel: historySourceIsLink ? "View official source ↗" : historyReference,\n'
        '      goWatch: this.go("watch"),\n',
    ),
    (
        "overview: render history spotlight from real workspace data",
        "{{ historyHeadline }}",  # stable marker
        "      <!-- Today in history (expandable) -->\n"
        '      <details style="border:1px solid #313844;border-radius:8px;background:#0f1318;">\n'
        '        <summary style="cursor:pointer;list-style:none;padding:16px 18px;display:flex;gap:14px;align-items:center;">\n'
        '          <span style="flex:0 0 auto;font-size:0.7rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#8a94a0;padding:4px 8px;border:1px solid #313844;border-radius:4px;">Today in history</span>\n'
        '          <p style="margin:0;font-size:0.88rem;color:#c7cfd8;line-height:1.5;flex:1;">11 JUL 1798 — The U.S. Marine Corps was re-established by an Act of Congress, formally creating the Corps as a standing military force.</p>\n'
        '          <span style="color:#5a6572;font-size:0.8rem;">Details ▾</span>\n'
        "        </summary>\n"
        '        <div style="padding:0 18px 16px;display:grid;gap:8px;border-top:1px solid #1a2027;margin-top:2px;padding-top:12px;">\n'
        '          <p style="margin:0;color:#aab4bf;font-size:0.84rem;line-height:1.5;">The original Continental Marines, formed in 1775, were disbanded after the Revolutionary War. On 11 July 1798, Congress passed "An Act for Establishing and Organizing a Marine Corps," creating the modern Marine Corps as a permanent service under the Department of the Navy — the date the Corps now marks as its founding.</p>\n'
        '          <a href="https://www.usmcu.edu/Research/Marine-Corps-History-Division/" target="_blank" rel="noopener" style="font-size:0.82rem;font-weight:600;">Source: Marine Corps History Division ↗</a>\n'
        "        </div>\n"
        "      </details>\n",
        "      <!-- Today in history / history spotlight (expandable) -->\n"
        '      <sc-if value="{{ historyVisible }}" hint-placeholder-val="{{ false }}">\n'
        '      <details style="border:1px solid #313844;border-radius:8px;background:#0f1318;">\n'
        '        <summary style="cursor:pointer;list-style:none;padding:16px 18px;display:flex;gap:14px;align-items:center;">\n'
        '          <span style="flex:0 0 auto;font-size:0.7rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;color:#8a94a0;padding:4px 8px;border:1px solid #313844;border-radius:4px;">{{ historyLabel }}</span>\n'
        '          <p style="margin:0;font-size:0.88rem;color:#c7cfd8;line-height:1.5;flex:1;">{{ historyHeadline }}</p>\n'
        '          <span style="color:#5a6572;font-size:0.8rem;">Details ▾</span>\n'
        "        </summary>\n"
        '        <div style="padding:0 18px 16px;display:grid;gap:8px;border-top:1px solid #1a2027;margin-top:2px;padding-top:12px;">\n'
        '          <p style="margin:0;color:#aab4bf;font-size:0.84rem;line-height:1.5;">{{ historyDetails }}</p>\n'
        '          <sc-if value="{{ historySourceIsLink }}" hint-placeholder-val="{{ false }}"><a href="{{ historySourceUrl }}" target="_blank" rel="noopener" style="font-size:0.82rem;font-weight:600;">{{ historySourceLabel }}</a></sc-if>\n'
        '          <sc-if value="{{ historySourceIsText }}" hint-placeholder-val="{{ false }}"><p style="margin:0;color:#8a94a0;font-size:0.78rem;">Source: {{ historySourceLabel }}</p></sc-if>\n'
        "        </div>\n"
        "      </details>\n"
        "      </sc-if>\n",
    ),
    (
        "history source: avoid claiming every imported URL is official",
        'historySourceLabel: historySourceIsLink ? "View source ↗" : historyReference,',
        '      historySourceLabel: historySourceIsLink ? "View official source ↗" : historyReference,\n',
        '      historySourceLabel: historySourceIsLink ? "View source ↗" : historyReference,\n',
    ),
    # ------------------------------------------------------------------
    # Feed refresh (2026-07-14): the design export's button only changed the
    # "Updated" label. Call every real feed refresh route concurrently, then
    # reload the workspace so the newest ticker data is actually rendered.
    # ------------------------------------------------------------------
    (
        "feeds: add real refresh orchestration with partial-failure feedback",
        "  async _refreshFeeds() {",  # stable marker
        "  }\n\n  // --- Feeds: real backend wiring. Custom watch feeds are global (no\n",
        "  }\n\n"
        "  async _refreshFeeds() {\n"
        "    if (this.state.feedRefreshRunning) return;\n"
        "    this.setState({ feedRefreshRunning: true });\n"
        "    const refreshOne = async (url) => {\n"
        '      const res = await fetch(url, { method: "POST", headers: this._apiHeaders() });\n'
        "      let payload = null;\n"
        "      try { payload = await res.json(); } catch (err) {}\n"
        "      const warnings = payload && Array.isArray(payload.warnings) ? payload.warnings : [];\n"
        '      if (!res.ok || warnings.length) throw new Error("refresh failed: " + url);\n'
        "      return payload;\n"
        "    };\n"
        "    const refreshTargets = [\n"
        '      { label: "MARADMIN", url: "/maradmins/refresh" },\n'
        '      { label: "NAVADMIN", url: "/message-watch/navadmins/refresh" },\n'
        '      { label: "ALNAV", url: "/message-watch/alnavs/refresh" },\n'
        '      { label: "DoD", url: "/message-watch/dod/refresh" },\n'
        "    ];\n"
        "    (this.state.feeds || []).filter((feed) => feed.isReal && feed.enabled !== false).forEach((feed) => {\n"
        '      refreshTargets.push({ label: feed.name, url: "/custom-watch-feeds/" + encodeURIComponent(feed.id) + "/refresh" });\n'
        "    });\n"
        "    const results = await Promise.allSettled(refreshTargets.map((target) => refreshOne(target.url)));\n"
        '    const failedLabels = results.map((result, index) => result.status === "rejected" ? refreshTargets[index].label : null).filter(Boolean);\n'
        "    await Promise.all([this._loadRealWorkspace(), this._loadRealFeeds()]);\n"
        '    const failureNote = failedLabels.length ? " · " + failedLabels.join(", ") + " failed" : "";\n'
        '    this.setState({ feedRefreshRunning: false, feedUpdated: "just now" + failureNote });\n'
        "  }\n\n"
        "  // --- Feeds: real backend wiring. Custom watch feeds are global (no\n",
    ),
    (
        "feeds: carry enabled state for custom refresh filtering",
        "      enabled: f.enabled !== false,",  # stable marker
        "      isReal: true,\n    };\n",
        "      isReal: true,\n      enabled: f.enabled !== false,\n    };\n",
    ),
    (
        "overview feeds: show live refresh status",
        "{{ feedRefreshStatus }}",  # stable marker
        '          <span style="font-size:0.76rem;color:#8a94a0;">Updated {{ feedUpdated }}</span>\n',
        '          <span style="font-size:0.76rem;color:#8a94a0;">{{ feedRefreshStatus }}</span>\n',
    ),
    (
        "overview feeds: show progress in the refresh button",
        "{{ refreshFeedsLabel }}",  # stable marker
        '          <button type="button" sc-camel-on-click="{{ refreshFeeds }}" style="height:34px;padding:0 16px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.84rem;cursor:pointer;">Refresh feeds</button>\n',
        '          <button type="button" sc-camel-on-click="{{ refreshFeeds }}" style="height:34px;padding:0 16px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.84rem;cursor:pointer;">{{ refreshFeedsLabel }}</button>\n',
    ),
    (
        "vals: wire Refresh feeds to the real refresh orchestration",
        "refreshFeeds: () => this._refreshFeeds(),",  # stable marker
        "      feedUpdated: this.state.feedUpdated,\n"
        '      refreshFeeds: () => this.setState({ feedUpdated: "just now" }),\n',
        "      feedUpdated: this.state.feedUpdated,\n"
        '      feedRefreshStatus: this.state.feedRefreshRunning ? "Refreshing sources…" : "Updated " + this.state.feedUpdated,\n'
        '      refreshFeedsLabel: this.state.feedRefreshRunning ? "Refreshing…" : "Refresh feeds",\n'
        "      refreshFeeds: () => this._refreshFeeds(),\n",
    ),
    (
        "feeds: name partial failures in the refresh status",
        "    const refreshTargets = [",  # stable marker
        "    const requests = [\n"
        '      refreshOne("/maradmins/refresh"),\n'
        '      refreshOne("/message-watch/navadmins/refresh"),\n'
        '      refreshOne("/message-watch/alnavs/refresh"),\n'
        '      refreshOne("/message-watch/dod/refresh"),\n'
        "    ];\n"
        "    (this.state.feeds || []).filter((feed) => feed.isReal && feed.enabled !== false).forEach((feed) => {\n"
        '      requests.push(refreshOne("/custom-watch-feeds/" + encodeURIComponent(feed.id) + "/refresh"));\n'
        "    });\n"
        "    const results = await Promise.allSettled(requests);\n"
        '    const failures = results.filter((result) => result.status === "rejected").length;\n'
        "    await Promise.all([this._loadRealWorkspace(), this._loadRealFeeds()]);\n"
        '    const failureNote = failures ? " · " + failures + " source" + (failures === 1 ? "" : "s") + " failed" : "";\n',
        "    const refreshTargets = [\n"
        '      { label: "MARADMIN", url: "/maradmins/refresh" },\n'
        '      { label: "NAVADMIN", url: "/message-watch/navadmins/refresh" },\n'
        '      { label: "ALNAV", url: "/message-watch/alnavs/refresh" },\n'
        '      { label: "DoD", url: "/message-watch/dod/refresh" },\n'
        "    ];\n"
        "    (this.state.feeds || []).filter((feed) => feed.isReal && feed.enabled !== false).forEach((feed) => {\n"
        '      refreshTargets.push({ label: feed.name, url: "/custom-watch-feeds/" + encodeURIComponent(feed.id) + "/refresh" });\n'
        "    });\n"
        "    const results = await Promise.allSettled(refreshTargets.map((target) => refreshOne(target.url)));\n"
        '    const failedLabels = results.map((result, index) => result.status === "rejected" ? refreshTargets[index].label : null).filter(Boolean);\n'
        "    await Promise.all([this._loadRealWorkspace(), this._loadRealFeeds()]);\n"
        '    const failureNote = failedLabels.length ? " · " + failedLabels.join(", ") + " failed" : "";\n',
    ),
    # ------------------------------------------------------------------
    # Watch integrity (2026-07-14): real source-update candidates, RSS
    # publication dates, independent row refresh/open-source actions, and
    # real template paths from the dashboard payload.
    # ------------------------------------------------------------------
    (
        "watch: initialize independent row and payload state",
        '    feedUpdated: "2 min ago",\n',
        '    feedUpdated: "2 min ago",\n'
        "    feedRefreshRunning: false,\n"
        "    feedRowStatus: {},\n"
        "    customFeedItemsById: {},\n"
        "    realSourceUpdates: [],\n",
    ),
    (
        "workspace: retain dates, source updates, custom previews, and template paths",
        "      // Ticker items and personal documents ride along on the same payload.\n"
        '      const mapTicker = (items) => (items || []).map((t) => ({ id: t.summary || "", title: t.title, url: t.source_url || "" }));\n'
        "      const personalItems = (data.document_details || []).map((doc) => ({\n"
        "        name: doc.filename,\n"
        '        meta: doc.document_type || "file",\n'
        '        path: "local_context/files/" + doc.context_id + "-" + doc.filename,\n'
        "      }));\n"
        "      this.setState((s) => ({\n"
        "        actions,\n"
        "        historySpotlight,\n"
        "        historyIsToday: !!data.history_is_today,\n"
        "        realMaradmins: mapTicker(data.maradmin_ticker),\n"
        "        realNavadmins: mapTicker(data.navadmin_ticker),\n"
        '        benchCards: s.benchCards.map((c) => (c.title !== "Personal files" ? c : { ...c, items: personalItems })),\n',
        "      // Ticker items and personal documents ride along on the same payload.\n"
        '      const mapTicker = (items) => (items || []).map((t) => ({ id: t.summary || "", title: t.title, url: t.source_url || "", publishedAt: t.published_at || "" }));\n'
        "      const personalItems = (data.document_details || []).map((doc) => ({\n"
        "        name: doc.filename,\n"
        '        meta: doc.document_type || "file",\n'
        '        path: "local_context/files/" + doc.context_id + "-" + doc.filename,\n'
        "      }));\n"
        "      const templateItems = (data.template_library || []).filter((item) => item.source_path).map((item) => ({\n"
        "        name: item.template_name,\n"
        '        meta: item.template_source === "system" ? "system" : "saved",\n'
        "        path: item.source_path,\n"
        "      }));\n"
        "      const customFeedItemsById = {};\n"
        "      (data.custom_watch_feeds || []).forEach((feed) => { customFeedItemsById[feed.feed_id] = mapTicker(feed.preview_items); });\n"
        "      this.setState((s) => ({\n"
        "        actions,\n"
        "        historySpotlight,\n"
        "        historyIsToday: !!data.history_is_today,\n"
        "        realMaradmins: mapTicker(data.maradmin_ticker),\n"
        "        realNavadmins: mapTicker(data.navadmin_ticker),\n"
        "        realSourceUpdates: data.documentation_updates || [],\n"
        "        customFeedItemsById,\n"
        '        benchCards: s.benchCards.map((c) => c.title === "Personal files" ? { ...c, items: personalItems } : (c.title === "Template library" ? { ...c, items: templateItems } : c)),\n',
    ),
    (
        "feeds: add independent refresh and open-source action",
        "  async _runFeedAction(id) {",
        "  async _refreshFeeds() {\n",
        "  async _runFeedAction(id) {\n"
        "    const feed = (this.state.feeds || []).find((item) => item.id === id);\n"
        '    if (!feed || feed.type === "manual") return;\n'
        '    if (feed.staticItems === "gazette" || (!feed.isReal && feed.type === "url")) {\n'
        '      if (feed.url) window.open(feed.url, "_blank", "noopener");\n'
        "      return;\n"
        "    }\n"
        '    let url = "";\n'
        '    if (feed.staticItems === "maradmin") url = "/maradmins/refresh";\n'
        '    else if (feed.staticItems === "navadmin") url = "/message-watch/navadmins/refresh";\n'
        '    else if (feed.isReal) url = "/custom-watch-feeds/" + encodeURIComponent(feed.id) + "/refresh";\n'
        "    if (!url) return;\n"
        '    this.setState((s) => ({ feedRowStatus: { ...(s.feedRowStatus || {}), [id]: "Refreshing…" } }));\n'
        "    try {\n"
        '      const res = await fetch(url, { method: "POST", headers: this._apiHeaders() });\n'
        "      let payload = null;\n"
        "      try { payload = await res.json(); } catch (err) {}\n"
        "      const warnings = payload && Array.isArray(payload.warnings) ? payload.warnings : [];\n"
        '      if (!res.ok || warnings.length) throw new Error("refresh failed");\n'
        "      await Promise.all([this._loadRealWorkspace(), this._loadRealFeeds()]);\n"
        '      this.setState((s) => ({ feedRowStatus: { ...(s.feedRowStatus || {}), [id]: "Updated" } }));\n'
        "    } catch (err) {\n"
        '      this.setState((s) => ({ feedRowStatus: { ...(s.feedRowStatus || {}), [id]: "Failed" } }));\n'
        "    }\n"
        "  }\n\n"
        "  async _refreshFeeds() {\n",
    ),
    (
        "projects: hide explicitly demo folders outside demo mode",
        "  async _loadRealProjects(showDemo) {",
        "  async _loadRealProjects() {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        "      this._realProjectNames = await res.json();\n"
        "      // The Project files bench card starts empty; fill it with the real\n"
        "      // folders under projects/ so no phantom demo folders are shown.\n"
        '      const items = (this._realProjectNames || []).map((n) => ({ name: n, meta: "project folder", path: "projects/" + n + "/" }));\n'
        '      this.setState((s) => ({ benchCards: s.benchCards.map((c) => (c.title !== "Project files" ? c : { ...c, items })) }));\n'
        "    } catch (err) {\n"
        "      this._realProjectNames = [];\n"
        "    }\n"
        "  }\n",
        "  async _loadRealProjects(showDemo) {\n"
        "    try {\n"
        '      const res = await fetch("/user-docs/projects", { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("projects fetch failed: " + res.status);\n'
        "      const descriptors = await res.json();\n"
        '      const includeDemo = typeof showDemo === "boolean" ? showDemo : !!this.state.demoMode;\n'
        "      const visible = (descriptors || []).filter((project) => includeDemo || !project.is_demo);\n"
        "      this._realProjectNames = visible.map((project) => project.name);\n"
        '      const items = visible.map((project) => ({ name: project.name, meta: "project folder", path: "projects/" + project.name + "/" }));\n'
        '      this.setState((s) => ({ benchCards: s.benchCards.map((c) => (c.title !== "Project files" ? c : { ...c, items })) }));\n'
        "    } catch (err) {\n"
        "      this._realProjectNames = [];\n"
        "    }\n"
        "  }\n",
    ),
    (
        "demo mode: clear personal and project demo files immediately",
        'c.title === "Personal files" || c.title === "Project files"',
        '      this.setState({ profileRank: "", profileLastName: "", profileBillet: "", profileUnit: "" });\n'
        "      this._loadRealHandoff();\n"
        "    }\n"
        "    this._loadRealWorkspace();\n",
        "      this.setState((s) => ({\n"
        '        profileRank: "", profileLastName: "", profileBillet: "", profileUnit: "",\n'
        "        realSourceUpdates: [],\n"
        '        benchCards: s.benchCards.map((c) => (c.title === "Personal files" || c.title === "Project files") ? { ...c, items: [] } : c),\n'
        "      }));\n"
        "      this._loadRealHandoff();\n"
        "    }\n"
        "    this._loadRealWorkspace();\n"
        "    this._loadRealProjects(on);\n",
    ),
    (
        "watch: map publication dates and per-row actions",
        "    const formatFeedDate = (value) => {",
        '    const tickerFeedItem = (m) => ({ text: (m.id ? m.id + " — " : "") + m.title, url: m.url });\n',
        "    const formatFeedDate = (value) => {\n"
        '      if (!value) return "";\n'
        "      const parsed = new Date(value);\n"
        '      if (Number.isNaN(parsed.getTime())) return "";\n'
        '      return parsed.toLocaleDateString("en-US", { day: "2-digit", month: "short", year: "numeric" }).toUpperCase();\n'
        "    };\n"
        '    const tickerFeedItem = (m) => ({ text: (m.id ? m.id + " — " : "") + m.title, url: m.url, dateLabel: formatFeedDate(m.publishedAt) });\n',
    ),
    (
        "watch: use custom RSS previews and expose row action state",
        "      const rawItems = f.staticItems\n"
        "        ? staticFeedItems[f.staticItems]\n"
        '        : (f.url ? [{ text: `Source: ${f.url}`, url: f.url }, { text: "No updates pulled yet — this feed populates once it\'s next checked", url: "" }] : [{ text: "No updates yet — recently added", url: "" }]);\n'
        "      const items = rawItems.map((it) => ({ text: it.text, url: it.url, noUrl: !it.url }));\n"
        "      return {\n",
        "      const previewItems = f.isReal ? (this.state.customFeedItemsById[f.id] || []).map(tickerFeedItem) : [];\n"
        "      const rawItems = f.staticItems\n"
        "        ? staticFeedItems[f.staticItems]\n"
        '        : (previewItems.length ? previewItems : (f.url ? [{ text: `Source: ${f.url}`, url: f.url }, { text: "No updates pulled yet — this feed populates once it\'s next checked", url: "" }] : [{ text: "No updates yet — recently added", url: "" }]));\n'
        '      const items = rawItems.map((it) => ({ text: it.text, url: it.url, noUrl: !it.url, dateLabel: it.dateLabel || "", hasDate: !!it.dateLabel }));\n'
        '      const rowStatus = (this.state.feedRowStatus || {})[f.id] || "";\n'
        '      const isManual = f.type === "manual";\n'
        '      const isOpenSource = f.staticItems === "gazette" || (!f.isReal && f.type === "url");\n'
        '      const actionLabel = isManual ? "Manual" : (isOpenSource ? "Open source" : (rowStatus === "Refreshing…" ? rowStatus : "Refresh"));\n'
        "      return {\n"
        '        actionLabel, actionDisabled: isManual || rowStatus === "Refreshing…",\n'
        '        actionStatus: rowStatus === "Updated" || rowStatus === "Failed" ? rowStatus : "",\n'
        '        hasActionStatus: rowStatus === "Updated" || rowStatus === "Failed",\n'
        "        onAction: () => this._runFeedAction(f.id),\n",
    ),
    (
        "watch: render per-feed action control",
        "{{ f.actionLabel }}",
        '                <span style="{{ f.trustStyle }}">{{ f.trust }}</span>\n'
        '                <button type="button" sc-camel-on-click="{{ f.onToggleEdit }}" style="flex:0 0 auto;height:26px;padding:0 10px;border:1px solid #313844;border-radius:5px;background:#1a2027;color:#aab4bf;font:inherit;font-size:0.74rem;font-weight:600;cursor:pointer;">{{ f.editToggleLabel }}</button>\n',
        '                <span style="{{ f.trustStyle }}">{{ f.trust }}</span>\n'
        '                <sc-if value="{{ f.hasActionStatus }}" hint-placeholder-val="{{ false }}"><span style="font-size:0.72rem;color:#8a94a0;">{{ f.actionStatus }}</span></sc-if>\n'
        '                <button type="button" disabled="{{ f.actionDisabled }}" sc-camel-on-click="{{ f.onAction }}" style="flex:0 0 auto;height:26px;padding:0 10px;border:1px solid #313844;border-radius:5px;background:#1a2027;color:#c7cfd8;font:inherit;font-size:0.74rem;font-weight:600;cursor:pointer;">{{ f.actionLabel }}</button>\n'
        '                <button type="button" sc-camel-on-click="{{ f.onToggleEdit }}" style="flex:0 0 auto;height:26px;padding:0 10px;border:1px solid #313844;border-radius:5px;background:#1a2027;color:#aab4bf;font:inherit;font-size:0.74rem;font-weight:600;cursor:pointer;">{{ f.editToggleLabel }}</button>\n',
    ),
    (
        "watch: render feed item dates when supplied",
        "{{ it.dateLabel }}",
        '                      <a href="{{ it.url }}" target="_blank" rel="noopener" style="display:block;padding:9px 11px;border:1px solid #1a2027;border-radius:5px;background:#12161b;font-size:0.82rem;color:#c7cfd8;line-height:1.4;">{{ it.text }}</a>\n'
        "                    </sc-if>\n"
        '                    <sc-if value="{{ it.noUrl }}" hint-placeholder-val="{{ true }}">\n'
        '                      <div style="padding:9px 11px;border:1px solid #1a2027;border-radius:5px;background:#12161b;font-size:0.82rem;color:#c7cfd8;line-height:1.4;">{{ it.text }}</div>\n',
        '                      <a href="{{ it.url }}" target="_blank" rel="noopener" style="display:block;padding:9px 11px;border:1px solid #1a2027;border-radius:5px;background:#12161b;font-size:0.82rem;color:#c7cfd8;line-height:1.4;"><span>{{ it.text }}</span><sc-if value="{{ it.hasDate }}" hint-placeholder-val="{{ false }}"><span style="display:block;margin-top:4px;color:#8a94a0;font-size:0.7rem;">{{ it.dateLabel }}</span></sc-if></a>\n'
        "                    </sc-if>\n"
        '                    <sc-if value="{{ it.noUrl }}" hint-placeholder-val="{{ true }}">\n'
        '                      <div style="padding:9px 11px;border:1px solid #1a2027;border-radius:5px;background:#12161b;font-size:0.82rem;color:#c7cfd8;line-height:1.4;"><span>{{ it.text }}</span><sc-if value="{{ it.hasDate }}" hint-placeholder-val="{{ false }}"><span style="display:block;margin-top:4px;color:#8a94a0;font-size:0.7rem;">{{ it.dateLabel }}</span></sc-if></div>\n',
    ),
    (
        "source updates: replace hardcoded demo entries with backend candidates",
        "    const srcUpdates = (this.state.realSourceUpdates || []).map((item) => {",
        "    const srcUpdates = [\n"
        '      { title: "MCO 1001R.1 possible change", detail: "AT budget language differs from your saved reference note — verify before citing.", sourceLabel: "Check MCO 1001R.1 on MCPEL", sourceUrl: "https://www.marines.mil/News/Publications/MCPEL/Search/1001R.1/" },\n'
        '      { title: "FitRep reporting occasions", detail: "MARADMIN 305/26 may supersede your current worksheet template.", sourceLabel: "Check MARADMIN 305/26", sourceUrl: "https://www.marines.mil/News/Messages/MARADMINS/" },\n'
        "    ];\n",
        "    const srcUpdates = (this.state.realSourceUpdates || []).map((item) => {\n"
        "      const published = formatFeedDate(item.source_published_at);\n"
        "      const detected = formatFeedDate(item.detected_at);\n"
        "      const signals = (item.change_signals || []).concat(item.matched_terms || []);\n"
        "      return {\n"
        '        title: item.tracked_title + " possible change",\n'
        '        detail: signals.join(" · ") || "A possible source change needs human review.",\n'
        '        dateLabel: published ? "Published " + published : (detected ? "Detected " + detected : ""),\n'
        "        hasDate: !!(published || detected),\n"
        '        sourceLabel: item.source_record_title || "Open source",\n'
        '        sourceUrl: item.source_url || "",\n'
        "        hasSource: !!item.source_url,\n"
        "      };\n"
        "    });\n"
        "    const srcUpdatesEmpty = srcUpdates.length === 0;\n",
    ),
    (
        "source updates: render dates, optional source links, and empty state",
        "{{ srcUpdatesEmpty }}",
        '          <div style="display:grid;gap:10px;">\n'
        '            <sc-for list="{{ srcUpdates }}" as="u" hint-placeholder-count="2">\n'
        '              <div style="padding:12px 14px;border:1px solid #313844;border-radius:6px;background:#0d1014;">\n'
        '                <div style="font-size:0.88rem;font-weight:600;">{{ u.title }}</div>\n'
        '                <div style="margin-top:4px;font-size:0.8rem;color:#aab4bf;line-height:1.45;">{{ u.detail }}</div>\n'
        '                <a href="{{ u.sourceUrl }}" target="_blank" rel="noopener" style="margin-top:8px;display:inline-flex;align-items:center;gap:6px;font-size:0.78rem;font-weight:600;color:#7db2e0;">{{ u.sourceLabel }} <span style="opacity:0.7;">↗</span></a>\n'
        "              </div>\n"
        "            </sc-for>\n"
        "          </div>\n",
        '          <div style="display:grid;gap:10px;">\n'
        '            <sc-if value="{{ srcUpdatesEmpty }}" hint-placeholder-val="{{ false }}"><div style="padding:12px 14px;border:1px dashed #313844;border-radius:6px;color:#8a94a0;font-size:0.82rem;">No source changes are awaiting review.</div></sc-if>\n'
        '            <sc-for list="{{ srcUpdates }}" as="u" hint-placeholder-count="2">\n'
        '              <div style="padding:12px 14px;border:1px solid #313844;border-radius:6px;background:#0d1014;">\n'
        '                <div style="font-size:0.88rem;font-weight:600;">{{ u.title }}</div>\n'
        '                <sc-if value="{{ u.hasDate }}" hint-placeholder-val="{{ false }}"><div style="margin-top:3px;font-size:0.7rem;color:#8a94a0;">{{ u.dateLabel }}</div></sc-if>\n'
        '                <div style="margin-top:4px;font-size:0.8rem;color:#aab4bf;line-height:1.45;">{{ u.detail }}</div>\n'
        '                <sc-if value="{{ u.hasSource }}" hint-placeholder-val="{{ false }}"><a href="{{ u.sourceUrl }}" target="_blank" rel="noopener" style="margin-top:8px;display:inline-flex;align-items:center;gap:6px;font-size:0.78rem;font-weight:600;color:#7db2e0;">{{ u.sourceLabel }} <span style="opacity:0.7;">↗</span></a></sc-if>\n'
        "              </div>\n"
        "            </sc-for>\n"
        "          </div>\n",
    ),
    (
        "vals: expose source update empty state",
        "      actNow, maradmins, navadmins, feeds, actions, srcUpdates,\n",
        "      actNow, maradmins, navadmins, feeds, actions, srcUpdates, srcUpdatesEmpty,\n",
    ),
    # ------------------------------------------------------------------
    # Navigation cleanup (2026-07-14): make the existing FitRep tracker a
    # first-class lane and identify every AI agent by its stable repo ID.
    # ------------------------------------------------------------------
    (
        "navigation: add top-level FitReps tab between Workspace and AI",
        '      tab("fitreps", "FitReps"),\n',
        '      tab("workspace", "Workspace"),\n      tab("ai", "AI"),\n',
        '      tab("workspace", "Workspace"),\n      tab("fitreps", "FitReps"),\n      tab("ai", "AI"),\n',
    ),
    (
        "navigation: point FitRep quick link to the new lane",
        '{ kind: "internal", name: "FitReps — Tracker", lane: "fitreps" },',
        '{ kind: "internal", name: "Workspace — FitRep Tracker", lane: "workspace" },',
        '{ kind: "internal", name: "FitReps — Tracker", lane: "fitreps" },',
    ),
    (
        "workspace: share the container with the new FitReps lane",
        "{{ isWorkspaceOrFitreps }}",
        '    <sc-if value="{{ isWorkspace }}" hint-placeholder-val="{{ false }}">\n'
        '    <div style="display:grid;gap:20px;">\n'
        '      <div style="border:1px dashed #3a4450;border-radius:8px;background:#12161b;padding:16px 18px;">\n',
        '    <sc-if value="{{ isWorkspaceOrFitreps }}" hint-placeholder-val="{{ false }}">\n'
        '    <div style="display:grid;gap:20px;">\n'
        '      <sc-if value="{{ isWorkspace }}" hint-placeholder-val="{{ false }}">\n'
        '      <div style="border:1px dashed #3a4450;border-radius:8px;background:#12161b;padding:16px 18px;">\n',
    ),
    (
        "fitreps: close Workspace content and open dedicated page",
        '<h2 style="margin:0;font-size:1.16rem;font-weight:700;">FitReps</h2>',
        '        <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px;">\n'
        '          <h3 style="margin:0 0 4px;font-size:1.02rem;font-weight:700;">FitRep Tracker</h3>\n',
        "        </sc-if>\n"
        '        <sc-if value="{{ isFitreps }}" hint-placeholder-val="{{ false }}">\n'
        '        <div style="border:1px dashed #3a4450;border-radius:8px;background:#12161b;padding:16px 18px;">\n'
        '          <h2 style="margin:0;font-size:1.16rem;font-weight:700;">FitReps</h2>\n'
        '          <p style="margin:6px 0 0;color:#aab4bf;font-size:0.88rem;line-height:1.5;max-width:70ch;">Keep report continuity, trait observations, and counseling links together. This is a local working record; verify the current form and MCO 1610.7 before submitting anything official.</p>\n'
        "        </div>\n"
        '        <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px;">\n'
        '          <h3 style="margin:0 0 4px;font-size:1.02rem;font-weight:700;">FitRep Tracker</h3>\n',
    ),
    (
        "fitreps: close dedicated page before the shared container",
        "<!-- dedicated FitReps lane ends -->",
        "        </section>\n"
        "    </div>\n"
        "    </sc-if>\n\n"
        "    <!-- ==================== AI LANE ==================== -->\n",
        "        </section>\n"
        "        </sc-if><!-- dedicated FitReps lane ends -->\n"
        "    </div>\n"
        "    </sc-if>\n\n"
        "    <!-- ==================== AI LANE ==================== -->\n",
    ),
    (
        "vals: expose dedicated FitReps lane flags",
        '      isFitreps: lane === "fitreps",\n',
        '      isWorkspace: lane === "workspace",\n      isLinks: lane === "links",\n',
        '      isWorkspace: lane === "workspace",\n'
        '      isFitreps: lane === "fitreps",\n'
        '      isWorkspaceOrFitreps: lane === "workspace" || lane === "fitreps",\n'
        '      isLinks: lane === "links",\n',
    ),
    (
        "AI agents: display stable Agent ID on every card",
        '<strong style="color:#aab4bf;">Agent ID:</strong> {{ a.id }}',
        '                  <p style="margin:8px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ a.description }}</p>\n',
        '                  <p style="margin:6px 0 0;color:#8a94a0;font-size:0.76rem;font-family:\'IBM Plex Mono\',monospace;"><strong style="color:#aab4bf;">Agent ID:</strong> {{ a.id }}</p>\n'
        '                  <p style="margin:8px 0 0;color:#c7cfd8;font-size:0.84rem;line-height:1.5;">{{ a.description }}</p>\n',
    ),
    # ------------------------------------------------------------------
    # Initial counseling (2026-07-14): a persistent staff-product workflow
    # with an optional, explicit FitRep relationship in Generation fields.
    # ------------------------------------------------------------------
    (
        "workflows: add the Initial Counseling scaffold",
        "    counseling: {\n",
        "    awards: {\n",
        "    counseling: {\n"
        "      fields: [\n"
        '        { key: "marineName", label: "Marine", placeholder: "Last name, first name / initials…", rows: 1 },\n'
        '        { key: "rank", label: "Rank", placeholder: "Rank…", rows: 1 },\n'
        '        { key: "unit", label: "Unit / section", placeholder: "Unit and staff section…", rows: 1 },\n'
        '        { key: "billet", label: "Billet / job title", placeholder: "The Marine\'s assigned billet…", rows: 1 },\n'
        '        { key: "purpose", label: "Purpose of counseling", placeholder: "Why this initial counseling is being conducted and what good looks like…", rows: 2 },\n'
        '        { key: "duties", label: "Duties and responsibilities", placeholder: "Core job description, recurring tasks, supported relationships, and decision authority…", rows: 5 },\n'
        '        { key: "performanceExpectations", label: "Performance expectations", placeholder: "Expected results, quality, timeliness, initiative, judgment, and follow-through…", rows: 4 },\n'
        '        { key: "standards", label: "Professional standards", placeholder: "Leadership, accountability, communication, conduct, readiness, and team standards…", rows: 4 },\n'
        '        { key: "priorities", label: "Current priorities", placeholder: "Near-term priorities and where the Marine should focus first…", rows: 3 },\n'
        '        { key: "communication", label: "Communication and reporting", placeholder: "Battle rhythm, update format, when to elevate issues, and preferred communication…", rows: 3 },\n'
        '        { key: "developmentGoals", label: "Development goals", placeholder: "Skills, PME, leadership opportunities, and measurable growth goals…", rows: 3 },\n'
        '        { key: "leaderCommitments", label: "Leader commitments", placeholder: "Coaching, access, resources, advocacy, and feedback the leader will provide…", rows: 3 },\n'
        '        { key: "followUp", label: "Follow-up plan", placeholder: "Next counseling date, interim check-ins, and how progress will be reviewed…", rows: 2 },\n'
        '        { key: "acknowledgment", label: "Marine comments / acknowledgment", placeholder: "Questions, concerns, agreed adjustments, and acknowledgment notes…", rows: 3 },\n'
        "      ],\n"
        "      doctrine: [\n"
        '        { title: "MCO 1610.7B Performance Evaluation System — verify current version", url: "https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1513503/mco-16107b/" },\n'
        "      ],\n"
        "      prompts: [\n"
        '        { title: "Review this counseling draft", text: "Review this initial counseling for clear duties, observable expectations, fair standards, two-way communication, and useful follow-up. Flag vague or unsupported language. DRAFT — verify all references against current official sources before acting.", agentIds: ["leadership-advisor", "writing-briefing-coach"] },\n'
        "      ],\n"
        "      agents: [\n"
        '        { id: "leadership-advisor", name: "Leadership Advisor", description: "Helps shape clear, fair leader expectations and development goals." },\n'
        '        { id: "writing-briefing-coach", name: "Writing / Briefing Coach", description: "Tightens language so expectations are specific and understandable." },\n'
        "      ],\n"
        "    },\n"
        "    awards: {\n",
    ),
    (
        "workflows: add Initial Counseling tile under staff products",
        '{ kind: "Staff product", title: "Initial Counseling",',
        '      { kind: "Staff product", title: "AAR", desc: "After-action scaffold with sustain / improve framing and follow-up owners.", output: "Markdown + .docx", templateType: "aar" },\n',
        '      { kind: "Staff product", title: "AAR", desc: "After-action scaffold with sustain / improve framing and follow-up owners.", output: "Markdown + .docx", templateType: "aar" },\n'
        '      { kind: "Staff product", title: "Initial Counseling", desc: "Job description, leader expectations, development goals, and follow-up for a Marine you supervise — optionally linked to a FitRep record.", output: "Counseling draft", templateType: "counseling" },\n',
    ),
    (
        "counseling: seed linked Marine fields only after explicit FitRep choice",
        '      if (w.templateType === "counseling" && w.linkedFitrep) {',
        '      if (w.templateType === "awards") data.awardType = Component.AWARD_TYPES[0].value;\n',
        '      if (w.templateType === "awards") data.awardType = Component.AWARD_TYPES[0].value;\n'
        '      if (w.templateType === "counseling" && w.linkedFitrep) {\n'
        "        data.linkedFitrepId = String(w.linkedFitrep.id);\n"
        '        data.marineName = w.linkedFitrep.name || "";\n'
        '        data.rank = w.linkedFitrep.rank || "";\n'
        '        data.unit = w.linkedFitrep.unit || "";\n'
        "      }\n",
    ),
    (
        "counseling: add FitRep link and reciprocal navigation helpers",
        "  linkCounselingToFitrep(docId) {",
        "  openWorkflowDoc(id) {\n",
        "  linkCounselingToFitrep(docId) {\n"
        "    return (e) => {\n"
        '      const linkedFitrepId = e.target.value || "";\n'
        "      const fitrep = this.state.fitreps.find((item) => String(item.id) === linkedFitrepId);\n"
        "      this.setState((s) => ({ workflowDocs: s.workflowDocs.map((doc) => {\n"
        "        if (doc.id !== docId) return doc;\n"
        "        const data = { ...doc.data, linkedFitrepId };\n"
        '        if (fitrep) { data.marineName = fitrep.name || ""; data.rank = fitrep.rank || ""; data.unit = fitrep.unit || ""; }\n'
        "        return { ...doc, data };\n"
        "      }) }));\n"
        "      this._scheduleGenerationSave(docId);\n"
        "    };\n"
        "  }\n"
        "  openLinkedFitrep(fitrepId) {\n"
        "    return () => {\n"
        "      const fitrep = this.state.fitreps.find((item) => String(item.id) === String(fitrepId));\n"
        '      if (!fitrep) { window.alert("That linked FitRep record no longer exists. You can leave this counseling unlinked or choose another Marine."); return; }\n'
        '      this.setState({ lane: "fitreps", activeFitrepId: fitrep.id, workflowEditorId: null });\n'
        "    };\n"
        "  }\n"
        "  openCounselingFromFitrep(docId) {\n"
        '    return () => this.setState({ lane: "bench", workflowEditorId: docId });\n'
        "  }\n"
        "  startCounselingForFitrep() {\n"
        "    const linkedFitrep = this.state.fitreps.find((item) => item.id === this.state.activeFitrepId);\n"
        "    if (!linkedFitrep) return () => {};\n"
        '    return this.createWorkflowDoc({ kind: "Staff product", title: "Initial Counseling", templateType: "counseling", linkedFitrep });\n'
        "  }\n"
        "  openWorkflowDoc(id) {\n",
    ),
    (
        "counseling: compute editor FitRep options and safe missing-link state",
        '    const isCounselingDoc = !!activeWorkflowDoc && activeWorkflowDoc.templateType === "counseling";',
        '    const isAwardsDoc = !!activeWorkflowDoc && activeWorkflowDoc.templateType === "awards";\n',
        '    const isAwardsDoc = !!activeWorkflowDoc && activeWorkflowDoc.templateType === "awards";\n'
        '    const isCounselingDoc = !!activeWorkflowDoc && activeWorkflowDoc.templateType === "counseling";\n'
        '    const counselingLinkedFitrepId = isCounselingDoc ? (activeWorkflowDoc.data.linkedFitrepId || "") : "";\n'
        '    const counselingFitrepOptions = [{ value: "", label: "No FitRep link" }].concat(this.state.fitreps.map((fitrep) => ({ value: String(fitrep.id), label: [fitrep.rank, fitrep.name, fitrep.unit].filter(Boolean).join(" · ") })));\n'
        "    const counselingLinkedFitrep = counselingLinkedFitrepId ? this.state.fitreps.find((fitrep) => String(fitrep.id) === String(counselingLinkedFitrepId)) : null;\n"
        "    const counselingLinkMissing = !!counselingLinkedFitrepId && !counselingLinkedFitrep;\n"
        "    const onCounselingFitrepChange = activeWorkflowDoc ? this.linkCounselingToFitrep(activeWorkflowDoc.id) : () => {};\n"
        "    const openCounselingFitrep = counselingLinkedFitrep ? this.openLinkedFitrep(counselingLinkedFitrep.id) : () => {};\n",
    ),
    (
        "counseling: expose editor link bindings",
        "      isCounselingDoc, counselingFitrepOptions, counselingLinkedFitrepId,",
        "      isAwardsDoc, isNotAwardsDoc: !isAwardsDoc,\n",
        "      isAwardsDoc, isNotAwardsDoc: !isAwardsDoc,\n"
        "      isCounselingDoc, counselingFitrepOptions, counselingLinkedFitrepId,\n"
        "      counselingHasLinkedFitrep: !!counselingLinkedFitrep, counselingLinkMissing,\n"
        "      onCounselingFitrepChange, openCounselingFitrep,\n",
    ),
    (
        "counseling: render optional FitRep link in the workflow editor",
        "{{ counselingFitrepOptions }}",
        '        <sc-if value="{{ isAwardsDoc }}" hint-placeholder-val="{{ false }}">\n',
        '        <sc-if value="{{ isCounselingDoc }}" hint-placeholder-val="{{ false }}">\n'
        '          <div style="margin-bottom:16px;padding:12px;border:1px solid #2a3c4a;border-radius:6px;background:#0f1620;display:grid;gap:8px;">\n'
        '            <label style="display:grid;gap:6px;font-size:0.82rem;font-weight:600;color:#c7cfd8;"><span>Optional FitRep link</span><sc-raw-select value="{{ counselingLinkedFitrepId }}" sc-camel-on-change="{{ onCounselingFitrepChange }}" style="height:38px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;"><sc-for list="{{ counselingFitrepOptions }}" as="fo" hint-placeholder-count="3"><option value="{{ fo.value }}">{{ fo.label }}</option></sc-for></sc-raw-select></label>\n'
        '            <p style="margin:0;color:#8a94a0;font-size:0.78rem;line-height:1.45;">Linking is optional. Choosing a Marine pre-fills only name, rank, and unit; the counseling remains a separate draft.</p>\n'
        '            <sc-if value="{{ counselingHasLinkedFitrep }}" hint-placeholder-val="{{ false }}"><button type="button" sc-camel-on-click="{{ openCounselingFitrep }}" style="justify-self:start;height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">Open linked FitRep</button></sc-if>\n'
        '            <sc-if value="{{ counselingLinkMissing }}" hint-placeholder-val="{{ false }}"><p style="margin:0;color:#d8a0a5;font-size:0.78rem;line-height:1.45;">The linked FitRep was removed. This counseling is still safe; choose another Marine or select No FitRep link.</p></sc-if>\n'
        "          </div>\n"
        "        </sc-if>\n\n"
        '        <sc-if value="{{ isAwardsDoc }}" hint-placeholder-val="{{ false }}">\n',
    ),
    (
        "counseling: show linked drafts on the active FitRep",
        "    const linkedCounselings = active ? this.state.workflowDocs.filter((doc) =>",
        "    return {\n      fitrepList,\n",
        '    const linkedCounselings = active ? this.state.workflowDocs.filter((doc) => doc.templateType === "counseling" && String(doc.data.linkedFitrepId || "") === String(active.id)).map((doc) => ({ id: doc.id, title: doc.title, onOpen: this.openCounselingFromFitrep(doc.id) })) : [];\n\n'
        "    return {\n"
        "      fitrepList,\n"
        "      linkedCounselings, linkedCounselingsEmpty: linkedCounselings.length === 0,\n"
        "      startInitialCounseling: this.startCounselingForFitrep(),\n",
    ),
    (
        "counseling: render reciprocal controls in FitReps",
        "{{ linkedCounselings }}",
        '              <label style="display:grid;gap:6px;font-size:0.82rem;font-weight:600;color:#c7cfd8;"><span>Additional notes</span><textarea rows="2" value="{{ frNotes }}" sc-camel-on-change="{{ onFrNotes }}" placeholder="Private notes — not part of the report itself…" style="border:1px solid #313844;border-radius:6px;padding:10px 12px;background:#12161b;color:#eef2f6;font:inherit;resize:vertical;"></textarea></label>\n\n'
        '              <div style="display:flex;gap:10px;flex-wrap:wrap;">\n',
        '              <label style="display:grid;gap:6px;font-size:0.82rem;font-weight:600;color:#c7cfd8;"><span>Additional notes</span><textarea rows="2" value="{{ frNotes }}" sc-camel-on-change="{{ onFrNotes }}" placeholder="Private notes — not part of the report itself…" style="border:1px solid #313844;border-radius:6px;padding:10px 12px;background:#12161b;color:#eef2f6;font:inherit;resize:vertical;"></textarea></label>\n'
        '              <div style="padding:10px 12px;border:1px solid #2a3c4a;border-radius:6px;background:#0f1620;display:grid;gap:8px;">\n'
        '                <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;"><span style="font-size:0.8rem;font-weight:700;color:#c7cfd8;">Initial counseling</span><button type="button" sc-camel-on-click="{{ startInitialCounseling }}" style="height:28px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.76rem;cursor:pointer;">+ Start linked counseling</button></div>\n'
        '                <sc-for list="{{ linkedCounselings }}" as="lc" hint-placeholder-count="1"><button type="button" sc-camel-on-click="{{ lc.onOpen }}" style="width:100%;text-align:left;padding:8px 10px;border:1px solid #313844;border-radius:5px;background:#12161b;color:#eef2f6;font:inherit;font-size:0.8rem;cursor:pointer;">Open {{ lc.title }}</button></sc-for>\n'
        '                <sc-if value="{{ linkedCounselingsEmpty }}" hint-placeholder-val="{{ true }}"><p style="margin:0;color:#8a94a0;font-size:0.76rem;">No counseling draft is linked to this FitRep yet.</p></sc-if>\n'
        "              </div>\n\n"
        '              <div style="display:flex;gap:10px;flex-wrap:wrap;">\n',
    ),
    (
        "counseling: label every editor draft as advisory",
        '<p style="margin:16px 0 0;padding-top:12px;border-top:1px solid #313844;color:#8a94a0;font-size:0.72rem;line-height:1.45;">DRAFT — Verify all references against current official sources before acting.</p>',
        '        <div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap;">\n',
        '        <p style="margin:16px 0 0;padding-top:12px;border-top:1px solid #313844;color:#8a94a0;font-size:0.72rem;line-height:1.45;">DRAFT — Verify all references against current official sources before acting.</p>\n'
        '        <div style="margin-top:12px;display:flex;gap:10px;flex-wrap:wrap;">\n',
    ),
    # ------------------------------------------------------------------
    # Travel / GTCC workspace (2026-07-15): user-driven trips, expense
    # ledger, receipt uploads, and monthly balance checks.
    # ------------------------------------------------------------------
    (
        "travel workspace: add persistent component state",
        "    travelCases: [],\n"
        "    activeTravelTripId: null,\n"
        '    travelLoadStatus: "",\n'
        '    travelDraftTitle: "",\n'
        '    travelDraftDestination: "",\n'
        '    travelLedgerDate: "",\n'
        '    travelLedgerDescription: "",\n'
        '    travelLedgerAmount: "",\n'
        '    travelLedgerCategory: "other",\n'
        '    gtccBalance: "",\n'
        '    gtccPayment: "",\n'
        "    gtccPaidInFull: false,\n"
        '    gtccCheckNotes: "",\n',
        "    dtsFlightBooked: false,\n    benchCards: [\n",
        "    dtsFlightBooked: false,\n"
        "    travelCases: [],\n"
        "    activeTravelTripId: null,\n"
        '    travelLoadStatus: "",\n'
        '    travelDraftTitle: "",\n'
        '    travelDraftDestination: "",\n'
        '    travelLedgerDate: "",\n'
        '    travelLedgerDescription: "",\n'
        '    travelLedgerAmount: "",\n'
        '    travelLedgerCategory: "other",\n'
        '    gtccBalance: "",\n'
        '    gtccPayment: "",\n'
        "    gtccPaidInFull: false,\n"
        '    gtccCheckNotes: "",\n'
        "    benchCards: [\n",
    ),
    (
        "travel workspace: load cases during mount",
        "    this._loadTravelCases();\n",
        "    this._loadRealHandoff();\n    this._loadRealNotes();\n",
        "    this._loadRealHandoff();\n    this._loadTravelCases();\n    this._loadRealNotes();\n",
    ),
    (
        "travel workspace: add API helpers and view bindings",
        "  async _loadTravelCases() {",
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        "  async _loadTravelCases() {\n"
        "    if (!this.userKey) this.userKey = this._resolveUserKey();\n"
        '    this.setState({ travelLoadStatus: "Loading travel…" });\n'
        "    try {\n"
        '      const res = await fetch("/travel-cases/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("travel fetch failed: " + res.status);\n'
        "      const data = await res.json();\n"
        "      const travelCases = data.records || [];\n"
        "      this.setState((s) => ({\n"
        "        travelCases,\n"
        "        activeTravelTripId: travelCases.some((item) => item.trip_id === s.activeTravelTripId)\n"
        "          ? s.activeTravelTripId : (travelCases[0] ? travelCases[0].trip_id : null),\n"
        '        travelLoadStatus: "",\n'
        "      }));\n"
        '    } catch (err) { this.setState({ travelLoadStatus: "Travel data could not be loaded." }); }\n'
        "  }\n"
        "  _replaceTravelCase(updated) {\n"
        "    this.setState((s) => ({\n"
        "      travelCases: s.travelCases.some((item) => item.trip_id === updated.trip_id)\n"
        "        ? s.travelCases.map((item) => item.trip_id === updated.trip_id ? updated : item)\n"
        "        : [updated, ...s.travelCases],\n"
        "      activeTravelTripId: updated.trip_id,\n"
        '      travelLoadStatus: "Saved locally.",\n'
        "    }));\n"
        "  }\n"
        "  _travelJson(url, body) {\n"
        '    return fetch(url, { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(body) })\n'
        "      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))\n"
        '      .then(({ ok, data }) => { if (!ok) throw new Error((data && data.detail) || "Travel save failed."); this._replaceTravelCase(data); return data; });\n'
        "  }\n"
        "  createTravelCase(e) {\n"
        "    e.preventDefault();\n"
        '    const title = (this.state.travelDraftTitle || "").trim();\n'
        "    if (!title) return;\n"
        '    this.setState({ travelLoadStatus: "Saving trip…" });\n'
        '    this._travelJson("/travel-cases/" + encodeURIComponent(this.userKey), {\n'
        '      user_key: this.userKey, title, destination: (this.state.travelDraftDestination || "").trim(),\n'
        '    }).then(() => this.setState({ travelDraftTitle: "", travelDraftDestination: "" }))\n'
        '      .catch(() => this.setState({ travelLoadStatus: "Trip could not be saved." }));\n'
        "  }\n"
        "  addTravelLedgerEntry(e) {\n"
        "    e.preventDefault();\n"
        "    const tripId = this.state.activeTravelTripId;\n"
        '    const description = (this.state.travelLedgerDescription || "").trim();\n'
        '    const amount = (this.state.travelLedgerAmount || "").trim();\n'
        "    if (!tripId || !description || !amount) return;\n"
        '    this.setState({ travelLoadStatus: "Saving expense…" });\n'
        '    this._travelJson("/travel-cases/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(tripId) + "/ledger", {\n'
        "      user_key: this.userKey, transaction_date: this.state.travelLedgerDate || new Date().toISOString().slice(0, 10),\n"
        '      description, amount, category: this.state.travelLedgerCategory || "other", payment_responsibility: "gtcc",\n'
        '    }).then(() => this.setState({ travelLedgerDescription: "", travelLedgerAmount: "" }))\n'
        '      .catch(() => this.setState({ travelLoadStatus: "Expense could not be saved." }));\n'
        "  }\n"
        "  recordGtccCheck(e) {\n"
        "    e.preventDefault();\n"
        "    const tripId = this.state.activeTravelTripId;\n"
        "    if (!tripId) return;\n"
        '    const body = { user_key: this.userKey, paid_in_full: !!this.state.gtccPaidInFull, notes: this.state.gtccCheckNotes || "" };\n'
        '    if ((this.state.gtccBalance || "").trim()) body.statement_balance = this.state.gtccBalance.trim();\n'
        '    if ((this.state.gtccPayment || "").trim()) body.payment_amount = this.state.gtccPayment.trim();\n'
        '    this.setState({ travelLoadStatus: "Recording check…" });\n'
        '    this._travelJson("/travel-cases/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(tripId) + "/gtcc-checks", body)\n'
        '      .then(() => this.setState({ gtccBalance: "", gtccPayment: "", gtccPaidInFull: false, gtccCheckNotes: "" }))\n'
        '      .catch(() => this.setState({ travelLoadStatus: "GTCC check could not be saved." }));\n'
        "  }\n"
        "  uploadTravelReceipt(e) {\n"
        "    const file = e.target.files && e.target.files[0];\n"
        "    const tripId = this.state.activeTravelTripId;\n"
        "    if (!file || !tripId) return;\n"
        '    const form = new FormData(); form.append("file", file); form.append("document_type", "travel_receipt"); form.append("tags", "travel,receipt");\n'
        '    this.setState({ travelLoadStatus: "Uploading receipt…" });\n'
        '    fetch("/context/upload", { method: "POST", headers: this._apiHeaders(), body: form })\n'
        "      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))\n"
        '      .then(({ ok, data }) => { if (!ok || !data.item) throw new Error("upload failed"); return this._travelJson("/travel-cases/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(tripId) + "/link-receipt", { user_key: this.userKey, context_id: data.item.context_id }); })\n'
        '      .catch(() => this.setState({ travelLoadStatus: "Receipt could not be linked." }));\n'
        '    e.target.value = "";\n'
        "  }\n"
        "  travelWorkspaceVals() {\n"
        "    const active = this.state.travelCases.find((item) => item.trip_id === this.state.activeTravelTripId) || null;\n"
        "    const trips = this.state.travelCases.map((item) => ({\n"
        '      id: item.trip_id, title: item.title, meta: [item.destination, item.travel_start].filter(Boolean).join(" · ") || "No dates set",\n'
        "      onClick: () => this.setState({ activeTravelTripId: item.trip_id }),\n"
        '      style: "width:100%;text-align:left;padding:9px 10px;border:1px solid " + (active && active.trip_id === item.trip_id ? "#b21f2d" : "#313844") + ";border-radius:6px;background:#0d1014;color:#eef2f6;font:inherit;cursor:pointer;",\n'
        "    }));\n"
        '    const ledger = active ? (active.ledger_entries || []).map((item) => ({ id: item.entry_id, title: item.description, meta: item.transaction_date + " · $" + item.amount + " · " + item.category })) : [];\n'
        "    const latest = active && active.latest_gtcc_check ? active.latest_gtcc_check : null;\n"
        "    return {\n"
        "      travelTrips: trips, travelTripsEmpty: trips.length === 0, activeTravelExists: !!active,\n"
        '      activeTravelTitle: active ? active.title : "Choose or create a trip", activeTravelUpdated: active ? new Date(active.updated_at).toLocaleString() : "",\n'
        '      activeTravelTotal: active ? active.estimated_spend_total : "0.00", travelLedger: ledger, travelLedgerEmpty: ledger.length === 0,\n'
        "      travelReceipts: active ? (active.attachment_names || []).map((name) => ({ name })) : [], travelReceiptsEmpty: !active || !(active.attachment_names || []).length,\n"
        '      gtccLatestLabel: latest ? ("Last checked " + new Date(latest.checked_at).toLocaleDateString() + (latest.paid_in_full ? " · marked paid in full" : "")) : "No GTCC check recorded yet.",\n'
        "      travelLoadStatus: this.state.travelLoadStatus, travelDraftTitle: this.state.travelDraftTitle, travelDraftDestination: this.state.travelDraftDestination,\n"
        "      travelLedgerDate: this.state.travelLedgerDate, travelLedgerDescription: this.state.travelLedgerDescription, travelLedgerAmount: this.state.travelLedgerAmount, travelLedgerCategory: this.state.travelLedgerCategory,\n"
        "      gtccBalance: this.state.gtccBalance, gtccPayment: this.state.gtccPayment, gtccPaidInFull: this.state.gtccPaidInFull, gtccCheckNotes: this.state.gtccCheckNotes,\n"
        "      onTravelTitle: (e) => this.setState({ travelDraftTitle: e.target.value }), onTravelDestination: (e) => this.setState({ travelDraftDestination: e.target.value }), onCreateTravel: (e) => this.createTravelCase(e),\n"
        "      onTravelLedgerDate: (e) => this.setState({ travelLedgerDate: e.target.value }), onTravelLedgerDescription: (e) => this.setState({ travelLedgerDescription: e.target.value }), onTravelLedgerAmount: (e) => this.setState({ travelLedgerAmount: e.target.value }), onTravelLedgerCategory: (e) => this.setState({ travelLedgerCategory: e.target.value }), onAddTravelLedger: (e) => this.addTravelLedgerEntry(e),\n"
        "      onGtccBalance: (e) => this.setState({ gtccBalance: e.target.value }), onGtccPayment: (e) => this.setState({ gtccPayment: e.target.value }), onGtccPaid: (e) => this.setState({ gtccPaidInFull: e.target.checked }), onGtccNotes: (e) => this.setState({ gtccCheckNotes: e.target.value }), onRecordGtccCheck: (e) => this.recordGtccCheck(e),\n"
        "      onTravelReceiptFile: (e) => this.uploadTravelReceipt(e),\n"
        "    };\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "travel workspace: expose view bindings",
        "      ...this.travelWorkspaceVals(),\n",
        "      ...this.fitrepVals(),\n      quote: this.state.quote,\n",
        "      ...this.fitrepVals(),\n      ...this.travelWorkspaceVals(),\n      quote: this.state.quote,\n",
    ),
    (
        "travel workspace: render third workspace panel",
        '<h3 style="margin:0 0 4px;font-size:1.02rem;font-weight:700;">Travel &amp; GTCC</h3>',
        "        </section>\n\n"
        "        </sc-if>\n"
        '        <sc-if value="{{ isFitreps }}" hint-placeholder-val="{{ false }}">\n',
        "        </section>\n"
        '        <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px;display:grid;gap:14px;">\n'
        '          <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;flex-wrap:wrap;">\n'
        '            <div><h3 style="margin:0 0 4px;font-size:1.02rem;font-weight:700;">Travel &amp; GTCC</h3><p style="margin:0;color:#8a94a0;font-size:0.82rem;line-height:1.45;">Trips, receipts, expenses, and monthly card checks. Stored values are user-entered and may be stale; this does not connect to Citi.</p></div>\n'
        '            <a href="https://home.cards.citidirect.com/CommercialCard/login" target="_blank" rel="noopener" style="height:34px;display:inline-flex;align-items:center;padding:0 14px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font-size:0.8rem;font-weight:700;">Open CitiManager ↗</a>\n'
        "          </div>\n"
        '          <p aria-live="polite" style="margin:0;color:#8a94a0;font-size:0.76rem;">{{ travelLoadStatus }}</p>\n'
        '          <div style="display:grid;grid-template-columns:minmax(220px,280px) 1fr;gap:16px;">\n'
        '            <div style="display:grid;gap:8px;align-content:start;">\n'
        '              <sc-for list="{{ travelTrips }}" as="trip" hint-placeholder-count="2"><button type="button" sc-camel-on-click="{{ trip.onClick }}" style="{{ trip.style }}"><strong style="display:block;font-size:0.84rem;">{{ trip.title }}</strong><span style="display:block;margin-top:3px;color:#8a94a0;font-size:0.74rem;">{{ trip.meta }}</span></button></sc-for>\n'
        '              <sc-if value="{{ travelTripsEmpty }}" hint-placeholder-val="{{ true }}"><p style="margin:0;color:#8a94a0;font-size:0.8rem;">No trips yet. Create one below.</p></sc-if>\n'
        '              <form sc-camel-on-submit="{{ onCreateTravel }}" style="display:grid;gap:7px;padding-top:8px;border-top:1px solid #313844;">\n'
        '                <input value="{{ travelDraftTitle }}" sc-camel-on-change="{{ onTravelTitle }}" placeholder="Trip title" aria-label="Trip title" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;">\n'
        '                <input value="{{ travelDraftDestination }}" sc-camel-on-change="{{ onTravelDestination }}" placeholder="Destination (optional)" aria-label="Trip destination" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 10px;background:#0d1014;color:#eef2f6;font:inherit;">\n'
        '                <button type="submit" style="height:32px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;cursor:pointer;">+ Create travel folder</button>\n'
        "              </form>\n"
        "            </div>\n"
        '            <sc-if value="{{ activeTravelExists }}" hint-placeholder-val="{{ false }}">\n'
        '            <div style="display:grid;gap:14px;align-content:start;">\n'
        '              <div><strong style="font-size:0.9rem;">{{ activeTravelTitle }}</strong><span style="display:block;margin-top:2px;color:#8a94a0;font-size:0.74rem;">Updated {{ activeTravelUpdated }} · logged spend ${{ activeTravelTotal }}</span></div>\n'
        '              <div style="display:grid;gap:6px;"><strong style="font-size:0.8rem;">Expense log</strong><sc-for list="{{ travelLedger }}" as="entry" hint-placeholder-count="2"><div style="padding:8px 10px;border:1px solid #313844;border-radius:6px;background:#0d1014;"><span style="font-size:0.8rem;font-weight:600;">{{ entry.title }}</span><span style="display:block;color:#8a94a0;font-size:0.72rem;margin-top:2px;">{{ entry.meta }}</span></div></sc-for><sc-if value="{{ travelLedgerEmpty }}" hint-placeholder-val="{{ true }}"><p style="margin:0;color:#8a94a0;font-size:0.76rem;">No expenses logged.</p></sc-if></div>\n'
        '              <form sc-camel-on-submit="{{ onAddTravelLedger }}" style="display:grid;grid-template-columns:140px 1fr 120px 140px auto;gap:7px;">\n'
        '                <input type="date" value="{{ travelLedgerDate }}" sc-camel-on-change="{{ onTravelLedgerDate }}" aria-label="Transaction date" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;">\n'
        '                <input value="{{ travelLedgerDescription }}" sc-camel-on-change="{{ onTravelLedgerDescription }}" placeholder="Description" aria-label="Expense description" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;">\n'
        '                <input type="number" step="0.01" value="{{ travelLedgerAmount }}" sc-camel-on-change="{{ onTravelLedgerAmount }}" placeholder="Amount" aria-label="Expense amount" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;">\n'
        '                <sc-raw-select value="{{ travelLedgerCategory }}" sc-camel-on-change="{{ onTravelLedgerCategory }}" aria-label="Expense category" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="other">Other</option><option value="lodging">Lodging</option><option value="transportation">Transportation</option><option value="meals">Meals</option><option value="fees">Fees</option></sc-raw-select>\n'
        '                <button type="submit" style="height:34px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;cursor:pointer;">Add</button>\n'
        "              </form>\n"
        '              <div style="display:grid;gap:6px;"><strong style="font-size:0.8rem;">Receipts</strong><sc-for list="{{ travelReceipts }}" as="receipt" hint-placeholder-count="1"><span style="font-size:0.76rem;color:#c7cfd8;">{{ receipt.name }}</span></sc-for><sc-if value="{{ travelReceiptsEmpty }}" hint-placeholder-val="{{ true }}"><span style="font-size:0.76rem;color:#8a94a0;">No receipts linked.</span></sc-if><label style="justify-self:start;height:30px;display:inline-flex;align-items:center;padding:0 10px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font-size:0.76rem;font-weight:600;cursor:pointer;">Upload receipt<input type="file" sc-camel-on-change="{{ onTravelReceiptFile }}" style="display:none"></label></div>\n'
        '              <form sc-camel-on-submit="{{ onRecordGtccCheck }}" style="display:grid;gap:8px;padding:12px;border:1px solid #2a3c4a;border-radius:6px;background:#0f1620;">\n'
        '                <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;"><strong style="font-size:0.82rem;">Monthly GTCC check</strong><span style="color:#8a94a0;font-size:0.74rem;">{{ gtccLatestLabel }}</span></div>\n'
        '                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:7px;"><input type="number" step="0.01" value="{{ gtccBalance }}" sc-camel-on-change="{{ onGtccBalance }}" placeholder="Statement balance (optional)" aria-label="GTCC statement balance" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input type="number" step="0.01" value="{{ gtccPayment }}" sc-camel-on-change="{{ onGtccPayment }}" placeholder="Payment (optional)" aria-label="GTCC payment amount" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ gtccCheckNotes }}" sc-camel-on-change="{{ onGtccNotes }}" placeholder="Notes" aria-label="GTCC check notes" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"></div>\n'
        '                <div style="display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap;"><label style="display:flex;gap:7px;align-items:center;color:#c7cfd8;font-size:0.78rem;"><input type="checkbox" checked="{{ gtccPaidInFull }}" sc-camel-on-change="{{ onGtccPaid }}"> Paid in full</label><button type="submit" style="height:32px;padding:0 14px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:700;cursor:pointer;">Mark checked</button></div>\n'
        "              </form>\n"
        "            </div>\n"
        "            </sc-if>\n"
        "          </div>\n"
        "        </section>\n\n"
        "        </sc-if>\n"
        '        <sc-if value="{{ isFitreps }}" hint-placeholder-val="{{ false }}">\n',
    ),
    # ------------------------------------------------------------------
    # Personal FitRep profile analytics (2026-07-15): reviewed imports,
    # manual entries, RS snapshots, improvement goals, and exact-value charts.
    # ------------------------------------------------------------------
    (
        "fitrep analytics: add component state",
        "    fitrepAnalyticsWorkspace: { reports: [], rs_profiles: [], goals: [] },\n"
        "    fitrepAnalytics: { sample_size: 0, relative_value_trend: [], by_reporting_senior: [], trait_trends: {}, data_quality_warnings: [] },\n"
        "    fitrepImportProposal: null,\n"
        '    fitrepProfileStatus: "",\n'
        '    fitrepManualPeriod: "",\n'
        '    fitrepManualRs: "",\n'
        '    fitrepManualRv: "",\n'
        '    fitrepManualGrade: "",\n'
        '    fitrepGoalTitle: "",\n'
        '    fitrepGoalRs: "",\n',
        '    fitrepPeriodFilter: "",\n    profilePasskey: "",\n',
        '    fitrepPeriodFilter: "",\n'
        "    fitrepAnalyticsWorkspace: { reports: [], rs_profiles: [], goals: [] },\n"
        "    fitrepAnalytics: { sample_size: 0, relative_value_trend: [], by_reporting_senior: [], trait_trends: {}, data_quality_warnings: [] },\n"
        "    fitrepImportProposal: null,\n"
        '    fitrepProfileStatus: "",\n'
        '    fitrepManualPeriod: "",\n'
        '    fitrepManualRs: "",\n'
        '    fitrepManualRv: "",\n'
        '    fitrepManualGrade: "",\n'
        '    fitrepGoalTitle: "",\n'
        '    fitrepGoalRs: "",\n'
        '    profilePasskey: "",\n',
    ),
    (
        "fitrep analytics: load profile during mount",
        "    this._loadFitrepAnalytics();\n",
        "    this._loadTravelCases();\n    this._loadRealNotes();\n    this._loadRealFitreps();\n",
        "    this._loadTravelCases();\n"
        "    this._loadRealNotes();\n"
        "    this._loadRealFitreps();\n"
        "    this._loadFitrepAnalytics();\n",
    ),
    (
        "fitrep and travel: reload profile domains on demo switch",
        "    this._loadFitrepAnalytics();\n    this._loadRealGenerations();\n    this._loadRealAgentNotes();\n",
        "    this._loadRealWorkspace();\n"
        "    this._loadRealProjects(on);\n"
        "    this._loadRealNotes();\n"
        "    this._loadRealFitreps();\n"
        "    this._loadRealGenerations();\n"
        "    this._loadRealAgentNotes();\n",
        "    this._loadRealWorkspace();\n"
        "    this._loadRealProjects(on);\n"
        "    this._loadRealNotes();\n"
        "    this._loadRealFitreps();\n"
        "    this._loadTravelCases();\n"
        "    this._loadFitrepAnalytics();\n"
        "    this._loadRealGenerations();\n"
        "    this._loadRealAgentNotes();\n",
    ),
    (
        "fitrep analytics: add API helpers and bindings",
        "  async _loadFitrepAnalytics() {",
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        "  async _loadFitrepAnalytics() {\n"
        "    if (!this.userKey) this.userKey = this._resolveUserKey();\n"
        "    try {\n"
        '      const base = "/fitreps/" + encodeURIComponent(this.userKey);\n'
        '      const responses = await Promise.all([fetch(base, { headers: this._apiHeaders() }), fetch(base + "/analytics", { headers: this._apiHeaders() })]);\n'
        '      if (!responses[0].ok || !responses[1].ok) throw new Error("fitrep profile load failed");\n'
        "      const values = await Promise.all(responses.map((res) => res.json()));\n"
        '      this.setState({ fitrepAnalyticsWorkspace: values[0], fitrepAnalytics: values[1], fitrepProfileStatus: "" });\n'
        '    } catch (err) { this.setState({ fitrepProfileStatus: "Profile analytics could not be loaded." }); }\n'
        "  }\n"
        "  uploadFitrepProfile(e, kind) {\n"
        "    const file = e.target.files && e.target.files[0]; if (!file) return;\n"
        '    const form = new FormData(); form.append("file", file); form.append("document_type", "fitrep"); form.append("tags", kind === "rs_profile" ? "fitrep,rs-profile" : "fitrep,my-record");\n'
        '    this.setState({ fitrepProfileStatus: "Reading local document…", fitrepImportProposal: null });\n'
        '    fetch("/context/upload", { method: "POST", headers: this._apiHeaders(), body: form })\n'
        "      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))\n"
        '      .then(({ ok, data }) => { if (!ok || !data.item) throw new Error("upload failed"); return fetch("/fitreps/" + encodeURIComponent(this.userKey) + "/imports/preview", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ user_key: this.userKey, context_id: data.item.context_id, kind }) }); })\n'
        "      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))\n"
        '      .then(({ ok, data }) => { if (!ok) throw new Error("preview failed"); this.setState({ fitrepImportProposal: data, fitrepProfileStatus: "Review the proposal before saving." }); })\n'
        '      .catch(() => this.setState({ fitrepProfileStatus: "The document could not be proposed for import." }));\n'
        '    e.target.value = "";\n'
        "  }\n"
        "  confirmFitrepImport() {\n"
        "    const proposal = this.state.fitrepImportProposal; if (!proposal) return;\n"
        '    this.setState({ fitrepProfileStatus: "Saving confirmed import…" });\n'
        '    fetch("/fitreps/" + encodeURIComponent(this.userKey) + "/imports/confirm", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ user_key: this.userKey, kind: proposal.kind, proposal }) })\n'
        '      .then((res) => { if (!res.ok) throw new Error("confirm failed"); this.setState({ fitrepImportProposal: null, fitrepProfileStatus: "Import saved locally." }); return this._loadFitrepAnalytics(); })\n'
        '      .catch(() => this.setState({ fitrepProfileStatus: "The proposed import was not saved." }));\n'
        "  }\n"
        "  addManualFitrepProfile(e) {\n"
        "    e.preventDefault();\n"
        '    const rv = (this.state.fitrepManualRv || "").trim();\n'
        '    if (!rv && !(this.state.fitrepManualRs || "").trim() && !(this.state.fitrepManualPeriod || "").trim()) return;\n'
        '    const body = { user_key: this.userKey, period_end: this.state.fitrepManualPeriod || null, rs_label: this.state.fitrepManualRs || "", grade: this.state.fitrepManualGrade || "" }; if (rv) body.relative_value = rv;\n'
        '    fetch("/fitreps/" + encodeURIComponent(this.userKey) + "/reports", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(body) })\n'
        '      .then((res) => { if (!res.ok) throw new Error("manual save failed"); this.setState({ fitrepManualPeriod: "", fitrepManualRs: "", fitrepManualRv: "", fitrepManualGrade: "", fitrepProfileStatus: "Manual profile entry saved." }); return this._loadFitrepAnalytics(); })\n'
        '      .catch(() => this.setState({ fitrepProfileStatus: "Manual profile entry was not saved." }));\n'
        "  }\n"
        "  addFitrepGoal(e) {\n"
        '    e.preventDefault(); const title = (this.state.fitrepGoalTitle || "").trim(); if (!title) return;\n'
        '    fetch("/fitreps/" + encodeURIComponent(this.userKey) + "/goals", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ user_key: this.userKey, title, rs_label: (this.state.fitrepGoalRs || "").trim() || "Unspecified RS" }) })\n'
        '      .then((res) => { if (!res.ok) throw new Error("goal save failed"); this.setState({ fitrepGoalTitle: "", fitrepGoalRs: "", fitrepProfileStatus: "Improvement goal saved." }); return this._loadFitrepAnalytics(); })\n'
        '      .catch(() => this.setState({ fitrepProfileStatus: "Improvement goal was not saved." }));\n'
        "  }\n"
        "  fitrepProfileVals() {\n"
        "    const workspace = this.state.fitrepAnalyticsWorkspace || { reports: [], rs_profiles: [], goals: [] }; const analytics = this.state.fitrepAnalytics || {}; const proposal = this.state.fitrepImportProposal;\n"
        '    const trend = (analytics.relative_value_trend || []).map((point) => ({ label: point.label, value: point.value, width: "width:" + Math.max(2, Math.min(100, Number(point.value) || 0)) + "%;height:8px;border-radius:999px;background:#5a9fd4;" }));\n'
        '    const rs = (analytics.by_reporting_senior || []).map((item) => ({ label: item.rs_label, meta: item.report_count + " report(s) · average RV " + (item.average_relative_value == null ? "not supplied" : item.average_relative_value) }));\n'
        '    const goals = (workspace.goals || []).map((item) => ({ title: item.title, meta: item.rs_label + " · " + item.status }));\n'
        '    let proposalSummary = ""; if (proposal && proposal.report) proposalSummary = [proposal.report.period_end, proposal.report.grade, proposal.report.rs_label, proposal.report.relative_value == null ? "RV not found" : "RV " + proposal.report.relative_value].filter(Boolean).join(" · "); else if (proposal && proposal.rs_profile) proposalSummary = [proposal.rs_profile.rs_label || "RS not found", proposal.rs_profile.as_of_date, proposal.rs_profile.report_count == null ? "Report count not found" : proposal.rs_profile.report_count + " reports"].filter(Boolean).join(" · ");\n'
        "    return {\n"
        "      fitrepProfileStatus: this.state.fitrepProfileStatus, fitrepImportProposalVisible: !!proposal, fitrepImportProposalSummary: proposalSummary, fitrepImportWarnings: proposal ? (proposal.warnings || []).map((text) => ({ text })) : [],\n"
        "      fitrepProfileSample: analytics.sample_size || 0, fitrepRvTrend: trend, fitrepRvTrendEmpty: trend.length === 0, fitrepRsSummaries: rs, fitrepRsSummariesEmpty: rs.length === 0, fitrepProfileGoals: goals, fitrepProfileGoalsEmpty: goals.length === 0,\n"
        "      fitrepProfileWarnings: (analytics.data_quality_warnings || []).map((text) => ({ text })),\n"
        "      fitrepManualPeriod: this.state.fitrepManualPeriod, fitrepManualRs: this.state.fitrepManualRs, fitrepManualRv: this.state.fitrepManualRv, fitrepManualGrade: this.state.fitrepManualGrade, fitrepGoalTitle: this.state.fitrepGoalTitle, fitrepGoalRs: this.state.fitrepGoalRs,\n"
        '      onMyRecordFile: (e) => this.uploadFitrepProfile(e, "my_record"), onRsProfileFile: (e) => this.uploadFitrepProfile(e, "rs_profile"), onConfirmFitrepImport: () => this.confirmFitrepImport(), onCancelFitrepImport: () => this.setState({ fitrepImportProposal: null, fitrepProfileStatus: "Import proposal discarded; the local source file remains available." }),\n'
        "      onFitrepManualPeriod: (e) => this.setState({ fitrepManualPeriod: e.target.value }), onFitrepManualRs: (e) => this.setState({ fitrepManualRs: e.target.value }), onFitrepManualRv: (e) => this.setState({ fitrepManualRv: e.target.value }), onFitrepManualGrade: (e) => this.setState({ fitrepManualGrade: e.target.value }), onAddManualFitrepProfile: (e) => this.addManualFitrepProfile(e),\n"
        "      onFitrepGoalTitle: (e) => this.setState({ fitrepGoalTitle: e.target.value }), onFitrepGoalRs: (e) => this.setState({ fitrepGoalRs: e.target.value }), onAddFitrepGoal: (e) => this.addFitrepGoal(e),\n"
        "    };\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "fitrep analytics: expose view bindings",
        "      ...this.fitrepProfileVals(),\n",
        "      ...this.fitrepVals(),\n      ...this.travelWorkspaceVals(),\n",
        "      ...this.fitrepVals(),\n      ...this.fitrepProfileVals(),\n      ...this.travelWorkspaceVals(),\n",
    ),
    (
        "fitrep analytics: render profile import and trends panel",
        '<h3 style="margin:0;font-size:1.02rem;font-weight:700;">My profile analytics</h3>',
        "        </section>\n        </sc-if><!-- dedicated FitReps lane ends -->\n",
        "        </section>\n"
        '        <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px;display:grid;gap:14px;">\n'
        '          <div><h3 style="margin:0;font-size:1.02rem;font-weight:700;">My profile analytics</h3><p style="margin:5px 0 0;color:#8a94a0;font-size:0.8rem;line-height:1.5;">Track your own confirmed report history, Reporting Senior context, and improvement goals. This descriptive view does not predict promotion, selection, or future marks.</p></div>\n'
        '          <div style="display:flex;gap:8px;flex-wrap:wrap;"><label style="height:32px;display:inline-flex;align-items:center;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font-size:0.78rem;font-weight:700;cursor:pointer;">Upload My Record<input type="file" sc-camel-on-change="{{ onMyRecordFile }}" style="display:none"></label><label style="height:32px;display:inline-flex;align-items:center;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font-size:0.78rem;font-weight:700;cursor:pointer;">Upload RS Profile<input type="file" sc-camel-on-change="{{ onRsProfileFile }}" style="display:none"></label><span aria-live="polite" style="align-self:center;color:#8a94a0;font-size:0.76rem;">{{ fitrepProfileStatus }}</span></div>\n'
        '          <sc-if value="{{ fitrepImportProposalVisible }}" hint-placeholder-val="{{ false }}"><div style="padding:12px;border:1px solid #5a4b2a;border-radius:6px;background:#1c1810;display:grid;gap:7px;"><strong style="font-size:0.82rem;color:#e0c77a;">Review proposed import</strong><span style="font-size:0.78rem;color:#c7cfd8;">{{ fitrepImportProposalSummary }}</span><sc-for list="{{ fitrepImportWarnings }}" as="warning" hint-placeholder-count="1"><span style="font-size:0.74rem;color:#d6bd7a;">{{ warning.text }}</span></sc-for><div style="display:flex;gap:8px;"><button type="button" sc-camel-on-click="{{ onConfirmFitrepImport }}" style="height:30px;padding:0 12px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-size:0.76rem;font-weight:700;cursor:pointer;">Confirm import</button><button type="button" sc-camel-on-click="{{ onCancelFitrepImport }}" style="height:30px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:transparent;color:#c7cfd8;font:inherit;font-size:0.76rem;cursor:pointer;">Discard proposal</button></div></div></sc-if>\n'
        '          <details><summary style="cursor:pointer;font-size:0.8rem;font-weight:700;color:#c7cfd8;">Manual profile entry</summary><form sc-camel-on-submit="{{ onAddManualFitrepProfile }}" style="display:grid;grid-template-columns:140px 100px 1fr 120px auto;gap:7px;margin-top:10px;"><input type="date" value="{{ fitrepManualPeriod }}" sc-camel-on-change="{{ onFitrepManualPeriod }}" aria-label="Reporting period end" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ fitrepManualGrade }}" sc-camel-on-change="{{ onFitrepManualGrade }}" placeholder="Grade" aria-label="Grade" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ fitrepManualRs }}" sc-camel-on-change="{{ onFitrepManualRs }}" placeholder="Reporting Senior label" aria-label="Reporting Senior label" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input type="number" step="0.01" value="{{ fitrepManualRv }}" sc-camel-on-change="{{ onFitrepManualRv }}" placeholder="Relative value" aria-label="Relative value" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><button type="submit" style="height:34px;padding:0 12px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;cursor:pointer;">Add</button></form></details>\n'
        '          <div style="display:grid;grid-template-columns:1.2fr 1fr;gap:14px;">\n'
        '            <div style="padding:12px;border:1px solid #313844;border-radius:6px;background:#0d1014;display:grid;gap:8px;"><div style="display:flex;justify-content:space-between;gap:10px;"><strong style="font-size:0.82rem;">Relative-value trend</strong><span style="color:#8a94a0;font-size:0.72rem;">{{ fitrepProfileSample }} confirmed reports · Exact values</span></div><sc-for list="{{ fitrepRvTrend }}" as="point" hint-placeholder-count="3"><div style="display:grid;grid-template-columns:100px 1fr 50px;gap:8px;align-items:center;"><span style="font-size:0.72rem;color:#8a94a0;">{{ point.label }}</span><div style="height:8px;background:#1a2027;border-radius:999px;overflow:hidden;"><div style="{{ point.width }}"></div></div><strong style="font-size:0.72rem;text-align:right;">{{ point.value }}</strong></div></sc-for><sc-if value="{{ fitrepRvTrendEmpty }}" hint-placeholder-val="{{ true }}"><span style="color:#8a94a0;font-size:0.76rem;">Add confirmed relative values to build the chart.</span></sc-if></div>\n'
        '            <div style="padding:12px;border:1px solid #313844;border-radius:6px;background:#0d1014;display:grid;gap:7px;align-content:start;"><strong style="font-size:0.82rem;">Reporting Senior comparison</strong><sc-for list="{{ fitrepRsSummaries }}" as="rs" hint-placeholder-count="2"><div style="padding:7px 0;border-bottom:1px solid #242b33;"><span style="font-size:0.76rem;font-weight:600;">{{ rs.label }}</span><span style="display:block;color:#8a94a0;font-size:0.7rem;margin-top:2px;">{{ rs.meta }}</span></div></sc-for><sc-if value="{{ fitrepRsSummariesEmpty }}" hint-placeholder-val="{{ true }}"><span style="color:#8a94a0;font-size:0.76rem;">No RS groupings yet.</span></sc-if></div>\n'
        "          </div>\n"
        '          <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;"><div style="display:grid;gap:7px;"><strong style="font-size:0.8rem;">Improvement under one RS</strong><sc-for list="{{ fitrepProfileGoals }}" as="goal" hint-placeholder-count="1"><div style="padding:8px 10px;border:1px solid #313844;border-radius:6px;background:#0d1014;"><span style="font-size:0.76rem;font-weight:600;">{{ goal.title }}</span><span style="display:block;color:#8a94a0;font-size:0.7rem;margin-top:2px;">{{ goal.meta }}</span></div></sc-for><sc-if value="{{ fitrepProfileGoalsEmpty }}" hint-placeholder-val="{{ true }}"><span style="color:#8a94a0;font-size:0.74rem;">No improvement goals saved.</span></sc-if></div><form sc-camel-on-submit="{{ onAddFitrepGoal }}" style="display:grid;gap:7px;align-content:start;"><input value="{{ fitrepGoalTitle }}" sc-camel-on-change="{{ onFitrepGoalTitle }}" placeholder="Observable improvement goal" aria-label="FitRep improvement goal" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ fitrepGoalRs }}" sc-camel-on-change="{{ onFitrepGoalRs }}" placeholder="Reporting Senior label" aria-label="Goal Reporting Senior" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><button type="submit" style="height:32px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;cursor:pointer;">Save goal</button></form></div>\n'
        '          <sc-for list="{{ fitrepProfileWarnings }}" as="warning" hint-placeholder-count="1"><p style="margin:0;color:#d6bd7a;font-size:0.72rem;">{{ warning.text }}</p></sc-for>\n'
        "        </section>\n"
        "        </sc-if><!-- dedicated FitReps lane ends -->\n",
    ),
    # Unit fitness and cadence workspace (2026-07-15): a low-friction entry
    # point for the typed 5-50 Marine planner and private cadence library.
    (
        "fitness workspace: add component state",
        '    fitnessParticipantCount: "20",\n',
        '    fitrepGoalRs: "",\n    profilePasskey: "",\n',
        '    fitrepGoalRs: "",\n'
        '    fitnessParticipantCount: "20",\n'
        '    fitnessObjective: "general fitness",\n'
        '    fitnessDuration: "60",\n'
        '    fitnessLocation: "unit training area",\n'
        '    fitnessEquipment: "",\n'
        '    fitnessAbilityNotes: "mixed ability",\n'
        '    fitnessWeatherNotes: "check current conditions",\n'
        '    fitnessCadencePreference: "",\n'
        "    fitnessIncludeCadence: true,\n"
        "    fitnessPlan: null,\n"
        '    fitnessStatus: "",\n'
        "    cadenceRecords: [],\n"
        "    cadenceIncludeAdult: false,\n"
        '    cadenceTitle: "",\n'
        '    cadenceText: "",\n'
        "    cadenceAdult: false,\n"
        '    cadenceStatus: "",\n'
        '    profilePasskey: "",\n',
    ),
    (
        "fitness workspace: load cadence library on mount",
        "    this._loadCadences();\n",
        "    this._loadRealFitreps();\n    this._loadFitrepAnalytics();\n    this._loadRealGenerations();\n",
        "    this._loadRealFitreps();\n"
        "    this._loadFitrepAnalytics();\n"
        "    this._loadCadences();\n"
        "    this._loadRealGenerations();\n",
    ),
    (
        "fitness workspace: add API helpers and bindings",
        "  async _loadCadences(includeAdult) {",
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        "  async _loadCadences(includeAdult) {\n"
        "    if (!this.userKey) this.userKey = this._resolveUserKey();\n"
        "    const adult = includeAdult == null ? !!this.state.cadenceIncludeAdult : !!includeAdult;\n"
        "    try {\n"
        '      const res = await fetch("/cadences/" + encodeURIComponent(this.userKey) + "?include_adult=" + adult, { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("cadence load failed");\n'
        '      const data = await res.json(); this.setState({ cadenceRecords: data.records || [], cadenceStatus: "" });\n'
        '    } catch (err) { this.setState({ cadenceStatus: "Cadence library could not be loaded." }); }\n'
        "  }\n"
        "  buildUnitPt(e) {\n"
        "    e.preventDefault();\n"
        '    const equipment = (this.state.fitnessEquipment || "").split(",").map((item) => item.trim()).filter(Boolean);\n'
        '    const body = { participant_count: Number(this.state.fitnessParticipantCount), objective: this.state.fitnessObjective, duration_minutes: Number(this.state.fitnessDuration), location: this.state.fitnessLocation || "unit training area", equipment, ability_notes: this.state.fitnessAbilityNotes || "mixed ability", weather_notes: this.state.fitnessWeatherNotes || "check current conditions", include_cadence: !!this.state.fitnessIncludeCadence, cadence_preference: (this.state.fitnessCadencePreference || "").trim() || null };\n'
        '    this.setState({ fitnessStatus: "Building staff-reviewed plan…" });\n'
        '    fetch("/fitness/unit-pt/plan", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(body) })\n'
        "      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))\n"
        '      .then(({ ok, data }) => { if (!ok) throw new Error("plan failed"); this.setState({ fitnessPlan: data, fitnessStatus: "Plan built. Review conditions and route residual-risk acceptance." }); })\n'
        '      .catch(() => this.setState({ fitnessStatus: "Plan could not be built. Participant count must be 5–50." }));\n'
        "  }\n"
        "  addPrivateCadence(e) {\n"
        '    e.preventDefault(); const title = (this.state.cadenceTitle || "").trim(); const text = (this.state.cadenceText || "").trim(); if (!title || !text) return;\n'
        '    this.setState({ cadenceStatus: "Saving cadence locally…" });\n'
        '    fetch("/cadences/" + encodeURIComponent(this.userKey), { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ user_key: this.userKey, title, text, rating: this.state.cadenceAdult ? "adult" : "clean" }) })\n'
        "      .then((res) => res.json().then((data) => ({ ok: res.ok, data })))\n"
        '      .then(({ ok, data }) => { if (!ok) throw new Error((data && data.detail) || "save failed"); this.setState({ cadenceTitle: "", cadenceText: "", cadenceAdult: false, cadenceStatus: "Cadence saved locally." }); return this._loadCadences(); })\n'
        '      .catch((err) => this.setState({ cadenceStatus: String((err && err.message) || "Cadence was not saved.") }));\n'
        "  }\n"
        "  fitnessWorkspaceVals() {\n"
        '    const plan = this.state.fitnessPlan; const cadences = (this.state.cadenceRecords || []).map((item) => ({ title: item.title, meta: (item.built_in ? "Built in" : "Private") + " · " + item.rating + " · " + item.use, text: item.text }));\n'
        "    return {\n"
        "      fitnessParticipantCount: this.state.fitnessParticipantCount, fitnessObjective: this.state.fitnessObjective, fitnessDuration: this.state.fitnessDuration, fitnessLocation: this.state.fitnessLocation, fitnessEquipment: this.state.fitnessEquipment, fitnessAbilityNotes: this.state.fitnessAbilityNotes, fitnessWeatherNotes: this.state.fitnessWeatherNotes, fitnessCadencePreference: this.state.fitnessCadencePreference, fitnessIncludeCadence: this.state.fitnessIncludeCadence, fitnessStatus: this.state.fitnessStatus, fitnessPlanVisible: !!plan,\n"
        '      fitnessPlanBand: plan ? plan.scaling_band : "", fitnessPlanBlocks: plan ? (plan.blocks || []).map((item) => ({ title: item.name + " · " + item.minutes + " min", text: (item.instructions || []).join(" ") })) : [], fitnessStaffReviews: plan ? (plan.staff_reviews || []).map((item) => ({ title: item.role, text: [...(item.findings || []), ...(item.actions || [])].join(" ") })) : [], fitnessOrmHazards: plan ? ((plan.orm && plan.orm.hazards) || []).map((item) => ({ title: item.hazard + " · residual " + item.residual_risk, text: (item.controls || []).join("; ") + ". Stop: " + item.stop_trigger })) : [], fitnessWarnings: plan ? (plan.warnings || []).map((text) => ({ text })) : [],\n'
        "      cadenceRecords: cadences, cadenceRecordsEmpty: cadences.length === 0, cadenceIncludeAdult: this.state.cadenceIncludeAdult, cadenceTitle: this.state.cadenceTitle, cadenceText: this.state.cadenceText, cadenceAdult: this.state.cadenceAdult, cadenceStatus: this.state.cadenceStatus,\n"
        "      onFitnessCount: (e) => this.setState({ fitnessParticipantCount: e.target.value }), onFitnessObjective: (e) => this.setState({ fitnessObjective: e.target.value }), onFitnessDuration: (e) => this.setState({ fitnessDuration: e.target.value }), onFitnessLocation: (e) => this.setState({ fitnessLocation: e.target.value }), onFitnessEquipment: (e) => this.setState({ fitnessEquipment: e.target.value }), onFitnessAbility: (e) => this.setState({ fitnessAbilityNotes: e.target.value }), onFitnessWeather: (e) => this.setState({ fitnessWeatherNotes: e.target.value }), onFitnessCadencePreference: (e) => this.setState({ fitnessCadencePreference: e.target.value }), onFitnessIncludeCadence: (e) => this.setState({ fitnessIncludeCadence: e.target.checked }), onBuildUnitPt: (e) => this.buildUnitPt(e),\n"
        "      onCadenceAdultFilter: (e) => { const value = e.target.checked; this.setState({ cadenceIncludeAdult: value }); this._loadCadences(value); }, onCadenceTitle: (e) => this.setState({ cadenceTitle: e.target.value }), onCadenceText: (e) => this.setState({ cadenceText: e.target.value }), onCadenceAdult: (e) => this.setState({ cadenceAdult: e.target.checked }), onAddPrivateCadence: (e) => this.addPrivateCadence(e),\n"
        "    };\n"
        "  }\n"
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "fitness workspace: expose view bindings",
        "      ...this.fitnessWorkspaceVals(),\n",
        "      ...this.fitrepProfileVals(),\n      ...this.travelWorkspaceVals(),\n",
        "      ...this.fitrepProfileVals(),\n"
        "      ...this.travelWorkspaceVals(),\n"
        "      ...this.fitnessWorkspaceVals(),\n",
    ),
    (
        "fitness workspace: render unit PT and cadence panel",
        '<h3 style="margin:0;font-size:1.02rem;font-weight:700;">Unit PT Planner &amp; Cadences</h3>',
        "        </section>\n\n"
        "        </sc-if>\n"
        '        <sc-if value="{{ isFitreps }}" hint-placeholder-val="{{ false }}">\n',
        "        </section>\n"
        '        <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px;display:grid;gap:14px;">\n'
        '          <div><h3 style="margin:0;font-size:1.02rem;font-weight:700;">Unit PT Planner &amp; Cadences</h3><p style="margin:5px 0 0;color:#8a94a0;font-size:0.8rem;line-height:1.5;">Build a scalable draft for 5–50 Marines with S-3, S-4, SgtMaj/SEL, Fitness, and ORM review. This is not FFI, CPTR, medical, or official risk-acceptance authority.</p></div>\n'
        '          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">\n'
        '            <form sc-camel-on-submit="{{ onBuildUnitPt }}" style="display:grid;gap:8px;align-content:start;">\n'
        '              <strong style="font-size:0.82rem;">Plan a unit PT event</strong>\n'
        '              <div style="display:grid;grid-template-columns:100px 1fr 100px;gap:7px;"><input type="number" min="5" max="50" value="{{ fitnessParticipantCount }}" sc-camel-on-change="{{ onFitnessCount }}" aria-label="Participant count" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><sc-raw-select value="{{ fitnessObjective }}" sc-camel-on-change="{{ onFitnessObjective }}" aria-label="Fitness objective" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="general fitness">General fitness</option><option value="PFT preparation">PFT preparation</option><option value="CFT preparation">CFT preparation</option><option value="strength">Strength</option><option value="endurance">Endurance</option><option value="mobility/recovery">Mobility / recovery</option></sc-raw-select><input type="number" min="20" max="120" value="{{ fitnessDuration }}" sc-camel-on-change="{{ onFitnessDuration }}" aria-label="Duration in minutes" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"></div>\n'
        '              <input value="{{ fitnessLocation }}" sc-camel-on-change="{{ onFitnessLocation }}" placeholder="Location" aria-label="PT location" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ fitnessEquipment }}" sc-camel-on-change="{{ onFitnessEquipment }}" placeholder="Equipment, comma-separated" aria-label="Available equipment" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ fitnessAbilityNotes }}" sc-camel-on-change="{{ onFitnessAbility }}" placeholder="Ability and limitation notes" aria-label="Ability and limitation notes" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ fitnessWeatherNotes }}" sc-camel-on-change="{{ onFitnessWeather }}" placeholder="Current weather and site conditions" aria-label="Weather and site conditions" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ fitnessCadencePreference }}" sc-camel-on-change="{{ onFitnessCadencePreference }}" placeholder="Cadence preference (optional)" aria-label="Cadence preference" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;">\n'
        '              <label style="display:flex;gap:7px;align-items:center;color:#c7cfd8;font-size:0.78rem;"><input type="checkbox" checked="{{ fitnessIncludeCadence }}" sc-camel-on-change="{{ onFitnessIncludeCadence }}"> Ask about and include cadence</label><button type="submit" style="height:34px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:700;cursor:pointer;">Build staff-reviewed plan</button><span aria-live="polite" style="color:#8a94a0;font-size:0.74rem;">{{ fitnessStatus }}</span>\n'
        "            </form>\n"
        '            <div style="display:grid;gap:8px;align-content:start;"><strong style="font-size:0.82rem;">Plan output <span style="color:#8a94a0;font-weight:400;">{{ fitnessPlanBand }}</span></strong><sc-if value="{{ fitnessPlanVisible }}" hint-placeholder-val="{{ false }}"><sc-for list="{{ fitnessPlanBlocks }}" as="item" hint-placeholder-count="3"><div style="padding:8px;border:1px solid #313844;border-radius:6px;background:#0d1014;"><strong style="font-size:0.76rem;">{{ item.title }}</strong><span style="display:block;color:#8a94a0;font-size:0.7rem;margin-top:3px;">{{ item.text }}</span></div></sc-for><details><summary style="cursor:pointer;font-size:0.76rem;font-weight:700;">Staff reviews and ORM</summary><div style="display:grid;gap:6px;margin-top:7px;"><sc-for list="{{ fitnessStaffReviews }}" as="item" hint-placeholder-count="4"><div><strong style="font-size:0.72rem;">{{ item.title }}</strong><span style="display:block;color:#8a94a0;font-size:0.68rem;">{{ item.text }}</span></div></sc-for><sc-for list="{{ fitnessOrmHazards }}" as="item" hint-placeholder-count="3"><div><strong style="font-size:0.72rem;color:#d6bd7a;">{{ item.title }}</strong><span style="display:block;color:#8a94a0;font-size:0.68rem;">{{ item.text }}</span></div></sc-for></div></details><sc-for list="{{ fitnessWarnings }}" as="warning" hint-placeholder-count="1"><span style="color:#d6bd7a;font-size:0.68rem;">{{ warning.text }}</span></sc-for></sc-if></div>\n'
        "          </div>\n"
        '          <details><summary style="cursor:pointer;font-size:0.82rem;font-weight:700;">Cadence library and private cadences</summary><div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:10px;"><div style="display:grid;gap:7px;align-content:start;"><label style="display:flex;gap:7px;align-items:center;color:#c7cfd8;font-size:0.76rem;"><input type="checkbox" checked="{{ cadenceIncludeAdult }}" sc-camel-on-change="{{ onCadenceAdultFilter }}"> Show my adult-labeled cadences</label><sc-for list="{{ cadenceRecords }}" as="item" hint-placeholder-count="3"><details style="padding:8px;border:1px solid #313844;border-radius:6px;background:#0d1014;"><summary style="cursor:pointer;font-size:0.76rem;font-weight:600;">{{ item.title }} <span style="color:#8a94a0;font-weight:400;">{{ item.meta }}</span></summary><pre style="white-space:pre-wrap;margin:7px 0 0;color:#c7cfd8;font:inherit;font-size:0.7rem;">{{ item.text }}</pre></details></sc-for><sc-if value="{{ cadenceRecordsEmpty }}" hint-placeholder-val="{{ false }}"><span style="color:#8a94a0;font-size:0.74rem;">No cadences available.</span></sc-if></div><form sc-camel-on-submit="{{ onAddPrivateCadence }}" style="display:grid;gap:7px;align-content:start;"><input value="{{ cadenceTitle }}" sc-camel-on-change="{{ onCadenceTitle }}" placeholder="Cadence title" aria-label="Cadence title" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><textarea value="{{ cadenceText }}" sc-camel-on-change="{{ onCadenceText }}" placeholder="Call and response" aria-label="Cadence text" style="min-height:100px;border:1px solid #313844;border-radius:6px;padding:8px;background:#0d1014;color:#eef2f6;font:inherit;"></textarea><label style="display:flex;gap:7px;align-items:center;color:#c7cfd8;font-size:0.76rem;"><input type="checkbox" checked="{{ cadenceAdult }}" sc-camel-on-change="{{ onCadenceAdult }}"> Label adult (still excludes slurs, harassment, hazing, sexual violence, and targeted degradation)</label><button type="submit" style="height:32px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;cursor:pointer;">Save private cadence</button><span aria-live="polite" style="color:#8a94a0;font-size:0.72rem;">{{ cadenceStatus }}</span></form></div></details>\n'
        "        </section>\n\n"
        "        </sc-if>\n"
        '        <sc-if value="{{ isFitreps }}" hint-placeholder-val="{{ false }}">\n',
    ),
    (
        "family readiness: add persistent event state",
        "    familyReadinessEvents: [],\n",
        '    gtccCheckNotes: "",\n    benchCards: [\n',
        '    gtccCheckNotes: "",\n'
        "    familyReadinessEvents: [],\n"
        "    familyReadinessOpen: false,\n"
        "    activeFamilyReadinessId: null,\n"
        '    familyReadinessStatus: "",\n'
        '    familyReadinessDraftTitle: "",\n'
        '    familyReadinessDraftStart: "",\n'
        '    familyReadinessDraftEnd: "",\n'
        '    familyContactRole: "",\n'
        '    familyContactOrganization: "",\n'
        '    familyContactPhone: "",\n'
        '    familyContactEmail: "",\n'
        "    benchCards: [\n",
    ),
    (
        "family readiness: load events on mount",
        "    this._loadFamilyReadiness();\n",
        "    this._loadTravelCases();\n    this._loadRealNotes();\n",
        "    this._loadTravelCases();\n    this._loadFamilyReadiness();\n    this._loadRealNotes();\n",
    ),
    (
        "family readiness: reload events when demo mode switches",
        "    this._loadFamilyReadiness();\n    this._loadFitrepAnalytics();\n",
        "    this._loadTravelCases();\n    this._loadFitrepAnalytics();\n",
        "    this._loadTravelCases();\n    this._loadFamilyReadiness();\n    this._loadFitrepAnalytics();\n",
    ),
    (
        "family readiness: add API actions",
        "  async _loadFamilyReadiness() {",
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
        "  async _loadFamilyReadiness() {\n"
        "    if (!this.userKey) this.userKey = this._resolveUserKey();\n"
        "    try {\n"
        '      const res = await fetch("/family-readiness/" + encodeURIComponent(this.userKey), { headers: this._apiHeaders() });\n'
        '      if (!res.ok) throw new Error("load failed");\n'
        "      const data = await res.json();\n"
        "      const records = (data.records || []).filter((item) => this.state.demoMode || !item.is_demo);\n"
        '      this.setState((s) => ({ familyReadinessEvents: records, activeFamilyReadinessId: records.some((item) => item.event_id === s.activeFamilyReadinessId) ? s.activeFamilyReadinessId : (records[0] ? records[0].event_id : null), familyReadinessStatus: records.length ? "" : "Create a named event to begin." }));\n'
        '    } catch (_) { this.setState({ familyReadinessStatus: "Family readiness events could not be loaded." }); }\n'
        "  }\n"
        "  openFamilyReadiness() { this.setState({ familyReadinessOpen: true }); }\n"
        "  closeFamilyReadiness() { this.setState({ familyReadinessOpen: false }); }\n"
        "  async createFamilyReadiness(e) {\n"
        '    e.preventDefault(); const title = (this.state.familyReadinessDraftTitle || "").trim(); if (!title) return;\n'
        '    this.setState({ familyReadinessStatus: "Building checklist…" });\n'
        "    const body = { user_key: this.userKey, title, approximate_start: this.state.familyReadinessDraftStart || null, approximate_end: this.state.familyReadinessDraftEnd || null, is_demo: false };\n"
        '    try { const res = await fetch("/family-readiness/" + encodeURIComponent(this.userKey), { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(body) }); if (!res.ok) throw new Error("create failed"); const record = await res.json(); this.setState((s) => ({ familyReadinessEvents: [record, ...s.familyReadinessEvents], activeFamilyReadinessId: record.event_id, familyReadinessDraftTitle: "", familyReadinessDraftStart: "", familyReadinessDraftEnd: "", familyReadinessStatus: "Checklist saved locally." })); } catch (_) { this.setState({ familyReadinessStatus: "Could not create the event. Check the dates and try again." }); }\n'
        "  }\n"
        "  selectFamilyReadiness(e) { this.setState({ activeFamilyReadinessId: e.target.value || null }); }\n"
        "  async toggleFamilyReadinessItem(itemId, complete) {\n"
        "    const eventId = this.state.activeFamilyReadinessId; if (!eventId) return;\n"
        '    try { const res = await fetch("/family-readiness/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(eventId) + "/items/" + encodeURIComponent(itemId), { method: "PATCH", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ status: complete ? "not_started" : "complete" }) }); if (!res.ok) throw new Error("update failed"); const record = await res.json(); this.setState((s) => ({ familyReadinessEvents: s.familyReadinessEvents.map((item) => item.event_id === record.event_id ? record : item), familyReadinessStatus: "Progress saved locally." })); } catch (_) { this.setState({ familyReadinessStatus: "Could not save that checklist change." }); }\n'
        "  }\n"
        "  async addFamilyReadinessContact(e) {\n"
        '    e.preventDefault(); const eventId = this.state.activeFamilyReadinessId; const role = (this.state.familyContactRole || "").trim(); if (!eventId || !role) return;\n'
        '    const body = { role, organization: this.state.familyContactOrganization || "", phone: this.state.familyContactPhone || "", email: this.state.familyContactEmail || "", shareable: true };\n'
        '    try { const res = await fetch("/family-readiness/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(eventId) + "/contacts", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(body) }); if (!res.ok) throw new Error("contact failed"); const record = await res.json(); this.setState((s) => ({ familyReadinessEvents: s.familyReadinessEvents.map((item) => item.event_id === record.event_id ? record : item), familyContactRole: "", familyContactOrganization: "", familyContactPhone: "", familyContactEmail: "", familyReadinessStatus: "Contact saved locally." })); } catch (_) { this.setState({ familyReadinessStatus: "Could not save the contact." }); }\n'
        "  }\n"
        "  async downloadFamilyReadinessCalendar() {\n"
        "    const eventId = this.state.activeFamilyReadinessId; if (!eventId) return;\n"
        '    try { const res = await fetch("/family-readiness/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(eventId) + "/ics", { headers: this._apiHeaders() }); if (!res.ok) throw new Error("calendar failed"); const blob = await res.blob(); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = "family-readiness-" + eventId + ".ics"; link.click(); URL.revokeObjectURL(url); this.setState({ familyReadinessStatus: "Generic calendar downloaded." }); } catch (_) { this.setState({ familyReadinessStatus: "Could not download the calendar." }); }\n'
        "  }\n"
        "  async generateFamilyReadinessSummary() {\n"
        '    const eventId = this.state.activeFamilyReadinessId; if (!eventId) return; this.setState({ familyReadinessStatus: "Generating spouse-friendly summary…" });\n'
        '    try { const res = await fetch("/family-readiness/" + encodeURIComponent(this.userKey) + "/" + encodeURIComponent(eventId) + "/summary", { method: "POST", headers: this._apiHeaders({ "Content-Type": "application/json" }), body: JSON.stringify({ user_key: this.userKey }) }); if (!res.ok) throw new Error("summary failed"); this.setState({ familyReadinessStatus: "Summary saved in Personal files → Generations." }); } catch (_) { this.setState({ familyReadinessStatus: "Could not generate the summary." }); }\n'
        "  }\n"
        '  openFamilyReadinessAgent() { this.setState({ familyReadinessOpen: false, lane: "ai", aiTab: "agents", agentCategoryFilter: "Reserve Admin & Readiness" }); }\n'
        "\n"
        "  go(lane) { return () => this.setState({ lane, benchModal: null, profileOpen: false }); }\n",
    ),
    (
        "family readiness: add bottom Bench tile",
        '{ kind: "Readiness", title: "Family & Deployment Readiness",',
        '      { kind: "Planning", title: "Lone planner mode", desc: "Thin-staff assist — what you\'re likely missing when covering multiple lanes alone.", output: "Walk-in brief", templateType: "brief" },\n'
        "    ].map((w) => ({ ...w, onOpen: this.createWorkflowDoc(w) }));\n",
        '      { kind: "Planning", title: "Lone planner mode", desc: "Thin-staff assist — what you\'re likely missing when covering multiple lanes alone.", output: "Walk-in brief", templateType: "brief" },\n'
        '      { kind: "Readiness", title: "Family & Deployment Readiness", desc: "Saved per named event: deployment prep, DEERS links, contacts, spouse-friendly terms, and a rough milestone calendar.", output: "Checklist + summary", templateType: "family_readiness" },\n'
        '    ].map((w) => ({ ...w, onOpen: w.templateType === "family_readiness" ? () => this.openFamilyReadiness() : this.createWorkflowDoc(w) }));\n',
    ),
    (
        "family readiness: compute and expose view bindings",
        "    const familyReadinessActive = this.state.familyReadinessEvents.find((item) => item.event_id === this.state.activeFamilyReadinessId) || null;\n",
        "    const workflows = [\n",
        "    const familyReadinessActive = this.state.familyReadinessEvents.find((item) => item.event_id === this.state.activeFamilyReadinessId) || null;\n"
        '    const familyReadinessEventOptions = this.state.familyReadinessEvents.map((item) => ({ value: item.event_id, label: item.title + " · " + item.status }));\n'
        '    const familyReadinessItems = familyReadinessActive ? (familyReadinessActive.items || []).map((item) => ({ ...item, complete: item.status === "complete", onToggle: () => this.toggleFamilyReadinessItem(item.item_id, item.status === "complete"), sourceVisible: !!item.source_url })) : [];\n'
        '    const familyReadinessContacts = familyReadinessActive ? (familyReadinessActive.contacts || []).map((item) => ({ ...item, detail: [item.organization, item.phone, item.email].filter(Boolean).join(" · ") || "No details yet" })) : [];\n'
        '    const familyReadinessGlossary = familyReadinessActive ? (familyReadinessActive.glossary || []).map((item) => ({ term: item.term + " — " + item.expansion, plain_language: item.plain_language })) : [];\n'
        '    const familyReadinessMilestones = familyReadinessActive ? (familyReadinessActive.milestones || []).map((item) => ({ label: item.label + " · " + item.target_date, title: item.title })) : [];\n'
        "    const familyReadinessComplete = familyReadinessItems.filter((item) => item.complete).length;\n"
        "\n"
        "    const workflows = [\n",
    ),
    (
        "family readiness: expose view values",
        "      familyReadinessOpen: this.state.familyReadinessOpen, familyReadinessHasActive: !!familyReadinessActive,\n",
        "      benchCards, benchCardsGrid, projectFilesCard, workflows,\n",
        "      benchCards, benchCardsGrid, projectFilesCard, workflows,\n"
        "      familyReadinessOpen: this.state.familyReadinessOpen, familyReadinessHasActive: !!familyReadinessActive,\n"
        '      familyReadinessEventOptions, activeFamilyReadinessId: this.state.activeFamilyReadinessId || "", onSelectFamilyReadiness: (e) => this.selectFamilyReadiness(e),\n'
        '      familyReadinessTitle: familyReadinessActive ? familyReadinessActive.title : "", familyReadinessDateRange: familyReadinessActive ? [familyReadinessActive.approximate_start, familyReadinessActive.approximate_end].filter(Boolean).join(" → ") : "", familyReadinessProgress: familyReadinessItems.length ? familyReadinessComplete + " / " + familyReadinessItems.length + " complete" : "No checklist selected",\n'
        "      familyReadinessItems, familyReadinessContacts, familyReadinessGlossary, familyReadinessMilestones, familyReadinessStatus: this.state.familyReadinessStatus,\n"
        "      familyReadinessDraftTitle: this.state.familyReadinessDraftTitle, familyReadinessDraftStart: this.state.familyReadinessDraftStart, familyReadinessDraftEnd: this.state.familyReadinessDraftEnd,\n"
        "      onFamilyDraftTitle: (e) => this.setState({ familyReadinessDraftTitle: e.target.value }), onFamilyDraftStart: (e) => this.setState({ familyReadinessDraftStart: e.target.value }), onFamilyDraftEnd: (e) => this.setState({ familyReadinessDraftEnd: e.target.value }), onCreateFamilyReadiness: (e) => this.createFamilyReadiness(e),\n"
        "      familyContactRole: this.state.familyContactRole, familyContactOrganization: this.state.familyContactOrganization, familyContactPhone: this.state.familyContactPhone, familyContactEmail: this.state.familyContactEmail, onFamilyContactRole: (e) => this.setState({ familyContactRole: e.target.value }), onFamilyContactOrganization: (e) => this.setState({ familyContactOrganization: e.target.value }), onFamilyContactPhone: (e) => this.setState({ familyContactPhone: e.target.value }), onFamilyContactEmail: (e) => this.setState({ familyContactEmail: e.target.value }), onAddFamilyContact: (e) => this.addFamilyReadinessContact(e),\n"
        "      closeFamilyReadiness: () => this.closeFamilyReadiness(), downloadFamilyReadinessCalendar: () => this.downloadFamilyReadinessCalendar(), generateFamilyReadinessSummary: () => this.generateFamilyReadinessSummary(), openFamilyReadinessAgent: () => this.openFamilyReadinessAgent(),\n",
    ),
    (
        "family readiness: render named-event editor",
        '<h3 style="margin:0;font-size:1.06rem;font-weight:700;">Family &amp; Deployment Readiness</h3>',
        "    <!-- ==================== BENCH ITEM MODAL ==================== -->\n",
        "    <!-- ==================== FAMILY READINESS MODAL ==================== -->\n"
        '    <sc-if value="{{ familyReadinessOpen }}" hint-placeholder-val="{{ false }}">\n'
        '    <div style="position:fixed;inset:0;z-index:45;background:rgba(0,0,0,0.7);display:flex;align-items:center;justify-content:center;padding:20px;" sc-camel-on-click="{{ closeFamilyReadiness }}">\n'
        '      <section sc-camel-on-click="{{ stopClickPropagation }}" role="dialog" aria-modal="true" aria-label="Family and Deployment Readiness" style="width:min(1120px,96vw);max-height:92vh;overflow:auto;border:1px solid #313844;border-radius:8px;background:#12161b;box-shadow:0 24px 60px rgba(0,0,0,0.55);padding:20px;display:grid;gap:16px;">\n'
        '        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;"><div><h3 style="margin:0;font-size:1.06rem;font-weight:700;">Family &amp; Deployment Readiness</h3><p style="margin:5px 0 0;color:#8a94a0;font-size:0.8rem;line-height:1.45;">Saved per named event, from an extended AT through a year overseas. UNCLASSIFIED only; avoid sensitive travel or operational details.</p></div><button type="button" sc-camel-on-click="{{ closeFamilyReadiness }}" aria-label="Close family readiness" style="background:transparent;border:0;color:#8a94a0;font-size:1.1rem;cursor:pointer;">✕</button></div>\n'
        '        <div style="display:grid;grid-template-columns:minmax(250px,0.75fr) minmax(0,2fr);gap:16px;">\n'
        '          <aside style="display:grid;gap:12px;align-content:start;"><label style="display:grid;gap:5px;font-size:0.78rem;font-weight:600;">Saved event<sc-raw-select value="{{ activeFamilyReadinessId }}" sc-camel-on-change="{{ onSelectFamilyReadiness }}" style="height:36px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#0d1014;color:#eef2f6;font:inherit;"><option value="">Choose an event…</option><sc-for list="{{ familyReadinessEventOptions }}" as="option" hint-placeholder-count="2"><option value="{{ option.value }}">{{ option.label }}</option></sc-for></sc-raw-select></label>\n'
        '            <form sc-camel-on-submit="{{ onCreateFamilyReadiness }}" style="display:grid;gap:7px;padding:12px;border:1px solid #313844;border-radius:6px;background:#0d1014;"><strong style="font-size:0.8rem;">Start a named event</strong><input required value="{{ familyReadinessDraftTitle }}" sc-camel-on-change="{{ onFamilyDraftTitle }}" placeholder="e.g. Overseas rotation 2027" aria-label="Event title" style="height:34px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#12161b;color:#eef2f6;font:inherit;"><label style="font-size:0.7rem;color:#8a94a0;">Approximate start<input type="date" value="{{ familyReadinessDraftStart }}" sc-camel-on-change="{{ onFamilyDraftStart }}" style="width:100%;height:34px;margin-top:4px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#12161b;color:#eef2f6;font:inherit;"></label><label style="font-size:0.7rem;color:#8a94a0;">Approximate end<input type="date" value="{{ familyReadinessDraftEnd }}" sc-camel-on-change="{{ onFamilyDraftEnd }}" style="width:100%;height:34px;margin-top:4px;border:1px solid #313844;border-radius:6px;padding:0 8px;background:#12161b;color:#eef2f6;font:inherit;"></label><button type="submit" style="height:34px;border:1px solid #b21f2d;border-radius:6px;background:#b21f2d;color:#f5ebe9;font:inherit;font-weight:700;cursor:pointer;">Build checklist</button></form>\n'
        '            <div style="display:grid;gap:6px;"><a href="https://www.tricare.mil/Plans/Eligibility/DEERS" target="_blank" rel="noopener" style="color:#7db2e0;font-size:0.78rem;">Open DEERS / TRICARE ↗</a><a href="https://milconnect.dmdc.osd.mil/milconnect/" target="_blank" rel="noopener" style="color:#7db2e0;font-size:0.78rem;">Open milConnect ↗</a><a href="https://idco.dmdc.osd.mil/idco/" target="_blank" rel="noopener" style="color:#7db2e0;font-size:0.78rem;">Find a RAPIDS office ↗</a><a href="https://www.militaryonesource.mil/deployment/" target="_blank" rel="noopener" style="color:#7db2e0;font-size:0.78rem;">Military OneSource deployment help ↗</a></div>\n'
        "          </aside>\n"
        '          <main style="display:grid;gap:14px;align-content:start;"><sc-if value="{{ familyReadinessHasActive }}" hint-placeholder-val="{{ false }}"><div><h4 style="margin:0;font-size:1rem;">{{ familyReadinessTitle }}</h4><p style="margin:4px 0 0;color:#8a94a0;font-size:0.76rem;">{{ familyReadinessDateRange }} · {{ familyReadinessProgress }}</p></div>\n'
        '            <div style="display:flex;gap:8px;flex-wrap:wrap;"><button type="button" sc-camel-on-click="{{ downloadFamilyReadinessCalendar }}" style="height:32px;padding:0 10px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-size:0.76rem;font-weight:600;cursor:pointer;">Download generic calendar</button><button type="button" sc-camel-on-click="{{ generateFamilyReadinessSummary }}" style="height:32px;padding:0 10px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-size:0.76rem;font-weight:600;cursor:pointer;">Generate spouse-friendly summary</button><button type="button" sc-camel-on-click="{{ openFamilyReadinessAgent }}" style="height:32px;padding:0 10px;border:1px solid #b21f2d;border-radius:6px;background:#1b1114;color:#eef2f6;font:inherit;font-size:0.76rem;font-weight:600;cursor:pointer;">Open readiness agent</button></div>\n'
        '            <section><strong style="font-size:0.82rem;">Checklist</strong><div style="display:grid;gap:7px;margin-top:8px;"><sc-for list="{{ familyReadinessItems }}" as="item" hint-placeholder-count="6"><label style="display:grid;grid-template-columns:auto 1fr;gap:8px;padding:9px;border:1px solid #313844;border-radius:6px;background:#0d1014;"><input type="checkbox" checked="{{ item.complete }}" sc-camel-on-change="{{ item.onToggle }}"><span><strong style="display:block;font-size:0.76rem;">{{ item.task }}</strong><span style="display:block;color:#8a94a0;font-size:0.7rem;line-height:1.4;">{{ item.plain_language }}</span><sc-if value="{{ item.sourceVisible }}" hint-placeholder-val="{{ false }}"><a href="{{ item.source_url }}" target="_blank" rel="noopener" style="color:#7db2e0;font-size:0.68rem;">Official source ↗</a></sc-if></span></label></sc-for></div></section>\n'
        '            <section style="display:grid;grid-template-columns:1fr 1fr;gap:12px;"><div><strong style="font-size:0.82rem;">Rough milestone calendar</strong><div style="display:grid;gap:6px;margin-top:7px;"><sc-for list="{{ familyReadinessMilestones }}" as="item" hint-placeholder-count="4"><div style="padding:7px;border-left:2px solid #b21f2d;"><strong style="font-size:0.72rem;">{{ item.label }}</strong><span style="display:block;color:#8a94a0;font-size:0.68rem;">{{ item.title }}</span></div></sc-for></div></div><div><strong style="font-size:0.82rem;">Spouse-friendly glossary</strong><div style="display:grid;gap:6px;margin-top:7px;"><sc-for list="{{ familyReadinessGlossary }}" as="item" hint-placeholder-count="4"><details><summary style="cursor:pointer;font-size:0.72rem;font-weight:600;">{{ item.term }}</summary><span style="display:block;color:#8a94a0;font-size:0.68rem;padding-top:3px;">{{ item.plain_language }}</span></details></sc-for></div></div></section>\n'
        '            <section><strong style="font-size:0.82rem;">Unit and public contacts</strong><div style="display:grid;gap:5px;margin:7px 0;"><sc-for list="{{ familyReadinessContacts }}" as="item" hint-placeholder-count="2"><div style="font-size:0.72rem;"><strong>{{ item.role }}</strong><span style="display:block;color:#8a94a0;">{{ item.detail }}</span></div></sc-for></div><form sc-camel-on-submit="{{ onAddFamilyContact }}" style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr auto;gap:6px;"><input required value="{{ familyContactRole }}" sc-camel-on-change="{{ onFamilyContactRole }}" placeholder="Role" aria-label="Contact role" style="height:32px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ familyContactOrganization }}" sc-camel-on-change="{{ onFamilyContactOrganization }}" placeholder="Organization" aria-label="Contact organization" style="height:32px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"><input value="{{ familyContactPhone }}" sc-camel-on-change="{{ onFamilyContactPhone }}" placeholder="Phone" aria-label="Contact phone" style="height:32px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"><input type="email" value="{{ familyContactEmail }}" sc-camel-on-change="{{ onFamilyContactEmail }}" placeholder="Email" aria-label="Contact email" style="height:32px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"><button type="submit" style="height:32px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;cursor:pointer;">Add</button></form></section>\n'
        '            <p style="margin:0;padding-top:10px;border-top:1px solid #313844;color:#d6bd7a;font-size:0.72rem;line-height:1.45;">The family-deployment-readiness-advisor provides preparation guidance and official links; it does not create legal documents or replace legal assistance. DRAFT — Verify all references against current official sources before acting.</p></sc-if><span aria-live="polite" style="color:#8a94a0;font-size:0.74rem;">{{ familyReadinessStatus }}</span></main>\n'
        "        </div>\n"
        "      </section>\n"
        "    </div>\n"
        "    </sc-if>\n\n"
        "    <!-- ==================== BENCH ITEM MODAL ==================== -->\n",
    ),
    (
        "career opportunities: add Watch state",
        "    careerOpportunityRecords: [],\n",
        '    realSourceUpdates: [],\n    repoRootPath: "",\n',
        "    realSourceUpdates: [],\n"
        "    careerOpportunityRecords: [],\n"
        "    careerOpportunitySources: [],\n"
        '    careerOpportunityStatus: "",\n'
        "    careerOpportunitySourceStatus: {},\n"
        '    careerOpportunitySort: "published_at",\n'
        '    careerOpportunityDirection: "descending",\n'
        '    careerOpportunityType: "",\n'
        '    careerOpportunityRank: "",\n'
        '    careerOpportunityMos: "",\n'
        '    careerOpportunityLocation: "",\n'
        '    careerOpportunityKeyword: "",\n'
        '    repoRootPath: "",\n',
    ),
    (
        "career opportunities: load Watch data on mount",
        "    this._loadCareerOpportunities();\n",
        "    this._loadRealFeeds();\n    this._loadRealLinks();\n",
        "    this._loadRealFeeds();\n    this._loadCareerOpportunities();\n    this._loadRealLinks();\n",
    ),
    (
        "career opportunities: add query and independent refresh actions",
        "  async _loadCareerOpportunities() {",
        "  async _loadFamilyReadiness() {\n",
        "  async _loadCareerOpportunities() {\n"
        "    const params = new URLSearchParams();\n"
        '    params.set("sort_by", this.state.careerOpportunitySort || "source_order"); params.set("direction", this.state.careerOpportunityDirection || "ascending");\n'
        '    if (this.state.careerOpportunityType) params.append("opportunity_type", this.state.careerOpportunityType);\n'
        '    if (this.state.careerOpportunityRank) params.set("rank", this.state.careerOpportunityRank);\n'
        '    if (this.state.careerOpportunityMos) params.set("mos", this.state.careerOpportunityMos);\n'
        '    if (this.state.careerOpportunityLocation) params.set("location", this.state.careerOpportunityLocation);\n'
        '    if (this.state.careerOpportunityKeyword) params.set("keyword", this.state.careerOpportunityKeyword);\n'
        '    try { const res = await fetch("/career-opportunities?" + params.toString(), { headers: this._apiHeaders() }); if (!res.ok) throw new Error("load failed"); const data = await res.json(); this.setState({ careerOpportunityRecords: data.records || [], careerOpportunitySources: data.sources || [], careerOpportunityStatus: (data.records || []).length ? "" : "No structured listings are cached. Refresh or open an official source." }); } catch (_) { this.setState({ careerOpportunityStatus: "Career opportunities could not be loaded. Open an official source below." }); }\n'
        "  }\n"
        "  async refreshCareerOpportunities() {\n"
        '    this.setState({ careerOpportunityStatus: "Refreshing both official sources…" });\n'
        '    try { const res = await fetch("/career-opportunities/refresh", { method: "POST", headers: this._apiHeaders() }); if (!res.ok) throw new Error("refresh failed"); await this._loadCareerOpportunities(); this.setState({ careerOpportunityStatus: "Refresh finished. Verify availability at the official listing." }); } catch (_) { this.setState({ careerOpportunityStatus: "Refresh failed. Cached results, if available, remain below." }); await this._loadCareerOpportunities(); }\n'
        "  }\n"
        "  async refreshCareerOpportunitySource(sourceKey) {\n"
        '    this.setState((s) => ({ careerOpportunitySourceStatus: { ...s.careerOpportunitySourceStatus, [sourceKey]: "Refreshing…" } }));\n'
        '    try { const res = await fetch("/career-opportunities/sources/" + encodeURIComponent(sourceKey) + "/refresh", { method: "POST", headers: this._apiHeaders() }); if (!res.ok) throw new Error("refresh failed"); const state = await res.json(); const label = state.outcome === "failed_cached" ? "Failed · cached" : state.outcome === "failed_no_cache" ? "Failed" : state.outcome === "link_only" ? "Source available" : "Updated"; this.setState((s) => ({ careerOpportunitySourceStatus: { ...s.careerOpportunitySourceStatus, [sourceKey]: label } })); await this._loadCareerOpportunities(); } catch (_) { this.setState((s) => ({ careerOpportunitySourceStatus: { ...s.careerOpportunitySourceStatus, [sourceKey]: "Failed" } })); await this._loadCareerOpportunities(); }\n'
        "  }\n"
        "  changeCareerOpportunityQuery(update) { this.setState(update, () => this._loadCareerOpportunities()); }\n"
        '  clearCareerOpportunityFilters() { this.setState({ careerOpportunityType: "", careerOpportunityRank: "", careerOpportunityMos: "", careerOpportunityLocation: "", careerOpportunityKeyword: "", careerOpportunitySort: "published_at", careerOpportunityDirection: "descending" }, () => this._loadCareerOpportunities()); }\n'
        "\n"
        "  async _loadFamilyReadiness() {\n",
    ),
    (
        "career opportunities: compute source, filter, and row bindings",
        "    const careerOpportunitySources = (this.state.careerOpportunitySources || []).map((state) => {\n",
        '    const toggleAddFeed = () => this.setState((s) => ({ addFeedOpen: !s.addFeedOpen, draftFeedName: "", draftFeedMeta: "", draftFeedUrl: "", draftFeedType: "rss", draftFeedTrust: "Unit" }));\n',
        "    const careerOpportunitySources = (this.state.careerOpportunitySources || []).map((state) => {\n"
        '      const sourceKey = state.source.key; const cached = state.outcome === "failed_cached"; const failed = state.outcome === "failed_no_cache"; const linkOnly = state.outcome === "link_only"; const rowStatus = (this.state.careerOpportunitySourceStatus || {})[sourceKey] || "";\n'
        '      const checked = state.last_checked_at ? new Date(state.last_checked_at).toLocaleString() : "Not checked yet";\n'
        '      return { key: sourceKey, name: state.source.name, url: state.source.url, countLabel: (state.records || []).length + " structured listing" + ((state.records || []).length === 1 ? "" : "s"), checkedLabel: "Checked " + checked, statusLabel: rowStatus || (cached ? "Showing cached results" : failed ? "Refresh failed" : linkOnly ? "Official source link" : "Listings refreshed"), stale: cached, warning: (state.warnings || [])[0] || "", refreshing: rowStatus === "Refreshing…", onRefresh: () => this.refreshCareerOpportunitySource(sourceKey) };\n'
        "    });\n"
        '    const careerOpportunityRecords = (this.state.careerOpportunityRecords || []).map((item) => ({ title: item.title, component: String(item.opportunity_type || "other").toUpperCase().replace("_", "/"), rank: item.rank || "Not provided", mos: item.mos || "Not provided", unit: item.unit || "Not provided", location: item.location || "Not provided", duration: item.duration || "Not provided", publishedLabel: item.published_at ? "Published " + formatFeedDate(item.published_at) : "Publication date unavailable", dueLabel: item.due_date ? "Apply by " + formatFeedDate(item.due_date) : "Application date unavailable", url: item.direct_url || item.source_url, sourceName: item.source_name || "Official source", description: item.description || item.notes || "Open the official listing for current duties, eligibility, and application details." }));\n'
        '    const careerOpportunitySortOptions = [{ value: "title", label: "Title" }, { value: "opportunity_type", label: "Component" }, { value: "rank", label: "Rank" }, { value: "mos", label: "MOS" }, { value: "unit", label: "Unit" }, { value: "location", label: "Location" }, { value: "duration", label: "Duration" }, { value: "published_at", label: "Publication date" }, { value: "due_date", label: "Application / due date" }];\n'
        '    const careerOpportunityTypeOptions = [{ value: "", label: "All components" }, { value: "smcr", label: "SMCR" }, { value: "ima", label: "IMA" }, { value: "ados", label: "ADOS" }, { value: "ia_jia", label: "IA/JIA" }, { value: "other", label: "Other / unknown" }];\n'
        '    const careerOpportunityDirectionOptions = [{ value: "ascending", label: "Ascending" }, { value: "descending", label: "Descending" }];\n'
        '    const careerOpportunitySortFallback = this.state.careerOpportunitySort === "published_at" && !careerOpportunityRecords.some((item) => item.publishedLabel.indexOf("Published ") === 0) ? "No publication dates supplied; preserving source order." : "";\n'
        '    const toggleAddFeed = () => this.setState((s) => ({ addFeedOpen: !s.addFeedOpen, draftFeedName: "", draftFeedMeta: "", draftFeedUrl: "", draftFeedType: "rss", draftFeedTrust: "Unit" }));\n',
    ),
    (
        "career opportunities: expose Watch values",
        "      careerOpportunitySources, careerOpportunityRecords, careerOpportunityRecordsEmpty: careerOpportunityRecords.length === 0,\n",
        "      actNow, maradmins, navadmins, feeds, actions, srcUpdates, srcUpdatesEmpty,\n",
        "      actNow, maradmins, navadmins, feeds, actions, srcUpdates, srcUpdatesEmpty,\n"
        "      careerOpportunitySources, careerOpportunityRecords, careerOpportunityRecordsEmpty: careerOpportunityRecords.length === 0,\n"
        "      careerOpportunityStatus: this.state.careerOpportunityStatus, careerOpportunitySortFallback, careerOpportunitySortOptions, careerOpportunityTypeOptions, careerOpportunityDirectionOptions, careerOpportunitySort: this.state.careerOpportunitySort, careerOpportunityDirection: this.state.careerOpportunityDirection, careerOpportunityType: this.state.careerOpportunityType, careerOpportunityRank: this.state.careerOpportunityRank, careerOpportunityMos: this.state.careerOpportunityMos, careerOpportunityLocation: this.state.careerOpportunityLocation, careerOpportunityKeyword: this.state.careerOpportunityKeyword,\n"
        "      refreshCareerOpportunities: () => this.refreshCareerOpportunities(), clearCareerOpportunityFilters: () => this.clearCareerOpportunityFilters(), onCareerOpportunitySort: (e) => this.changeCareerOpportunityQuery({ careerOpportunitySort: e.target.value }), onCareerOpportunityDirection: (e) => this.changeCareerOpportunityQuery({ careerOpportunityDirection: e.target.value }), onCareerOpportunityType: (e) => this.changeCareerOpportunityQuery({ careerOpportunityType: e.target.value }), onCareerOpportunityRank: (e) => this.setState({ careerOpportunityRank: e.target.value }), onCareerOpportunityMos: (e) => this.setState({ careerOpportunityMos: e.target.value }), onCareerOpportunityLocation: (e) => this.setState({ careerOpportunityLocation: e.target.value }), onCareerOpportunityKeyword: (e) => this.setState({ careerOpportunityKeyword: e.target.value }), applyCareerOpportunityFilters: (e) => { e.preventDefault(); this._loadCareerOpportunities(); },\n",
    ),
    (
        "career opportunities: render sortable Watch widget below Connected feeds",
        '<h3 style="margin:0 0 4px;font-size:1.02rem;font-weight:700;">Career Opportunities</h3>',
        '        <button type="button" sc-camel-on-click="{{ toggleAddFeed }}" style="margin-top:14px;height:34px;padding:0 16px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.84rem;cursor:pointer;">+ Add feed</button>\n'
        "      </section>\n\n"
        '      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">\n',
        '        <button type="button" sc-camel-on-click="{{ toggleAddFeed }}" style="margin-top:14px;height:34px;padding:0 16px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-weight:600;font-size:0.84rem;cursor:pointer;">+ Add feed</button>\n'
        "      </section>\n\n"
        '      <section style="border:1px solid #313844;border-radius:8px;background:#12161b;padding:18px;display:grid;gap:14px;">\n'
        '        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;"><div><h3 style="margin:0 0 4px;font-size:1.02rem;font-weight:700;">Career Opportunities</h3><p style="margin:0;color:#8a94a0;font-size:0.82rem;">SMCR / IMA / ADOS public opportunities from official MARFORRES gateways.</p></div><button type="button" sc-camel-on-click="{{ refreshCareerOpportunities }}" style="height:30px;padding:0 12px;border:1px solid #b21f2d;border-radius:6px;background:#1b1114;color:#eef2f6;font:inherit;font-size:0.76rem;font-weight:700;cursor:pointer;">Refresh all</button></div>\n'
        '        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:8px;"><sc-for list="{{ careerOpportunitySources }}" as="source" hint-placeholder-count="2"><div style="padding:10px;border:1px solid #313844;border-radius:6px;background:#0d1014;display:grid;gap:5px;"><div style="display:flex;justify-content:space-between;gap:8px;"><strong style="font-size:0.78rem;">{{ source.name }}</strong><button type="button" disabled="{{ source.refreshing }}" sc-camel-on-click="{{ source.onRefresh }}" style="height:25px;padding:0 8px;border:1px solid #313844;border-radius:5px;background:#1a2027;color:#c7cfd8;font:inherit;font-size:0.68rem;font-weight:600;cursor:pointer;">Refresh</button></div><span style="color:#8a94a0;font-size:0.68rem;">{{ source.countLabel }} · {{ source.checkedLabel }}</span><span style="color:#d6bd7a;font-size:0.68rem;">{{ source.statusLabel }}</span><sc-if value="{{ source.stale }}" hint-placeholder-val="{{ false }}"><span style="color:#d8a0a5;font-size:0.68rem;">Showing cached results — verify they are still open.</span></sc-if><a href="{{ source.url }}" target="_blank" rel="noopener" style="color:#7db2e0;font-size:0.7rem;">Open official source ↗</a></div></sc-for></div>\n'
        '        <form sc-camel-on-submit="{{ applyCareerOpportunityFilters }}" style="display:grid;grid-template-columns:1.2fr 0.8fr 0.8fr 1fr 1fr 1fr 1.2fr auto;gap:7px;"><label style="font-size:0.68rem;color:#8a94a0;">Sort by<sc-raw-select value="{{ careerOpportunitySort }}" sc-camel-on-change="{{ onCareerOpportunitySort }}" aria-label="Sort Career Opportunities by field" style="display:block;width:100%;height:32px;margin-top:3px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"><sc-for list="{{ careerOpportunitySortOptions }}" as="option" hint-placeholder-count="9"><option value="{{ option.value }}">{{ option.label }}</option></sc-for></sc-raw-select></label><label style="font-size:0.68rem;color:#8a94a0;">Direction<sc-raw-select value="{{ careerOpportunityDirection }}" sc-camel-on-change="{{ onCareerOpportunityDirection }}" aria-label="Career Opportunities sort direction" style="display:block;width:100%;height:32px;margin-top:3px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"><sc-for list="{{ careerOpportunityDirectionOptions }}" as="option" hint-placeholder-count="2"><option value="{{ option.value }}">{{ option.label }}</option></sc-for></sc-raw-select></label><label style="font-size:0.68rem;color:#8a94a0;">Component<sc-raw-select value="{{ careerOpportunityType }}" sc-camel-on-change="{{ onCareerOpportunityType }}" style="display:block;width:100%;height:32px;margin-top:3px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"><sc-for list="{{ careerOpportunityTypeOptions }}" as="option" hint-placeholder-count="6"><option value="{{ option.value }}">{{ option.label }}</option></sc-for></sc-raw-select></label><label style="font-size:0.68rem;color:#8a94a0;">Rank<input value="{{ careerOpportunityRank }}" sc-camel-on-change="{{ onCareerOpportunityRank }}" style="display:block;width:100%;height:32px;margin-top:3px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"></label><label style="font-size:0.68rem;color:#8a94a0;">MOS<input value="{{ careerOpportunityMos }}" sc-camel-on-change="{{ onCareerOpportunityMos }}" style="display:block;width:100%;height:32px;margin-top:3px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"></label><label style="font-size:0.68rem;color:#8a94a0;">Location<input value="{{ careerOpportunityLocation }}" sc-camel-on-change="{{ onCareerOpportunityLocation }}" style="display:block;width:100%;height:32px;margin-top:3px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"></label><label style="font-size:0.68rem;color:#8a94a0;">Keyword<input value="{{ careerOpportunityKeyword }}" sc-camel-on-change="{{ onCareerOpportunityKeyword }}" style="display:block;width:100%;height:32px;margin-top:3px;border:1px solid #313844;border-radius:6px;padding:0 7px;background:#0d1014;color:#eef2f6;font:inherit;"></label><div style="display:flex;align-items:end;gap:5px;"><button type="submit" style="height:32px;padding:0 10px;border:1px solid #313844;border-radius:6px;background:#1a2027;color:#eef2f6;font:inherit;font-size:0.7rem;font-weight:600;cursor:pointer;">Apply</button><button type="button" sc-camel-on-click="{{ clearCareerOpportunityFilters }}" style="height:32px;padding:0 10px;border:0;background:transparent;color:#7db2e0;font:inherit;font-size:0.7rem;cursor:pointer;">Clear filters</button></div></form>\n'
        '        <span aria-live="polite" style="color:#8a94a0;font-size:0.72rem;">{{ careerOpportunityStatus }} {{ careerOpportunitySortFallback }}</span>\n'
        '        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:9px;max-height:520px;overflow:auto;"><sc-if value="{{ careerOpportunityRecordsEmpty }}" hint-placeholder-val="{{ false }}"><div style="padding:12px;border:1px dashed #313844;border-radius:6px;color:#8a94a0;font-size:0.76rem;">No structured listings match. Refresh, clear filters, or open an official source.</div></sc-if><sc-for list="{{ careerOpportunityRecords }}" as="item" hint-placeholder-count="4"><article style="padding:11px;border:1px solid #313844;border-radius:6px;background:#0d1014;display:grid;gap:6px;"><div style="display:flex;justify-content:space-between;gap:8px;"><strong style="font-size:0.8rem;">{{ item.title }}</strong><span style="color:#d6bd7a;font-size:0.66rem;font-weight:700;">{{ item.component }}</span></div><span style="color:#aab4bf;font-size:0.7rem;">Rank {{ item.rank }} · MOS {{ item.mos }}</span><span style="color:#8a94a0;font-size:0.68rem;">{{ item.unit }} · {{ item.location }} · {{ item.duration }}</span><span style="color:#8a94a0;font-size:0.68rem;">{{ item.publishedLabel }} · {{ item.dueLabel }}</span><p style="margin:0;color:#aab4bf;font-size:0.7rem;line-height:1.4;">{{ item.description }}</p><a href="{{ item.url }}" target="_blank" rel="noopener" style="color:#7db2e0;font-size:0.72rem;font-weight:600;">Open official listing ↗</a></article></sc-for></div>\n'
        '        <p style="margin:0;padding-top:9px;border-top:1px solid #313844;color:#d6bd7a;font-size:0.7rem;line-height:1.45;">Availability and eligibility require verification at the official source. The dashboard does not authenticate, apply, or infer missing dates or requirements.</p>\n'
        "      </section>\n\n"
        '      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">\n',
    ),
    (
        "browser identity: keep CRT EGA metadata in the rendered document head",
        "<!-- Browser identity metadata -->",
        '<helmet>\n  <link rel="preconnect" href="https://fonts.googleapis.com">\n',
        "<helmet>\n"
        "  <!-- Browser identity metadata -->\n"
        "  <title>SMCR Staff AI</title>\n"
        '  <link rel="manifest" href="/static/dashboard/manifest.webmanifest">\n'
        '  <link rel="icon" type="image/png" sizes="16x16" href="/static/dashboard/icons/icon-16.png?v=crt-ega-2">\n'
        '  <link rel="icon" type="image/png" sizes="32x32" href="/static/dashboard/icons/icon-32.png?v=crt-ega-2">\n'
        '  <link rel="apple-touch-icon" href="/static/dashboard/icons/icon-192.png">\n'
        '  <meta name="theme-color" content="#0d1014">\n'
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n',
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
