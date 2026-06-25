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

MOS_0102_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="NAVMC 3500.3E Manpower and Administration Training and Readiness Manual",
        url="https://www.marines.mil/Portals/1/Publications/NAVMC%203500.3E%20Manpower%20and%20Administrtion%20T-R%20Manual.pdf?ver=2020-04-28-100336-353",
        publisher="United States Marine Corps",
        notes=(
            "Current public manpower and administration T&R baseline, including 0102 billet descriptions, "
            "core capabilities, and S-1/adjutant training expectations."
        ),
    ),
    SourceRef(
        title="NAVMC 1200.1E Military Occupational Specialties Manual",
        url="https://www.marines.mil/Portals/1/Publications/MOS%20Manual%20NAVMC%201200.1E.pdf?ver=2019-04-23-135930-100",
        publisher="United States Marine Corps",
        notes="Official MOS manual describing 0102 Manpower Officer duties, progression, and course requirements.",
    ),
    SourceRef(
        title="MCO 5216.20B Marine Corps Supplement to the Department of the Navy Correspondence Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2869007/mco-521620b/",
        publisher="United States Marine Corps",
        notes="Official correspondence and routing discipline reference for adjutant work.",
    ),
    SourceRef(
        title="MCO 1001R.1L w/ Ch-2 Marine Corps Reserve Administrative Management Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900627/mco-1001r1l-w-ch-2/index.html",
        publisher="United States Marine Corps",
        notes="Reserve administration, participation, and continuity baseline for SMCR manpower/admin work.",
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
        title="MCWP 2-10 Marine Corps Intelligence",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899774/mcwp-2-10/",
        publisher="United States Marine Corps",
        notes=(
            "Core S-2/G-2 warfighting pub covering IPB methodology, collection management, "
            "all-source fusion, intelligence estimate, and INTSUM production."
        ),
    ),
    SourceRef(
        title="MCTP 2-10B Intelligence Preparation of the Battlespace",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899553/mctp-2-10b/",
        publisher="United States Marine Corps",
        notes=(
            "Four-step IPB methodology (define, describe, evaluate, determine) with "
            "practical worksheets, templates, and echelon-appropriate application guidance."
        ),
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

MOS_0202_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="PMOS 0202 Intelligence Officer",
        url="https://www.intelligence.marines.mil/Careers/PMOS/0202/",
        publisher="United States Marine Corps",
        notes=(
            "Official 0202 career page describing advisor role, prerequisites, and Tactical Intelligence Officer "
            "Course requirement for active and reserve officers."
        ),
    ),
    SourceRef(
        title="NAVMC 3500.100B Intelligence Training and Readiness Manual",
        url="https://www.marines.mil/portals/1/Publications/NAVMC%203500.100B.pdf",
        publisher="United States Marine Corps",
        notes="Official intelligence T&R baseline for MAGTF intelligence officer training standards.",
    ),
    SourceRef(
        title="MCDP 2 Intelligence",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899844/mcdp-2/",
        publisher="United States Marine Corps",
        notes="Doctrine for intelligence as commander decision support.",
    ),
    SourceRef(
        title="MCTP 3-30A Command and Staff Actions",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/",
        publisher="United States Marine Corps",
        notes="Staff-action rhythm for turning intelligence into usable command support.",
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
    SourceRef(
        title="MCRP 2-10A.3 Open-Source Intelligence",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/3631282/mcrp-2-10a3/",
        publisher="United States Marine Corps",
        notes=(
            "2024 Marine OSINT pub: five-step methodology (frame, acquire PAI/CAI, evaluate, "
            "exploit, disseminate/fuse), source reliability, and analytic standards."
        ),
    ),
    SourceRef(
        title="Copernicus Browser (Sentinel Hub)",
        url="https://browser.dataspace.copernicus.eu/",
        publisher="European Space Agency / European Commission",
        notes=(
            "Free Sentinel-2 multispectral imagery (10 m) with near-daily revisit. "
            "Useful for change detection, vegetation analysis, and terrain context."
        ),
    ),
    SourceRef(
        title="NASA Worldview",
        url="https://worldview.earthdata.nasa.gov/",
        publisher="National Aeronautics and Space Administration",
        notes=(
            "Near-real-time global imagery layers (MODIS, VIIRS) for weather, fires, "
            "thermal anomalies, and large-area environmental monitoring."
        ),
    ),
    SourceRef(
        title="NGA Tearline",
        url="https://www.tearline.mil/",
        publisher="National Geospatial-Intelligence Agency",
        notes=(
            "Unclassified geospatial intelligence assessments with GEOINT tradecraft "
            "useful for OSINT methodology modeling."
        ),
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
        notes=(
            "Public PME curriculum reference for company-grade staff-planning maturity, MAGTF employment, "
            "planning exercises, and MOS credibility."
        ),
    ),
    SourceRef(
        title="Command and Staff College",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/",
        publisher="Marine Corps University",
        notes=(
            "Public intermediate-level PME reference for critical thinking, joint and external-context awareness, "
            "complex problem solving, and capstone staff planning."
        ),
    ),
    SourceRef(
        title="Command and Staff College Preparatory Knowledge Program",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/Preparatory-Knowledge-Program/",
        publisher="Marine Corps University",
        notes=(
            "Useful for shaping mission-analysis conduct, planning refresh, critical thinking, critical reading, "
            "writing, and research discipline."
        ),
    ),
)

