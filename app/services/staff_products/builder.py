from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.agents import Confidence, StructuredCitation
from app.schemas.product_templates import ProductTemplateRecord
from app.schemas.staff_products import (
    StaffProductDraftRequest,
    StaffProductDraftResponse,
    StaffProductSection,
    StaffProductType,
)
from app.services.agents.source_refs import (
    CORRESPONDENCE_REFERENCES,
    FORCE_PROTECTION_REFERENCES,
    G8_REFERENCES,
    IG_REFERENCES,
    LEADERSHIP_REFERENCES,
    LEGAL_REFERENCES,
    MAP_REFERENCES,
    MEDICAL_REFERENCES,
    OPORD_REFERENCES,
    ORM_REFERENCES,
    PAO_REFERENCES,
    S1_REFERENCES,
    S2_REFERENCES,
    S3_REFERENCES,
    S4_REFERENCES,
    SEL_REFERENCES,
    STAFF_PROCESS_REFERENCES,
    STAFF_PRODUCT_REFERENCES,
    TRAINING_REFERENCES,
    SourceRef,
    citation_titles,
    structured_citations,
)

OPORD_SECTIONS = [
    StaffProductSection(
        heading="1. Situation",
        prompts=["Area of interest/context", "Friendly forces", "Attachments/detachments", "Civil considerations"],
    ),
    StaffProductSection(
        heading="2. Mission",
        prompts=["Who, what, when, where, and why in one clear sentence"],
    ),
    StaffProductSection(
        heading="3. Execution",
        prompts=["Commander's intent", "Concept of operations", "Tasks", "Coordinating instructions"],
    ),
    StaffProductSection(
        heading="4. Administration and Logistics",
        prompts=["Supply", "Transportation", "Medical", "DTS/travel/admin support", "Reporting requirements"],
    ),
    StaffProductSection(
        heading="5. Command and Signal",
        prompts=["Command relationships", "PACE concept", "Reports", "Information management"],
    ),
]

WARNO_SECTIONS = [
    StaffProductSection(heading="Situation", prompts=["What changed or is expected to change?"]),
    StaffProductSection(heading="Mission / Task", prompts=["Likely task, purpose, and timeline"]),
    StaffProductSection(heading="Initial Timeline", prompts=["Key planning events and immediate suspenses"]),
    StaffProductSection(heading="Coordinating Instructions", prompts=["Required coordination and information needs"]),
]

FRAGO_SECTIONS = [
    StaffProductSection(
        heading="Changes",
        prompts=[
            "Only what changed from the base order",
            "State the command decision, changed task, or new control measure in plain language",
        ],
    ),
    StaffProductSection(
        heading="Tasks",
        prompts=[
            "Updated tasks by unit/staff section",
            "Use task, purpose, method, and no-later-than language where possible",
        ],
    ),
    StaffProductSection(
        heading="Coordinating Instructions",
        prompts=[
            "Updated timeline, control measures, reporting",
            "Call out what remains fixed across all subordinate units versus what may be refined locally",
        ],
    ),
]

CONOP_SECTIONS = [
    StaffProductSection(
        heading="1. Purpose and End State",
        prompts=["Supported mission or training problem", "Desired end state", "Main effort"],
    ),
    StaffProductSection(
        heading="2. Unit and Sub-Unit Relationships",
        prompts=[
            "Higher / supported / supporting relationships",
            "Subordinate tasks in Marine-staff language",
            "Coordination requirements and command relationships",
        ],
    ),
    StaffProductSection(
        heading="3. Concept of Execution",
        prompts=[
            "Phasing",
            "Main effort and supporting effort",
            "Decision points",
            "Control measures and required reports",
        ],
    ),
    StaffProductSection(
        heading="4. Support and Sustainment",
        prompts=["Logistics concept", "Medical support", "Reporting and accountability", "Comms dependencies"],
    ),
    StaffProductSection(
        heading="5. Assessment and Transition",
        prompts=["Measures of performance", "Measures of effectiveness", "AAR capture", "Follow-on refinement"],
    ),
]

SITREP_SECTIONS = [
    StaffProductSection(heading="Current Status", prompts=["What is true now?"]),
    StaffProductSection(heading="Significant Events", prompts=["What changed since the last report?"]),
    StaffProductSection(heading="Issues / Risks", prompts=["What needs command or staff attention?"]),
    StaffProductSection(heading="Next 24-72 Hours", prompts=["Expected activity, decisions, and support requirements"]),
]

RUNNING_ESTIMATE_SECTIONS = [
    StaffProductSection(
        heading="1. Current Situation",
        prompts=[
            "What is true now in this staff lane",
            "What command problem, event, or decision this estimate supports",
            "What part of the plan is stable versus still moving",
        ],
    ),
    StaffProductSection(
        heading="2. Changes Since Last Update",
        prompts=[
            "What changed since the last estimate or brief",
            "What assumption, support status, or timeline moved",
            "What changed command understanding rather than just adding noise",
        ],
    ),
    StaffProductSection(
        heading="3. Assumptions And Risks",
        prompts=[
            "Which assumptions still carry the plan",
            "Which risk is most likely and which risk is most severe",
            "What requires verification before this estimate drives action",
        ],
    ),
    StaffProductSection(
        heading="4. Supportability And Coordination",
        prompts=[
            "What this lane can support now",
            "What adjacent staff section support is required",
            "What friction point or unresolved dependency will break execution first",
        ],
    ),
    StaffProductSection(
        heading="5. Decisions Needed And Next 24-72 Hours",
        prompts=[
            "What decision, approval, or reprioritization is needed now",
            "What due-outs, owners, and suspenses are next",
            "What should happen in the next 24-72 hours before the estimate is refreshed",
        ],
    ),
]

AIR_SUPPORT_ESTIMATE_SECTIONS = [
    StaffProductSection(
        heading="1. Supported Aviation Effect And Event Frame",
        prompts=[
            "Supported event, desired aviation effect, and command purpose",
            "What supported unit or decision this aviation support exists to help",
            "What assumption most threatens aviation realism or supportability",
        ],
    ),
    StaffProductSection(
        heading="2. Supported Scheme, Control, And Timing",
        prompts=[
            "What phase, timeline window, or training objective the aviation support aligns to",
            "What control method, supported/supporting relationship, or approval path applies",
            "What timing issue or branch condition most affects the aviation portion",
        ],
    ),
    StaffProductSection(
        heading="3. Airspace, Comms, And Deconfliction",
        prompts=[
            "What airspace, range, fires, ground movement, and comm/PACE questions need resolution",
            "What S-3, S-6, safety, and supported-unit coordination must occur before execution",
            "What lost-comm, abort, or no-go condition should be explicit",
        ],
    ),
    StaffProductSection(
        heading="4. Risk, Supportability, And Fallbacks",
        prompts=[
            "What weather, visibility, med, landing-zone, or supportability risk matters most",
            "What condition stops the aviation portion instead of forcing fake or unsafe training",
            "What branch preserves training value if aviation support is reduced or cancelled",
        ],
    ),
    StaffProductSection(
        heading="5. Review, Rehearsal, And Follow-Through",
        prompts=[
            "Who is the qualified aviation reviewer and what is the latest useful review point",
            "What must be rehearsed before the estimate is treated as executable",
            "What note or due-out survives into the next staff sync or AAR",
        ],
    ),
]

AIR_GROUND_COORDINATION_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. Coordination Frame",
        prompts=[
            "Supported event, supported aviation effect, and why this matrix exists",
            "What relationship between air, ground, comm, and safety lanes must stay visible",
            "What friction point is most likely to break air-ground coordination first",
        ],
    ),
    StaffProductSection(
        heading="2. Coordination Rows",
        prompts=[
            "For each phase: supported unit, aviation role, control method, report, and owner",
            "What commander, S-3, AirO/ACE, S-6, safety, and medical touchpoint matters in each row",
            "What movement or fires deconfliction item needs resolution before the row is credible",
        ],
    ),
    StaffProductSection(
        heading="3. Comms, Control, And Deconfliction Checks",
        prompts=[
            "What PACE, report, or acknowledgement requirement governs the air-ground link",
            "What airspace, range, fires, or landing-zone issue creates the first no-go condition",
            "What fallback applies if comms, timing, or support changes under friction",
        ],
    ),
    StaffProductSection(
        heading="4. Risk And Branch Conditions",
        prompts=[
            "What weather, visibility, supportability, or training-value risk is driving command attention",
            "What branch or sequel applies if the aviation portion changes",
            "What trigger elevates immediately to command or qualified aviation review",
        ],
    ),
    StaffProductSection(
        heading="5. Rehearsal And Closeout",
        prompts=[
            "What must be rehearsed physically or talked through before execution",
            "What item remains a due-out after the matrix is published",
            "What evidence shows the coordination matrix actually held during the event",
        ],
    ),
]

AVIATION_SUPPORTABILITY_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. Supportability Frame",
        prompts=[
            "Supported event, ACE or aviation-supportability problem, and command decision",
            "What aviation capability or support assumption the plan is leaning on",
            "What shortfall is most likely to cancel or shrink the aviation contribution",
        ],
    ),
    StaffProductSection(
        heading="2. Sortie, Platform, And Crew Assumptions",
        prompts=[
            "What platform, crew, sortie, or support window assumptions apply",
            "What readiness, maintenance, or availability issue most affects supportability",
            "What assumption still requires qualified aviation confirmation",
        ],
    ),
    StaffProductSection(
        heading="3. Ground Integration And Support Dependencies",
        prompts=[
            "What landing-zone, embark, fuel, ordnance, comm, med, or support dependency matters most",
            "What GCE, LCE, S-3, S-4, S-6, and safety coordination is required",
            "What dependency is being hand-waved and needs a real owner",
        ],
    ),
    StaffProductSection(
        heading="4. Risk, No-Go, And Branch Logic",
        prompts=[
            "What weather, supportability, maintenance, or deconfliction risk is most severe",
            "What no-go condition stops the aviation contribution before it becomes false realism",
            "What branch preserves training or exercise value if supportability drops",
        ],
    ),
    StaffProductSection(
        heading="5. Review And Decision Support",
        prompts=[
            "What command decision or support cut/rephase decision this matrix supports",
            "What must be reviewed by aviation authorities before publication is treated as useful",
            "What next due-out or brief line survives after this matrix is complete",
        ],
    ),
]

SYNCHRONIZATION_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. Event Frame And Command Focus",
        prompts=[
            "Supported event, command focus, and planning horizon",
            "Main effort, supporting effort, and what is being protected first",
            "What this matrix is supposed to synchronize rather than merely list",
        ],
    ),
    StaffProductSection(
        heading="2. Timeline And Battle Rhythm",
        prompts=[
            "Key phases, suspenses, and review points",
            "What must happen before drill, during drill, before execution, and at closeout",
            "Which timeline point is most likely to slip first",
        ],
    ),
    StaffProductSection(
        heading="3. Staff Lanes And Required Actions",
        prompts=[
            "Lane-by-lane tasks for S-1, S-3, S-4, S-6, safety, medical, and other required sections",
            "Owner, suspense, command touchpoint, and required report for each action",
            "What adjacent coordination is required before each task is considered complete",
        ],
    ),
    StaffProductSection(
        heading="4. Decision Points And Friction",
        prompts=[
            "What commander or XO decisions must occur at each key point",
            "What friction is most likely to break the timeline or change scope",
            "What gets cut or deferred if time or support collapses",
        ],
    ),
    StaffProductSection(
        heading="5. Closeout And Follow-Through",
        prompts=[
            "What must be complete before the matrix can be closed",
            "What due-outs survive to the next drill or next planning cycle",
            "What AAR or turnover item must be captured while the facts are still fresh",
        ],
    ),
]

ADMIN_ESTIMATE_SECTIONS = [
    StaffProductSection(
        heading="1. Admin Frame And Supported Event",
        prompts=[
            "Supported event, command problem, and what the S-1/admin lane must protect first",
            "What part of the admin picture is stable and what is still moving",
            "What admin fact changes execution reality instead of remaining background noise",
        ],
    ),
    StaffProductSection(
        heading="2. Accountability, Rosters, And Orders",
        prompts=[
            "Roster and accountability posture",
            "Orders coverage, routing posture, and signature status",
            "What attendance, orders, or manpower assumption is still too optimistic",
        ],
    ),
    StaffProductSection(
        heading="3. Travel, DTS, GTCC, And Records",
        prompts=[
            "Travel-admin posture, DTS/GTCC friction, and records or continuity requirements",
            "What voucher, authorization, receipt, or card issue still needs visibility",
            "Which admin file, tracker, or report must be refreshed before next drill",
        ],
    ),
    StaffProductSection(
        heading="4. Risks, Dependencies, And Suspenses",
        prompts=[
            "What admin risk or late package can still hijack the event",
            "What adjacent section support or commander decision is required",
            "Which suspense matters most to the next command touchpoint",
        ],
    ),
    StaffProductSection(
        heading="5. Decisions And Next 24-72 Hours",
        prompts=[
            "What decision, reprioritization, or escalation is needed now",
            "What due-outs survive into the next drill or next admin cycle",
            "What the S-1 lane must do in the next 24-72 hours to stay ahead of drift",
        ],
    ),
]

