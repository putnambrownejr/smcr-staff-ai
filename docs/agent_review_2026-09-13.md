# Agent Review — 13 Sep 2026

Scope: all 45 registered agents in `app/services/agents/` (26 standalone, 3 MAGTF element, 16 staff-council seats). Reviewed for (1) response correctness, (2) doctrinal correctness, (3) user benefit. Core staff and high-use agents first, then outward.

Method: read every agent file, `base.py`, `registry.py`, `source_refs.py`, `roundtable.py`, the staff-products builder, and `tests/test_agent_content_reliability.py`; spot-checked suspect doctrine claims against live public sources (marines.mil, jcs.mil, acquisition.gov). Anything not verified is marked **verify**.

Verdict up front:

- The roster is structurally sound and safety discipline is excellent (draft footer, sensitive-input degrade, citation markers everywhere).
- The main correctness problem is not the framework text; it is **stale or wrong doctrine embedded in `system_prompt` / `mos_depth` strings** that nobody has fact-checked. Fires, GCE, uniform, assessment, G-8, and SEL each carry at least one error that a Marine would catch.
- The main usability problem is that **most agents ignore the user's input entirely** and return the same page every time. Only ~12 of 45 vary their answer with the request. That is by design for a local-first tool, but several agents *promise* scenario-specific output and then do not deliver it.
- Recommend **6 merges / 2 culls** (below). No new agents needed; two gaps are best handled as modes inside existing agents.

---

## 1. Cross-cutting findings (affect many agents)

### 1.1 Static answers that ignore input

Agents whose `run()` returns a fixed string regardless of `input_text` (only active-context lines vary):

writing-briefing-coach, orm-risk-management, uniform-advisor, drill-prep-calendar, leadership-advisor, warrior-monk, installation-practical-advisor, gtcc-advisor, financial-readiness-advisor, family-deployment-readiness-advisor, ace, gce, lce, infantry-tactics-advisor, fires-advisor, and every staff-council seat outside scenario mode.

Agents that actually respond to the request: chief-of-staff (handoff data), planning-advisor (tempo read), staff-products (product routing), assessment-learning (labelled AAR fields), red-team (archetype inference), pki (issue type), terrain-map (category detection), osint (source items), fitness-planning (parses count/objective/duration), unit-checkin (officer/enlisted/lateral), staff-s2/s4/s6/g9 + chief-of-staff + planning-advisor (LLM scenario mode only).

Why it matters: the doctrine value lives in `system_prompt` and `mos_depth`, and those strings are only consumed by the external scenario path (`llm_client.py`, `preflight.py`). For every non-scenario request the user sees the framework paragraph, not the knowledge. **Recommendation:** either (a) surface `system_prompt` + `mos_depth` verbatim on the AI page / prompt packs so the user's own chat model gets the knowledge, or (b) append the `mos_depth` block to every non-scenario answer (the staff seats already do this; the standalone agents do not).

### 1.2 Scenario mode is promised but only delivered for six agents

Every staff-council seat's `system_prompt` says "SCENARIO MODE: ... apply your framework TO that scenario." `_build_scenario_answer()` only has templates for g9, s2, s4, s6; every other seat silently falls through to the static framework text. This includes staff-surgeon, staff-sja, staff-pao, staff-provost, and staff-g8, which `roundtable.py` actively pulls into a round table on scenario keywords, so a FHADR round table returns real assessments from S-2/S-4/S-6/G-9 and boilerplate from Surgeon/SJA/PAO. **Recommendation:** add scenario templates + `*ScenarioOutput` schemas for xo, opso, surgeon, sja, pao at minimum (the roundtable triggers define the priority), or remove the SCENARIO MODE promise from seats that cannot honor it.

### 1.3 Duplicated reserve-admin text

The Drill Manager / MROWS / DTS / MOL / MCTFS chain appears verbatim in chief-of-staff, drill-prep-calendar, and staff-s1. The NOSC / NROWS / T-60 block appears in drill-prep, staff-surgeon, staff-chaplain, and staff-g8. When MARADMIN 157/25 is superseded, five strings need editing. **Recommendation:** one `RESERVE_ADMIN_SYSTEMS` and one `NAVY_RESERVE_ADMIN` constant in a shared module, referenced by all five.

### 1.4 Source URL hygiene

Several MCPEL article IDs in `source_refs.py` are reused for different publications, which means at least one of each pair is wrong:

| Article ID | Used for |
|---|---|
| 899779 | MCRP 2-10B.1 IPB **and** MCRP 3-03A.2 CMO Planning |
| 899782 | "MCWP 3-31 MAGTF C4" **and** MCWP 3-33.1 CMO |
| 899844 | MCDP 2 **and** MCWP 3-25 |
| 899747 | MCTP 3-30A (live MCPEL entry is article 2325814) |

