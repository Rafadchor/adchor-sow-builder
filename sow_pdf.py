"""
Generate a branded Adchor SOW PDF using ReportLab.
Mirrors the design language of the Creative Brief.
"""
import io
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Brand Colors ──────────────────────────────────────────────────────────────
BLUE      = HexColor('#014bf7')
DARK_BLUE = HexColor('#021de0')
GREEN     = HexColor('#00ff79')
TEXT_DARK = HexColor('#2f3234')
TEXT_GRAY = HexColor('#595959')
DIVIDER   = HexColor('#D5DAE8')
FIELD_BG  = HexColor('#F4F6FB')
CORE_BG   = HexColor('#EEF3FF')
LIGHT_GREEN = HexColor('#F0FFF7')
MID_GREEN = HexColor('#00cc62')

# ── Layout ────────────────────────────────────────────────────────────────────
W, H       = letter
LM         = 46
RM         = W - 46
CW         = RM - LM
HEADER_H   = 125
FOOTER_H   = 100
CT         = H - HEADER_H - 16
CB         = FOOTER_H + 8

# ── Asset Paths (works with direct run, import, and runpy) ────────────────────
_DIR       = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
HEADER_IMG = os.path.join(_DIR, 'assets', 'header.png')
FOOTER_IMG = os.path.join(_DIR, 'assets', 'footer.png')

# ── Fonts ─────────────────────────────────────────────────────────────────────
# Fonts are bundled in assets/ so they work on both local VM and Streamlit Cloud
_ASSETS = os.path.join(_DIR, 'assets')
REG  = 'Poppins'
BOLD = 'Poppins-Bold'
SEMI = 'Poppins-Medium'

def _setup_fonts():
    try:
        for name, fname in [(REG, 'Poppins-Regular.ttf'), (BOLD, 'Poppins-Bold.ttf'), (SEMI, 'Poppins-Medium.ttf')]:
            pdfmetrics.registerFont(TTFont(name, os.path.join(_ASSETS, fname)))
    except Exception:
        pass  # Fall back to Helvetica if fonts unavailable


