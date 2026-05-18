from __future__ import annotations

from dataclasses import dataclass

from app.schemas.agents import Confidence, StructuredCitation
from app.schemas.source_state import SourceTrustMarker, VerifiedSourceStatus


@dataclass(frozen=True)
class SourceRef:
    title: str
    url: str
    publisher: str
    notes: str

    def citation(self) -> StructuredCitation:
        return StructuredCitation(
            title=self.title,
            url=self.url,
            publisher=self.publisher,
            confidence=Confidence.medium,
            notes=f"{source_tier_for_ref(self)}. {self.notes}",
        )

    def trust(self, notes: str | None = None) -> SourceTrustMarker:
        return SourceTrustMarker(
            tracked_title=self.title,
            status=VerifiedSourceStatus.needs_review,
            verification_source_url=self.url,
            notes=notes or f"{source_tier_for_ref(self)}. {self.notes}",
        )


S1_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 1001R.1L w/ Ch-2 Marine Corps Reserve Administrative Management Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900627/mco-1001r1l-w-ch-2/index.html",
        publisher="United States Marine Corps",
        notes="Reserve participation, continuity, and administrative reality baseline.",
    ),
    SourceRef(
        title="MCO 1610.7B Performance Evaluation System",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1513503/mco-16107b/",
        publisher="United States Marine Corps",
        notes="FitRep and PES suspense discipline reference.",
    ),
    SourceRef(
        title="MCO 5216.20B Marine Corps Supplement to the Department of the Navy Correspondence Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2869007/mco-521620b/",
        publisher="United States Marine Corps",
        notes="Official correspondence and routing format reference.",
    ),
    SourceRef(
        title="Travel Explorer Training",
        url="https://www.travel.dod.mil/Training/Travel-Explorer/",
        publisher="Department of Defense",
        notes="Official DTS training and continuity aid.",
    ),
    SourceRef(
        title="Government Travel Charge Card Program",
        url="https://www.travel.dod.mil/Programs/Government-Travel-Charge-Card/",
        publisher="Department of Defense",
        notes="Official GTCC program and training reference.",
    ),
)

S2_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCDP 2 Intelligence",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899844/mcdp-2/",
        publisher="United States Marine Corps",
        notes="Doctrine for framing intelligence as decision support rather than trivia collection.",
    ),
    SourceRef(
        title="MCTP 3-30A Command and Staff Actions",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/",
        publisher="United States Marine Corps",
        notes="Useful for how staff estimates should feed commander decisions and staff action.",
    ),
    SourceRef(
        title="MCRP 2-10B.1 Intelligence Preparation of the Battlespace",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899779/mcrp-2-10b1/",
        publisher="United States Marine Corps",
        notes="Reference for structured problem framing, assumptions, and information gaps.",
    ),
    SourceRef(
        title="CIA World Factbook",
        url="https://www.cia.gov/the-world-factbook/",
        publisher="Central Intelligence Agency",
        notes=(
            "Useful public baseline source for country context, demographics, geography, "
            "economy, and infrastructure."
        ),
    ),
    SourceRef(
        title="USGS The National Map",
        url="https://www.usgs.gov/the-national-map",
        publisher="United States Geological Survey",
        notes=(
            "Authoritative public terrain, elevation, hydrography, and topographic-map source for location-based "
            "planning context."
        ),
    ),
)

OSINT_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="CIA World Factbook",
        url="https://www.cia.gov/the-world-factbook/",
        publisher="Central Intelligence Agency",
        notes="Use as a baseline public country-reference source before layering on current reporting.",
    ),
    SourceRef(
        title="USGS The National Map",
        url="https://www.usgs.gov/the-national-map",
        publisher="United States Geological Survey",
        notes="Use as a first-line public source for terrain, elevation, hydrography, and topographic-map context.",
    ),
    SourceRef(
        title="USGS topoView",
        url="https://ngmdb.usgs.gov/topoview/",
        publisher="United States Geological Survey",
        notes="Use to pull historical and current public USGS topographic maps for specific areas.",
    ),
    SourceRef(
        title="MCDP 2 Intelligence",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899844/mcdp-2/",
        publisher="United States Marine Corps",
        notes="Doctrine for disciplined assessment, caveats, and commander decision support.",
    ),
    SourceRef(
        title="MCTP 3-30A Command and Staff Actions",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/",
        publisher="United States Marine Corps",
        notes="Staff-action reference for turning sourced information into usable command support.",
    ),
)