Also `MCWP 3-31` is titled **MAGTF Fires and Effects** (May 2024), not "MAGTF C4" as listed under `S6_REFERENCES`; the S-6 seat is citing the fires pub for PACE/Annex K. **Recommendation:** run the existing `/source-audit` skill (or a plain link checker) over `source_refs.py` and fix titles/IDs. Verified: [MCWP 3-31 MCPEL entry](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900549/mcwp-3-31/), [MCTP 3-30A MCPEL entry](https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2325814/mctp-3-30a/).

### 1.5 Dating rule not applied

AGENTS.md requires "as of [date]" on organizational/policy facts. The G-9 USAID-dissolution block, the G-8 thresholds, the SEL PME gates, and the uniform seasonal dates all state facts flat with no date. Add an `as_of` note to each `mos_depth` block that carries time-sensitive policy.

---

## 2. Core staff / high-impact agents

### chief-of-staff — Keep. Grade: B+
- Correct: MROWS/DTS/MOL/MCTFS chain, MRRS/RHRP/PHA, 28-day-gap framing, routing table. Scenario mode wired to LLM with a sensible watch-list template.
- Fix: "AT planning triggers T-45/T-30/T-15" are unit rules of thumb, not policy; label them as such. Non-scenario answer is 60% connector-status boilerplate ("Email: provider interface exists; live access is not enabled") that a Marine does not need every time; move to a one-line footer.
- Overlap: non-scenario output is essentially drill-prep-calendar plus admin routing. See merge recommendation.

### planning-advisor — Keep. Grade: A-
- Correct: R2P2 gating logic is the right emphasis, logs discipline, failure modes are genuinely useful.
- Fix: the deliberate rhythm lists "Problem framing" then "Mission analysis" as separate steps. MCWP 5-10 (2016) folded mission analysis into Problem Framing; the six MCPP steps are Problem Framing, COA Development, COA War Game, COA Comparison and Decision, Orders Development, Transition. Use those six by name so the tool matches what EWS/CSC teach.
- Scenario template uses "MISSION ANALYSIS" as its heading; acceptable as a generic label but say "Problem Framing (mission analysis)".

### staff-products — Keep. Grade: A-
- 45 product types with real section prompts; routing on keywords works. OPORD scaffold is correct five-paragraph structure.
- Fix: `system_prompt` cites "MCWP 5-10, MCTP 3-30A/B" only; correspondence products should also cite SECNAV M-5216.5 (already in `CORRESPONDENCE_REFERENCES`). The 45-item follow-up question is unusable as a question; replace with "Name the product type (list in Bench+Files → Templates)."

### staff-xo — Keep. Grade: B
- Voice is good. No `mos_depth`, no scenario template despite being the natural synthesizer for anything that is not a CoS problem. Add a scenario template (decision matrix + staff-integration gaps) and pull it into `CORE_PARTICIPANTS` alongside staff-s2 / planning-advisor.

### staff-opso — Keep. Grade: B
- Good 0511 depth questions. Missing the S-3's actual daily material: range/ammo request lead times (RFMSS, E581/ammo forecasting), T&R event selection, MCTIMS entry. No scenario template. Add these to `mos_depth`; the OpsO is the most-used seat in a reserve battalion.

