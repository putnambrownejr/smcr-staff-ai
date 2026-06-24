---
name: verifier-dashboard
description: Launch the smcr-staff-ai server, open the dashboard in a browser, and walk through a verification checklist — overview loads, lanes switch, forms submit, API health, no console errors. Designed to be discovered by the bundled /verify skill as the project's evidence-capture protocol for UI changes.
---

# Verifier: Dashboard — smcr-staff-ai

## Purpose

Standardized evidence-capture protocol for verifying dashboard changes. The bundled `/verify` skill looks for `verifier-*` skills in `.claude/skills/` before falling back to generic behavior — this skill is that hook for any change that touches the dashboard UI.

## When This Fires

The `/verify` skill invokes this when:
- The diff touches `app/static/dashboard/` (JS, HTML, CSS)
- The diff touches API routes that the dashboard consumes
- The diff touches agent registry or council (which feed dashboard dropdowns)
- The user explicitly asks to verify the dashboard

## Setup

### 1. Start the server

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
```

### 2. Wait for healthy

```bash
# Poll until the health endpoint responds
timeout=30
while [ $timeout -gt 0 ]; do
  curl -sf http://localhost:8000/health && break
  sleep 1
  timeout=$((timeout - 1))
done
```

On Windows (PowerShell):
```powershell
$timeout = 30
while ($timeout -gt 0) {
  try { (Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing).StatusCode; break } catch { Start-Sleep 1; $timeout-- }
}
```

### 3. Open the dashboard

Navigate to `http://localhost:8000/dashboard` in a browser (use the Chrome MCP `navigate` tool if available, otherwise open manually).

## Verification Checklist

Walk each item in order. For each, capture evidence (screenshot, response body, or console output).

### Core Health

| # | Check | How | Pass criteria |
|---|---|---|---|
| 1 | API health | `GET /health` | 200, body contains `"status": "ok"` |
| 2 | Dashboard loads | Navigate to `/dashboard` | Page renders without blank screen or JS error |
| 3 | No console errors | Check browser console | No red errors (warnings are acceptable) |

### Lane Navigation

| # | Check | How | Pass criteria |
|---|---|---|---|
| 4 | Overview lane | Click "Overview" tab (or it loads by default) | Readiness strip and Act Now section render |
| 5 | Watch lane | Click "Watch" tab | Lane content appears, no JS error |
| 6 | Bench+Files lane | Click "Bench+Files" tab | Module packs section visible |
| 7 | Workflows lane | Click "Workflows" tab | Lane content appears |
| 8 | Workspace lane | Click "Workspace" tab | Profile section visible |

### Interactive Features (if touched by the diff)

| # | Check | How | Pass criteria |
|---|---|---|---|
| 9 | Quick Links | Workspace → scroll to Quick Links | Seed links render, filter chips toggle, "Add link" form opens |
| 10 | Session Handoff | Workspace → Configure → Session handoff | Form fields render (display name, rank, etc.), Save button works |
| 11 | A Few Good Links | Click "A Few Good Links" tab | Curated military links render (MOL, myPay, MarineNet) |
| 12 | Agent advisor form | Watch lane → Ask an advisor | Dropdown lists agents, form submits, response renders |
| 13 | Custom MOS recipe | Bench+Files → Custom MOS recipe form | Parent agent dropdown populated, form submits |
| 14 | History feed | Overview → history facts area | Facts render with DD MON YYYY format, "Next fact" works |

### Edge Cases (probe)

| # | Check | How | Pass criteria |
|---|---|---|---|
| 15 | Empty state | Clear localStorage, reload | Onboarding card or graceful empty state, no crash |
| 16 | Resize | Narrow browser to ~400px width | Layout doesn't break catastrophically |
| 17 | Rapid lane switching | Click through all 5 tabs quickly | No stuck loading states or duplicate renders |

## Reporting

Follow the `/verify` report format:

```
## Verification: <what changed>

**Verdict:** PASS | FAIL | BLOCKED

**Claim:** <what the diff is supposed to do>
**Method:** verifier-dashboard skill — launched server, drove dashboard in browser

### Steps
1. ✅/❌/⚠️/🔍 <what you did> → <what you observed>
   <evidence>

### Findings
<anything that made you pause>
```

## Teardown

Kill the server process after verification completes:

```bash
# Kill the uvicorn process
kill %1  # if backgrounded
# Or find and kill by port
lsof -ti:8000 | xargs kill 2>/dev/null
```

PowerShell:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -ErrorAction SilentlyContinue | Stop-Process -Force
```