MOS_0511_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="NAVMC 3500.108B Marine Air-Ground Task Force Planner Training and Readiness Manual",
        url="https://www.marines.mil/Portals/1/Publications/NAVMC%203500.108B%20Marine%20Air-Ground%20Task%20Force%20Planner%20T-R%20Manual.pdf?ver=2020-04-16-101300-923",
        publisher="United States Marine Corps",
        notes="Current public MAGTF planner T&R baseline, including 0511 individual-event standards.",
    ),
    SourceRef(
        title="MCDP 5 Planning",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899841/mcdp-5/",
        publisher="United States Marine Corps",
        notes="Planning mindset, uncertainty management, and decision-support doctrine.",
    ),
    SourceRef(
        title="MCWP 5-10 Marine Corps Planning Process",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900553/mcwp-5-10/",
        publisher="United States Marine Corps",
        notes="Concrete MCPP rhythm, planning support, and staff-product discipline reference.",
    ),
    SourceRef(
        title="Command and Staff College Preparatory Knowledge Program",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/Preparatory-Knowledge-Program/",
        publisher="Marine Corps University",
        notes="Useful public reference for mission-analysis, research, writing, and planning discipline.",
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
    SourceRef(
        title="MCWP 4-1 Logistics Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899853/mcwp-4-1/",
        publisher="United States Marine Corps",
        notes=(
            "Keystone logistics operations doctrine covering the six logistics functions "
            "(supply, maintenance, transportation, general engineering, health services, services), "
            "CSS estimate format, and logistics synchronization within the MAGTF."
        ),
    ),
)

MOS_0402_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="NAVMC 3500.27D Logistics Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1838898/navmc-350027d/",
        publisher="United States Marine Corps",
        notes="Current public logistics T&R baseline, including 0402 individual-event training expectations.",
    ),
    SourceRef(
        title="NAVMC 1200.1E Military Occupational Specialties Manual",
        url="https://www.marines.mil/Portals/1/Publications/MOS%20Manual%20NAVMC%201200.1E.pdf?ver=2019-04-23-135930-100",
        publisher="United States Marine Corps",
        notes="Official MOS manual describing 0402 Logistics Officer duties and progression.",
    ),
    SourceRef(
        title="MCDP 4 Logistics",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899840/mcdp-4/",
        publisher="United States Marine Corps",
        notes="Logistics philosophy and support mindset reference for 0402 work.",
    ),
    SourceRef(
        title="Logistics Operations School",
        url="https://www.mccsss.marines.mil/Schools/Logistics-Operations/",
        publisher="United States Marine Corps",
        notes="Official schoolhouse reference for resident logistics training supporting 0402 and related fields.",
    ),
)