class SOWDoc:
    """ReportLab canvas wrapper — mirrors BriefPDF pattern."""

    def __init__(self, buf):
        self.c    = canvas.Canvas(buf, pagesize=letter)
        self.page = 1
        self.y    = CT
        self._header()
        self._page_num()

    def _header(self):
        if os.path.exists(HEADER_IMG):
            self.c.drawImage(HEADER_IMG, 0, H - HEADER_H, W, HEADER_H,
                             preserveAspectRatio=True, anchor='sw', mask='auto')

    def _footer(self):
        if os.path.exists(FOOTER_IMG):
            self.c.drawImage(FOOTER_IMG, 0, 0, W, FOOTER_H,
                             preserveAspectRatio=True, anchor='sw', mask='auto')

    def _page_num(self):
        self.c.setFillColor(TEXT_GRAY)
        self.c.setFont(REG, 7)
        self.c.drawRightString(RM, FOOTER_H - 4, f'Page {self.page}')

    def new_page(self):
        self._footer()
        self.c.showPage()
        self.page += 1
        self.y = CT
        self._header()
        self._page_num()

    def need(self, h):
        if self.y - h < CB:
            self.new_page()

    def gap(self, h=8):
        self.y -= h

    def _wrap(self, text, font, size, max_w):
        words = str(text).split()
        lines, line = [], ''
        for w in words:
            test = f'{line} {w}'.strip()
            if self.c.stringWidth(test, font, size) <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines or ['']

    def h1(self, text):
        """Large title text."""
        self.need(30)
        self.c.setFillColor(TEXT_DARK)
        self.c.setFont(BOLD, 20)
        self.c.drawString(LM, self.y, text)
        self.y -= 20
        self.c.setFillColor(BLUE)
        self.c.setLineWidth(2.5)
        self.c.line(LM, self.y, LM + self.c.stringWidth(text, BOLD, 20) * 0.6, self.y)
        self.y -= 10

    def section_bar(self, title, color=DARK_BLUE):
        """Full-width dark section header bar."""
        self.need(50)
        self.gap(14)
        bh = 28
        self.c.setFillColor(color)
        self.c.rect(LM, self.y - bh, CW, bh, fill=1, stroke=0)
        # Green accent line below
        self.c.setFillColor(GREEN)
        self.c.rect(LM, self.y - bh - 2, CW, 2, fill=1, stroke=0)
        self.c.setFillColor(white)
        self.c.setFont(BOLD, 10)
        self.c.drawString(LM + 14, self.y - bh / 2 - 4, title.upper())
        self.y -= bh + 10

    def label(self, text):
        """Small blue uppercase label."""
        self.c.setFillColor(BLUE)
        self.c.setFont(SEMI, 7)
        self.c.drawString(LM, self.y, text.upper())
        self.y -= 10

    def body(self, text, indent=0, color=TEXT_DARK, size=9, font=None):
        """Wrapped body paragraph."""
        font = font or REG
        x = LM + indent
        lines = self._wrap(text, font, size, CW - indent)
        self.need(len(lines) * 12 + 4)
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        for ln in lines:
            self.c.drawString(x, self.y, ln)
            self.y -= 12
        self.y -= 3

    def bullet(self, text, indent=12):
        """Single bullet point."""
        x = LM + indent
        max_w = CW - indent - 10
        lines = self._wrap(text, REG, 8.5, max_w)
        self.need(len(lines) * 11 + 3)
        self.c.setFillColor(BLUE)
        self.c.circle(LM + indent - 6, self.y - 3, 2, fill=1, stroke=0)
        self.c.setFillColor(TEXT_DARK)
        self.c.setFont(REG, 8.5)
        for i, ln in enumerate(lines):
            self.c.drawString(x, self.y, ln)
            self.y -= 11
        self.y -= 2

    def sub_header(self, text):
        """Bold sub-section label."""
        self.need(20)
        self.gap(4)
        self.c.setFillColor(TEXT_DARK)
        self.c.setFont(BOLD, 9)
        self.c.drawString(LM, self.y, text)
        self.y -= 13

    def divider(self):
        self.c.setStrokeColor(DIVIDER)
        self.c.setLineWidth(0.3)
        self.c.line(LM, self.y, RM, self.y)
        self.y -= 8

    def two_col_field(self, label1, val1, label2, val2):
        """Two-column info pair."""
        hw = (CW - 12) / 2
        self.need(36)
        for i, (lbl, val) in enumerate([(label1, val1), (label2, val2)]):
            x = LM + i * (hw + 12)
            self.c.setFillColor(BLUE)
            self.c.setFont(SEMI, 6.5)
            self.c.drawString(x, self.y, lbl.upper())
            # Value box
            self.c.setFillColor(FIELD_BG)
            self.c.setStrokeColor(DIVIDER)
            self.c.setLineWidth(0.5)
            self.c.roundRect(x, self.y - 20, hw, 18, 3, fill=1, stroke=1)
            self.c.setFillColor(TEXT_DARK)
            self.c.setFont(REG, 8.5)
            # Truncate if too long
            val_str = str(val or '—')
            while self.c.stringWidth(val_str, REG, 8.5) > hw - 10 and len(val_str) > 3:
                val_str = val_str[:-4] + '...'
            self.c.drawString(x + 6, self.y - 14, val_str)
        self.y -= 28

    def info_box(self, text, bg=CORE_BG, border=BLUE):
        """Highlighted info box for key content like core message."""
        lines = self._wrap(text, REG, 9, CW - 20)
        bh = len(lines) * 13 + 16
        self.need(bh + 6)
        self.c.setFillColor(bg)
        self.c.setStrokeColor(border)
        self.c.setLineWidth(1.5)
        self.c.roundRect(LM, self.y - bh, CW, bh, 4, fill=1, stroke=1)
        # Left accent bar
        self.c.setFillColor(border)
        self.c.roundRect(LM, self.y - bh, 5, bh, 2, fill=1, stroke=0)
        self.c.setFillColor(TEXT_DARK)
        self.c.setFont(REG, 9)
        ty = self.y - 12
        for ln in lines:
            self.c.drawString(LM + 14, ty, ln)
            ty -= 13
        self.y -= bh + 8

    def scope_section_header(self, title):
        """Collapsible-style scope section header — dark navy with dropdown indicator."""
        self.need(50)
        self.gap(10)
        bh = 30
        self.c.setFillColor(DARK_BLUE)
        self.c.rect(LM, self.y - bh, CW, bh, fill=1, stroke=0)
        # Green left accent
        self.c.setFillColor(GREEN)
        self.c.rect(LM, self.y - bh, 5, bh, fill=1, stroke=0)
        # Title
        self.c.setFillColor(white)
        self.c.setFont(BOLD, 10)
        self.c.drawString(LM + 16, self.y - bh / 2 - 4, title)
        # "▼" indicator on right (like Qwilr)
        self.c.setFont(REG, 9)
        self.c.drawString(RM - 16, self.y - bh / 2 - 4, '▾')
        self.y -= bh

    def save(self):
        self._footer()
        self.c.save()


