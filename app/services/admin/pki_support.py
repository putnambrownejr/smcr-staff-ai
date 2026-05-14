from __future__ import annotations

from app.core.security import DEFAULT_WARNINGS
from app.schemas.pki import PkiIssueType, PkiTroubleshootingRequest, PkiTroubleshootingResponse


class PkiTroubleshootingService:
    def build(self, request: PkiTroubleshootingRequest) -> PkiTroubleshootingResponse:
        likely_causes, immediate_checks, deeper_checks = _issue_playbook(request.issue_type)
        immediate_checks = [
            *immediate_checks,
            *[f"Confirm symptom: {item}" for item in request.symptoms],
        ]
        deeper_checks = [
            *deeper_checks,
            *[f"Environment note to validate: {item}" for item in request.environment_notes],
        ]
        summary_lines = _build_summary_lines(request)
        escalation_path = _build_escalation_path(request)
        safe_data_handling_notes = [
            "Do not share PINs, private keys, screenshots of certificate serials, or full personnel details.",
            "Keep troubleshooting notes generic and store only the minimum local context needed for continuity.",
            (
                "If the issue involves official portals, verify the current help-desk "
                "or enterprise service-desk guidance before acting."
            ),
        ]
        return PkiTroubleshootingResponse(
            title=f"PKI/CAC troubleshooting: {request.title}",
            issue_type=request.issue_type,
            summary_lines=summary_lines,
            likely_causes=likely_causes,
            immediate_checks=immediate_checks,
            deeper_checks=deeper_checks,
            escalation_path=escalation_path,
            safe_data_handling_notes=safe_data_handling_notes,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "PKI/CAC support is advisory only; use official enterprise IT "
                    "guidance and local help-desk procedures for final resolution."
                ),
            ],
        )


def _build_summary_lines(request: PkiTroubleshootingRequest) -> list[str]:
    lines = [
        (
            "Start with the lowest-friction checks first: reader seating, middleware, "
            "browser certificate prompt, and portal-specific behavior."
        ),
        (
            "Separate hardware detection problems from certificate-selection or "
            "browser-authentication problems before escalating."
        ),
    ]
    if request.browser:
        lines.append(f"Browser context captured: {request.browser}.")
    if request.affected_systems:
        lines.append(f"Affected systems: {', '.join(request.affected_systems)}.")
    if request.on_government_furnished_equipment is False:
        lines.append("User appears to be on non-GFE equipment, so local browser and middleware drift are more likely.")
    if request.using_vpn:
        lines.append(
            "VPN is in play; confirm the problem exists both with and without the "
            "approved VPN path when policy allows."
        )
    return lines


def _build_escalation_path(request: PkiTroubleshootingRequest) -> list[str]:
    path = [
        "Document what system failed, what browser was used, and which certificate behavior was observed.",
        (
            "Escalate with reproducible steps, recent changes, and whether the issue "
            "affects one portal or multiple portals."
        ),
    ]
    if request.on_government_furnished_equipment:
        path.append(
            "If on GFE, capture the asset context and route through the local "
            "enterprise/service desk or supporting S-6/G-6 help path."
        )
    else:
        path.append(
            "If on personal equipment, confirm the portal is authorized for that "
            "access pattern and shift to approved devices if required."
        )
    path.append(
        "If certificates appear expired, missing, or mismatched, stop short of "
        "guesswork and use official PKI support channels."
    )
    return path


