# Dual Today in History Design

**Status:** Approved 2026-07-15  
**Scope:** Overview dashboard history card, history record schema, local history selection, and regression coverage

## Objective

Restore the dashboard's history feature as a useful daily heritage brief. The card will show two independently selected and clearly labeled entries:

1. a Marine Corps event; and
2. a broader United States military event.

The feature must not present an unrelated event as if it happened on the current date.

## Current Problem

`TodayInMarineHistoryService.get_or_random()` returns a deterministic but otherwise arbitrary library item when no exact month/day match exists. The dashboard then renders only the first returned item. History records also lack explicit scope metadata, so the application cannot distinguish Marine Corps history from broader U.S. military history without unreliable text inference.

## Approved Selection Rules

Each history record will carry an explicit scope:

- `usmc` for Marine Corps events; or
- `us_military` for joint or non-USMC United States service events.

For each scope, the selector will:

1. prefer an event whose month and day exactly match the user's local calendar date;
2. otherwise choose the event with the smallest circular calendar distance from that date; and
3. return no entry when that scope contains no records.

Circular distance will compare month/day values on the leap-year-neutral reference calendar for year 2000, so February 29 remains valid and the cycle contains 366 days. The distance is the smaller of the forward and backward distances around that cycle. For example, December 31 and January 1 are one day apart. If one event falls the same number of days before the target as another falls after it, choose the preceding event, then use year label and slug as stable tie-breakers when multiple records share that month/day.

The service will return selection metadata with each result so the UI does not have to infer whether the event is exact or a fallback.

## Data Model and Sources

Extend `TodayInMarineHistoryItem` with explicit scope metadata. Existing bundled Marine Corps records will be marked `usmc`. New imports must declare a scope, with the existing Marine-history import workflow defaulting to `usmc`. Legacy local records that predate the field may be read as `usmc` because the prior feature and importer were explicitly Marine-history-only; this compatibility rule must be documented in code and covered by a test. Refreshed records must receive a defensible scope before they can participate in the two-entry selector.

Add a small curated set of broader U.S. military records backed by official primary or service-history sources. Initial sources may include:

- U.S. Army Center of Military History, *American Military History, Volume II*, including the 15 July 1918 defense by the 38th Infantry: <https://history.army.mil/Portals/143/Images/Publications/Publication%20By%20Title%20Images/A%20Titles%20PDF/CMH_Pub_30-22.pdf?ver=AZSZhsSpAI4Yo0ejWufwlw%3D%3D>
- U.S. Navy, USS *Tripoli* commissioning on 15 July 2020: <https://www.navy.mil/Press-Office/News-Stories/display-news/Article/2284375/us-navy-amphibious-assault-ship-uss-tripoli-joins-the-fleet/>

Official Marine Corps, Department of Defense, Army, Navy, Air Force, Space Force, and Coast Guard sources are preferred. Every bundled event must retain at least one source reference and a concise factual summary. Sources and facts are verified as of 2026-07-15 and remain subject to later official correction.

Wikipedia refresh results will not be treated as authoritative scope classifications. If that refresh path remains available, it may store an event only with an explicit, defensible scope; ambiguous foreign or generic military events must not enter either daily slot.

## API Contract

Replace the ambiguous single-list fallback contract with two explicit selections in the dashboard workspace response:

- Marine Corps selection;
- U.S. military selection;
- per-selection exact-date/fallback status.

The history library remains available for the existing history drawer. Compatibility fields may be retained temporarily only if required by another consumer, but the Overview card must consume the explicit selections.

Personal and demo dashboard routes must use the same selector and return the same shape.

## Dashboard Presentation

Keep one expandable Today in History card on Overview. Within it, render up to two stacked entries:

- **Marine Corps — Today** or **Closest Marine Corps event**;
- **U.S. Military — Today** or **Closest U.S. military event**.

Each entry shows its actual month, day, year, title, summary, and source link. A fallback entry must display its actual event date and must never be worded as though it happened today.

If one scope has no data, show the available entry and a concise unavailable state for the missing scope. If neither scope has data, hide the card without fabricating content.

## Error Handling

- Empty or malformed local history files must not prevent dashboard loading.
- Records with an unknown scope must not be silently assigned to a daily slot.
- Missing references should be rejected for bundled seed records by validation tests.
- Network refresh failure continues to serve local data and must not alter the selected local entries.

## Testing

Add coverage for:

- exact USMC and U.S. military matches on the same day;
- nearest USMC fallback while the U.S. military event is exact;
- nearest U.S. military fallback while the USMC event is exact;
- circular distance across December/January;
- deterministic equal-distance ties;
- one empty scope and both scopes empty;
- scope preservation while loading seed and local files;
- personal and demo dashboard response parity;
- dashboard rendering of both labels, actual dates, fallback labels, and source links;
- validation that bundled entries include recognized scope values and source references.

Run targeted history and dashboard tests, then the repository's full pytest, mypy, and Ruff checks.

## Out of Scope

- Building a complete 365-day historical encyclopedia;
- scraping arbitrary web pages at dashboard load time;
- using AI or keyword inference to classify historical events;
- redesigning the history library drawer beyond compatibility updates required by the new schema.

---

DRAFT — Verify all references against current official sources before acting.