# ── Cover Page ────────────────────────────────────────────────────────────────

def _cover_page(doc, sow_data):
    c = doc.c

    # "STATEMENT OF WORK" title
    doc.gap(8)
    doc.h1('STATEMENT OF WORK')
    doc.gap(6)

    # Client × Adchor
    client = sow_data.get('client_name', 'Client')
    project = sow_data.get('project_name', 'Project')
    c.setFillColor(BLUE)
    c.setFont(BOLD, 14)
    c.drawString(LM, doc.y, project)
    doc.y -= 16
    c.setFillColor(TEXT_GRAY)
    c.setFont(REG, 10)
    c.drawString(LM, doc.y, f'{client}  ×  Adchor')
    doc.y -= 20

    doc.divider()
    doc.gap(4)

    # Key fields grid
    lead  = sow_data.get('account_lead', '')
    owner = sow_data.get('business_owner', '')
    date  = sow_data.get('date', datetime.today().strftime('%B %d, %Y'))
    ver   = sow_data.get('version', 'v1.0')
    ddl   = sow_data.get('final_deadline', '')
    bgt   = sow_data.get('budget_range', '')

    doc.two_col_field('Prepared For', client,    'Prepared By', 'Adchor')
    doc.two_col_field('Account Lead', lead,       'Business Owner', owner)
    doc.two_col_field('Date',         date,       'Version', ver)
    doc.two_col_field('Final Deadline', ddl,      'Investment Range', bgt)

    doc.gap(10)
    doc.divider()
    doc.gap(8)

    # Why Now
    why_now = sow_data.get('why_now', '')
    if why_now:
        doc.label('Why This, Why Now')
        doc.body(why_now, size=9)
        doc.gap(6)

    # Project Overview
    overview = sow_data.get('project_overview', '')
    if overview:
        doc.label('Project Overview')
        doc.body(overview, size=9)
        doc.gap(6)

    # Core Message
    core = sow_data.get('core_message', '')
    if core:
        doc.label('Core Message')
        doc.info_box(core)


# ── Scope of Services ─────────────────────────────────────────────────────────

def _scope_page(doc, sow_data):
    doc.section_bar('Scope of Services')

    sections = sow_data.get('scope_sections', [])
    for section in sections:
        title = section.get('title', 'Scope Section')
        description = section.get('description', '')
        services = section.get('services', [])
        deliverables = section.get('deliverables', [])

        doc.scope_section_header(title)
        doc.gap(6)

        if description:
            doc.body(description, size=9, color=TEXT_GRAY)
            doc.gap(4)

        if services:
            doc.sub_header('Services Include:')
            for s in services:
                if s.strip():
                    doc.bullet(s)

        if deliverables:
            doc.gap(4)
            doc.sub_header('Primary Deliverables:')
            for d in deliverables:
                if d.strip():
                    doc.bullet(d)

        doc.gap(10)
        doc.divider()


# ── Investment / Pricing ──────────────────────────────────────────────────────

