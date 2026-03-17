"""
Extract AcroForm field values from a filled Adchor Creative Brief PDF.
Uses pypdf to read named fields — same field names defined in build_brief.py.
"""
import io
import pypdf

# Human-readable labels for brief field names
FIELD_LABELS = {
    'client_name':             'Client Name',
    'project_name':            'Project / Campaign Name',
    'brief_date':              'Date',
    'brief_version':           'Version',
    'account_lead':            'Account Lead',
    'project_manager':         'Project Manager',
    'primary_contact':         'Primary Contact',
    'decision_maker':          'Final Decision-Maker',
    'business_owner':          'Business Owner / Success Owner',
    'client_contributors':     'Client Contributors',
    'why_now':                 'Why Is This Happening Now',
    'business_challenge':      'Business Challenge',
    'objective':               'Objective',
    'audience':                'Target Audience',
    'audience_today':          'What Audience Believes Today',
    'audience_after':          'What We Want Them to Think/Feel/Do',
    'emotional_outcome':       'Emotional Outcome',
    'core_message':            'Core Message',
    'brand_positioning':       'Brand Positioning',
    'tone_words':              'Tone of Voice',
    'competitive_context':     'Competitive Context',
    'brand_differentiator':    'Brand Differentiator',
    'brand_exclusions':        'Brand Exclusions',
    'mandatory_inclusions':    'Mandatory Inclusions',
    'already_tried':           'Already Tried',
    'existing_assets':         'Existing Assets',
    'cta':                     'Call to Action',
    'tech_requirements':       'Technical Requirements',
    'deadline_driver':         'Deadline Driver',
    'final_deadline':          'Final Deadline',
    'final_approver':          'Final Approver',
    'reviewers':               'Reviewers',
    'feedback_owner':          'Feedback Owner',
    'feedback_turnaround':     'Feedback Turnaround',
    'feedback_protocol':       'Feedback Protocol',
    'budget_range':            'Budget Range',
    'kpi_r1_c1':               'KPI 1',
    'kpi_r1_c3':               'KPI 1 Target',
    'kpi_r2_c1':               'KPI 2',
    'kpi_r2_c3':               'KPI 2 Target',
    'deliverable_r1_c1':       'Deliverable 1',
    'deliverable_r2_c1':       'Deliverable 2',
    'deliverable_r3_c1':       'Deliverable 3',
}

# Priority fields for SOW generation — passed to Claude in a focused block
PRIORITY_FIELDS = [
    'client_name', 'project_name', 'account_lead', 'business_owner',
    'final_deadline', 'budget_range', 'why_now', 'business_challenge',
    'objective', 'audience', 'emotional_outcome', 'core_message',
    'brand_differentiator', 'cta', 'tech_requirements', 'feedback_protocol',
    'kpi_r1_c1', 'kpi_r1_c3', 'kpi_r2_c1', 'kpi_r2_c3',
    'deliverable_r1_c1', 'deliverable_r2_c1', 'deliverable_r3_c1',
]


def extract_brief_fields(pdf_bytes: bytes) -> dict:
    """
    Extract all filled AcroForm field values from the brief PDF.
    Returns a dict of {field_name: value} for non-empty fields.
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        raw_fields = reader.get_fields()

        if not raw_fields:
            return {}

        extracted = {}
        for name, field_obj in raw_fields.items():
            value = field_obj.get('/V')
            if value is None:
                continue

            # Resolve indirect objects
            if hasattr(value, 'get_object'):
                value = value.get_object()

            value_str = str(value).strip()

            # Skip empty / unchecked / null
            if not value_str or value_str in ('/Off', 'None', '/None', '/'):
                continue

            # Strip leading slash from NameObjects (e.g. radio button values)
            if value_str.startswith('/'):
                value_str = value_str[1:]

            extracted[name] = value_str

        return extracted

    except Exception as e:
        return {'_error': str(e)}


def format_for_prompt(fields: dict) -> str:
    """
    Format extracted fields into a clean text block for the Claude prompt.
    Priority fields come first, then everything else.
    """
    lines = []

    # Priority fields first
    for key in PRIORITY_FIELDS:
        if key in fields:
            label = FIELD_LABELS.get(key, key.replace('_', ' ').title())
            lines.append(f"{label}: {fields[key]}")

    # Remaining fields
    for key, value in fields.items():
        if key not in PRIORITY_FIELDS and not key.startswith('_'):
            label = FIELD_LABELS.get(key, key.replace('_', ' ').title())
            lines.append(f"{label}: {value}")

    return "\n".join(lines)
            return {}

        extracted = {}
        for name, field_obj in raw_fields.items():
            value = field_obj.get('/V')
            if value is None:
                continue

            # Resolve indirect objects
            if hasattr(value, 'get_object'):
                value = value.get_object()

            value_str = str(value).strip()

            # Skip empty / unchecked / null
            if not value_str or value_str in ('/Off', 'None', '/None', '/'):
                continue

            # Strip leading slash from NameObjects (e.g. radio button values)
            if value_str.startswith('/'):
                value_str = value_str[1:]

            extracted[name] = value_str

        return extracted

    except Exception as e:
        return {'_error': str(e)}


def format_for_prompt(fields: dict) -> str:
    """
    Format extracted fields into a clean text block for the Claude prompt.
    Priority fields come first, then everything else.
    """
    lines = []

    # Priority fields first
    for key in PRIORITY_FIELDS:
        if key in fields:
            label = FIELD_LABELS.get(key, key.replace('_', ' ').title())
            lines.append(f"{label}: {fields[key]}")

    # Remaining fields
    for key, value in fields.items():
        if key not in PRIORITY_FIELDS and not key.startswith('_'):
            label = FIELD_LABELS.get(key, key.replace('_', ' ').title())
            lines.append(f"{label}: {value}")

    return "\n".join(lines)
