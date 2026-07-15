# Family Readiness and Career Opportunities Design

**Date:** 2026-07-15

**Status:** Draft for written review; product direction approved in conversation

**Scope:** A saved Family & Deployment Readiness checklist in Bench+Files, one supporting readiness agent, and a refreshable Career Opportunities widget on Watch.

## Purpose

Add two focused capabilities without introducing another dashboard lane or rebuilding the existing workspace:

1. Help a Marine prepare their household and support network for an absence ranging from extended annual training through approximately one year overseas.
2. Consolidate public SMCR, IMA, and active-duty/ADOS opportunity information into a sortable Watch surface that always links back to the official source.

Both capabilities reuse existing local-first storage, dashboard cards, agent registry, calendar export, opportunity tracking, and source-refresh conventions.

## Product Boundaries

- Family readiness is a Bench+Files workflow, not a new workspace, spouse account, or family portal.
- Career opportunities appear on Watch as a widget or Connected Feeds sub-card, not a new career lane.
- The application remains UNCLASSIFIED-only and must not collect mission details, precise unit movement information, classified or CUI material, SSNs, dependent identity records, medical records, account credentials, or unnecessary PII.
- Family readiness may track that the user consulted legal assistance or completed a document review. It does not draft a power of attorney, will, custody instrument, or other legal document and does not store document contents.
- DEERS support consists of reminders, official links, and completion tracking. The application does not connect to or mirror DEERS.
- Opportunity recommendations do not determine eligibility, availability, assignment, selection, funding, or command approval.
- Every generated checklist, summary, or advisory includes: `DRAFT — Verify all references against current official sources before acting.`

## Selected Approach

The selected approach is a compact integrated addition:

- one Bench+Files tile that creates and reopens named readiness events;
- one combined Family & Deployment Readiness Advisor under **Reserve Admin & Readiness**;
- one Career Opportunities Watch widget that normalizes whatever structured public data is available and degrades safely to official link-outs;
- deterministic profile matching only when the source exposes enough rank or MOS information to explain the result.

A links-only implementation was rejected as too shallow. Dedicated Family Readiness and Career workspaces were rejected as unnecessary scope.

## Family & Deployment Readiness Checklist

### Placement and entry flow

Add **Family & Deployment Readiness** as the final tile in the Staff Products area of Bench+Files. Opening it shows:

- existing saved readiness events, newest updated first;
- **Start readiness checklist**;
- event title, such as `Extended AT 2027` or `Overseas orders 2028`;
- approximate absence start and end windows;
- a duration band derived from the dates but editable by the user;
- an option to open the Family & Deployment Readiness Advisor for tailoring.

The supported duration bands are application heuristics, not policy:

- extended AT or short absence: roughly 14–30 days;
- temporary duty or extended training: roughly 31–180 days;
- mobilization or long overseas absence: roughly 181–395 days;
- custom duration when none of the bands fit.

The UI uses the same modal/editor conventions as existing Bench+Files generations. It does not add a top-level navigation item.

### Saved event model

A user-key-scoped readiness event owns:

- stable event ID;
- title;
- approximate start and end dates or windows;
- duration band;
- status: planning, active, reintegration, archived;
- checklist items;
- public and user-entered contact references;
- optional acronym entries added for this event;
- generated milestone dates;
- creation and update timestamps;
- source titles, source URLs, and source verification dates used to seed the event.

Each checklist item owns:

- stable item ID;
- category;
- task text;
- plain-language explanation for a spouse, partner, or support person;
- status: not started, in progress, complete, not applicable;
- optional responsible-person label without requiring a full name;
- optional target date;
- optional low-sensitivity notes;
- official source URL when applicable;
- whether the item is baseline, duration-added, or user-created.

Readiness events should use a small typed local store under the configured local state root. They may be surfaced through Bench+Files alongside generation documents, but checklist state must not be hidden inside an unvalidated free-form `fields` dictionary. Existing User Docs remains appropriate for an exported spouse-friendly summary, not the canonical checklist record.

### Checklist modules

Every event begins with a common baseline and receives additional tasks based on duration and user choices.

1. **Unit and administrative coordination**
   - confirm the unit-provided checklist and reporting requirements;
   - identify the unit readiness or family-readiness contact using user-entered or official public information;
   - validate emergency-notification and communication expectations;
   - record public reference numbers and generic billet labels rather than private rosters.

2. **Legal-readiness actions**
   - schedule or complete an installation legal-assistance review;
   - review whether a limited or special power of attorney is needed;
   - review wills, emergency data, beneficiaries, and document access with qualified support;
   - record completion only, never document language or sensitive identifiers.