def _pricing_page(doc, pricing_items, total, discount):
    doc.section_bar('Investment', color=DARK_BLUE)

    if not pricing_items:
        doc.body('Investment details to be confirmed.', color=TEXT_GRAY)
        return

    # Table setup
    col_w = [220, 120, 60, 80, 80]
    col_x = [LM, LM+220, LM+340, LM+400, LM+480]
    headers = ['Service', 'Description', 'Qty', 'Unit Price', 'Total']

    doc.need(len(pricing_items) * 24 + 44)

    # Header row
    doc.c.setFillColor(DARK_BLUE)
    doc.c.rect(LM, doc.y - 22, CW, 22, fill=1, stroke=0)
    doc.c.setFillColor(white)
    doc.c.setFont(SEMI, 8.5)
    for lbl, cx in zip(headers, col_x):
        doc.c.drawString(cx + 5, doc.y - 15, lbl)
    doc.y -= 22

    # Data rows
    for r, item in enumerate(pricing_items):
        bg = FIELD_BG if r % 2 == 0 else white
        row_h = 22
        doc.c.setFillColor(bg)
        doc.c.setStrokeColor(DIVIDER)
        doc.c.setLineWidth(0.3)
        doc.c.rect(LM, doc.y - row_h, CW, row_h, fill=1, stroke=1)

        doc.c.setFillColor(TEXT_DARK)
        doc.c.setFont(REG, 8.5)

        vals = [
            item.get('name', ''),
            item.get('description', ''),
            str(item.get('qty', 1)),
            f"${item.get('unit_price', 0):,.0f}",
            f"${item.get('total', 0):,.0f}",
        ]
        for val, cx, cw in zip(vals, col_x, col_w):
            # Truncate if needed
            v = str(val)
            while doc.c.stringWidth(v, REG, 8.5) > cw - 8 and len(v) > 3:
                v = v[:-4] + '...'
            doc.c.drawString(cx + 5, doc.y - 15, v)

        doc.y -= row_h

    # Subtotal / discount / total footer
    doc.gap(4)
    subtotal = sum(i.get('total', 0) for i in pricing_items)

    if discount and discount > 0:
        # Subtotal row
        doc.c.setFillColor(FIELD_BG)
        doc.c.rect(LM, doc.y - 20, CW, 20, fill=1, stroke=0)
        doc.c.setFillColor(TEXT_GRAY)
        doc.c.setFont(REG, 8.5)
        doc.c.drawString(LM + 10, doc.y - 14, 'Subtotal')
        doc.c.drawRightString(RM - 8, doc.y - 14, f'${subtotal:,.0f}')
        doc.y -= 20

        # Discount row
        doc.c.setFillColor(LIGHT_GREEN)
        doc.c.rect(LM, doc.y - 20, CW, 20, fill=1, stroke=0)
        doc.c.setFillColor(MID_GREEN)
        doc.c.setFont(REG, 8.5)
        doc.c.drawString(LM + 10, doc.y - 14, 'Discount')
        doc.c.drawRightString(RM - 8, doc.y - 14, f'-${discount:,.0f}')
        doc.y -= 20

    # Total row
    doc.c.setFillColor(DARK_BLUE)
    doc.c.rect(LM, doc.y - 28, CW, 28, fill=1, stroke=0)
    doc.c.setFillColor(GREEN)
    doc.c.rect(LM, doc.y - 28, 5, 28, fill=1, stroke=0)
    doc.c.setFillColor(white)
    doc.c.setFont(BOLD, 11)
    doc.c.drawString(LM + 14, doc.y - 18, 'Total Investment')
    doc.c.drawRightString(RM - 8, doc.y - 18, f'${total:,.0f}')
    doc.y -= 36


# ── Assumptions & Out of Scope ────────────────────────────────────────────────

def _assumptions_page(doc, sow_data):
    assumptions = sow_data.get('assumptions', [])
    out_of_scope = sow_data.get('out_of_scope', [])
    timeline = sow_data.get('timeline_notes', '')
    review_rounds = sow_data.get('review_rounds', '2')

    if assumptions or out_of_scope or timeline:
        doc.section_bar('Project Terms & Assumptions', color=BLUE)

    if timeline:
        doc.sub_header('Timeline & Milestones')
        doc.body(timeline, size=9)
        doc.gap(6)

    if review_rounds:
        doc.sub_header('Creative Review Rounds')
        doc.body(f'This SOW includes {review_rounds} round(s) of consolidated client feedback. '
                 'Additional rounds are available as a change order.', size=9)
        doc.gap(6)

    if assumptions:
        doc.sub_header('Assumptions')
        for a in assumptions:
            if a.strip():
                doc.bullet(a)
        doc.gap(8)

    if out_of_scope:
        doc.sub_header('Out of Scope')
        for o in out_of_scope:
            if o.strip():
                doc.bullet(o)
        doc.gap(8)


# ── Signature Block ────────────────────────────────────────────────────────────

def _signature_page(doc, sow_data):
    doc.section_bar('Authorization & Signature', color=DARK_BLUE)
    doc.gap(6)

    client = sow_data.get('client_name', 'Client')
    owner  = sow_data.get('business_owner', '')
    lead   = sow_data.get('account_lead', '')

    doc.body(
        f'By signing below, {client} authorizes Adchor to proceed with the scope of work '
        f'outlined in this document under the terms described herein.',
        size=9, color=TEXT_GRAY
    )
    doc.gap(16)

    # Two signature boxes
    hw = (CW - 20) / 2
    for i, (party, name) in enumerate([
        (f'{client} — Authorized Signature', owner),
        ('Adchor — Account Lead', lead),
    ]):
        x = LM + i * (hw + 20)
        # Line
        doc.c.setStrokeColor(DARK_BLUE)
        doc.c.setLineWidth(1)
        doc.c.line(x, doc.y - 30, x + hw, doc.y - 30)
        # Labels
        doc.c.setFillColor(TEXT_DARK)
        doc.c.setFont(BOLD, 8)
        doc.c.drawString(x, doc.y - 43, party)
        doc.c.setFillColor(TEXT_GRAY)
        doc.c.setFont(REG, 7.5)
        doc.c.drawString(x, doc.y - 54, f'Name: {name}' if name else 'Name:')
        doc.c.drawString(x, doc.y - 65, 'Date:')

    doc.y -= 80
    doc.gap(16)

    # Footer note
    doc.c.setFillColor(TEXT_GRAY)
    doc.c.setFont(REG, 7)
    note = (f'This Statement of Work was prepared by Adchor on {sow_data.get("date", "")} '
            f'and is valid for 30 days. Version {sow_data.get("version", "v1.0")}.')
    doc.c.drawString(LM, doc.y, note)
    doc.y -= 10


