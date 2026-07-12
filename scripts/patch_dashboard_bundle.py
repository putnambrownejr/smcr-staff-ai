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


def apply_patches(inner_html: str, patches: list[tuple[str, str, str]]) -> str:
    for label, old, new in patches:
        count = inner_html.count(old)
        if count == 0:
            raise SystemExit(
                f"Patch {label!r} target text not found -- the bundle was likely "
                "re-exported and this patch needs updating. Aborting without writing."
            )
        if count > 1:
            raise SystemExit(
                f"Patch {label!r} target text matched {count} times (expected 1) -- "
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

PATCHES: list[tuple[str, str, str]] = [
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
        "  _mapRealAction(a) {\n"
        "    return {\n"
        "      id: a.action_id,\n"
        "      title: a.title,\n"
        "      owner: a.owner || \"Unassigned\",\n"
        "      due: a.suspense_date || \"unscheduled\",\n"
        "      done: a.status === \"closed\" || a.status === \"complete\",\n"
        "      notes: a.notes || \"\",\n"
        "      editOpen: false,\n"
        "    };\n"
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
