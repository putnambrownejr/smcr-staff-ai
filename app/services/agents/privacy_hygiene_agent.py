from pathlib import Path

from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.privacy.repo_privacy_sweeper import RepoPrivacySweeper


class PrivacyHygieneAgent(Agent):
    metadata = AgentMetadata(
        id="repo-privacy-sweeper",
        name="Repo Privacy Sweeper",
        description=(
            "Reviews the local git working tree for personal-data backflow, risky tracked files, "
            "and push-time privacy hygiene issues."
        ),
        domain="repo privacy hygiene",
        intended_users=["contributors", "maintainers", "reservists using local-only context"],
        allowed_sources=[
            "local git status",
            "tracked file list",
            "staged and unstaged diff summaries",
            "repo-local ignore rules and README guidance",
        ],
        disallowed_inputs=[
            "requests to upload local-only user data to public remotes",
            "requests to ignore PII or OPSEC findings before push",
        ],
        system_prompt=(
            "Review the repo before push. Look for tracked local-only paths, staged or unstaged PII/OPSEC "
            "content, and holes in ignore coverage. Be conservative, specific, and remind the user that "
            "the sweep is advisory rather than authoritative."
        ),
        required_human_review=True,
        citation_required=False,
    )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        repo_root = _repo_root_from_context(context)
        result = RepoPrivacySweeper(repo_root).sweep()
        if result.git_available is False:
            answer = (
                "I could not inspect git state for this repo, so I cannot give a trustworthy pre-push privacy read. "
                "Run the sweep from a valid git working tree."
            )
            return self._response(
                answer=answer,
                input_text=input_text,
                follow_up_questions=[
                    "Can you rerun this from the repo root?",
                    "Do you want a route or script invocation instead of the agent runner?",
                ],
                citations=["README.md", ".gitignore"],
                confidence=Confidence.low,
            )

        headline = "Safe to push for checked heuristics." if result.safe_to_push else "Not ready to push yet."
        finding_lines = []
        for finding in result.findings[:6]:
            paths = f" Paths: {', '.join(finding.affected_paths[:4])}." if finding.affected_paths else ""
            finding_lines.append(f"- [{finding.severity}] {finding.title}: {finding.detail}{paths}")
        if not finding_lines:
            finding_lines.append("- No high-risk tracked paths or diff-content warnings matched the current checks.")

        answer = (
            f"{headline}\n\n"
            f"Repo root: {result.repo_root}\n"
            f"Staged files: {len(result.staged_files)}\n"
            f"Unstaged files: {len(result.unstaged_files)}\n"
            f"Untracked files: {len(result.untracked_files)}\n\n"
            "Privacy sweep findings:\n"
            + "\n".join(finding_lines)
            + "\n\nRecommended next actions:\n"
            + "\n".join(f"- {item}" for item in result.recommendations[:3])
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            follow_up_questions=[
                "Do you want the raw structured sweep from `/privacy/pre-push-review` too?",
                "Should we add any more local-only path patterns to the high-risk list?",
            ],
            citations=["README.md", ".gitignore", "docs/offline_notes.example.md"],
            confidence=Confidence.medium if result.safe_to_push else Confidence.low,
        )


def build_privacy_hygiene_agent() -> PrivacyHygieneAgent:
    return PrivacyHygieneAgent()


def _repo_root_from_context(context: AgentContext) -> Path:
    raw_repo_root = context.extra.get("repo_root")
    if isinstance(raw_repo_root, str) and raw_repo_root.strip():
        return Path(raw_repo_root)
    return Path(__file__).resolve().parents[3]