S3_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCDP 5 Planning",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899841/mcdp-5/",
        publisher="United States Marine Corps",
        notes="Planning mindset, learning under uncertainty, and commander decision-making discipline.",
    ),
    SourceRef(
        title="MCWP 5-10 Marine Corps Planning Process",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900553/mcwp-5-10/",
        publisher="United States Marine Corps",
        notes="Concrete MCPP rhythm, R2P2 conditions, staff products, and commander decision support.",
    ),
    SourceRef(
        title="MCTP 3-30A Command and Staff Actions",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/",
        publisher="United States Marine Corps",
        notes="Command-post rhythm, staff-action flow, and planning support to decisions.",
    ),
    SourceRef(
        title="MCO 1553.3C Unit Training Management",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899431/mco-15533c/",
        publisher="United States Marine Corps",
        notes="Core training design, assessment, and event discipline reference.",
    ),
    SourceRef(
        title="MCO 1500.55 Military Thinking and Decision Making Exercises",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/898778/mco-150055/",
        publisher="United States Marine Corps",
        notes="Formal grounding for TDGs, decision games, wargaming, and mental rehearsal under stress.",
    ),
    SourceRef(
        title="NAVMC 3500.18D Common Skills Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2158067/navmc-350018d/",
        publisher="United States Marine Corps",
        notes="Common-skills standard reference for training design and evaluation.",
    ),
    SourceRef(
        title="Expeditionary Warfare School Resident Curriculum",
        url="https://www.usmcu.edu/Colleges-and-Schools/Expeditionary-Warfare-School/Resident/Curriculum/",
        publisher="Marine Corps University",
        notes="Public PME curriculum reference for staff-planning maturity and professional development.",
    ),
)

S4_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCDP 4 Logistics",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899840/mcdp-4/",
        publisher="United States Marine Corps",
        notes="Logistics mindset and support philosophy.",
    ),
    SourceRef(
        title="MCTP 3-40B Tactical Logistics",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899787/mctp-3-40b/",
        publisher="United States Marine Corps",
        notes="Practical logistics planning and support relationships.",
    ),
    SourceRef(
        title="MCTP 3-40F Distribution and Transportation Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899565/mctp-3-40f/",
        publisher="United States Marine Corps",
        notes="Movement and transportation planning reference.",
    ),
    SourceRef(
        title="MCO 3502.8A Marine Corps Logistics Tactics, Training, and Education Program",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2221611/mco-35028a/",
        publisher="United States Marine Corps",
        notes="Logistics training expectations and professional development baseline.",
    ),
)

S6_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCDP 6 Command and Control",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899771/mcdp-6/",
        publisher="United States Marine Corps",
        notes="Doctrine for command-and-control design and disciplined information flow.",
    ),
    SourceRef(
        title="MCTP 3-30A Command and Staff Actions",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/",
        publisher="United States Marine Corps",
        notes="Useful for staff-action rhythm and information flow inside command posts and planning cycles.",
    ),
    SourceRef(
        title="MCTP 3-30B Information Management",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899781/mctp-3-30b/",
        publisher="United States Marine Corps",
        notes="Information-management discipline and reporting flow reference.",
    ),
    SourceRef(
        title="NAVMC 3500.56C Communications Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Tag/21778/communications/",
        publisher="United States Marine Corps",
        notes="Communications training standards and readiness framing.",
    ),
)

MEDICAL_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCTP 3-40A Health Service Support",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899786/mctp-3-40a/",
        publisher="United States Marine Corps",
        notes="Health-service-support planning and coordination reference.",
    ),
    SourceRef(
        title="Deployed Medicine",
        url="https://deployedmedicine.com/",
        publisher="Defense Health Agency / Joint Trauma System",
        notes="Official public portal for TCCC education and training support.",
    ),
    SourceRef(
        title="Joint Trauma System",
        url="https://jts.health.mil/",
        publisher="Defense Health Agency",
        notes="Authoritative public trauma-system and TCCC-related guidance hub.",
    ),
)

G9_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="NAVMC 3500.124A w/Ch-1 Information Maneuver Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1630860/navmc-3500124a-wch-1/",
        publisher="United States Marine Corps",
        notes=(
            "Current public T&R source for common Civil Affairs/Civil-Military Operations events "
            "and MOS 0530/0532 individual events."
        ),
    ),
    SourceRef(
        title="MCTP 3-32D Civil Affairs Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1898548/mctp-3-32d/",
        publisher="United States Marine Corps",
        notes="Civil affairs and civil-information planning reference.",
    ),
    SourceRef(
        title="MCWP 3-33.1 Marine Air-Ground Task Force Civil-Military Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899782/mcwp-3-331/",
        publisher="United States Marine Corps",
        notes="Civil-military integration and external coordination reference.",
    ),
)