MOS_0430_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="NAVMC 3500.27D Logistics Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1838898/navmc-350027d/",
        publisher="United States Marine Corps",
        notes="Current public logistics T&R baseline, including 0430 mobility officer individual events.",
    ),
    SourceRef(
        title="NAVMC 1200.1E Military Occupational Specialties Manual",
        url="https://www.marines.mil/Portals/1/Publications/MOS%20Manual%20NAVMC%201200.1E.pdf?ver=2019-04-23-135930-100",
        publisher="United States Marine Corps",
        notes="Official MOS manual describing 0430 Mobility Officer duties, prerequisites, and training path.",
    ),
    SourceRef(
        title="Strategic Mobility Mission",
        url="https://www.iandl.marines.mil/Divisions/Logistics-Division-LP/Logistics-Plans-and-Operations-Branch-LPO/LPO-3-Mission/",
        publisher="United States Marine Corps",
        notes="Official I&L mission page framing Marine Corps strategic mobility, FDP&E, and embarkation oversight.",
    ),
    SourceRef(
        title="MCTP 3-40F Distribution and Transportation Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899565/mctp-3-40f/",
        publisher="United States Marine Corps",
        notes="Distribution, transportation, and movement-planning reference for mobility officers.",
    ),
)

MOS_3002_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="NAVMC 3500.64D Supply Chain Management Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/3259614/navmc-350064d/",
        publisher="United States Marine Corps",
        notes="Current public supply-chain-management T&R baseline for 3002 training standards.",
    ),
    SourceRef(
        title="NAVMC 1200.1E Military Occupational Specialties Manual",
        url="https://www.marines.mil/Portals/1/Publications/MOS%20Manual%20NAVMC%201200.1E.pdf?ver=2019-04-23-135930-100",
        publisher="United States Marine Corps",
        notes="Official MOS manual describing 3002 Ground Supply Officer duties and course requirement.",
    ),
    SourceRef(
        title="MCDP 4 Logistics",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899840/mcdp-4/",
        publisher="United States Marine Corps",
        notes="Logistics philosophy baseline for supply support, accountability, and sustainment judgment.",
    ),
    SourceRef(
        title="MCO 3502.8A Marine Corps Logistics Tactics, Training, and Education Program",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2221611/mco-35028a/",
        publisher="United States Marine Corps",
        notes="Logistics training expectations and professional-development baseline relevant to 3002 support lanes.",
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
    SourceRef(
        title="MCWP 3-31 Marine Air-Ground Task Force C4",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899782/mcwp-3-31/",
        publisher="United States Marine Corps",
        notes=(
            "MAGTF C4I architecture — enterprise, tactical, and transport layers; "
            "Annex K structure (6 appendices), PACE planning, and EMCON guidance."
        ),
    ),
)

MOS_4402_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 5800.16 w/Ch 1-7 w/Vol 1-17 Legal Support and Administration Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1447370/mco-580016-wch-1-7-wvol-1-17/",
        publisher="United States Marine Corps",
        notes="Current public LEGADMINMAN/LSAM hub for Marine Corps legal support and unit legal administration.",
    ),
    SourceRef(
        title="Joint Service Committee Sources of Military Law",
        url="https://jsc.defense.gov/Military-Law/Sources-of-Military-Law/",
        publisher="Joint Service Committee on Military Justice",
        notes="Public overview of UCMJ, Manual for Courts-Martial, and military-justice source relationships.",
    ),
    SourceRef(
        title="MCO 5800.16 Volume 5 Marine Corps Legal Assistance Program",
        url="https://www.marines.mil/Portals/1/Publications/MCO%205800.16%20Volume%205.pdf?ver=2018-02-21-144314-933",
        publisher="United States Marine Corps",
        notes="Marine Corps legal assistance policy, procedures, and responsibilities reference.",
    ),
)

