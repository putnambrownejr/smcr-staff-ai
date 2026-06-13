"""
Generates a structured open-source research note for a user's billet, unit, and MOS.

All content is derived from publicly available, unclassified doctrine and
organizational references. No live web requests are made — results are
compiled from a curated static lookup and formatted as markdown.
"""

from __future__ import annotations

_MOS_CATALOG: dict[str, dict] = {
    "01": {
        "name": "Personnel and Administration",
        "navmc": "NAVMC 3500.3",
        "roles": ["Admin Chief", "S-1 SNCO", "Personnel Officer"],
        "doctrine": [
            "MCO P1000.6 — Assignment, Classification, and Travel of Enlisted Marines",
            "MCO 1080.40 — Active Reserve Management",
            "MARADMIN 318/14 — Reserve Component Common Skills",
        ],
        "notes": "Personnel and admin Marines manage manpower records, casualty reporting, and admin support across the unit.",
    },
    "02": {
        "name": "Intelligence",
        "navmc": "NAVMC 3500.100",
        "roles": ["S-2 Officer", "Intelligence Analyst", "HUMINT Collector"],
        "doctrine": [
            "MCWP 2-10 — Intelligence",
            "MCRP 2-10A.6 — MAGTF Intelligence Production and Analysis",
        ],
        "notes": "Intelligence Marines produce and disseminate threat assessments, IPB products, and all-source analysis.",
    },
    "03": {
        "name": "Infantry",
        "navmc": "NAVMC 3500.44",
        "roles": ["Rifle Platoon Commander", "Company Commander", "S-3 Officer"],
        "doctrine": [
            "MCWP 3-11.2 — Marine Rifle Company",
            "MCWP 3-11.3 — Marine Rifle Platoon",
            "MCRP 3-10A.4 — Marine Rifle Squad",
        ],
        "notes": "Infantry Marines execute close combat, raid, assault, and defensive operations. Core METL tasks center on MCT 1.6.1 (Offensive) and 1.6.4 (Defensive).",
    },
    "04": {
        "name": "Logistics",
        "navmc": "NAVMC 3500.27",
        "roles": ["SuppO", "S-4 Officer", "Logistics Chief"],
        "doctrine": [
            "MCWP 4-11 — Tactical Level Logistics",
            "MCTP 4-10B — Marine Corps Bulk Liquid Operations",
            "MCO 4400.16 — Unit Supply Policies and Procedures",
        ],
        "notes": "Logistics officers manage CSS planning and execution across Classes I–IX. SuppO is typically the primary interface with higher-echelon supply and maintenance.",
    },
    "05": {
        "name": "MAGTF Plans",
        "navmc": None,
        "roles": ["Plans Officer", "Strategy and Plans"],
        "doctrine": [
            "MCWP 5-10 — Marine Corps Planning Process",
            "MCRP 5-10.1 — Commander's Handbook for the MAGTF",
        ],
        "notes": "Plans Marines facilitate the MCPP and develop operational and campaign plans.",
    },
    "06": {
        "name": "Communications",
        "navmc": "NAVMC 3500.56",
        "roles": ["S-6 Officer", "Communications Chief", "Radio Operator"],
        "doctrine": [
            "MCWP 3-40.3 — Communication Systems",
            "MCO 2100.2 — Marine Corps Radio Systems",
        ],
        "notes": "Communications Marines plan, install, operate, and maintain tactical voice and data networks.",
    },
    "08": {
        "name": "Field Artillery",
        "navmc": "NAVMC 3500.7",
        "roles": ["FDO", "Battery Commander", "FSO"],
        "doctrine": [
            "MCWP 3-16 — Fire Support Coordination in the Ground Combat Element",
            "MCRP 3-16.1A — Tactics, Techniques, and Procedures for the FDC",
        ],
        "notes": "Artillery officers and SNCOs plan and coordinate indirect fire support and fire mission execution.",
    },
    "13": {
        "name": "Combat Engineering",
        "navmc": "NAVMC 3500.9",
        "roles": ["Combat Engineer Officer", "Engineer Platoon Commander"],
        "doctrine": [
            "MCWP 3-17 — Engineer Operations",
            "MCRP 3-17.1 — Engineer Field Data",
        ],
        "notes": "Engineer Marines conduct mobility, countermobility, survivability, and general engineering operations.",
    },
    "18": {
        "name": "Tank and Assault Amphibian",
        "navmc": "NAVMC 3500.2",
        "roles": ["AAV Platoon Commander", "Tank Commander"],
        "doctrine": [
            "MCWP 3-12 — Marine Corps Tank Employment",
            "MCWP 3-15.3 — Marine Corps Assault Amphibious Vehicle",
        ],
        "notes": "Assault Amphibian Marines conduct ship-to-shore and over-land operations supporting infantry maneuver.",
    },
    "21": {
        "name": "Ground Ordnance Maintenance",
        "navmc": "NAVMC 3500.19",
        "roles": ["Maintenance Officer", "Maintenance Chief", "Motor T Chief"],
        "doctrine": [
            "TM 4700-15/1 — Ground Equipment Record Procedures",
            "MCO 4790.2 — Vehicle Management",
        ],
        "notes": "Ordnance maintenance Marines keep ground equipment operational, managing PMCS, deadlined equipment, and repair parts.",
    },
    "23": {
        "name": "Ammunition",
        "navmc": "NAVMC 3500.37",
        "roles": ["Ammunition Officer", "Ammo Technician"],
        "doctrine": [
            "MCO 8020.10 — Marine Corps Conventional Ammunition Management",
        ],
        "notes": "Ammunition Marines manage the receipt, storage, issue, and disposal of Class V(W) ammunition.",
    },
    "30": {
        "name": "Supply",
        "navmc": "NAVMC 3500.35",
        "roles": ["S-4 Supply Chief", "SuppO", "Supply Warehouse Marine"],
        "doctrine": [
            "MCO 4400.16 — Unit Supply Policies and Procedures",
            "MCWP 4-11.7 — Classes of Supply",
        ],
        "notes": "Supply Marines manage property accountability, requisitioning, and Classes of Supply distribution.",
    },
    "35": {
        "name": "Motor Transport",
        "navmc": "NAVMC 3500.39",
        "roles": ["Motor Transport Officer", "Motor T Chief", "Vehicle Commander"],
        "doctrine": [
            "MCWP 4-11.3 — Motor Transport Operations",
            "MCO 4790.2 — Vehicle Management",
        ],
        "notes": "Motor transport Marines plan and execute tactical ground movement of personnel and materiel.",
    },
    "40": {
        "name": "Finance",
        "navmc": "NAVMC 3500.3",
        "roles": ["Disbursing Officer", "Finance Chief"],
        "doctrine": [
            "DoD 7000.14-R — DoD Financial Management Regulation (FMR)",
            "MCO 7300.21 — Marine Corps Finance Manual",
        ],
        "notes": "Finance Marines manage military pay, travel claims, and disbursing operations.",
    },
    "43": {
        "name": "Food Service",
        "navmc": "NAVMC 3500.35",
        "roles": ["Food Service Officer", "Mess Chief"],
        "doctrine": [
            "MCO P10110.42 — Marine Corps Food Service Manual",
        ],
        "notes": "Food service Marines plan, prepare, and manage subsistence operations across the unit.",
    },
    "46": {
        "name": "Public Affairs",
        "navmc": "NAVMC 3500.129",
        "roles": ["PAO", "Public Affairs SNCO"],
        "doctrine": [
            "MCWP 3-33.2 — Marine Air-Ground Task Force Public Affairs Operations",
            "MCO 5720.77 — Marine Corps Public Affairs Program",
        ],
        "notes": "PA Marines plan and execute command information, media relations, and community engagement operations.",
    },
    "58": {
        "name": "Military Police",
        "navmc": "NAVMC 3500.25",
        "roles": ["Provost Marshal", "MP Platoon Commander", "Senior MP"],
        "doctrine": [
            "MCWP 3-34.1 — Military Police in Support of the MAGTF",
        ],
        "notes": "MP Marines conduct law enforcement, force protection, area security, and detainee operations.",
    },
    "59": {
        "name": "Electronics Maintenance",
        "navmc": "NAVMC 3500.19",
        "roles": ["Electronics Maintenance Officer", "Calibration Technician"],
        "doctrine": [
            "MCO 4790.2 — Equipment Management",
        ],
        "notes": "Electronics maintenance Marines repair and calibrate avionics, communications, and radar equipment.",
    },
}

