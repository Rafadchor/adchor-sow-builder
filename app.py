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
    border-right: 1px solid #0d0f1a !important;
}
[data-testid="stSidebar"] > div { padding-top: 56px !important; }

/* ── Sidebar collapse button — keep it above brand row ── */
[data-testid="stSidebarCollapseButton"] {
    position: absolute !important;
    top: 10px !important;
    right: 10px !important;
    z-index: 1000 !important;
    background: transparent !important;
    border: none !important;
}
[data-testid="stSidebarCollapseButton"] button {
    background: transparent !important;
    color: #1e2540 !important;
}
[data-testid="stSidebarCollapseButton"] button:hover {
    color: #014bf7 !important;
    background: rgba(1,75,247,0.08) !important;
}

/* ══════════════════════════════════════════
   SIDEBAR — Brand Row & Logo
══════════════════════════════════════════ */
.sb-brand-row {
    display: flex; align-items: center; gap: 11px;
    margin-bottom: 22px; padding: 0 2px;
}
/* Logo visibility: dark mode shows dark logo, light mode shows light logo */
.sb-logo { height: 60px; width: auto; display: block; max-width: 100%; }
.sb-logo-light { display: none; }
@media (prefers-color-scheme: light) {
    .sb-logo-dark  { display: none; }
    .sb-logo-light { display: block; }
}
.sb-brand-mark {
    width: 40px; height: 40px; border-radius: 12px;
    background: linear-gradient(135deg, #014bf7, #021de0);
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; font-weight: 900; color: white;
    box-shadow: 0 4px 20px rgba(1,75,247,0.6), 0 0 40px rgba(1,75,247,0.2);
    flex-shrink: 0;
}
.sb-bname { font-size: 13px; font-weight: 800; color: #fff; letter-spacing: 3px; text-transform: uppercase; }
.sb-bsub  { font-size: 8px; font-weight: 600; color: #14a4fe; letter-spacing: 2px; text-transform: uppercase; margin-top: 2px; }

/* ── Progress bar ── */
.sb-prog-wrap { margin-bottom: 18px; padding: 0 2px; }
.sb-prog-label {
    font-size: 8px; font-weight: 700; color: #1e2540; letter-spacing: 2px;
    text-transform: uppercase; margin-bottom: 7px;
    display: flex; justify-content: space-between;
}
.sb-prog-label span { color: #014bf7; }
.sb-prog-track { height: 3px; background: #0d0f1a; border-radius: 99px; }
.sb-prog-fill  { height: 3px; background: linear-gradient(90deg, #014bf7, #14a4fe); border-radius: 99px; box-shadow: 0 0 8px rgba(20,164,254,0.6); }

/* ── Step items ── */
.sb-step-item {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 10px; border-radius: 11px; margin-bottom: 4px;
}
.sb-step-icon {
    width: 32px; height: 32px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 900; flex-shrink: 0;
}
.sb-step-name { font-size: 11px; font-weight: 700; }
.sb-step-desc { font-size: 9px; font-weight: 500; margin-top: 2px; }

.step-done .sb-step-icon { background: rgba(0,255,121,0.1); color: #00ff79; }
.step-done .sb-step-name { color: #00ff79; }
.step-done .sb-step-desc { color: rgba(0,255,121,0.5); }

.step-active { background: rgba(1,75,247,0.1); }
.step-active .sb-step-icon { background: #014bf7; color: white; box-shadow: 0 4px 14px rgba(1,75,247,0.55); }
.step-active .sb-step-name { color: #ffffff; }
.step-active .sb-step-desc { color: rgba(255,255,255,0.45); }

.step-pend .sb-step-icon { background: rgba(255,255,255,0.03); color: #1e2540; border: 1px solid #0d0f1a; }
.step-pend .sb-step-name { color: #1e2540; }
.step-pend .sb-step-desc { color: #141828; }

/* ── Active Client chip ── */
.sb-client-chip {
    margin-top: 20px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 12px 14px;
}
.sb-chip-label {
    font-size: 8px; font-weight: 700; color: #1e2540;
    letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px;
}
.sb-chip-row { display: flex; align-items: center; gap: 9px; }
.sb-chip-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: #00ff79; box-shadow: 0 0 6px rgba(0,255,121,0.7); flex-shrink: 0;
}
.sb-chip-name { font-size: 13px; font-weight: 800; color: #9aa0b4; }

/* ══════════════════════════════════════════
   HERO BAR — Step header
══════════════════════════════════════════ */
.hero-bar {
    background: linear-gradient(135deg, #010c30 0%, #014bf7 60%, #021de0 100%);
    padding: 20px 26px;
    border-radius: 12px;
    position: relative; overflow: hidden;
    margin: 0 0 20px;
    box-shadow: 0 6px 28px rgba(1,75,247,0.4);
}
.hero-bar::before {
    content: '';
    position: absolute; top: -40px; right: -40px;
    width: 140px; height: 140px; border-radius: 50%;
    background: rgba(20,164,254,0.12);
}
.hero-bar::after {
    content: '';
    position: absolute; bottom: -25px; right: 110px;
    width: 80px; height: 80px; border-radius: 50%;
    background: rgba(0,255,121,0.07);
}
.hero-eyebrow {
    font-size: 9px; font-weight: 700; letter-spacing: 3px;
    text-transform: uppercase; color: rgba(255,255,255,0.45); margin-bottom: 5px;
}
.hero-title {
    font-size: 20px; font-weight: 900; color: white;
    letter-spacing: -0.5px; line-height: 1.1;
}
.hero-sub {
    font-size: 11px; font-weight: 500; color: rgba(255,255,255,0.5); margin-top: 5px;
}

/* ── Section header bar (sub-section within a step) ── */
.sec-bar {
    background: linear-gradient(135deg, #030a20 0%, #014bf7 100%);
    color: white;
    padding: 13px 22px;
    border-radius: 10px;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    margin: 0 0 18px;
    box-shadow: 0 4px 20px rgba(1,75,247,0.3);
    position: relative; overflow: hidden;
}
.sec-bar::before {
    content: '';
    position: absolute; top: -20px; right: -20px;
    width: 80px; height: 80px; border-radius: 50%;
    background: rgba(20,164,254,0.1);
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

/* ── Pricing total / Investment bar ── */
.pricing-total {
    background: linear-gradient(135deg, #021de0 0%, #014bf7 100%);
    color: white;
    padding: 18px 24px;
    border-radius: 14px;
    text-align: right;
    font-size: 22px;
    font-weight: 800;
    margin-top: 14px;
    box-shadow: 0 8px 32px rgba(1,75,247,0.4);
    border: 1px solid rgba(20,164,254,0.25);
    letter-spacing: -0.5px;
    position: relative; overflow: hidden;
}
.pricing-total::before {
    content: '';
    position: absolute; top: -25px; right: -25px;
    width: 100px; height: 100px; border-radius: 50%;
    background: rgba(20,164,254,0.12);
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

/* ── AI instruction panel (Step 2 global editor) ── */
.ai-instr-panel {
    background: linear-gradient(135deg, #090d1c 0%, #070b17 100%);
    border: 1px solid #1a2545;
    border-left: 4px solid #14a4fe;
    border-radius: 12px;
    padding: 14px 20px 12px;
    margin: 8px 0 4px;
}
.ai-instr-label {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #14a4fe;
    margin-bottom: 3px;
}
.ai-instr-sub {
    font-size: 11px;
    color: #5a6278;
    line-height: 1.5;
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
    color: #ffffff !important;
    box-shadow: 0 4px 16px rgba(1,75,247,0.4) !important;
}
.stButton > button[kind="primary"] p,
.stButton > button[kind="primary"] span,
.stButton > button[kind="primary"] div {
    color: #ffffff !important;
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

/* ══════════════════════════════════════════
   LIGHT MODE  (OS-level preference)
══════════════════════════════════════════ */
@media (prefers-color-scheme: light) {
    .stApp { background: #eef1fb !important; }
    [data-testid="stAppViewBlockContainer"] { background: #eef1fb !important; }
    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #e4e8f4 !important;
        box-shadow: 2px 0 20px rgba(1,75,247,0.06) !important;
    }
    .sb-bname { color: #0d1025; }
    .sb-bsub  { color: #014bf7; }
    .sb-prog-label { color: #c8d0e4; }
    .sb-prog-track { background: #eef1f8; }
    .sb-prog-fill  { box-shadow: none; }
    .step-done .sb-step-icon { background: rgba(0,168,84,0.1); color: #00a854; }
    .step-done .sb-step-name { color: #00a854; }
    .step-done .sb-step-desc { color: rgba(0,168,84,0.6); }
    .step-active { background: #f0f4ff; }
    .step-active .sb-step-icon { background: #014bf7; box-shadow: 0 4px 14px rgba(1,75,247,0.35); }
    .step-active .sb-step-name { color: #014bf7; }
    .step-active .sb-step-desc { color: #8090b8; }
    .step-pend .sb-step-icon { background: #f4f6fc; color: #c8d0e4; border-color: #eef1f8; }
    .step-pend .sb-step-name { color: #c8d0e4; }
    .step-pend .sb-step-desc { color: #d8dff0; }
    .sb-client-chip { background: #f4f7ff; border-color: #e4e8f4; }
    .sb-chip-label  { color: #c0c8e0; }
    .sb-chip-dot    { background: #00a854; box-shadow: 0 0 5px rgba(0,168,84,0.5); }
    .sb-chip-name   { color: #3a4060; }
    .stButton > button[kind="primary"],
    .stButton > button[kind="primary"] p,
    .stButton > button[kind="primary"] span { color: #ffffff !important; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        background: #ffffff !important;
        border-color: #e4e8f4 !important;
        color: #1a1d2e !important;
    }
    .info-box { background: #f0f4ff; border-color: #c8d4f8; color: #4a5280; }
    .ai-instr-panel { background: #f0f4ff; border-color: #c8d4f8; }
    .ai-instr-sub   { color: #6070a0; }
    .ai-box { background: #f4f6fc; border-color: #c8d4f8; color: #5a6080; }
    .dl-note { background: #f0fff4; border-color: rgba(0,180,80,0.3); color: #3a4060; }
    [data-testid="stExpander"] { background: #ffffff !important; border-color: #e4e8f4 !important; }
    [data-testid="stSelectbox"] > div > div {
        background: #ffffff !important;
        border-color: #e4e8f4 !important;
        color: #1a1d2e !important;
    }
    [data-testid="stFileUploader"] { background: #ffffff !important; border-color: #c8d4f8 !important; }
    ::-webkit-scrollbar-track { background: #eef1fb; }
    ::-webkit-scrollbar-thumb { background: #c8d0e4; }
    hr { border-color: #e4e8f4 !important; }
    .stCaption { color: #8090b4 !important; }
    .sb-logo-dark  { display: none; }
    .sb-logo-light { display: block; }
}

/* ══════════════════════════════════════════
   LIGHT MODE  (Streamlit theme toggle)
   Streamlit adds html.light / html.dark when
   the user changes theme in the settings menu.
   This mirrors the @media block so custom CSS
   adapts even when the OS theme differs from
   the Streamlit theme selection.
══════════════════════════════════════════ */
html.light .stApp { background: #eef1fb !important; }
html.light [data-testid="stAppViewBlockContainer"] { background: #eef1fb !important; }
html.light [data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e4e8f4 !important;
    box-shadow: 2px 0 20px rgba(1,75,247,0.06) !important;
}
html.light .sb-bname { color: #0d1025; }
html.light .sb-bsub  { color: #014bf7; }
html.light .sb-prog-label { color: #c8d0e4; }
html.light .sb-prog-track { background: #eef1f8; }
html.light .sb-prog-fill  { box-shadow: none; }
html.light .step-done .sb-step-icon { background: rgba(0,168,84,0.1); color: #00a854; }
html.light .step-done .sb-step-name { color: #00a854; }
html.light .step-done .sb-step-desc { color: rgba(0,168,84,0.6); }
html.light .step-active { background: #f0f4ff; }
html.light .step-active .sb-step-icon { background: #014bf7; box-shadow: 0 4px 14px rgba(1,75,247,0.35); }
html.light .step-active .sb-step-name { color: #014bf7; }
html.light .step-active .sb-step-desc { color: #8090b8; }
html.light .step-pend .sb-step-icon { background: #f4f6fc; color: #c8d0e4; border-color: #eef1f8; }
html.light .step-pend .sb-step-name { color: #c8d0e4; }
html.light .step-pend .sb-step-desc { color: #d8dff0; }
html.light .sb-client-chip { background: #f4f7ff; border-color: #e4e8f4; }
html.light .sb-chip-label  { color: #c0c8e0; }
html.light .sb-chip-dot    { background: #00a854; box-shadow: 0 0 5px rgba(0,168,84,0.5); }
html.light .sb-chip-name   { color: #3a4060; }
html.light .stButton > button[kind="primary"],
html.light .stButton > button[kind="primary"] p,
html.light .stButton > button[kind="primary"] span { color: #ffffff !important; }
html.light .stButton > button[kind="secondary"] {
    background: #ffffff !important;
    border-color: #c8d0e4 !important;
    color: #4a5280 !important;
}
html.light .stTextInput > div > div > input,
html.light .stTextArea > div > div > textarea,
html.light .stNumberInput > div > div > input {
    background: #ffffff !important;
    border-color: #e4e8f4 !important;
    color: #1a1d2e !important;
}
html.light .info-box { background: #f0f4ff; border-color: #c8d4f8; color: #4a5280; }
html.light .ai-instr-panel { background: #f0f4ff; border-color: #c8d4f8; }
html.light .ai-instr-sub   { color: #6070a0; }
html.light .ai-box { background: #f4f6fc; border-color: #c8d4f8; color: #5a6080; }
html.light .dl-note { background: #f0fff4; border-color: rgba(0,180,80,0.3); color: #3a4060; }
html.light [data-testid="stExpander"] { background: #ffffff !important; border-color: #e4e8f4 !important; }
html.light [data-testid="stSelectbox"] > div > div {
    background: #ffffff !important;
    border-color: #e4e8f4 !important;
    color: #1a1d2e !important;
}
html.light [data-testid="stFileUploader"] { background: #ffffff !important; border-color: #c8d4f8 !important; }
html.light hr { border-color: #e4e8f4 !important; }
html.light .stCaption { color: #8090b4 !important; }
html.light .sb-logo-dark  { display: none !important; }
html.light .sb-logo-light { display: block !important; }
html.dark  .sb-logo-dark  { display: block !important; }
html.dark  .sb-logo-light { display: none !important; }
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
# NEW: AI SOW Update — whole-document revision from a free-form instruction
# ════════════════════════════════════════════════════════════════════════════════
def _ai_update_sow(sow_data: dict, instruction: str, api_key: str) -> dict:
    """
    Call Claude to apply a free-form instruction to the entire SOW.
    Returns the complete updated sow_data dict (all fields, even unchanged ones).
    """
    import anthropic as _ant
    import json as _json

    _client = _ant.Anthropic(api_key=api_key)
    _sow_json = _json.dumps(sow_data, indent=2, ensure_ascii=False)

    _msg = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": (
                "You are an expert editor of Statement of Work (SOW) documents "
                "for a creative advertising agency called Adchor.\n\n"
                "Here is the current SOW data in JSON:\n"
                f"{_sow_json}\n\n"
                f"User instruction: {instruction}\n\n"
                "Apply the instruction and return the COMPLETE updated SOW as a single "
                "valid JSON object. Rules:\n"
                "1. Include EVERY field — even ones you did not change.\n"
                "2. Preserve existing values unless the instruction explicitly changes them.\n"
                "3. For list fields (assumptions, out_of_scope, scope_sections[].services, "
                "scope_sections[].deliverables), always return JSON arrays of strings.\n"
                "4. Keep the same JSON structure and key names as the input.\n"
                "5. Return raw JSON only — no markdown, no code fences, no commentary."
            ),
        }],
    )

    _text = _msg.content[0].text.strip()
    # Strip markdown code fences if the model wrapped in them anyway
    if _text.startswith("```"):
        _lines = _text.splitlines()
        _inner = _lines[1:-1] if _lines and _lines[-1].strip() == "```" else _lines[1:]
        _text = "\n".join(_inner).strip()

    return _json.loads(_text)


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
    "ai_sow_instruction",
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
        "ai_sow_instruction": "",
        "ai_sow_update_status": "",
    }
    for k, v in reset_vals.items():
        st.session_state[k] = v
    # Clear SOW field widget state so they re-initialise with fresh sow_data
    for k in _SOW_FIELD_WIDGET_KEYS + _AI_WIDGET_KEYS:
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
    "ai_sow_instruction": "",     # global SOW AI editor instruction box
    "ai_sow_update_status": "",   # success/error banner after AI SOW update
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Brand row — real logos (dark/light) embedded as base64 ────────────────
    _LOGO_DARK  = (
    "iVBORw0KGgoAAAANSUhEUgAABLAAAAH9CAYAAAAK34XaAAC+FklEQVR42uzdd3hUVf4G8Pd77kx6"
    "IQlpBBJKQJqgggI2Eru7Krqa6P50XcuuZV1s2MsmsWBfde11bburE13L2gUSLCgKKEjvvbeQnpl7"
    "zu+P3BsDpkwgwCS8n+eZR0yZzJy598w973zPOQAREREREREREcEYo0QEzzzzzJitW7fCGAPbtmGM"
    "4W0/3zw8PImIiIiIiIiIABHRxhhLRN7v0qXLlWedddYz4eHhMMZARNhAREREREREREQUGowxHgB4"
    "//3373MrgLTWrITajzfGh0REREREREREOxNnOqFdUlLyfk5Ozhg2yf5lsQmIiIiIiIiIiH5FSktL"
    "1ciRI98/9dRTZ6ekpDypteZUwv2EARYRERERERER0S4mT55sBg0apF599dXa5OTkKQMHDlwXExMD"
    "hlhERERERERERBRSSkpKPADw5ptvjnV3JOR6WFwDi4iIiIiIiIgolIizM2GgtLS0ZPTo0blskn2P"
    "UwiJiIiIiIiIiFpRWlqKO++88+vhw4dvjY+P51RCIiIiIiIiIiIKLcYYCwBef/31se4UQk4l5BRC"
    "IiIiIiIiIqJQIsYYJSLqhx9+mDp8+PDD2CT7jmITEBERERERERG1yhQXF0NE/B9//PE1ZWVl9V80"
    "hi1DREREREREREShw92VsLS09E1O7dt3N1ZgEREREREREREFadOmTcYYI6+99to9a9euBQBordkw"
    "REREREREREQUOtwF3f/73//+h9VR++Zm8bAjIiIiIiIiImoTKS0txfjx4+ePHDlyY2xsLLTWEOFe"
    "eUREREREREREFCLcKqxJkyb9mxVSXAOLiIiIiIiIiCjkFBcXwxgjU6dOfWjbtm0AuCPh3sTaNiIi"
    "IiIiIiKi3WCMUSJifvjhh5Lhw4fnsEX2HlZgERERERERERHthtLSUiUiZs6cOc+5OxGyCouIiIiI"
    "iIiIiEKJGGOkf//+SYsWLdpgjIFt21yzimtgERERERERERGFDAPAmj9//pbly5d/AABKMWrZG9iq"
    "RERERERERES7qbi42ACQ77777p3q6moAnEa4N3ARdyIiIiIiIiKi3SciYowx0XPmzFk4cODADK01"
    "K7HaGVuTiIiIiIiIiGj3Ga21BaBy8+bNHwGcRrg3WGwCIiIiIiIiIqI9Yk2ePNkce+yx3iFDhsxj"
    "gNX+2KJERERERERERHtGAzA+n+/7VatW1QCA1pqt0o64BhYRERERERER0R4yxoiImO+//37a4Ycf"
    "Ppwt0r5YgUVEREREREREtOcsANi0adMUNkX7Y4BFRERERERERLSHSktLAQDV1dWTOH2w/XERdyIi"
    "IiIiIiKiPVRVVSVz5841iYmJniOOOGJjTEwMtNYQ4epN7YGtSERERERERES05wSAARC7YMGChf36"
    "9Uu3bRuWxdqh9sAphEREREREREREe84YYywAFbW1tQsBMLxqRwywiIiIiIiIiIjaj9m8efNqNkP7"
    "YoBFRERERERERNQOSktLBQAqKioWsjXaFwMsIiIiIiIiIqJ2tHHjxrVshfbFAIuIiIiIiIiIqB1s"
    "2rTJAEBERMRiv98PADDGsGHaAQMsIiIiIiIiIqJ2NGXKFLuyspIN0Y4YYBERERERERERtYO8vDwN"
    "ADk5OfPcr4kIG6YdMMAiIiIiIiIiImpHP/74I6qrqwEAWms2SDtggEVERERERERE1I6++uor1NTU"
    "lLMl2g8DLCIiIiIiIiKidrR+/XoEAgE2RDtigEVERERERERE1I4qKiq4+2A7Y4BFREREREREREQh"
    "jQEWERERERERERGFNAZYREREREREREQU0hhgERERERERERFRSGOARUREREREREREIY0BFhERERER"
    "ERERhTQGWEREREREREREFNIYYBERERERERERUUhjgEVERERERERERCGNARYREREREREREYU0BlhE"
    "RERERERERBTSGGAREREREREREVFIY4BFREREREREREQhjQEWERERERERERGFNAZYREREREREREQU"
    "0hhgERERERERERFRSGOARUREREREREREIY0BFhERERERERERhTQGWEREREREREREFNIYYBERERER"
    "ERERUUhjgEVERERERERERCGNARYREREREREREYU0BlhERERERERERBTSGGAREREREREREVFIY4BF"
    "REREREREREQhjQEWERERERERERGFNAZYREREREREREQU0hhgERERERERERFRSGOARURERERERERE"
    "IY0BFhERERERERERhTQGWEREREREREREFNIYYBERERERERERUUhjgEVERERERERERCGNARYRERER"
    "EREREYU0BlhERERERERERBTSGGAREREREREREVFIY4BFREREREREREQhjQEWERERERERERGFNAZY"
    "REREREREREQU0hhgERERERERERFRSGOARUREREREREREIY0BFhERERERERERhTQGWERERERERERE"
    "FNIYYBERERERERERUUhjgEVERERERERERCGNARYREREREREREYU0BlhERERERERERBTSGGARERER"
    "EREREVFIY4BFREREREREREQhjQEWERERERERERGFNAZYREREREREREQU0hhgERERERERERFRSGOA"
    "RUREREREREREIY0BFhERERERERERhTQGWEREREREREREFNIYYBERERERERERUUhjgEVERERERERE"
    "RCGNARYREREREREREYU0BlhERERERERERBTSGGAREREREREREVFIY4BFREREREREREQhjQEWERER"
    "ERERERGFNAZYREREREREREQU0hhgERERERERERFRSGOARUREREREREREIY0BFhERERERERERhTQG"
    "WEREREREREREFNIYYBERERERERERUUhjgEVERERERERERCGNARYREREREREREYU0BlhERERERERE"
    "RBTSGGAR0V5TUFCgjDGqpKTEY4xp9lZSUuLx+XxWQUGBAiBsOSIiIiIiIiIi2hvE5/NZTihliexe"
    "DiUiMMa498OQnYiIiIiIOgxjjABAWlpa8oIFC8qNMbBtG8YY3vbw5uHhRUR7wufzWXl5eSIigfz8"
    "fLvx9woK7u9+wglHJcXGxvZJSEqKWb1y5dCMjB4IDw8HALN582bZuHF9+dChQ2d9880328vL/Usu"
    "uOCcVSJi7/IGoABoETFscSIiIiIiIiIiapUxRpqosgovLn5vxE8//XT9unXr/rV589bZ27ZtqwoE"
    "AiZYO3aU127evHnBsmXLin/4YfrYf//734N2+bvuNEMiIiIiIqKQHCsBrMBiBRYR7ffOuLS01BKR"
    "AAAbAD7/fNLxAwb0PTMqKuqU2NjYbK/X29Sv2gBaqp4SABIbGxMGxPRLSkrq17Nnz3MGDuxvb9iw"
    "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"
    "Kjk5OXHfxbp8daexFv4KpbzXQDUZU6mrqyvcsWPHq4sXL371xhtvXNnOwcqhmKNGRPyqQa2Uqnj5"
    "5ZefEJEnIpHI4MGDB09ITk6+OD09fWRaWloP/86a+1uEN5mr+zZ5/7c5tHPnzj1VVVVr9+zZ8+YX"
    "X3zxZm5u7tK33nqr3H+O4ziWUspp421d/vx+WkRWtWJ+v98R87sNeJ9liau1niYiyfv73RzHEcuy"
    "pK6uznEcZ7uISF5enumgOeZ4c0wppdZNnz79f0Xkty+//HIoKytrfFpaWqhTp04npaen7zW/9jkX"
    "unu/T+1/ftXW1kpVVdW6ioqKpeXl5fOmTZsWLS4urvYGSjc5N3fka2NE5IYDvTb7zLt/NZ2vAIAA"
    "rZKAr8PfnnPFtdcee1XOlcVDh2Z1qq2tE8vS35LpZ1r/Vebf/9R1jThOXGpra2XPnvpdu2pqqoxI"
    "ye5duz8qq9i6snTd5+89+OC9Hze5elK5ublWXl4ewdWBR9sSUY7q+crvVZcJN4m7XRryd3MYn9aa"
    "FkN4607jikhMxK0WMXsqjNQXi1O50riVb0j87QLZPnPnV89xLa9JO3OqdasYVVBQYIVCIbfpQuy2"
    "227LDIVCJ/Xu3fukxMTEUZmZmb3q6ur6JyYmpiQnJ8uuXbu6WZbl31LeOeqoo6q2b9+uEhMTN1RU"
    "VJRprVdt2LDhkzVr1rx//fXXFzdd9Bhj7Nzc3MOu4bUXZO21CL333nsHjh07dmxGRsbZqampIzt1"
    "6jS4c+fO6V26tK6YIR6Py65du3bF4/F1O3fuXL19+/al77333ns33XRTUZPx1Pn5+Yd1rxy/WkYa"
    "qlMaj+1LLrmk+8033zy4V69eJ3Tq1OlkERmenp6eVldXd0y3bt3MUUcdpWpqarp5VTOSkpJSWV9f"
    "b3bu3KmMMeUismn37t2fV1ZWluzZs6do5cqVq2+44YbSpucPY4yVn58v9CI6Iq7htNY63rQHVjgc"
    "Pi4UCp2Qnp5+cteuXY/r3r17r507dw7t1q2b1blzZ11bW5vq3100Ho9LUlLS9srKSqWU2lxdXb1V"
    "a71q/fr1n23cuPGfV1999SciUn+4nwsBHNnXlUopk5mZmfHWW2+tGzp0aLLruu1y99YjDQEW2uXi"
    "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"
)
    _LOGO_LIGHT = (
    "iVBORw0KGgoAAAANSUhEUgAABLAAAAH9CAYAAAAK34XaAACn4ElEQVR42uzdd3hkV3k/8O97zrkz"
    "qqtVl7Z43TDFAQdsOgTJmAAJYJpkU4MhYEqMAUNMlwTYpjeDjSFAIBBgBKHkR+iW6JCsKQ6mxcZ9"
    "m7Zpd9Xm3nPe3x9zr1a7XkmjXWl3JH0/zzOPbVn1zL1n7vnOe94rICIiIiIiIiIiqKoxxoSGta3n"
    "/+WWP369sbERIQQYYzg4J5hwCIiIiIiIiIiISlTViohvaup42ZYtt12bz+ehqhBhhHIiMUIkIiIi"
    "IiIiIkqJiFdVt3v3tmvXbzj1qvRjUFUOzol8XjgERERERERERESHEFU1IuJbWjd8fWTHnedzSE4s"
    "VmARERERERERER1K+/v7VVWtNfGzOzpP/hMAhBA4MkREREREREREVDkKhYIVEdSvaXrQ9u3boarw"
    "3kNV+TjODyIiIiIiIiIimsXQ0JADgKbmzkuy8CqEwFDpOD/YA4uIiIiIiIiIaHaS3pkwaW3dMLRj"
    "x53dHJLjjz2wiIiIiIiIiIhmp/39/UFVZWxs9MV33HEHAPbDOt5YgUVERERERERENI+0Css3NnVc"
    "smvnlqtFpLS1TRitHA8cZSIiIiIiIiKi+YmqGhExbe0n/XL7ttsfxCE5friFkIiIiIiIiIhofjo4"
    "OAgRiScnxi4dHR0tfZB3yCMiIiIiIiIiokqS3ZWwtXXDF3l3wOP3YAUWEREREREREVGZRkZGVFVl"
    "bHzfO7Zs2QKADd2PB/bAIiIiIiIiIiJagKyhe3Nz5xd27tzyLI7I0mMFFhERERERERHRAvT396uq"
    "ysTEgStYhXV8sAKLiIiIiIiIiGiBsiqsltYN/z6y485nc0SWFiuwiIiIiIiIiIgWaHBwEKoqxeLk"
    "e/bs2QOAdyRcSqzAIiIiIiIiIiI6CqpqRETb2k8a2r7t9i6OyNJhBRYRERERERER0VEYHh42IqJx"
    "PHVd1gOLVVhLgxVYRERERERERERHR1QV973vfZv27p38/datt7aHEGAM64UWG0eUiIiIiIiIiOjo"
    "KAD7xz/+cVfi428AYHi1RDiqRERERERERERHaXBwUAFIcWryKxMTEwC4jXApcAshEREREREREdHR"
    "ExFRVa1t79j0521bb1vPbYSLj6NJRERERERERHT0NIRgAYwF778JcBvhUuCIEhEREREREREdg/7+"
    "fgEgSRJ/23vPAVkCDLCIiIiIiIiIiI5NAKAPfegD/3vDxntNAkAIgaOyiNgDi4iIiIiIiIjoGKmq"
    "iIi2tZ20efv228/hiCwuVmARERERERERER07CwA+JD/jUCw+BlhERERERERERMdoeHgYAKCq13P7"
    "4OJjgEVEREREREREdIyuueYaBYCpyfGbR0ZGALAP1mJiDywiIiIiIiIiomMnABRAfXvHyX/etvXW"
    "Tu89rLUcmUXACiwiIiIiIiIiomOnqmoBHIDqnwEwvFpEDLCIiIiIiIiIiBaP+uDv4jAsLgZYRERE"
    "RERERESLYHh4WABANfyZo7G4GGARERERERERES2i4P0WjsLiYoBFRERERERERLQIRkZGFABE5OY4"
    "jgEAqsqBWQQMsIiIiIiIiIiIFtFUccKPjY1xIBaRcAiIiIiIiIiIiI6dqoqIaKFQaH3c4x43snbt"
    "Wg7KImEFFhERERERERHRIvr1r3+NiYkJAEAIgQOyCBhgEREREREREREtoh//+Md40NmP3M+RWDwM"
    "sIiIiIiIiIiIFtG2bdvYvH2RMcAiIiIiIiIiIlpEBw4c4CAsMgZYRERERERERERU0RhgERERERER"
    "ERFRRWOARUREREREREREFY0BFhERERERERERVTQGWEREREREREREVNEYYBERERERERERUUVjgEVE"
    "RERERERERBWNARYREREREREREVU0BlhERERERERERFTRGGAREREREREREVFFY4BFREREREREREQV"
    "jQEWERERERERERFVNAZYRERERERERERU0RhgERERERERERFRRWOARUREREREREREFY0BFhERERER"
    "ERERVTQGWEREREREREREVNEYYBERERERERERUUVjgEVERERERERERBWNARYREREREREREVU0BlhE"
    "RERERERERFTRGGAREREREREREVFFY4BFREREREREREQVjQEWERERERERERFVNAZYRERERERERERU"
    "0RhgERERERERERFRRWOARUREREREREREFY0BFhERERERERERVTQGWEREREREREREVNEYYBERERER"
    "ERERUUVjgEVERERERERERBWNARYREREREREREVU0BlhERERERERERFTRGGAREREREREREVFFY4BF"
    "REREREREREQVjQEWERERERERERFVNAZYRERERERERERU0RhgERERERERERFRRWOARURERERERERE"
    "FY0BFhERERERERERVTQGWEREREREREREVNEYYBERERERERERUUVjgEVERERERERERBWNARYRERER"
    "EREREVU0BlhERERERERERFTRGGAREREREREREVFFY4BFREREREREREQVjQEWERERERERERFVNAZY"
    "RERERERERERU0RhgERERERERERFRRWOARUREREREREREFY0BFhERERERERERVTQGWERERERERERE"
    "VNEYYBERERERERERUUVjgEVERERERERERBWNARYREREREREREVU0BlhERERERERERFTRGGARERER"
    "EREREVFFY4BFREREREREREQVjQEWERERERERERFVNAZYRERERERERERU0RhgERERERERERFRRWOA"
    "RUREREREREREFY0BFhERERERERERVTQGWEREREREREREVNEYYBERERERERERUUVjgEVERERERERE"
    "RBWNARYREREREREREVU0BlhERERERERERFTRGGAREREREREREVFFY4BFREREREREREQVjQEWES2Z"
    "vr4+o6pmaGjIqeqsj6GhIVcoFGxfX58BIBw5IiIiIiIiIiJaClIoFGwaSlmRo8uhRASqmn0fhuxE"
    "RERERLRsqKoAQEdHR2t7x8n7VRXee6gqH8f4YKUDER2TQqFge3p6RESSw/9fX987N1xz7UebReQ0"
    "Y2yd98lZ1jqk4ZYG78UHvz+K8jcWixN7Negtu3dvvRNAOOwFwAAIIqIccSIiIiIiqlSqKiKiHR0d"
    "rYqqv2zbemt9CAHG8L35Y8UAi4iOalIGYIwxXnU6U8o3Na/7a+fcI611ZwNylghOFTHV5VZjhRCK"
    "qnqbargxBP+jJC5ev3v3tptm/Fzb39+vAwMDgc8CERERERFV4lqJAdbScBwCIlrIZDw8PGzTaisP"
    "AC2tGx7rXPRUI+YJYszps4RVHsBc1VMCQIwxOQBnAPYMIHqmcznfue7Uzarhc++8qv+rInJ3+ntY"
    "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"
    "i/rqw4KtU/Whpqnnm6b5dkT59GAw+PS1z/meGz/72c/uG7ZvXddVSqle4mVdTdt5PxARXzuL/v2l"
    "C9G/l8DwoL8mIv10RKw+1d82PLCglKau6/pARMS2bdvKBepjddvHUkrpjsOx91ci4t3rNzxxstcb"
    "fW3OeTJFekGuqof1r5PGwubhr1On7l+laaIpzR1NU9/Y1PWfrlu3cua22759pG2DvGhsvpDPTYmI"
    "nzndc3NSv/v6SeMxAF2ZJcGjMVyes2LlmqtXrFh9W683OrrwxuzS+jvLI2YlJ07QOlpKczgibi+l"
    "+bumrr86qAdfePDIgW8seveUtm7dWm3btk1wdfrWriJSnSb+/LfTytf982gOxEOnxV+qw9riYoh2"
    "3lmaiOhHNEciyvz+EnO3RX3wq6U5+P/G4K93xIH3PPDQY5qqXUKmT53dLCbt2LGjmpycbBZPxH7u"
    "535u8/v/8MMvqKreC1LKL6yqalMp5SkppStSylFKWbvox9QppcNNU6eU0neapt4bkb42GPS/WQ/6"
    "Xzp4cPdtiyc9pZTe1q1bL7kNr9sg62GT0CvWbHjasmVjr8i598qc83UR6ekppXX5LM9fWBhPm6Ol"
    "xB2lNLc2TX3j/NzxLxw6tPcri+6Tt2/ffknvlTOslol2I/Xh99/4xjeuv/Fvbn56VVXPTZFeFBHX"
    "5lyNlyhX5ZTb8rVm7XA8ybk6WEpTmqZJEbEvInaWUu5umvr2UspX+v25Ww8d3HPX4vGjlFJt3749"
    "7EV0WbyHyznnh50suvqKdc9atmzFc3OuXpRzelbO1aamaZ6Zc1W1+86tWfz6lVI+0DR1ikj3l9Ls"
    "joivDQb9bzX14IsHDuz6ZkTMXepjIXB5v69MKZXNmzdvLDF2x67771zdNE1k5049ZgIszsubn23b"
    "tjVjy1c9d2zZin+QctXPOeeUUonSfoSVut39SimP/NuliHKKBKuUiKYZRClldynlzp/+J//0jl/7"
    "tW2HI+Lowx6ecnzmM5/u/c7v/E7Zvn27ycBZDVWllzf/5U9F7ykrozl6+sMA8rJ4fO+L1UQ0c6f4"
    "3sFoBnc1UT3zq9G/8WjU3/xWHP6jQyf13Cpie0SYYC7FBC4WAqlTBYDLp6amlr397W9Pz3nO86/J"
    "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"
)
    st.markdown(f"""
    <div class="sb-brand-row">
        <img class="sb-logo sb-logo-dark"  src="data:image/png;base64,{_LOGO_DARK}"  alt="Adchor" />
        <img class="sb-logo sb-logo-light" src="data:image/png;base64,{_LOGO_LIGHT}" alt="Adchor" />
    </div>
    """, unsafe_allow_html=True)

    # ── Progress bar ──────────────────────────────────────────────────────────
    _prog_pct = min(100, int((st.session_state.step - 1) / 3 * 100))
    st.markdown(f"""
    <div class="sb-prog-wrap">
        <div class="sb-prog-label">Progress <span>{_prog_pct}%</span></div>
        <div class="sb-prog-track"><div class="sb-prog-fill" style="width:{_prog_pct}%"></div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Step indicators ───────────────────────────────────────────────────────
    _step_info = [
        ("Upload Brief",  "PDF & transcript"),
        ("Review SOW",    "AI draft content"),
        ("Pricing",       "Line items & total"),
        ("Download PDF",  "Export & send"),
    ]
    _steps_html = ""
    for i, (name, desc) in enumerate(_step_info, 1):
        if i < st.session_state.step:
            _state = "step-done"
            _icon  = "&#10003;"
        elif i == st.session_state.step:
            _state = "step-active"
            _icon  = str(i)
        else:
            _state = "step-pend"
            _icon  = str(i)
        _steps_html += f"""
        <div class="sb-step-item {_state}">
            <div class="sb-step-icon">{_icon}</div>
            <div>
                <div class="sb-step-name">{name}</div>
                <div class="sb-step-desc">{desc}</div>
            </div>
        </div>"""
    st.markdown(_steps_html, unsafe_allow_html=True)
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
            &#9888; API key not configured.<br>
            <span style="color:#5a6278;">Contact your Adchor admin.</span>
        </div>""", unsafe_allow_html=True)
    st.divider()

    # MODIFIED: use centralised reset helper
    if st.button("&#8635; Start New SOW", use_container_width=True):
        _reset_sow_state()
        st.rerun()

    # ── Active Client chip ────────────────────────────────────────────────────
    _client_name = (st.session_state.sow_data or {}).get("client_name", "") or "No active client"
    st.markdown(f"""
    <div class="sb-client-chip">
        <div class="sb-chip-label">Active Client</div>
        <div class="sb-chip-row">
            <div class="sb-chip-dot"></div>
            <div class="sb-chip-name">{_client_name}</div>
        </div>
    </div>
    <div style='margin-top:14px;color:#141828;font-size:9px;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;'>Adchor&#8482; &middot; 2026</div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 -- INPUT  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.markdown("""
    <div class="hero-bar">
        <div class="hero-eyebrow">Step 1 of 4</div>
        <div class="hero-title">Upload Brief &amp; Transcript</div>
        <div class="hero-sub">Upload your filled creative brief PDF and call transcript &mdash; our AI extracts everything and drafts the SOW</div>
    </div>
    """, unsafe_allow_html=True)

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
                placeholder="Paste the full call transcript here. The AI will extract decisions, requirements, and context...",
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
        if st.button("Generate SOW", use_container_width=True, type="primary", disabled=disabled):
            if not has_key:
                st.error("AI generation is not available -- API key not configured. Contact your Adchor admin.")
            else:
                with st.spinner("Reading your brief and transcript — drafting the SOW..."):
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
    st.markdown("""
    <div class="hero-bar">
        <div class="hero-eyebrow">Step 2 of 4</div>
        <div class="hero-title">Review &amp; Edit SOW Content</div>
        <div class="hero-sub">All fields are editable &mdash; refine the AI draft before moving to pricing</div>
    </div>
    """, unsafe_allow_html=True)

    sow = st.session_state.sow_data or {}

    # ════════════════════════════════════════════════════════════════════════════
    # AI INSTRUCTION BOX — whole-SOW editor via free-form Claude instruction
    # ════════════════════════════════════════════════════════════════════════════
    st.markdown(
        '<div class="ai-instr-panel">'
        '<div class="ai-instr-label">AI SOW Editor</div>'
        '<div class="ai-instr-sub">'
        'Tell the AI what to fix and it will update all relevant fields automatically. '
        'You can still edit anything manually after the update.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    _ai_sow_instr = st.text_area(
        "AI instruction",
        key="ai_sow_instruction",
        height=85,
        label_visibility="collapsed",
        placeholder=(
            'e.g. "The client name is wrong — update it to Acme Corp."  ·  '
            '"Remove brand audit from services and add social media management."  ·  '
            '"Rewrite the project overview to sound more strategic and concise."  ·  '
            '"The assumptions are incomplete — add: client provides all assets by Day 5."'
        ),
    )

    _upd_col, _ = st.columns([2, 3])
    with _upd_col:
        _ai_sow_clicked = st.button(
            "Update SOW",
            type="primary",
            use_container_width=True,
            key="btn_ai_sow_update",
        )

    if _ai_sow_clicked:
        if not _ai_sow_instr.strip():
            st.warning("Please type an instruction before submitting.")
        elif not st.session_state.get("api_key"):
            st.error("API key not configured. Contact your Adchor admin.")
        else:
            with st.spinner("Updating your SOW…"):
                try:
                    _updated_sow = _ai_update_sow(
                        sow,
                        _ai_sow_instr.strip(),
                        st.session_state.api_key,
                    )
                    # Write updated SOW back as the source of truth
                    st.session_state.sow_data = _updated_sow
                    # Clear all field widget keys so they reinitialise from new sow_data
                    for _wk in _SOW_FIELD_WIDGET_KEYS:
                        st.session_state.pop(_wk, None)
                    for _wi in range(30):
                        for _wk in [f"st_{_wi}", f"sd_{_wi}", f"ss_{_wi}", f"del_{_wi}"]:
                            st.session_state.pop(_wk, None)
                    # Clear the instruction box
                    st.session_state.pop("ai_sow_instruction", None)
                    st.session_state["ai_sow_update_status"] = (
                        "✓ SOW updated! Review the fields below — you can still edit anything manually."
                    )
                    st.rerun()
                except Exception as _exc:
                    st.error(f"Update failed: {_exc}")

    if st.session_state.get("ai_sow_update_status"):
        st.success(st.session_state["ai_sow_update_status"])
        st.session_state["ai_sow_update_status"] = ""

    st.divider()

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
        with st.expander(f"{label}", expanded=(i == 0)):
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
    with st.expander("AI Reword Assistant", expanded=False):
        st.caption(
            "Select a SOW field, load its content, ask the AI to improve it, "
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
            if st.button("Reword", type="primary", use_container_width=True, key="btn_reword"):
                if not input_text.strip():
                    st.warning("Please load a field or paste some text first.")
                elif not instruction.strip():
                    st.warning("Please choose or enter an instruction.")
                elif not st.session_state.get("api_key"):
                    st.error("API key not configured. Contact your Adchor admin.")
                else:
                    with st.spinner("Refining your copy…"):
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
                "letter-spacing:1px;text-transform:uppercase;'>✓ AI suggestion</span>"
                " <span style='color:#5a6278;font-size:11px;'>(editable before applying)</span>",
                unsafe_allow_html=True,
            )
            edited_result = st.text_area(
                "AI suggestion",
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
                    # Remove the widget's cached state so it re-reads from
                    # value= on the next render (avoids the "default value +
                    # Session State API" Streamlit warning).
                    st.session_state.pop(_t_wkey, None)
                    st.success(f"✓ Applied to '{selected_label}'! Scroll up to review.")
                    st.rerun()

            with _ap2:
                if st.button("✕ Discard", use_container_width=True, key="btn_discard"):
                    st.session_state.ai_reword_result = ""
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
    st.markdown("""
    <div class="hero-bar">
        <div class="hero-eyebrow">Step 3 of 4</div>
        <div class="hero-title">Investment &amp; Pricing</div>
        <div class="hero-sub">Price the services from your SOW &mdash; click any service to add it, then set price and quantity</div>
    </div>
    """, unsafe_allow_html=True)

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
        disc_raw = st.text_input("Discount (%)", value=str(int(st.session_state.sow_discount)) if st.session_state.sow_discount else "", placeholder="0", key="disc_input")
        try:
            discount_pct = float(str(disc_raw).replace(",","").replace("%","").strip()) if disc_raw else 0.0
            discount_pct = max(0.0, min(100.0, discount_pct))
        except ValueError:
            discount_pct = 0.0
        discount_amt = subtotal * discount_pct / 100
        st.session_state.sow_discount = discount_pct
        final_total = subtotal - discount_amt
        st.session_state.sow_total = final_total
        disc_line = f'<div class="sub">Discount ({discount_pct:.0f}%): -${discount_amt:,.0f}</div>' if discount_pct else ""
        st.markdown(f"""
        <div class="pricing-total">
            <div class="sub">Subtotal: ${subtotal:,.0f}</div>
            {disc_line}
            Total Investment: ${final_total:,.0f}
        </div>""", unsafe_allow_html=True)

    # ── Section D: Library (collapsed) ────────────────────────────────────────
    with st.expander("Add from Service Library or save new item"):
        lib_col1, lib_col2 = st.columns(2)
        with lib_col1:
            st.markdown("**Quick-add from library**")
            if lib_items:
                lib_labels = [it["name"] for it in lib_items]
                sel = st.selectbox("Pick a service", ["-- Select --"] + lib_labels, key="lib_sel", label_visibility="collapsed")
                if sel != "-- Select --" and st.button("Add to pricing", use_container_width=True):
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
            "Download Pricing Library (commit to GitHub to persist)",
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
    st.markdown("""
    <div class="hero-bar">
        <div class="hero-eyebrow">Step 4 of 4</div>
        <div class="hero-title">Download &amp; Send</div>
        <div class="hero-sub">Generate your branded PDF and deliver via Adobe Sign</div>
    </div>
    """, unsafe_allow_html=True)

    sow     = st.session_state.sow_data or {}
    client  = sow.get("client_name", "Client")
    project = sow.get("project_name", "Project")
    total        = st.session_state.sow_total
    discount_pct = st.session_state.sow_discount
    subtotal_s4  = sum(i.get("total", 0) for i in st.session_state.pricing_items)
    discount_amt = subtotal_s4 * discount_pct / 100

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
                    discount=discount_amt,
                )
                filename = f"{client}_{project}_SOW.pdf".replace(" ", "_").replace("/", "-")

                # MODIFIED: capture the return value of download_button.
                # It returns True on the rerun triggered by the click,
                # which is the reliable signal that the file was sent to the browser.
                _downloaded = st.download_button(
                    label=f"Download {filename}",
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
                "color:#ffb400;'>Click the button above to download the PDF before finishing.</div>",
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
