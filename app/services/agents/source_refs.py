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
            notes=self.notes,
        )

    def trust(self, notes: str | None = None) -> SourceTrustMarker:
        return SourceTrustMarker(
            tracked_title=self.title,
            status=VerifiedSourceStatus.needs_review,
            verification_source_url=self.url,
            notes=notes or self.notes,
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
)

S3_REFERENCES: tuple[SourceRef, ...] = (
    SourceRef(
        title="MCDP 5 Planning",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899841/mcdp-5/",
        publisher="United States Marine Corps",
        notes="Planning mindset and decision-making discipline.",
    ),
    SourceRef(
        title="MCWP 5-10 Marine Corps Planning Process",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/900553/mcwp-5-10/",
        publisher="United States Marine Corps",
        notes="Concrete MCPP rhythm, staff products, and commander decision support.",
    ),
    SourceRef(
        title="MCO 1553.3C Unit Training Management",
        url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/899431/mco-15533c/",
        publisher="United States Marine Corps",
        notes="Core training design, assessment, and event discipline reference.",
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


def citation_titles(refs: tuple[SourceRef, ...]) -> list[str]:
    return [ref.title for ref in refs]


def structured_citations(refs: tuple[SourceRef, ...]) -> list[StructuredCitation]:
    return [ref.citation() for ref in refs]


def source_trust_markers(
    refs: tuple[SourceRef, ...], notes_prefix: str = "Verify current public source and local applicability."
) -> list[SourceTrustMarker]:
    return [ref.trust(f"{notes_prefix} {ref.notes}") for ref in refs]