# ── Public Entry Point ─────────────────────────────────────────────────────────

def build_sow_pdf(sow_data: dict, pricing_items: list, total: float, discount: float = 0) -> bytes:
    """
    Build the complete SOW PDF and return as bytes.
    Call from Streamlit: pdf_bytes = build_sow_pdf(...)
    """
    _setup_fonts()
    buf = io.BytesIO()
    doc = SOWDoc(buf)

    # Page 1: Cover
    _cover_page(doc, sow_data)

    # Page 2+: Scope
    doc.new_page()
    _scope_page(doc, sow_data)

    # Pricing
    doc.need(200)
    _pricing_page(doc, pricing_items, total, discount)

    # Assumptions / Terms
    doc.new_page()
    _assumptions_page(doc, sow_data)

    # Signature
    doc.need(180)
    _signature_page(doc, sow_data)

    doc.save()
    return buf.getvalue()
    def _page_num(self):
        self.c.setFillColor(TEXT_GRAY)
        self.c.setFont(REG, 7)
        self.c.drawRightString(RM, FOOTER_H - 4, f'Page {self.page}')

    def new_page(self):
        self._footer()
        self.c.showPage()
        self.page += 1
        self.y = CT
        self._header()
        self._page_num()

    def need(self, h):
        if self.y - h < CB:
            self.new_page()

    def gap(self, h=8):
        self.y -= h

    def _wrap(self, text, font, size, max_w):
        words = str(text).split()
        lines, line = [], ''
        for w in words:
            test = f'{line} {w}'.strip()
            if self.c.stringWidth(test, font, size) <= max_w:
                line = test
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines or ['']

    def h1(self, text):
        """Large title text."""
        self.need(30)
        self.c.setFillColor(TEXT_DARK)
        self.c.setFont(BOLD, 20)
        self.c.drawString(LM, self.y, text)
        self.y -= 20
        self.c.setFillColor(BLUE)
        self.c.setLineWidth(2.5)
        self.c.line(LM, self.y, LM + self.c.stringWidth(text, BOLD, 20) * 0.6, self.y)
        self.y -= 10

    def section_bar(self, title, color=DARK_BLUE):
        """Full-width dark section header bar."""
        self.need(50)
        self.gap(14)
        bh = 28
        self.c.setFillColor(color)
        self.c.rect(LM, self.y - bh, CW, bh, fill=1, stroke=0)
        # Green accent line below
        self.c.setFillColor(GREEN)
        self.c.rect(LM, self.y - bh - 2, CW, 2, fill=1, stroke=0)
        self.c.setFillColor(white)
        self.c.setFont(BOLD, 10)
        self.c.drawString(LM + 14, self.y - bh / 2 - 4, title.upper())
        self.y -= bh + 10

    def label(self, text):
        """Small blue uppercase label."""
        self.c.setFillColor(BLUE)
        self.c.setFont(SEMI, 7)
        self.c.drawString(LM, self.y, text.upper())
        self.y -= 10

    def body(self, text, indent=0, color=TEXT_DARK, size=9, font=None):
        """Wrapped body paragraph."""
        font = font or REG
        x = LM + indent
        lines = self._wrap(text, font, size, CW - indent)
        self.need(len(lines) * 12 + 4)
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        for ln in lines:
            self.c.drawString(x, self.y, ln)
            self.y -= 12
        self.y -= 3

    def bullet(self, text, indent=12):
        """Single bullet point."""
        x = LM + indent
        max_w = CW - indent - 10
        lines = self._wrap(text, REG, 8.5, max_w)
        self.need(len(lines) * 11 + 3)
        self.c.setFillColor(BLUE)
        self.c.circle(LM + indent - 6, self.y - 3, 2, fill=1, stroke=0)
        self.c.setFillColor(TEXT_DARK)
        self.c.setFont(REG, 8.5)
        for i, ln in enumerate(lines):
            self.c.drawString(x, self.y, ln)
            self.y -= 11
        self.y -= 2

    def sub_header(self, text):
        """Bold sub-section label."""
        self.need(20)
        self.gap(4)
        self.c.setFillColor(TEXT_DARK)
        self.c.setFont(BOLD, 9)
        self.c.drawString(LM, self.y, text)
        self.y -= 13

    def divider(self):
        self.c.setStrokeColor(DIVIDER)
        self.c.setLineWidth(0.3)
        self.c.line(LM, self.y, RM, self.y)
        self.y -= 8

    def two_col_field(self, label1, val1, label2, val2):
        """Two-column info pair."""
        hw = (CW - 12) / 2
        self.need(36)
        for i, (lbl, val) in enumerate([(label1, val1), (label2, val2)]):
            x = LM + i * (hw + 12)
            self.c.setFillColor(BLUE)
            self.c.setFont(SEMI, 6.5)
            self.c.drawString(x, self.y, lbl.upper())
            # Value box
            self.c.setFillColor(FIELD_BG)
            self.c.setStrokeColor(DIVIDER)
            self.c.setLineWidth(0.5)
            self.c.roundRect(x, self.y - 20, hw, 18, 3, fill=1, stroke=1)
            self.c.setFillColor(TEXT_DARK)
            self.c.setFont(REG, 8.5)
            # Truncate if too long
            val_str = str(val or '—')
            while self.c.stringWidth(val_str, REG, 8.5) > hw - 10 and len(val_str) > 3:
                val_str = val_str[:-4] + '...'
            self.c.drawString(x + 6, self.y - 14, val_str)
        self.y -= 28

    def info_box(self, text, bg=CORE_BG, border=BLUE):
        """Highlighted info box for key content like core message."""
        lines = self._wrap(text, REG, 9, CW - 20)
        bh = len(lines) * 13 + 16
        self.need(bh + 6)
        self.c.setFillColor(bg)
        self.c.setStrokeColor(border)
        self.c.setLineWidth(1.5)
        self.c.roundRect(LM, self.y - bh, CW, bh, 4, fill=1, stroke=1)
        # Left accent bar
        self.c.setFillColor(border)
        self.c.roundRect(LM, self.y - bh, 5, bh, 2, fill=1, stroke=0)
        self.c.setFillColor(TEXT_DARK)
        self.c.setFont(REG, 9)
        ty = self.y - 12
        for ln in lines:
            self.c.drawString(LM + 14, ty, ln)
            ty -= 13
        self.y -= bh + 8

    def scope_section_header(self, title):
        """Collapsible-style scope section header — dark navy with dropdown indicator."""
        self.need(50)
        self.gap(10)
        bh = 30
        self.c.setFillColor(DARK_BLUE)
        self.c.rect(LM, self.y - bh, CW, bh, fill=1, stroke=0)
        # Green left accent
        self.c.setFillColor(GREEN)
        self.c.rect(LM, self.y - bh, 5, bh, fill=1, stroke=0)
        # Title
        self.c.setFillColor(white)
        self.c.setFont(BOLD, 10)
        self.c.drawString(LM + 16, self.y - bh / 2 - 4, title)
        # "▼" indicator on right (like Qwilr)
        self.c.setFont(REG, 9)
        self.c.drawString(RM - 16, self.y - bh / 2 - 4, '▾')
        self.y -= bh

    def save(self):
        self._footer()
        self.c.save()


