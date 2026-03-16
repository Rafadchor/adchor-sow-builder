"""
Adchor SOW Builder — Streamlit Web App
Team URL: deploy to Streamlit Community Cloud or sow.adchor.com

Flow:
  Step 1 — Upload filled creative brief PDF + call transcript
  Step 2 — Review & edit AI-generated SOW content
  Step 3 — Build pricing (live auto-total, growing library)
  Step 4 — Download PDF → send via Adobe Sign
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

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
/* ── Global ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar header ── */
.adchor-header {
    background: linear-gradient(135deg, #021de0 0%, #014bf7 100%);
    padding: 16px 20px 14px;
    border-radius: 10px;
    border-bottom: 3px solid #00ff79;
    margin-bottom: 4px;
}
.adchor-header h2 { color: white; font-size: 18px; margin: 0 0 2px; font-weight: 800; letter-spacing: 1px; }
.adchor-header p  { color: rgba(255,255,255,0.65); font-size: 11px; margin: 0; }

/* ── Step pills ── */
.step-row { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0; }
.pill { padding: 5px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.pill-done    { background: #00ff79; color: #2f3234; }
.pill-active  { background: #014bf7; color: white; }
.pill-pending { background: #F4F6FB; color: #595959; border: 1px solid #D5DAE8; }

/* ── Section headers ── */
.sec-bar {
    background: #021de0;
    color: white;
    padding: 10px 16px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.5px;
    border-left: 5px solid #00ff79;
    margin: 14px 0 10px;
}

/* ── Scope block ── */
.scope-header {
    background: #021de0;
    color: white;
    padding: 10px 16px;
    border-radius: 6px 6px 0 0;
    font-weight: 700;
    font-size: 13px;
    border-left: 5px solid #00ff79;
    margin-top: 12px;
}

/* ── Pricing total ── */
.pricing-total {
    background: #021de0;
    color: white;
    padding: 14px 20px;
    border-radius: 8px;
    text-align: right;
    font-size: 20px;
    font-weight: 800;
    margin-top: 10px;
    border-left: 5px solid #00ff79;
}
.pricing-total .sub { font-size: 12px; opacity: 0.65; font-weight: 400; }

/* ── Info box ── */
.info-box {
    background: #EEF3FF;
    border: 1.5px solid #014bf7;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 6px 0 12px;
    border-left: 5px solid #014bf7;
    font-size: 13px;
    color: #2f3234;
}

/* ── Download cta ── */
.dl-note {
    background: #F0FFF7;
    border: 1px solid #00cc62;
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 12px;
    font-size: 13px;
    color: #2f3234;
}
</style>
""", unsafe_allow_html=True)

# ── Pricing Library (load once per session) ───────────────────────────────────
LIBRARY_PATH = Path(__file__).parent / "pricing_library.json"

