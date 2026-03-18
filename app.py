"""
Adchor SOW Builder -- Streamlit Web App
Team URL: deploy to Streamlit Community Cloud or sow.adchor.com

Flow:
  Step 1 -- Upload filled creative brief PDF + call transcript
  Step 2 -- Review & edit AI-generated SOW content
  Step 3 -- Build pricing (live auto-total, growing library)
  Step 4 -- Download PDF → send via Adobe Sign
"""
import streamlit as st
import json
import os
import sys
import base64
from pathlib import Path
from datetime import datetime

# ── Ensure app directory is always in sys.path ────────────────────────────────
_APP_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

# ── Import all app modules upfront (no lazy imports -- prevents runpy issues) ──
from brief_extractor import extract_brief_fields, format_for_prompt
from sow_generator import generate_sow_content, get_empty_sow
from sow_pdf import build_sow_pdf

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Adchor SOW Builder",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Adchor Brand CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800;900&display=swap');

/* ── Global ── */
html, body, [class*="css"],
.stMarkdown, .stTextInput, .stTextArea,
.stSelectbox, .stButton, .stNumberInput,
.stFileUploader, p, span, div, label {
    font-family: 'Montserrat', sans-serif !important;
}

/* Preserve Material Icons font */
[data-testid="stIconMaterial"] {
    font-family: 'Material Symbols Rounded', 'Material Icons', 'Material Icons Round' !important;
}