# ── Cover Page ────────────────────────────────────────────────────────────────

def _cover_page(doc, sow_data):
    c = doc.c

    # "STATEMENT OF WORK" title
    doc.gap(8)
    doc.h1('STATEMENT OF WORK')
    doc.gap(6)

    # Client × Adchor
    client = sow_data.get('client_name', 'Client')
    project = sow_data.get('project_name', 'Project')
    c.setFillColor(BLUE)
    c.setFont(BOLD, 14)
    c.drawString(LM, doc.y, project)
    doc.y -= 16
    c.setFillColor(TEXT_GRAY)
    c.setFont(REG, 10)
    c.drawString(LM, doc.y, f'{client}  ×  Adchor')
    doc.y -= 20

    doc.divider()
    doc.gap(4)

    # Key fields grid
    lead  = sow_data.get('account_lead', '')
    owner = sow_data.get('business_owner', '')
    date  = sow_data.get('date', datetime.today().strftime('%B %d, %Y'))
    ver   = sow_data.get('version', 'v1.0')
    ddl   = sow_data.get('final_deadline', '')
    bgt   = sow_data.get('budget_range', '')

    doc.two_col_field('Prepared For', client,    'Prepared By', 'Adchor')
    doc.two_col_field('Account Lead', lead,       'Business Owner', owner)
    doc.two_col_field('Date',         date,       'Version', ver)
    doc.two_col_field('Final Deadline', ddl,      'Investment Range', bgt)

    doc.gap(10)
    doc.divider()
    doc.gap(8)

    # Why Now
    why_now = sow_data.get('why_now', '')
    if why_now:
        doc.label('Why This, Why Now')
        doc.body(why_now, size=9)
        doc.gap(6)

    # Project Overview
    overview = sow_data.get('project_overview', '')
    if overview:
        doc.label('Project Overview')
        doc.body(overview, size=9)
        doc.gap(6)

    # Core Message
    core = sow_data.get('core_message', '')
    if core:
        doc.label('Core Message')
        doc.info_box(core)