MOS_7200_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="NAVMC 3500.14C Aviation Training and Readiness Program Manual",
        url="https://www.marines.mil/Portals/1/Publications/NAVMC_3500.14C_2.pdf",
        publisher="United States Marine Corps",
        notes="Public aviation T&R program reference for training standards, readiness events, and program structure.",
    ),
    SourceRef(
        title="Marine Aviation Weapons and Tactics Squadron One",
        url="https://www.29palms.marines.mil/Units/MAWTS-1/",
        publisher="United States Marine Corps",
        notes="Official MAWTS-1 public page for aviation training, readiness, weapons, and tactics support.",
    ),
    SourceRef(
        title="MCO 5100.29C Volume 4 Marine Corps Safety Management System",
        url="https://www.marines.mil/Portals/1/Publications/MCO%205100.29C%20Vol.%204%20Change%201.pdf",
        publisher="United States Marine Corps",
        notes="Marine Corps aviation safety management, command safety, and mishap-prevention reference.",
    ),
    SourceRef(
        title="MCWP 3-20 Aviation Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899843/mcwp-3-20/",
        publisher="United States Marine Corps",
        notes=(
            "MAGTF ACE doctrine defining the six functions of Marine aviation, MACCS agencies and roles, "
            "and the MAGTF air tasking cycle."
        ),
    ),
    SourceRef(
        title="MCWP 3-25 Control of Aircraft and Missiles",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899844/mcwp-3-25/",
        publisher="United States Marine Corps",
        notes=(
            "MACCS operations doctrine covering TACC, DASC, MASS, TAOC employment "
            "and command relationships for ACE C2."
        ),
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
    SourceRef(
        title="MCRP 3-03A.2 MAGTF Civil-Military Operations Planning",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899779/mcrp-3-03a2/",
        publisher="United States Marine Corps",
        notes=(
            "Best current Marine planning source for G-9/CMO products across MCPP, "
            "Annex G, CPB, civil estimate, Green Cell, and transition."
        ),
    ),
    SourceRef(
        title="MCRP 3-03A.1 Civil Affairs Tactics, Techniques, and Procedures",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899778/mcrp-3-03a1/",
        publisher="United States Marine Corps",
        notes=(
            "Civil reconnaissance, civil engagement, CIM, MARCIMS, network analysis, "
            "and civil-information methods reference."
        ),
    ),
    SourceRef(
        title="MCWP 8-10 Information",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/3077947/mcwp-8-10/",
        publisher="United States Marine Corps",
        notes=(
            "Generate, preserve, deny, project framework; Annex I and information-staff "
            "responsibilities for CMO integration into the information function."
        ),
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
        title="Command and Staff College",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/",
        publisher="Marine Corps University",
        notes=(
            "Public PME reference for field-grade expectations in leadership, problem solving, staff work, "
            "and joint or external coordination."
        ),
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
    SourceRef(
        title="Marine Forces Reserve (MARFORRES)",
        url="https://www.marforres.marines.mil/",
        publisher="United States Marine Corps",
        notes=(
            "Official MARFORRES public hub for RTC network, I&I support structure, "
            "and reserve force management across 160+ sites."
        ),
    ),
)

PAO_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCDP 8 Information",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/3077947/mcdp-8/",
        publisher="United States Marine Corps",
        notes=(
            "Capstone doctrine for the information warfighting function and the broader role of information in "
            "Marine planning, public posture, and influence."
        ),
    ),
    SourceRef(
        title="USMC Communication Strategy",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/3389350/usmc-communication-strategy/",
        publisher="United States Marine Corps",
        notes=(
            "Service-level communication priorities and enduring guidance for themes, messages, public engagement, "
            "and support to commanders."
        ),
    ),
    SourceRef(
        title="Communication Directorate",
        url="https://www.cd.marines.mil/",
        publisher="United States Marine Corps",
        notes=(
            "Official Marine Corps communication and COMMSTRAT hub describing the mission, posture, and public "
            "information responsibilities of the force."
        ),
    ),
    SourceRef(
        title="MCWP 3-33.3 Marine Corps Public Affairs",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899784/mcwp-3-333/",
        publisher="United States Marine Corps",
        notes=(
            "PA/COMMSTRAT doctrine: media engagement, Annex F structure, community relations, "
            "information environment generate/preserve/deny/project functions."
        ),
    ),
)