_BILLET_CATALOG: dict[str, dict] = {
    "co": {
        "title": "Commanding Officer (CO)",
        "responsibilities": [
            "Mission accomplishment and welfare of assigned Marines and Sailors",
            "METL development, approval, and training execution",
            "Readiness reporting (DRRS-MC) and unit T/P/U assessments",
            "Commander's training brief preparation and delivery",
            "Personnel discipline and administrative actions",
        ],
        "key_pubs": ["MCO 1553.3 — Unit Training Management", "MCO 3000.13 — Force Readiness Reporting"],
    },
    "xo": {
        "title": "Executive Officer (XO)",
        "responsibilities": [
            "Day-to-day operations management; primary deputy to CO",
            "Battle rhythm ownership and staff synchronization",
            "Training plan coordination and drill weekend scheduling",
            "Readiness reporting coordination across staff sections",
            "Administrative and logistical oversight",
        ],
        "key_pubs": ["MCTP 7-20A — Unit Training Guide", "MCRP 5-10.1 — Commander's Handbook"],
    },
    "suppo": {
        "title": "Supply Officer (SuppO)",
        "responsibilities": [
            "Class I–IX supply support and accountability",
            "Property book management and annual inventories",
            "Coordination with higher echelon supply and G-4/S-4",
            "Requisitioning, receiving, and issuing supplies",
            "Tactical logistics planning support to S-3",
        ],
        "key_pubs": [
            "MCO 4400.16 — Unit Supply Policies",
            "MCWP 4-11.7 — Classes of Supply",
            "NAVMC 3500.27 — Logistics T&R Manual",
        ],
    },
    "s-1": {
        "title": "S-1 (Personnel and Administration Officer)",
        "responsibilities": [
            "Personnel accountability and strength reporting",
            "Casualty reporting and notification",
            "Awards, evaluations (FitRep/Counseling) processing",
            "Admin support to staff and subordinate units",
            "Reserve component specific: IDT/AT pay, personnel readiness",
        ],
        "key_pubs": [
            "MCO P1000.6 — Assignment and Classification",
            "MCO 1080.40 — Active Reserve Management",
            "NAVMC 3500.3 — Manpower and Administration T&R",
        ],
    },
    "s-2": {
        "title": "S-2 (Intelligence Officer)",
        "responsibilities": [
            "Intelligence preparation of the battlefield (IPB)",
            "SMEAC and threat analysis products for CO",
            "OSINT collection and synthesis (public sources only)",
            "Counterintelligence and force protection coordination",
            "Training Marines on threat awareness",
        ],
        "key_pubs": [
            "MCWP 2-10 — Intelligence",
            "MCRP 2-10A.6 — MAGTF Intelligence Production",
            "NAVMC 3500.100 — Intelligence T&R Manual",
        ],
    },
    "s-3": {
        "title": "S-3 (Operations Officer)",
        "responsibilities": [
            "Training plan development (LRTP, MRTP, SRTP)",
            "METL management and T/P/U input to CO",
            "MCTIMS UTM — posting training completions and scheduling",
            "Drill weekend schedule development and publication",
            "OPORD, WARNO, FRAGORD production",
        ],
        "key_pubs": [
            "MCTP 7-20A — Unit Training Guide",
            "MCO 1553.3 — Unit Training Management",
            "MCRP 7-20A.1 — Training Plan Design",
            "MCRP 7-20A.5 — Training Data Management",
        ],
    },
    "s-4": {
        "title": "S-4 (Logistics Officer)",
        "responsibilities": [
            "Logistical planning and coordination in support of operations",
            "Class I–IX requirements estimation and sourcing",
            "Vehicle management and PMCS coordination",
            "Supply chain coordination with SuppO and higher G-4",
            "Maintenance tracking and deadline reporting",
        ],
        "key_pubs": [
            "MCWP 4-11 — Tactical Level Logistics",
            "MCO 4790.2 — Vehicle Management",
            "NAVMC 3500.27 — Logistics T&R Manual",
        ],
    },
    "s-6": {
        "title": "S-6 (Communications Officer)",
        "responsibilities": [
            "Communications plan development and PACE plan maintenance",
            "Tactical network architecture and radio net management",
            "COMSEC accountability (KMI/EKMS procedures)",
            "Comms equipment maintenance and readiness tracking",
            "IT and network support at the command post",
        ],
        "key_pubs": [
            "MCWP 3-40.3 — Communication Systems",
            "NAVMC 3500.56 — Communications T&R Manual",
        ],
    },
}

