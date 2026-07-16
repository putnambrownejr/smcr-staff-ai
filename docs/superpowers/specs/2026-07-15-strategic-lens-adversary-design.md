# Strategic Lens and Fictional Adversary Design

## Goal

Let users create either a fictional training adversary shaped by strategic
patterns or a public-source country/force strategic lens. Both inform Scenario
Builder, Red Team, Actor Network, and IPB without stereotyping populations,
predicting real-world intent, producing targeting guidance, or creating
operational recommendations.

## Rationale

Existing scenario and Red Cell logic models generic adversary archetypes. It
does not give a user a structured way to express how an actor's strategic
preferences, escalation posture, information behavior, constraints, or theory
of advantage should shape exercise friction.

The feature uses a strategic lens rather than a national-character generator.
It treats analytical ideas such as *shashoujian* (often rendered "assassin's
mace") as bounded pattern cards, not a complete description of a nation or an
assertion that a real force will act in a particular way. DoD discussion of
PLA concepts such as systems-destruction warfare and multi-domain precision
warfare likewise informs questions and exercise friction only. Source checked:
2026-07-15.

Sources:

- U.S. Department of Defense, [China Military Power Report discussion, 2022](https://www.defense.gov/News/News-Stories/Article/Article/3230682/china-military-power-report-examines-changes-in-beijings-strategy/).
- U.S.-China Economic and Security Review Commission, [China Dream, Space Dream](https://www.uscc.gov/sites/default/files/Research/China%20Dream%20Space%20Dream_Report.pdf), accessed 2026-07-15.

## Two Operating Modes

### Fictional posture mode

The user chooses two to four posture cards and a fictional actor name. No real
country, people, unit, or organization is named. The result is a training
profile that creates coherent exercise pressure without representing any real
population.

Example posture cards:

- indirect leverage and asymmetric effect;
- political or legitimacy-first objectives;
- gradual, threshold-sensitive escalation;
- system-friction and decision-delay emphasis;
- ambiguity, deception, or information contest;
- proxy, partner, or influence-network reliance;
- risk acceptance for short-term political effect;
- preservation of force and avoidance of decisive engagement.

The system must describe cards as planning hypotheses, give counter-pressures,
and avoid prescribing tactics, targets, vulnerabilities, or exploit paths.

### Public-source lens mode

The user selects reviewed local Source Library records and names a country,
force, institution, or strategic problem. The source-aware resolver supplies
only local excerpts, citations, hashes, retrieval dates, and trust markers.

The output may make only attributed observations that are supported by selected
evidence. It must provide:

- source-backed observations;
- evidence gaps and source trust warnings;
- analytical hypotheses, separately labelled;
- a competing interpretation;
- a discriminator that could change the assessment;
- a statement that the lens does not predict intent or conduct.

Unreviewed, stale, watch, or superseded sources follow the existing explicit
opt-in rule and remain visibly marked. No external retrieval occurs during a
run.

## Shared Strategic Lens Contract

A `StrategicLens` model has these dimensions:

- `mode`: `fictional` or `public_source`;
- `actor_name`: fictional actor name or the user-provided public subject;
- `strategic_objective`;
- `theory_of_advantage`;
- `risk_and_escalation_posture`;
- `force_employment_preference`;
- `information_posture`;
- `constraints`;
- `observable_indicators`;
- `competing_interpretation`;
- `discriminator`;
- `confidence` and `evidence_gaps`.

In fictional mode, values are derived from posture cards and are labelled as
scenario assumptions. In public-source mode, values are derived only from
resolved local evidence or marked as unknown. A lens never contains individual
profiles, target sets, exploit paths, real-time activity inference, sensitive
movements, COMSEC, or collection tasking.

## Pattern Cards

Pattern cards are reusable strategic abstractions, each with:

- a neutral label and concise description;
- its decision/force/information emphasis;
- likely exercise friction at a high level;
- counter-pressures and failure conditions;
- questions that test whether the pattern actually applies;
- citations when a card is used in public-source mode.

The first library is deliberately small. It includes the cards listed in the
fictional posture mode section and a carefully phrased "asymmetric systems
effect" card derived from the analytical value, not a tactical interpretation,
of the *shashoujian* example.

## Integration

### Scenario Builder

Accept an optional `StrategicLens` or fictional posture-card selection. Add the
lens to the generated adversary profile, exercise friction, decision points,
and Red Cell questions. It does not replace the existing scenario archetype.

### Red Team

Add a `strategic_lens` option. In assumptions mode, it challenges whether the
friendly plan is relying on a mirror-imaged adversary. In evidence mode, it
tests whether source evidence supports the chosen lens. In hypotheses mode, it
compares at least two strategic interpretations and their discriminators.

### Actor Network and IPB

Actor Network may use a lens only to frame organization-level interests and
relationships as hypotheses. IPB may use it only to frame broad patterns,
indicators, and collection gaps. Neither agent predicts intent or supports
targeting.

## Safety and Truthfulness

- UNCLASSIFIED, public, local, training, or fictional inputs only.
- Human review, source citations, source-trust markers, and the required DRAFT
  warning remain mandatory.
- No nation, culture, ethnicity, religion, or population is represented as
  inherently aggressive, deceptive, rational, irrational, or monolithic.
- Public-source mode describes evidence and uncertainty, not a national
  personality or a forecast of conduct.
- No real-world target development, tactical employment, vulnerability
  exploitation, collection tasking, sensitive movement analysis, or COMSEC.

## Acceptance Criteria

1. Users can create a fictional lens from two to four posture cards and a
   fictional actor name.
2. Public-source lenses require source selection and preserve citation, hash,
   retrieval date, and trust information.
3. Public-source outputs label evidence, hypotheses, gaps, competing
   interpretation, and discriminator separately.
4. Scenario Builder, Red Team, Actor Network, and IPB accept the common lens
   contract without altering their existing safe defaults.
5. Tests prove no lens output creates person-level targeting, real-time intent
   prediction, operational recommendations, or unstated factual claims.
6. The dashboard remains a discovery surface; no agent-execution console is
   added.
