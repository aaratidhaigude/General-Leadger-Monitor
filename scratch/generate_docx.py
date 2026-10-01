import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

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
        run.font.size = Pt(18)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
    elif level == 2:
        run.font.color.rgb = RGBColor(41, 128, 185) # Slate/Ocean Blue (#2980B9)
        run.font.size = Pt(14)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
    elif level == 3:
        run.font.color.rgb = RGBColor(52, 73, 94) # Dark Grey (#34495E)
        run.font.size = Pt(12)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(2)
    return h

def build_docx():
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Title Banner
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title_run = title_p.add_run("Enterprise Specification Document")
    title_run.font.name = "Calibri"
    title_run.font.size = Pt(24)
    title_run.font.bold = True
    title_run.font.color.rgb = RGBColor(31, 56, 100)

    sub_p = doc.add_paragraph()
    sub_run = sub_p.add_run("AI & Finance Autonomous Vendor Risk & Accounts Payable (AP) Suite")
    sub_run.font.name = "Calibri"
    sub_run.font.size = Pt(15)
    sub_run.font.bold = True
    sub_run.font.color.rgb = RGBColor(41, 128, 185)

    meta_p = doc.add_paragraph()
    meta_run = meta_p.add_run("Target Audience: SAP FICO Consultants, AP Managers, Internal Auditors, CFO Office | Version 2.0")
    meta_run.font.size = Pt(10)
    meta_run.font.italic = True
    meta_run.font.color.rgb = RGBColor(127, 140, 141)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Executive Summary
    add_styled_heading(doc, "1. Executive Summary", level=1)
    p = doc.add_paragraph()
    p.add_run("Standard SAP S/4HANA / FICO handles routine transaction recording (FB60, MIRO, F110, MR11). However, standard SAP relies on ")
    r_bold = p.add_run("rigid, exact-match rules and manual user intervention")
    r_bold.bold = True
    p.add_run(". It cannot interpret unstructured PDF contracts, detect sophisticated Business Email Compromise (BEC) fraud, reconcile unstructured monthly vendor statements, or dynamically verify real-time government tax portal filings.\n\nThis document outlines ")
    r_bold2 = p.add_run("8 High-Impact Enterprise AI & Finance Use Cases")
    r_bold2.bold = True
    p.add_run(" designed to eliminate manual FICO/AP auditor workloads, prevent multi-crore cash leakage, enforce compliance, and protect working capital.")

    # Summary Table
    add_styled_heading(doc, "2. Use Case Summary Matrix", level=1)

    matrix_data = [
        ("UC #", "Use Case Name", "Core SAP Limitation", "Manual Effort Saved", "Enterprise Business Impact"),
        ("1", "Vendor Bank Account Change Fraud & BEC Guard", "SAP FK08 offers basic dual control; can't detect spoofed letterheads or BEC scams.", "100% manual phone/email vendor bank verification.", "Prevents multi-crore direct wire transfer fraud."),
        ("2", "Contract Price & Volume Rebate Leakage Detector", "MIRO checks PO price; ignores PDF contracts & dynamic volume rebates.", "Months of manual year-end contract auditing.", "Reclaims 2-5% of annual procurement leakage."),
        ("3", "Vendor Statement Reconciliation & Credit Recovery", "SAP FBL1N tracks internal data only; external statements checked manually.", "Hundreds of AP accounting hours per month.", "Recovers unapplied credit notes & avoids vendor disputes."),
        ("4", "Real-Time Tax Credit (GST/VAT) Mismatch Guard", "SAP posts tax codes but can't verify if vendor filed on government portal.", "Manual monthly report downloads & portal comparisons.", "Protects 100% of Input Tax Credit (ITC) eligibility."),
        ("5", "GR/IR Clearing Root Cause & Auto-Resolution", "MR11 lists un-cleared items but gives zero root-cause explanation.", "Days investigating line-item discrepancies.", "Accelerates month-end financial close by 70%."),
        ("6", "Dynamic Early Payment Discount Optimizer", "F110 executes payments on fixed terms without cash flow yield calculation.", "Manual treasury decision making.", "Generates 15-24% annualized return on idle cash."),
        ("7", "Split-Invoice & Evasion Duplicate Posting Audit", "SAP FB60 catches exact duplicate invoice numbers only.", "Manual sample auditing by internal risk teams.", "Blocks split-billing approval bypasses & double payments."),
        ("8", "Predictive Vendor Risk & Insolvency Monitor", "Vendor Master (BP) stores static data; no dynamic credit/bankruptcy tracking.", "Reactive fire-fighting when vendor goes bankrupt.", "Protects supply chain continuity & advance deposits.")
    ]

    table = doc.add_table(rows=len(matrix_data), cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = [Inches(0.5), Inches(1.8), Inches(1.8), Inches(1.5), Inches(1.8)]

    for row_idx, row_data in enumerate(matrix_data):
        row = table.rows[row_idx]
        for col_idx, cell_value in enumerate(row_data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            cell.text = cell_value
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            
            run = p.runs[0] if p.runs else p.add_run(cell_value)
            run.font.size = Pt(9.5)
            
            if row_idx == 0:
                set_cell_background(cell, "1F3864")
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
            else:
                if row_idx % 2 == 1:
                    set_cell_background(cell, "F2F4F4")
                else:
                    set_cell_background(cell, "FFFFFF")

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # Detailed Specifications Section
    add_styled_heading(doc, "3. Detailed Technical Specifications", level=1)

    use_cases = [
        {
            "num": "1",
            "title": "Vendor Bank Account Change Fraud & BEC Guard",
            "context": "A vendor's finance manager (or a hacker spoofing their email address via Business Email Compromise) sends a PDF on company letterhead requesting: 'Please update our bank account details for all future invoice payouts to Account X.'",
            "limitation": "In SAP S/4HANA, when bank details are changed in BP (Vendor Master) or LFBK, SAP logs the change in CDHDR/CDPOS and optionally requires confirmation via FK08 / FK09 (4-Eye Principle). However, SAP has ZERO capability to verify whether the attached PDF letterhead is authentic, if the bank account belongs to a shell company, or if the bank account matches an internal company employee's personal payroll bank account (internal fraud collusion).",
            "solution": [
                "Multimodal Document Inspection: AI ingests bank change request PDFs, inspecting font consistency, digital stamp integrity, and bank logo authenticity.",
                "Employee-Vendor Cross Matching: Continuously cross-checks vendor bank accounts against internal employee payroll accounts to block insider collusion.",
                "Risk-Based Payment Lock: If a bank account is changed within 7 days before an F110 payment run, or for a vendor with pending high-value invoices, the AI applies a SAP Payment Block (BSEG-ZLSPR = 'A') and triggers an automated out-of-band verification workflow."
            ]
        },
        {
            "num": "2",
            "title": "AI Contract Price & Volume Rebate Leakage Detector",
            "context": "A company signs a 3-year procurement contract for raw materials specifying Base Price ₹1,000/unit, plus a 5% retroactive rebate if annual purchase volume exceeds ₹10 Crore.",
            "limitation": "Standard 3-way matching in SAP (MIRO) compares Invoice vs Purchase Order (EKPO) vs Goods Receipt (MSEG). MIRO checks static PO prices but cannot parse or evaluate unstructured PDF contract clauses, tiered volume rebates, or external commodity market indices. Vendors bill at base PO price, and companies miss out on crores in rebates unless FICO auditors manually audit contracts at year-end.",
            "solution": [
                "Contract RAG & LLM Clause Extraction: AI parses PDF contracts, extracting rebate tiers, penalty terms, and index linkages.",
                "Real-Time Cumulative Audit: The AI tracks cumulative year-to-date invoice volumes in SAP (BSEG/BKPF). Once the ₹10 Crore threshold is breached, the AI calculates the 5% rebate due.",
                "Automated Leakage Recovery: Drafts an SAP Credit Memo / Debit Note (FB65) and alerts Procurement before the next payment run."
            ]
        },
        {
            "num": "3",
            "title": "Vendor Statement Reconciliation & Credit Recovery Agent",
            "context": "At month-end, suppliers mail vendor statements (PDF/Excel) listing all invoices issued, payments received, and credit notes issued (for damaged or returned goods).",
            "limitation": "Standard SAP (FBL1N / FAGLL03) shows only internal SAP records. Reconciling an external 500-row vendor statement against internal SAP line items is 100% manual for AP accountants. Unapplied credit notes issued by vendors are easily missed, resulting in overpaying suppliers.",
            "solution": [
                "Multi-Format Statement Ingestion: AI parses vendor monthly statements in any layout (PDF, XLS, CSV).",
                "4-Way Fuzzy Matching Engine: Performs intelligent matching across Vendor Statement vs SAP Open Items (BSEG) vs Bank Clearings (FEBEP) vs Credit Memos.",
                "Unapplied Credit Recovery: Highlights missing credit notes in SAP and automatically drafts credit memo entries for AP sign-off."
            ]
        },
        {
            "num": "4",
            "title": "Real-Time Tax Credit (GST / VAT) Mismatch & ITC Guard",
            "context": "When a vendor bills ₹10 Lakhs + ₹1.8 Lakhs GST (18%), the buyer pays ₹11.8 Lakhs. The buyer expects to claim ₹1.8 Lakhs as Input Tax Credit (ITC) from the government.",
            "limitation": "SAP records tax codes (BSET), but cannot verify if the vendor actually filed the invoice on the government portal (e.g., GSTR-2B in India, VIES in EU). If the vendor fails to file, the buyer loses the tax credit. FICO teams spend hundreds of hours manually downloading tax portal reports and comparing them against SAP registers in Excel.",
            "solution": [
                "API Tax Portal Sync: AI agent fetches live tax portal data via API and reconciles it line-by-line with SAP BSET / BSEG tax tables.",
                "Predictive ITC Payment Block: If a vendor has a history of tax filing defaults or missing portal entries, the AI automatically applies a payment block equal to the unverified Tax Amount (BSEG-ZLSPR) until the vendor files on the portal."
            ]
        },
        {
            "num": "5",
            "title": "AI GR/IR Clearing Root-Cause Intelligence",
            "context": "In SAP MM/FI, when goods arrive, a Goods Receipt (GR) is posted. When the bill arrives, an Invoice Receipt (IR) is posted. If amounts or quantities differ, the transaction stays open in the GR/IR clearing account.",
            "limitation": "Transaction MR11 in SAP lists open GR/IR balances, but provides ZERO explanation as to why the item won't clear. FICO consultants spend days investigating line-item discrepancies across POs, GRs, and IRs to determine if variance is due to short delivery, freight misallocation, or price changes.",
            "solution": [
                "Graph/ML Root Cause Analyzer: AI examines transaction history (EKKO, EKPO, MKPF, MSEG, RBKP, RSEG) to pinpoint exact root causes (e.g., 'Vendor delivered +4% over PO tolerance').",
                "Autonomous Resolution Proposal: Recommends exact corrective actions (MR11 write-off, PO quantity adjustment, vendor debit note) with confidence scoring."
            ]
        },
        {
            "num": "6",
            "title": "Dynamic Early Payment Discount & Working Capital Optimizer",
            "context": "Vendors often offer early payment terms such as '2/10 Net 30' (2% discount if paid within 10 days, otherwise full payment in 30 days). A 2% discount paid 20 days early equals an annualized return of ~36% on cash.",
            "limitation": "SAP F110 (Automatic Payment Run) executes payments strictly on fixed baseline dates (e.g., net due date). SAP cannot dynamically evaluate corporate treasury bank balances against vendor discount yields to optimize return on liquidity.",
            "solution": [
                "Dynamic Yield Evaluator: AI monitors real-time cash balances and evaluates payment terms across all open vendor invoices (BSEG).",
                "ROI Payment Scheduler: Ranks invoices by highest discount yield and recommends the optimal payment date to maximize interest saved without compromising working capital."
            ]
        },
        {
            "num": "7",
            "title": "Split-Invoice & Evasion Duplicate Posting Audit",
            "context": "To bypass internal manager approval thresholds (e.g., approval required for invoices > ₹5 Lakhs), vendors or internal buyers split a ₹12 Lakh purchase into three smaller invoices of ₹4 Lakhs each. Or, a vendor submits the same invoice twice under altered numbers (e.g., INV-1001 and INV1001_A).",
            "limitation": "Standard SAP duplicate invoice checks (FB60/MIRO) only check for EXACT matches of Vendor + Invoice Number + Amount + Currency + Date. Minor character changes or split invoice dates completely bypass SAP's duplicate check.",
            "solution": [
                "Fuzzy & N-Gram Text Matching: AI checks invoice numbers using Levenshtein distance and N-gram similarity.",
                "Velocity Clustering: Detects multiple invoices from the same vendor within short time windows that collectively match standard approval thresholds or prior invoice amounts.",
                "Automated Audit Flag: Flags suspicious split invoices before F110 execution."
            ]
        },
        {
            "num": "8",
            "title": "Predictive Vendor Risk & Insolvency Monitor",
            "context": "A critical sole-source supplier facing bankruptcy suddenly stops operations, leaving advance deposits lost and key manufacturing lines halted.",
            "limitation": "SAP Vendor Master (BP) stores static attributes (address, tax ID, payment terms). SAP has no connectivity to external credit ratings, legal court filings, or market news to monitor vendor solvency.",
            "solution": [
                "OSINT & Credit API Monitoring: AI continuously ingests public court records, credit updates (CIBIL / Dun & Bradstreet), news sentiment, and SAP payment stretch metrics.",
                "Vendor Health Index (VHI): Computes a real-time risk score. If insolvency risk increases, the AI alerts Procurement and blocks advance payments."
            ]
        }
    ]

    for uc in use_cases:
        add_styled_heading(doc, f"3.{uc['num']} Use Case {uc['num']}: {uc['title']}", level=2)
        
        # Context
        p_c = doc.add_paragraph()
        r_lbl = p_c.add_run("Real-World Business Context: ")
        r_lbl.bold = True
        r_lbl.font.color.rgb = RGBColor(41, 128, 185)
        p_c.add_run(uc["context"])
        
        # Limitation
        p_l = doc.add_paragraph()
        r_lbl2 = p_l.add_run("Why Standard SAP FICO Fails: ")
        r_lbl2.bold = True
        r_lbl2.font.color.rgb = RGBColor(192, 57, 43) # Dark Red
        p_l.add_run(uc["limitation"])
        
        # Solution
        p_s = doc.add_paragraph()
        r_lbl3 = p_s.add_run("AI Agent Solution Workflow:")
        r_lbl3.bold = True
        r_lbl3.font.color.rgb = RGBColor(39, 174, 96) # Emerald Green
        
        for item in uc["solution"]:
            bp = doc.add_paragraph(style='List Bullet')
            parts = item.split(":", 1)
            if len(parts) == 2:
                r1 = bp.add_run(parts[0] + ":")
                r1.bold = True
                bp.add_run(parts[1])
            else:
                bp.add_run(item)
            bp.paragraph_format.space_before = Pt(1)
            bp.paragraph_format.space_after = Pt(2)
            
        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    # Rebranding Title Suggestion
    add_styled_heading(doc, "4. Rebranded Project Title Recommendation", level=1)
    p_title = doc.add_paragraph()
    p_title.add_run("To present this enterprise-grade scope to SAP FICO teams and C-level executives, we recommend rebranding the system as:\n\n")
    
    r_main = p_title.add_run("SAP Vendor Intelligence & AP Risk Agent (VIRA)")
    r_main.bold = True
    r_main.font.size = Pt(14)
    r_main.font.color.rgb = RGBColor(31, 56, 100)
    
    p_title.add_run("\nSubtitle: Enterprise AI Engine for Source-to-Pay Risk, Fraud & Working Capital Optimization")

    # Save to artifacts and local directory
    artifact_dir = r"C:\Users\Varad\.gemini\antigravity-cli\brain\519454df-0cdb-42fc-94bd-b5ee6e8747f1"
    artifact_path = os.path.join(artifact_dir, "SAP_Vendor_AI_Use_Cases_Specification.docx")
    local_path = os.path.join(os.getcwd(), "SAP_Vendor_AI_Use_Cases_Specification.docx")

    doc.save(artifact_path)
    doc.save(local_path)
    print(f"DOCX successfully generated:\n Artifact: {artifact_path}\n Local: {local_path}")

if __name__ == "__main__":
    build_docx()