FORCE_PROTECTION_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 5530.14A Marine Corps Physical Security Program Manual",
        url="https://www.marines.mil/Portals/1/Publications/MCO%205530_14A.pdf",
        publisher="United States Marine Corps",
        notes=(
            "Primary Marine Corps physical-security and access-control baseline for protecting personnel, "
            "facilities, and installation entry points."
        ),
    ),
    SourceRef(
        title="Release of Marine Corps Order 5530.13 Marine Corps Site Perimeter Access Control",
        url="https://www.marines.mil/News/Messages/Messages-Display/Article/2622028/release-of-marine-corps-order-553013-marine-corps-site-perimeter-access-control/",
        publisher="United States Marine Corps",
        notes=(
            "Official message announcing site perimeter access-control policy and its relationship to the physical "
            "security program."
        ),
    ),
    SourceRef(
        title="HQMC Physical Security",
        url="https://www.ar.marines.mil/Branches/ARS-Security-Programs-and-Information-Management/Physical-Security/",
        publisher="United States Marine Corps",
        notes=(
            "Official public page describing HQMC physical-security responsibilities, access-control requirements, "
            "and force-protection support functions."
        ),
    ),
    *INSTALLATION_REFERENCES,
)

G8_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCO 7300.21B",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900441/mco-730021b/",
        publisher="United States Marine Corps",
        notes=(
            "Primary Marine Corps financial-management order for effective and efficient financial principles, "
            "operations, controls, and stewardship."
        ),
    ),
    SourceRef(
        title="MARFORRES G-8 Comptroller Resources",
        url="https://www.marforres.marines.mil/Staff-Sections/General-Staff/G-8-Comptroller/Resources/",
        publisher="United States Marine Corps",
        notes=(
            "Reserve-focused G-8 mission framing for financial resource management, internal control, audit support, "
            "and decision support for limited resources."
        ),
    ),
    SourceRef(
        title="Marine Corps Logistics Command G-8 Comptroller",
        url="https://www.logcom.marines.mil/Staff-Offices/G-8-Comptroller/",
        publisher="United States Marine Corps",
        notes=(
            "Useful public framing for PPBE, appropriated-fund budgeting, execution oversight, and fiscal "
            "stewardship in support of the force."
        ),
    ),
)

IG_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="Inspector General of the Marine Corps",
        url="https://www.igmc.marines.mil/",
        publisher="United States Marine Corps",
        notes=(
            "Official IGMC mission and public entry point for objective, independent assistance, assessments, "
            "inspections, and investigations."
        ),
    ),
    SourceRef(
        title="MCO 5430.1A W/ADMIN CH-2",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/4062347/mco-54301a-wadmin-ch-2/",
        publisher="United States Marine Corps",
        notes=(
            "Primary Marine Corps Inspector General Program order defining scope, authorities, independence, and "
            "command relationships."
        ),
    ),
    SourceRef(
        title="MCO 5370.8A W/ADMIN CH-1",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1924487/mco-53708a/",
        publisher="United States Marine Corps",
        notes=(
            "Marine Corps Hotline Program order useful for complaint-routing boundaries, fraud/waste/abuse logic, "
            "and IG channel discipline."
        ),
    ),
    SourceRef(
        title="IGMC Functional Area Checklists",
        url="https://www.igmc.marines.mil/Divisions/Inspections-Division/Checklists/",
        publisher="United States Marine Corps",
        notes=(
            "Current inspection checklists and update rhythm for readiness, compliance, and functional-area "
            "inspection preparation."
        ),
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

INFANTRY_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="Training Command Mission",
        url="https://www.trngcmd.marines.mil/Unit-Home/About/",
        publisher="United States Marine Corps",
        notes=(
            "Useful public framing for standards-based MOS skill training, evaluation, and delivery of "
            "combat-capable Marines to the operating forces."
        ),
    ),
    SourceRef(
        title="The Basic School Mission",
        url="https://www.trngcmd.marines.mil/TBS/",
        publisher="United States Marine Corps",
        notes=(
            "Useful officer-development baseline for provisional rifle-platoon leadership, warfighting skills, "
            "and common tactical vocabulary."
        ),
    ),
    SourceRef(
        title="MCWP 3-10 MAGTF Ground Operations",
        url="https://www.marines.mil/Portals/1/Publications/MCWP%203-10.pdf",
        publisher="United States Marine Corps",
        notes="Keystone ground-combat doctrine reference for planning and employing the GCE.",
    ),
    SourceRef(
        title="MCWP 3-01 Offensive and Defensive Tactics",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2362952/mcwp-3-01/",
        publisher="United States Marine Corps",
        notes="Foundational tactics reference for offensive and defensive actions.",
    ),
    SourceRef(
        title="MCRP 3-10A.2 Infantry Company Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1780135/mcrp-3-10a2/",
        publisher="United States Marine Corps",
        notes="Company-level infantry planning and employment reference.",
    ),
    SourceRef(
        title="MCRP 3-10A.3 Marine Infantry Platoon",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2500719/mcrp-3-10a3/",
        publisher="United States Marine Corps",
        notes="Platoon-level planning and employment reference.",
    ),
    SourceRef(
        title="MCRP 3-10A.4 Marine Rifle Squad",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2472229/mcrp-3-10a4/",
        publisher="United States Marine Corps",
        notes="Rifle-squad employment and basic TTP reference.",
    ),
    SourceRef(
        title="MCTP 12-10B Urban Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/1464473/mctp-12-10b/",
        publisher="United States Marine Corps",
        notes="Urban-operations planning and training reference for commanders, staffs, and Marines.",
    ),
    SourceRef(
        title="School of Infantry-East Combat Instructor School Mission",
        url="https://www.tecom.marines.mil/soieast/Units/CombatInstructorSchool.aspx",
        publisher="United States Marine Corps",
        notes=(
            "Useful source for the teach-mentor-lead model behind entry-level and advanced infantry training."
        ),
    ),
    SourceRef(
        title="School of Infantry-East Infantry Training Battalion MOS Description",
        url="https://www.trngcmd.marines.mil/Units/School-of-Infantry-East/Units/Infantry-Training-Battalion/MOS-Description/",
        publisher="United States Marine Corps",
        notes=(
            "Useful public description of SOI infantry training as field craft and MOS-task evaluation producing "
            "basically qualified infantry Marines for the operating forces."
        ),
    ),
    SourceRef(
        title="NAVMC 3500.44D Infantry Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2187958/navmc-350044d/",
        publisher="United States Marine Corps",
        notes="Infantry training standards, regulations, and readiness baseline.",
    ),
    SourceRef(
        title="NAVMC 3500.18D Common Skills Training and Readiness Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2158067/navmc-350018d/",
        publisher="United States Marine Corps",
        notes="Common-skills baseline for all Marines supporting event design and evaluation.",
    ),
)