ORM_WORKSHEET_SECTIONS = [
    StaffProductSection(
        heading="1. Event Frame And Hazard Context",
        prompts=[
            "Supported event, commander concern, and what the worksheet is meant to protect",
            "What hazard or condition matters most right now",
            "What part of the risk picture is stable versus still moving",
        ],
    ),
    StaffProductSection(
        heading="2. Hazards And Initial Assessment",
        prompts=[
            "Named hazards by phase or lane",
            "Initial severity, probability, and who is exposed",
            "What hazard becomes more dangerous when the schedule slips or support degrades",
        ],
    ),
    StaffProductSection(
        heading="3. Controls And Owners",
        prompts=[
            "Control measures, who owns them, and when they are verified",
            "What control exists only on paper versus in trained execution",
            "What adjacent staff support is required for controls to hold",
        ],
    ),
    StaffProductSection(
        heading="4. Residual Risk And Decision Points",
        prompts=[
            "What risk remains after controls are applied",
            "What risk is acceptable, by whom, and at what review point",
            "What changes the commander decision from acceptable friction to no-go",
        ],
    ),
    StaffProductSection(
        heading="5. Rehearsal And Verification",
        prompts=[
            "What must be rehearsed before execution",
            "What stop-training or halt condition must be briefed explicitly",
            "What gets rechecked if tempo, weather, support, or location changes",
        ],
    ),
]

NO_GO_CRITERIA_SECTIONS = [
    StaffProductSection(
        heading="1. Command No-Go Frame",
        prompts=[
            "Supported event, command intent, and why no-go criteria are being formalized",
            "What the commander is unwilling to accept",
            "What condition forces pause, modification, or cancellation",
        ],
    ),
    StaffProductSection(
        heading="2. Universal Stop Conditions",
        prompts=[
            "Positive control, communications, accountability, medical response, and supervision thresholds",
            "What baseline must hold for the event to continue",
            "What threshold is easy to ignore until it is already too late",
        ],
    ),
    StaffProductSection(
        heading="3. Event-Specific No-Go Conditions",
        prompts=[
            "Range, vehicle, overnight, environmental, or public-event conditions that change the decision",
            "What support or site condition invalidates the current control plan",
            "What branch condition moves this from friction to stop-training authority",
        ],
    ),
    StaffProductSection(
        heading="4. Decision Authority And Escalation",
        prompts=[
            "Who can stop, pause, modify, or resume the event",
            "How the no-go call is passed and acknowledged",
            "What must be elevated immediately to command",
        ],
    ),
    StaffProductSection(
        heading="5. Revalidation And Restart Conditions",
        prompts=[
            "What must be true before activity resumes",
            "What gets rechecked after a halt",
            "What remains no-go for the rest of the event even if conditions improve",
        ],
    ),
]

RESIDUAL_RISK_DECISION_NOTE_SECTIONS = [
    StaffProductSection(
        heading="1. Decision Problem",
        prompts=[
            "What residual risk decision is required now",
            "What hazard picture and control posture led to this note",
            "What happens if the decision is deferred",
        ],
    ),
    StaffProductSection(
        heading="2. Residual Risk Summary",
        prompts=[
            "What risk remains after controls",
            "Which residual risk is most severe versus most likely",
            "What assumption still carries too much of the commander’s comfort",
        ],
    ),
    StaffProductSection(
        heading="3. Options, Limits, And Tradeoffs",
        prompts=[
            "What can be accepted, reduced, modified, deferred, or cut",
            "What each choice protects and what it gives up",
            "What event standard changes if the commander accepts the risk",
        ],
    ),
    StaffProductSection(
        heading="4. Recommendation And Authority",
        prompts=[
            "What the staff recommends",
            "Who must accept or reframe the residual risk",
            "What trigger forces the decision back to command",
        ],
    ),
    StaffProductSection(
        heading="5. Follow-Through",
        prompts=[
            "What changes immediately after the decision",
            "What must be briefed to leaders and controllers",
            "What gets tracked through rehearsal and execution to ensure the decision remains valid",
        ],
    ),
]

REHEARSAL_SAFETY_BRIEF_SECTIONS = [
    StaffProductSection(
        heading="1. Event And Safety Frame",
        prompts=[
            "Supported event, safety posture, and why this rehearsal brief matters",
            "What leaders, controllers, and participants must understand before start",
            "What risk area will matter most during the first hour",
        ],
    ),
    StaffProductSection(
        heading="2. Hazards, Controls, And Watch Items",
        prompts=[
            "Top hazards, control measures, and who is watching them",
            "What control requires active supervision instead of one-time briefing",
            "What condition makes the written safety plan unreliable under friction",
        ],
    ),
    StaffProductSection(
        heading="3. Emergency And Stop-Training Actions",
        prompts=[
            "Emergency actions, lost-comm actions, lost-accountability actions, and medical actions",
            "Who can call stop-training and how the call is passed",
            "What first report and first movement action must happen immediately",
        ],
    ),
    StaffProductSection(
        heading="4. Rehearsal Checks And Verification",
        prompts=[
            "What gets rehearsed physically before execution",
            "What communication, control, or med-response action must be verified on the ground",
            "What must be rechecked if the plan shifts during execution",
        ],
    ),
    StaffProductSection(
        heading="5. Command Notes And Revalidation",
        prompts=[
            "What the commander or OIC should re-ask before go-time",
            "What no-go criteria and residual-risk decisions remain in force",
            "What post-rehearsal correction must happen before the event can be called ready",
        ],
    ),
]

ADMIN_TASK_TRACKER_SECTIONS = [
    StaffProductSection(
        heading="1. Tracking Standard And Command Focus",
        prompts=[
            "Supported event, command focus, and what this tracker exists to protect",
            "What qualifies as a real admin task versus a background reminder",
            "What owner, suspense, and status standard each line must meet",
        ],
    ),
    StaffProductSection(
        heading="2. Critical Admin Tasks",
        prompts=[
            "Roster, orders, travel, DTS/GTCC, accountability, awards, FitRep, or readiness tasks due this cycle",
            "Owner, suspense, status, and command review point for each line",
            "Which admin task matters most to the next drill or command brief",
        ],
    ),
    StaffProductSection(
        heading="3. Slippage, Friction, And Escalation",
        prompts=[
            "What is late, blocked, or being quietly assumed complete",
            "What admin issue requires direct S-1 chief, XO, or commander visibility",
            "What missed suspense changes event feasibility or command posture",
        ],
    ),
    StaffProductSection(
        heading="4. Continuity And Turnover",
        prompts=[
            "What the next drill cycle or relieving admin lead must inherit clearly",
            "What has already been elevated and should not be rediscovered from scratch",
            "What item is waiting on command signature versus staff action",
        ],
    ),
    StaffProductSection(
        heading="5. Closeout And Follow-Through",
        prompts=[
            "What makes a task actually complete",
            "What evidence, routing confirmation, or receipt closes the line",
            "What unfinished item survives to the next cycle and under whose ownership",
        ],
    ),
]

ROUTING_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. Routing Frame",
        prompts=[
            "What packages are being routed and why they matter to this event or command cycle",
            "What routing chain, reviewer, and signature authority apply",
            "What package is most likely to slip first",
        ],
    ),
    StaffProductSection(
        heading="2. Package Inventory And Owners",
        prompts=[
            "Orders, awards, FitReps, travel documents, correspondence, or other formal packages in scope",
            "Owner, reviewer, routing chain, and suspense for each package",
            "What package depends on outside inputs before it can move",
        ],
    ),
    StaffProductSection(
        heading="3. Bottlenecks, Dependencies, And Risk",
        prompts=[
            "What stale roster, missing signature, or missing attachment will stop routing cold",
            "What must be coordinated with S-3, S-4, XO, or command group before routing",
            "What package delay changes execution or command visibility",
        ],
    ),
    StaffProductSection(
        heading="4. Status, Escalation, And Turnover",
        prompts=[
            "Current status by package",
            "What gets elevated if a suspense slips",
            "What turnover note keeps the next admin cycle from restarting the routing fight",
        ],
    ),
    StaffProductSection(
        heading="5. Closeout Criteria",
        prompts=[
            "What proof closes each routing line",
            "What package is complete, pending command action, or still blocked",
            "What routing burden survives to the next drill or reporting cycle",
        ],
    ),
]

PRE_DRILL_ADMIN_READINESS_CHECK_SECTIONS = [
    StaffProductSection(
        heading="1. Pre-Drill Admin Posture",
        prompts=[
            "What the admin lane must have true before drill begins",
            "What roster, orders, routing, or travel fact is most likely to surprise the unit late",
            "What the commander or XO should know before Marines arrive",
        ],
    ),
    StaffProductSection(
        heading="2. Accountability And Roster Checks",
        prompts=[
            "Attendance, accountability, and contact-data checks",
            "What roster issue still needs resolution",
            "What must be confirmed before the first formation or planning event",
        ],
    ),
    StaffProductSection(
        heading="3. Orders, Routing, And Travel Checks",
        prompts=[
            "Orders, routing packages, signatures, DTS, vouchers, GTCC, and travel-admin checks",
            "What is complete, what is pending, and what is blocked",
            "What admin item becomes visible only after Marines disperse if not caught now",
        ],
    ),
    StaffProductSection(
        heading="4. Continuity, Records, And Suspenses",
        prompts=[
            "Records, trackers, continuity files, and required references to verify before drill",
            "What suspense is nearest or easiest to miss",
            "What note must survive into after-drill follow-through",
        ],
    ),
    StaffProductSection(
        heading="5. No-Surprise Standard",
        prompts=[
            "What must be true for the admin lane to call itself ready",
            "What issue gets elevated before drill rather than explained during drill",
            "What immediate follow-up happens if a check fails",
        ],
    ),
]

TROOP_FLOW_CHECKLIST_SECTIONS = [
    StaffProductSection(
        heading="1. Event Frame And Marine Flow",
        prompts=[
            "Supported event, audience, and what Marine flow this checklist is protecting",
            "What the first formation, main movement, and release sequence must accomplish",
            "What friction point is most likely to cause confusion, bunching, or lost accountability",
        ],
    ),
    StaffProductSection(
        heading="2. Formation And Muster Checks",
        prompts=[
            "First formation time, location, uniform, and reporting standard",
            "Who controls muster, headcount verification, and reporting upward",
            "What must be corrected before Marines are moved to the next phase",
        ],
    ),
    StaffProductSection(
        heading="3. Movement, Holding, And Release Checks",
        prompts=[
            "Where Marines move, wait, report, and recover during each major phase",
            "Who releases, who receives, and how accountability is re-established at each move",
            "What support dependency most threatens troop flow if it slips",
        ],
    ),
    StaffProductSection(
        heading="4. Standards, Welfare, And Intervention Points",
        prompts=[
            "What standards the SEL needs enforced before movement or public-facing execution",
            "What welfare, chow, transport, or fatigue issue becomes a command issue if ignored",
            "What condition forces an intervention instead of letting the event continue to drift",
        ],
    ),
    StaffProductSection(
        heading="5. Final Accountability And Follow-Through",
        prompts=[
            "How the unit closes accountability, release authority, and unresolved Marine issues",
            "What issue survives into turnover or follow-up after dismissal",
            "What the next leader in the chain must know before the event is declared complete",
        ],
    ),
]

FORMATION_TRANSITION_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. Transition Frame",
        prompts=[
            "Supported event, key formations, and major transitions to control",
            "What sequence discipline matters most to the commander's standard",
            "What transition is most likely to fail first under time pressure",
        ],
    ),
    StaffProductSection(
        heading="2. Formation Control Rows",
        prompts=[
            "For each formation: trigger, location, owner, required standard, and report",
            "What must be verified before the unit may move out of that formation",
            "What issue needs immediate SEL correction before the next phase",
        ],
    ),
    StaffProductSection(
        heading="3. Movement And Handoff Rows",
        prompts=[
            "For each transition: releasing leader, receiving leader, accountability method, and timing",
            "What support, comm, or safety dependency affects the handoff",
            "What fallback applies if the transition degrades or compresses",
        ],
    ),
    StaffProductSection(
        heading="4. Standards And Marine-Impact Checks",
        prompts=[
            "What standard, protocol, or discipline check must remain visible at each transition",
            "What Marines will feel first if the transition control is weak",
            "What confusion point needs a simple corrective control instead of a speech",
        ],
    ),
    StaffProductSection(
        heading="5. Release And Reset",
        prompts=[
            "How final release, straggler resolution, and accountability closeout are handled",
            "What unresolved issue carries into turnover or the next battle-rhythm window",
            "What evidence shows the transition matrix actually held during execution",
        ],
    ),
]

