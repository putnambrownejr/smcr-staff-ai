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

Initial agents return structured placeholder responses. The response contract already supports citations, warnings, human-review flags, confidence, and follow-up questions.

## Expansion Pattern

Adding an agent should require:

1. Create a new agent file.
2. Add manifest metadata.
3. Add doctrine source mappings.
4. Add tests.
5. Register in `AgentRegistry`.

Agents should prefer checklists, templates, and questions over authoritative outputs. Operationally specific, classified, CUI, COMSEC, keying material, real frequency, real movement, or sensitive unit-plan requests must be refused or reduced to generic training guidance.

## OSINT Trend Agent

The OSINT agent is a public-source trend and evidence aggregation assistant. It should consume user-supplied trusted public source items, not perform unrestricted scraping. Outputs must include citations, counterarguments or alternative explanations, confidence weighting, source caveats, and human-review prompts.

It must not collect private personal data, bypass access controls, evade rate limits, or infer sensitive operational details from public chatter.

The vetted social connector at `/social/ingest` normalizes public news/social trend records into the `context.extra.source_items` shape. Future live platform adapters should be explicit, terms-aware, rate-limited, fixture-tested, and disabled by default unless configured.
