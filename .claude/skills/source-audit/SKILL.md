---
name: source-audit
description: Audit all agent source references (SourceRef tuples in source_refs.py and inline refs) for duplicates, orphans, stale URLs, inconsistent formatting, and cross-agent coverage gaps. Use after consolidation rounds, when adding new sources, or as a periodic hygiene check.
---

# Source Audit — smcr-staff-ai

## Purpose

The agents cite specific Marine Corps orders, doctrinal publications, and public references via `SourceRef` tuples in `app/services/agents/source_refs.py`. After consolidation rounds where agents merge, references can become orphaned, duplicated, or inconsistently formatted. This skill audits the full source inventory.

## When to Use

- After any agent merge, rename, or consolidation
- When adding new source references
- Periodic hygiene check (monthly or after major changes)
- When a user reports a broken or outdated citation
- When extending an agent's `allowed_sources`

## Audit Workflow

### Phase 1 — Inventory

#### Extract all SourceRef tuples

```bash
# List all named reference tuples
grep -n 'REFERENCES.*:.*tuple' app/services/agents/source_refs.py
```

```bash
# Count total SourceRef entries
grep -c 'SourceRef(' app/services/agents/source_refs.py
```

#### Map which agents use which reference tuples

```bash
# Find all imports of reference tuples across agent files
grep -rn '_REFERENCES' app/services/agents/ --include="*.py" | grep -v source_refs.py | grep -v __pycache__
```

Build a matrix:

```
| Reference Tuple | Used by |
|---|---|
| S1_REFERENCES | staff-s1, chief-of-staff |
| S4_REFERENCES | staff-s4, lce |
| MEDICAL_REFERENCES | staff-surgeon, lce |
| ... | ... |
```

### Phase 2 — Duplicate Detection

#### Cross-tuple duplicates

Check if the same `SourceRef` (same title or same URL) appears in multiple tuples:

```bash
# Extract all titles
grep "title=" app/services/agents/source_refs.py | sort | uniq -d
```

```bash
# Extract all URLs
grep "url=" app/services/agents/source_refs.py | sort | uniq -d
```

Duplicates across tuples are acceptable when different agents legitimately share a source (e.g., MCO 5100.29 in both ORM and safety contexts). Flag them but don't auto-remove.

#### Within-tuple duplicates

Same source appearing twice in one tuple — always a bug. Fix immediately.

### Phase 3 — Orphan Detection

#### Unused reference tuples

A tuple defined in `source_refs.py` but not imported by any agent file:

```bash
# List all tuple names defined
grep -o '^[A-Z_]*REFERENCES' app/services/agents/source_refs.py | sort -u > /tmp/defined.txt

# List all tuple names imported
grep -roh '[A-Z_]*REFERENCES' app/services/agents/ --include="*.py" | grep -v source_refs.py | sort -u > /tmp/imported.txt

# Orphans = defined but not imported
comm -23 /tmp/defined.txt /tmp/imported.txt
```

Orphans from retired agents should be removed or reassigned.

#### Agents without any source refs

```bash
# Agents that don't import from source_refs
for f in app/services/agents/*_agent.py; do
  grep -qL 'source_refs' "$f" && echo "No source refs: $f"
done
```

Some agents legitimately have no citations (e.g., drill-prep-calendar). But domain advisory agents without sources are a gap.

### Phase 4 — Format Consistency

Check that all SourceRef entries follow the standard format:

| Field | Expected format |
|---|---|
| `title` | Official document title with number (e.g., "MCO 1001R.1L...") |
| `url` | Full HTTPS URL, no trailing slash |
| `publisher` | Consistent publisher names: "United States Marine Corps", "Department of Defense", "Department of the Navy" |
| `notes` | One sentence describing relevance, ending with period |

Common issues:
- Publisher inconsistency: "USMC" vs "United States Marine Corps" vs "Marine Corps"
- URL trailing slashes or missing index.html
- Notes missing terminal period
- Title missing the order/publication number

```bash
# Check publisher consistency
grep "publisher=" app/services/agents/source_refs.py | sort -u
```

### Phase 5 — URL Spot Check

Spot-check a sample of URLs for liveness. Don't crawl all — just check 5–10 representative ones:

```bash
# Pick a sample and check HTTP status
grep -o 'url="[^"]*"' app/services/agents/source_refs.py | head -10 | while read -r line; do
  url=$(echo "$line" | sed 's/url="//;s/"//')
  status=$(curl -sI -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
  echo "$status $url"
done
```

- **200**: live
- **301/302**: redirected — update URL
- **403**: may require CAC/auth — note but don't remove
- **404**: stale — flag for replacement or removal
- **000/timeout**: military sites may block automated checks — manual verify

Note: Many `.mil` URLs return 403 to automated requests. This doesn't mean they're broken — it means they require browser access or CAC. Flag but don't auto-remove.

### Phase 6 — Coverage Analysis

Check whether the source coverage matches the agent's stated domain:

- Does an agent claiming to advise on "MCO 5100.29 ORM" actually cite that order?
- Does an agent mentioning a specific MOS have references for that OccFld?
- After a merge, did the target agent inherit all the merged agent's references?

```bash
# Find MCO/MCRP/NAVMC mentions in agent answer strings that aren't in source_refs
grep -rn 'MCO\|MCRP\|NAVMC\|MCWP' app/services/agents/*_agent.py | grep -v 'source_refs'
```

If an agent mentions a publication in its advisory text but doesn't cite it via SourceRef, that's a coverage gap.

## Report Format

```markdown
# Source Audit — <YYYY-MM-DD>

## Summary
- Total SourceRef entries: <N>
- Reference tuples: <N>
- Agents with source refs: <N> / <total agents>

## Duplicates
<cross-tuple and within-tuple duplicates>

## Orphans
<unused reference tuples, agents without refs>

## Format Issues
<publisher inconsistency, URL issues, missing fields>

## URL Status (spot check)
<sample results>

## Coverage Gaps
<agents mentioning pubs they don't cite>

## Recommendations
1. <immediate fixes>
2. <cleanup tasks>
3. <new refs to add>
```

## Rules

- **Don't auto-delete.** Flag issues for review. A "duplicate" may be intentional cross-referencing.
- **Don't crawl .mil URLs aggressively.** Many require CAC auth or block automated requests. Spot-check a small sample.
- **UNCLASSIFIED only.** All source references must be publicly accessible documents. Do not add references to classified or CUI publications.
- **Preserve provenance.** When removing an orphaned tuple, note which retired agent it came from in the commit message.