3. **DEERS, identification, and health-benefit administration**
   - check whether DEERS contact information is current;
   - verify dependent ID-card expiration and locate a RAPIDS office if action is needed;
   - link to milConnect and current TRICARE/DEERS guidance;
   - remind the user that DEERS and TRICARE contractor records may require separate updates when the official guidance says so.

4. **Household, finance, and emergency continuity**
   - identify recurring bills, access arrangements, vehicle/home responsibilities, emergency contacts, and backup support;
   - link financial or legal questions to the appropriate existing advisor or qualified professional;
   - avoid storing bank, card, account, or credential data.

5. **Communication and OPSEC**
   - agree on a communication rhythm and backup method;
   - provide spouse-friendly explanations of operational-security cautions;
   - prohibit mission, route, exact movement, location, or return details from generated shareable summaries.

6. **Family and support-network preparation**
   - identify child, pet, school, employer, caregiver, or special-support coordination only at a generic task level;
   - offer official Military OneSource and installation-support links;
   - avoid names, diagnoses, custody facts, or other unnecessary sensitive details.

7. **Reintegration and closeout**
   - revisit powers of attorney and access arrangements with legal or institutional support;
   - restore household responsibilities and review benefits/contact information;
   - schedule a family expectations conversation and archive the event when complete.

Users may add, edit, reorder, mark not applicable, and restore baseline items. Baseline items may be hidden for the event but are not permanently deleted from the system template.

### Contacts and plain-language glossary

Each event contains a compact contacts block rather than a separate directory. Suggested roles include:

- unit readiness/family-readiness contact;
- unit duty or administrative contact;
- installation legal assistance;
- RAPIDS/ID-card office;
- TRICARE/DEERS support;
- American Red Cross emergency communications;
- Military OneSource.

Official public contacts include a source URL and last-verified date. User-entered unit contacts are optional, local-only, and minimally structured as role, organization, phone/email, and notes. The UI warns users not to add private rosters or unnecessary PII.

The event includes an expandable **Plain-language guide** seeded with common Marine Corps, reserve, orders, benefits, and family-support terms. Definitions spell out the term first and explain what the spouse or support person may need to do. Users may add event-specific terms. Generated summaries include only glossary entries used by that event.

### Rough calendar and export

The event generates a milestone list relative to the approximate absence window. The default rhythm may include T-90, T-60, T-30, T-14, T-7, departure-window, mid-absence check, return-window, and reintegration follow-up milestones when the duration supports them.

Milestones contain only personal readiness actions. They must not include unit movement, mission, route, destination, force-composition, or return-operation details.

Users may edit milestone target dates and download an `.ics` file through the existing local ICS provider pattern. Calendar titles are generic, such as `Review DEERS contact information`, and the description includes the draft/current-source warning.

### Spouse-friendly summary

The user may generate a printable/shareable summary containing:

- event title and broad absence window;
- incomplete household-facing tasks;
- communication expectations;
- selected public and user-approved contacts;
- relevant plain-language terms;
- rough milestones;
- official resource links and warnings.

The summary excludes private notes, exact operational details, sensitive identifiers, and any item the user marks `Do not share`. It is stored as an existing generation document and may be saved to a project using existing User Docs behavior.

## Family & Deployment Readiness Advisor

### Registry and scope

Add a stable agent ID such as `family-deployment-readiness-advisor` under **Reserve Admin & Readiness**. The agent card displays that ID under the existing agent-name convention.

The agent:

- tailors a checklist for an existing or new readiness event;
- scales recommendations based on duration and broad household/support needs;
- explains acronyms and processes in plain language;
- identifies missing roles, unresolved tasks, and approaching milestones;
- prepares a spouse-friendly summary;
- routes legal, medical, financial, GTCC, fitness, command, or travel questions to qualified support or an existing narrowly scoped agent.

It asks only for the event title, approximate duration/window, whether the Marine has household/dependent/support responsibilities requiring generic planning, and which preparation areas are already complete. It does not ask for names, SSNs, diagnoses, account information, mission, route, or exact movement details.

The first version may create a proposed checklist from typed local rules. The user reviews the proposed additions before they are saved. Optional external inference remains subject to the repository's existing sanitized-preview and explicit-acknowledgement controls.

## Career Opportunities Watch Widget

### Placement

Add **Career Opportunities** to Watch as a sub-card directly below or within the visual group containing Connected Feeds. It follows existing feed conventions:

- a global refresh control;
- independent source refresh controls;
- per-source loading, success, failure, item-count, and last-checked states;
- external-link labels;
- publication dates only when supplied by the source;
- a visible stale-data warning when showing cached results.

### Official source registry

The first source registry contains:

1. **MARFORRES Reserve Billets** — SMCR and IMA gateway:
   <https://www.marforres.marines.mil/About/Reserve-Billets/>