LEADER_TOUCHPOINT_PLAN_SECTIONS = [
    StaffProductSection(
        heading="1. Leader Touchpoint Frame",
        prompts=[
            "Supported event, leader chain, and what this touchpoint plan exists to protect",
            "What standards, accountability, or welfare concerns need repeated leader attention",
            "What point in the event most needs deliberate leader presence",
        ],
    ),
    StaffProductSection(
        heading="2. Pre-Execution Touchpoints",
        prompts=[
            "What leaders confirm before first formation, movement, or execution begins",
            "What standards, uniform, support, or accountability issue gets solved before Marines are committed",
            "Who needs to hear the same guidance before the event starts moving",
        ],
    ),
    StaffProductSection(
        heading="3. Phase-Change Touchpoints",
        prompts=[
            "What leaders verify at each phase change or location change",
            "What Marine issue, discipline issue, or support issue triggers immediate intervention",
            "How the SEL keeps the chain aligned when the schedule compresses",
        ],
    ),
    StaffProductSection(
        heading="4. Welfare, Discipline, And Capacity Checks",
        prompts=[
            "What signs show Marines are overloaded, confused, or not absorbing the weekend well",
            "What welfare or standards issue rises from informal correction to command visibility",
            "What the SEL must protect so the event stays realistic for reserve Marines",
        ],
    ),
    StaffProductSection(
        heading="5. Release, Turnover, And Next Follow-Through",
        prompts=[
            "What leaders confirm before dismissal and release",
            "What issue must be handed off to the next day, next drill, or command group",
            "What touchpoint should be preserved as a repeatable standard for the next event",
        ],
    ),
]

DECISION_SUPPORT_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. Decision Frame",
        prompts=[
            "Supported event, command problem, and why a decision is needed now",
            "What the commander or XO is actually deciding instead of what the staff wishes they would notice",
            "What happens if the decision slips to the next review point",
        ],
    ),
    StaffProductSection(
        heading="2. Current Picture And Friction",
        prompts=[
            "What changed, what is stable, and what friction is forcing the decision",
            "Which staff assumption is still carrying too much weight",
            "What branch condition, shortfall, or timing issue is driving command attention",
        ],
    ),
    StaffProductSection(
        heading="3. Options, Cuts, And Tradeoffs",
        prompts=[
            "What options, cuts, deferrals, or risk-acceptance choices exist",
            "What each option protects and what each option gives up",
            "Which option is most supportable inside the reserve timeline",
        ],
    ),
    StaffProductSection(
        heading="4. Recommendation And Decision Triggers",
        prompts=[
            "What the staff recommends and why",
            "What trigger elevates the issue immediately instead of waiting for the next huddle",
            "What information would change the recommendation",
        ],
    ),
    StaffProductSection(
        heading="5. Immediate Actions After Decision",
        prompts=[
            "What must happen in the first hour after a decision is made",
            "Who gets tasked, informed, or redirected",
            "What product, brief, or turnover note must be updated immediately",
        ],
    ),
]

DUE_OUT_TRACKER_SECTIONS = [
    StaffProductSection(
        heading="1. Command Focus And Tracking Standard",
        prompts=[
            "Supported event, command focus, and what this tracker exists to protect",
            "What qualifies as a real due-out versus background noise",
            "What ownership, suspense, and command-touchpoint standard every line must meet",
        ],
    ),
    StaffProductSection(
        heading="2. Critical Due-Outs",
        prompts=[
            "What products, asks, or coordination actions are due this cycle",
            "Owner, suspense, status, and command review point for each line",
            "Which due-out matters most to the next commander or XO touchpoint",
        ],
    ),
    StaffProductSection(
        heading="3. Drift, Slippage, And Escalation",
        prompts=[
            "What is late, at risk, or being quietly assumed complete",
            "What shortfall requires chief or battle-captain intervention now",
            "What missed suspense changes scope, risk, or briefing posture",
        ],
    ),
    StaffProductSection(
        heading="4. Turnover And Continuity",
        prompts=[
            "What the relieving watch or next drill cycle must inherit clearly",
            "What has already been elevated and should not be re-litigated from zero",
            "What item is waiting on command decision versus staff action",
        ],
    ),
    StaffProductSection(
        heading="5. Closeout Criteria",
        prompts=[
            "What makes a due-out actually complete",
            "What evidence, review, or confirmation closes the line",
            "What unfinished item survives into the next cycle and under whose ownership",
        ],
    ),
]

COLLECTION_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. Intelligence Problem Frame",
        prompts=[
            "Command question, planning problem, and supported decision",
            "What the staff needs to know that it does not know yet",
            "What public-source, training, or approved collection boundaries apply",
        ],
    ),
    StaffProductSection(
        heading="2. PIR, IR, And Indicators",
        prompts=[
            "Priority intelligence requirements and information requirements",
            "Indicators or warnings that confirm or disconfirm the assessment",
            "Which indicator matters most to the next commander decision",
        ],
    ),
    StaffProductSection(
        heading="3. Collection Tasks And Owners",
        prompts=[
            "What must be collected, by whom, and by when",
            "Which lane owns each collection task or source check",
            "What report, update, or estimate the collection will feed",
        ],
    ),
    StaffProductSection(
        heading="4. Gaps, Caveats, And Confidence",
        prompts=[
            "Which gaps remain unresolved",
            "What source caveat or confidence limit applies",
            "What assumption changes if the collection comes back differently than expected",
        ],
    ),
    StaffProductSection(
        heading="5. Decision Support And Refresh",
        prompts=[
            "What decision point this matrix supports",
            "When the collection picture must be refreshed",
            "What should be elevated to the commander, XO, or S-3 immediately",
        ],
    ),
]

SUSTAINMENT_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. Sustainment Frame",
        prompts=[
            "Supported event, concept, and sustainment objective",
            "What support must work for the event to remain executable",
            "What resource is most likely to become the critical path",
        ],
    ),
    StaffProductSection(
        heading="2. Movement And Distribution",
        prompts=[
            "Who moves, when, by what means, and under what accountability method",
            "Movement table or distribution flow by phase",
            "What assumptions exist about drivers, vehicles, recovery, or return-to-home-station timing",
        ],
    ),
    StaffProductSection(
        heading="3. Supply, Maintenance, And Services",
        prompts=[
            "Equipment, supply, maintenance, chow, billeting, water, and issue/turn-in requirements",
            "Which support request has the longest lead time",
            "What mandatory support cannot be replaced by local improvisation",
        ],
    ),
    StaffProductSection(
        heading="4. Coordination, Dependencies, And Risk",
        prompts=[
            "What S-1, S-3, S-6, medical, safety, or external coordination is required",
            "What shortfall changes scope versus cancels the event",
            "What unresolved logistics risk needs command visibility",
        ],
    ),
    StaffProductSection(
        heading="5. Recovery, Reset, And Follow-Through",
        prompts=[
            "Recovery timeline, reset burden, and remaining support debt",
            "What must be closed before the event is truly complete",
            "What follow-on sustainment due-outs survive into the next drill",
        ],
    ),
]

MOVEMENT_TABLE_SECTIONS = [
    StaffProductSection(
        heading="1. Movement Frame",
        prompts=[
            "Supported event, movement purpose, and what the table is protecting",
            "What movement assumption most threatens timely execution",
            "What report or accountability method governs each move",
        ],
    ),
    StaffProductSection(
        heading="2. Movement Rows",
        prompts=[
            "For each move: element, origin, destination, no-later-than time, and transport method",
            "What leader owns release, arrival confirmation, and accountability closeout",
            "What vehicle, driver, or staging shortfall is most likely to break the sequence",
        ],
    ),
    StaffProductSection(
        heading="3. Support And Coordination Dependencies",
        prompts=[
            "What billeting, chow, loading, unloading, or recovery dependency affects movement timing",
            "What S-1, S-3, S-4, S-6, safety, or medical coordination is tied to each move",
            "What support request must be confirmed before the movement table is credible",
        ],
    ),
    StaffProductSection(
        heading="4. Friction, Fallbacks, And Reporting",
        prompts=[
            "What delay, breakdown, weather, or accountability friction changes the plan first",
            "What primary and fallback movement method or sequencing adjustment exists",
            "What missed-report or late-arrival trigger requires command visibility",
        ],
    ),
    StaffProductSection(
        heading="5. Recovery And Reset",
        prompts=[
            "Return-to-home-station, vehicle recovery, and reset timeline",
            "What movement issue survives into the next day or next drill",
            "What evidence closes each movement line as complete",
        ],
    ),
]

MEDICAL_ESTIMATE_SECTIONS = [
    StaffProductSection(
        heading="1. Medical Support Frame",
        prompts=[
            "Supported event, casualty profile, and medical support objective",
            "What medical reality most affects the plan right now",
            "What qualified coverage, equipment, or authority assumption still needs confirmation",
        ],
    ),
    StaffProductSection(
        heading="2. Risks, Treatment, And TCCC Considerations",
        prompts=[
            "Most likely casualty or injury scenarios",
            "Immediate life-threat, treatment, and trauma-gear considerations at a training-safe level",
            "What TCCC knowledge or awareness refresh leaders and key personnel need before execution",
            "What medical risk is most severe even if it is less likely",
        ],
    ),
    StaffProductSection(
        heading="3. CASEVAC, MEDEVAC, And Reporting",
        prompts=[
            "CASEVAC / MEDEVAC check: trigger, request path, movement method, and accountability owner",
            "Casualty collection points, handoff points, and movement methods",
            "9-line or casualty reporting responsibilities at a generic planning level",
            "What comm, terrain, transport, or timing assumption weakens the evacuation concept",
        ],
    ),
    StaffProductSection(
        heading="4. Command Decisions And Rehearsal Checks",
        prompts=[
            "What stop-training, movement, or escalation decision needs command visibility",
            "What must be rehearsed before this estimate is treated as executable",
            "Who makes the first hard call and who receives the report",
        ],
    ),
    StaffProductSection(
        heading="5. Coordination And Follow-Through",
        prompts=[
            "What coordination trigger list should force command, S-4, S-6, safety, or qualified medical review",
            "What coordination is required with S-3, S-4, S-6, safety, and command",
            "What due-outs remain before execution",
            "What medical lesson or corrective action should carry into the next event",
        ],
    ),
]

CASEVAC_QUICK_CARD_SECTIONS = [
    StaffProductSection(
        heading="1. Event And Casualty Frame",
        prompts=[
            "Supported event, likely casualty scenario, and what this quick card is for",
            "Who makes the first casualty call and who receives the first report",
            "What immediate condition changes the event from training problem to command problem",
        ],
    ),
    StaffProductSection(
        heading="2. Immediate Actions",
        prompts=[
            "What trained responders, leaders, and nearby Marines do first at a training-safe level",
            "What stop-training, scene-control, or escalation action happens immediately",
            "What trauma gear, aid source, or support assumption must already be true",
        ],
    ),
    StaffProductSection(
        heading="3. CASEVAC / MEDEVAC Call And Movement",
        prompts=[
            "Generic 9-line or casualty-report flow, sender, validator, and update path",
            "Casualty collection point, handoff point, pickup logic, and movement method",
            "What terrain, comm, vehicle, or timing factor weakens the evacuation concept first",
        ],
    ),
    StaffProductSection(
        heading="4. Accountability And Command Triggers",
        prompts=[
            "Who tracks the casualty, the element, and the change to the event picture",
            "What trigger elevates immediately to commander, XO, OIC/RSO, safety, or doc/surgeon",
            "What condition forces pause, modification, or termination of training",
        ],
    ),
    StaffProductSection(
        heading="5. Rehearsal And Use Notes",
        prompts=[
            "What must be rehearsed before this quick card is trusted under stress",
            "What assumptions require qualified medical review before execution",
            "What note keeps the quick card useful without pretending to be clinical direction",
        ],
    ),
]

RELIGIOUS_SUPPORT_PLAN_SECTIONS = [
    StaffProductSection(
        heading="1. Religious Support Frame",
        prompts=[
            "Supported event, population, and religious-support objective",
            "What morale, ethical, or confidential-support reality matters most to the event",
            "What command assumption about support access still needs to be tested",
        ],
    ),
    StaffProductSection(
        heading="2. Support Access And Coverage",
        prompts=[
            "How Marines, Sailors, or families access chaplain support during the event",
            "What schedule, location, or movement issue most affects support access",
            "What support demand is likely enough to require deliberate planning instead of goodwill",
        ],
    ),
    StaffProductSection(
        heading="3. Confidentiality, Referral, And Boundaries",
        prompts=[
            "What confidentiality or privileged-communication boundary must be explicit",
            "What issue belongs to chaplain support, medical, behavioral health, SJA, or the chain of command",
            "What trigger elevates immediately because the concern is beyond routine morale support",
        ],
    ),
    StaffProductSection(
        heading="4. Command, Ceremony, And Casualty-Adjacent Touchpoints",
        prompts=[
            "What ceremony, memorial, casualty, or family-support requirement should remain visible",
            "What public, command, or family touchpoint needs chaplain coordination",
            "What event condition creates the first real need for command-chaplain synchronization",
        ],
    ),
    StaffProductSection(
        heading="5. Follow-Through And Continuity",
        prompts=[
            "What chaplain or RP follow-through survives after the event",
            "What note or referral must carry into the next drill or command update",
            "What lesson should be preserved for the next similar event",
        ],
    ),
]

