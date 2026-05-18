from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.security import detect_pii_input, detect_sensitive_input
from app.schemas.privacy_review import (
    PrivacyFinding,
    PrivacyFindingSeverity,
    RepoPrivacySweepResponse,
)

HIGH_RISK_EXACT_PATHS = {
    ".env",
    "docs/offline_notes.md",
    "docs/sources/civil_affairs.md",
}
HIGH_RISK_PREFIXES = (
    "data/local_context/",
    "docs/scenarios/",
    "outputs/",
)


class RepoPrivacySweeper:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()

    def sweep(
        self,
        include_untracked: bool = True,
        include_ignored_status: bool = True,
    ) -> RepoPrivacySweepResponse:
        git_status = self._git_status()
        if git_status is None:
            return RepoPrivacySweepResponse(
                repo_root=str(self.repo_root),
                git_available=False,
                safe_to_push=False,
                findings=[
                    PrivacyFinding(
                        severity=PrivacyFindingSeverity.high,
                        category="git",
                        title="Git status unavailable",
                        detail=(
                            "The privacy sweep could not inspect repository state because git is not available "
                            "or this path is not a git work tree."
                        ),
                        recommendation="Run the sweep from the repo root of a valid git working tree.",
                    )
                ],
                recommendations=[
                    "Run `git status` locally and verify tracked, staged, and ignored files before pushing."
                ],
                warnings=["This check is advisory and cannot guarantee a clean push without git access."],
            )

        tracked_files = set(self._git_lines(["ls-files"]) or [])
        staged_files: list[str] = []
        unstaged_files: list[str] = []
        untracked_files: list[str] = []
        ignored_files: list[str] = []

        for code, path in git_status:
            if code == "??":
                untracked_files.append(path)
                continue
            if code == "!!":
                ignored_files.append(path)
                continue
            if code and code[0] not in {" ", "?"}:
                staged_files.append(path)
            if len(code) > 1 and code[1] not in {" ", "?"}:
                unstaged_files.append(path)

        findings: list[PrivacyFinding] = []
        tracked_high_risk = sorted(path for path in tracked_files if _is_high_risk_path(path))
        if tracked_high_risk:
            findings.append(
                PrivacyFinding(
                    severity=PrivacyFindingSeverity.high,
                    category="tracked-paths",
                    title="Tracked local-only or personal-data path detected",
                    detail=(
                        "One or more tracked files match local-only paths that should stay outside the "
                        "GitHub-facing repo surface."
                    ),
                    affected_paths=tracked_high_risk,
                    recommendation=(
                        "Remove these files from git tracking, keep them in local-only storage, and rely on "
                        "the repo-safe example/template files instead."
                    ),
                )
            )

        present_high_risk = self._present_high_risk_paths()
        ignored_high_risk = sorted(path for path in present_high_risk if path in set(ignored_files))
        unprotected_high_risk = sorted(
            path
            for path in present_high_risk
            if path not in tracked_files and path not in set(ignored_files)
        )
        if unprotected_high_risk:
            findings.append(
                PrivacyFinding(
                    severity=PrivacyFindingSeverity.medium,
                    category="ignore-rules",
                    title="High-risk local path is not ignored",
                    detail=(
                        "A local-only file or folder exists in the repo tree but is neither tracked nor matched "
                        "by current ignore rules."
                    ),
                    affected_paths=unprotected_high_risk,
                    recommendation="Extend `.gitignore` or move the file into the external local state home.",
                )
            )

        staged_diff = self._git_text(["diff", "--cached", "--no-color", "--unified=0"])
        unstaged_diff = self._git_text(["diff", "--no-color", "--unified=0"])
        findings.extend(_diff_findings(staged_diff, staged=True))
        findings.extend(_diff_findings(unstaged_diff, staged=False))

        if include_untracked:
            risky_untracked = sorted(path for path in untracked_files if _is_high_risk_path(path))
            if risky_untracked:
                findings.append(
                    PrivacyFinding(
                        severity=PrivacyFindingSeverity.low,
                        category="untracked",
                        title="Local-only high-risk files are present in the working tree",
                        detail=(
                            "These files are currently untracked, which is usually fine, but they should stay "
                            "ignored and never be force-added."
                        ),
                        affected_paths=risky_untracked,
                        recommendation="Leave these files untracked or move them into the external local state home.",
                    )
                )

        recommendations = [
            "Review `git diff --cached --name-only` before pushing.",
            "Keep drill notes, receipts, handoffs, local uploads, and scratch outputs in external local storage.",
            "Treat this sweep as advisory; a force-add can still bypass ignore rules.",
        ]
        if not tracked_high_risk and not unprotected_high_risk and not findings:
            recommendations.insert(
                0,
                "The repo surface looks clean for the checked heuristics; still do a final human review before push.",
            )

        return RepoPrivacySweepResponse(
            repo_root=str(self.repo_root),
            git_available=True,
            safe_to_push=not any(finding.severity == PrivacyFindingSeverity.high for finding in findings),
            staged_files=sorted(set(staged_files)),
            unstaged_files=sorted(set(unstaged_files)),
            untracked_files=sorted(set(untracked_files)),
            ignored_high_risk_paths=ignored_high_risk if include_ignored_status else [],
            findings=findings,
            recommendations=recommendations,
            warnings=[
                "This sweep is heuristic and advisory.",
                "It helps catch common user-data backflow, but it cannot guarantee a safe push in every case.",
            ],
        )

    def _git_status(self) -> list[tuple[str, str]] | None:
        lines = self._git_lines(["status", "--short", "--ignored=matching"])
        if lines is None:
            return None
        parsed: list[tuple[str, str]] = []
        for raw in lines:
            if len(raw) < 3:
                continue
            code = raw[:2]
            path = raw[3:]
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            parsed.append((code, path.replace("\\", "/")))
        return parsed

    def _git_lines(self, args: list[str]) -> list[str] | None:
        text = self._git_text(args)
        if text is None:
            return None
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _git_text(self, args: list[str]) -> str | None:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_root,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return None
        return result.stdout

    def _present_high_risk_paths(self) -> list[str]:
        found: set[str] = set()
        for exact in HIGH_RISK_EXACT_PATHS:
            candidate = self.repo_root / exact
            if candidate.exists():
                found.add(exact)
        found.update(_glob_matches(self.repo_root, "docs/deep_research/*_pull.md"))
        found.update(_glob_matches(self.repo_root, "docs/scenarios/**/*"))
        found.update(_glob_matches(self.repo_root, "outputs/**/*"))
        found.update(_glob_matches(self.repo_root, "scripts/scratch_*"))
        found.update(_glob_matches(self.repo_root, "scripts/scratch_*/*"))
        found.update(_glob_matches(self.repo_root, "data/local_context/**/*"))
        found.update(_glob_matches(self.repo_root, "*.db"))
        found.update(_glob_matches(self.repo_root, "*.sqlite*"))
        return sorted(path for path in found if _is_high_risk_path(path))


