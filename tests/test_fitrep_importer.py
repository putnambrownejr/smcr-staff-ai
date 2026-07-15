from decimal import Decimal

from app.services.fitreps.importer import propose_report_import, propose_rs_profile_import


def test_report_importer_proposes_only_labeled_values() -> None:
    proposal = propose_report_import(
        "Reporting Period End: 2026-06-30\nOccasion: AN\nGrade: Capt\nBillet: S-4\n"
        "Reporting Senior: RS Alpha\nRelative Value: 92.4\nLeadership: 5.0\n",
        context_id="0123456789abcdef",
        user_key="capt-fitrep",
    )
    assert proposal.report is not None
    assert proposal.report.relative_value == Decimal("92.4")
    assert proposal.report.traits["leadership"] == 5.0
    assert proposal.report.source_context_id == "0123456789abcdef"
    assert proposal.requires_confirmation is True


def test_sparse_import_does_not_invent_values() -> None:
    proposal = propose_report_import("A narrative with no labeled fields.", "0123456789abcdef", "capt-fitrep")
    assert proposal.report is not None
    assert proposal.report.relative_value is None
    assert proposal.report.rs_label == ""
    assert proposal.warnings


def test_rs_profile_importer_preserves_as_of_and_counts() -> None:
    proposal = propose_rs_profile_import(
        "Reporting Senior: RS Alpha\nAs of: 2026-07-01\nGrade: Capt\nPopulation: 8\nReports: 12\n",
        context_id="0123456789abcdef",
        user_key="capt-fitrep",
    )
    assert proposal.rs_profile is not None
    assert proposal.rs_profile.population_size == 8
    assert proposal.rs_profile.report_count == 12