RMT_SUPPORT_MATRIX_SECTIONS = [
    StaffProductSection(
        heading="1. RMT Support Frame",
        prompts=[
            "Supported event, RMT support problem, and what this matrix exists to coordinate",
            "What chaplain-support or movement assumption most threatens continuity",
            "What command or support relationship should be explicit",
        ],
    ),
    StaffProductSection(
        heading="2. Support Rows And Schedule",
        prompts=[
            "For each support window: service, movement, location, owner, and required support",
            "What RP, chaplain, driver, comm, or access requirement applies to each row",
            "What row is most likely to fail if left informal",
        ],
    ),
    StaffProductSection(
        heading="3. Logistics, Movement, And Access Checks",
        prompts=[
            "What transport, billeting, chow, escort, or access-control issue affects RMT support",
            "What S-1, S-4, provost, medical, or command coordination is required",
            "What dependency still needs confirmation before the matrix is useful",
        ],
    ),
    StaffProductSection(
        heading="4. Welfare, Referral, And Continuity Triggers",
        prompts=[
            "What morale, casualty, memorial, or family-support condition changes the support demand",
            "What trigger requires chaplain, RP, medical, or command follow-up now",
            "What continuity note must survive a watch change or drill break",
        ],
    ),
    StaffProductSection(
        heading="5. Review And Follow-Through",
        prompts=[
            "What must be reviewed with chaplain, RP, and command before execution",
            "What unresolved support issue survives after the event",
            "What evidence shows the support matrix helped instead of existing on paper",
        ],
    ),
]

MORALE_WELFARE_ESTIMATE_SECTIONS = [
    StaffProductSection(
        heading="1. Morale And Welfare Frame",
        prompts=[
            "Supported event, formation, and what this estimate is trying to illuminate",
            "What morale, welfare, fatigue, family, or ethical tension matters most right now",
            "What issue changes command judgment if it gets worse",
        ],
    ),
    StaffProductSection(
        heading="2. Marine-Impact Indicators",
        prompts=[
            "What behavior, friction, or support signal suggests Marines are absorbing the plan poorly",
            "What reserve-specific stressor, tempo issue, or continuity gap matters most",
            "What indicator is most likely to be visible before a formal complaint or crisis",
        ],
    ),
    StaffProductSection(
        heading="3. Support, Referral, And Boundary Notes",
        prompts=[
            "What support channel should be primary: chaplain, RP, medical, behavioral health, or command",
            "What confidentiality or dignity boundary should stay explicit",
            "What issue must be routed carefully rather than discussed casually in staff traffic",
        ],
    ),
    StaffProductSection(
        heading="4. Command Considerations And Interventions",
        prompts=[
            "What leader intervention, touchpoint, or support adjustment should happen now",
            "What ceremony, casualty, memorial, family, or high-stress event changes the estimate",
            "What condition requires command visibility before morale damage compounds",
        ],
    ),
    StaffProductSection(
        heading="5. Continuity And Follow-Through",
        prompts=[
            "What note should survive into the next drill, AAR, or command update",
            "What welfare trend or unresolved tension needs continued observation",
            "What support action needs an owner before the estimate is closed",
        ],
    ),
]

ROAD_TO_WAR_BRIEF_SECTIONS = [
    StaffProductSection(
        heading="Slide 1. Strategic Setting And Why This Scenario Matters",
        prompts=[
            "What region, theater, or fictional setting this brief level-sets",
            "Why the scenario matters to U.S., naval, Marine, or partner interests",
            "What single strategic tension or crisis dynamic the audience must understand first",
        ],
    ),
    StaffProductSection(
        heading="Slide 2. Historical And Political Context",
        prompts=[
            "What historical grievance, political fracture, or recurring dispute shaped the current problem",
            "What recent trigger event, escalation, or governance problem moved the scenario toward crisis",
            "What context the unit needs to know without drowning the audience in background trivia",
        ],
    ),
    StaffProductSection(
        heading="Slide 3. Key Actors, Interests, And Alignment",
        prompts=[
            "Who the primary state, non-state, partner, civilian, and outside-power actors are",
            "What each actor wants, fears, or is trying to prevent",
            "What alignment, proxy, or alliance relationship most changes the problem for Marines on entry",
        ],
    ),
    StaffProductSection(
        heading="Slide 4. Operational Environment And Civil Frame",
        prompts=[
            "What terrain, infrastructure, population, weather, littoral, or access features matter most",
            "What civil, information, or governance factor will shape first contact with the scenario",
            "What OE fact matters immediately to a unit jumping in before a fuller IPB or CPB exists",
        ],
    ),
    StaffProductSection(
        heading="Slide 5. Adversary, Threat Methods, And Escalation Pattern",
        prompts=[
            "What threat behavior, capability, or coercive method the unit should expect first",
            "What hybrid, irregular, conventional, information, or proxy pattern defines the scenario",
            "What assumption about enemy intent or escalation still needs validation",
        ],
    ),
    StaffProductSection(
        heading="Slide 6. Friendly Posture, MAGTF Frame, And Constraints",
        prompts=[
            "What higher mission, partner posture, or joint/naval frame the unit enters under",
            "How CE/C2, GCE, ACE, and LCE are likely to matter at first contact",
            "What legal, political, sustainment, distance, or access constraint most affects Marine options",
        ],
    ),
    StaffProductSection(
        heading="Slide 7. What This Means For The Unit",
        prompts=[
            "What problem the unit is inheriting on arrival",
            "What assumptions, risks, and information gaps should shape the unit's first estimate or mission analysis",
            "What commanders and staff sections need to watch immediately in the first 24-72 hours",
        ],
    ),
]

PUBLIC_AFFAIRS_PLAN_SECTIONS = [
    StaffProductSection(
        heading="1. Command Frame And Release Authority",
        prompts=[
            "Supported event, command intent, and public posture for the event or issue",
            "What release authority, approval chain, and commander guidance apply",
            "What public question or media interest is most likely to force a decision first",
        ],
    ),
    StaffProductSection(
        heading="2. Audience, Media, And Visitor Posture",
        prompts=[
            "Primary internal and external audiences",
            "Expected media, visitor, or VIP presence and what level of access is acceptable",
            "What escort, imagery, or timeline friction will matter to PAO, S-3, and force protection",
        ],
    ),
    StaffProductSection(
        heading="3. Themes, Messages, And Response Lines",
        prompts=[
            "Approved themes and messages",
            "Likely media, public, or higher-headquarters questions and response-to-query lines",
            "What should be said, what should be deferred, and what needs commander review first",
        ],
    ),
    StaffProductSection(
        heading="4. OPSEC, Imagery, And Approval Controls",
        prompts=[
            "What information, imagery, locations, or timelines require extra control",
            "How OPSEC, legal, and release review will occur before public release",
            "What imagery-handling, social-media, or visitor-boundary rule must be explicit",
        ],
    ),
    StaffProductSection(
        heading="5. Execution, Contingencies, And Follow-Through",
        prompts=[
            "Who speaks, who escorts, who approves, and who captures the event",
            "What to do if facts change, an incident occurs, or media attention spikes",
            "What after-action, archive, or next-touchpoint requirement remains after execution",
        ],
    ),
]

SECURITY_ANNEX_SECTIONS = [
    StaffProductSection(
        heading="1. Security Frame And Supported Event",
        prompts=[
            "Supported event, security objective, and command posture",
            "What the annex is protecting first: people, access, equipment, information, or movement",
            "What security assumption most threatens execution if it proves false",
        ],
    ),
    StaffProductSection(
        heading="2. Access Control And Visitor Management",
        prompts=[
            "Entry points, control measures, badge or roster checks, and escort requirements",
            "Visitor, VIP, contractor, media, or partner access rules",
            "What force-protection, legal, and commander approval boundaries apply",
        ],
    ),
    StaffProductSection(
        heading="3. Movement, Traffic, And Parking Control",
        prompts=[
            "Vehicle flow, parking control, staging, pedestrian safety, and choke points",
            "Who controls arrival, departure, overflow, and emergency access",
            "What timing or terrain friction will create the first real access problem",
        ],
    ),
    StaffProductSection(
        heading="4. Force Protection And Emergency Actions",
        prompts=[
            "Immediate actions for incident response, escalation, shelter, medical handoff, or site lockdown",
            "What suspicious-activity, disturbance, or lost-accountability trigger requires rapid reporting",
            "What coordination is required with safety, medical, S-6, and the chain of command",
        ],
    ),
    StaffProductSection(
        heading="5. Legal Boundaries, Rehearsals, And AAR Capture",
        prompts=[
            "Authorities, limits, notifications, and documentation requirements",
            "What must be rehearsed before the annex is treated as executable",
            "What incident log, turnover, or after-action capture requirement survives the event",
        ],
    ),
]

VISITOR_CONTROL_CHECKLIST_SECTIONS = [
    StaffProductSection(
        heading="1. Visitor-Control Frame",
        prompts=[
            "Supported event, visitor category, and what this checklist is protecting",
            "What access, sponsorship, or escort assumption most threatens execution",
            "What command, legal, or installation boundary applies",
        ],
    ),
    StaffProductSection(
        heading="2. Entry And Verification Checks",
        prompts=[
            "Entry points, roster or badge checks, identification standard, and sponsor requirements",
            "Who verifies visitors, who escorts them, and who closes out access at departure",
            "What documentation or local process still needs confirmation before execution",
        ],
    ),
    StaffProductSection(
        heading="3. Movement, Escort, And Restricted-Area Checks",
        prompts=[
            "Where visitors may go, where they may not go, and how movement is controlled",
            "What media, VIP, partner, or contractor boundary needs to be explicit",
            "What force-protection or OPSEC concern matters most once visitors are inside",
        ],
    ),
    StaffProductSection(
        heading="4. Incident And Escalation Checks",
        prompts=[
            "What lost visitor, restricted-area issue, disturbance, or suspicious activity trigger is most likely",
            "Who reports, who responds, and who elevates the issue",
            "What immediate action happens if visitor control breaks down",
        ],
    ),
    StaffProductSection(
        heading="5. Departure, Accountability, And Follow-Through",
        prompts=[
            "How visitor departure, badge or roster closeout, and accountability are confirmed",
            "What unresolved issue survives into turnover or AAR",
            "What evidence shows visitor control actually worked",
        ],
    ),
]

TRAFFIC_PARKING_CONTROL_PLAN_SECTIONS = [
    StaffProductSection(
        heading="1. Traffic-Control Frame",
        prompts=[
            "Supported event, traffic objective, and what this plan must protect first",
            "What arrival, departure, or emergency-access assumption is carrying too much weight",
            "What command, safety, or installation control standard governs traffic flow",
        ],
    ),
    StaffProductSection(
        heading="2. Vehicle Flow And Parking Scheme",
        prompts=[
            "Arrival routes, staging, parking areas, overflow, and pedestrian separation",
            "Who controls ingress, egress, overflow, and emergency access",
            "What vehicle category or timing window creates the first choke point",
        ],
    ),
    StaffProductSection(
        heading="3. Control Measures And Support Dependencies",
        prompts=[
            "What cones, barriers, signs, marshals, comms, or escorts are required",
            "What S-4, provost, safety, medical, and installation coordination is needed",
            "What support shortfall makes the traffic plan non-credible",
        ],
    ),
    StaffProductSection(
        heading="4. Incident, Delay, And Emergency Actions",
        prompts=[
            "What breakdown, congestion, weather, or visitor surge changes the plan first",
            "What immediate action preserves emergency access and positive control",
            "What trigger requires command review, traffic halt, or re-sequencing",
        ],
    ),
    StaffProductSection(
        heading="5. Reset And After-Action Notes",
        prompts=[
            "How traffic control is closed out and restored after the event",
            "What unresolved parking or access issue survives into the next event",
            "What evidence or observation should be captured for the AAR",
        ],
    ),
]

RESOURCE_ESTIMATE_SECTIONS = [
    StaffProductSection(
        heading="1. Resource Frame And Supported Decision",
        prompts=[
            "Supported event, command problem, and what resource decision this estimate must support",
            "What resourcing posture is known now and what remains tentative",
            "What timeline or lead-time issue most threatens supportability",
        ],
    ),
    StaffProductSection(
        heading="2. Available Resources And Constraints",
        prompts=[
            "Known funds, authorities, support lines, or fiscal limits relevant to the decision",
            "What cannot be assumed, obligated, or moved without higher review",
            "What control, audit, or stewardship rule matters most here",
        ],
    ),
    StaffProductSection(
        heading="3. Prioritization And Tradeoffs",
        prompts=[
            "What must be protected first and what can be cut, deferred, or rephased",
            "What option gives the best effect for the resource burden",
            "What risk is created if the staff chooses the cheaper or faster path",
        ],
    ),
    StaffProductSection(
        heading="4. Execution, Controls, And Friction",
        prompts=[
            "Who owns execution, tracking, and review of the resource decision",
            "What coordination is required with operations, logistics, admin, or higher headquarters",
            "What friction point is most likely to surface after the decision is made",
        ],
    ),
    StaffProductSection(
        heading="5. Command Decision And Next Resourcing Window",
        prompts=[
            "What exact command decision or reprioritization is needed now",
            "What suspense, review point, or next budget window matters next",
            "What needs to be briefed upward or preserved for the next drill or cycle",
        ],
    ),
]

