# Agent Design

Agents implement a common interface:

- `id`
- `name`
- `description`
- `domain`
- `intended_users`
- `allowed_sources`
- `disallowed_inputs`
- `system_prompt`
- `required_human_review`
- `citation_required`
- `run(input, context)`

Agents must be concrete implementations of `Agent` from `app/services/agents/base.py`. Do not add or register `PlaceholderAgent`-style scaffolds; tests enforce that registered agents return usable advisory responses with citations or source-trust markers when required.

## Expansion Pattern

Adding an agent should require:

1. Copy an existing simple concrete agent pattern, such as `uniform_agent.py`.
2. Extend `Agent` from `base.py` and provide real metadata, source mappings, warnings, and response structure.
3. Add tests in `tests/test_agent_registry.py` and reliability coverage in `tests/test_agent_content_reliability.py`.
4. Register the builder in `app/services/agents/registry.py`.
5. Verify no registered response reads as a placeholder and citation-required agents include citations or source-trust markers.

Agents should prefer checklists, templates, and questions over authoritative outputs. Operationally specific, classified, CUI, COMSEC, keying material, real frequency, real movement, or sensitive unit-plan requests must be refused or reduced to generic training guidance.

## OSINT Trend Agent

The OSINT agent is a public-source trend and evidence aggregation assistant. It should consume user-supplied trusted public source items before turning to outside sources. When utilizing outside sources it should prefer institutional/trusted and validated sources. Outputs must include citations, counterarguments or alternative explanations, confidence weighting, source caveats, and human-review prompts.

It must not collect private personal data from the user, bypass access controls, evade rate limits, or infer sensitive operational details from public chatter.

The vetted social connector at `/social/ingest` normalizes public news/social trend records into the `context.extra.source_items` shape. Future live platform adapters should be explicit, terms-aware, rate-limited, fixture-tested, and disabled by default unless configured.
