from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MAP_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class TerrainMapAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="terrain-map-advisor",
            name="Terrain / Map Advisor",
            description=(
                "Supports public-source terrain and map discovery for staff planning, area familiarization, and "
                "training-scenario grounding using authoritative public map references such as USGS."
            ),
            domain="terrain and map planning",
            intended_users=["SMCR officers", "S-2", "S-3", "G-9", "planners", "chief of staff / aide"],
            allowed_sources=[
                "USGS public map and terrain products",
                "public topographic and elevation references",
                "public hydrography and transport-layer references",
                "training-only scenarios and user-provided area names",
            ],
            disallowed_inputs=[
                "classified geospatial products",
                "sensitive facility targeting",
                "real-world hostile-action planning",
                "private location tracking",
            ],
            system_prompt=(
                "Respond like a practical terrain and map planning advisor under the public-source S-2/S-3 lane. "
                "Focus on what public map products to pull, what terrain questions matter, and how to use USGS "
                "products safely for training, familiarization, and staff planning. Stay advisory."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = "Active local operating context:\n" + "\n".join(
                f"- {line}" for line in active_context_lines
            ) + "\n\n"
        answer = (
            "Terrain / map advisory draft.\n\n"
            "Use this to decide what public maps or terrain products to pull for a location, not as authoritative "
            "geospatial tasking.\n\n"
            f"{active_context_block}"
            "Primary map-planning lenses:\n"
            "- What area needs terrain or map familiarization?\n"
            "- What matters most: elevation, hydrography, transport routes, structures, land cover, or historical "
            "map comparison?\n"
            "- Is the need current terrain awareness, training-scenario grounding, movement planning context, or "
            "a simple topo-map pull?\n\n"
            "Recommended first-line public sources:\n"
            "- USGS The National Map for current topographic and terrain layers.\n"
            "- USGS topoView for historical and current topo maps by area.\n"
            "- USGS National Map Downloader when you need a specific map product or layer export.\n"
            "- USGS EarthExplorer when imagery or land-use context matters.\n\n"
            "My read:\n"
            "- If the question is just 'what does this ground look like,' start with USGS before wandering into "
            "random map sites.\n"
            "- Pull only the layers that answer the planning question. More layers are not automatically more useful.\n"
            "- For training design, the best map is usually the one that makes the decision point, mobility issue, "
            "or civil constraint obvious.\n\n"
            "Map pull checklist:\n"
            "- Name the area, nearest city, or coordinate reference.\n"
            "- Decide whether you need topo, imagery, hydrography, transportation, or historical comparison.\n"
            "- Pull one overview product and one detailed product before adding more.\n"
            "- Capture the product name, URL, scale, and retrieval date.\n"
            "- Treat public map products as planning context; verify any real access, ownership, or use restriction "
            "through the proper local authority.\n\n"
            "Useful outputs:\n"
            "- Recommended map products by area\n"
            "- Terrain questions to answer before planning continues\n"
            "- Sketch-map prompts for TDGs or rehearsals\n"
            "- Civil or mobility constraints worth handing to S-3, G-9, or Doc\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MAP_REFERENCES),
            structured_citations=structured_citations(MAP_REFERENCES),
            source_trust=source_trust_markers(
                MAP_REFERENCES,
                notes_prefix=(
                    "Use these as first-line public terrain and map references before "
                    "less authoritative sites."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What exact area, city, or coordinate reference do you need to map?",
                "Do you need topographic context, imagery, hydrography, movement routes, or a historical comparison?",
                "Is this for training design, public-source familiarization, a TDG, or staff planning support?",
            ],
        )


def build_map_agent() -> TerrainMapAdvisorAgent:
    return TerrainMapAdvisorAgent()