def load_library():
    if LIBRARY_PATH.exists():
        with open(LIBRARY_PATH) as f:
            return json.load(f)
    return {"items": []}

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
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="adchor-header">
        <h2>⚡ ADCHOR</h2>
        <p>SOW Builder · Powered by Claude AI</p>
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

    # API Key
    env_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if env_key:
        st.success("✓ API key loaded")
        st.session_state.api_key = env_key
    else:
        api_input = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-...",
            help="Set ANTHROPIC_API_KEY as an environment variable / Streamlit secret to avoid entering each time.",
        )
        st.session_state.api_key = api_input

    st.divider()

    # Reset
    if st.button("↺ Start New SOW", use_container_width=True):
        for k in ["step", "brief_fields", "transcript", "sow_data", "pricing_items", "sow_discount", "sow_total"]:
            st.session_state[k] = defaults[k]
        st.rerun()

    st.caption("Adchor · 2026")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — INPUT
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.markdown('<div class="sec-bar">STEP 1 — UPLOAD BRIEF & TRANSCRIPT</div>', unsafe_allow_html=True)
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
            from brief_extractor import extract_brief_fields
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
                st.warning("No filled fields found — brief may not be completed yet.")
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
        if st.button("Skip AI — Enter Manually", use_container_width=True):
            from sow_generator import get_empty_sow
            st.session_state.sow_data = get_empty_sow()
            st.session_state.step = 2
            st.rerun()

    with col_gen:
        has_input = bool(st.session_state.brief_fields or st.session_state.transcript)
        has_key   = bool(st.session_state.get("api_key"))
        disabled  = not (has_input and has_key)

        if st.button("⚡ Generate SOW with Claude", use_container_width=True, type="primary", disabled=disabled):
            with st.spinner("Claude is reading your brief and transcript — drafting the SOW..."):
                from sow_generator import generate_sow_content
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
                    st.error(f"Generation failed: {e}")

        if disabled and has_input and not has_key:
            st.caption("⚠️ Add your Anthropic API key in the sidebar to use AI generation.")
        elif disabled:
            st.caption("Upload a brief or paste a transcript to continue.")


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — REVIEW & EDIT CONTENT
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown('<div class="sec-bar">STEP 2 — REVIEW & EDIT SOW CONTENT</div>', unsafe_allow_html=True)
    st.caption("All fields are editable. Refine Claude's draft before moving to pricing.")

    sow = st.session_state.sow_data or {}

    # ── Client Details ────────────────────────────────────────────────────────
    with st.expander("Client & Project Details", expanded=True):
        c1, c2, c3 = st.columns(3)
        sow["client_name"]   = c1.text_input("Client Name",          value=sow.get("client_name", ""))
        sow["project_name"]  = c2.text_input("Project / Campaign",   value=sow.get("project_name", ""))
        sow["version"]       = c3.text_input("Version",              value=sow.get("version", "v1.0"))

        c4, c5, c6 = st.columns(3)
        sow["account_lead"]  = c4.text_input("Account Lead",         value=sow.get("account_lead", ""))
        sow["business_owner"]= c5.text_input("Business Owner",       value=sow.get("business_owner", ""))
        sow["date"]          = c6.text_input("Date",                 value=sow.get("date", datetime.today().strftime("%B %d, %Y")))

        c7, c8 = st.columns(2)
        sow["final_deadline"]= c7.text_input("Final Deadline",       value=sow.get("final_deadline", ""))
        sow["budget_range"]  = c8.text_input("Budget Range",         value=sow.get("budget_range", ""))

    # ── Strategic Summary ─────────────────────────────────────────────────────
    with st.expander("Strategic Summary", expanded=True):
        sow["why_now"] = st.text_area(
            "Why This, Why Now",
            value=sow.get("why_now", ""),
            height=70,
            help="The trigger — what changed or what window exists.",
        )
        sow["project_overview"] = st.text_area(
            "Project Overview",
            value=sow.get("project_overview", ""),
            height=100,
            help="Executive summary of the engagement.",
        )
        sow["core_message"] = st.text_input(
            "Core Message",
            value=sow.get("core_message", ""),
            help="One sentence that drives everything.",
        )

    # ── Scope Sections ────────────────────────────────────────────────────────
    st.markdown('<div class="sec-bar">SCOPE OF SERVICES</div>', unsafe_allow_html=True)
    st.caption("Each section becomes a collapsible block in the SOW. Add as many as needed.")

    sections = sow.get("scope_sections", [{"title": "", "description": "", "services": [], "deliverables": []}])

    for i, sec in enumerate(sections):
        label = sec.get("title") or f"Section {i + 1}"
        with st.expander(f"▾  {label}", expanded=(i == 0)):
            sec["title"] = st.text_input("Section Title", value=sec.get("title", ""), key=f"st_{i}")
            sec["description"] = st.text_area("Description", value=sec.get("description", ""), height=80, key=f"sd_{i}")

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
    with st.expander("Assumptions & Out of Scope"):
        c_left, c_right = st.columns(2)
        with c_left:
            assume_raw = st.text_area(
                "Assumptions (one per line)",
                value="\n".join(sow.get("assumptions", [])),
                height=150,
            )
            sow["assumptions"] = [l.strip() for l in assume_raw.splitlines() if l.strip()]

        with c_right:
            oos_raw = st.text_area(
                "Out of Scope (one per line)",
                value="\n".join(sow.get("out_of_scope", [])),
                height=150,
            )
            sow["out_of_scope"] = [l.strip() for l in oos_raw.splitlines() if l.strip()]

        sow["timeline_notes"] = st.text_input(
            "Timeline Notes",
            value=sow.get("timeline_notes", ""),
        )
        sow["review_rounds"] = st.text_input(
            "Creative Review Rounds",
            value=sow.get("review_rounds", "2"),
        )

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
# STEP 3 — PRICING BUILDER
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    st.markdown('<div class="sec-bar">STEP 3 — INVESTMENT & PRICING</div>', unsafe_allow_html=True)
    st.caption("Price the services from your SOW. Click any service below to add it, then set the price and quantity.")

    library   = st.session_state.pricing_library
    lib_items = library.get("items", [])
    items     = st.session_state.pricing_items
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
        st.info("No items yet — click a service above or use '+ Add Row' below.")
    else:
        # Table header
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

            # Qty — plain text input, parse to int
            qty_raw = c3.text_input("", value=str(item.get("qty", 1)), key=f"q_{i}", label_visibility="collapsed")
            try:
                item["qty"] = max(1, int(qty_raw))
            except ValueError:
                item["qty"] = 1

            # Unit price — plain text input with $ hint, parse to float
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

    # ── Add Row button ─────────────────────────────────────────────────────────
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
                sel = st.selectbox("Pick a service", ["— Select —"] + lib_labels, key="lib_sel", label_visibility="collapsed")
                if sel != "— Select —" and st.button("Add to pricing ➕", use_container_width=True):
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
        if st.button("Generate PDF →", use_container_width=True, type="primary"):
            st.session_state.step = 4
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — DOWNLOAD
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    st.markdown('<div class="sec-bar">STEP 4 — DOWNLOAD & SEND</div>', unsafe_allow_html=True)

    sow     = st.session_state.sow_data or {}
    client  = sow.get("client_name", "Client")
    project = sow.get("project_name", "Project")
    total   = st.session_state.sow_total
    discount= st.session_state.sow_discount

    st.success(f"✓  SOW ready: **{client} — {project}**  ·  Investment: **${total:,.0f}**")

    col_pdf, col_steps = st.columns([1, 1])

    with col_pdf:
        st.markdown("#### Download PDF")
        st.markdown("Branded PDF ready for Adobe Sign.")
        with st.spinner("Building PDF..."):
            from sow_pdf import build_sow_pdf
            try:
                pdf_bytes = build_sow_pdf(
                    sow_data=sow,
                    pricing_items=st.session_state.pricing_items,
                    total=total,
                    discount=discount,
                )
                filename = f"{client}_{project}_SOW.pdf".replace(" ", "_").replace("/", "-")
                st.download_button(
                    label=f"⬇ Download {filename}",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"PDF generation error: {e}")

    with col_steps:
        st.markdown("#### Next Steps")
        st.markdown("""
        <div class="dl-note">
        <strong>After downloading:</strong><br><br>
        1. Open <strong>Adobe Sign</strong><br>
        2. Upload the PDF and add signature fields for the client and your account lead<br>
        3. Send for e-signature<br>
        4. Once fully signed, attach to the <strong>Monday.com</strong> project card and move to Active<br><br>
        <em>Tip: Keep the PDF file name as-is — it follows the Client_Project_SOW convention.</em>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    if st.button("← Back to Pricing"):
        st.session_state.step = 3
        st.rerun()