/* ── App background ── */
.stApp { background: #0a0c12 !important; }
[data-testid="stAppViewBlockContainer"] { background: #0a0c12; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #000000 !important;
    border-right: 1px solid #1a1d2e !important;
}
[data-testid="stSidebar"] > div { padding-top: 24px !important; }

/* ── Sidebar header ── */
.adchor-header { padding: 0 0 20px; border-bottom: 1px solid #1a1d2e; margin-bottom: 16px; }
.adchor-logomark {
    display: inline-block;
    background: #014bf7;
    color: white;
    font-size: 15px;
    font-weight: 900;
    width: 34px; height: 34px;
    border-radius: 8px;
    text-align: center;
    line-height: 34px;
    letter-spacing: -1px;
    margin-bottom: 10px;
    box-shadow: 0 0 20px rgba(1,75,247,0.5);
}
.adchor-wordmark {
    color: #ffffff;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin: 0; line-height: 1;
}
.adchor-subtext {
    color: #14a4fe;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin: 4px 0 0;
}

/* ── Step pills ── */
.step-row { display: flex; flex-direction: column; gap: 5px; margin: 4px 0; }
.pill {
    padding: 9px 14px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    display: flex; align-items: center; gap: 8px;
    transition: all 0.2s;
}
.pill-done    { background: rgba(0,255,121,0.08); color: #00ff79; border: 1px solid rgba(0,255,121,0.25); }
.pill-active  { background: #014bf7; color: white; border: 1px solid #014bf7; box-shadow: 0 4px 14px rgba(1,75,247,0.4); }
.pill-pending { background: transparent; color: #3a3f52; border: 1px solid #1a1d2e; }

/* ── Section header bar ── */
.sec-bar {
    background: linear-gradient(90deg, #014bf7 0%, #021de0 100%);
    color: white;
    padding: 13px 22px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin: 0 0 18px;
    box-shadow: 0 6px 24px rgba(1,75,247,0.3);
}

/* ── Scope block header ── */
.scope-header {
    background: #014bf7;
    color: white;
    padding: 11px 18px;
    border-radius: 8px 8px 0 0;
    font-weight: 700;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-top: 14px;
    box-shadow: 0 4px 12px rgba(1,75,247,0.25);
}

/* ── Pricing total ── */
.pricing-total {
    background: linear-gradient(135deg, #021de0 0%, #014bf7 100%);
    color: white;
    padding: 18px 22px;
    border-radius: 12px;
    text-align: right;
    font-size: 22px;
    font-weight: 800;
    margin-top: 14px;
    box-shadow: 0 8px 28px rgba(1,75,247,0.35);
    border: 1px solid rgba(20,164,254,0.3);
    letter-spacing: -0.5px;
}
.pricing-total .sub { font-size: 12px; opacity: 0.65; font-weight: 500; letter-spacing: 0; }

/* ── Info box ── */
.info-box {
    background: #0f111a;
    border: 1px solid #1e2235;
    border-left: 4px solid #014bf7;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0 14px;
    font-size: 13px;
    color: #c8ccd8;
}

/* ── Download CTA ── */
.dl-note {
    background: rgba(0,255,121,0.05);
    border: 1px solid rgba(0,255,121,0.2);
    border-radius: 10px;
    padding: 16px 20px;
    margin-top: 14px;
    font-size: 13px;
    color: #c8ccd8;
}

/* ── AI reword box ── */
.ai-box {
    background: #0d0f1a;
    border: 1px solid #1e2540;
    border-left: 4px solid #14a4fe;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 6px 0 10px;
    font-size: 12px;
    color: #9aa0b4;
    white-space: pre-wrap;
    word-break: break-word;
    line-height: 1.6;
}

/* ── Input fields ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: #0f111a !important;
    border: 1px solid #1e2235 !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 13px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #014bf7 !important;
    box-shadow: 0 0 0 2px rgba(1,75,247,0.15) !important;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"] {
    background: #014bf7 !important;
    border: none !important;
    box-shadow: 0 4px 16px rgba(1,75,247,0.4) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #0240d4 !important;
    box-shadow: 0 6px 22px rgba(1,75,247,0.6) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #1e2235 !important;
    color: #9aa0b4 !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: #014bf7 !important;
    color: white !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #0f111a !important;
    border: 1.5px dashed #1e2235 !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #014bf7 !important;
}

/* ── Dividers ── */
hr { border-color: #1a1d2e !important; margin: 16px 0 !important; }

/* ── Success/warning/error ── */
.stSuccess { background: rgba(0,255,121,0.08) !important; border-color: rgba(0,255,121,0.3) !important; color: #00ff79 !important; }
.stAlert { border-radius: 8px !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #0f111a !important;
    border: 1px solid #1e2235 !important;
    border-radius: 10px !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #0f111a !important;
    border: 1px solid #1e2235 !important;
    border-radius: 8px !important;
    color: #e8eaf0 !important;
}

/* ── Caption/small text ── */
.stCaption { color: #5a6278 !important; font-size: 12px !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0a0c12; }
::-webkit-scrollbar-thumb { background: #1e2235; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #014bf7; }
</style>
""", unsafe_allow_html=True)

# ── Base directory (works with both direct run and runpy) ─────────────────────
_BASE_DIR = Path(__file__).parent if "__file__" in dir() else Path(os.getcwd())

# ── Pricing Library (load once per session) ───────────────────────────────────
LIBRARY_PATH = _BASE_DIR / "pricing_library.json"

def load_library():
    if LIBRARY_PATH.exists():
        with open(LIBRARY_PATH) as f:
            return json.load(f)
    return {"items": []}


# ════════════════════════════════════════════════════════════════════════════════
# NEW: AI Reword Helper
# ════════════════════════════════════════════════════════════════════════════════
def _ai_reword(text: str, instruction: str, api_key: str) -> str:
    """Call Claude to reword/improve a piece of SOW text."""
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                "You are a professional copywriter for a creative agency. "
                "You write polished, client-facing statements of work.\n\n"
                f"Task: {instruction}\n\n"
                f"Text to improve:\n{text}\n\n"
                "Return only the improved text — no preamble, no explanation, "
                "no markdown formatting, no code fences."
            ),
        }],
    )
    return msg.content[0].text.strip()


# ════════════════════════════════════════════════════════════════════════════════
# NEW: Widget keys that must be cleared when resetting a SOW
# ════════════════════════════════════════════════════════════════════════════════
_SOW_FIELD_WIDGET_KEYS = [
    "ta_why_now", "ta_project_overview", "ta_core_message",
    "ta_assumptions", "ta_out_of_scope", "ta_timeline_notes",
]
_AI_WIDGET_KEYS = [
    "ai_field_select", "ai_preset", "ai_custom_instr",
    "ai_input_text", "ai_result_area",
]


# ════════════════════════════════════════════════════════════════════════════════
# NEW: Centralised reset helper (used by sidebar + Done button)
# ════════════════════════════════════════════════════════════════════════════════
def _reset_sow_state():
    """Full SOW workflow reset — preserves pricing_library and api_key."""
    reset_vals = {
        "step": 1,
        "brief_fields": {},
        "transcript": "",
        "sow_data": None,
        "pricing_items": [],
        "sow_discount": 0,
        "sow_total": 0,
        # new keys
        "pdf_downloaded": False,
        "ai_reword_result": "",
        "ai_reword_target": "",
        "ai_reword_widget_key": None,
        "ai_reword_field_type": "",
        "ai_input_text": "",
    }
    for k, v in reset_vals.items():
        st.session_state[k] = v
    # Clear SOW field widget state so they re-initialise with fresh sow_data
    for k in _SOV_FIELD_WIDGET_KEYS + _AI_WIDGET_KEYS:
        st.session_state.pop(k, None)
    # Clear scope-section widget keys (support up to 30 sections)
    for i in range(30):
        for k in [f"st_{i}", f"sd_{i}", f"ss_{i}", f"del_{i}"]:
            st.session_state.pop(k, None)


# ── Session State Init ────────────────────────────────────────────────────────
defaults = {
    "step": 1,
    "brief_fields": {},
    "transcript": "",
    "sow_data": None,
    "pricing_items": [],
    "sow_discount": 0,
    "sow_total": 0,
    "pricing_library": load_library(),
    # ── NEW keys ──────────────────────────────────────────────────────────────
    "pdf_downloaded": False,      # True only after the download button is clicked
    "ai_reword_result": "",       # Stores Claude's latest reword suggestion
    "ai_reword_target": "",       # sow field key that was targeted
    "ai_reword_widget_key": None, # widget key for the targeted field
    "ai_reword_field_type": "",   # "text" | "list"
    "ai_input_text": "",          # content in the AI reword input box
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    _logo_path = _BASE_DIR / 'assets' / 'logo.png'
    _logo_html = ""
    if _logo_path.exists():
        _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
        _logo_html = f'<img src="data:image/png;base64,{_logo_b64}" style="width:100%;max-width:200px;display:block;margin:0 auto 10px;" />'
    st.markdown(f"""
    {_logo_html}
    <div style="border-bottom:1px solid #1a1d2e; padding-bottom:14px; margin-bottom:14px; margin-top:2px;">
        <span style="color:#14a4fe; font-size:10px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; font-family:'Montserrat',sans-serif;">SOW Builder</span>
    </div>
    """, unsafe_allow_html=True)

    # Step indicators
    step_labels = ["1 Upload", "2 Content", "3 Pricing", "4 Download"]
    pills_html = '<div class="step-row">'
    for i, lbl in enumerate(step_labels, 1):
        if i < st.session_state.step:
            pills_html += f'<span class="pill pill-done">✓ {lbl}</span>'
        elif i == st.session_state.step:
            pills_html += f'<span class="pill pill-active">{lbl}</span>'
        else:
            pills_html += f'<span class="pill pill-pending">{lbl}</span>'
    pills_html += '</div>'
    st.markdown(pills_html, unsafe_allow_html=True)
    st.divider()

    # API Key -- loaded once from Streamlit Secrets or environment, never shown to users
    def _load_api_key():
        try:
            return st.secrets["ANTHROPIC_API_KEY"]
        except Exception:
            pass
        return os.environ.get("ANTHROPIC_API_KEY", "")

    if "api_key" not in st.session_state or not st.session_state.api_key:
        st.session_state.api_key = _load_api_key()

    if not st.session_state.api_key:
        st.markdown("""
        <div style="background:rgba(255,60,60,0.07);border:1px solid rgba(255,60,60,0.25);
            border-radius:8px;padding:10px 14px;font-size:11px;color:#ff6b6b;">
            ⚠ API key not configured.<br>
            <span style="color:#5a6278;">Contact your Adchor admin.</span>
        </div>""", unsafe_allow_html=True)
    st.divider()

    # MODIFIED: use centralised reset helper
    if st.button("↺ Start New SOW", use_container_width=True):
        _reset_sow_state()
        st.rerun()

    st.markdown("<div style='margin-top:12px;color:#2a2d3e;font-size:10px;font-weight:600;letter-spacing:1px;text-transform:uppercase;'>Adchor™ · 2026</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 -- INPUT  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.markdown('<div class="sec-bar">STEP 1 -- UPLOAD BRIEF & TRANSCRIPT</div>', unsafe_allow_html=True)
    st.caption("Upload the filled creative brief and paste the call transcript. Claude will extract everything and draft the SOW.")

    col_brief, col_trans = st.columns(2)

    with col_brief:
        st.markdown("#### Creative Brief PDF")
        brief_file = st.file_uploader(
            "Upload filled Adchor Creative Brief (.pdf)",
            type=["pdf"],
            label_visibility="collapsed",
        )
        if brief_file:
            fields = extract_brief_fields(brief_file.read())
            if '_error' in fields:
                st.error(f"Could not read PDF: {fields['_error']}")
            elif fields:
                st.success(f"✓ {len(fields)} fields extracted from brief")
                with st.expander("Preview extracted data"):
                    for k, v in fields.items():
                        if v:
                            st.text(f"{k.replace('_',' ').title()}: {v}")
                st.session_state.brief_fields = fields
            else:
                st.warning("No filled fields found -- brief may not be completed yet.")
                st.session_state.brief_fields = {}

    with col_trans:
        st.markdown("#### Call Transcript")
        source = st.radio("Source", ["Paste text", "Upload .txt"], horizontal=True, label_visibility="collapsed")
        if source == "Paste text":
            transcript = st.text_area(
                "Paste Zoom / Teams transcript",
                height=220,
                placeholder="Paste the full call transcript here. Claude will extract decisions, requirements, and context...",
                label_visibility="collapsed",
            )
        else:
            tf = st.file_uploader("Upload .txt transcript", type=["txt"], label_visibility="collapsed")
            transcript = tf.read().decode("utf-8") if tf else ""
            if transcript:
                st.success(f"✓ {len(transcript.split())} words loaded")
        st.session_state.transcript = transcript

    st.divider()
    col_skip, col_gen = st.columns([1, 1])
    with col_skip:
        if st.button("Skip AI -- Enter Manually", use_container_width=True):
            st.session_state.sow_data = get_empty_sow()
            st.session_state.step = 2
            st.rerun()
    with col_gen:
        has_input = bool(st.session_state.brief_fields or st.session_state.transcript)
        has_key   = bool(st.session_state.get("api_key"))
        disabled  = not has_input
        if st.button("⚡ Generate SOW with Claude", use_container_width=True, type="primary", disabled=disabled):
            if not has_key:
                st.error("AI generation is not available -- API key not configured. Contact your Adchor admin.")
            else:
                with st.spinner("Claude is reading your brief and transcript -- drafting the SOW..."):
                    try:
                        sow = generate_sow_content(
                            st.session_state.brief_fields,
                            st.session_state.transcript,
                            st.session_state.api_key,
                        )
                        st.session_state.sow_data = sow
                        st.session_state.step = 2
                        st.rerun()
                    except Exception as e:
                        import traceback as _tb
                        st.error(f"Generation failed: {e}")
                        with st.expander("Full error details"):
                            st.code(_tb.format_exc())
        if disabled:
            st.caption("Upload a brief or paste a transcript to continue.")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 -- REVIEW & EDIT CONTENT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown('<div class="sec-bar">STEP 2 -- REVIEW & EDIT SOW CONTENT</div>', unsafe_allow_html=True)
    st.caption("All fields are editable. Refine Claude's draft before moving to pricing.")

    sow = st.session_state.sow_data or {}

    # ── Client Details ────────────────────────────────────────────────────────
    with st.expander("Client & Project Details", expanded=True):
        c1, c2, c3 = st.columns(3)
        sow["client_name"]    = c1.text_input("Client Name",        value=sow.get("client_name", ""))
        sow["project_name"]   = c2.text_input("Project / Campaign", value=sow.get("project_name", ""))
        sow["version"]        = c3.text_input("Version",            value=sow.get("version", "v1.0"))
        c4, c5, c6 = st.columns(3)
        sow["account_lead"]   = c4.text_input("Account Lead",       value=sow.get("account_lead", ""))
        sow["business_owner"] = c5.text_input("Business Owner",     value=sow.get("business_owner", ""))
        sow["date"]           = c6.text_input("Date",               value=sow.get("date", datetime.today().strftime("%B %d, %Y")))
        c7, c8 = st.columns(2)
        sow["final_deadline"] = c7.text_input("Final Deadline",     value=sow.get("final_deadline", ""))
        sow["budget_range"]   = c8.text_input("Budget Range",       value=sow.get("budget_range", ""))

    # ── Strategic Summary ─────────────────────────────────────────────────────
    # MODIFIED: explicit keys added to why_now, project_overview, core_message
    # so the AI Reword Apply button can force-update these widgets.
    with st.expander("Strategic Summary", expanded=True):
        sow["why_now"] = st.text_area(
            "Why This, Why Now",
            value=sow.get("why_now", ""),
            height=70,
            key="ta_why_now",
            help="The trigger -- what changed or what window exists.",
        )
        sow["project_overview"] = st.text_area(
            "Project Overview",
            value=sow.get("project_overview", ""),
            height=100,
            key="ta_project_overview",
            help="Executive summary of the engagement.",
        )
        sow["core_message"] = st.text_input(
            "Core Message",
            value=sow.get("core_message", ""),
            key="ta_core_message",
            help="One sentence that drives everything.",
        )

    # ── Scope Sections ────────────────────────────────────────────────────────
    st.markdown('<div class="sec-bar">SCOPE OF SERVICES</div>', unsafe_allow_html=True)
    st.caption("Each section becomes a collapsible block in the SOW. Add as many as needed.")

    sections = sow.get("scope_sections", [{"title": "", "description": "", "services": [], "deliverables": []}])
    for i, sec in enumerate(sections):
        label = sec.get("title") or f"Section {i + 1}"
        with st.expander(f"▾  {label}", expanded=(i == 0)):
            sec["title"]       = st.text_input("Section Title", value=sec.get("title", ""),       key=f"st_{i}")
            # key sd_{i} already existed; kept unchanged — Apply targets this key
            sec["description"] = st.text_area("Description",   value=sec.get("description", ""), height=80, key=f"sd_{i}")
            c_svc, c_del = st.columns(2)
            with c_svc:
                svc_raw = st.text_area(
                    "Services Included (one per line)",
                    value="\n".join(sec.get("services", [])),
                    height=120, key=f"ss_{i}",
                )
                sec["services"] = [l.strip() for l in svc_raw.splitlines() if l.strip()]
            with c_del:
                del_raw = st.text_area(
                    "Primary Deliverables (one per line)",
                    value="\n".join(sec.get("deliverables", [])),
                    height=120, key=f"del_{i}",
                )
                sec["deliverables"] = [l.strip() for l in del_raw.splitlines() if l.strip()]
            if st.button(f"Remove Section {i + 1}", key=f"rm_sec_{i}"):
                sections.pop(i)
                st.rerun()
        sections[i] = sec

    if st.button("+ Add Scope Section"):
        sections.append({"title": "", "description": "", "services": [], "deliverables": []})
        st.rerun()
    sow["scope_sections"] = sections

    # ── Assumptions & Out of Scope ────────────────────────────────────────────
    # MODIFIED: explicit keys added so Apply can force-update these widgets
    with st.expander("Assumptions & Out of Scope"):
        c_left, c_right = st.columns(2)
        with c_left:
            assume_raw = st.text_area(
                "Assumptions (one per line)",
                value="\n".join(sow.get("assumptions", [])),
                height=150,
                key="ta_assumptions",
            )
            sow["assumptions"] = [l.strip() for l in assume_raw.splitlines() if l.strip()]
        with c_right:
            oos_raw = st.text_area(
                "Out of Scope (one per line)",
                value="\n".join(sow.get("out_of_scope", [])),
                height=150,
                key="ta_out_of_scope",
            )
            sow["out_of_scope"] = [l.strip() for l in oos_raw.splitlines() if l.strip()]
        sow["timeline_notes"] = st.text_input(
            "Timeline Notes",
            value=sow.get("timeline_notes", ""),
            key="ta_timeline_notes",
        )
        sow["review_rounds"] = st.text_input(
            "Creative Review Rounds",
            value=sow.get("review_rounds", "2"),
        )

    # ════════════════════════════════════════════════════════════════════════════
    # NEW: AI Reword Assistant
    # ════════════════════════════════════════════════════════════════════════════
    with st.expander("✦ AI Reword Assistant", expanded=False):
        st.caption(
            "Select a SOW field, load its content, ask Claude to improve it, "
            "then apply the result directly back into the field."
        )

        # Build field map: label → (sow_field_key, widget_key, field_type)
        # field_type is "text" for strings or "list" for newline-separated lists
        field_map = {
            "Why This, Why Now":   ("why_now",         "ta_why_now",          "text"),
            "Project Overview":    ("project_overview", "ta_project_overview", "text"),
            "Core Message":        ("core_message",     "ta_core_message",     "text"),
            "Assumptions":         ("assumptions",      "ta_assumptions",      "list"),
            "Out of Scope":        ("out_of_scope",     "ta_out_of_scope",     "list"),
            "Timeline Notes":      ("timeline_notes",   "ta_timeline_notes",   "text"),
        }
        for _i, _sec in enumerate(sow.get("scope_sections", [])):
            _title = _sec.get("title") or f"Section {_i + 1}"
            field_map[f"Scope: {_title} — Description"] = (
                f"scope_{_i}_description", f"sd_{_i}", "text"
            )

        ai_r1c1, ai_r1c2 = st.columns([1, 1])
        with ai_r1c1:
            selected_label = st.selectbox(
                "Field to improve",
                list(field_map.keys()),
                key="ai_field_select",
            )
        fkey, wkey, ftype = field_map[selected_label]

        # Resolve current value from the live sow dict (reflects latest edits
        # made in this render pass — Step 2→3 sync source of truth)
        if fkey.startswith("scope_") and fkey.endswith("_description"):
            _idx = int(fkey.split("_")[1])
            _secs = sow.get("scope_sections", [])
            current_val = _secs[_idx].get("description", "") if _idx < len(_secs) else ""
        elif ftype == "list":
            current_val = "\n".join(sow.get(fkey, []))
        else:
            current_val = sow.get(fkey, "")

        with ai_r1c2:
            _presets = [
                "Make this more strategic and client-facing",
                "Make this more concise",
                "Improve clarity and readability",
                "Make this more persuasive",
                "Make this more professional",
                "Simplify for a non-technical audience",
                "Custom instruction…",
            ]
            preset_choice = st.selectbox("Improvement style", _presets, key="ai_preset")

        if preset_choice == "Custom instruction…":
            instruction = st.text_input(
                "Custom instruction",
                key="ai_custom_instr",
                placeholder="e.g. Make this sound more urgent and results-driven",
            )
        else:
            instruction = preset_choice

        # ── Current value display ─────────────────────────────────────────────
        if current_val:
            _preview = current_val[:400] + ("…" if len(current_val) > 400 else "")
            st.markdown(
                f'<div class="ai-box"><strong style="color:#14a4fe;font-size:10px;'
                f'letter-spacing:1px;text-transform:uppercase;">Current field value</strong>'
                f'<br><br>{_preview}</div>',
                unsafe_allow_html=True,
            )

        # ── Load & edit input ─────────────────────────────────────────────────
        _load_col, _ = st.columns([1, 3])
        with _load_col:
            if st.button("↻ Load field into editor", key="ai_load_btn", use_container_width=True):
                st.session_state["ai_input_text"] = current_val
                st.rerun()

        input_text = st.text_area(
            "Text to improve (editable)",
            key="ai_input_text",
            height=110,
            placeholder="Click 'Load field into editor' above, or paste any text you want to improve.",
        )

        # ── Reword button ─────────────────────────────────────────────────────
        _rw_col, _ = st.columns([1, 2])
        with _rw_col:
            if st.button("✦ Reword with Claude", type="primary", use_container_width=True, key="btn_reword"):
                if not input_text.strip():
                    st.warning("Please load a field or paste some text first.")
                elif not instruction.strip():
                    st.warning("Please choose or enter an instruction.")
                elif not st.session_state.get("api_key"):
                    st.error("API key not configured. Contact your Adchor admin.")
                else:
                    with st.spinner("Claude is refining your copy…"):
                        try:
                            _result = _ai_reword(
                                input_text,
                                instruction,
                                st.session_state.api_key,
                            )
                            st.session_state.ai_reword_result     = _result
                            st.session_state.ai_reword_target     = fkey
                            st.session_state.ai_reword_widget_key = wkey
                            st.session_state.ai_reword_field_type = ftype
                            # Force-update result display widget on next render
                            st.session_state["ai_result_area"]    = _result
                            st.rerun()
                        except Exception as _exc:
                            st.error(f"Reword failed: {_exc}")

        # ── Result + Apply ────────────────────────────────────────────────────
        if st.session_state.get("ai_reword_result"):
            st.markdown(
                "<span style='font-size:11px;font-weight:700;color:#00ff79;"
                "letter-spacing:1px;text-transform:uppercase;'>✓ Claude's suggestion</span>"
                " <span style='color:#5a6278;font-size:11px;'>(editable before applying)</span>",
                unsafe_allow_html=True,
            )
            edited_result = st.text_area(
                "Claude's suggestion",
                height=130,
                key="ai_result_area",
                label_visibility="collapsed",
            )

            _ap1, _ap2 = st.columns([1, 1])
            _t_fkey  = st.session_state.get("ai_reword_target",     fkey)
            _t_wkey  = st.session_state.get("ai_reword_widget_key", wkey)
            _t_ftype = st.session_state.get("ai_reword_field_type", ftype)

            with _ap1:
                if st.button("← Apply to field", type="primary", use_container_width=True, key="btn_apply"):
                    # 1. Force-update the source widget so it shows the new value
                    if _t_wkey:
                        st.session_state[_t_wkey] = edited_result

                    # 2. Also update sow_data directly for belt-and-suspenders safety
                    if _t_fkey.startswith("scope_") and _t_fkey.endswith("_description"):
                        _si = int(_t_fkey.split("_")[1])
                        _sc = sow.get("scope_sections", [])
                        if _si < len(_sc):
                            _sc[_si]["description"] = edited_result
                            sow["scope_sections"] = _sc
                    elif _t_ftype == "list":
                        sow[_t_fkey] = [l.strip() for l in edited_result.splitlines() if l.strip()]
                    else:
                        sow[_t_fkey] = edited_result

                    st.session_state.sow_data         = sow
                    st.session_state.ai_reword_result = ""
                    st.session_state.pop("ai_result_area", None)
                    st.session_state["ai_input_text"] = ""
                    st.success(f"✓ Applied to '{selected_label}'! Scroll up to review.")
                    st.rerun()

            with _ap2:
                if st.button("✕ Discard", use_container_width=True, key="btn_discard"):
                    st.session_state.ai_reword_result = ""
                    st.session_state.pop("ai_result_area", None)
                    st.rerun()

    # ── Save & navigate ───────────────────────────────────────────────────────
    # sow_data is the single source of truth for Step 3 pricing sync.
    # Saving here ensures any manual edit made in this render is persisted
    # before Step 3 reads it.
    st.session_state.sow_data = sow

    st.divider()
    col_back, _, col_next = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("Pricing →", use_container_width=True, type="primary"):
            st.session_state.step = 3
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 -- PRICING BUILDER  (unchanged except pdf_downloaded reset on enter)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown('<div class="sec-bar">STEP 3 -- INVESTMENT & PRICING</div>', unsafe_allow_html=True)
    st.caption("Price the services from your SOW. Click any service below to add it, then set the price and quantity.")

    library   = st.session_state.pricing_library
    lib_items = library.get("items", [])
    items     = st.session_state.pricing_items
    # Step 3 always reads from st.session_state.sow_data — the single source of
    # truth written at the end of every Step 2 render — so any edit made in
    # Step 2 is automatically reflected here without extra wiring.
    sow       = st.session_state.sow_data

    # ── Section A: Services from your SOW ─────────────────────────────────────
    scope_sections = sow.get("scope_sections", [])
    if scope_sections:
        st.markdown("##### Services from your SOW")
        st.caption("Click a service to add it as a line item below.")
        sow_cols = st.columns(3)
        for i, sec in enumerate(scope_sections):
            title = sec.get("title", "").strip()
            desc  = sec.get("description", "")[:80] + "…" if len(sec.get("description","")) > 80 else sec.get("description","")
            if not title:
                continue
            with sow_cols[i % 3]:
                st.markdown(f"""
                <div style="background:#1a1d24;border:1px solid #2a2d3a;border-left:4px solid #014bf7;
                    border-radius:8px;padding:12px 14px;margin-bottom:8px;">
                    <div style="color:white;font-weight:700;font-size:13px;">{title}</div>
                    <div style="color:#9aa0b0;font-size:11px;margin-top:4px;">{desc}</div>
                </div>""", unsafe_allow_html=True)
                if st.button(f"+ Add to pricing", key=f"sow_add_{i}", use_container_width=True):
                    items.append({
                        "name":        title,
                        "description": sec.get("description","")[:100],
                        "category":    "SOW Service",
                        "unit_price":  0,
                        "qty":         1,
                        "total":       0,
                    })
                    st.session_state.pricing_items = items
                    st.rerun()
        st.divider()

    # ── Section B: Pricing Table ───────────────────────────────────────────────
    st.markdown("##### Line Items")
    if not items:
        st.info("No items yet -- click a service above or use '+ Add Row' below.")
    else:
        h1, h2, h3, h4, h5, h6 = st.columns([3, 3, 1, 1.5, 1.5, 0.4])
        for col, hdr in zip([h1,h2,h3,h4,h5,h6], ["Service","Description","Qty","Unit Price ($)","Total",""]):
            col.markdown(f"<span style='font-size:11px;font-weight:700;color:#9aa0b0;text-transform:uppercase;'>{hdr}</span>",
                         unsafe_allow_html=True)
        st.markdown("<hr style='margin:4px 0 8px;border-color:#2a2d3a;'>", unsafe_allow_html=True)

        to_remove = []
        for i, item in enumerate(items):
            c1, c2, c3, c4, c5, c6 = st.columns([3, 3, 1, 1.5, 1.5, 0.4])
            item["name"]        = c1.text_input("", value=item.get("name",""),        key=f"n_{i}", label_visibility="collapsed", placeholder="Service name")
            item["description"] = c2.text_input("", value=item.get("description",""), key=f"d_{i}", label_visibility="collapsed", placeholder="Brief description")
            qty_raw = c3.text_input("", value=str(item.get("qty", 1)), key=f"q_{i}", label_visibility="collapsed")
            try:
                item["qty"] = max(1, int(qty_raw))
            except ValueError:
                item["qty"] = 1
            price_raw = c4.text_input("", value=str(item.get("unit_price", "")), key=f"p_{i}",
                                      label_visibility="collapsed", placeholder="0")
            try:
                item["unit_price"] = float(str(price_raw).replace(",","").replace("$","").strip()) if price_raw else 0.0
            except ValueError:
                item["unit_price"] = 0.0
            item["total"] = item["qty"] * item["unit_price"]
            c5.markdown(f"<div style='padding-top:8px;font-weight:700;color:white;'>${item['total']:,.0f}</div>",
                        unsafe_allow_html=True)
            if c6.button("✕", key=f"del_{i}"):
                to_remove.append(i)

        for idx in sorted(to_remove, reverse=True):
            items.pop(idx)
        if to_remove:
            st.session_state.pricing_items = items
            st.rerun()
        st.session_state.pricing_items = items

    if st.button("＋ Add Row", use_container_width=False):
        items.append({"name":"","description":"","category":"","unit_price":0,"qty":1,"total":0})
        st.session_state.pricing_items = items
        st.rerun()

    st.divider()

    # ── Section C: Totals ──────────────────────────────────────────────────────
    subtotal = sum(i.get("total", 0) for i in items)
    tc1, tc2 = st.columns([3, 1])
    with tc2:
        disc_raw = st.text_input("Discount ($)", value=str(int(st.session_state.sow_discount)) if st.session_state.sow_discount else "", placeholder="0", key="disc_input")
        try:
            discount = float(str(disc_raw).replace(",","").replace("$","").strip()) if disc_raw else 0.0
        except ValueError:
            discount = 0.0
        st.session_state.sow_discount = discount
        final_total = subtotal - discount
        st.session_state.sow_total = final_total
        disc_line = f'<div class="sub">Discount: -${discount:,.0f}</div>' if discount else ""
        st.markdown(f"""
        <div class="pricing-total">
            <div class="sub">Subtotal: ${subtotal:,.0f}</div>
            {disc_line}
            Total Investment: ${final_total:,.0f}
        </div>""", unsafe_allow_html=True)

    # ── Section D: Library (collapsed) ────────────────────────────────────────
    with st.expander("📚 Add from Service Library or save new item"):
        lib_col1, lib_col2 = st.columns(2)
        with lib_col1:
            st.markdown("**Quick-add from library**")
            if lib_items:
                lib_labels = [it["name"] for it in lib_items]
                sel = st.selectbox("Pick a service", ["-- Select --"] + lib_labels, key="lib_sel", label_visibility="collapsed")
                if sel != "-- Select --" and st.button("Add to pricing ➕", use_container_width=True):
                    idx = lib_labels.index(sel)
                    new = lib_items[idx].copy()
                    new["qty"] = 1
                    new["total"] = new["unit_price"]
                    items.append(new)
                    st.session_state.pricing_items = items
                    st.rerun()
            else:
                st.info("Library is empty.")
        with lib_col2:
            st.markdown("**Save a new item to library**")
            save_name  = st.text_input("Service Name", key="save_name")
            save_desc  = st.text_input("Description",  key="save_desc")
            save_cat   = st.text_input("Category",     key="save_cat")
            save_price_raw = st.text_input("Default Price ($)", key="save_price", placeholder="0")
            try:
                save_price = float(save_price_raw.replace(",","").replace("$","").strip()) if save_price_raw else 0.0
            except ValueError:
                save_price = 0.0
            if st.button("Save to Library", use_container_width=True):
                if save_name.strip():
                    entry = {"name": save_name.strip(), "description": save_desc.strip(),
                             "category": save_cat.strip(), "unit_price": save_price}
                    if not any(it["name"] == entry["name"] for it in lib_items):
                        lib_items.append(entry)
                        st.session_state.pricing_library["items"] = lib_items
                        st.success(f"'{save_name}' saved to library.")
        st.divider()
        st.download_button(
            "⬇ Download Pricing Library (commit to GitHub to persist)",
            data=json.dumps(st.session_state.pricing_library, indent=2),
            file_name="pricing_library.json",
            mime="application/json",
        )

    st.divider()
    col_back, _, col_next = st.columns([1, 3, 1])
    with col_back:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        # MODIFIED: reset pdf_downloaded whenever entering Step 4 with new/
        # updated pricing so the user must download the fresh PDF before Done.
        if st.button("Generate PDF →", use_container_width=True, type="primary"):
            st.session_state.pdf_downloaded = False
            st.session_state.step = 4
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 -- DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    st.markdown('<div class="sec-bar">STEP 4 -- DOWNLOAD & SEND</div>', unsafe_allow_html=True)

    sow     = st.session_state.sow_data or {}
    client  = sow.get("client_name", "Client")
    project = sow.get("project_name", "Project")
    total   = st.session_state.sow_total
    discount= st.session_state.sow_discount

    st.success(f"✓  SOW ready: **{client} -- {project}**  ·  Investment: **${total:,.0f}**")

    col_pdf, col_steps = st.columns([1, 1])

    with col_pdf:
        st.markdown("#### Download PDF")
        st.markdown("Branded PDF ready for Adobe Sign.")
        with st.spinner("Building PDF..."):
            try:
                pdf_bytes = build_sow_pdf(
                    sow_data=sow,
                    pricing_items=st.session_state.pricing_items,
                    total=total,
                    discount=discount,
                )
                filename = f"{client}_{project}_SOW.pdf".replace(" ", "_").replace("/", "-")

                # MODIFIED: capture the return value of download_button.
                # It returns True on the rerun triggered by the click,
                # which is the reliable signal that the file was sent to the browser.
                _downloaded = st.download_button(
                    label=f"⬇ Download {filename}",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
                if _downloaded:
                    st.session_state.pdf_downloaded = True

            except Exception as e:
                st.error(f"PDF generation error: {e}")

        # Download status indicator
        if st.session_state.get("pdf_downloaded"):
            st.markdown(
                "<div style='margin-top:8px;padding:8px 14px;background:rgba(0,255,121,0.07);"
                "border:1px solid rgba(0,255,121,0.25);border-radius:8px;font-size:12px;"
                "color:#00ff79;font-weight:600;'>✓ PDF downloaded</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='margin-top:8px;padding:8px 14px;background:rgba(255,180,0,0.07);"
                "border:1px solid rgba(255,180,0,0.25);border-radius:8px;font-size:12px;"
                "color:#ffb400;'>⬇ Click the button above to download the PDF before finishing.</div>",
                unsafe_allow_html=True,
            )

    with col_steps:
        st.markdown("#### Next Steps")
        st.markdown("""
        <div class="dl-note">
        <strong>After downloading:</strong><br><br>
        1. Open <strong>Adobe Sign</strong><br>
        2. Upload the PDF and add signature fields for the client and your account lead<br>
        3. Send for e-signature<br>
        4. Once fully signed, attach to the <strong>Monday.com</strong> project card and move to Active<br><br>
        <em>Tip: Keep the PDF file name as-is -- it follows the Client_Project_SOW convention.</em>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # MODIFIED: two-button row — Back on the left, Done on the right.
    col_back, _, col_done = st.columns([1, 3, 1])

    with col_back:
        if st.button("← Back to Pricing", use_container_width=True):
            # Going back resets the download flag — new pricing requires a new download.
            st.session_state.pdf_downloaded = False
            st.session_state.step = 3
            st.rerun()

    with col_done:
        # NEW: Done button — only completes the workflow after the PDF is downloaded.
        if st.button("✓ Done", use_container_width=True, type="primary"):
            if st.session_state.get("pdf_downloaded", False):
                _reset_sow_state()
                st.rerun()
            else:
                st.warning("Please make sure to download the PDF before finishing the SOW.")
