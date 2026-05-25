# Communications Sources

## Primary Source

- Title: MCDP 6 Command and Control
- Type: Marine Corps Doctrinal Publication
- Category: Command and control doctrine
- Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899771/mcdp-6/
- Classification label: UNCLASSIFIED
- CUI flag: false

- Title: MCTP 3-30B Information Management
- Type: Marine Corps Tactical Publication
- Category: Information management
- Official URL: https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899781/mctp-3-30b/
- Classification label: UNCLASSIFIED
- CUI flag: false

- Title: NAVMC 3500.56C Communications Training and Readiness Manual
- Type: NAVMC
- Category: Communications doctrine/training
- Official URL: https://www.marines.mil/News/Publications/MCPEL/Tag/21778/communications/
- Classification label: UNCLASSIFIED
- CUI flag: false

## Expected Uses

- `mos-commo`
- `s6-comms`
- Communications training checklists
- Reserve communications readiness prompts
- C2 support and PACE planning templates
- Information flow and command-and-control discipline

## Baseline S-6 Products

### PACE Matrix

Keep the matrix generic and authorized. Do not include real frequencies, COMSEC, call signs, sensitive network details,
or current operational communications plans.

| Level | Method | Use | Failure trigger | Owner |
| --- | --- | --- | --- | --- |
| Primary | Best authorized routine method | Normal reports and accountability | Missed report or unreachable key node | S-6 with S-3 and reporting elements |
| Alternate | Second authorized path | Routine traffic when primary degrades | Cannot reach the required audience | S-6 and unit leaders |
| Contingency | Simplified fallback | Minimum essential reports | Cannot pass minimum report | S-3 defines content; S-6 confirms supportability |
| Emergency | Last-resort authorized method | Safety, accountability, urgent command notification | No acknowledgement | Commander/XO sets escalation rule; S-6 validates |

### Radio Guard Chart

| Period | Net/group | Guard station | Responsibility | Report required |
| --- | --- | --- | --- | --- |
| Pre-execution comm check | Generic training net/reporting group | All reporting elements | Confirm reach-back, access, fallback | Ready/not ready and unresolved access issues |
| Execution window | Primary reporting path | CP/control node | Receive reports and track missed-report triggers | Status, CCIR/PIR updates, support requests, safety |
| Degraded comms | Alternate/contingency path | Alternate guard station | Acknowledge switch-over and simplify traffic | Affected users, viable reports, next check |
| Closeout | Primary/recovered path | CP and element leaders | Confirm accountability and capture AAR inputs | Final accountability and next-action owners |

### Comm Plan Outline

1. Purpose and supported C2 effect.
2. Supported event, audience, command relationships, and reporting elements.
3. Information flow: report types, report windows, acknowledgement rules, and missed-report action.
4. PACE matrix with switch criteria and owners.
5. Radio guard / monitoring chart with periods, reports, and escalation triggers.
6. Support plan: equipment, power, access, permissions, rehearsals, and help-desk path.
7. Risk controls: lost-comm action, degraded reporting, sensitive-detail exclusion, and AAR capture.

## Notes

The CommO agent must not process or generate real frequencies, COMSEC, keying material, call signs, sensitive network details, or current operational communications plans. Keep outputs to training-only checklists unless future controls support more.

For staff-function grounding, the best pairing is:

- `MCDP 6` for command-and-control thinking
- `MCTP 3-30B` for staff information-management discipline
- `NAVMC 3500.56C` for communications training and readiness expectations