INSPECTION_READINESS_PLAN_SECTIONS = [
    StaffProductSection(
        heading="1. Inspection Frame And Scope",
        prompts=[
            "Supported inspection, assessment, or readiness concern and why it matters now",
            "What command concern is being addressed without compromising IG independence",
            "What is in scope and what must stay out of scope",
        ],
    ),
    StaffProductSection(
        heading="2. Standards, Functional Areas, And Evidence",
        prompts=[
            "Applicable functional areas, standards, or checklists",
            "What evidence, records, or observations should be reviewed",
            "What area is most likely to show recurring friction instead of a one-off mistake",
        ],
    ),
    StaffProductSection(
        heading="3. Gaps, Trends, And Boundary Notes",
        prompts=[
            "What trend, compliance gap, or readiness pattern should be elevated",
            "What belongs in command channels, what belongs in IG channels, and what belongs elsewhere",
            "What inquiry, complaint, or independence boundary must be protected explicitly",
        ],
    ),
    StaffProductSection(
        heading="4. Remediation Owners And Follow-Through",
        prompts=[
            "What corrective actions, owners, and suspenses would improve readiness",
            "What evidence should be preserved to show closure or trend movement",
            "What issue needs commander attention versus routine staff correction",
        ],
    ),
    StaffProductSection(
        heading="5. Command Decisions, Referrals, And Next Review",
        prompts=[
            "What should be briefed to the commander without compromising impartiality",
            "What must be referred to IG, SJA, safety, or other proper channels",
            "What next inspection, review, or follow-up point keeps this from becoming a forgotten note",
        ],
    ),
]

DECISION_BRIEF_SECTIONS = [
    StaffProductSection(
        heading="Slide 1. Commander Problem and Decision Required",
        prompts=[
            "State the problem in one sentence",
            "State the exact decision or approval being requested",
            "End the slide with the ask, not background",
        ],
    ),
    StaffProductSection(
        heading="Slide 2. Why This Matters Now",
        prompts=[
            "What changed or why the issue is on the board now",
            "Timeline pressure, readiness impact, or opportunity cost",
            "Keep it to the few facts that make the decision urgent",
        ],
    ),
    StaffProductSection(
        heading="Slide 3. Situation and Mission Linkage",
        prompts=[
            "Current status",
            "Higher guidance or commander's intent linkage",
            "What this supports in mission, training, or readiness terms",
        ],
    ),
    StaffProductSection(
        heading="Slide 4. Options or COAs",
        prompts=[
            "Present realistic options only",
            "For each option: what it gives, what it costs, what it risks",
            "Do not create fake options just to fill the slide",
        ],
    ),
    StaffProductSection(
        heading="Slide 5. Risks, Friction, and Assumptions",
        prompts=[
            "What breaks this plan first",
            "Critical assumptions that still need confirmation",
            "Support, comm, medical, admin, or timeline friction",
        ],
    ),
    StaffProductSection(
        heading="Slide 6. Recommendation and Immediate Actions",
        prompts=[
            "Recommended option and why",
            "Immediate actions if approved",
            "Named owners and next suspense point",
        ],
    ),
]

COMMAND_UPDATE_BRIEF_SECTIONS = [
    StaffProductSection(
        heading="Slide 1. Executive Snapshot",
        prompts=[
            "What the commander needs to know in under thirty seconds",
            "Overall posture: on track, slipping, or blocked",
            "Lead with meaning, not chronology",
        ],
    ),
    StaffProductSection(
        heading="Slide 2. Current Status by Main Effort",
        prompts=[
            "What is complete",
            "What is in progress",
            "What remains open",
        ],
    ),
    StaffProductSection(
        heading="Slide 3. What Changed Since the Last Brief",
        prompts=[
            "New facts only",
            "Changes to timeline, support, risk, or command guidance",
            "Do not re-brief stable information out of habit",
        ],
    ),
    StaffProductSection(
        heading="Slide 4. Risks and Friction",
        prompts=[
            "Top blockers",
            "What is trending worse",
            "What requires commander or XO attention",
        ],
    ),
    StaffProductSection(
        heading="Slide 5. Decisions, Support Requirements, and Suspenses",
        prompts=[
            "Decision required now, if any",
            "Support shortfalls or asks",
            "Named suspenses and next touchpoint",
        ],
    ),
]

AAR_SECTIONS = [
    StaffProductSection(
        heading="1. Event and Command Frame",
        prompts=[
            "Training event, date, audience, objectives",
            "Supported mission or commander's intent",
            "Why this event mattered to the unit, not just that it occurred",
            "State the event in a way the XO or S-3 can revisit later without re-learning the context",
        ],
    ),
    StaffProductSection(
        heading="2. Standards and Task Alignment",
        prompts=[
            "MET/METL or task standard assessed",
            "What right looked like",
            "What was actually observed",
            "Where the standard broke under friction",
            "Call out whether the event measured competence, exposed a gap, or only generated activity",
        ],
    ),
    StaffProductSection(
        heading="3. Sustains and What Held",
        prompts=[
            "What should continue",
            "Why it mattered",
            "What to preserve in the next iteration",
            "Identify deliberate good practice, not lucky improvisation",
            "Name which sustain should be protected even if the event gets compressed next drill",
        ],
    ),
    StaffProductSection(
        heading="4. Improves and Where It Broke",
        prompts=[
            "What should change",
            "What friction drove the shortfall",
            "What needs command attention",
            "State the first fix that changes the next event instead of writing a complaint",
            "Identify whether the failure was design, rehearsal, support, supervision, or execution",
        ],
    ),
    StaffProductSection(
        heading="5. Corrective Actions for the Next Event",
        prompts=[
            "Owner",
            "Suspense",
            "Follow-up requirement",
            "What must be verified before next execution",
            "Tie each item to the next rehearsal, drill, or execution date",
            "Make each corrective action specific enough that someone can actually close it",
        ],
    ),
]

IPB_SECTIONS = [
    StaffProductSection(
        heading="1. Define The Operational Environment",
        prompts=[
            "Area of operations, area of interest, and time horizon",
            "Supported mission or training problem",
            "Relevant physical, informational, and civil boundaries",
            "Known facts, assumptions, source caveats, and information gaps",
        ],
    ),
    StaffProductSection(
        heading="2. Describe Environmental Effects",
        prompts=[
            "Terrain, weather, infrastructure, and civil considerations that affect operations",
            "Observation, fields of fire, cover, concealment, obstacles, key terrain, and avenues of approach",
            "Effects on mobility, sustainment, communications, casualty response, and force protection",
            "What the environment enables, restricts, or makes uncertain for friendly and opposing actors",
        ],
    ),
    StaffProductSection(
        heading="3. Evaluate The Threat Or Relevant Actor",
        prompts=[
            "Composition, disposition, capabilities, limitations, and likely intent",
            "Doctrine, TTP, or behavior patterns only when sourced or explicitly assumed for training",
            "Critical vulnerabilities, dependencies, and decision requirements",
            "Confidence level and what collection or staff input would change the assessment",
        ],
    ),
    StaffProductSection(
        heading="4. Determine Threat COAs And Indicators",
        prompts=[
            "Most likely and most dangerous COA or actor behavior",
            "Named indicators and warnings that would confirm or disconfirm each COA",
            "Priority intelligence requirements, information requirements, and collection gaps",
            "Decision points, triggers, and branches the commander or S-3 may need to plan against",
        ],
    ),
    StaffProductSection(
        heading="5. Staff Use And Recommended Outputs",
        prompts=[
            "Commander implications, risk to mission, and recommended focus areas",
            (
                "Specific products or graphics needed: overlays, event template, COA sketch, collection matrix, "
                "or annex input"
            ),
            "Cross-staff friction for S-3, S-4, S-6, medical, force protection, and CA/G-9",
            "What must be verified before this IPB can support an order, brief, or exercise design",
        ],
    ),
]

CORRESPONDENCE_SECTIONS = [
    StaffProductSection(
        heading="Header / Routing",
        prompts=[
            "From, to, via, subject, references, enclosures",
            "Use the exact command/activity names and routing chain that should appear on the final product",
        ],
    ),
    StaffProductSection(
        heading="Purpose",
        prompts=[
            "Short opening paragraph that states the action or information",
            "Lead with the ask, decision, or notification instead of a long throat-clearing paragraph",
        ],
    ),
    StaffProductSection(
        heading="Discussion",
        prompts=[
            "Plain-language supporting paragraphs",
            "Use numbered paragraphs and subparagraphs that can survive routing edits without losing sequence",
        ],
    ),
    StaffProductSection(
        heading="Action / Closing",
        prompts=[
            "Required action, deadline, approval, or point of contact",
            "Name who owes what by when and what package component or coordination still must be attached",
        ],
    ),
]


class StaffProductBuilder:
    def build(
        self,
        request: StaffProductDraftRequest,
        templates: list[ProductTemplateRecord] | None = None,
    ) -> StaffProductDraftResponse:
        applied_templates = templates or []
        sections = _sections_for(request.product_type)
        title = f"{request.product_type.value.upper()} draft scaffold: {request.topic}"
        warnings = [
            *DEFAULT_WARNINGS,
            *detect_sensitive_input(" ".join([request.topic, *request.facts, *request.constraints])),
            "Staff products are advisory drafts and must be reviewed by the appropriate human chain.",
        ]
        if applied_templates:
            warnings.append(
                "Local templates are reusable examples only. Scrub stale names, "
                "routing, dates, and unit-specific details."
            )
        if request.product_type in {
            StaffProductType.opord,
            StaffProductType.warno,
            StaffProductType.frago,
            StaffProductType.conop,
            StaffProductType.ipb,
            StaffProductType.air_support_estimate,
            StaffProductType.air_ground_coordination_matrix,
            StaffProductType.aviation_supportability_matrix,
            StaffProductType.orm_worksheet,
            StaffProductType.no_go_criteria,
            StaffProductType.residual_risk_decision_note,
            StaffProductType.rehearsal_safety_brief,
            StaffProductType.admin_estimate,
            StaffProductType.admin_task_tracker,
            StaffProductType.routing_matrix,
            StaffProductType.pre_drill_admin_readiness_check,
            StaffProductType.troop_flow_checklist,
            StaffProductType.formation_transition_matrix,
            StaffProductType.leader_touchpoint_plan,
            StaffProductType.decision_support_matrix,
            StaffProductType.due_out_tracker,
            StaffProductType.collection_matrix,
            StaffProductType.sustainment_matrix,
            StaffProductType.movement_table,
            StaffProductType.medical_estimate,
            StaffProductType.casevac_quick_card,
            StaffProductType.religious_support_plan,
            StaffProductType.rmt_support_matrix,
            StaffProductType.morale_welfare_estimate,
            StaffProductType.road_to_war_brief,
            StaffProductType.public_affairs_plan,
            StaffProductType.security_annex,
            StaffProductType.visitor_control_checklist,
            StaffProductType.traffic_parking_control_plan,
        }:
            warnings.append("Use fictional/training-only data unless working in an approved environment.")
        if request.product_type == StaffProductType.ipb:
            warnings.append(
                "Treat IPB as an S-2/G-2 decision-support product; use public or training-safe sources unless "
                "working in an approved environment."
            )
        if request.product_type == StaffProductType.road_to_war_brief:
            warnings.append(
                "Treat road-to-war briefs as scenario-background aids only; verify regional context and actor "
                "assessments against current public sources before use."
            )
        if request.product_type == StaffProductType.public_affairs_plan:
            warnings.append(
                "Treat public affairs outputs as release-planning aids only; confirm OPSEC, legal, and command "
                "approval before any public use."
            )
        if request.product_type == StaffProductType.security_annex:
            warnings.append(
                "Treat security annexes as planning aids only; confirm local authorities, installation rules, and "
                "emergency procedures before execution."
            )
        if request.product_type in {
            StaffProductType.naval_letter,
            StaffProductType.memorandum,
            StaffProductType.endorsement,
        }:
            warnings.append("Verify final formatting against current correspondence manuals before release.")
        return StaffProductDraftResponse(
            product_type=request.product_type,
            title=title,
            sections=_enrich_sections(sections, request, applied_templates),
            applied_templates=[template.template_name for template in applied_templates],
            formatting_notes=_formatting_notes_for(request, applied_templates),
            review_checklist=_review_checklist(request, applied_templates) if request.include_review_checklist else [],
            citations=_citations_for(request.product_type),
            structured_citations=_structured_citations_for(request.product_type),
            warnings=sorted(set(warnings)),
            confidence=Confidence.low,
        )


