from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    MAP_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)

_RESOURCE_CATEGORIES = {
    "topo": (
        "Topographic & Elevation",
        "Contour lines, elevation models, slope analysis, viewshed planning.",
        ("USGS The National Map", "USGS topoView", "USGS National Map Downloader", "OpenTopoMap", "OpenTopography"),
    ),
    "imagery": (
        "Satellite Imagery",
        "Current and historical overhead imagery, multispectral analysis, change detection.",
        ("USGS EarthExplorer", "Sentinel Hub EO Browser", "Google Earth (Web)"),
    ),
    "hydro": (
        "Hydrology & Waterways",
        "Rivers, streams, flood zones, water levels, nautical charts, port approach.",
        ("USGS National Water Dashboard", "NOAA Nautical Charts (Office of Coast Survey)"),
    ),
    "weather": (
        "Weather & Climate",
        "Wind, precipitation, visibility, temperature overlays for exercise planning.",
        ("Windy.com", "NWS Forecast Maps"),
    ),
    "political": (
        "Political, Borders & Administrative",
        "Country/state boundaries, demographics, populated places, infrastructure baselines.",
        ("Natural Earth", "CIA World Factbook"),
    ),
    "conflict": (
        "Conflict, Humanitarian & OSINT",
        "Active conflict events, displacement, humanitarian access, security situation maps.",
        ("ACLED (Armed Conflict Location & Event Data)", "ReliefWeb Maps", "Liveuamap"),
    ),
    "infra": (
        "Infrastructure & Transportation",
        "Roads, bridges, railroads, buildings, land use, LOC analysis.",
        ("OpenStreetMap", "OpenRailwayMap"),
    ),
    "historical": (
        "Historical Maps",
        "Campaign maps, historical boundaries, terrain change over time.",
        ("David Rumsey Map Collection", "Library of Congress Map Collections", "USGS topoView"),
    ),
    "terrain3d": (
        "Terrain Analysis & 3D",
        "LiDAR, high-res DEMs, 3D terrain visualization, slope/aspect modeling.",
        ("OpenTopography", "Fatmap / Strava Heatmap (terrain)", "Google Earth (Web)"),
    ),
}

_CATEGORY_SIGNALS: dict[str, list[str]] = {
    "topo": ["topo", "elevation", "contour", "relief", "slope", "viewshed", "hilltop", "ridge", "valley"],
    "imagery": ["satellite", "imagery", "overhead", "aerial", "photo", "sentinel", "landsat", "multispectral"],
    "hydro": ["river", "stream", "water", "flood", "crossing", "waterway", "port", "harbor", "nautical", "coastal", "littoral", "amphibious"],
    "weather": ["weather", "wind", "rain", "visibility", "climate", "forecast", "precipitation"],
    "political": ["political", "border", "boundar", "country", "demographic", "population", "administrative"],
    "conflict": ["conflict", "fighting", "attack", "violence", "humanitarian", "refugee", "displaced", "crisis", "security situation"],
    "infra": ["road", "bridge", "rail", "infrastructure", "transport", "route", "msr", "asr", "loc", "building"],
    "historical": ["histor", "old map", "campaign", "civil war", "wwi", "wwii", "colonial", "boundary change"],
    "terrain3d": ["3d", "lidar", "dem", "slope analysis", "aspect", "viewshed", "rugged", "mountain"],
}


def _detect_categories(text: str) -> list[str]:
    lowered = text.lower()
    hits: list[str] = []
    for cat, signals in _CATEGORY_SIGNALS.items():
        if any(s in lowered for s in signals):
            hits.append(cat)
    return hits


class TerrainMapAdvisorAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="terrain-map-advisor",
            name="Map & Geospatial OSINT Resource Finder",
            description=(
                "Find and recommend public map and geospatial OSINT resources for area analysis, exercise "
                "planning, and staff familiarization. Covers topographic, satellite imagery, political, "
                "conflict, hydrological, historical, infrastructure, weather, and 3D terrain sources."
            ),
            domain="map and geospatial OSINT",
            intended_users=["SMCR officers", "S-2", "S-3", "G-9", "planners", "OSINT analysts"],
            allowed_sources=[
                "public geospatial data portals (USGS, NOAA, ESA, OSM)",
                "public conflict and humanitarian mapping (ACLED, ReliefWeb, Liveuamap)",
                "public historical map archives (LOC, David Rumsey)",
                "public weather and hydrological services",
                "training-only scenarios and user-provided area names",
            ],
            disallowed_inputs=[
                "classified geospatial products or NGA data",
                "sensitive facility targeting or real-world fire missions",
                "real-world hostile-action planning",
                "private location tracking or PII-linked geolocation",
            ],
            system_prompt=(
                "You are a map and geospatial OSINT resource finder. When given an area or scenario, "
                "recommend the specific public map resources to pull — not generic advice, but actual "
                "sources with URLs organized by what they answer. Think like an S-2 building an area "
                "study: what does the terrain look like, what's the infrastructure, where's the water, "
                "what's the political situation, what's the conflict history, what did it look like "
                "historically. Match resources to the planning question."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        active_context_lines = self._active_context_lines(context)
        active_context_block = ""
        if active_context_lines:
            active_context_block = "Active local operating context:\n" + "\n".join(
                f"- {line}" for line in active_context_lines
            ) + "\n\n"

        detected = _detect_categories(input_text)
        if not detected:
            detected = list(_RESOURCE_CATEGORIES.keys())

        resource_blocks: list[str] = []
        for cat_key in detected:
            cat_name, cat_desc, cat_sources = _RESOURCE_CATEGORIES[cat_key]
            ref_lines = []
            for ref in MAP_REFERENCES:
                if ref.title in cat_sources:
                    ref_lines.append(f"  - {ref.title}: {ref.url}\n    {ref.notes}")
            if ref_lines:
                resource_blocks.append(f"**{cat_name}** — {cat_desc}\n" + "\n".join(ref_lines))

        all_categories = "\n\n".join(resource_blocks) if resource_blocks else "No specific category detected — showing all resources."

        answer = (
            "Map & geospatial OSINT resource advisory.\n\n"
            f"{active_context_block}"
            "Based on your query, here are the relevant public map resources:\n\n"
            f"{all_categories}\n\n"
            "How to use this for area analysis:\n"
            "1. Start with the planning question — what do you need to know about this area?\n"
            "2. Pull one resource per category that answers your question.\n"
            "3. Layer them: topo base → imagery overlay → infrastructure → hydro → political context.\n"
            "4. For exercise design: add conflict/humanitarian context and historical comparison.\n"
            "5. Capture each product with source URL, retrieval date, and scale/resolution.\n\n"
            "Available resource categories (ask for any by name):\n"
            "- topo: Topographic maps and elevation data\n"
            "- imagery: Satellite and aerial imagery\n"
            "- hydro: Rivers, water levels, nautical charts\n"
            "- weather: Wind, precipitation, visibility\n"
            "- political: Borders, demographics, country profiles\n"
            "- conflict: Active conflicts, humanitarian situations\n"
            "- infra: Roads, bridges, rail, buildings\n"
            "- historical: Campaign maps, historical boundaries\n"
            "- terrain3d: LiDAR, 3D visualization, slope analysis\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(MAP_REFERENCES),
            structured_citations=structured_citations(MAP_REFERENCES),
            source_trust=source_trust_markers(
                MAP_REFERENCES,
                notes_prefix="Public geospatial sources — verify currency and accuracy before operational use.",
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What area or region do you need to analyze?",
                "What's the planning purpose — exercise design, area study, route analysis, or familiarization?",
                "Do you need current conditions (imagery, water, weather) or historical context?",
                "What specific map layers matter most: terrain, infrastructure, waterways, political, or conflict?",
            ],
        )


def build_map_agent() -> TerrainMapAdvisorAgent:
    return TerrainMapAdvisorAgent()
