# MCPP And R2P2 Deep Dive

This note gives the repo a practical planning reference for the Marine Corps Planning Process (MCPP)
and the Rapid Response Planning Process (R2P2). It is meant to sharpen S-3, XO, and staff-product
behavior, not to replace formal doctrine.

## Official Sources

- MCDP 5 Planning
  - Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899841/mcdp-5/
  - Why it matters: gives the planning philosophy behind all Marine planning, especially planning as
    decision support and learning under uncertainty.

- MCWP 5-10 Marine Corps Planning Process
  - Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900553/mcwp-5-10/
  - Why it matters: gives the actual staff process, products, tenets, and the current public appendix
    on R2P2.

- MCTP 3-30A Command and Staff Actions
  - Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/
  - Why it matters: helps connect planning to command-post rhythm, staff actions, and decision support.

- MCO 1500.55 Military Thinking and Decision Making Exercises
  - Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/898778/mco-150055/
  - Why it matters: formal grounding for TDGs, wargaming, and decision-forcing exercises that support
    planning maturity.

## MCPP In Plain Terms

MCPP is the Marine Corps' deliberate planning process for units with staffs. It is not just a form or
order outline. It is the commander's and staff's structured way to understand the problem, develop a
solution, test it, decide, write it, and hand it off for execution.

The current public `MCWP 5-10` describes MCPP as a six-step process:

1. Problem framing
2. Course of action development
3. Course of action war game
4. Course of action comparison and decision
5. Orders development
6. Transition

The key point for this repo: MCPP should make the staff think better, not just write cleaner products.

## What MCPP Should Force The Staff To Do

- Clarify the problem before talking solutions.
- Expose assumptions, constraints, and missing information early.
- Give the commander real decisions instead of just updates.
- Build branches, sequels, and decision points before execution exposes the gap.
- Produce products that support execution, not paperwork for its own sake.

## MCPP Tenets That Matter Most Here

`MCWP 5-10` highlights three tenets that should shape how this repo reasons:

- Top-down planning
  - The commander drives the effort with intent, guidance, and decisions.
- Single-battle concept
  - Operations, logistics, intelligence, communications, information, and support are planned as one
    fight, not as separate shop products.
- Integrated planning
  - Relevant staff sections and subordinate representatives are involved early enough to matter.

For the repo, this means a strong planning answer should not sound like one shop talking to itself.

## Common MCPP Failure Modes

- Jumping straight to the event or mission without framing the problem.
- Treating assumptions as facts.
- Confusing a schedule with a concept of operations.
- Building a plan that requires more coordination than the unit can actually sustain.
- Writing a polished order without rehearsing decision points, support friction, or failure triggers.
- Letting staff products drift away from the commander's intent.

## R2P2 In Plain Terms

R2P2 is not a separate planning philosophy. It is a time-compressed version of the same six-step logic.

The current public `MCWP 5-10` describes R2P2 as:

- a time-leveraged planning process
- used primarily by MEUs
- designed to allow a MEU to begin execution of certain tasks within 6 hours
- dependent on deliberate predeployment preparation, rehearsed SOPs, and prior mission work

That matters a lot. R2P2 is fast because the force has already done heavy work beforehand.

## What Makes R2P2 Work

`MCWP 5-10` says successful rapid planning is predicated on:

- significant MCPP knowledge and experience
- detailed preparation, training, and organization of the force and equipment
- intelligence and mission-planning products developed previously
- current intelligence information
- refined, well-rehearsed SOPs

The same appendix also says a unit needs four capability areas in place to employ R2P2 well:

- integrated planning cells
- planning and operations SOPs
- intelligence
- information management

If those are weak, the unit is not really doing R2P2 well. It is just hurrying.

## Relationship Between MCPP And R2P2

The most important relationship is this:

- MCPP is the deliberate default.
- R2P2 is a compressed adaptation for severe time constraints.
- R2P2 mirrors the same six-step logic.
- R2P2 works best when the unit has already done the deliberate learning, rehearsal, and SOP work.

So the repo should not recommend "just do R2P2" for a unit that has not already built the staff habits
and planning products to support it.

## What Non-MEU Units Should Take From R2P2

The same public `MCWP 5-10` appendix says rapid planning by non-MEU units is usually more effective
for routine missions or tasks for which the unit has been well trained and has established SOPs.

That is the practical line for SMCR use:

- use full MCPP when the problem is new, complex, ambiguous, poorly rehearsed, or cross-functional
- use compressed planning only when the mission is familiar, the unit has strong SOPs, and the real
  challenge is time rather than understanding

## How This Should Shape SMCR Planning

For reserve units, the dangerous mistake is pretending compressed planning can replace preparation.

Good reserve use of MCPP:

- deliberate planning before drill or event execution
- prebuilt templates, graphics, checklists, and SOP-driven products
- rehearsed staff battle rhythm
- named decision points and suspense owners
- short wargames or TDGs to expose weak assumptions early

Good reserve use of R2P2-like compression:

- drill-weekend refinements to a mission already framed
- adjusting a known event after late changes
- handling short-notice but familiar requirements
- crisis-action style staff drills where the training objective is speed and clarity

Bad reserve use of R2P2-like compression:

- using it as an excuse not to do mission analysis
- skipping subordinate input and support planning
- assuming unfamiliar Marines or ad hoc teams can plan like a rehearsed MEU cell
- calling a rushed FRAGO "rapid planning" when there is no shared SOP base underneath it

## What The S-3 Lane Should Sound Like

When this repo talks like a good S-3/XO lane, it should:

- ask whether the problem needs deliberate MCPP or compressed refinement
- name the first thing that will fail if the unit tries to move too fast
- force command decisions, support relationships, and follow-on products into the open
- use TDGs and wargaming as planning stress tests, not as decoration
- connect AARs back to planning discipline, not just execution mistakes

## Usage Guidance For The Repo

This note should sharpen:

- `s3-opso`
- `doctrine-opord-assistant`
- `training-planner`
- `staff-products`
- `build_staff_package`
- `build_frago_to_conop`
- TDG / wargaming outputs

The repo should stay advisory and training-oriented. It should not produce real-world operational
planning, current-mission support, or sensitive movement details.