_DIVISION_INFO: dict[str, str] = {
    "1st mardiv": "1st Marine Division — Camp Pendleton, CA. Active component.",
    "2nd mardiv": "2nd Marine Division — Camp Lejeune, NC. Active component.",
    "3rd mardiv": "3rd Marine Division — Okinawa, Japan. Active component.",
    "4th mardiv": "4th Marine Division — Reserve component. Subordinate to MARFORRES. Regiments in TX, LA, CA, and UT.",
    "4th mardiv ": "4th Marine Division — Reserve component. Subordinate to MARFORRES.",
    "marforres": "Marine Forces Reserve (MARFORRES) — New Orleans, LA. Commands all SMCR units.",
    "1st mef": "I Marine Expeditionary Force — Camp Pendleton, CA.",
    "2nd mef": "II Marine Expeditionary Force — Camp Lejeune, NC.",
}


def _normalize(s: str) -> str:
    return s.lower().strip()


def _lookup_mos(mos: str) -> dict | None:
    if not mos:
        return None
    prefix = mos[:2]
    return _MOS_CATALOG.get(prefix)


def _lookup_billet(billet: str) -> dict | None:
    if not billet:
        return None
    normalized = _normalize(billet).replace("/", "-").replace(" ", "-")
    for key, info in _BILLET_CATALOG.items():
        if key in normalized or normalized in key:
            return info
    return None


