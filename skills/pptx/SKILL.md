---
name: pptx
description: Use when creating, editing, or extracting content from PowerPoint (.pptx) files. Handles staff briefings, decision briefs, back-briefs, AARs, and MDMP products in slide format.
---

# PPTX

Sourced from: https://www.skills.sh/anthropics/skills/pptx (anthropics/skills)

## Purpose

Handle the full .pptx lifecycle for military staff products: reading and extracting content from existing decks, editing presentations via template unpacking and repacking, and creating new decks from scratch.

## When To Use

- Building a decision brief, back-brief, command update brief, or MDMP slide package.
- Extracting text or structure from an existing .pptx template or prior brief.
- Converting a planning cell output, AAR, or staff product scaffold into slides.
- Any task where the deliverable is a .pptx file.

## When Not To Use

- When a Word document (naval letter, memorandum, OPORD) is the correct format — use the `docx` skill instead.
- When the audience only needs a markdown or text output, not slides.

## Workflow

1. **Read** — If an existing .pptx is provided, extract text, structure, and slide count first. Do not assume the template structure.
2. **Plan** — Identify the slide count, section structure, and key messages before writing any content.
3. **Create or Edit** — Use PptxGenJS for new decks. For edits, unpack the .pptx (it is a ZIP), modify XML, and repack. Prefer template reuse over building from scratch.
4. **QA** — Before delivering, check: no placeholder text remaining, no overlapping elements, no text overflow, sufficient contrast, consistent typography.

## Design Rules

- Use one of the 10 curated palettes from the anthropics/skills pptx skill rather than default Office themes.
- Prefer clean, high-contrast layouts. Military briefs prioritise legibility over decoration.
- One message per slide when building decision or command-update briefs.
- Action items and decisions belong on their own slide with clear owner/suspense fields.

## Staff Product Mapping

| Product | Slide structure |
|---|---|
| Decision brief | Situation → Problem → COA analysis → Recommended COA → Decision required |
| Back-brief | Task → Understanding → Plan → Risks → Questions |
| CUB | Status → Changes → Decisions → Near-term requirements |
| AAR | Standards → Observations → Sustains → Improves → Actions |
| OPORD brief | Situation → Mission → Execution → Admin/Log → Command/Signal |

## Safety And Review Rules

- All outputs are advisory drafts requiring human review.
- Do not include classified, CUI, personally identifying, or OPSEC-sensitive content.
- Source citations belong in speaker notes, not on the slide face.

## Dependencies

Requires Node.js and PptxGenJS (`npm install pptxgenjs`) for creating decks from scratch.
For extraction and editing, Python with `python-pptx` (`pip install python-pptx`) works without Node.