SEL_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 5060.20 Marine Corps Drill and Ceremonies Manual",
        url="https://www.marines.mil/Portals/1/Publications/MCO%205060.20_Enclosure%201_signed_EDD.pdf?ver=2019-06-05-105622-833",
        publisher="United States Marine Corps",
        notes="Primary drill, ceremonies, and military-ceremonial procedures reference.",
    ),
    SourceRef(
        title="Marine Corps Manual w/ CH 1-3",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/898634/marine-corps-manual-wch-1-3/",
        publisher="United States Marine Corps",
        notes="Marine customs, leadership expectations, and institutional standards reference.",
    ),
    SourceRef(
        title="NAVMC 3500.18D Common Skills Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2158067/navmc-350018d/",
        publisher="United States Marine Corps",
        notes="Contains common-skills standards including customs, courtesies, and honors.",
    ),
    SourceRef(
        title="MCO 1020.34H Marine Corps Uniform Regulations",
        url="https://www.marines.mil/portals/1/Publications/MCO%201020.34H%20v2.pdf?ver=20",
        publisher="United States Marine Corps",
        notes="Uniform and appearance standards reference for ceremonies and formal events.",
    ),
    SourceRef(
        title="MCO 5216.20B Marine Corps Supplement to the Department of the Navy Correspondence Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2795618/mco-521620b-wadmin-ch-4/",
        publisher="United States Marine Corps",
        notes="Correspondence and protocol-adjacent routing reference for formal packages.",
    ),
)

LEADERSHIP_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCDP 1 Warfighting",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899837/mcdp-1/",
        publisher="United States Marine Corps",
        notes="Baseline warfighting philosophy and decision-making mindset reference.",
    ),
    SourceRef(
        title="MCRP 6-11D Sustaining the Transformation",
        url="https://www.marines.mil/Portals/1/MCRP%206-11D.pdf",
        publisher="United States Marine Corps",
        notes="Leadership, standards, mentorship, and Marine development reference.",
    ),
    SourceRef(
        title="Expeditionary Warfare School Mission and Curriculum",
        url="https://www.usmcu.edu/EWS/",
        publisher="Marine Corps University",
        notes="Public PME reference for the level of planning maturity expected from company-grade officers.",
    ),
    SourceRef(
        title="Update to the Commandant's Professional Reading List for Fiscal Year 26",
        url="https://www.marines.mil/News/Messages/Messages-Display/Article/4351724/update-to-the-commandants-professional-reading-list-for-fiscal-year-26/",
        publisher="United States Marine Corps",
        notes="Current official professional reading program reference for leadership and historical study.",
    ),
)

INSTALLATION_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="Installation Access Control Policy",
        url="https://www.marines.mil/News/Messages/Messages-Display/Article/889956/installation-access-control-policy/",
        publisher="United States Marine Corps",
        notes="High-level Marine Corps installation-access framing and sponsorship expectations.",
    ),
    SourceRef(
        title="MCRD Parris Island Base Access Policies",
        url="https://www.mcrdpi.marines.mil/Visitors/Base-Access/",
        publisher="United States Marine Corps",
        notes="Current public example of Marine Corps visitor access, REAL ID, sponsorship, and visitor restrictions.",
    ),
    SourceRef(
        title="MCAS New River Visitor Access",
        url="https://www.newriver.marines.mil/Visitor-Access/",
        publisher="United States Marine Corps",
        notes="Current public example of visitor-control, DBIDS, IARA, and local access-process reality.",
    ),
)

TRAINING_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 1553.3C Unit Training Management",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899431/mco-15533c/",
        publisher="United States Marine Corps",
        notes="Core event design, evaluation, and training-management reference.",
    ),
    SourceRef(
        title="NAVMC 3500.18D Common Skills Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2158067/navmc-350018d/",
        publisher="United States Marine Corps",
        notes="Training-standard and common-skills baseline for reserve events.",
    ),
    SourceRef(
        title="NAVMC 3500.124A w/Ch-1 Information Maneuver Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1630860/navmc-3500124a-wch-1/",
        publisher="United States Marine Corps",
        notes=(
            "Civil Affairs/Civil-Military Operations T&R standard source for G-9, civil reconnaissance, "
            "CMOC, and MOS 0530/0532 training packages."
        ),
    ),
    SourceRef(
        title="MCWP 5-10 Marine Corps Planning Process",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900553/mcwp-5-10/",
        publisher="United States Marine Corps",
        notes="Planning-process and staff-rhythm reference for training packages.",
    ),
)

OPORD_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCDP 5 Planning",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899841/mcdp-5/",
        publisher="United States Marine Corps",
        notes="Planning philosophy and commander decision support reference.",
    ),
    SourceRef(
        title="MCWP 5-10 Marine Corps Planning Process",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900553/mcwp-5-10/",
        publisher="United States Marine Corps",
        notes="Staff-product and MCPP rhythm reference.",
    ),
    SourceRef(
        title="MCTP 3-30A Command and Staff Actions",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/",
        publisher="United States Marine Corps",
        notes="Command-and-staff action reference for order production and follow-through.",
    ),
)

