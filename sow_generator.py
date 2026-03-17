"""
Generate SOW content using Anthropic Claude.
Takes extracted brief fields + call transcript -> returns structured SOW dict.
"""
import json
import unicodedata
import anthropic
from brief_extractor import format_for_prompt


def _safe_text(text: str) -> str:
    """
    Normalize unicode text to ASCII-safe form before sending to the API.
    Converts common smart quotes, dashes, symbols to plain ASCII equivalents.
    Unknown non-ASCII chars are dropped rather than crashing.
    """
    if not text:
        return text
    text = unicodedata.normalize('NFKC', text)
    _subs = {
        '\u00d7': 'x',
        '\u00f7': '/',
        '\u2013': '-',
        '\u2014': '--',
        '\u2018': "'",
        '\u2019': "'",
        '\u201c': '"',
        '\u201d': '"',
        '\u2026': '...',
        '\u00a0': ' ',
        '\u00ae': '(R)',
        '\u2122': '(TM)',
        '\u00a9': '(C)',
        '\u2192': '->',
        '\u2190': '<-',
        '\u2022': '-',
        '\u00b7': '-',
    }
    for char, sub in _subs.items():
        text = text.replace(char, sub)
    # Final safety net: drop any remaining non-ASCII
    return text.encode('ascii', errors='ignore').decode('ascii')


SYSTEM_PROMPT = """You are a senior strategist and account lead at Adchor, a creative agency built around the Transformative Acceleration Blueprint -- a three-phase methodology:

- TARGET PHASE: Audience, positioning, competitive differentiation, strategic foundation
- BUILD PHASE: Creative development, messaging architecture, production
- ACCELERATE PHASE: Activation, distribution, performance optimization

Your task is to draft a professional, client-ready Statement of Work based on data from a filled creative brief and/or a call transcript. Your output must be:
- Specific to this client and project (never generic)
- Written in confident agency voice -- clear, direct, professional
- Structured for editing before sending
- Realistic about scope -- do not over-promise

Output ONLY valid JSON. No markdown fences, no explanation text."""


def generate_sow_content(brief_fields: dict, transcript: str, api_key: str) -> dict:
    """
    Call Claude to generate structured SOW content.
    Returns a dict with all sections needed to build the SOW PDF.
    """
    client = anthropic.Anthropic(api_key=api_key)

    brief_text = _safe_text(format_for_prompt(brief_fields)) if brief_fields else "No brief data provided."
    transcript_text = _safe_text(transcript.strip()) if transcript else "No transcript provided."

    prompt = f"""Generate a complete SOW from the following inputs:

=== CREATIVE BRIEF ===
{brief_text}

=== CALL TRANSCRIPT ===
{transcript_text}

Return ONLY this JSON (no markdown, no explanation):
{{
    "client_name": "client name from brief",
    "project_name": "project or campaign name",
    "account_lead": "account lead name",
    "business_owner": "business owner name",
    "final_deadline": "deadline from brief",
    "budget_range": "budget from brief",
    "version": "v1.0",
    "project_overview": "3-4 sentence executive summary. Open with the business opportunity or challenge. Close with what Adchor will deliver and why it matters now.",
    "why_now": "1-2 sentences on the specific trigger -- what changed, what window exists, what is at stake if this doesn't happen.",
    "objective": "Primary objective, specific and measurable where possible.",
    "audience": "Specific audience description from the brief.",
    "core_message": "Core message if provided in brief.",
    "scope_sections": [
        {{
            "title": "Specific, descriptive section title (e.g. 'Educational Animated Video - Primary Asset')",
            "description": "2-3 sentences describing what Adchor will create, the strategic intent, and why this deliverable drives the objective.",
            "services": [
                "Specific service included -- be concrete, not generic",
                "Another specific service",
                "Another specific service",
                "Another specific service"
            ],
            "deliverables": [
                "Primary deliverable with format/spec (e.g. One animated video, 90 seconds, 16:9, MP4)",
                "Secondary deliverable if applicable"
            ]
        }}
    ],
    "review_rounds": "number of review rounds (default 2 if not specified)",
    "timeline_notes": "Key timeline considerations, milestone dependencies, or constraints noted in the brief/transcript.",
    "assumptions": [
        "Client provides approved brand assets, copy, and access to subject matter experts within 5 business days of project kickoff.",
        "All client feedback is consolidated into a single document per review round. Verbal-only feedback will not be accepted.",
        "Final copy and messaging approved by client before production begins.",
        "Add 1-2 more project-specific assumptions based on the brief/transcript."
    ],
    "out_of_scope": [
        "Specific item NOT included based on what was discussed",
        "Another specific out-of-scope boundary",
        "Add items that prevent scope creep for this specific project"
    ],
    "adchor_notes": "Internal note: 1 sentence on the strategic angle Adchor should lean into for this project."
}}

Create one scope_section per major deliverable group. If the brief mentions multiple distinct deliverables (e.g. two videos + a social package), create separate sections for each. Be specific -- use actual project details, not placeholders."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()

    # Extract JSON from response (handles cases where model adds explanation)
    start = response_text.find('{')
    end = response_text.rfind('}') + 1
    if start >= 0 and end > start:
        return json.loads(response_text[start:end])

    raise ValueError(f"Claude response did not contain valid JSON. Preview: {response_text[:300]}")


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