2. **MARFORRES Active Billets / Find** — active-duty, IA/JIA, and ADOS information and application links:
   <https://www.marforres.marines.mil/Staff-Sections/General-Staff/G-1-Administration/Active-Billets/Find/>
3. Any official listing document or endpoint linked from those pages that can be fetched without authentication and remains within an allowlisted `.mil` or approved DoD host.

The current `MARFORRES_BILLETS_URL` points to an older generic `/Billets/` path and must be replaced by the current gateway registry. The route must continue rejecting arbitrary source URLs supplied by clients.

### Source adapters and refresh behavior

Each official source has a typed adapter with:

- allowlisted source key and canonical URL;
- fetch timeout and response-size limit;
- content-type validation;
- parser for supported HTML tables/cards or public linked documents;
- source-page link discovery;
- normalized result mapping;
- source warnings and refresh metadata.

Refresh proceeds independently per source. A failure in one source does not clear successful cached results from another source or block unrelated refresh actions.

Because the current public pages function partly as gateways and may move listings into tabs, linked documents, JavaScript modules, or authenticated forms, refresh has three truthful outcomes:

1. **Listings refreshed** — normalized public rows were extracted.
2. **Source available; structured listings unavailable** — show the official page and any safe discovered official listing links.
3. **Refresh failed** — retain the last successful cache, label its age, show the error, and provide **Open official source**.

The widget never interprets a parser failure as “no open billets.” Sample fixtures remain test/demo-only and must never appear in personal mode as current listings.

### Normalized opportunity model

Extend the existing opportunity types to distinguish at least:

- SMCR;
- IMA;
- ADOS;
- IA/JIA or other active-duty opportunity when the source identifies it;
- unknown/other without guessing.

A normalized record may contain:

- stable fingerprint/source ID;
- title or billet description;
- opportunity/component type;
- unit;
- location;
- rank or rank range;
- MOS or MOS range/list;
- duration;
- publication date;
- application/due date;
- source name and canonical source URL;
- direct listing/application URL when available;
- notes/requirements;
- detected/last-seen timestamps;
- parser provenance and warnings.

Unavailable values remain null and render as `Not provided` or `Date unavailable`. The application never invents publication dates, deadlines, eligibility, or duration.

### Sorting and filtering

The widget supports client-visible sort controls for:

- title;
- opportunity/component type;
- rank;
- MOS;
- unit;
- location;
- duration;
- publication date;
- application/due date;
- profile-match score when that score is available.

Every field supports ascending and descending order. Date sorts place unavailable dates after dated records in both directions unless the user explicitly chooses an `Unknown first` option later. Rank sorting uses a Marine grade-order mapping while preserving the displayed source text. MOS sorting uses normalized string/numeric ordering without implying equivalence.

Default sorting is newest publication date first when at least one publication date is present; otherwise it preserves source order. The UI states which fallback is active.

Filters include opportunity type, rank, MOS, location, source, and free-text keyword. Sorting and filtering compose without mutating the cached records. A **Clear filters** action restores the current source set and default order.

### Profile matching

The existing deterministic recommender may be reused only after a normalized record contains enough structured data to explain its score. The first version may expose a **Profile matches** filter or score sort using:

- exact or normalized MOS match;
- apparent rank/range compatibility;
- desired location and willingness-to-travel preferences when the user has entered them;
- user-entered career keywords.

Every score shows its match reasons. Records with insufficient structured data remain visible but unscored. The UI does not label unscored records as poor matches. If live-source structure makes reliable matching disproportionate, recommendation controls are omitted without blocking consolidation, sorting, filtering, refresh, or link-out delivery.

### Tracking and link-outs

Users may track a normalized opportunity through the existing local OpportunityTracker. Tracking copies source provenance and the last-seen timestamp but does not freeze or imply current availability.

Every row provides **Open official listing** or **Open official source**. The application does not submit forms, authenticate to DoD systems, or auto-apply. Authenticated forms open in the user's browser and remain outside the application.

## API and Storage Shape

The implementation plan should prefer small typed additions:

- family-readiness schemas, store, service, and route module;
- family-readiness calendar export using the existing ICS provider pattern;
- one agent builder and registry/category entry;
- an expanded billet source registry and source-adapter service;
- normalized opportunity cache stored under the existing opportunities/source-state roots or a dedicated configured child directory;
- dashboard/workspace response additions only where needed to hydrate the Watch widget.

All local records remain user-key scoped where they contain user state. Public opportunity cache data may be shared locally across user keys, while tracking and preferences remain user-scoped.

No database migration, frontend framework, background scheduler, browser automation dependency, or cloud service is introduced.

## Error, Empty, and Stale States