def _sections_for(product_type: StaffProductType) -> list[StaffProductSection]:
    if product_type == StaffProductType.opord:
        return OPORD_SECTIONS
    if product_type == StaffProductType.warno:
        return WARNO_SECTIONS
    if product_type == StaffProductType.frago:
        return FRAGO_SECTIONS
    if product_type == StaffProductType.conop:
        return CONOP_SECTIONS
    if product_type == StaffProductType.sitrep:
        return SITREP_SECTIONS
    if product_type == StaffProductType.air_support_estimate:
        return AIR_SUPPORT_ESTIMATE_SECTIONS
    if product_type == StaffProductType.air_ground_coordination_matrix:
        return AIR_GROUND_COORDINATION_MATRIX_SECTIONS
    if product_type == StaffProductType.aviation_supportability_matrix:
        return AVIATION_SUPPORTABILITY_MATRIX_SECTIONS
    if product_type == StaffProductType.running_estimate:
        return RUNNING_ESTIMATE_SECTIONS
    if product_type == StaffProductType.synchronization_matrix:
        return SYNCHRONIZATION_MATRIX_SECTIONS
    if product_type == StaffProductType.orm_worksheet:
        return ORM_WORKSHEET_SECTIONS
    if product_type == StaffProductType.no_go_criteria:
        return NO_GO_CRITERIA_SECTIONS
    if product_type == StaffProductType.residual_risk_decision_note:
        return RESIDUAL_RISK_DECISION_NOTE_SECTIONS
    if product_type == StaffProductType.rehearsal_safety_brief:
        return REHEARSAL_SAFETY_BRIEF_SECTIONS
    if product_type == StaffProductType.admin_estimate:
        return ADMIN_ESTIMATE_SECTIONS
    if product_type == StaffProductType.admin_task_tracker:
        return ADMIN_TASK_TRACKER_SECTIONS
    if product_type == StaffProductType.routing_matrix:
        return ROUTING_MATRIX_SECTIONS
    if product_type == StaffProductType.pre_drill_admin_readiness_check:
        return PRE_DRILL_ADMIN_READINESS_CHECK_SECTIONS
    if product_type == StaffProductType.troop_flow_checklist:
        return TROOP_FLOW_CHECKLIST_SECTIONS
    if product_type == StaffProductType.formation_transition_matrix:
        return FORMATION_TRANSITION_MATRIX_SECTIONS
    if product_type == StaffProductType.leader_touchpoint_plan:
        return LEADER_TOUCHPOINT_PLAN_SECTIONS
    if product_type == StaffProductType.decision_support_matrix:
        return DECISION_SUPPORT_MATRIX_SECTIONS
    if product_type == StaffProductType.due_out_tracker:
        return DUE_OUT_TRACKER_SECTIONS
    if product_type == StaffProductType.collection_matrix:
        return COLLECTION_MATRIX_SECTIONS
    if product_type == StaffProductType.sustainment_matrix:
        return SUSTAINMENT_MATRIX_SECTIONS
    if product_type == StaffProductType.movement_table:
        return MOVEMENT_TABLE_SECTIONS
    if product_type == StaffProductType.medical_estimate:
        return MEDICAL_ESTIMATE_SECTIONS
    if product_type == StaffProductType.casevac_quick_card:
        return CASEVAC_QUICK_CARD_SECTIONS
    if product_type == StaffProductType.religious_support_plan:
        return RELIGIOUS_SUPPORT_PLAN_SECTIONS
    if product_type == StaffProductType.rmt_support_matrix:
        return RMT_SUPPORT_MATRIX_SECTIONS
    if product_type == StaffProductType.morale_welfare_estimate:
        return MORALE_WELFARE_ESTIMATE_SECTIONS
    if product_type == StaffProductType.road_to_war_brief:
        return ROAD_TO_WAR_BRIEF_SECTIONS
    if product_type == StaffProductType.public_affairs_plan:
        return PUBLIC_AFFAIRS_PLAN_SECTIONS
    if product_type == StaffProductType.security_annex:
        return SECURITY_ANNEX_SECTIONS
    if product_type == StaffProductType.visitor_control_checklist:
        return VISITOR_CONTROL_CHECKLIST_SECTIONS
    if product_type == StaffProductType.traffic_parking_control_plan:
        return TRAFFIC_PARKING_CONTROL_PLAN_SECTIONS
    if product_type == StaffProductType.resource_estimate:
        return RESOURCE_ESTIMATE_SECTIONS
    if product_type == StaffProductType.inspection_readiness_plan:
        return INSPECTION_READINESS_PLAN_SECTIONS
    if product_type == StaffProductType.decision_brief:
        return DECISION_BRIEF_SECTIONS
    if product_type == StaffProductType.command_update_brief:
        return COMMAND_UPDATE_BRIEF_SECTIONS
    if product_type == StaffProductType.aar:
        return AAR_SECTIONS
    if product_type == StaffProductType.ipb:
        return IPB_SECTIONS
    return CORRESPONDENCE_SECTIONS


def _enrich_sections(
    sections: list[StaffProductSection],
    request: StaffProductDraftRequest,
    templates: list[ProductTemplateRecord],
) -> list[StaffProductSection]:
    sensitivity_warnings = detect_sensitive_input(" ".join([request.topic, *request.facts, *request.constraints]))
    context_prompts = [
        f"Topic: {request.topic}",
        *([f"Audience: {request.audience}"] if request.audience else []),
        *([f"Echelon: {request.echelon}"] if request.echelon else []),
        *([f"Preferred format: {request.preferred_format}"] if request.preferred_format else []),
    ]
    template_prompts: list[str] = []
    for template in templates:
        template_prompts.append(
            f"Local template reference: {template.template_name} "
            f"({template.template_type.value}). Use as structure only."
        )
        if template.audience_hint:
            template_prompts.append(f"Template audience hint: {template.audience_hint}")
        if template.preferred_format:
            template_prompts.append(f"Template preferred format: {template.preferred_format}")
        template_prompts.extend(
            f"Template heading to consider: {heading}" for heading in template.reusable_headings[:6]
        )
        template_prompts.extend(f"Template reuse note: {note}" for note in template.reusable_guidance[:4])
    if sensitivity_warnings:
        fact_prompts = ["Sensitive details were withheld. Use only generic training-safe placeholders."]
        constraint_prompts = ["Constraint: verify all operational specifics in an approved environment."]
    else:
        fact_prompts = [f"User fact to verify: {fact}" for fact in request.facts]
        constraint_prompts = [f"Constraint: {constraint}" for constraint in request.constraints]
    return [
        StaffProductSection(
            heading=section.heading,
            prompts=[*context_prompts, *template_prompts, *section.prompts, *fact_prompts, *constraint_prompts],
        )
        for section in sections
    ]


def _review_checklist(request: StaffProductDraftRequest, templates: list[ProductTemplateRecord]) -> list[str]:
    checklist = [
        "Confirm the product is UNCLASSIFIED and appropriate for this prototype.",
        "Verify every factual claim against official/public sources or user-confirmed local context.",
        "Assign human owner, reviewer, and suspense.",
        "Remove unnecessary PII and sensitive unit-specific details.",
        "Confirm final product with the appropriate chain before release.",
    ]
    if templates:
        checklist.append(
            "Check every borrowed template element for stale names, dates, "
            "routing, attachments, and unit-specific assumptions."
        )
    if request.product_type in {
        StaffProductType.opord,
        StaffProductType.warno,
        StaffProductType.frago,
        StaffProductType.conop,
        StaffProductType.ipb,
        StaffProductType.air_support_estimate,
        StaffProductType.air_ground_coordination_matrix,
        StaffProductType.aviation_supportability_matrix,
        StaffProductType.orm_worksheet,
        StaffProductType.no_go_criteria,
        StaffProductType.residual_risk_decision_note,
        StaffProductType.rehearsal_safety_brief,
        StaffProductType.admin_estimate,
        StaffProductType.admin_task_tracker,
        StaffProductType.routing_matrix,
        StaffProductType.pre_drill_admin_readiness_check,
        StaffProductType.troop_flow_checklist,
        StaffProductType.formation_transition_matrix,
        StaffProductType.leader_touchpoint_plan,
        StaffProductType.decision_support_matrix,
        StaffProductType.due_out_tracker,
        StaffProductType.collection_matrix,
        StaffProductType.sustainment_matrix,
        StaffProductType.movement_table,
        StaffProductType.medical_estimate,
        StaffProductType.casevac_quick_card,
        StaffProductType.religious_support_plan,
        StaffProductType.rmt_support_matrix,
        StaffProductType.morale_welfare_estimate,
        StaffProductType.road_to_war_brief,
        StaffProductType.public_affairs_plan,
        StaffProductType.security_annex,
        StaffProductType.visitor_control_checklist,
        StaffProductType.traffic_parking_control_plan,
    }:
        checklist.append("Confirm the scenario is fictional/training-only or handled in an approved environment.")
    if request.product_type == StaffProductType.running_estimate:
        checklist.extend(
            [
                "State what changed since the last update instead of rebuilding the whole estimate from zero.",
                "Tie each risk, support ask, and due-out to an owner or adjacent section.",
                "Name the command decision or next refresh point before sending the estimate up the chain.",
            ]
        )
    if request.product_type == StaffProductType.air_support_estimate:
        checklist.extend(
            [
                "State the supported aviation effect before listing coordination detail.",
                "Make qualified aviation review, no-go conditions, and fallback value explicit.",
                "Keep airspace, comm, and deconfliction assumptions visible enough to challenge.",
            ]
        )
    if request.product_type == StaffProductType.air_ground_coordination_matrix:
        checklist.extend(
            [
                "Give each coordination row an owner, control method, report, and branch condition.",
                "Make comm, deconfliction, and safety triggers explicit for each phase.",
                "Keep the matrix tied to a real supported event instead of generic aviation admiration.",
            ]
        )
    if request.product_type == StaffProductType.aviation_supportability_matrix:
        checklist.extend(
            [
                "Make sortie, platform, maintenance, and support assumptions specific enough to test honestly.",
                "Identify the shortfall that cancels or shrinks aviation support first.",
                "Tie the matrix to a real command tradeoff or supportability decision.",
            ]
        )
    if request.product_type == StaffProductType.synchronization_matrix:
        checklist.extend(
            [
                "Give every row an owner, suspense, and command touchpoint.",
                "Make the friction point and cut/defer rule explicit instead of assuming the staff remembers it.",
                "Keep the matrix tied to actual decision points, not just task accumulation.",
            ]
        )
    if request.product_type == StaffProductType.orm_worksheet:
        checklist.extend(
            [
                (
                    "Tie hazards, controls, owners, and residual risk together instead of treating "
                    "ORM like a signature sheet."
                ),
                "Show what control is actually rehearsed and executable under friction.",
                "Make the commander risk-acceptance point explicit.",
            ]
        )
    if request.product_type == StaffProductType.no_go_criteria:
        checklist.extend(
            [
                "State stop, pause, modify, and resume authorities clearly.",
                "Separate universal stop conditions from event-specific no-go thresholds.",
                "Make restart conditions explicit so the staff does not improvise them under pressure.",
            ]
        )
    if request.product_type == StaffProductType.residual_risk_decision_note:
        checklist.extend(
            [
                "State the residual-risk decision in one line before adding context.",
                "Show what remains risky after controls and who must accept it.",
                "Tie the note to a real commander decision point, not generic ORM language.",
            ]
        )
    if request.product_type == StaffProductType.rehearsal_safety_brief:
        checklist.extend(
            [
                "Make emergency actions, stop-training calls, and first reports briefable in seconds.",
                "Verify what must be rehearsed physically before the event starts.",
                "Tie the brief to the actual no-go criteria and residual-risk decisions in force.",
            ]
        )
    if request.product_type == StaffProductType.admin_estimate:
        checklist.extend(
            [
                "Show which admin fact changes execution and which remains continuity background.",
                "Keep roster, orders, travel-admin, and records lanes distinct enough to own separately.",
                "Tie the estimate to a real suspense, command touchpoint, or decision instead of admin narration.",
            ]
        )
    if request.product_type == StaffProductType.admin_task_tracker:
        checklist.extend(
            [
                "Give every admin line one owner, one suspense, one status, and one command touchpoint.",
                "Separate late items, blocked items, and complete items clearly.",
                "Preserve turnover notes so the next drill cycle can continue the tracker without guessing.",
            ]
        )
    if request.product_type == StaffProductType.routing_matrix:
        checklist.extend(
            [
                "Make routing chain, reviewer, signature authority, and suspense explicit for each package.",
                "Show what document, attachment, or outside input still blocks movement.",
                "Keep routing closeout evidence visible instead of assuming a package is done because it moved once.",
            ]
        )
    if request.product_type == StaffProductType.pre_drill_admin_readiness_check:
        checklist.extend(
            [
                "Use the check to catch no-surprise admin failures before drill, not to admire a checklist.",
                "Elevate any roster, orders, or travel-admin gap that will still matter once Marines disperse.",
                "Tie every failed check to an owner and immediate follow-up action.",
            ]
        )
    if request.product_type == StaffProductType.troop_flow_checklist:
        checklist.extend(
            [
                "Make troop flow from first formation through final release readable in seconds.",
                "Keep accountability ownership explicit at every phase instead of relying on habit.",
                "Show the first point where Marines bunch up, wait too long, or become easy to lose track of.",
            ]
        )
    if request.product_type == StaffProductType.formation_transition_matrix:
        checklist.extend(
            [
                "Give each formation and transition an owner, trigger, standard, and required report.",
                "Make handoff responsibility explicit so no transition sits in dead space.",
                "Keep fallback actions visible for compressed timelines, missing leaders, or support slippage.",
            ]
        )
    if request.product_type == StaffProductType.leader_touchpoint_plan:
        checklist.extend(
            [
                "Tie each touchpoint to a real leader action, not a generic reminder to check in.",
                "Keep welfare, standards, and capacity checks visible enough for reserve reality.",
                "Show what issue gets corrected informally, what gets elevated, and who owns follow-through.",
            ]
        )
    if request.product_type == StaffProductType.decision_support_matrix:
        checklist.extend(
            [
                "State the actual decision in one line before adding context.",
                "Show what changes if the commander approves, defers, cuts, or redirects the issue.",
                "Keep triggers, tradeoffs, and immediate follow-on actions explicit.",
            ]
        )
    if request.product_type == StaffProductType.due_out_tracker:
        checklist.extend(
            [
                "Give every due-out one owner, one suspense, and one command touchpoint.",
                "Separate late items, waiting-on-decision items, and complete items clearly.",
                "Preserve turnover notes so the next watch or drill cycle can pick up without guesswork.",
            ]
        )
    if request.product_type == StaffProductType.collection_matrix:
        checklist.extend(
            [
                "Separate PIR, IR, indicators, collection tasks, and source caveats clearly.",
                "Assign an owner and refresh point for each collection task.",
                (
                    "Confirm the matrix supports a real commander or S-3 decision "
                    "instead of generic intelligence curiosity."
                ),
            ]
        )
    if request.product_type == StaffProductType.sustainment_matrix:
        checklist.extend(
            [
                "Identify which support shortfall changes scope and which one cancels the event.",
                "Give movement and recovery assumptions explicit owners and suspense points.",
                "Keep the matrix honest about reset burden and support debt after execution.",
            ]
        )
    if request.product_type == StaffProductType.movement_table:
        checklist.extend(
            [
                "Give every move an element, origin, destination, time, transport method, and owner.",
                "Make accountability confirmation and missed-report actions explicit for each move.",
                "Keep fallback movement logic visible enough to use when the schedule slips.",
            ]
        )
    if request.product_type == StaffProductType.medical_estimate:
        checklist.extend(
            [
                "Confirm qualified medical review before treating the estimate as executable.",
                "Name stop-training, CASEVAC, and higher-care assumptions explicitly.",
                "Tie casualty scenarios, rehearsal checks, and command decisions to the actual event.",
            ]
        )
    if request.product_type == StaffProductType.casevac_quick_card:
        checklist.extend(
            [
                "Keep the quick card training-safe, non-clinical, and tied to qualified medical review.",
                "Make first call, movement path, accountability owner, and "
                "stop-training trigger obvious in seconds.",
                "Do not let the card replace local emergency procedures, "
                "credentialed direction, or real TCCC instruction.",
            ]
        )
    if request.product_type == StaffProductType.religious_support_plan:
        checklist.extend(
            [
                "Make support access, referral boundaries, and confidentiality considerations explicit.",
                "Keep morale and family-touching support grounded in real event demand, not generic care language.",
                "Show what requires chaplain, RP, medical, or command coordination before execution.",
            ]
        )
    if request.product_type == StaffProductType.rmt_support_matrix:
        checklist.extend(
            [
                "Give each support row an owner, time, location, and support dependency.",
                "Keep transport, access, and continuity assumptions visible enough to test.",
                "Show what casualty, memorial, or morale trigger changes the support load first.",
            ]
        )
    if request.product_type == StaffProductType.morale_welfare_estimate:
        checklist.extend(
            [
                "Distinguish observable morale indicators from private or privileged detail.",
                "Keep referral boundaries and leader actions more visible than narration.",
                "Tie the estimate to a real intervention, trend watch, or command consideration.",
            ]
        )
    if request.product_type == StaffProductType.road_to_war_brief:
        checklist.extend(
            [
                "Keep the brief focused on scenario understanding, not a full IPB or current-intelligence product.",
                "Verify regional background, actor motives, and trigger events against public sources before briefing.",
                "End with what the unit should care about in the first 24-72 hours, not a history lecture.",
            ]
        )
    if request.product_type == StaffProductType.public_affairs_plan:
        checklist.extend(
            [
                "Confirm release authority, OPSEC review, and legal review boundaries before public use.",
                "Make themes, response lines, and visitor/media choreography specific to the event.",
                "State who may speak, who approves content, and what changes require command reapproval.",
            ]
        )
    if request.product_type == StaffProductType.security_annex:
        checklist.extend(
            [
                "Confirm installation or local physical-security rules before treating the annex as executable.",
                "Make access control, traffic flow, and incident escalation owners explicit.",
                "Tie emergency actions, rehearsals, and incident logging to actual site conditions and authorities.",
            ]
        )
    if request.product_type == StaffProductType.visitor_control_checklist:
        checklist.extend(
            [
                "Make sponsor, escort, identification, and restricted-area rules obvious at a glance.",
                "Keep incident and lost-visitor actions explicit enough to use under stress.",
                "Validate local installation access processes before treating the checklist as executable.",
            ]
        )
    if request.product_type == StaffProductType.traffic_parking_control_plan:
        checklist.extend(
            [
                "Show ingress, egress, overflow, and emergency-access logic clearly.",
                "Make marshaling, barrier, and control-measure requirements explicit.",
                "Keep the first choke point and the fallback action visible enough to act on quickly.",
            ]
        )
    if request.product_type == StaffProductType.resource_estimate:
        checklist.extend(
            [
                (
                    "Verify fiscal controls, lead times, and local comptroller review before treating "
                    "the estimate as executable."
                ),
                "State what gets funded, cut, deferred, or rephased in plain command language.",
                "Make the command decision and next resource-review window explicit.",
            ]
        )
    if request.product_type == StaffProductType.inspection_readiness_plan:
        checklist.extend(
            [
                "Protect IG independence and do not use the plan to shortcut complaint or investigation channels.",
                "Tie each readiness gap to evidence, owner, suspense, and proper referral path.",
                "State what belongs to command correction, what belongs to IG, and what belongs elsewhere.",
            ]
        )
    if request.product_type == StaffProductType.ipb:
        checklist.extend(
            [
                "Confirm S-2/G-2 review before using the IPB to drive commander decisions or exercise injects.",
                "Label assumptions, confidence, and source gaps instead of presenting estimates as settled facts.",
                "Separate public-source environmental context from threat or actor assessments.",
            ]
        )
    if request.product_type in {StaffProductType.decision_brief, StaffProductType.command_update_brief}:
        checklist.extend(
            [
                "Cut any slide that does not change understanding, decision quality, or execution.",
                "Limit each slide to one main point and no more than a few support bullets.",
                "Move narrative paragraphs, source detail, and backup data to speaker notes or an annex.",
                "Make the decision, ask, or suspense explicit before the brief leaves the staff level.",
            ]
        )
    if request.product_type == StaffProductType.aar:
        checklist.extend(
            [
                (
                    "Tie every improve item to a named owner, suspense, and the next drill, rehearsal, "
                    "or execution window."
                ),
                (
                    "Separate standard failure from support, rehearsal, supervision, or design failure "
                    "before finalizing the AAR."
                ),
                (
                    "Strip out complaint language and preserve only observations, friction, decisions, "
                    "and corrective action."
                ),
            ]
        )
    return checklist


