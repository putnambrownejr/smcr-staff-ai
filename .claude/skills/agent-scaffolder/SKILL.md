---
name: agent-scaffolder
description: Walk through the full multi-file checklist for adding, renaming, merging, or removing an agent in smcr-staff-ai. Covers the agent file, registry, 3 test files, dashboard dropdowns, VALID_PARENT_AGENTS, and council routing. Use when creating a new agent, consolidating agents, or renaming an agent ID.
---

# Agent Scaffolder — smcr-staff-ai

## Purpose

Adding or modifying an agent touches 6–8 files in a specific pattern. This skill walks that checklist so nothing gets missed. It covers new agents, renames, merges, and removals.

## When to Use

- "Add a new agent for [domain]"
- "Rename [old-id] to [new-id]"
- "Merge [agent-a] into [agent-b]"
- "Remove [agent-id]"
- After any agent consolidation round, as a post-flight check

## The Checklist

### Adding a New Standalone Agent

#### 1. Agent file — `app/services/agents/{name}_agent.py`

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
        # Build answer string with advisory structure
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

Required elements in every agent:
- `_response()` helper (inherited from `Agent` base class) sets `human_review_required=True`
- `disallowed_inputs` must include classified/sensitive content types
- `follow_up_questions` — at least 3
- Advisory preamble: "Use this to shape X, not to replace qualified Y"

#### 2. Registry — `app/services/agents/registry.py`

```python
# Add import
from app.services.agents.my_new_agent import build_my_new_agent

# Add to default_agents() in the right section:
def default_agents() -> list[Agent]:
    return [
        # Standalone utility agents
        ...
        build_my_new_agent(),      # <-- add here
        # MAGTF element agents (standalone)
        ...
        # Consolidated staff archetypes
        *build_staff_advisor_agents(),
    ]
```

Sections in `default_agents()`:
- **Standalone utility agents** — most new agents go here
- **MAGTF element agents** — only ace, gce, lce
- **Consolidated staff archetypes** — only via `build_staff_advisor_agents()`

#### 3. Test: registry — `tests/test_agent_registry.py`

Add the new ID to the expected set in `test_agent_registry_loads_expected_agents`:

```python
assert {
    ...
    "my-new-agent",    # <-- add here
    ...
}.issubset(ids)
```

If replacing a retired agent, add a retirement mapping:

```python
("old-retired-id", "my-new-agent"),
```

#### 4. Test: content reliability — `tests/test_agent_content_reliability.py`

Add a prompt to `DEFAULT_PROMPTS`:

```python
DEFAULT_PROMPTS: dict[str, str] = {
    ...
    "my-new-agent": "A realistic prompt that exercises this agent's primary use case.",
    ...
}
```

#### 5. Test: agent-specific — `tests/test_agent_registry.py`

Add at least one agent-specific test:

```python
def test_my_new_agent_returns_expected_structure() -> None:
    registry = AgentRegistry()
    agent = registry.get("my-new-agent")
    assert agent is not None

    response = agent.run("Relevant prompt.", context=AgentContext())

    assert "Expected keyword" in response.answer
    assert response.structured_citations
    assert response.source_trust
```

#### 6. VALID_PARENT_AGENTS — `app/api/routes/custom_mos_recipes.py`

If the agent can parent custom MOS recipes (most domain agents can), add to the set:

```python
VALID_PARENT_AGENTS = {
    ...
    "my-new-agent",
    ...
}
```

#### 7. Dashboard dropdowns — `app/static/dashboard/index.html`

Update the relevant `<select>` dropdowns:
- Custom MOS recipe `parent_agent` dropdown
- MOS advisor form dropdown (if applicable)

Search for `<option value="fires-advisor"` to find the right sections.

#### 8. Verify

```bash
uv run pytest tests/test_agent_registry.py tests/test_agent_content_reliability.py -q
uv run ruff check app/services/agents/ app/api/routes/custom_mos_recipes.py
```

### Renaming an Agent ID

All the same files, but search-and-replace the old ID → new ID:

1. Agent file: change `id="old"` → `id="new"`, update class name and builder function name
2. Registry: update import and call
3. `test_agent_registry.py`: update expected set, add retirement mapping `("old", "new")`
4. `test_agent_content_reliability.py`: rename the key in `DEFAULT_PROMPTS`
5. `custom_mos_recipes.py`: update `VALID_PARENT_AGENTS`
6. `index.html`: update `<option>` values
7. If the old agent was in Staff Council routing (`council.py`): update `_normalize_role()` aliases

### Removing an Agent

1. Delete or keep the agent file (keep if builder is reused)
2. Registry: remove import and call from `default_agents()`
3. `test_agent_registry.py`: remove from expected set, optionally add retirement mapping
4. `test_agent_content_reliability.py`: remove from `DEFAULT_PROMPTS`
5. `custom_mos_recipes.py`: remove from `VALID_PARENT_AGENTS`
6. `index.html`: remove `<option>`
7. `council.py`: remove from `_normalize_role()` if aliased there
8. Run `uv run ruff check --fix .` to catch unused imports

### Adding a Staff Archetype (rare)

Staff archetypes live in `app/services/agents/staff_advisor_agent.py` as `StaffRoleArchetype` entries in the `ROLE_ARCHETYPES` tuple. They don't need separate files or registry imports — `build_staff_advisor_agents()` generates them all.

1. Add a new `StaffRoleArchetype(...)` entry to `ROLE_ARCHETYPES`
2. The ID will be `staff-{role}` automatically
3. It auto-joins the Staff Council — no council.py changes needed
4. Still need: test expected set, content reliability prompt, dashboard dropdown, VALID_PARENT_AGENTS

## Post-Flight Check

After any agent change, run the full suite:

```bash
uv run pytest tests/ -q
uv run ruff check .
```

If tests pass and ruff is clean, the scaffolding is complete.

## Rules

- **Murder-board first.** Before scaffolding a new agent, run `murder-board` to validate the design. Don't scaffold agents that should be extensions of existing ones.
- **Check the catalog.** Run `agent-catalog` to see the current roster before adding.
- **One agent per domain.** If an existing agent covers 80% of the need, extend it rather than creating a new one.
- **UNCLASSIFIED only.** Agent content, sources, and prompts must stay unclassified.
