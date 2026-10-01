import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_styled_heading(doc, text, level):
    h = doc.add_heading(text, level=level)
    run = h.runs[0]
    if level == 1:
        run.font.color.rgb = RGBColor(31, 56, 100) # Deep Blue (#1F3864)
        run.font.size = Pt(15)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
    elif level == 2:
        run.font.color.rgb = RGBColor(41, 128, 185) # Ocean Blue (#2980B9)
        run.font.size = Pt(13)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(3)
    elif level == 3:
        run.font.color.rgb = RGBColor(52, 73, 94) # Dark Grey (#34495E)
        run.font.size = Pt(11)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(2)
    return h

def build_vira_project_plan():
    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Title Banner (PODZO Style)
    p_title = doc.add_paragraph()
    r_brand = p_title.add_run("VIRA — Project Plan\n")
    r_brand.font.size = Pt(22)
    r_brand.font.bold = True
    r_brand.font.color.rgb = RGBColor(31, 56, 100)

    r_sub = p_title.add_run("SAP S/4HANA-Connected AI Vendor Intelligence & AP Risk Platform")
    r_sub.font.size = Pt(13)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(41, 128, 185)

    p_meta = doc.add_paragraph()
    p_meta.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_m = p_meta.add_run("PROJECT PLAN | Version 2.0 • October 2026")
    r_m.font.size = Pt(9.5)
    r_m.font.bold = True
    r_m.font.color.rgb = RGBColor(127, 140, 141)

    # Executive Summary Box
    p_exec = doc.add_paragraph()
    p_exec.paragraph_format.space_before = Pt(6)
    p_exec.paragraph_format.space_after = Pt(8)
    r_ex_title = p_exec.add_run("Executive Summary: ")
    r_ex_title.bold = True
    r_ex_title.font.color.rgb = RGBColor(31, 56, 100)
    p_exec.add_run("VIRA provides a centralized operational AI interface for managing SAP-connected contracts, purchase orders, vendor statement reconciliations, and automated credit/debit memo posting through to SAP MIRO / FB60 / FB65 payment clearing.")

    # SECTION 1 — USE CASE
    add_styled_heading(doc, "SECTION 1 — USE CASE", level=1)
    p_uc = doc.add_paragraph()
    p_uc.add_run("Procurement contract enforcement and vendor statement reconciliation in SAP run largely on manual effort. Unstructured PDF contract clauses (rate cards, volume rebates, price adjustment terms) and monthly vendor statements (PDF/XLS) are audited manually by AP teams. ")
    r_bold_need = p_uc.add_run("Need: ")
    r_bold_need.bold = True
    p_uc.add_run("Automated contract RAG clause extraction, dynamic volume rebate leakage detection, and 4-way fuzzy vendor statement reconciliation tied to S/4HANA POs and settlement, with SAP remaining the authoritative financial system of record.")

    # SECTION 2 — REFERENCE USE CASE
    add_styled_heading(doc, "SECTION 2 — REFERENCE USE CASE", level=1)
    p_ref = doc.add_paragraph()
    p_ref.add_run("Standard SAP procure-to-pay 3-way match (PO → Goods Receipt / Service Entry Sheet → Supplier Invoice MIRO) checks static PO line items. ")
    p_ref.add_run("However, MIRO cannot evaluate unstructured PDF contract clauses, cumulative year-to-date volume rebate thresholds (> ₹10 Crore), or unapplied credit notes on external vendor statements. VIRA bridges this gap by automatically injecting RAG clause verification and 4-way statement reconciliation into the SAP posting flow.")

    # SECTION 3 — SOLUTION: VIRA AT A GLANCE
    add_styled_heading(doc, "SECTION 3 — SOLUTION: VIRA AT A GLANCE", level=1)
    p_sol = doc.add_paragraph()
    p_sol.add_run("VIRA is an enterprise operational execution and AI verification platform designed to bridge SAP S/4HANA with contract compliance and vendor accounts payable fulfillment. ")
    p_sol.add_run("By retrieving active contracts (ME33K), purchase orders (ME23N), and open items (BSEG/BKPF) directly from SAP S/4HANA, VIRA governs AI contract clause auditing, RAG vector search, volume rebate calculation, and multi-format statement matching—delivering end-to-end auditability while preserving SAP as the single authoritative financial core.")

    # 3 Summary Bullet Cards
    p_bullets = doc.add_paragraph()
    p_bullets.add_run("✓ Direct SAP S/4HANA Alignment\n").bold = True
    p_bullets.add_run("Live ingestion of active contracts (ME33K) & POs (ME23N) via real-time OData / REST services.\n\n")
    p_bullets.add_run("✓ RAG Vector Search & Clause Governance\n").bold = True
    p_bullets.add_run("Embeddings engine (all-MiniLM-L6-v2 / Ollama qwen2.5) indexes contract clauses for instant rate card & rebate auditing.\n\n")
    p_bullets.add_run("✓ Automated SAP Settlement & FB65\n").bold = True
    p_bullets.add_run("RAG verification feeds verified rebate credit memos and debit notes directly into SAP MIRO / FB65 invoice parking.")

    # SECTION 4 — KEY CAPABILITIES
    add_styled_heading(doc, "SECTION 4 — KEY CAPABILITIES", level=1)
    
    caps = [
        ("◆ SAP S/4HANA Synchronization", "Direct ingestion of active outline agreements (ME33K) and purchase orders (ME23N) with materials, rate cards, target values, and validity windows."),
        ("◆ RAG Vector Search & Embeddings Engine", "Ingests PDF/Text contract agreements, generates 384-dimensional vector embeddings, and performs Cosine Similarity search for clause retrieval."),
        ("◆ Cumulative Volume Rebate Auditor", "Tracks YTD purchase volume in SAP (BSEG/BKPF). Once the ₹10 Crore threshold is breached, calculates the 5% rebate due and drafts SAP Credit Memos (FB65)."),
        ("◆ Multi-Format Vendor Statement Ingestion", "Parses monthly vendor statements in any layout (PDF, XLS, CSV) using OCR and Intelligent Document Processing (IDP)."),
        ("◆ 4-Way Fuzzy Reconciliation Desk", "Performs intelligent matching across Vendor Statement vs SAP Open Items (BSEG) vs Bank Clearings (FEBEP) vs Credit Memos to spot unapplied credits."),
        ("◆ Invoicing & SAP MIRO / FB65 Posting", "Consolidation of verified audit results into draft credit/debit memos, staging audit-ready data for SAP MIRO supplier invoice parking and settlement.")
    ]

    for title, desc in caps:
        p_cap = doc.add_paragraph()
        r_c = p_cap.add_run(title + "\n")
        r_c.bold = True
        r_c.font.color.rgb = RGBColor(41, 128, 185)
        p_cap.add_run(desc)
        p_cap.paragraph_format.space_after = Pt(4)

    # SECTION 5 — ROLE-BASED OPERATIONS
    add_styled_heading(doc, "SECTION 5 — ROLE-BASED OPERATIONS", level=1)
    
    roles = [
        ("[CA] Company Admin / Finance Controller", "Manages contract rate cards, volume rebate targets, variance approval queues, and final SAP MIRO/FB65 invoice approvals."),
        ("[AP] Accounts Payable Auditor", "Reviews RAG contract overbilling alerts, verifies unapplied vendor credit notes, and releases payment blocks."),
        ("[VM] Vendor Management Lead", "Monitors supplier statement reconciliation status, tracks rebate claims, and manages vendor contract rate card updates."),
        ("[AI] Autonomous RAG Engine", "Executes vector search against contract agreements, computes cosine similarity, and flags price leakage or missing credit notes."),
        ("[SA] SAP FICO Specialist", "Governs OData/REST API sync, configures BSEG-ZLSPR payment block rules, and maintains SAP system-of-record integrity.")
    ]

    for r_title, r_desc in roles:
        p_role = doc.add_paragraph()
        r_r = p_role.add_run(r_title + ": ")
        r_r.bold = True
        r_r.font.color.rgb = RGBColor(31, 56, 100)
        p_role.add_run(r_desc)
        p_role.paragraph_format.space_after = Pt(3)

    # SECTION 6 — END-TO-END OPERATIONAL WORKFLOW
    add_styled_heading(doc, "SECTION 6 — END-TO-END OPERATIONAL WORKFLOW", level=1)

    wf_table_data = [
        ("STEP 1", "STEP 2", "STEP 3", "STEP 4", "STEP 5", "STEP 6", "STEP 7"),
        ("SAP Sync\nContracts & POs", "Doc Ingestion\nPDF Contracts/Stmts", "RAG Vector Store\nEmbedding Index", "Use Case 2 Audit\nRebate Leakage", "Use Case 3 Audit\nStatement Recon", "Exception Desk\nAuditor Sign-off", "SAP MIRO/FB65\nClear & Post")
    ]

    t_wf = doc.add_table(rows=2, cols=7)
    t_wf.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_wf.autofit = False

    for r_idx, r_data in enumerate(wf_table_data):
        row = t_wf.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = Inches(1.0)
            cell.text = val
            set_cell_margins(cell, top=60, bottom=60, left=40, right=40)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.font.size = Pt(8.5)
            if r_idx == 0:
                set_cell_background(cell, "1F3864")
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F2F4F4")

    p_cont = doc.add_paragraph()
    p_cont.paragraph_format.space_before = Pt(6)
    r_cont_lbl = p_cont.add_run("Operational Data Continuity: ")
    r_cont_lbl.bold = True
    p_cont.add_run("SAP S/4HANA Contracts (ME33K) & POs (ME23N) • RAG Vector Embedding Index • Use Case 2 Volume Rebate Calculation • Use Case 3 Statement 4-Way Match • AP Exception Desk • SAP MIRO/FB65 Posting & Settlement.")

    # PAGE BREAK FOR ARCHITECTURE BLUEPRINT
    doc.add_page_break()

    # Title Banner Page 2
    p_title2 = doc.add_paragraph()
    r_brand2 = p_title2.add_run("VIRA — Integration & Architecture\n")
    r_brand2.font.size = Pt(22)
    r_brand2.font.bold = True
    r_brand2.font.color.rgb = RGBColor(31, 56, 100)

    r_sub2 = p_title2.add_run("SAP S/4HANA Integration, Architectural Blueprint & Enterprise Value")
    r_sub2.font.size = Pt(13)
    r_sub2.font.bold = True
    r_sub2.font.color.rgb = RGBColor(41, 128, 185)

    p_meta2 = doc.add_paragraph()
    p_meta2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_m2 = p_meta2.add_run("ENTERPRISE BLUEPRINT | Page 2 of 2")
    r_m2.font.size = Pt(9.5)
    r_m2.font.bold = True
    r_m2.font.color.rgb = RGBColor(127, 140, 141)

    # SECTION 7 — SAP S/4HANA INTEGRATION
    add_styled_heading(doc, "SECTION 7 — SAP S/4HANA INTEGRATION", level=1)

    integ_data = [
        ("Integration Dimension", "Data Scope & Functional Mapping", "Data Governance & Storage Boundary"),
        ("Inbound from SAP S/4HANA\n(OData / REST APIs)", "Outline Contracts (ME33K), POs (ME23N), Line Items, Target Values, Agreed Unit Rates, Cost Centers, Vendor Master (LFA1).", "Retrieved from SAP. Master records remain governed exclusively in SAP S/4HANA; cached for operational display."),
        ("Operational Processing\n(VIRA Core Layer)", "PDF contract ingestion, RAG vector embeddings (all-MiniLM-L6-v2), YTD volume rebate calculation, 4-way statement fuzzy matching.", "Stored in VIRA. RAG vector chunks, audit logs, and exception telemetry are persisted in VIRA's transactional database."),
        ("Outbound to SAP S/4HANA\n(ABAP RFC / MIRO API)", "Verified contract rebates, draft Credit Memos (FB65), SAP Payment Blocks (BSEG-ZLSPR = 'A'), MIRO invoice parking.", "Posted to SAP. Final financial and compliance artifacts are transmitted back to SAP for settlement.")
    ]

    t_int = doc.add_table(rows=len(integ_data), cols=3)
    t_int.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_int.autofit = False
    col_w = [Inches(2.0), Inches(2.8), Inches(2.4)]

    for r_idx, r_data in enumerate(integ_data):
        row = t_int.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = col_w[c_idx]
            cell.text = val
            set_cell_margins(cell, top=70, bottom=70, left=80, right=80)
            p = cell.paragraphs[0]
            run = p.runs[0]
            run.font.size = Pt(9.0)
            if r_idx == 0:
                set_cell_background(cell, "1F3864")
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
            else:
                if r_idx % 2 == 1:
                    set_cell_background(cell, "F2F4F4")
                else:
                    set_cell_background(cell, "FFFFFF")

    # SECTION 8 — HIGH-LEVEL SOLUTION ARCHITECTURE
    add_styled_heading(doc, "SECTION 8 — HIGH-LEVEL SOLUTION ARCHITECTURE", level=1)

    arch_layers = [
        ("1. Enterprise ERP Layer (SAP S/4HANA System of Record)", "SAP S/4HANA\nOutline Agreements (ME33K) • Purchase Orders (ME23N) • Open Items (BSEG/BKPF) • Supplier Invoices (MIRO/FB60/FB65)\n<> Secure SAP Integration Layer (REST • OData • RFC Proxy • Destination Service • Sync Logs) <>"),
        ("2. VIRA Operational Core Platform (Execution & AI Verification Layer)", "CAP • Python FastAPI • RAG Vector Engine (all-MiniLM-L6-v2 / Ollama qwen2.5) • SQLite / SAP HANA Cloud\nUse Case 2 Rebate Auditor • Use Case 3 Statement Recon Engine • Exception Review Queue • Audit Event Logger\n<> Role-Governed Secure Web Endpoints (XSUAA / JWT Authentication • RBAC) <>"),
        ("3. Role-Tailored Operational Consoles (SAP Fiori-Inspired UX)", "React 19 / Vite • Desktop • Mobile\nCA: Admin Control Tower & Approvals • AP: Accounts Payable Auditor Desk • VM: Vendor Management Console")
    ]

    for title, body in arch_layers:
        p_a = doc.add_paragraph()
        r_at = p_a.add_run(title + "\n")
        r_at.bold = True
        r_at.font.color.rgb = RGBColor(31, 56, 100)
        p_a.add_run(body)
        p_a.paragraph_format.space_after = Pt(6)

    # SECTION 9 — TECHNOLOGY OVERVIEW
    add_styled_heading(doc, "SECTION 9 — TECHNOLOGY OVERVIEW", level=1)

    tech_data = [
        ("FRONTEND", "BACKEND SERVICES", "RAG & AI ENGINE", "DATA STORE", "PLATFORM"),
        ("React 19 • Vite\nTypeScript, Fiori Horizon UX", "Python FastAPI • CAP\nRESTful / OData API", "sentence-transformers\nall-MiniLM-L6-v2 / Ollama", "SQLite (WAL) — current\nSAP HANA Cloud — via CAP", "SAP BTP Cloud Foundry\nMTA, XSUAA, Destination")
    ]

    t_tech = doc.add_table(rows=2, cols=5)
    t_tech.alignment = WD_TABLE_ALIGNMENT.CENTER
    t_tech.autofit = False

    for r_idx, r_data in enumerate(tech_data):
        row = t_tech.rows[r_idx]
        for c_idx, val in enumerate(r_data):
            cell = row.cells[c_idx]
            cell.width = Inches(1.4)
            cell.text = val
            set_cell_margins(cell, top=60, bottom=60, left=50, right=50)
            p = cell.paragraphs[0]
            run = p.runs[0]
            run.font.size = Pt(8.5)
            if r_idx == 0:
                set_cell_background(cell, "1F3864")
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
            else:
                set_cell_background(cell, "F2F4F4")

    # SECTION 10 — DEPLOYMENT, SAP APIs & POLICY
    add_styled_heading(doc, "SECTION 10 — DEPLOYMENT, SAP APIs & POLICY (SAP BTP)", level=1)

    deploy_items = [
        ("Deployment", "MTA (mta.yaml) to SAP BTP Cloud Foundry: Python FastAPI service; React UI via HTML5 Repository + Approuter. Persistence: SQLite for local; SAP HANA Cloud for production via CAP DB binding."),
        ("Auth & Access", "XSUAA (IAS as identity provider); JWT on every endpoint; role collections mapped to CA / AP / VM / SA."),
        ("Connectivity", "Destination and Connectivity services; Cloud Connector if S/4HANA is on-premise; least-privilege technical user."),
        ("SAP APIs", "Inbound OData: Purchase Order (ME23N), Purchase Contract (ME33K), Open Items (BSEG). Outbound: Supplier Invoice (MIRO/FB65), Payment Block (BSEG-ZLSPR)."),
        ("Data Policy", "SAP owns master and financial data; VIRA caches for display and RAG vector search only. Encryption at rest and TLS in transit."),
        ("Audit & Governance", "Every RAG clause retrieval, volume rebate calculation, and statement match timestamped with user credentials and audit log IDs.")
    ]

    for title, desc in deploy_items:
        p_d = doc.add_paragraph()
        r_dt = p_d.add_run(title + ": ")
        r_dt.bold = True
        r_dt.font.color.rgb = RGBColor(41, 128, 185)
        p_d.add_run(desc)
        p_d.paragraph_format.space_after = Pt(3)

    # SECTION 11 — BUSINESS VALUE
    add_styled_heading(doc, "SECTION 11 — BUSINESS VALUE", level=1)

    values = [
        ("Eliminated Contract Overbilling (UC2)", "RAG vector clause search continuously audits invoice line items against PDF contract rate cards and automatically calculates retroactive 5% volume rebates once the ₹10 Crore threshold is passed."),
        ("Automated Statement Reconciliation (UC3)", "Multi-format OCR ingestion and 4-way fuzzy matching replace manual line-by-line Excel checking, discovering unapplied vendor credit notes and recovering overpayments."),
        ("Compressed Financial Close Cycles", "Real-time RAG clause verification and statement matching replace multi-week manual contract audits, collapsing period-end clearing to hours."),
        ("Complete Audit Governance", "Every vector clause match, volume calculation, and MIRO/FB65 posting is immutably timestamped with user credentials and audit logs.")
    ]

    for title, desc in values:
        p_v = doc.add_paragraph()
        r_vt = p_v.add_run(title + "\n")
        r_vt.bold = True
        r_vt.font.color.rgb = RGBColor(31, 56, 100)
        p_v.add_run(desc)
        p_v.paragraph_format.space_after = Pt(4)

    # SOLUTION APPROACH & POSITIONING
    add_styled_heading(doc, "SOLUTION APPROACH & POSITIONING", level=1)
    p_pos = doc.add_paragraph()
    p_pos.add_run("VIRA provides a purpose-built operational AI execution and RAG verification layer around SAP-connected contract and accounts payable workflows. ")
    p_pos.add_run("It enables business users, finance auditors, and procurement leads to collaborate through a modern, role-based interface while preserving strict alignment, security, and traceability with SAP S/4HANA business data.")

    # Save DOCX to Downloads and local workspace
    downloads_docx = r"C:\Users\Varad\Downloads\VIRA_Vendor_AI_Project_Plan.docx"
    downloads_md = r"C:\Users\Varad\Downloads\VIRA_Vendor_AI_Project_Plan.md"
    local_docx = os.path.join(os.getcwd(), "VIRA_Vendor_AI_Project_Plan.docx")
    local_md = os.path.join(os.getcwd(), "VIRA_Vendor_AI_Project_Plan.md")

    doc.save(downloads_docx)
    doc.save(local_docx)

    # Write PODZO-Style Markdown Document
    md_content = """# VIRA — Project Plan
## SAP S/4HANA-Connected AI Vendor Intelligence & AP Risk Platform
**PROJECT PLAN | Version 2.0 • October 2026**

**Executive Summary**: VIRA provides a centralized operational AI interface for managing SAP-connected contracts, purchase orders, vendor statement reconciliations, and automated credit/debit memo posting through to SAP MIRO / FB60 / FB65 payment clearing.

---

### SECTION 1 — USE CASE
Procurement contract enforcement and vendor statement reconciliation in SAP run largely on manual effort. Unstructured PDF contract clauses (rate cards, volume rebates, price adjustment terms) and monthly vendor statements (PDF/XLS) are audited manually by AP teams. **Need**: field execution tied to S/4HANA POs and settlement, with SAP remaining the financial system of record.

---

### SECTION 2 — REFERENCE USE CASE
Standard SAP procure-to-pay 3-way match (PO → Goods Receipt → Supplier Invoice MIRO) checks static PO line items. However, MIRO cannot evaluate unstructured PDF contract clauses, cumulative year-to-date volume rebate thresholds (> ₹10 Crore), or unapplied credit notes on external vendor statements. VIRA bridges this gap by automatically injecting RAG clause verification and 4-way statement reconciliation into the SAP posting flow.

---

### SECTION 3 — SOLUTION: VIRA AT A GLANCE
VIRA is an enterprise operational execution and AI verification platform designed to bridge SAP S/4HANA with contract compliance and vendor accounts payable fulfillment. By retrieving active contracts (ME33K), purchase orders (ME23N), and open items (BSEG/BKPF) directly from SAP S/4HANA, VIRA governs AI contract clause auditing, RAG vector search, volume rebate calculation, and multi-format statement matching—delivering end-to-end auditability while preserving SAP as the single authoritative financial core.

* **✓ Direct SAP S/4HANA Alignment**: Live ingestion of active contracts (ME33K) & POs (ME23N) via real-time OData / REST services.
* **✓ RAG Vector Search & Clause Governance**: Embeddings engine (`all-MiniLM-L6-v2` / Ollama `qwen2.5`) indexes contract clauses for instant rate card & rebate auditing.
* **✓ Automated Settlement & FB65**: RAG verification feeds verified rebate credit memos and debit notes directly into SAP MIRO / FB65 invoice parking.

---

### SECTION 4 — KEY CAPABILITIES
* **◆ SAP S/4HANA Synchronization**: Direct ingestion of active outline agreements (ME33K) and purchase orders (ME23N) with materials, rate cards, target values, and validity windows.
* **◆ RAG Vector Search & Embeddings Engine**: Ingests PDF/Text contract agreements, generates 384-dimensional vector embeddings, and performs Cosine Similarity search for clause retrieval.
* **◆ Cumulative Volume Rebate Auditor**: Tracks YTD purchase volume in SAP (BSEG/BKPF). Once the ₹10 Crore threshold is breached, calculates the 5% rebate due and drafts SAP Credit Memos (FB65).
* **◆ Multi-Format Vendor Statement Ingestion**: Parses monthly vendor statements in any layout (PDF, XLS, CSV) using OCR and Intelligent Document Processing (IDP).
* **◆ 4-Way Fuzzy Reconciliation Desk**: Performs intelligent matching across Vendor Statement vs SAP Open Items (BSEG) vs Bank Clearings (FEBEP) vs Credit Memos to spot unapplied credits.
* **◆ Invoicing & SAP MIRO / FB65 Posting**: Consolidation of verified audit results into draft credit/debit memos, staging audit-ready data for SAP MIRO supplier invoice parking and settlement.

---

### SECTION 5 — ROLE-BASED OPERATIONS
* **[CA] Company Admin / Finance Controller**: Manages contract rate cards, volume rebate targets, variance approval queues, and final SAP MIRO/FB65 invoice approvals.
* **[AP] Accounts Payable Auditor**: Reviews RAG contract overbilling alerts, verifies unapplied vendor credit notes, and releases payment blocks.
* **[VM] Vendor Management Lead**: Monitors supplier statement reconciliation status, tracks rebate claims, and manages vendor contract rate card updates.
* **[AI] Autonomous RAG Engine**: Executes vector search against contract agreements, computes cosine similarity, and flags price leakage or missing credit notes.
* **[SA] SAP FICO Specialist**: Governs OData/REST API sync, configures BSEG-ZLSPR payment block rules, and maintains SAP system-of-record integrity.

---

### SECTION 6 — END-TO-END OPERATIONAL WORKFLOW

| STEP 1 | STEP 2 | STEP 3 | STEP 4 | STEP 5 | STEP 6 | STEP 7 |
|---|---|---|---|---|---|---|
| **SAP Sync**<br>Contracts & POs | **Doc Ingestion**<br>PDF Contracts/Stmts | **RAG Vector Store**<br>Embedding Index | **Use Case 2 Audit**<br>Rebate Leakage | **Use Case 3 Audit**<br>Statement Recon | **Exception Desk**<br>Auditor Sign-off | **SAP MIRO/FB65**<br>Clear & Post |

**Operational Data Continuity**: SAP S/4HANA Contracts (ME33K) & POs (ME23N) • RAG Vector Embedding Index • Use Case 2 Volume Rebate Calculation • Use Case 3 Statement 4-Way Match • AP Exception Desk • SAP MIRO/FB65 Posting & Settlement.

---

### SECTION 7 — SAP S/4HANA INTEGRATION

| Integration Dimension | Data Scope & Functional Mapping | Data Governance & Storage Boundary |
|---|---|---|
| **Inbound from SAP S/4HANA** (OData / REST APIs) | Outline Contracts (ME33K), POs (ME23N), Line Items, Target Values, Agreed Unit Rates, Cost Centers, Vendor Master (LFA1). | Retrieved from SAP. Master records remain governed exclusively in SAP S/4HANA; cached for operational display. |
| **Operational Processing** (VIRA Core Layer) | PDF contract ingestion, RAG vector embeddings (`all-MiniLM-L6-v2`), YTD volume rebate calculation, 4-way statement fuzzy matching. | Stored in VIRA. RAG vector chunks, audit logs, and exception telemetry are persisted in VIRA's transactional database. |
| **Outbound to SAP S/4HANA** (ABAP RFC / MIRO API) | Verified contract rebates, draft Credit Memos (FB65), SAP Payment Blocks (`BSEG-ZLSPR = 'A'`), MIRO invoice parking. | Posted to SAP. Final financial and compliance artifacts are transmitted back to SAP for settlement. |

---

### SECTION 8 — HIGH-LEVEL SOLUTION ARCHITECTURE

1. **Enterprise ERP Layer (SAP S/4HANA System of Record)**: SAP S/4HANA Outline Agreements (ME33K) • Purchase Orders (ME23N) • Open Items (BSEG/BKPF) • Supplier Invoices (MIRO/FB60/FB65).
   * `<> Secure SAP Integration Layer (REST • OData • RFC Proxy • Destination Service • Sync Logs) <>`
2. **VIRA Operational Core Platform (Execution & AI Verification Layer)**: CAP • Python FastAPI • RAG Vector Engine (`all-MiniLM-L6-v2` / Ollama `qwen2.5`) • SQLite / SAP HANA Cloud. Use Case 2 Rebate Auditor • Use Case 3 Statement Recon Engine • Exception Review Queue • Audit Event Logger.
   * `<> Role-Governed Secure Web Endpoints (XSUAA / JWT Authentication • RBAC) <>`
3. **Role-Tailored Operational Consoles (SAP Fiori-Inspired UX)**: React 19 / Vite • Desktop • Mobile. CA: Admin Control Tower & Approvals • AP: Accounts Payable Auditor Desk • VM: Vendor Management Console.

---

### SECTION 9 — TECHNOLOGY OVERVIEW

| FRONTEND | BACKEND SERVICES | RAG & AI ENGINE | DATA STORE | PLATFORM |
|---|---|---|---|---|
| React 19 • Vite<br>TypeScript, Fiori Horizon UX | Python FastAPI • CAP<br>RESTful / OData API | sentence-transformers<br>`all-MiniLM-L6-v2` / Ollama | SQLite (WAL) — current<br>SAP HANA Cloud — via CAP | SAP BTP Cloud Foundry<br>MTA, XSUAA, Destination |

---

### SECTION 10 — DEPLOYMENT, SAP APIs & POLICY (SAP BTP)
* **Deployment**: MTA (`mta.yaml`) to SAP BTP Cloud Foundry: Python FastAPI service; React UI via HTML5 Repository + Approuter. Persistence: SQLite for local; SAP HANA Cloud for production via CAP DB binding.
* **Auth & Access**: XSUAA (IAS as identity provider); JWT on every endpoint; role collections mapped to CA / AP / VM / SA.
* **Connectivity**: Destination and Connectivity services; Cloud Connector if S/4HANA is on-premise; least-privilege technical user.
* **SAP APIs**: Inbound OData: Purchase Order (ME23N), Purchase Contract (ME33K), Open Items (BSEG). Outbound: Supplier Invoice (MIRO/FB65), Payment Block (`BSEG-ZLSPR`).
* **Data Policy**: SAP owns master and financial data; VIRA caches for display and RAG vector search only. Encryption at rest and TLS in transit.
* **Audit & Governance**: Every RAG clause retrieval, volume rebate calculation, and statement match timestamped with user credentials and audit log IDs.

---

### SECTION 11 — BUSINESS VALUE
* **Eliminated Contract Overbilling (UC2)**: RAG vector clause search continuously audits invoice line items against PDF contract rate cards and automatically calculates retroactive 5% volume rebates once the ₹10 Crore threshold is passed.
* **Automated Statement Reconciliation (UC3)**: Multi-format OCR ingestion and 4-way fuzzy matching replace manual line-by-line Excel checking, discovering unapplied vendor credit notes and recovering overpayments.
* **Compressed Financial Close Cycles**: Real-time RAG clause verification and statement matching replace multi-week manual contract audits, collapsing period-end clearing to hours.
* **Complete Audit Governance**: Every vector clause match, volume calculation, and MIRO/FB65 posting is immutably timestamped with user credentials and audit logs.

---

### SOLUTION APPROACH & POSITIONING
VIRA provides a purpose-built operational AI execution and RAG verification layer around SAP-connected contract and accounts payable workflows. It enables business users, finance auditors, and procurement leads to collaborate through a modern, role-based interface while preserving strict alignment, security, and traceability with SAP S/4HANA business data.
"""

    with open(downloads_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(local_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("VIRA PODZO-Style Project Plan generated successfully!")

if __name__ == "__main__":
    build_vira_project_plan()