def _glob_matches(repo_root: Path, pattern: str) -> set[str]:
    matches: set[str] = set()
    for path in repo_root.glob(pattern):
        if path.is_file() or path.is_dir():
            rel = path.relative_to(repo_root).as_posix()
            matches.add(rel)
    return matches


def _is_high_risk_path(path: str) -> bool:
    normalized = path.replace("\\", "/").strip()
    if normalized in HIGH_RISK_EXACT_PATHS:
        return True
    if normalized.startswith(HIGH_RISK_PREFIXES):
        return True
    if normalized.startswith("docs/deep_research/") and normalized.endswith("_pull.md"):
        return True
    if normalized.startswith("scripts/scratch_"):
        return True
    return normalized.endswith(".db") or ".sqlite" in normalized


def _diff_findings(diff_text: str | None, staged: bool) -> list[PrivacyFinding]:
    if not diff_text:
        return []
    findings: list[PrivacyFinding] = []
    pii_warnings = detect_pii_input(diff_text)
    sensitive_warnings = detect_sensitive_input(diff_text)
    if pii_warnings:
        findings.append(
            PrivacyFinding(
                severity=PrivacyFindingSeverity.high if staged else PrivacyFindingSeverity.medium,
                category="content",
                title="Potential PII detected in git diff",
                detail=(
                    "The sweep matched personal-data heuristics in the "
                    + ("staged" if staged else "unstaged")
                    + " diff."
                ),
                evidence=pii_warnings,
                recommendation="Redact or move the personal data into local-only storage before pushing.",
            )
        )
    if sensitive_warnings:
        findings.append(
            PrivacyFinding(
                severity=PrivacyFindingSeverity.high if staged else PrivacyFindingSeverity.medium,
                category="content",
                title="Potential sensitive operational content detected in git diff",
                detail=(
                    "The sweep matched OPSEC/classification heuristics in the "
                    + ("staged" if staged else "unstaged")
                    + " diff."
                ),
                evidence=sensitive_warnings,
                recommendation=(
                    "Keep sensitive operational details out of the repo and reduce the content to generic "
                    "training-safe language."
                ),
            )
        )
    return findings