# ── Scope of Services ─────────────────────────────────────────────────────────

def _scope_page(doc, sow_data):
    doc.section_bar('Scope of Services')

    sections = sow_data.get('scope_sections', [])
    for section in sections:
        title = section.get('title', 'Scope Section')
        description = section.get('description', '')
        services = section.get('services', [])
        deliverables = section.get('deliverables', [])

        doc.scope_section_header(title)
        doc.gap(6)

        if description:
            doc.body(description, size=9, color=TEXT_GRAY)
            doc.gap(4)

        if services:
            doc.sub_header('Services Include:')
            for s in services:
                if s.strip():
                    doc.bullet(s)

        if deliverables:
            doc.gap(4)
            doc.sub_header('Primary Deliverables:')
            for d in deliverables:
                if d.strip():
                    doc.bullet(d)

        doc.gap(10)
        doc.divider()


# ── Investment / Pricing ──────────────────────────────────────────────────────

def _pricing_page(doc, pricing_items, total, discount):
    doc.section_bar('Investment', color=DARK_BLUE)

    if not pricing_items:
        doc.body('Investment details to be confirmed.', color=TEXT_GRAY)
        return

    # Table setup
    col_w = [220, 120, 60, 80, 80]
    col_x = [LM, LM+220, LM+340, LM+400, LM+480]
    headers = ['Service', 'Description', 'Qty', 'Unit Price', 'Total']

    doc.need(len(pricing_items) * 24 + 44)

    # Header row
    doc.c.setFillColor(DARK_BLUE)
    doc.c.rect(LM, doc.y - 22, CW, 22, fill=1, stroke=0)
    doc.c.setFillColor(white)
    doc.c.setFont(SEMI, 8.5)
    for lbl, cx in zip(headers, col_x):
        doc.c.drawString(cx + 5, doc.y - 15, lbl)
    doc.y -= 22

    # Data rows
    for r, item in enumerate(pricing_items):
        bg = FIELD_BG if r % 2 == 0 else white
        row_h = 22
        doc.c.setFillColor(bg)
        doc.c.setStrokeColor(DIVIDER)
        doc.c.setLineWidth(0.3)
        doc.c.rect(LM, doc.y - row_h, CW, row_h, fill=1, stroke=1)

        doc.c.setFillColor(TEXT_DARK)
        doc.c.setFont(REG, 8.5)

        vals = [
            item.get('name', ''),
            item.get('description', ''),
            str(item.get('qty', 1)),
            f"${item.get('unit_price', 0):,.0f}",
            f"${item.get('total', 0):,.0f}",
        ]
        for val, cx, cw in zip(vals, col_x, col_w):
            # Truncate if needed
            v = str(val)
            while doc.c.stringWidth(v, REG, 8.5) > cw - 8 and len(v) > 3:
                v = v[:-4] + '...'
            doc.c.drawString(cx + 5, doc.y - 15, v)

        doc.y -= row_h

    # Subtotal / discount / total footer
    doc.gap(4)
    subtotal = sum(i.get('total', 0) for i in pricing_items)

    if discount and discount > 0:
        # Subtotal row
        doc.c.setFillColor(FIELD_BG)
        doc.c.rect(LM, doc.y - 20, CW, 20, fill=1, stroke=0)
        doc.c.setFillColor(TEXT_GRAY)
        doc.c.setFont(REG, 8.5)
        doc.c.drawString(LM + 10, doc.y - 14, 'Subtotal')
        doc.c.drawRightString(RM - 8, doc.y - 14, f'${subtotal:,.0f}')
        doc.y -= 20

        # Discount row
        doc.c.setFillColor(LIGHT_GREEN)
        doc.c.rect(LM, doc.y - 20, CW, 20, fill=1, stroke=0)
        doc.c.setFillColor(MID_GREEN)
        doc.c.setFont(REG, 8.5)
        doc.c.drawString(LM + 10, doc.y - 14, 'Discount')
        doc.c.drawRightString(RM - 8, doc.y - 14, f'-${discount:,.0f}')
        doc.y -= 20

    # Total row
    doc.c.setFillColor(DARK_BLUE)
    doc.c.rect(LM, doc.y - 28, CW, 28, fill=1, stroke=0)
    doc.c.setFillColor(GREEN)
    doc.c.rect(LM, doc.y - 28, 5, 28, fill=1, stroke=0)
    doc.c.setFillColor(white)
    doc.c.setFont(BOLD, 11)
    doc.c.drawString(LM + 14, doc.y - 18, 'Total Investment')
    doc.c.drawRightString(RM - 8, doc.y - 18, f'${total:,.0f}')
    doc.y -= 36