def _lookup_unit(unit: str) -> str | None:
    if not unit:
        return None
    normalized = _normalize(unit)
    for key, desc in _DIVISION_INFO.items():
        if key in normalized:
            return desc
    return None


def build_research_note(user_key: str, billet: str, unit: str, mos: str) -> str:
    sections: list[str] = [f"# Billet Research — {billet or 'Unknown Billet'}\n"]
    sections.append(f"*Generated for: {user_key} | MOS: {mos or 'not set'} | Unit: {unit or 'not set'}*\n")
    sections.append("*All content is UNCLASSIFIED, derived from publicly available sources. Advisory use only.*\n")

    billet_info = _lookup_billet(billet)
    if billet_info:
        sections.append(f"\n## {billet_info['title']}\n")
        sections.append("**Key responsibilities:**\n")
        for r in billet_info["responsibilities"]:
            sections.append(f"- {r}\n")
        sections.append("\n**Key publications:**\n")
        for pub in billet_info["key_pubs"]:
            sections.append(f"- {pub}\n")
    else:
        sections.append(f"\n## Billet: {billet}\n")
        sections.append("No pre-built reference found for this billet. Add publications and responsibilities manually.\n")

    mos_info = _lookup_mos(mos)
    if mos_info:
        sections.append(f"\n## MOS {mos} — {mos_info['name']}\n")
        if mos_info.get("navmc"):
            mcpel_url = "https://www.marines.mil/News/Publications/MCPEL/Tag/87635/tr-manual/"
            sections.append(f"**T&R Manual:** {mos_info['navmc']} — [Browse MCPEL]({mcpel_url})\n")
        sections.append("\n**Common billets for this MOS:**\n")
        for role in mos_info.get("roles", []):
            sections.append(f"- {role}\n")
        sections.append("\n**Key doctrine:**\n")
        for doc in mos_info.get("doctrine", []):
            sections.append(f"- {doc}\n")
        if mos_info.get("notes"):
            sections.append(f"\n**Notes:** {mos_info['notes']}\n")

    unit_info = _lookup_unit(unit)
    if unit_info:
        sections.append(f"\n## Unit: {unit}\n")
        sections.append(f"{unit_info}\n")
    elif unit:
        sections.append(f"\n## Unit: {unit}\n")
        sections.append(
            "No pre-built reference found for this unit. "
            "Look up lineage and honors at https://www.marines.mil/News/Publications/MCPEL/\n"
        )

    sections.append("\n## SMCR Training Context\n")
    sections.append(
        "- **Authorized training time:** 48 drill periods/year (24 battle assemblies) + 14 days Annual Training\n"
        "- **Usable METL training time per drill weekend:** ~8–12 hours after mandatory training and admin\n"
        "- **Annual Training** is disproportionately valuable — many E-Coded collective events require "
        "sustainment at 6–12 month intervals, aligning with once-yearly AT\n"
        "- **MCTIMS UTM** is the authoritative system for METL management and training event recording "
        "(CAC-authenticated)\n"
        "- **T/P/U ratings** (Trained / Practiced / Untrained) are commander's assessments informed by "
        "MCTIMS CRP data\n"
    )

    sections.append("\n## Reference Links\n")
    sections.append(
        "- [MCPEL — T&R Manuals](https://www.marines.mil/News/Publications/MCPEL/Tag/87635/tr-manual/)\n"
        "- [MCTP 7-20A — Unit Training Guide](https://www.marines.mil/Portals/1/Publications/MCTP%207-20A.pdf)\n"
        "- [MCO 1553.3A — Unit Training Management](https://www.trngcmd.marines.mil/Portals/207/Docs/safety/MCO_1553.3A_UNIT_TRAINING_MANAGEMENT_(UTM).pdf)\n"
        "- [MCRP 7-20A.1 — Training Plan Design](https://www.marines.mil/Portals/1/Publications/MCRP%207-20A.1.pdf)\n"
        "- [DRRS-MC Commanders Readiness Handbook](https://www.usmcu.edu/Portals/218/Commanders_Readiness_Handbook_2020-09-16.pdf)\n"
    )

    return "".join(sections)