def _formatting_notes_for(
    request: StaffProductDraftRequest,
    templates: list[ProductTemplateRecord],
) -> list[str]:
    shared_notes = (
        [
            (
                "A local example template was applied. Preserve useful structure and tone, "
                "but rewrite stale specifics before release."
            )
        ]
        if templates
        else []
    )
    if request.product_type == StaffProductType.naval_letter:
        return [
            *shared_notes,
            "Use From/To/Via/Subj/Ref/Encl in the header and keep the subject line short and literal.",
            "Write numbered paragraphs that can survive routing edits and endorsements.",
            "Keep the opening paragraph action-oriented: what is being requested, directed, or provided for decision.",
            "Reserve enclosures, references, and routing notes for items that will actually exist in the package.",
            "End with a clear action, suspense, and point of contact instead of a vague courtesy close.",
        ]
    if request.product_type == StaffProductType.memorandum:
        return [
            *shared_notes,
            "Use memorandum format when the product is internal and does not need full naval-letter routing.",
            "Keep the subject plain and administrative, then move quickly to the purpose and required action.",
            "Use short numbered paragraphs and avoid burying the suspense or decision in the discussion section.",
        ]
    if request.product_type == StaffProductType.endorsement:
        return [
            *shared_notes,
            "Anchor the endorsement to the forwarded package and state whether it recommends, concurs, or elevates "
            "an issue.",
            "Keep the endorsement short; do not rewrite the base package unless the deficiency is the point.",
            "Identify unresolved risks, missing enclosures, or command concerns plainly so the next reviewer can act.",
        ]
    if request.product_type == StaffProductType.frago:
        return [
            *shared_notes,
            "A FRAGO should only state what changed from the base order, not restate the whole order out of habit.",
            "Task subordinate elements in plain Marine-staff language with task, purpose, and no-later-than "
            "discipline where possible.",
            "Make sure coordinating instructions separate what is fixed across the force from what subordinate units "
            "may refine locally.",
        ]
    if request.product_type == StaffProductType.conop:
        return [
            *shared_notes,
            "A CONOP should explain how the unit intends to execute, not pretend to be a full OPORD.",
            "State supported/supporting relationships clearly so subordinate units can draft their own local concepts.",
            "Tie assessment language to task standards, decision points, and AAR capture rather than generic "
            "enthusiasm.",
        ]
    if request.product_type == StaffProductType.air_support_estimate:
        return [
            *shared_notes,
            "An air support estimate should lead with supported effect, not aviation jargon.",
            "Keep control method, deconfliction, no-go conditions, and fallback value visible at a glance.",
            "Treat the estimate as planning support only until qualified aviation review occurs.",
        ]
    if request.product_type == StaffProductType.air_ground_coordination_matrix:
        return [
            *shared_notes,
            "An air-ground coordination matrix should make phase, owner, control method, and report easy to scan.",
            "Do not bury deconfliction and comm triggers inside prose.",
            "Write it so S-3, AirO, S-6, and safety can use the same picture under time pressure.",
        ]
    if request.product_type == StaffProductType.aviation_supportability_matrix:
        return [
            *shared_notes,
            "An aviation supportability matrix should show what aviation support is "
            "actually plausible, not merely desired.",
            "Keep readiness, maintenance, support windows, and branch logic more visible than enthusiasm.",
            "Tie the matrix to a real command tradeoff or supportability decision.",
        ]
    if request.product_type == StaffProductType.running_estimate:
        return [
            *shared_notes,
            "A running estimate should show what changed, what matters now, and what decision or due-out follows.",
            "Keep the estimate lane-specific and decision-support focused; do not let it become a diary entry.",
            "Use short bullets with explicit assumptions, risks, adjacent asks, and next-24-72-hour actions.",
        ]
    if request.product_type == StaffProductType.synchronization_matrix:
        return [
            *shared_notes,
            "A synchronization matrix should make timing, ownership, and review points visible at a glance.",
            "Do not let it become a long parking lot of tasks with no friction logic or decision support.",
            "Show what gets cut, elevated, or re-sequenced when the timeline starts to slip.",
        ]
    if request.product_type == StaffProductType.orm_worksheet:
        return [
            *shared_notes,
            "An ORM worksheet should help the commander judge risk, not just satisfy paperwork.",
            "Make hazards, controls, owners, and residual risk readable at a glance.",
            "Keep the actual risk-acceptance decision visible instead of burying it in admin language.",
        ]
    if request.product_type == StaffProductType.no_go_criteria:
        return [
            *shared_notes,
            "No-go criteria should be crisp enough to call under stress without debate.",
            "Separate pause, modify, and full-stop thresholds clearly.",
            "Write restart conditions so the staff does not improvise them after a halt.",
        ]
    if request.product_type == StaffProductType.residual_risk_decision_note:
        return [
            *shared_notes,
            "A residual-risk decision note should be short, explicit, and tied to command authority.",
            "Lead with what remains risky after controls, then show options and recommendation.",
            "Do not let the note blur into generic ORM narration or after-action explanation.",
        ]
    if request.product_type == StaffProductType.rehearsal_safety_brief:
        return [
            *shared_notes,
            "A rehearsal safety brief should sound like something leaders can actually brief before execution.",
            "Keep emergency actions, stop-training calls, and verification checks more visible than background detail.",
            "Tie the brief directly to the hazards and no-go conditions most likely to matter early.",
        ]
    if request.product_type == StaffProductType.admin_estimate:
        return [
            *shared_notes,
            "An admin estimate should show what matters now in rosters, orders, travel-admin, and continuity.",
            "Keep it tied to execution impact, not generic admin housekeeping.",
            "Use short bullets with explicit risks, suspenses, and adjacent staff dependencies.",
        ]
    if request.product_type == StaffProductType.admin_task_tracker:
        return [
            *shared_notes,
            "An admin task tracker should read like a real S-1 battle board, not a miscellaneous to-do list.",
            "Status, owner, suspense, and next command look should be easier to see than explanation.",
            "Keep DTS, GTCC, orders, rosters, and readiness tasks distinct enough to hand off cleanly.",
        ]
    if request.product_type == StaffProductType.routing_matrix:
        return [
            *shared_notes,
            "A routing matrix should make chain, reviewer, signature authority, and suspense obvious at a glance.",
            "Do not mix package status, admin commentary, and unrelated action items in the same line.",
            "Show the first routing bottleneck before it surprises the staff close to drill.",
        ]
    if request.product_type == StaffProductType.pre_drill_admin_readiness_check:
        return [
            *shared_notes,
            "A pre-drill admin readiness check should surface likely failures before Marines arrive or disperse.",
            (
                "Keep it practical: roster truth, routing truth, and travel-admin truth matter "
                "more than perfect formatting."
            ),
            "Write it so an S-1 chief or XO can scan it quickly and know what still needs intervention.",
        ]
    if request.product_type == StaffProductType.troop_flow_checklist:
        return [
            *shared_notes,
            "A troop-flow checklist should make Marine movement, waiting points, and accountability easy to scan fast.",
            "Keep formation, movement, release, and welfare checks more visible than commentary.",
            "Write it so a 1stSgt, SgtMaj, or platoon sergeant can use it without reconstructing the event.",
        ]
    if request.product_type == StaffProductType.formation_transition_matrix:
        return [
            *shared_notes,
            "A formation/transition matrix should show trigger, owner, standard, and report for each phase change.",
            "Do not bury the handoff logic inside prose; the whole point is to make transition control visible.",
            "Keep fallback actions short enough to call out when the sequence gets compressed.",
        ]
    if request.product_type == StaffProductType.leader_touchpoint_plan:
        return [
            *shared_notes,
            "A leader touchpoint plan should show when leaders intervene, what they verify, and what gets elevated.",
            "Keep welfare, discipline, and reserve-capacity checks explicit "
            "instead of assuming leaders will improvise them.",
            "Write it so the SEL and chain can preserve the same touchpoints across repeated events.",
        ]
    if request.product_type == StaffProductType.decision_support_matrix:
        return [
            *shared_notes,
            "A decision-support matrix should make the decision, triggers, and tradeoffs obvious in seconds.",
            "Keep background short and preserve most of the space for options, recommendations, and consequences.",
            "Write it so the XO, chief, or battle captain can brief it quickly without reconstructing the logic aloud.",
        ]
    if request.product_type == StaffProductType.due_out_tracker:
        return [
            *shared_notes,
            "A due-out tracker should read like a command-cell watchboard, not an unlabeled task dump.",
            "Status, owner, suspense, and next command look should be easier to see than narrative explanation.",
            "Keep turnover and continuity visible so the staff does not restart the same tracking fight each cycle.",
        ]
    if request.product_type == StaffProductType.collection_matrix:
        return [
            *shared_notes,
            "A collection matrix should tie PIR, IR, indicators, owners, and refresh points to a real decision.",
            "Label source caveats and confidence so the staff does not over-read weak information.",
            "Keep collection tasks narrow enough that someone can actually close them inside the planning window.",
        ]
    if request.product_type == StaffProductType.sustainment_matrix:
        return [
            *shared_notes,
            "A sustainment matrix should show movement, support flow, dependencies, and recovery, not just supplies.",
            "Make the longest lead-time support ask and event-canceling shortfall easy to spot.",
            "Do not hide reset burden or post-event sustainment debt.",
        ]
    if request.product_type == StaffProductType.movement_table:
        return [
            *shared_notes,
            "A movement table should make sequence, timing, transport method, and accountability readable at a glance.",
            "Keep release, arrival confirmation, and fallback logic more visible than narrative explanation.",
            "Write it so S-4, XO, and leaders can use it quickly when the timeline starts to compress.",
        ]
    if request.product_type == StaffProductType.medical_estimate:
        return [
            *shared_notes,
            (
                "A medical estimate should support command judgment on risk, coverage, evacuation, "
                "and stop-training authority."
            ),
            "Keep casualty scenarios, CASEVAC logic, rehearsal checks, and decision points explicit.",
            "Do not confuse a template with qualified medical direction or local emergency procedures.",
        ]
    if request.product_type == StaffProductType.casevac_quick_card:
        return [
            *shared_notes,
            "A CASEVAC quick card should be briefable in seconds under stress.",
            "Keep first call, movement path, accountability, and stop-training "
            "triggers more visible than background detail.",
            "Treat it as a training-safe aid, not as clinical instruction or a substitute for local emergency SOP.",
        ]
    if request.product_type == StaffProductType.religious_support_plan:
        return [
            *shared_notes,
            "A religious support plan should make support access, referral "
            "boundaries, and event touchpoints easy to brief.",
            "Keep confidentiality and support-channel boundaries explicit instead of assumed.",
            "Write it so chaplain, RP, and command can see where demand may exceed informal support.",
        ]
    if request.product_type == StaffProductType.rmt_support_matrix:
        return [
            *shared_notes,
            "An RMT support matrix should make schedule, movement, access, and "
            "support dependencies visible at a glance.",
            "Keep continuity and casualty-or-memorial branch conditions explicit.",
            "Write it so RP and chaplain support does not rely on verbal memory.",
        ]
    if request.product_type == StaffProductType.morale_welfare_estimate:
        return [
            *shared_notes,
            "A morale and welfare estimate should surface command-relevant stress "
            "and support signals without oversharing private detail.",
            "Keep referral boundaries, leader actions, and follow-through more "
            "visible than diagnosis-like language.",
            "Treat it as leader awareness and support planning, not counseling.",
        ]
    if request.product_type == StaffProductType.road_to_war_brief:
        return [
            *shared_notes,
            "A road-to-war brief should level-set the scenario fast enough "
            "for a unit to enter the problem with context.",
            "Keep it broader than an IPB, but sharper than generic regional trivia or a college lecture.",
            "End with what matters to the unit, the MAGTF frame, and the first assumptions that need testing.",
        ]
    if request.product_type == StaffProductType.public_affairs_plan:
        return [
            *shared_notes,
            "A public affairs plan should make release authority, audiences, and response lines easy to use fast.",
            "Keep OPSEC, imagery controls, visitor/media choreography, and approval triggers explicit.",
            "Do not let themes and messages drift away from the commander's actual event and risk posture.",
        ]
    if request.product_type == StaffProductType.security_annex:
        return [
            *shared_notes,
            "A security annex should make access, movement, escalation, and emergency actions readable at a glance.",
            "Keep local authorities, installation rules, and legal boundaries visible instead of assuming them.",
            (
                "Show the first likely choke point in traffic, visitor flow, or incident response "
                "before it surprises the staff."
            ),
        ]
    if request.product_type == StaffProductType.visitor_control_checklist:
        return [
            *shared_notes,
            "A visitor-control checklist should keep sponsor, escort, "
            "verification, and boundary rules obvious at a glance.",
            "Make incident and lost-visitor actions more visible than commentary.",
            "Write it so provost, site control, and event leads can use the same checklist under friction.",
        ]
    if request.product_type == StaffProductType.traffic_parking_control_plan:
        return [
            *shared_notes,
            "A traffic and parking control plan should show vehicle flow, parking logic, and emergency access clearly.",
            "Keep the first choke point and fallback action more visible than background explanation.",
            "Write it so marshals, provost, safety, and event leads can act on it fast.",
        ]
    if request.product_type == StaffProductType.resource_estimate:
        return [
            *shared_notes,
            "A resource estimate should frame a decision, not just list financial constraints in the abstract.",
            "Show what can be funded, what must wait, and what tradeoff the commander is actually being asked to make.",
            "Keep controls, stewardship, and next review windows visible so the estimate stays executable.",
        ]
    if request.product_type == StaffProductType.inspection_readiness_plan:
        return [
            *shared_notes,
            "An inspection readiness plan should surface standards, evidence, trends, and referral boundaries cleanly.",
            "Do not confuse inspection preparation with complaint handling, legal review, or command-directed inquiry.",
            (
                "Make independence boundaries and next follow-through points visible before the issue turns "
                "political or vague."
            ),
        ]
    if request.product_type == StaffProductType.decision_brief:
        return [
            *shared_notes,
            "Treat each section like a slide, not a memo paragraph.",
            "Put one decision problem on the screen at a time; background belongs only where it changes the decision.",
            "Use short bullets, not prose blocks. If it cannot be briefed aloud in a few seconds, it is too dense.",
            "End with a recommendation, immediate actions, and the exact decision or approval required.",
            "Keep backup data off the main slides and move it to annex slides or speaker notes.",
        ]
    if request.product_type == StaffProductType.command_update_brief:
        return [
            *shared_notes,
            "This brief should update command understanding, not restate the whole plan from scratch.",
            "Lead with posture, changes, and blockers before detail.",
            "Use one idea per slide and cut decorative language, slogans, and filler transitions.",
            (
                "If a slide has no decision, support ask, or readiness consequence, "
                "it probably does not belong in the brief."
            ),
        ]
    if request.product_type == StaffProductType.aar:
        return [
            *shared_notes,
            "Write the AAR like a product the XO or S-3 would keep: standards, observations, friction, and "
            "corrective actions worth revisiting later.",
            "Separate deliberate good practice from lucky improvisation so the unit knows what to preserve.",
            "Every improve item should point to the next rehearsal, drill, or execution window.",
            "Lead with what mattered, what held, where the standard broke, and what changes before the next event.",
            "Avoid diary language. Capture judgment, friction, and decisions that shape the next cycle.",
        ]
    if request.product_type == StaffProductType.ipb:
        return [
            *shared_notes,
            "IPB should support decisions and planning, not become a generic terrain, weather, or country brief.",
            (
                "Keep each estimate tied to commander decisions, S-3 planning, collection needs, "
                "or exercise inject design."
            ),
            (
                "Use most-likely and most-dangerous COAs only when they are sourced, explicitly fictional, "
                "or clearly assumed."
            ),
            (
                "Label assumptions, confidence, and information gaps so the staff knows what still needs "
                "collection or review."
            ),
        ]
    return shared_notes


