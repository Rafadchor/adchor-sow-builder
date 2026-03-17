"""
Generate SOW content using Anthropic Claude.
Takes extracted brief fields + call transcript -> returns structured SOW dict.
"""
import json
import unicodedata
import requests as _requests
from brief_extractor import format_for_prompt


def _safe_text(text: str) -> str:
    """
    Strip all non-ASCII characters from text before sending to the API.
    Converts common punctuation to ASCII equivalents first, then drops the rest.
    """
    if not text:
        return text
    text = unicodedata.normalize('NFKC', text)
    # Replace common non-ASCII punctuation with ASCII equivalents
    _subs = {
        '\u00d7': 'x',      # multiplication sign
        '\u00f7': '/',      # division sign
        '\u2013': '-',      # en dash
        '\u2014': '--',     # em dash
        '\u2015': '--',     # horizontal bar
        '\u2018': "'",      # left single quote
        '\u2019': "'",      # right single quote
        '\u201a': ',',      # low-9 quotation mark
        '\u201c': '"',      # left double quote
        '\u201d': '"',      # right double quote
        '\u2026': '...',    # ellipsis
        '\u00a0': ' ',      # non-breaking space
        '\u00ae': '(R)',    # registered trademark
        '\u2122': '(TM)',   # trademark
        '\u00a9': '(C)',    # copyright
        '\u2192': '->',     # right arrow
        '\u2190': '<-',     # left arrow
        '\u2022': '-',      # bullet
        '\u00b7': '-',      # middle dot
        '\u00b0': ' deg',   # degree sign
        '\u00bd': '1/2',    # one half
        '\u00bc': '1/4',    # one quarter
        '\u00be': '3/4',    # three quarters
        '\u2264': '<=',     # less than or equal
        '\u2265': '>=',     # greater than or equal
        '\u00e9': 'e',      # e acute
        '\u00e8': 'e',      # e grave
        '\u00e0': 'a',      # a grave
        '\u00f3': 'o',      # o acute
        '\u00fa': 'u',      # u acute
        '\u00ed': 'i',      # i acute
        '\u00f1': 'n',      # n tilde
    }
    for char, sub in _subs.items():
        text = text.replace(char, sub)
    # Final hard strip: drop anything still non-ASCII
    return text.encode('ascii', errors='ignore').decode('ascii')


SYSTEM_PROMPT = (
    "You are a senior strategist and account lead at Adchor, a creative agency built around "
    "the Transformative Acceleration Blueprint -- a three-phase methodology:\n\n"
    "- TARGET PHASE: Audience, positioning, competitive differentiation, strategic foundation\n"
    "- BUILD PHASE: Creative development, messaging architecture, production\n"
    "- ACCELERATE PHASE: Activation, distribution, performance optimization\n\n"
    "Your task is to draft a professional, client-ready Statement of Work based on data from "
    "a filled creative brief and/or a call transcript. Your output must be:\n"
    "- Specific to this client and project (never generic)\n"
    "- Written in confident agency voice -- clear, direct, professional\n"
    "- Structured for editing before sending\n"
    "- Realistic about scope -- do not over-promise\n\n"
    "Output ONLY valid JSON. No markdown fences, no explanation text."
)