- No readiness events: show **Start readiness checklist** and a short explanation.
- Incomplete event setup: preserve entered fields and identify the missing field inline.
- No source listings extracted: explain that the official source is available but structured data could not be read; provide link-outs.
- One source fails: retain its last successful cache and continue refreshing other sources.
- Cached opportunities: show `Last refreshed`, `Last seen`, and a stale warning rather than silently presenting old data.
- Missing publication/due date: show `Date unavailable` and keep it last in date sorting.
- Removed official listing: retain a tracked user record with `Not present in latest refresh; verify at source` rather than deleting it.
- Source layout change: fail closed, log a parser warning without response-body secrets, and never substitute test/demo rows.
- Demo mode: use explicitly demo-tagged readiness events and opportunity fixtures; hide them immediately when Demo is off.

## Accessibility and Cohesion

- Reuse existing card, modal, feed-row, button, status, and external-link styles.
- All checklist items, sort controls, filters, and refresh controls are keyboard reachable and visibly focused.
- Status changes are announced through an accessible live region without moving focus.
- Sort controls expose the active field and direction in text and ARIA state.
- Tables or card lists retain field labels at narrow widths; horizontal scrolling is not the only way to reach row actions.
- Completion is never conveyed by color alone.
- Each asynchronous source refresh owns its own pending/success/failure state.

## Source Baseline

Primary sources verified for this design on 2026-07-15:

- MARFORRES Reserve and IMA billet gateway:
  <https://www.marforres.marines.mil/About/Reserve-Billets/>
- MARFORRES Active Billets / Find:
  <https://www.marforres.marines.mil/Staff-Sections/General-Staff/G-1-Administration/Active-Billets/Find/>
- Military OneSource, Preparing for Military Deployment:
  <https://planmydeployment.militaryonesource.mil/pre-deployment>
- Military OneSource, Legal Matters Before Deployment:
  <https://planmydeployment.militaryonesource.mil/pre-deployment/service-members/legal-matters-steps-to-take-before-deployment/>
- TRICARE, Defense Enrollment Eligibility Reporting System:
  <https://www.tricare.mil/DEERS>
- TRICARE, milConnect:
  <https://www.tricare.mil/Plans/Eligibility/DEERS/milConnect>
- DoD ID Card Office Online / RAPIDS locator:
  <https://idco.dmdc.osd.mil/idco/>
- Military OneSource, Common Military Acronyms:
  <https://www.militaryonesource.mil/military-basics/extended-family-friend/common-military-acronyms/>

Implementation must re-check live page structure, downloadable listing links, contact details, and last-updated dates before adding exact policy or contact claims to built-in content.

## Testing and Validation

Add schema, store, service, route, parser, recommender-gating, and dashboard assertions covering:

- creating, reopening, updating, archiving, and deleting a readiness event;
- duration-band baseline selection and user customization;
- legal/DEERS links and absence of legal-document content fields;
- milestone generation and safe ICS export;
- spouse-summary redaction of private notes and non-shareable items;
- agent registration, category, allowed sources, prohibited-input behavior, and draft footer;
- current allowlisted billet source URLs;
- parsing SMCR, IMA, and ADOS fixtures derived from representative public structures;
- partial source success, timeout, content-type rejection, layout changes, and cached fallback;
- no demo/sample opportunity leakage into personal mode;
- stable deduplication/fingerprints;
- every sort field in both directions, including null dates and grade-order rank sorting;
- combined filters and clear-filter behavior;
- profile scoring only when enough structured data exists;
- official link-outs and tracked-opportunity provenance;
- keyboard labels, live statuses, and active-sort accessibility attributes.

High-value browser flows cover:

1. Create `Extended AT 2027`, complete tasks, reopen it, and export its generic milestone calendar.
2. Generate a spouse-friendly summary and confirm private notes are absent.
3. Refresh all opportunity sources when one succeeds and one fails, then open both an extracted listing and the failed source's official fallback.
4. Filter to IMA, sort by rank, reverse direction, clear filters, and sort by publication date with missing dates last.
5. Toggle Demo off and confirm demo readiness events and opportunity rows disappear.

Before release, run:

```text
uv run pytest tests/ -q
uv run mypy app tests
uv run ruff check .
```

Then perform a browser cohesion review across Watch, Bench+Files, AI, Demo mode, connected-feed refresh behavior, desktop launch, and the existing Travel/FitRep features.

## Explicitly Out of Scope

- a Family Readiness workspace or top-level lane;
- a spouse login, remote portal, shared account, email, or messaging feature;
- legal-document creation or storage;
- DEERS/TRICARE synchronization;
- exact deployment or unit movement tracking;
- automated DoD authentication, form submission, application, or assignment workflow;
- opaque AI eligibility decisions;
- mandatory recommendation scoring;
- background scraping or notifications when the app is not running.

DRAFT — Verify all references against current official sources before acting.
