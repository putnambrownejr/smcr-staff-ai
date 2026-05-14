from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.services.agents.base import Agent, AgentContext


class FitrepAssistantAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="fitrep-assistant",
            name="FitRep Assistant",
            description="Helps outline PES/FitRep drafting considerations without storing personal evaluations.",
            domain="performance evaluation",
            intended_users=["officers", "reporting seniors", "reviewing officers", "AdminO", "S-1"],
            allowed_sources=[
                "public PES references",
                "MCRAMM or other current Reserve admin references",
                "local accomplishment notes marked UNCLASSIFIED",
            ],
            disallowed_inputs=[
                "SSNs",
                "medical data",
                "sensitive personnel files",
                "official final FitRep submission data",
            ],
            system_prompt=(
                "Support FitRep planning, accomplishment capture, and review prompts. "
                "Do not make final ratings decisions or serve as an official submission tool."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "FitRep planning advisory draft.\n\n"
            "Use this to organize evidence, bullet themes, suspense items, and review checkpoints. "
            "Do not use it as the final official evaluation or as the basis for unsupported comparative marks.\n\n"
            "Suggested workflow:\n"
            "- Confirm the reporting occasion, dates, billet, and chain (MRO/RS/RO).\n"
            "- Gather documented accomplishments, quantified outcomes, leadership examples, "
            "and reserve-specific context.\n"
            "- Separate substantiated facts from opinions or praise-only language.\n"
            "- Build concise action-impact-result bullets and note what still needs verification.\n"
            "- Check routing suspense, reviewer expectations, and any command-specific admin guidance.\n"
            "- Route for human review before any official use.\n\n"
            "Common support modes:\n"
            "- accomplishment capture checklist\n"
            "- FitRep prep timeline\n"
            "- bullet theme brainstorm\n"
            "- routing and suspense review\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "MCO 1610.7 Performance Evaluation System",
                "MCRAMM or current Reserve admin references as applicable",
            ],
            structured_citations=[
                StructuredCitation(
                    title="MCO 1610.7 Performance Evaluation System",
                    url="https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/Article/2861459/mco-16107a/",
                    publisher="Headquarters Marine Corps",
                    confidence=Confidence.low,
                    notes="Manifest/source-note citation; verify the current MCPEL entry and revision before use.",
                )
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "What reporting occasion and suspense are you working against?",
                "What documented accomplishments or notes already exist?",
                "Do you need planning help, bullet themes, or routing review?",
            ],
        )


def build_fitrep_agent() -> FitrepAssistantAgent:
    return FitrepAssistantAgent()