def generate_sow_content(brief_fields: dict, transcript: str, api_key: str) -> dict:
    """
    Call Claude to generate structured SOW content.
    Returns a dict with all sections needed to build the SOW PDF.
    """
    brief_text = _safe_text(format_for_prompt(brief_fields)) if brief_fields else "No brief data provided."
    transcript_text = _safe_text(transcript.strip()) if transcript else "No transcript provided."

    prompt = (
        "Generate a complete SOW from the following inputs:\n\n"
        "=== CREATIVE BRIEF ===\n"
        + brief_text +
        "\n\n=== CALL TRANSCRIPT ===\n"
        + transcript_text +
        "\n\nReturn ONLY this JSON (no markdown, no explanation):\n"
        '{\n'
        '    "client_name": "client name from brief",\n'
        '    "project_name": "project or campaign name",\n'
        '    "account_lead": "account lead name",\n'
        '    "business_owner": "business owner name",\n'
        '    "final_deadline": "deadline from brief",\n'
        '    "budget_range": "budget from brief",\n'
        '    "version": "v1.0",\n'
        '    "project_overview": "3-4 sentence executive summary. Open with the business opportunity or challenge. Close with what Adchor will deliver and why it matters now.",\n'
        '    "why_now": "1-2 sentences on the specific trigger -- what changed, what window exists, what is at stake if this does not happen.",\n'
        '    "objective": "Primary objective, specific and measurable where possible.",\n'
        '    "audience": "Specific audience description from the brief.",\n'
        '    "core_message": "Core message if provided in brief.",\n'
        '    "scope_sections": [\n'
        '        {\n'
        '            "title": "Specific, descriptive section title (e.g. Educational Animated Video - Primary Asset)",\n'
        '            "description": "2-3 sentences describing what Adchor will create, the strategic intent, and why this deliverable drives the objective.",\n'
        '            "services": [\n'
        '                "Specific service included -- be concrete, not generic",\n'
        '                "Another specific service",\n'
        '                "Another specific service"\n'
        '            ],\n'
        '            "deliverables": [\n'
        '                "Primary deliverable with format/spec (e.g. One animated video, 90 seconds, 16:9, MP4)",\n'
        '                "Secondary deliverable if applicable"\n'
        '            ]\n'
        '        }\n'
        '    ],\n'
        '    "review_rounds": "number of review rounds (default 2 if not specified)",\n'
        '    "timeline_notes": "Key timeline considerations, milestone dependencies, or constraints noted in the brief/transcript.",\n'
        '    "assumptions": [\n'
        '        "Client provides approved brand assets, copy, and access to subject matter experts within 5 business days of project kickoff.",\n'
        '        "All client feedback is consolidated into a single document per review round. Verbal-only feedback will not be accepted.",\n'
        '        "Final copy and messaging approved by client before production begins.",\n'
        '        "Add 1-2 more project-specific assumptions based on the brief/transcript."\n'
        '    ],\n'
        '    "out_of_scope": [\n'
        '        "Specific item NOT included based on what was discussed",\n'
        '        "Another specific out-of-scope boundary",\n'
        '        "Add items that prevent scope creep for this specific project"\n'
        '    ],\n'
        '    "adchor_notes": "Internal note: 1 sentence on the strategic angle Adchor should lean into for this project."\n'
        '}\n\n'
        "Create one scope_section per major deliverable group. If the brief mentions multiple distinct deliverables "
        "(e.g. two videos + a social package), create separate sections for each. "
        "Be specific -- use actual project details, not placeholders."
    )

    # Final safety sweep — strip any non-ASCII that survived earlier processing
    _safe_system = _safe_text(SYSTEM_PROMPT)
    _safe_prompt = _safe_text(prompt)

    # Use requests directly -- bypasses h11 ASCII encoding limitation
    resp = _requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 4000,
            "system": _safe_system,
            "messages": [{"role": "user", "content": _safe_prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    response_text = resp.json()["content"][0]["text"].strip()

    start = response_text.find('{')
    end = response_text.rfind('}') + 1
    if start >= 0 and end > start:
        return json.loads(response_text[start:end])

    raise ValueError("Claude response did not contain valid JSON. Preview: " + response_text[:300])


def get_empty_sow() -> dict:
    """Return a blank SOW structure for manual entry."""
    return {
        "client_name": "",
        "project_name": "",
        "account_lead": "",
        "business_owner": "",
        "final_deadline": "",
        "budget_range": "",
        "version": "v1.0",
        "project_overview": "",
        "why_now": "",
        "objective": "",
        "audience": "",
        "core_message": "",
        "scope_sections": [
            {
                "title": "",
                "description": "",
                "services": [],
                "deliverables": []
            }
        ],
        "review_rounds": "2",
        "timeline_notes": "",
        "assumptions": [
            "Client provides approved brand assets and access to subject matter experts within 5 business days of project kickoff.",
            "All client feedback is consolidated into a single document per review round.",
            "Final copy and messaging approved by client before production begins.",
        ],
        "out_of_scope": [],
        "adchor_notes": "",
    }