UNIFORM_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 1020.34H Marine Corps Uniform Regulations",
        url="https://www.marines.mil/portals/1/Publications/MCO%201020.34H%20v2.pdf?ver=20",
        publisher="United States Marine Corps",
        notes="Primary public uniform standards reference.",
    ),
    SourceRef(
        title="Marine Corps Uniform Board FAQ",
        url="https://www.hqmc.marines.mil/Agencies/Marine-Corps-Uniform-Board/Frequently-Asked-Questions/",
        publisher="United States Marine Corps",
        notes="Useful public clarification source for ambiguous wear and policy questions.",
    ),
)

DRILL_PREP_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 1001R.1L w/ Ch-2 Marine Corps Reserve Administrative Management Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900627/mco-1001r1l-w-ch-2/index.html",
        publisher="United States Marine Corps",
        notes="Reserve admin and participation reality baseline for drill preparation.",
    ),
    SourceRef(
        title="MCO 1553.3C Unit Training Management",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899431/mco-15533c/",
        publisher="United States Marine Corps",
        notes="Training-preparation and event-discipline reference.",
    ),
    SourceRef(
        title="Travel Explorer Training",
        url="https://www.travel.dod.mil/Training/Travel-Explorer/",
        publisher="Department of Defense",
        notes="Official DTS training and continuity aid for drill-prep reminders.",
    ),
)

MARADMIN_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="Marine Corps Publications Electronic Library (MCPEL)",
        url="https://www.marines.mil/News/Publications/MCPEL/",
        publisher="United States Marine Corps",
        notes="Primary public index for current doctrine, orders, and publication families.",
    ),
    SourceRef(
        title="MARADMIN Messages",
        url="https://www.marines.mil/News/Messages/MARADMINS/",
        publisher="United States Marine Corps",
        notes="Primary public index for current MARADMIN messages and message freshness checks.",
    ),
)

ORM_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 5100.29C Marine Corps Safety Management System",
        url="https://www.marines.mil/News/Publications/MCPEL/Search/5100/",
        publisher="United States Marine Corps",
        notes="Primary public safety-management and ORM reference family.",
    ),
    SourceRef(
        title="Marine Corps Safety Management System Resources",
        url="https://www.safety.marines.mil/Resources/Marine-Corps-Safety-Management-System/",
        publisher="United States Marine Corps",
        notes="Public safety resource hub for ORM framing, supervision, and command-risk acceptance.",
    ),
    SourceRef(
        title="MCO 1553.3C Unit Training Management",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899431/mco-15533c/",
        publisher="United States Marine Corps",
        notes="Useful for tying ORM to training design and assessment discipline.",
    ),
)

MAP_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="USGS The National Map",
        url="https://www.usgs.gov/the-national-map",
        publisher="United States Geological Survey",
        notes=(
            "Primary public source for elevation, hydrography, structures, transport layers, "
            "and topographic context."
        ),
    ),
    SourceRef(
        title="USGS topoView",
        url="https://ngmdb.usgs.gov/topoview/",
        publisher="United States Geological Survey",
        notes="Public source for downloadable historical and current topographic maps by area.",
    ),
    SourceRef(
        title="USGS National Map Downloader",
        url="https://apps.nationalmap.gov/downloader/",
        publisher="United States Geological Survey",
        notes="Public source for specific map products and geospatial layers by location and product type.",
    ),
    SourceRef(
        title="USGS EarthExplorer",
        url="https://earthexplorer.usgs.gov/",
        publisher="United States Geological Survey",
        notes="Public discovery portal for imagery and geospatial products when terrain or land-use context matters.",
    ),
)


def citation_titles(refs: tuple[SourceRef, ...]) -> list[str]:
    return [ref.title for ref in refs]


def structured_citations(refs: tuple[SourceRef, ...]) -> list[StructuredCitation]:
    return [ref.citation() for ref in refs]


def source_trust_markers(
    refs: tuple[SourceRef, ...], notes_prefix: str = "Verify current public source and local applicability."
) -> list[SourceTrustMarker]:
    return [ref.trust(f"{notes_prefix} {ref.notes}") for ref in refs]


def source_tier_for_ref(ref: SourceRef) -> str:
    title = ref.title.lower()
    publisher = ref.publisher.lower()
    if "cia world factbook" in title:
        return "Tier: baseline reference"
    if (
        "united states marine corps" in publisher
        or "department of defense" in publisher
        or "united states geological survey" in publisher
    ):
        return "Tier: official current source"
    return "Tier: reference source"