def _issue_playbook(issue_type: PkiIssueType) -> tuple[list[str], list[str], list[str]]:
    if issue_type == PkiIssueType.cac_not_detected:
        return (
            [
                "Reader or cable seating issue.",
                "Reader driver or middleware not loading correctly.",
                "CAC is not being detected consistently by the host system.",
            ],
            [
                "Reseat the CAC and reader, then test whether the OS detects the card before opening any portal.",
                "Try a different USB port or approved reader if available.",
                "Check whether another smart-card-aware application sees the CAC.",
            ],
            [
                "Validate middleware installation and recent updates.",
                "Confirm the issue persists after a clean reboot.",
                "Compare behavior on a second approved device to separate card issues from host issues.",
            ],
        )
    if issue_type == PkiIssueType.certificate_issue:
        return (
            [
                "Wrong certificate selected for the task.",
                "Expired or unavailable certificate chain.",
                "Portal is rejecting the certificate even though the card is present.",
            ],
            [
                (
                    "Confirm whether the task needs authentication, signing, or "
                    "encryption and choose the matching certificate prompt if one appears."
                ),
                "Check the displayed certificate dates and whether expected certificates appear at all.",
                "Test another official CAC-enabled site to see whether the issue is portal-specific.",
            ],
            [
                "Validate certificate trust chain behavior in the browser or middleware tooling.",
                "Check whether the portal recently changed supported browser or certificate behavior.",
                "Escalate with the exact portal behavior rather than trial-and-error certificate changes.",
            ],
        )
    if issue_type == PkiIssueType.middleware_issue:
        return (
            [
                "Middleware is missing, disabled, or stale.",
                "Recent updates changed certificate access behavior.",
                "Browser cannot reach the local smart-card middleware correctly.",
            ],
            [
                "Confirm the approved middleware is installed and running.",
                "Restart the host and retest after confirming the middleware service loads.",
                "Check whether multiple middleware tools are competing on the same machine.",
            ],
            [
                "Validate version drift against current enterprise guidance.",
                "Remove assumptions about browser problems until middleware behavior is confirmed independently.",
                "Escalate with version, OS, and whether the failure is universal or browser-specific.",
            ],
        )
    if issue_type == PkiIssueType.browser_auth_issue:
        return (
            [
                "Browser certificate prompt is suppressed or cached incorrectly.",
                "Portal/browser compatibility drift.",
                "Browser profile settings or extensions are interfering with auth flow.",
            ],
            [
                "Try the supported browser for that portal and compare behavior in a clean session.",
                "Clear browser state relevant to certificate prompts if allowed by policy.",
                "Disable nonessential extensions and retry the sign-in flow.",
            ],
            [
                "Test in a private/incognito session to separate profile drift from portal issues.",
                "Confirm whether the issue occurs across multiple browsers or only one.",
                "Capture whether the failure happens before, during, or after certificate selection.",
            ],
        )
    if issue_type == PkiIssueType.signing_encryption_issue:
        return (
            [
                "Signing/encryption certificate mismatch.",
                "Mail or document client configuration drift.",
                "Recipient trust or certificate availability issue.",
            ],
            [
                "Confirm whether the failure is in email signing, encryption, or document signing.",
                "Test a simple sign-only workflow before troubleshooting encryption paths.",
                "Verify the client can still see the expected signing certificates.",
            ],
            [
                "Separate sender configuration issues from recipient trust issues.",
                "Check whether the problem started after updates to Outlook, browser, or middleware.",
                "Escalate with client name, action attempted, and whether sign-only succeeds.",
            ],
        )
    if issue_type == PkiIssueType.portal_access_issue:
        return (
            [
                "Portal-specific outage or browser support issue.",
                "Certificate flow works generally, but the target site is failing.",
                "Network path, VPN, or session policy issue.",
            ],
            [
                "Confirm whether other CAC-enabled portals work.",
                "Check whether the issue is limited to one URL or one workflow on that site.",
                "Retry from the supported access path and note any exact error message.",
            ],
            [
                "Look for portal maintenance notices or enterprise outages.",
                "Compare behavior on approved network paths if policy allows.",
                "Escalate with portal name, time of failure, and reproducible sequence.",
            ],
        )
    if issue_type == PkiIssueType.reader_hardware_issue:
        return (
            [
                "Reader hardware failure or inconsistent connection.",
                "Cable/port power issue.",
                "Reader driver mismatch with the host environment.",
            ],
            [
                "Swap ports or use a second approved reader if available.",
                "Check whether the OS recognizes reader connect/disconnect events.",
                "Avoid concluding the CAC is bad until a second reader or device is tested.",
            ],
            [
                "Validate reader model and driver compatibility with the host OS.",
                "Capture whether the issue is intermittent, heat-related, or cable-sensitive.",
                "Escalate with reader model and whether other cards fail the same way.",
            ],
        )
    return (
            [
                (
                    "The failure could be in hardware detection, middleware, browser "
                    "prompt handling, or portal-specific behavior."
                ),
                "Without isolating the layer first, escalation tends to be noisy and slow.",
            ],
        [
            "Confirm whether the CAC is detected by the host before opening the target site.",
            "Check whether one or multiple portals are affected.",
            "Record browser, device type, and any exact error text.",
        ],
        [
            "Test a second approved browser or device to separate user environment issues from portal issues.",
            "Capture the smallest reproducible sequence before opening a ticket.",
            "Escalate with facts, not guesses about certificates or middleware.",
        ],
    )