### staff-s1 — Keep. Grade: B+
- Correct: MCO 1001R.1L baseline, $750 IDT cap under MARADMIN 157/25 (verified: [IDT travel update](https://www.marines.mil/News/Messages/Messages-Display/Article/4133200/inactive-duty-training-idt-travel-reimbursement-update/)).
- Fix: "FitRep timeline: officer reporting periods, submission windows, RS/RO responsibilities" is a heading with no content; either populate from MCO 1610.7B (report occasions, 30-day submission window, RS/RO/3O chain) or delete. Note MCO 1001R.1L "w/CH-2, 7 Mar 2025" — **verify** the change date on MCPEL.

### staff-s2 — Keep. Grade: A-
- Correct: four-step IPB, PIR-to-collection linkage, OSINT methodology per MCRP 2-10A.3. Scenario template (intel estimate with most-likely/most-dangerous) is the best in the file.
- Fix: `S2_REFERENCES` lists both MCRP 2-10B.1 and MCTP 2-10B as "IPB"; only one is the current IPB pub — **verify** and drop the other. See URL hygiene above.

### staff-s4 — Keep. Grade: B+
- Scenario template covers Class I/III/V/VIII and support agreements (CSSA/ACSA); good. `mos_depth` is only questions, no planning factors; the LCE agent holds the consumption factors that belong here. See merge recommendation (lce → s4).

### staff-s6 — Keep. Grade: B
- Correct: PRC-117G/160/158 bands, MUOS, JENM, Silvus MANET, PACE discipline.
- Fix: cited pub is mis-titled (see 1.4). "Annex K structure: 6 appendices (signal, EMCON, spectrum, SATCOM, data, cyber)" — **verify**; MCWP 5-10 Annex K appendices do not match that list as written. Scenario template says "Assess COMSEC sharing limitations"; fine as a prompt, but the sensitive-input filter will degrade any answer that names actual COMSEC, so add "keep answers generic" to the template.

### red-team-assumptions-challenge — Keep. Grade: A-
- Three modes (assumptions / evidence / hypotheses), archetype inference, strategic-lens integration, civil-network snapshot. The most sophisticated agent in the roster and the one that most benefits a staff before a brief.
- Fix: nothing doctrinal. Modes are only reachable via `agent_options.mode`; confirm the dashboard exposes the selector, otherwise 2/3 of the agent is invisible.

### assessment-learning-advisor — Keep. Grade: B-
- Correct: AAR four-step structure, reserve owner/suspense discipline, corrective-action register with explicit "human assignment required."
- **Doctrinal errors:**
  - "Evaluation codes: T (trained), P (partially trained), U (untrained)" is Army. Marine MET assessment in DRRS-MC is **Y / Q / N** (yes, qualified yes, no) per MCO 3000.13B (verified: [MCO 3000.13B](https://www.marines.mil/Portals/1/Publications/MCO%203000.13B.pdf)). This appears in both `system_prompt` and the answer text.
  - Collective T&R example "INF-MN-6001 = infantry platoon defensive operations": the functional-area code is MAN, and the 6000-level is battalion; platoon is 4000-level. Use a real event code from NAVMC 3500.44D.
  - "T-rating is one of four pillars (personnel, equipment, supply, training)": the DRRS-MC resource areas are P, S (supply/equipment on hand), R (equipment readiness/condition), T. Say so.

### drill-prep-calendar — Merge into chief-of-staff. Grade: B
- Content is correct and useful (pre/during/post-drill checklist, NROWS T-60). But it is a strict subset of what chief-of-staff already emits, it reads no calendar data despite its name, and it duplicates the admin-systems block. Make it the CoS's default non-scenario output and retire the ID (add a retirement mapping in `test_agent_registry.py`).

### orm-risk-management — Keep. Grade: B-
- Correct products list (worksheet, no-go, residual-risk note, rehearsal safety brief). Cites MCO 5100.29C.
- Fix: never mentions the actual ORM process steps (identify hazards, assess, make decisions, implement controls, supervise) or the RAC matrix (probability × severity) that every Marine safety brief uses. Never mentions DD Form 2977 (the writing coach does). Static answer; a 30-line `mos_depth` with the five steps, RAC categories, and residual-risk approval levels would double its value.

### writing-briefing-coach — Keep. Grade: B
- Correct format list (naval letter, point paper, decision brief). Static; the knowledge is in `system_prompt` only. See missing-mode note in §6 (FitRep / awards writing).

---

## 3. Remaining staff-council seats

| Seat | Grade | Findings |
|---|---|---|
| staff-battle_captain | A- | Best `mos_depth` in the file: watch roles, COP track colors, SALUTE, turnover checklist, reserve stand-up/tear-down reality. Keep. |
| staff-sel | B- | Enormous depth, but time-sensitive and partly stale: "15 per MCI" (MCIs no longer exist; composite score uses MarineNet/college credit), "SNCO Leadership School" is not a current course name (GySgt PME is Advanced School), Sergeants/Career/Advanced School resident requirements changed by MARADMIN in 2025 — **verify** every gate against [updated EPME requirements](https://www.marines.mil/News/Messages/Messages-Display/Article/4015948/updated-enlisted-professional-military-education-epme-requirements-for-active-d/) and add `as of`. MCIRSA phone number and NAVMC 10476 — **verify**. |
| staff-surgeon | B | NOSC/NROWS content is correct and valuable. Fix: "DNA sample verified in MEDPROS" — MEDPROS is Army; Navy/USMC use MRRS. "HIV testing: annual" — DoD interval is every two years; **verify**. Dental class definitions correct. No scenario template although roundtable pulls it on "casualt/medical." |
| staff-sja | B+ | NJP mechanics and court-martial tiers correct. "MCO P1900.16" is now MCO 1900.16 (no P). No scenario template although roundtable pulls it on ROE/RUF/SOFA. |
| staff-pao | B | Correct Annex F = Public Affairs, generate/preserve/deny/project. Thin; add release-authority ladder and RTQ format from MCWP 3-33.3. No scenario template. |
| staff-chaplain | B+ | MRE 503 privilege, DSTRESS and OneSource numbers correct. Duplicated NROWS block. |
| staff-provost | C+ | No `mos_depth` at all despite `FORCE_PROTECTION_REFERENCES` (MCO 5530.14A, 5530.13). Add 20 lines: FPCON levels, DBIDS, random antiterrorism measures, AT/FP officer role, visitor/contractor vetting. Roundtable pulls it on "access control / crowd." |
| staff-ig | C+ | No `mos_depth`. IGMC functional-area checklists are cited; pull the checklist categories into depth text (CGRI/CGIP structure, hotline vs. command investigation vs. request-mast lanes). |
| staff-g8 | B | Appropriation symbols (17-1108 RPMC, 17-1105 MPMC, 17-1107 O&M MCR), ADOS 1,095/1,460 rule, and FY2023 clean audit are all correct. **Errors:** micro-purchase threshold is **$15,000** as of 1 Oct 2025 (verified: [GSA SmartPay bulletin](https://smartpay.gsa.gov/guidance-and-audits/smart-bulletins/002/)); services subject to SCLS remain $2,500. "Mid-Year Review (MIDLIFE)" is not a term; it is MYR. Add `as of`. |
| staff-g9 | A- | ASCOPE/PMESII/CPB/Annex G correct; USAID-dissolution block matches project memory and is the right emphasis. Fix: date every claim in that block ("as of Sep 2026"); "Food for Peace Title II transferred to USDA" — **verify**. `G9_REFERENCES` says MCWP 8-10 defines "Annex I"; Marine/joint format does not use letters I or O — **verify**. |

---

## 4. MAGTF element and tactical agents

### fires-advisor — Keep, but fix before anyone relies on it. Grade: C
Call-for-fire six elements and D3A are correct. The rest has the most doctrinal errors of any agent:
- **CFL is reversed.** Doctrine: fires *beyond* the CFL need no additional coordination; fires *short of* it must be coordinated with the establishing HQ. The agent says the opposite (verified against JP 3-09 / MCWP 3-16 definitions: [CFL definition](https://www.militaryfactory.com/dictionary/military-terms-defined.php?term_id=1314), [MCWP 3-16 App B](https://www.globalsecurity.org/military/library/policy/usmc/mcwp/3-16/fdraft_appb.pdf)).
- **FSCL is labelled restrictive.** It is a permissive measure.
- **"NFL (no-fire line)"** is an obsolete term; the current measure is the No-Fire Area (NFA). Restrictive measures are NFA, RFA, RFL.
- **"Annex F (Fire Support)"** is wrong for a Marine OPORD; Annex F is Public Affairs (the PAO seat already says so). Fire support sits in Annex C (Operations), Appendix 19 — **verify** against MCWP 5-10 Appendix.
- **M109** self-propelled howitzers are not in the Marine Corps inventory (retired 2005).
- **120mm mortar** listed as a fires means; the EFSS was divested. Meanwhile HIMARS, NMESIS, and the Force Design cannon-to-rocket shift are absent entirely.
- 81mm max range is ~5.9 km (M252), not 5.6.

### gce — Merge into staff-opso as a MAGTF lens, or keep only as a roundtable voice. Grade: C+
- **Stale structure:** "Tank Battalion: 3 tank companies" — all Marine tank battalions were deactivated by 2021 under Force Design. "Scout Sniper platoons (organic to infantry bn)" — disbanded 2023, replaced by Scout Platoons. "Infantry squads expanded to 13 Marines" — the current design is 15 (squad leader, assistant, systems operator, three fire teams); **verify**. The agent cites Force Design in the same paragraph, so the inconsistency is visible to any 03xx reader.
- The combined-arms MCDP 1 framing and the checklist are fine but overlap heavily with infantry-tactics-advisor and staff-opso.

### ace — Keep as roundtable voice. Grade: B-
- MACCS agencies, six functions, air tasking cycle are correct.
- Fix: "LAAD ... Stinger/Avenger" — Avenger is Army; Marine LAAD uses Stinger MANPADS and MADIS/L-MADIS. "RQ-21" is divested; VMUs are transitioning to MQ-9A — **verify** current status. F-35B squadron size is 10–16, not 16–20.

### lce — Merge into staff-s4. Grade: B
- Classes of supply, six logistics functions, CSS estimate format, and consumption factors are correct and are exactly what the S-4 seat is missing. Move this text into `staff-s4.mos_depth`, keep `lce` only if the roundtable needs a distinct MLG voice (it currently does not trigger it).

### infantry-tactics-advisor — Keep. Grade: B+
- Formations, movement techniques, platoon attack sequence, SMEAC, and the reserve building blocks (4-hr STX, platoon FTX, company FTX at AT) are correct and practical.
- **Fix:** Troop Leading Steps are the six-step BAMCIS (Begin planning, Arrange recon, Make recon, Complete plan, Issue order, Supervise). The agent lists eight by adding "Rehearse, Execute," which is not doctrinal. "RTR" is usually "return fire, take cover, return accurate fire"; fine.

---

## 5. Intelligence and research agents

| Agent | Grade | Findings |
|---|---|---|
| osint-research-assistant | A- | STANAG 2511 A–F / 1–6 correct; MCRP 2-10A.3 five-step method correct; source tiering and counterargument discipline are exactly right. Keep. |
| terrain-map-advisor | A- | One of the few agents that responds to the question (category detection). Resource list is good. Keep. Consider adding NGA "Tearline" (already in OSINT refs) and the CIA Factbook map tab. |
| area-study-builder | C | Without attached `source_evidence` every PMESII/ASCOPE line is "collection gap; no supplied evidence," and it never calls the LLM. Doctrinally correct; practically empty. |
| actor-network-analyst | C | Same: returns "Relationship not established" scaffolds. Correct targeting guardrail. |
| information-requirements-manager | C+ | Same pattern; the three-IR template (PIR/FFIR/CIR) is doctrinally fine. |
| ipb-assistant | C | Same; the staff-s2 scenario template already produces a better IPB when the LLM is approved. |

**Recommendation:** these four form a pipeline (area study → actor network → IR → IPB) that only makes sense with source evidence attached and a human chaining them. Either (a) wire them into `_try_llm_populate` with their existing `*ScenarioOutput` schemas so a scenario request actually fills them, or (b) collapse them into modes of staff-s2 (ipb, information-requirements) and staff-g9 (area-study, actor-network) and retire the four IDs. Option (b) removes four near-empty entries from the AI page without losing any doctrine.

---

## 6. Reserve admin and readiness agents

| Agent | Grade | Findings |
|---|---|---|
| unit-checkin | A- | Highest user benefit per line in the roster for a new join. **Terminology fixes:** "Service Alphas (Chucks for officers)" — "Chucks" is slang for Service C, not an officer variant; delete. "CIF account" and "TA-50" are Army; Marines say IIF (Individual Issue Facility) and 782/deuce gear. "Record of Emergency Data, NAVMC 10922" — **verify** form number (RED is maintained in MOL). Otherwise correct (SGLV 8286, DBIDS, ESGR/USERRA). |
| uniform-advisor | C+ | Several errors in `system_prompt`/answer: "summer whites" is Navy, not Marine; **Blue Dress D includes ribbons** (short-sleeve khaki shirt with ribbons) — agent says "no ribbons"; **PUC is not first in precedence** — personal decorations (MoH, Navy Cross, …) precede all unit awards; **"Sleeves down (never cuffed)"** is wrong — sleeves are rolled during the summer season (reinstated 2014); seasonal changeover dates and the MCO 1020.34H chapter map — **verify** (the order lets commanders set changeover). Undershirt color guidance — **verify**. `docs/sources/uniform_regulations.md` exists; the agent should be rebuilt from it. |
| installation-practical-advisor | B+ | Practical and honest ("local page beats generic advice"). Correct on DBIDS/IARA/REAL-ID. Keep. Overlaps with staff-provost on visitor control; acceptable because audiences differ. |
| pki-cac-troubleshooter | B | Playbook logic is good and input-responsive. **Citations are a placeholder** ("until a verified public source stack is added") while `docs/sources/cac_setup_windows_mac.md` already has militarycac.com and DoD Cyber Exchange InstallRoot links. Wire those as a `PKI_REFERENCES` tuple. |
| leadership-advisor | B | Sound MLD six-F framing; Lejeune/Krulak/Mattis/Butler lenses. Static. Keep. |
| warrior-monk | C+ | Fifteen lines of static reflection text that already points users back to leadership-advisor. Merge as a "reflect" mode of leadership-advisor. |
| gtcc-advisor | B | Correct, tightly scoped, links to CitiManager. Keep. |
| financial-readiness-advisor | B- | Correct pointers (LES, TSP, FINRED, OneSource). Static and thin. Keep (distinct compliance boundary from GTCC). |
| fitness-planning-advisor | A- | Parses the request, runs the PT engine, emits ORM matrix with owners and stop triggers. Keep. |
| family-deployment-readiness-advisor | C | Three sentences pointing to a Bench+Files checklist. Cull as an agent; keep the checklist feature and route the domain to staff-s1 (family care plan) and staff-sja (POA/wills). |

---

## 7. Merge / cull recommendations (summary)

| Action | From | Into | Rationale |
|---|---|---|---|
| Merge | drill-prep-calendar | chief-of-staff | Strict subset; duplicated admin block; reads no calendar. |
| Merge | lce | staff-s4 (`mos_depth`) | Supply-class factors and CSS estimate belong to the S-4 seat; roundtable never triggers lce. |
| Merge | warrior-monk | leadership-advisor (mode) | Already cross-references; 15 static lines. |
| Merge | ipb-assistant + information-requirements-manager | staff-s2 (modes) | S-2 scenario template already does this better. |
| Merge | area-study-builder + actor-network-analyst | staff-g9 (modes) | Empty without attached evidence; G-9 owns civil estimate/CPB. |
| Cull | family-deployment-readiness-advisor | (checklist feature stays) | No advisory content beyond a pointer. |
| Keep but demote | gce, ace | roundtable-only voices | Useful in a round table; redundant on the AI page next to opso/fires/infantry. |

Net: 45 → 36 registered agents with no loss of doctrine content.

---

## 8. Research / material gaps (look here first, then fetch)

Material already in the repo that agents are not using:
- `docs/sources/cac_setup_windows_mac.md` → pki-cac-troubleshooter (placeholder citations).
- `docs/sources/uniform_regulations.md` → uniform-advisor (rebuild the facts block).
- `docs/sources/performance_evaluation.md` + `app/services/fitreps/` → writing-briefing-coach (no FitRep guidance anywhere in the agent layer).
- `docs/sources/safety_risk_management.md` → orm-risk-management (add the five-step process and RAC matrix).
- `docs/sources/inspector_general_readiness.md`, `force_protection_access_control.md` → staff-ig, staff-provost (both have refs but no depth text).
- `docs/interagency_reference.md` → chief-of-staff and planning-advisor scenario templates (they mention "Interagency" but do not point to the doc the G-9 seat points to).

Material that needs to be fetched or refreshed:
- **Fires:** MCWP 3-31 (May 2024 edition), MCWP 3-16, JP 3-09 FSCM definitions; Force Design fires structure (HIMARS battalions, NMESIS, cannon reduction).
- **GCE:** current infantry battalion design (squad of 15, Scout Platoon, no tanks, MRB/LAAB/MLR).
- **ACE:** MQ-9A VMU transition, MADIS/L-MADIS, current squadron sizing.
- **SEL:** 2025 EPME MARADMIN, MCO P1400.32D composite-score factors (post-MCI), RQS form number.
- **Assessment:** MCO 3000.13B chapter 4 (Y/Q/N, P/S/R/T), a real collective event code from NAVMC 3500.44D.
- **G-8:** FAR 2.101 thresholds effective 1 Oct 2025; date the block.
- **Surgeon:** MRRS vs. MEDPROS, DoD HIV testing interval, IMR categories per BUMED.
- **S-6:** correct the MCWP 3-31 mis-title; identify the current MAGTF communications pub (successor to MCWP 3-40.3) and the real Annex K appendix list from MCWP 5-10.
- **Source URL audit:** dedupe MCPEL article IDs across `source_refs.py` (see §1.4).

---

## 9. Missing agents

Agree with the premise that the roster is already broad. Two real gaps, both best served as modes rather than new IDs:

1. **FitRep / awards writing** — The repo has a FitRep analytics service and a performance-evaluation source doc, but no agent helps write Section I comments, RS/RO markings rationale, or an award citation/summary of action (MCO 1610.7B, MCO 1650.19). Add as a mode of writing-briefing-coach with `S1_REFERENCES` + an awards-manual ref. This is the single most-requested staff writing task in a reserve unit.
2. **Range / ammunition / training-resource requests** — RFMSS range requests, ammo forecasting and E581 lead times, MCTIMS entry. Belongs in staff-opso `mos_depth`, not a new agent.

Nothing else surfaced as a gap that an existing seat could not absorb.

---

## 10. Suggested execution order

1. Fix the confirmed doctrinal errors (fires FSCMs and annex, assessment Y/Q/N, uniform Blue Dress D / precedence / sleeves, GCE tanks/scout snipers, G-8 threshold, infantry BAMCIS, check-in terminology). Half a day; all string edits.
2. Run `/source-audit` over `source_refs.py`; fix duplicated article IDs and the MCWP 3-31 title.
3. Add scenario templates for surgeon, sja, pao, xo (the roundtable already expects them).
4. Centralize the reserve-admin and NOSC blocks.
5. Execute the merges in §7 using the checklist in `docs/contributing-agents.md`.
6. Add the FitRep/awards mode and the OpsO range/ammo depth.

DRAFT — Verify all references against current official sources before acting.

---

## Status — 13 Sep 2026 fix pass

Done (all tests pass: 847 passed, ruff and mypy clean):
- §2/§4/§6 confirmed doctrinal errors fixed in fires, assessment, uniform, GCE, ACE, infantry, check-in, surgeon, SJA, SEL, G-8, planning-advisor.
- §1.4 source URLs corrected for MCTP 3-30A, MCWP 3-31 (now "Fires and Effects"), MCTP 3-10F (formerly MCWP 3-16), MCDP 3, MCWP 3-20, MCWP 3-25, MCWP 3-33.1, MCRP 3-03A.2; S-6 now cites MCRP 3-30B.2 (formerly MCWP 3-40.3).
- §1.2 scenario templates and output schemas added for staff-surgeon, staff-sja, staff-pao, staff-xo.
- §1.3 reserve-admin and NOSC/NROWS text centralized in `app/services/agents/reserve_admin_text.py`.
- §1.5 "as of" dating added to the G-8, G-9, SEL, and fires policy blocks.
- pki-cac-troubleshooter now cites `PKI_REFERENCES` instead of a placeholder.

Not done (awaiting decision): §7 merges/culls, FitRep/awards writing mode, OpsO range/ammo depth, ORM five-step/RAC depth, provost/IG depth text.

## Status — merge pass (same day)

Done (841 tests pass; ruff and mypy clean):
- §7 merges executed. Roster is now 37 catalog agents (21 standalone + 16 staff seats). Retired ids
  (`lce`, `drill-prep-calendar`, `warrior-monk`, `family-deployment-readiness-advisor`, `ipb-assistant`,
  `information-requirements-manager`, `area-study-builder`, `actor-network-analyst`) resolve through
  `MERGED_AGENT_ALIASES` to the survivor with a forced mode, so dashboard chain presets, seed cadence data,
  saved MOS recipes, and the `/agents/{id}/run` API keep working. `lce_agent.py` and `drill_prep_agent.py`
  deleted; the four intel specialists remain as unregistered delegates behind `staff-s2` / `staff-g9`.
- `staff-s4` now carries the full LCE depth (MLG/CLR/CLB, six functions, classes of supply with planning
  factors, 9-section CSS estimate, sync matrix); round-table triggers route LCE/CLB/MLG/distribution/
  Class VIII language to it. `ace` and `gce` gained round-table triggers.
- `writing-briefing-coach` gained the FitRep & awards mode (14 attributes, RV, Section I structure, RO
  Section K, occasions, adverse-report rights; awards package, SOA discipline, citation skeleton) with
  `FITREP_AWARDS_REFERENCES` (MCO 1610.7B, SECNAV M-1650.1, MCO 1650.19J).
- `staff-opso` gained range/ammo/T&R lead-time depth and `RANGE_TRAINING_REFERENCES` (MCO 3570.1D,
  MCO 3574.2M); `orm-risk-management` gained the five-step process, RAC matrix, three ORM levels, and
  range specifics; `staff-provost` and `staff-ig` gained full depth blocks (MCO 3302.1F added to refs).
- `chief-of-staff` non-scenario answer now carries the standing pre/during/post drill timeline and cites
  `DRILL_PREP_REFERENCES`; `leadership-advisor` has a `reflect` mode; `staff-s1` has a `family_readiness` mode.
- `docs/contributing-agents.md` documents the merge-into-mode pattern; roadmap counts updated.

Remaining from the review: §1.1 surfacing `system_prompt`/`mos_depth` on the AI page or prompt packs;
`staff-xo` into round-table `CORE_PARTICIPANTS`; scenario templates for `staff-opso`, `staff-provost`,
`staff-g8`; the source-audit link check over the rest of `source_refs.py`.

## Status — follow-up pass (same day)

Done:
- §1.1 Doctrine strings surfaced: every staff seat's `system_prompt` now carries its `mos_depth` as a
  "ROLE DEPTH" block (so the external scenario path and the AI page both see it); each agent card on the
  AI page has a "Doctrine notes" panel with a copy-as-chatbot-prompt button.
- Round table: `staff-xo` joined `CORE_PARTICIPANTS`; `RoundtableRequest.preset` added (`auto`,
  `full_staff`, `training`, `command_team`); `auto` falls back to the full staff when no section is
  triggered, so a generic question gets every seat; training/admin/SEL/ORM/AAR triggers added. A
  **Round table tab** on the dashboard AI page calls `POST /agents/roundtable` and renders the synthesis,
  each seat's answer and follow-up questions, warnings, and a copyable transcript. Combos are now
  runnable (`POST /agents/chain`) from the Combos tab. Dashboard changes live in
  `scripts/dashboard_integrity_patches.py` (`AI_PAGE_PATCHES`) and `scripts/dashboard_integrity_methods.js`.
- Scenario templates + output schemas added for `staff-opso`, `staff-provost`, `staff-g8` (the PT-planner
  `OpsPtScenarioOutput` role was renamed `opso_pt` to free `opso`).
- Source link check: `scripts/check_source_refs.py` added. marines.mil and usmcu.edu return 403 to every
  scripted fetch, so MCPEL article ids were verified by search instead. Corrected: MCDP 2, MCDP 6,
  MCWP 2-10, MCTP 2-10B (title was wrong — it is *MAGTF Intelligence Production and Analysis*),
  MCRP 2-10B.1, MCTP 3-30B, MCTP 3-40A, MCWP 8-10, MCO 5216.20B, MCO 1020.34H, MCO 5060.20, MCO 5100.29C,
  MCO 5530.14A, MCWP 3-10, MCRP 3-03A.1, MCTP 3-30F (formerly MCWP 3-33.3), NAVMC 3500.100C (supersedes
  100B); dead links replaced: USGS National Map, Fatmap (now Strava Global Heatmap).
  Still unverified by search (ids left as-is): MCO 3502.8A, MCO 5430.1A, MCO 1500.55, MCRP 6-11D,
  MCTP 3-32D, MCRP 3-16.6A, NAVMC 3500.56C, MCO 1650.19J change level.
- Round table synthesis in local mode: the service now hands the synthesizer a per-seat digest
  (concerns, next actions, open questions) so the Chief of Staff's synthesis integrates what the
  table said instead of returning its standing brief. Verified in the browser: 19 seats, synthesis,
  copyable transcript.
- Dashboard bundle bug found and fixed while verifying: the integrity guard injection placed the
  `requestKey`/`modeVersion` snapshot after a leading `setState`, which threw
  "Cannot access 'requestKey' before initialization" in `_loadTravelCases`. `hoist_identity_snapshots`
  in `scripts/dashboard_integrity_patches.py` repairs it idempotently and the injection order is fixed
  for future exports.

## Status — honesty pass (same day)

The user rejected any template output presented as analysis. Changes:
- `RoundtableResponse.mode` (`external_ai` | `local_templates`); local mode's first warning is
  "NO AI ANALYSIS WAS PERFORMED …". The digest "synthesis" was removed.
- `GET /agents/roundtable/capability` reports whether a live table is possible; `POST /agents/roundtable/packet`
  builds a **staff call packet** (input + seats' scope, lenses, standing questions, products, role notes +
  instructions for the AI) for round tables or agent chains, optionally saved to Drafted files
  (`user-docs/generations`) so it can be moved into a project folder the AI can search.
- `app/services/agents/perspective.py`: when the caller asks for external inference (`inference: "auto"|"external"`
  or `options.inference`) and a seat's own run produced no scenario output, the seat is re-run through the approved
  external path with its template as the *lens* (`StaffPerspectiveOutput`, role bound per seat); the synthesizer
  uses `RoundtableSynthesisOutput`. Wired into `/agents/{id}/run`, `/agents/chain`, and the round table. Approval
  preview/digest rules unchanged.
- Dashboard Round table tab v2: shows the capability note; without an external AI it only builds/copies/saves the
  packet; with one it runs preview → acknowledge → convene. Combos build chain packets. No template is rendered as
  a seat answer anywhere.
- `AGENTS.md` gained "Convening the Virtual Staff (round table) as the AI Assistant" — the procedure Claude Code /
  Codex follow when a user drops in a SITREP. `prompt-packs/round-table.md` is generated by
  `scripts/build_roundtable_pack.py` for chatbots without the app.

Verified in the browser (packet mode, no LLM key): the Round table tab shows the capability note, offers
only "Build staff call packet", the built packet opens with the no-analysis disclaimer, no seat "answer" is
rendered, and "Save packet to my files" wrote `Staff call packet — full_staff` into Drafted files
(`/user-docs/generations`). The earlier `requestKey` console error is gone.

## Status — user-built automations (same day)

- New `/automations` API (`app/api/routes/automations.py`, `app/services/chief/automation_store.py`,
  `app/schemas/automations.py`): per-user CRUD, six starter templates (post-drill admin sweep, pre-drill readiness
  check, MARADMIN watch, AAR into next drill, FitRep suspense chase, range day package), a rendered
  standing-instruction block (mirrors the Chief of Staff block and inherits its unit/billet context), and a
  run-packet endpoint that wraps one occurrence's input plus the block plus the chosen seats' lenses into a staff
  call packet (optionally saved to Drafted files). Storage: `automations_storage_dir` (local context dir).
- Dashboard Automations tab (v3 integrity patches): "Your automations" list with copy-block / edit / delete and a
  per-automation run box that builds or builds-and-saves a run packet; a builder form with template picker,
  seat checkboxes from the live catalog, steps, inputs, format, tone, notes. The tab states that the app never runs
  automations and produces no analysis. Verified in the browser: template prefill, save (201), card render with
  block, run packet built from typed input (3 seats, standing instruction, input echoed).

## Watch feed pass (2026-09-13, later)

- **NAVADMIN feed removed.** MyNavyHR has no public RSS or API for NAVADMINs or ALNAVs (the only DNN RSS on that host is a test feed), and the HTML scraper was blocked with HTTP 403, so the dashboard showed a "live" card with nothing behind it. The scraper, its routes, storage dir, and tickers are gone.
- **ALMAR feed added** in its place: official marines.mil RSS (same endpoint family as MARADMIN, category 14335) via `AlmarFeedService`, routes `/message-watch/almars/{feed,refresh}`, `almar_ticker` on the workspace payload, the overview card, and an `ALMAR RSS` row on the Watch page. Failures return warnings plus cached data rather than a 500.
- **NAVADMIN and ALNAV stay reachable** as portal-link rows on the Watch page (Open source button) and in the Messages & policy quick links; the rows say plainly that nothing is fetched.
- MARADMIN and ALMAR ticker ids now show the message number (parsed from the RSS header) instead of a tag list; the MARADMIN store drops older hash-keyed copies of a message when the numbered record lands.
