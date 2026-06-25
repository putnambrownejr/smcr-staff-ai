# Contributing: Agents

How to add, modify, merge, or remove agents in smcr-staff-ai. Each agent change
touches 6-8 files in a specific pattern — this checklist keeps nothing from getting
missed.

## Adding a New Standalone Agent

### 1. Agent file — `app/services/agents/{name}_agent.py`

Follow the established pattern (see `lce_agent.py` or `ace_agent.py` as templates):

```python
from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    # relevant reference tuples
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class MyNewAgent(Agent):
    def __init__(self) -> None:
        refs = ...  # tuple of SourceRef from source_refs.py
        self.metadata = AgentMetadata(
            id="my-new-agent",              # kebab-case, unique
            name="My New Agent",            # display name
            description="...",
            domain="...",
            intended_users=["SMCR officers", ...],
            allowed_sources=[...],          # what it CAN cite
            disallowed_inputs=[...],        # what it must reject
            system_prompt="...",
        )
        self._refs = refs

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = "..."
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(self._refs),
            structured_citations=structured_citations(self._refs),
            source_trust=source_trust_markers(self._refs, notes_prefix="..."),
            confidence=Confidence.medium,
            follow_up_questions=["...", "...", "..."],
        )


def build_my_new_agent() -> MyNewAgent:
    return MyNewAgent()
```

Required elements:
- `_response()` helper (inherited from `Agent`) sets `human_review_required=True`
- `disallowed_inputs` must include classified/sensitive content types
- `follow_up_questions` — at least 3
- Advisory preamble: "Use this to shape X, not to replace qualified Y"

### 2. Registry — `app/services/agents/registry.py`

Add import and call in `default_agents()`.

### 3. Test: registry — `tests/test_agent_registry.py`

Add the new ID to the expected set.

### 4. Test: content reliability — `tests/test_agent_content_reliability.py`

Add a prompt to `DEFAULT_PROMPTS`.

### 5. VALID_PARENT_AGENTS — `app/api/routes/custom_mos_recipes.py`

Add to the set if the agent can parent custom MOS recipes.

### 6. Dashboard dropdowns — `app/static/dashboard/index.html`

Update relevant `<select>` dropdowns. Search for `<option value="fires-advisor"` to
find the right sections.

### 7. Verify

```bash
uv run pytest tests/ -q
uv run ruff check .
```

## Renaming an Agent ID

Same files as adding, but search-and-replace old ID → new ID across all of them.
Add a retirement mapping in `test_agent_registry.py`: `("old-id", "new-id")`.

## Removing an Agent

1. Delete or keep the agent file
2. Remove from registry `default_agents()`
3. Remove from test expected set (optionally add retirement mapping)
4. Remove from `DEFAULT_PROMPTS`
5. Remove from `VALID_PARENT_AGENTS`
6. Remove from dashboard `<option>` elements
7. Run `uv run ruff check --fix .` to catch unused imports

## Adding a Staff Archetype

Staff archetypes live in `staff_advisor_agent.py` as `StaffRoleArchetype` entries.
They don't need separate files — `build_staff_advisor_agents()` generates them all.
The ID is `staff-{role}` and they auto-join the Staff Council.

Still need: test expected set, content reliability prompt, dashboard dropdown.

## Source References

### Adding new SourceRef entries

Add to the appropriate tuple in `app/services/agents/source_refs.py`:

```python
SourceRef(
    title="MCO 1234.5A Full Title Here",
    url="https://www.marines.mil/...",
    publisher="United States Marine Corps",
    notes="One sentence describing relevance.",
),
```

Format conventions:
- `title`: Official document title with number
- `url`: Full HTTPS URL
- `publisher`: "United States Marine Corps", "Department of Defense", or "Department of the Navy"
- `notes`: One sentence, ends with period

### Auditing source references

Periodic hygiene checks:

```bash
# Count total entries
grep -c 'SourceRef(' app/services/agents/source_refs.py

# Check for duplicate titles
grep "title=" app/services/agents/source_refs.py | sort | uniq -d

# Find agents without source refs
for f in app/services/agents/*_agent.py; do
  grep -qL 'source_refs' "$f" && echo "No source refs: $f"
done

# Find publications mentioned in agent text but not cited
grep -rn 'MCO\|MCRP\|NAVMC\|MCWP' app/services/agents/*_agent.py | grep -v 'source_refs'
```

## Testing Agent Content

### Single agent run

```python
from app.services.agents.base import AgentContext
from app.services.agents.registry import AgentRegistry

registry = AgentRegistry()
agent = registry.get("fires-advisor")
response = agent.run("Help me plan a combined-arms live-fire exercise.", context=AgentContext())

print(response.answer)
print(response.confidence)
print(response.follow_up_questions)
print(response.structured_citations)
```

### Multi-agent comparison

```python
agents_to_compare = ["fires-advisor", "staff-opso", "ace"]
prompt = "Help me plan fire support for a combined-arms training exercise."

for agent_id in agents_to_compare:
    agent = registry.get(agent_id)
    response = agent.run(prompt, context=AgentContext())
    print(f"\n{'='*60}")
    print(f"Agent: {agent_id} — Confidence: {response.confidence}")
    print(f"Answer: {response.answer[:300]}...")
```

### Echelon comparison

```python
from app.schemas.staff import StaffEchelon

agent = registry.get("staff-s4")
prompt = "Help me plan sustainment for a field exercise."

for echelon in [StaffEchelon.battalion, StaffEchelon.regiment_meu_wing, StaffEchelon.division_group]:
    context = AgentContext(extra={"echelon": echelon.value})
    response = agent.run(prompt, context=context)
    print(f"\nEchelon: {echelon.value}")
    print(f"Answer: {response.answer[:400]}...")
```

### What to check in responses

| Check | What to look for |
|---|---|
| Advisory preamble | Opens with "Use this to shape X, not to replace Y" |
| human_review_required | Always `True` |
| confidence | `medium` for normal, `low` for ambiguous/sensitive |
| structured_citations | Non-empty for agents with references |
| follow_up_questions | At least 3, relevant to the scenario |
| Domain coverage | Addresses the specific domain, not generic advice |
| Echelon adaptation | Staff prefix and scope match echelon |

## Dashboard Verification Checklist

After changes that touch the UI, verify manually:

| Check | How | Pass criteria |
|---|---|---|
| API health | `GET /health` | 200, `"status": "ok"` |
| Dashboard loads | Navigate to `/dashboard` | No blank screen or JS error |
| No console errors | Browser console | No red errors |
| Lane switching | Click all 5 lane tabs | Each lane renders, no stuck states |
| Agent advisor form | Watch → Ask an advisor | Dropdown lists agents, response renders |
| Quick Links | Workspace → Quick Links section | Links render, filter works |
| Empty state | Clear localStorage, reload | Onboarding or graceful empty state |

## Rules

- **One agent per domain.** Extend an existing agent before creating a new one.
- **UNCLASSIFIED only.** Agent content, sources, and prompts must stay unclassified.
- **All outputs are advisory drafts.** Agents never claim authority.