def _citations_for(product_type: StaffProductType) -> list[str]:
    return citation_titles(_source_refs_for(product_type))


def _structured_citations_for(product_type: StaffProductType) -> list[StructuredCitation]:
    citations = structured_citations(_source_refs_for(product_type))
    for citation in citations:
        citation.confidence = Confidence.low
        citation.notes = f"{citation.notes} Exact section citation requires RAG ingestion."
    return citations


def _source_refs_for(product_type: StaffProductType) -> tuple[SourceRef, ...]:
    if product_type in {StaffProductType.naval_letter, StaffProductType.memorandum, StaffProductType.endorsement}:
        return (*CORRESPONDENCE_REFERENCES, *OPORD_REFERENCES)
    if product_type == StaffProductType.aar:
        return (*TRAINING_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.sitrep:
        return STAFF_PRODUCT_REFERENCES
    if product_type in {
        StaffProductType.air_support_estimate,
        StaffProductType.air_ground_coordination_matrix,
        StaffProductType.aviation_supportability_matrix,
    }:
        return (*S3_REFERENCES, *ORM_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.running_estimate:
        return STAFF_PRODUCT_REFERENCES
    if product_type == StaffProductType.synchronization_matrix:
        return STAFF_PRODUCT_REFERENCES
    if product_type in {
        StaffProductType.orm_worksheet,
        StaffProductType.no_go_criteria,
        StaffProductType.residual_risk_decision_note,
        StaffProductType.rehearsal_safety_brief,
    }:
        return (*ORM_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type in {
        StaffProductType.admin_estimate,
        StaffProductType.admin_task_tracker,
        StaffProductType.routing_matrix,
        StaffProductType.pre_drill_admin_readiness_check,
    }:
        return (*S1_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type in {
        StaffProductType.troop_flow_checklist,
        StaffProductType.formation_transition_matrix,
        StaffProductType.leader_touchpoint_plan,
    }:
        return (*SEL_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.decision_support_matrix:
        return STAFF_PRODUCT_REFERENCES
    if product_type == StaffProductType.due_out_tracker:
        return STAFF_PRODUCT_REFERENCES
    if product_type == StaffProductType.collection_matrix:
        return (*S2_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.sustainment_matrix:
        return (*S4_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.movement_table:
        return (*S4_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.medical_estimate:
        return (*MEDICAL_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.casevac_quick_card:
        return (*MEDICAL_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type in {
        StaffProductType.religious_support_plan,
        StaffProductType.rmt_support_matrix,
        StaffProductType.morale_welfare_estimate,
    }:
        return (*LEADERSHIP_REFERENCES, *STAFF_PROCESS_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.road_to_war_brief:
        return (*S2_REFERENCES, *S3_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.public_affairs_plan:
        return (*PAO_REFERENCES, *STAFF_PROCESS_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.security_annex:
        return (*FORCE_PROTECTION_REFERENCES, *LEGAL_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type in {
        StaffProductType.visitor_control_checklist,
        StaffProductType.traffic_parking_control_plan,
    }:
        return (*FORCE_PROTECTION_REFERENCES, *LEGAL_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.resource_estimate:
        return (*G8_REFERENCES, *STAFF_PROCESS_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.inspection_readiness_plan:
        return (*IG_REFERENCES, *STAFF_PROCESS_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type == StaffProductType.ipb:
        return (*S2_REFERENCES, *MAP_REFERENCES, *STAFF_PRODUCT_REFERENCES)
    if product_type in {
        StaffProductType.opord,
        StaffProductType.warno,
        StaffProductType.frago,
        StaffProductType.conop,
        StaffProductType.decision_brief,
        StaffProductType.command_update_brief,
    }:
        return STAFF_PRODUCT_REFERENCES
    return OPORD_REFERENCES