# ── Assumptions & Out of Scope ────────────────────────────────────────────────

def _assumptions_page(doc, sow_data):
    assumptions = sow_data.get('assumptions', [])
    out_of_scope = sow_data.get('out_of_scope', [])
    timeline = sow_data.get('timeline_notes', '')
    review_rounds = sow_data.get('review_rounds', '2')

    if assumptions or out_of_scope or timeline:
        doc.section_bar('Project Terms & Assumptions', color=BLUE)

    if timeline:
        doc.sub_header('Timeline & Milestones')
        doc.body(timeline, size=9)
        doc.gap(6)

    if review_rounds:
        doc.sub_header('Creative Review Rounds')
        doc.body(f'This SOW includes {review_rounds} round(s) of consolidated client feedback. '
                 'Additional rounds are available as a change order.', size=9)
        doc.gap(6)

    if assumptions:
        doc.sub_header('Assumptions')
        for a in assumptions:
            if a.strip():
                doc.bullet(a)
        doc.gap(8)

    if out_of_scope:
        doc.sub_header('Out of Scope')
        for o in out_of_scope:
            if o.strip():
                doc.bullet(o)
        doc.gap(8)


# ── Signature Block ────────────────────────────────────────────────────────────

def _signature_page(doc, sow_data):
    doc.section_bar('Authorization & Signature', color=DARK_BLUE)
    doc.gap(6)

    client = sow_data.get('client_name', 'Client')
    owner  = sow_data.get('business_owner', '')
    lead   = sow_data.get('account_lead', '')

    doc.body(
        f'By signing below, {client} authorizes Adchor to proceed with the scope of work '
        f'outlined in this document under the terms described herein.',
        size=9, color=TEXT_GRAY
    )
    doc.gap(16)

    # Two signature boxes
    hw = (CW - 20) / 2
    for i, (party, name) in enumerate([
        (f'{client} — Authorized Signature', owner),
        ('Adchor — Account Lead', lead),
    ]):
        x = LM + i * (hw + 20)
        # Line
        doc.c.setStrokeColor(DARK_BLUE)
        doc.c.setLineWidth(1)
        doc.c.line(x, doc.y - 30, x + hw, doc.y - 30)
        # Labels
        doc.c.setFillColor(TEXT_DARK)
        doc.c.setFont(BOLD, 8)
        doc.c.drawString(x, doc.y - 43, party)
        doc.c.setFillColor(TEXT_GRAY)
        doc.c.setFont(REG, 7.5)
        doc.c.drawString(x, doc.y - 54, f'Name: {name}' if name else 'Name:')
        doc.c.drawString(x, doc.y - 65, 'Date:')

    doc.y -= 80
    doc.gap(16)

    # Footer note
    doc.c.setFillColor(TEXT_GRAY)
    doc.c.setFont(REG, 7)
    note = (f'This Statement of Work was prepared by Adchor on {sow_data.get("date", "")} '
            f'and is valid for 30 days. Version {sow_data.get("version", "v1.0")}.')
    doc.c.drawString(LM, doc.y, note)
    doc.y -= 10


# ── Public Entry Point ─────────────────────────────────────────────────────────

def build_sow_pdf(sow_data: dict, pricing_items: list, total: float, discount: float = 0) -> bytes:
    """
    Build the complete SOW PDF and return as bytes.
    Call from Streamlit: pdf_bytes = build_sow_pdf(...)
    """
    _setup_fonts()
    buf = io.BytesIO()
    doc = SOWDoc(buf)

    # Page 1: Cover
    _cover_page(doc, sow_data)

    # Page 2+: Scope
    doc.new_page()
    _scope_page(doc, sow_data)

    # Pricing
    doc.need(200)
    _pricing_page(doc, pricing_items, total, discount)

    # Assumptions / Terms
    doc.new_page()
    _assumptions_page(doc, sow_data)

    # Signature
    doc.need(180)
    _signature_page(doc, sow_data)

    doc.save()
    return buf.getvalue()