STAFF_PROCESS_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="Command and Staff College",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/",
        publisher="Marine Corps University",
        notes=(
            "Intermediate-level PME reference for critical thinking, problem solving, staff work, "
            "joint context, and capstone planning."
        ),
    ),
    SourceRef(
        title="Command and Staff College Preparatory Knowledge Program",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/Preparatory-Knowledge-Program/",
        publisher="Marine Corps University",
        notes=(
            "Useful for planning refresh, mission analysis, critical thinking, critical reading, "
            "writing, and research discipline."
        ),
    ),
    SourceRef(
        title="MCTP 3-30A Command and Staff Actions",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/",
        publisher="United States Marine Corps",
        notes=(
            "Staff-action and command-post rhythm reference for running estimates, "
            "battle rhythm, and follow-through."
        ),
    ),
    SourceRef(
        title="MCWP 5-10 Marine Corps Planning Process",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900553/mcwp-5-10/",
        publisher="United States Marine Corps",
        notes="Planning-process reference for OPT conduct, mission analysis, COA work, and transition discipline.",
    ),
    SourceRef(
        title="MCDP 5 Planning",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899841/mcdp-5/",
        publisher="United States Marine Corps",
        notes="Planning philosophy for learning, uncertainty, and decision support rather than product fetishism.",
    ),
)

WRITING_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="Command and Staff College Preparatory Knowledge Program",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/Preparatory-Knowledge-Program/",
        publisher="Marine Corps University",
        notes=(
            "Public PME signal that critical reading, writing, and research discipline are expected inputs to "
            "command-and-staff performance."
        ),
    ),
    SourceRef(
        title="MCO 5216.20B Marine Corps Supplement to the Department of the Navy Correspondence Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2869007/mco-521620b/",
        publisher="United States Marine Corps",
        notes="Formal correspondence, structure, and routing reference for official-style products.",
    ),
    SourceRef(
        title="Command and Staff College",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/",
        publisher="Marine Corps University",
        notes=(
            "Useful PME reference for the level of briefing, writing, and oral defense "
            "expected of field-grade staff."
        ),
    ),
)

