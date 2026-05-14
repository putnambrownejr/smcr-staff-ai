# Source Inventory and Integration Plan

**Executive Summary:** We identified and analyzed NIPR-accessible Marine Corps sources for doctrine, orders, news, and organizational data.  Key sources include the Marines.mil news site (MARADMIN/ALMAR messages and MCPEL publications with HTML and PDF content) and the MARFORRES site (unit hierarchy and exercise announcements). We outline URLs, formats, and scraping considerations for each. For example, MARADMINs can be fetched via the Marines.mil RSS feed or by parsing the MARADMIN list page【105†L109-L112】. The Marine Corps Publications Electronic Library (MCPEL) provides access to MCOs, MCBuls, MCDPs/MCWPs, etc., with individual HTML pages linking to PDF orders (e.g., MCO 1800.12【115†L98-L106】) and doctrine (MCDP 1【146†L98-L106】). Reserve force data comes from MARFORRES (Marine Forces Reserve) pages: the **“Marine Forces Reserve – Leaders”** page provides an HTML tree of commands and sub-units【132†L61-L69】【133†L212-L220】, and the **“Operations/Exercises”** news section contains exercise announcements (e.g., ITX‐4‐23【138†L610-L614】, UNITAS【140†L608-L615】). We document RSS feeds (MARADMIN, Orders/Directives) and direct URLs for key documents (MCOs, MCDPs). For each source we note update frequency, parsing method (RSS/XML vs HTML vs PDF), rate-limit issues, and examples of selectors or download links. We include a comparison of scraping methods, and diagrams for data flow (scraper → parser → storage → RAG). Finally, we provide a short list of immediate action items (e.g. fetch a MARADMIN RSS sample, download an MCO PDF) and solicit user input on unit priorities.

## MARADMINs and Messages

