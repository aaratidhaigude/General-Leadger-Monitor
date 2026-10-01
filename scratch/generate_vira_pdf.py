import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def build_pdf():
    pdf_path = r"C:\Users\Varad\Downloads\VIRA_Vendor_AI_Project_Plan.pdf"
    artifact_path = r"C:\Users\Varad\.gemini\antigravity-cli\brain\519454df-0cdb-42fc-94bd-b5ee6e8747f1\VIRA_Vendor_AI_Project_Plan.pdf"

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=0.4 * inch,
        rightMargin=0.4 * inch,
        topMargin=0.4 * inch,
        bottomMargin=0.4 * inch
    )

    styles = getSampleStyleSheet()

    # Color Palette (PODZO Palette)
    NAVY = colors.HexColor("#1A5276")
    BLUE_HDR = colors.HexColor("#1F3864")
    ORANGE_SEC = colors.HexColor("#E67E22")
    DARK_TEXT = colors.HexColor("#2C3E50")
    LIGHT_BG = colors.HexColor("#F8F9F9")
    BORDER_CLR = colors.HexColor("#BDC3C7")
    BLUE_ACCENT = colors.HexColor("#2980B9")

    # Paragraph Styles
    style_title = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=20,
        textColor=NAVY
    )
    style_subtitle = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=BLUE_ACCENT
    )
    style_meta = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#7F8C8D"),
        alignment=2 # Right
    )
    style_sec_bar = ParagraphStyle(
        "SecBar",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.white
    )
    style_body = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.5,
        textColor=DARK_TEXT
    )
    style_body_bold = ParagraphStyle(
        "BodyTextBoldCustom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=10.5,
        textColor=DARK_TEXT
    )
    style_card_title = ParagraphStyle(
        "CardTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=10,
        textColor=NAVY
    )
    style_wf_step = ParagraphStyle(
        "WFStep",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.0,
        leading=8.5,
        textColor=colors.white,
        alignment=1 # Center
    )
    style_wf_desc = ParagraphStyle(
        "WFDesc",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.8,
        leading=8.0,
        textColor=DARK_TEXT,
        alignment=1 # Center
    )
    style_tbl_cell = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=DARK_TEXT
    )
    style_tbl_hdr = ParagraphStyle(
        "TblHdr",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.0,
        leading=10,
        textColor=colors.white
    )

    story = []

    def make_sec_bar(title_text):
        p = Paragraph(f"  {title_text.upper()}", style_sec_bar)
        t = Table([[p]], colWidths=[7.7 * inch])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), ORANGE_SEC),
            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        return t

    # -------------------------------------------------------------------------
    # PAGE 1
    # -------------------------------------------------------------------------

    # Header Row
    t_hdr_meta = Table([[
        Paragraph("<b>VIRA — Project Plan</b>", style_title),
        Paragraph("PROJECT PLAN<br/>Version 2.0 • October 2026", style_meta)
    ]], colWidths=[5.2 * inch, 2.5 * inch])
    t_hdr_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_hdr_meta)
    story.append(Paragraph("SAP S/4HANA-Connected AI Vendor Intelligence & AP Risk Platform", style_subtitle))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=4, spaceBefore=0))

    # Executive Summary Box
    p_ex = Paragraph(
        "<b>Executive Summary:</b> VIRA provides a centralized operational AI interface for managing SAP-connected contracts, purchase orders, vendor statement reconciliations, and automated credit/debit memo posting through to SAP MIRO / FB60 / FB65 payment clearing.",
        style_body
    )
    t_ex = Table([[p_ex]], colWidths=[7.7 * inch])
    t_ex.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.8, BLUE_ACCENT),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_ex)
    story.append(Spacer(1, 4))

    # SECTION 1
    story.append(make_sec_bar("SECTION 1 — USE CASE"))
    story.append(Spacer(1, 2))
    p_s1 = Paragraph(
        "Procurement contract enforcement and vendor statement reconciliation in SAP run largely on manual effort. Unstructured PDF contract clauses (rate cards, volume rebates, price adjustment terms) and monthly vendor statements (PDF/XLS) are audited manually by AP teams. <b>Need:</b> field execution tied to S/4HANA POs and settlement, with SAP remaining the financial system of record.",
        style_body
    )
    story.append(p_s1)
    story.append(Spacer(1, 4))

    # SECTION 2
    story.append(make_sec_bar("SECTION 2 — REFERENCE USE CASE"))
    story.append(Spacer(1, 2))
    p_s2 = Paragraph(
        "Standard SAP procure-to-pay 3-way match (PO → Goods Receipt → Supplier Invoice MIRO) checks static PO line items. However, MIRO cannot evaluate unstructured PDF contract clauses, cumulative year-to-date volume rebate thresholds (> ₹10 Crore), or unapplied credit notes on external vendor statements. VIRA bridges this gap by automatically injecting RAG clause verification and 4-way statement reconciliation into the SAP posting flow.",
        style_body
    )
    story.append(p_s2)
    story.append(Spacer(1, 4))

    # SECTION 3
    story.append(make_sec_bar("SECTION 3 — SOLUTION: VIRA AT A GLANCE"))
    story.append(Spacer(1, 2))
    p_s3 = Paragraph(
        "VIRA is an enterprise operational execution and AI verification platform designed to bridge SAP S/4HANA with contract compliance and vendor accounts payable fulfillment. By retrieving active contracts (ME33K), purchase orders (ME23N), and open items (BSEG/BKPF) directly from SAP S/4HANA, VIRA governs AI contract clause auditing, RAG vector search, volume rebate calculation, and multi-format statement matching—delivering end-to-end auditability while preserving SAP as the single authoritative financial core.",
        style_body
    )
    story.append(p_s3)
    story.append(Spacer(1, 3))

    p_b1 = Paragraph("<b>✓ Direct SAP S/4HANA Alignment</b><br/>Live ingestion of active contracts (ME33K) & POs (ME23N) via real-time OData / REST services.", style_body)
    p_b2 = Paragraph("<b>✓ RAG Vector Search Governance</b><br/>Embeddings engine (all-MiniLM-L6-v2 / Ollama qwen2.5) indexes contract clauses for instant rate card & rebate auditing.", style_body)
    p_b3 = Paragraph("<b>✓ Automated Settlement & FB65</b><br/>RAG verification feeds verified rebate credit memos and debit notes directly into SAP MIRO / FB65 invoice parking.", style_body)
    
    t_pillars = Table([[p_b1, p_b2, p_b3]], colWidths=[2.5 * inch, 2.6 * inch, 2.6 * inch])
    t_pillars.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_pillars)
    story.append(Spacer(1, 4))

    # SECTION 4
    story.append(make_sec_bar("SECTION 4 — KEY CAPABILITIES"))
    story.append(Spacer(1, 2))

    cap1 = Paragraph("<b>◆ SAP S/4HANA Synchronization</b><br/>Direct ingestion of active outline agreements (ME33K) and POs (ME23N) with rate cards, target values, and validity windows.", style_body)
    cap2 = Paragraph("<b>◆ RAG Vector Search & Embeddings Engine</b><br/>Ingests PDF contract agreements, generates 384-dim embeddings, and performs Cosine Similarity search for clause retrieval.", style_body)
    cap3 = Paragraph("<b>◆ Contract Rebate Leakage Audit</b><br/>Tracks YTD volume in SAP (BSEG/BKPF). Once ₹10Cr threshold is breached, calculates 5% rebate due and drafts SAP Credit Memos (FB65).", style_body)
    cap4 = Paragraph("<b>◆ Vendor Statement Reconciliation</b><br/>Parses monthly statements in any layout (PDF, XLS, CSV) using OCR and Intelligent Document Processing (IDP).", style_body)
    cap5 = Paragraph("<b>◆ 4-Way Fuzzy Matching Desk</b><br/>Performs intelligent matching across Vendor Statement vs SAP Open Items (BSEG) vs Bank Clearings (FEBEP) vs Credit Memos.", style_body)
    cap6 = Paragraph("<b>◆ Invoicing & SAP MIRO / FB65 Posting</b><br/>Consolidation of audit results into draft credit/debit memos, staging audit-ready data for SAP MIRO supplier invoice parking and settlement.", style_body)

    t_caps = Table([
        [cap1, cap2],
        [cap3, cap4],
        [cap5, cap6]
    ], colWidths=[3.85 * inch, 3.85 * inch])
    t_caps.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_caps)
    story.append(Spacer(1, 4))

    # SECTION 5
    story.append(make_sec_bar("SECTION 5 — ROLE-BASED OPERATIONS"))
    story.append(Spacer(1, 2))

    r1 = Paragraph("<b>[CA] Company Admin / Controller:</b> Manages rate cards, rebate targets, variance approval queues, and final SAP MIRO/FB65 invoice approvals.", style_body)
    r2 = Paragraph("<b>[AP] Accounts Payable Auditor:</b> Reviews RAG contract overbilling alerts, verifies unapplied vendor credit notes, and releases payment blocks.", style_body)
    r3 = Paragraph("<b>[VM] Vendor Management Lead:</b> Monitors supplier statement reconciliation status, tracks rebate claims, and manages vendor contracts.", style_body)
    r4 = Paragraph("<b>[AI] Autonomous RAG Engine:</b> Executes vector search against contract agreements, computes cosine similarity, and flags price leakage.", style_body)
    r5 = Paragraph("<b>[SA] SAP FICO Specialist:</b> Governs OData/REST API sync, configures BSEG-ZLSPR payment block rules, and maintains SAP system-of-record integrity.", style_body)

    t_roles = Table([
        [r1, r2],
        [r3, r4],
        [r5, Paragraph("", style_body)]
    ], colWidths=[3.85 * inch, 3.85 * inch])
    t_roles.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_roles)
    story.append(Spacer(1, 4))

    # SECTION 6
    story.append(make_sec_bar("SECTION 6 — END-TO-END OPERATIONAL WORKFLOW"))
    story.append(Spacer(1, 2))

    wf_hdrs = [
        Paragraph("STEP 1", style_wf_step),
        Paragraph("STEP 2", style_wf_step),
        Paragraph("STEP 3", style_wf_step),
        Paragraph("STEP 4", style_wf_step),
        Paragraph("STEP 5", style_wf_step),
        Paragraph("STEP 6", style_wf_step),
        Paragraph("STEP 7", style_wf_step)
    ]
    wf_descs = [
        Paragraph("<b>SAP Sync</b><br/>Contracts & POs", style_wf_desc),
        Paragraph("<b>Doc Ingestion</b><br/>PDF Contracts/Stmts", style_wf_desc),
        Paragraph("<b>RAG Vector Store</b><br/>Embedding Index", style_wf_desc),
        Paragraph("<b>Rebate Audit</b><br/>Overbill & Volume", style_wf_desc),
        Paragraph("<b>Statement Recon</b><br/>4-Way Match", style_wf_desc),
        Paragraph("<b>Exception Desk</b><br/>Auditor Sign-off", style_wf_desc),
        Paragraph("<b>SAP Settlement</b><br/>MIRO / FB65 Clear", style_wf_desc)
    ]

    col_w = [1.1 * inch] * 7
    t_wf = Table([wf_hdrs, wf_descs], colWidths=col_w)
    t_wf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_HDR),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(t_wf)
    story.append(Spacer(1, 2))
    story.append(Paragraph("<font size='6.8' color='#555555'><b>Operational Data Continuity:</b> SAP S/4HANA Contracts (ME33K) & POs (ME23N) • RAG Vector Embedding Index • Volume Rebate Audit • Vendor Statement 4-Way Match • AP Exception Desk • SAP MIRO/FB65 Posting & Settlement.</font>", style_body))

    # -------------------------------------------------------------------------
    # PAGE 2
    # -------------------------------------------------------------------------
    story.append(PageBreak())

    # Header Row Page 2
    t_hdr2 = Table([[
        Paragraph("<b>VIRA — Integration & Architecture</b>", style_title),
        Paragraph("ENTERPRISE BLUEPRINT<br/>Page 2 of 2", style_meta)
    ]], colWidths=[5.2 * inch, 2.5 * inch])
    t_hdr2.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_hdr2)
    story.append(Paragraph("SAP S/4HANA Integration, Architectural Blueprint & Enterprise Value", style_subtitle))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=4, spaceBefore=0))

    # SECTION 7
    story.append(make_sec_bar("SECTION 7 — SAP S/4HANA INTEGRATION"))
    story.append(Spacer(1, 2))

    t7_hdr = [Paragraph("Integration Dimension", style_tbl_hdr), Paragraph("Data Scope & Functional Mapping", style_tbl_hdr), Paragraph("Data Governance & Storage Boundary", style_tbl_hdr)]
    t7_r1 = [Paragraph("<b>Inbound from SAP S/4HANA</b><br/>OData / REST APIs", style_tbl_cell), Paragraph("Outline Contracts (ME33K), POs (ME23N), Line Items, Target Values, Agreed Unit Rates, Cost Centers, Vendor Master (LFA1).", style_tbl_cell), Paragraph("Retrieved from SAP. Master records remain governed exclusively in SAP S/4HANA; cached for operational display.", style_tbl_cell)]
    t7_r2 = [Paragraph("<b>Operational Processing</b><br/>VIRA Core Layer", style_tbl_cell), Paragraph("PDF contract ingestion, RAG vector embeddings (all-MiniLM-L6-v2 / Ollama), YTD volume rebate calculation, 4-way statement fuzzy matching.", style_tbl_cell), Paragraph("Stored in VIRA. RAG vector chunks, audit logs, and exception telemetry are persisted in VIRA's transactional database.", style_tbl_cell)]
    t7_r3 = [Paragraph("<b>Outbound to SAP S/4HANA</b><br/>ABAP RFC / MIRO API", style_tbl_cell), Paragraph("Verified contract rebates, draft Credit Memos (FB65), SAP Payment Blocks (BSEG-ZLSPR = 'A'), MIRO invoice parking.", style_tbl_cell), Paragraph("Posted to SAP. Final financial and compliance artifacts are transmitted back to SAP for settlement.", style_tbl_cell)]

    t7 = Table([t7_hdr, t7_r1, t7_r2, t7_r3], colWidths=[2.0 * inch, 3.2 * inch, 2.5 * inch])
    t7.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_HDR),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BG),
        ('BACKGROUND', (0, 2), (-1, 2), colors.white),
        ('BACKGROUND', (0, 3), (-1, 3), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t7)
    story.append(Spacer(1, 4))

    # SECTION 8
    story.append(make_sec_bar("SECTION 8 — HIGH-LEVEL SOLUTION ARCHITECTURE"))
    story.append(Spacer(1, 2))

    a1 = Paragraph("<b>1. Enterprise ERP Layer (SAP S/4HANA System of Record)</b><br/>SAP S/4HANA: Outline Agreements (ME33K) • Purchase Orders (ME23N) • Open Items (BSEG/BKPF) • Supplier Invoices (MIRO/FB60/FB65)<br/><i>&lt;&gt; Secure SAP Integration Layer (REST • OData • RFC Proxy • Destination Service • Sync Logs) &lt;&gt;</i>", style_body)
    a2 = Paragraph("<b>2. VIRA Operational Core Platform (Execution & AI Verification Layer)</b><br/>CAP • Python FastAPI • RAG Vector Engine (all-MiniLM-L6-v2 / Ollama qwen2.5) • SQLite / SAP HANA Cloud<br/>Contract Rebate Auditor • Statement Recon Engine • Exception Review Queue • Audit Event Logger<br/><i>&lt;&gt; Role-Governed Secure Web Endpoints (XSUAA / JWT Authentication • RBAC) &lt;&gt;</i>", style_body)
    a3 = Paragraph("<b>3. Role-Tailored Operational Consoles (SAP Fiori-Inspired UX)</b><br/>React 19 / Vite • Desktop • Mobile<br/>CA: Admin Control Tower & Approvals • AP: Accounts Payable Auditor Desk • VM: Vendor Management Console", style_body)

    t_arch = Table([[a1], [a2], [a3]], colWidths=[7.7 * inch])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 4))

    # SECTION 9 & 10
    story.append(make_sec_bar("SECTION 9 — TECHNOLOGY OVERVIEW"))
    story.append(Spacer(1, 2))

    t9_hdr = [Paragraph("FRONTEND", style_tbl_hdr), Paragraph("BACKEND SERVICES", style_tbl_hdr), Paragraph("RAG & AI ENGINE", style_tbl_hdr), Paragraph("DATA STORE", style_tbl_hdr), Paragraph("PLATFORM", style_tbl_hdr)]
    t9_r1 = [
        Paragraph("React 19 • Vite<br/>TypeScript, Fiori UX", style_tbl_cell),
        Paragraph("Python FastAPI • CAP<br/>RESTful / OData API", style_tbl_cell),
        Paragraph("sentence-transformers<br/>all-MiniLM-L6-v2 / Ollama", style_tbl_cell),
        Paragraph("SQLite (WAL Mode)<br/>SAP HANA Cloud via CAP", style_tbl_cell),
        Paragraph("SAP BTP Cloud Foundry<br/>MTA, XSUAA, Destination", style_tbl_cell)
    ]
    t9 = Table([t9_hdr, t9_r1], colWidths=[1.54 * inch] * 5)
    t9.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BLUE_HDR),
        ('BACKGROUND', (0, 1), (-1, 1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t9)
    story.append(Spacer(1, 4))

    # SECTION 10
    story.append(make_sec_bar("SECTION 10 — DEPLOYMENT, SAP APIs & POLICY (SAP BTP CLOUD FOUNDRY)"))
    story.append(Spacer(1, 2))

    d1 = Paragraph("<b>Deployment:</b> MTA (mta.yaml) to SAP BTP Cloud Foundry: CAP Node.js service; React UI via HTML5 Repository + Approuter. Persistence: SQLite now; SAP HANA Cloud (HDI container) via CAP binding.", style_body)
    d2 = Paragraph("<b>Auth & Access:</b> XSUAA (IAS as identity provider); JWT on every endpoint; role collections mapped to CA / AP / VM / SA.", style_body)
    d3 = Paragraph("<b>Connectivity:</b> Destination and Connectivity services; Cloud Connector if S/4HANA is on-premise; least-privilege technical user.", style_body)
    d4 = Paragraph("<b>SAP APIs:</b> Inbound OData: Purchase Order (ME23N), Purchase Contract (ME33K), Open Items (BSEG). Outbound: Supplier Invoice (MIRO/FB65), Payment Block (BSEG-ZLSPR).", style_body)
    d5 = Paragraph("<b>Data Policy:</b> SAP owns master and financial data; VIRA caches for display and RAG vector search only. Encryption at rest and TLS in transit.", style_body)
    d6 = Paragraph("<b>Audit & Governance:</b> Every dispatch, RAG clause retrieval, volume rebate calculation, and statement match timestamped with user credentials and audit logs.", style_body)

    t10 = Table([[d1, d2], [d3, d4], [d5, d6]], colWidths=[3.85 * inch, 3.85 * inch])
    t10.setStyle(TableStyle([
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t10)
    story.append(Spacer(1, 4))

    # SECTION 11
    story.append(make_sec_bar("SECTION 11 — BUSINESS VALUE"))
    story.append(Spacer(1, 2))

    v1 = Paragraph("<b>Eliminated Contract Overbilling</b><br/>RAG vector clause search continuously audits invoice line items against PDF contract rate cards and automatically calculates retroactive 5% volume rebates once the ₹10 Crore threshold is passed.", style_body)
    v2 = Paragraph("<b>Automated Statement Reconciliation</b><br/>Multi-format OCR ingestion and 4-way fuzzy matching replace manual line-by-line Excel checking, discovering unapplied vendor credit notes and recovering overpayments.", style_body)
    v3 = Paragraph("<b>Compressed Financial Close Cycles</b><br/>Real-time RAG clause verification and statement matching replace multi-week manual contract audits, collapsing period-end clearing to hours.", style_body)
    v4 = Paragraph("<b>Complete Audit Governance</b><br/>Every vector clause match, volume calculation, and MIRO/FB65 posting is immutably timestamped with user credentials and audit logs.", style_body)

    t11 = Table([[v1, v2], [v3, v4]], colWidths=[3.85 * inch, 3.85 * inch])
    t11.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t11)
    story.append(Spacer(1, 3))

    p_sol_pos = Paragraph("<b>SOLUTION APPROACH & POSITIONING:</b> VIRA provides a purpose-built operational AI execution and RAG verification layer around SAP-connected contract and accounts payable workflows. It enables business users, finance auditors, and procurement leads to collaborate through a modern, role-based interface while preserving strict alignment, security, and traceability with SAP S/4HANA business data.", style_body)
    story.append(p_sol_pos)

    # Build PDF Document
    doc.build(story)
    
    # Save a copy to artifact directory as well
    import shutil
    shutil.copy(pdf_path, artifact_path)

    print(f"2-Page PDF successfully built:\n  Downloads: {pdf_path}\n  Artifact: {artifact_path}")

if __name__ == "__main__":
    build_pdf()