JOINT_FRAME_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="Command and Staff College",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/",
        publisher="Marine Corps University",
        notes=(
            "Public intermediate-level PME reference for Marine, service, joint, interagency, intergovernmental, "
            "and multinational staff work in complex environments."
        ),
    ),
    SourceRef(
        title="Command and Staff College Preparatory Knowledge Program",
        url="https://www.usmcu.edu/Colleges-and-Schools/Command-and-Staff-College/Preparatory-Knowledge-Program/",
        publisher="Marine Corps University",
        notes=(
            "Useful for joint and Marine Corps operations framing, planning refresh, and external-context awareness."
        ),
    ),
    SourceRef(
        title="MCTP 3-30A Command and Staff Actions",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899747/mctp-3-30a/",
        publisher="United States Marine Corps",
        notes="Staff-action reference for coordination, command relationships, and disciplined follow-through.",
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

STAFF_PRODUCT_REFERENCES: tuple[SourceRef, ...] = (
    *OPORD_REFERENCES,
    SourceRef(
        title="CJCSM 3150.05F Joint Reporting System Situation Monitoring Manual",
        url="https://www.jcs.mil/Portals/36/Documents/Library/Manuals/CJCSM%203150.05F.pdf",
        publisher="Joint Chiefs of Staff",
        notes="Primary public joint reference for SITREP and operational report framing.",
    ),
    SourceRef(
        title="MCO 1553.3C Unit Training Management",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899431/mco-15533c/",
        publisher="United States Marine Corps",
        notes="Training design, evaluation, AAR, and standards-based event discipline reference.",
    ),
)

CORRESPONDENCE_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
        url="https://www.secnav.navy.mil/doni/SECNAV%20Manuals1/5216.5%20%20CH-1.pdf",
        publisher="Department of the Navy",
        notes="Department-level naval correspondence format and routing reference.",
    ),
    SourceRef(
        title="MCO 5216.20B Marine Corps Supplement to the Department of the Navy Correspondence Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2795618/mco-521620b-wadmin-ch-4/",
        publisher="United States Marine Corps",
        notes="Marine Corps supplement for official correspondence, endorsements, and routing discipline.",
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
        notes=(
            "Reserve admin and participation reality baseline. Key facts: "
            "48 IDT + 14 days AT minimum, 7 Mar 2025 revision."
        ),
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
    SourceRef(
        title="Marine Online (MOL)",
        url="https://mol.tfs.usmc.mil/",
        publisher="United States Marine Corps",
        notes=(
            "Self-service portal for Marine Corps personnel: LES, OMPF, training records, "
            "duty status, and leave/liberty management."
        ),
    ),
    SourceRef(
        title="Marine Corps Total Force System (MCTFS)",
        url="https://www.manpower.usmc.mil/webcenter/portal/MCTFS",
        publisher="United States Marine Corps",
        notes=(
            "Authoritative system of record for personnel status. "
            "Unit diaries drive all status changes (gains, losses, promotions, duty status)."
        ),
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

LEGAL_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="Military Justice References",
        url="https://www.sja.marines.mil/Branches/Military-Justice-Branch/Military-Justice-References/",
        publisher="United States Marine Corps",
        notes=(
            "Official Marine Corps SJA public reference hub for military justice, NJP, courts-martial, "
            "post-trial processing, and related command legal resources."
        ),
    ),
    SourceRef(
        title="Manual for Courts-Martial (2024 ed.)",
        url="https://jsc.defense.gov/Portals/99/2024%20MCM%20files/MCM%20%282024%20ed%29%20%282024_01_02%29%20%28adjusted%20bookmarks%29.pdf",
        publisher="Joint Service Committee on Military Justice",
        notes=(
            "Primary current source for courts-martial procedure and Article 15 nonjudicial punishment under Part V."
        ),
    ),
    SourceRef(
        title="Joint Service Committee Sources of Military Law",
        url="https://jsc.defense.gov/Military-Law/Sources-of-Military-Law/",
        publisher="Joint Service Committee on Military Justice",
        notes=(
            "Useful public source map tying the UCMJ, presidential authority, and the MCM together."
        ),
    ),
    SourceRef(
        title="JAGINST 5800.7G CH-2 - JAGMAN 2023",
        url="https://stjececmsdusgva001.blob.core.usgovcloudapi.net/public/documents/Encl_JAGINST_5800.7G_CH-2_Under_Revision.pdf",
        publisher="Department of the Navy",
        notes=(
            "Department of the Navy regulation implementing and supplementing the MCM, including NJP, "
            "Reserve-component jurisdiction points, appeals, records, and courts-martial authorities."
        ),
    ),
    SourceRef(
        title="MCO 5800.16-V14 Enlisted Nonjudicial Punishment Matters and Preparation of the Unit Punishment Book",
        url="https://www.marines.mil/Portals/1/Publications/MCO%205800.16%20Vol14.pdf?ver=GiRsIU5b8B1FOhzJlbyB2Q%3D%3D",
        publisher="United States Marine Corps",
        notes=(
            "Marine Corps legal-support manual volume for enlisted NJP matters, advice to accused, UPB preparation, "
            "appeals, judge advocate review, and Reserve-specific NJP concerns."
        ),
    ),
    SourceRef(
        title="MCO 5800.16-V16 Military Justice",
        url="https://www.marines.mil/Portals/1/Publications/MCO%205800.16%20Vol%2016.pdf?ver=Kw6Bv7bjXXFICy5ujnlk1Q%3D%3D",
        publisher="United States Marine Corps",
        notes=(
            "Marine Corps legal-support manual volume covering military justice organization, pretrial matters, "
            "Article 32, courts-martial, discovery, and post-trial processing."
        ),
    ),
    SourceRef(
        title="MCWP 11-10 Marine Corps Legal Support",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899768/mcwp-11-10/",
        publisher="United States Marine Corps",
        notes=(
            "Six functional areas of legal support: military justice, international/operational law, "
            "administrative law, civil law, legal assistance, legal administration. "
            "Reserve-specific UCMJ jurisdiction and mobilization legal readiness."
        ),
    ),
    SourceRef(
        title="MCO P1900.16 Separation and Retirement Manual",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899428/mco-p190016/",
        publisher="United States Marine Corps",
        notes=(
            "Enlisted separations including unsatisfactory participation, administrative discharge boards, "
            "and reserve-component involuntary separation procedures."
        ),
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


ARTILLERY_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCWP 3-16 Fire Support Coordination in the Ground Combat Element",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899837/mcwp-3-16/",
        publisher="United States Marine Corps",
        notes=(
            "Core doctrine for fire support coordination, the FSCC, and fire support planning "
            "in the context of MAGTF ground operations."
        ),
    ),
    SourceRef(
        title="MCDP 3 Expeditionary Operations",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899543/mcdp-3/",
        publisher="United States Marine Corps",
        notes="Frames fire support and fires integration within the broader expeditionary context.",
    ),
    SourceRef(
        title="MCWP 3-31 MAGTF Fires",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899845/mcwp-3-31/",
        publisher="United States Marine Corps",
        notes="MAGTF fires doctrine covering artillery, NSFS, and air-delivered fires integration.",
    ),
    SourceRef(
        title="Training Command Mission",
        url="https://www.trngcmd.marines.mil/Unit-Home/About/",
        publisher="United States Marine Corps",
        notes=(
            "Public framing for standards-based MOS skill training, evaluation, and delivery of "
            "combat-capable Marines to the operating forces — applicable to 08xx artillery training."
        ),
    ),
    SourceRef(
        title="Joint Publication 3-09 Joint Fire Support",
        url="https://www.jcs.mil/Portals/36/Documents/Doctrine/pubs/jp3_09.pdf",
        publisher="Department of Defense",
        notes="Joint fires doctrine useful for understanding fire support coordination at echelons above battalion.",
    ),
    SourceRef(
        title="MCRP 3-16.6A Supporting Arms Observer, Spotter, and Controller",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899673/mcrp-3-166a/",
        publisher="United States Marine Corps",
        notes=(
            "Call-for-fire format, observer procedures, adjustment techniques, and fire support "
            "coordination measures reference for FOs and supporting arms coordinators."
        ),
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