- **Purpose:** Ingest official Marine Corps messages (MARADMINs, ALMARs) for Reserve personnel guidance.  
- **Sources:** Marines.mil “Messages” pages provide lists of ALMAR and MARADMIN entries (e.g. [**MARADMINS** listing](https://www.marines.mil/News/Messages/MARADMINS/))【100†L96-L104】. Each MARADMIN has an HTML page (e.g. [219/26 MARADMIN content](https://www.marines.mil/News/Messages/Messages-Display/Article/4484718/...))【102†L98-L107】 and a print-friendly HTML (e.g. [Print view](https://www.marines.mil/DesktopModules/ArticleCS/Print.aspx?Article=4484718))【103†L27-L35】.  
- **Fetching Method:** Two options:  
  1. **RSS Feed:** Marines.mil provides an official RSS feed for MARADMINs (ContentType=6, category=14336)【105†L109-L112】【106†L0-L0】. Use an HTTP GET on the RSS URL (e.g. `RSS.ashx?...&category=14336`) to retrieve new messages. Benefits: structured XML with latest items; downsides: limited items (pagination or custom feed may be needed).  
  2. **HTML Scraping:** Parse the MARADMIN listing page (e.g. the HTML grid at [100]) and extract links and metadata. Selectors could target table rows or link text (e.g. number and title columns). Each “Number” cell contains an anchor to the message page. Example selector: `//table//tr/td/a` for links. Pagination may be via year filters (the UI shows year toggles) – might require multiple year queries or simulation.  
  3. **PDF/Print Parsing:** If needed, use the print view (DesktopModules/ArticleCS/Print.aspx) which is clean text. Example: print link [103] shows the full message body in plain HTML without navigation. Use it to easily extract structured fields (e.g. MSGID, SUBJECT).  
- **Deliverables:**  
  - **Scripts:** RSS fetcher and HTML scraper (e.g. Python + `requests`/`BeautifulSoup` or Node.js).  
  - **Parsers:** XPath or CSS to extract MARADMIN number, date, subject, body text.  
  - **Fixtures:** Sample RSS XML (latest 10 items) and HTML snippets for parser testing.  
- **Effort:** *Medium*. RSS is quick; robust HTML scraping with pagination/filtering requires more work.  
- **Dependencies:** Public HTTP access to marines.mil (no login needed). No special API tokens.  
- **NIPR Feasibility:** Fully accessible (public .mil site). No classified content.  
- **Risks:** Rate-limiting or anti-bot not obvious, but throttle requests (e.g. one per second). The dynamic year filter may complicate scraping; may need form parameters. MARADMIN updates are infrequent, RSS mitigates load.  
- **Next Steps:** Test fetching the MARADMIN RSS (e.g. using `requests`) and the HTML listing. Extract one MARADMIN (e.g. 219/26) via print view to verify parser works.  

## MCPEL Publications (MCOs, MCBuls, MCDPs, etc.)

- **Purpose:** Ingest official Marine Corps orders, bulletins, and doctrine (Uniform regs, FitRep, ORM, staff manuals).  
- **Sources:** The Marine Corps Publications Electronic Library (MCPEL) on Marines.mil lists all releasable orders and directives【115†L108-L112】【146†L98-L106】. The MCPEL **Catalog** page (`/Publications/MCPEL/Custompubstatus/3000/`) offers filters (by Type, SSIC). Individual items have HTML pages with summaries and a “DOWNLOAD PDF” link (e.g. MCO 1800.12【115†L108-L112】, MCDP 1【146†L98-L106】).  
- **Fetching Method:**  
  1. **MCPEL Web UI Scraping:** Use queries or static filters to list relevant items. For example, to find all current MCOs, search by type “MCO” in MCPEL (or navigate via tags). Since the UI is dynamic, we might use the MCPEL **Tag** feature (as [120] shows tag links) or search endpoints. Each entry’s HTML (like [115], [126], [146]) can be parsed for metadata and the PDF link.  
  2. **PDF Download:** Once we have an item, use the “DOWNLOAD PDF” link (e.g. [115]→[116] for MCO 1800.12, [146]→[147] for MCDP 1) to fetch the binary PDF. Store it or text-extract it with a PDF library (with careful handling of large docs).  
  3. **RSS/Feed:** Marines.mil provides an “Orders & Directives” RSS (ContentType=5)【105†L109-L112】【108†L0-L0】 that may include recent MCOs/MCWPs. Use this to discover new orders.  
- **Deliverables:**  
  - **Scripts:** MCPEL scraper to query or crawl lists (MCO, MCBul, NAVMC, MCWP, etc). PDF downloader for each relevant item.  
  - **Parsers:** Extract Title, SSIC, status, effective date from HTML; and citations/paragraphs from PDFs.  
  - **Fixtures:** Sample HTML of an MCPEL entry and the corresponding PDF bytes. Tables of choices (e.g. vector DBs, LLMs) are not needed here.  
- **Effort:** *High.* The MCPEL interface is not a simple static list; may require reverse-engineering of its filtering or tag system. Bulk PDF download and text extraction are involved.  
- **Dependencies:** Network access; ability to handle PDF and HTML parsing libraries. Possibly need to respect website load.  
- **NIPR Feasibility:** Yes, all content is unclassified/public release.  
- **Risks:** Large volume of PDFs; ensure we only download needed ones (avoid re-fetching unchanged docs). Some “Current” orders might be superseded and marked “Deleted” in MCPEL – pay attention to status.  
- **Next Steps:** Identify top-priority publications (e.g. Uniform Regs, FitRep manual, ORM order). Use MCPEL search (or tag pages) to get their Article IDs, then fetch their HTML and PDFs to test extraction.  

## Doctrine Publications (MCDP/MCWP)

- **Purpose:** Include Marine Corps doctrinal manuals as knowledge sources (for tailored doctrinal agents).  
- **Sources:** Many doctrinal pubs are accessible via MCPEL (e.g. MCDP, MCWP). Example: MCDP 1 (Warfighting) has an MCPEL entry【146†L98-L106】 and PDF【147†L2-L9】. The “Doctrine” link on the Publications page (SharePoint) is CAC-protected, so use MCPEL for public versions.  
- **Fetching Method:** Same as above – use MCPEL search by tag “doctrine” or specific MCDP/MCWP numbers. Fetch entry page and PDF.  
- **Deliverables:** Script to collect key doctrine manuals (MCDPs, MCWPs listed in MCPEL). PDF downloads and text extraction.  
- **Effort:** *Medium.* Fewer items than MCOs, but still manual identification needed.  
- **Dependencies:** As above (MCPEL access). Possibly some references on Marines.mil news site.  
- **Feasibility:** NIPR-public.  
- **Risks:** Minimal. Ensure getting current versions (check MCPEL status).  
- **Next Steps:** Make a list of needed doctrinal pubs (e.g. MCDP 1, MCWP 3-34.5 Drill and Ceremonies, MCRP/MCWP on Civil Affairs) and fetch via MCPEL.

## Reserve Unit and Command Structure

- **Purpose:** Build the organizational hierarchy (units and higher commands) for SMCR Marines.  
- **Sources:** The MARFORRES site provides a complete tree of Reserve units. The **“Marine Forces Reserve – Leaders”** page shows MARFORRES HQ sections and subordinate units (4th MARDIV, 4th MAW, 4th MLG, FHG) with clickable links【132†L61-L69】【133†L212-L220】. Each unit (e.g. 2d Battalion, 23d Marines) may have its own page.  
- **Fetching Method:** Scrape the HTML at `https://www.marforres.marines.mil/Marine-Forces-Reserve-Leaders/`. Use an HTML parser to traverse nested `<ul>/<li>` lists. For example, CSS/XPath selectors like `#nav li a` or `//*[@id="nav"]/ul/li//a` would catch all unit links. Capture (Unit name → URL → parent unit).  
- **Deliverables:**  
  - **Script:** Crawler that downloads and parses the leaders page. Possibly follow unit links to collect additional metadata (location, email).  
  - **Data:** A JSON or CSV mapping “unit → parent” (e.g. 14th Marines → 4th MARDIV) and “unit → base/location”. Example snippet from MARFORRES: *4th Marine Division > 14th Marine Regiment > 2d Battalion > Headquarters Battery*【132†L61-L69】.  
  - **Artifacts:** Table of units/hierarchy, small diagram snippet of org chart.  
- **Effort:** *Low to Medium.* The HTML is straightforward; the tree is in a static page. The hierarchy is large (~hundreds of units) but well-structured.  
- **Dependencies:** Public web access. Possibly some unit pages require login for details, but basic names are visible.  
- **Feasibility:** High (public .mil).  
- **Risks:** If site redesign changes HTML structure, scrapers may break. Also ensure not to miss any “inactive” units (likely none in MARFORRES list).  
- **Next Steps:** Fetch and parse the current leaders page. Produce a draft unit hierarchy list. *Action:* Ask user to confirm which specific units to prioritize (see table below).  

| Command Level             | Example Unit                          | Include? (Yes/No) |
|---------------------------|---------------------------------------|-------------------|
| Marine Forces Reserve HQ  | *Marine Forces Reserve (HQMC)*       |                   |
| 4th Marine Division       | *14th Marine Regiment*               |                   |
| 4th Marine Division       | *23d Marine Regiment*                |                   |
| 4th Marine Division       | *25th Marine Regiment*               |                   |
| 4th Marine Aircraft Wing  | *MAG-41, MAG-49, MACG-48*            |                   |
| 4th Marine Logistics Gp   | *4th MLG, CLR-4, 4th CRR*            |                   |
| Force Headquarters Gp     | *FHG, 1st, 3d, 4th Civil Affairs Gp*|                   |
| Other (list as needed)    |                                       |                   |

*User action:* Please indicate which units and command levels we should include first for the organizational dataset. You may modify or add to the list above.

## Exercises and Training Events

- **Purpose:** Collect data on typical Reserve training events and annual exercises by unit/season.  
- **Sources:** The MARFORRES “Operations/Exercises” section (under News & Photos) archives major exercises. Examples: **ITX 4-23** (Integrated Training Exercise, a summer MAGTF training)【138†L610-L614】, **UNITAS LXIII (2022)** (multinational maritime exercise)【140†L608-L615】, and presumably others (e.g. SME, small exercises). Each exercise has an “About” blurb on its page.  
- **Fetching Method:** Crawl `https://www.marforres.marines.mil/News-Photos/Operations-and-Exercises/`. This page lists years and exercises; follow links to individual exercise pages (e.g. ITX-4-23, UNITAS). Parse the “About” section text and dates. For ITX, [138] shows ITX is the “annual capstone MAGTF training event” in June【138†L610-L614】. For UNITAS, [140] explains it is a longstanding maritime exercise in Sep【140†L608-L615】.  
- **Deliverables:**  
  - **Scripts:** Scraper to retrieve each exercise page and extract event name, year, description, date/location.  
  - **Dataset:** A table of exercise names, type, typical months, participating units. E.g. *ITX (Jun, MAGTF elements)*, *UNITAS (Sep, international maritime)*.  
  - **Artifacts:** Mermaid timeline or seasonal chart (e.g. summer = ITX, fall = UNITAS, etc.).  
- **Effort:** *Medium.* There are many exercises; focus on the big ones first (ITX, UNITAS, CASP, SERPENTEX, etc.).  
- **Dependencies:** Public MARFORRES news site.  
- **Feasibility:** High.  
- **Risks:** Exercise pages vary in format. Some older events might be archived as PDFs or on DVIDS. But recent years are HTML.  
- **Next Steps:** Fetch a list of exercise pages (e.g. by year) and sample one (ITX 4-23【138†L610-L614】). Extract key info for timeline.  

## Third-Party Tools and Resources

- **Purpose:** Identify existing open-source tools and data sources to reuse (e.g. admin tools, templates).  
- **Sources:** Examples like Jeranaias’s *usmc-tools* (a GitHub collection of Marine admin web tools) show approaches for Pro/Con statements, OSMEAC orders, etc.【144†L111-L119】. These OSS tools are offline-capable and might inspire components (e.g. AAR/OSMEAC generator). Also consider DVIDS public videos/news for imagery (but NIPR scraping limited).  
- **Deliverables:** List of relevant OSS projects (with URLs), short summary. Possibly reuse code (license permitting).  
- **Effort:** *Low.* Mostly web research.  
- **Dependencies:** GitHub/public repos.  
- **Next Steps:** Catalog any well-known OSS Marine tools (like those at jeranaias.github.io/usmc-tools【144†L111-L119】) and consider whether any code or ideas can be integrated into the agent UI or templates.

## Scraping Method Comparison

| Method      | Use Case                       | Pros                          | Cons                             | Example                                |
|-------------|--------------------------------|-------------------------------|----------------------------------|----------------------------------------|
| **RSS**     | News feeds (MARADMIN, MCO)     | Automatic updates, simple XML | Only last N items; sometimes incomplete metadata | Marines.mil MARADMIN RSS【105†L109-L112】|
| **HTML**    | Listing pages (MCPEL, Leaders) | Full info, easy to parse links| Layout changes break parsers      | MARFORRES Leaders page【132†L61-L69】   |
| **PDF**     | Official orders/manuals        | Complete text, authoritative  | Harder parsing, large binary     | MCO 1800.12 PDF【116†L2-L10】           |

## Data Flow Diagram

```mermaid
flowchart LR
    A(MARADMIN RSS/XML) -->|feed| D[Scraper]
    B(MARADMIN/News HTML) --> D
    C(MCPEL HTML) --> D
    E(MCPEL PDF) --> D
    F(MARFORRES Org HTML) --> D
    G(MARFORRES Exercises HTML) --> D
    D --> H[Parser]
    H --> I[(Storage: Database/Files)]
    I --> J[Vector DB / Indexes]
    I --> K[RAG Engine (LLM + Index)]
```

## Artifacts and Next Actions

- **Scripts to write:** RSS fetchers (e.g. Python script `fetch_maradmin_rss.py`), HTML parsers (e.g. `parse_marforres_structure.py`), PDF downloaders (`download_mco_pdf.py`).  
- **Data tables:** Unit hierarchy mapping; calendar event list; vector DB comparison.  
- **Diagrams:** Org chart snippet (Mermaid), training timeline (Gantt by quarter).  
- **Immediate Steps:**  
  1. Test MARADMIN RSS fetch and parse one MARADMIN via print view.  
  2. Download a sample MCPEL PDF (e.g. MCO 1020.34H or MCO 1800.12) to ensure PDF reading works.  
  3. Scrape the MARFORRES Leaders page to output the first 10 units and parents.  
  4. Fetch the MARFORRES ITX-4-23 page【138†L610-L614】 and verify extraction of the “About” text.  

By following these tasks, the initial data sources will be in place for the SMCR multi-agent repository. The above plan sets up an ingestion pipeline (illustrated above) and highlights immediate coding tasks (e.g. “fetch MARADMIN RSS feed”). All identified sources are NIPR-accessible (public .mil) and suitable for integration under Marine Corps compliance.