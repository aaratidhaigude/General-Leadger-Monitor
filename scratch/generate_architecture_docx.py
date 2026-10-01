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
        run.font.color.rgb = RGBColor(31, 56, 100) # Deep Executive Navy (#1F3864)
        run.font.size = Pt(18)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(16)
        h.paragraph_format.space_after = Pt(6)
    elif level == 2:
        run.font.color.rgb = RGBColor(41, 128, 185) # Slate Blue (#2980B9)
        run.font.size = Pt(14)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(14)
        h.paragraph_format.space_after = Pt(4)
    elif level == 3:
        run.font.color.rgb = RGBColor(52, 73, 94) # Dark Slate (#34495E)
        run.font.size = Pt(12)
        run.font.bold = True
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(2)
    return h

def build_architecture_doc():
    doc = Document()

    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Document Header
    p_title = doc.add_paragraph()
    r_t = p_title.add_run("System Architecture & Workflow Specification")
    r_t.font.size = Pt(24)
    r_t.font.bold = True
    r_t.font.color.rgb = RGBColor(31, 56, 100)

    p_sub = doc.add_paragraph()
    r_s = p_sub.add_run("SAP Vendor Intelligence & AP Risk Agent (VIRA) — RAG & AI Pipeline")
    r_s.font.size = Pt(15)
    r_s.font.bold = True
    r_s.font.color.rgb = RGBColor(41, 128, 185)

    p_meta = doc.add_paragraph()
    r_m = p_meta.add_run("Version 2.0 | Domain: SAP S/4HANA Finance, RAG Vector Search & Accounts Payable AI")
    r_m.font.size = Pt(10)
    r_m.font.italic = True
    r_m.font.color.rgb = RGBColor(127, 140, 141)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 1: End-to-End System Topology
    add_styled_heading(doc, "1. End-to-End System Architecture Topology", level=1)
    
    p_arch = doc.add_paragraph()
    p_arch.add_run("The ")
    r_bold = p_arch.add_run("SAP Vendor Intelligence & AP Risk Agent (VIRA)")
    r_bold.bold = True
    p_arch.add_run(" system operates as an autonomous intelligent risk layer positioned between ")
    p_arch.add_run("SAP S/4HANA Finance modules (BKPF, BSEG, EKKO, EKPO, RBKP) and the F110 Payment Engine.\n\n")
    p_arch.add_run("The architecture comprises 4 core layers:")

    layers = [
        ("Layer 1: SAP Data Ingestion Layer", "Pulls live or mock invoice data, vendor master attributes (BP/LFBK), purchase orders (EKKO/EKPO), goods receipts (MSEG), and clearing history."),
        ("Layer 2: RAG Vector Store & Embeddings Engine", "Ingests unstructured PDF/Text contracts, splits them into clause chunks, generates 384-dimensional vector embeddings using sentence-transformers (all-MiniLM-L6-v2), and indexes them for cosine similarity search."),
        ("Layer 3: Autonomous AI Risk Pipeline Engine", "Executes 8 parallel enterprise AI use cases across Pre-Payment Guard (Pipeline A) and Post-Payment Reconciliation (Pipeline B)."),
        ("Layer 4: SAP Action & Workflow Control Layer", "Executes automated SAP actions, placing Payment Blocks (BSEG-ZLSPR = 'A'), drafting SAP Credit Memos (FB65), or issuing MR11 write-off recommendations.")
    ]

    for title, desc in layers:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(title + ": ")
        r1.bold = True
        r1.font.color.rgb = RGBColor(31, 56, 100)
        bp.add_run(desc)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 2: Detailed Workflow Sequence Diagram
    add_styled_heading(doc, "2. End-to-End Workflow & Pipeline Execution Flow", level=1)

    p_wf = doc.add_paragraph()
    p_wf.add_run("The diagram below illustrates the detailed execution workflow from SAP Invoice Ingestion to RAG Vector Search, AI Scoring, and SAP Payment Block execution:")

    workflow_steps = [
        ("Step 1: Invoice Ingestion", "SAP invoice posted via FB60 / MIRO or pulled via API endpoint (/api/pull). Invoice details (Vendor, Amount, GL, Contract Ref) enter the pipeline."),
        ("Step 2: Pre-Payment Pipeline A (UC1, UC2, UC7, UC8)", "Executes 4 Pre-Payment Risk Checks in parallel:\n  • UC1: Scans vendor bank change history & employee payroll matches.\n  • UC2: Executes RAG Vector Search against contract rate cards.\n  • UC7: Runs Levenshtein fuzzy text matching & velocity split-billing audit.\n  • UC8: Computes Vendor Health Index (VHI) for insolvency signals."),
        ("Step 3: RAG Vector Search Execution", "rag_engine.py encodes the invoice query into a 384-dimensional vector, searches stored contract chunks, and retrieves the highest matching contract clause."),
        ("Step 4: Composite ARI Score Calculation", "Combines raw scores from all 4 steps using weighted matrix (Bank Guard 35%, Contract Audit 30%, Evasion Audit 20%, Vendor Health 15%)."),
        ("Step 5: SAP Payment Block / Hard Override Trigger", "If ARI > 70 or a Hard Override is triggered (e.g. Bank Changed < 7d), SAP Payment Block 'A' is placed on BSEG-ZLSPR."),
        ("Step 6: Post-Payment Pipeline B (UC3, UC4, UC5, UC6)", "For cleared invoices (Status Z), executes post-payment audit:\n  • UC3: Performs 4-way fuzzy reconciliation against vendor monthly statements.\n  • UC4: Verifies live government tax portal filings (GSTR-2B / VIES).\n  • UC5: Classifies un-cleared GR/IR items (MR11) via ML root-cause analysis.\n  • UC6: Evaluates cash flow liquidity against payment discount yields (2/10 Net 30)."),
        ("Step 7: Dashboard UI Rendering & Review Queue", "Results are served via FastAPI endpoints (/api/engine/both) and rendered live on the Fiori Horizon UI (http://localhost:8000).")
    ]

    for title, desc in workflow_steps:
        add_styled_heading(doc, title, level=3)
        p = doc.add_paragraph(desc)
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)

    # Section 3: RAG Vector Search Architecture Deep-Dive
    add_styled_heading(doc, "3. RAG Vector Search & Embeddings Engine Deep-Dive", level=1)

    p_rag = doc.add_paragraph()
    p_rag.add_run("The RAG Vector Engine (")
    r_code = p_rag.add_run("backend/agent/rag_engine.py")
    r_code.bold = True
    p_rag.add_run(") operates as follows:\n")

    rag_details = [
        ("1. Text Vectorization", "Loads contract documents from data/contracts/*.txt, splits them by SECTION headers, and converts each clause into a 384-dimensional vector embedding using all-MiniLM-L6-v2."),
        ("2. Cosine Similarity Matching", "When an invoice is scored, query_contract_clauses(vendor_name, query_text) computes the dot product / cosine similarity between the invoice query vector and stored clause vectors."),
        ("3. Clause Retrieval & Injection", "The highest-scoring clause is retrieved and injected into the contract auditor output (contract_auditor.py), providing a clear mathematical and textual audit rationale.")
    ]

    for title, desc in rag_details:
        bp = doc.add_paragraph(style='List Bullet')
        r1 = bp.add_run(title + ": ")
        r1.bold = True
        bp.add_run(desc)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Section 4: 8 Use Cases Workflow Matrix
    add_styled_heading(doc, "4. 8 Use Cases Workflow & Weight Matrix", level=1)

    matrix_data = [
        ("UC #", "Pipeline", "Use Case Name", "AI Engine / RAG Component", "Weight", "Automated SAP Action"),
        ("UC1", "Pre-Payment (A)", "Vendor Bank Change Fraud & BEC Guard", "Multimodal PDF check & Employee Payroll Match", "35%", "Block Payment (BSEG-ZLSPR = 'A')"),
        ("UC2", "Pre-Payment (A)", "Contract Price & Volume Rebate Detector", "RAG Vector Search (rag_engine.py)", "30%", "Draft SAP Debit Memo (FB65)"),
        ("UC7", "Pre-Payment (A)", "Split-Invoice & Evasion Duplicate Audit", "Levenshtein Fuzzy Match & Velocity Clustering", "20%", "Flag Split Approval Bypass"),
        ("UC8", "Pre-Payment (A)", "Predictive Vendor Risk & Insolvency Monitor", "OSINT & Vendor Health Index (VHI)", "15%", "Advance Payment Hold"),
        ("UC3", "Post-Payment (B)", "Vendor Statement Reconciliation", "4-Way Fuzzy Statement Matching Engine", "30%", "Unapplied Credit Note Recovery"),
        ("UC4", "Post-Payment (B)", "Real-Time Tax Credit (GST/VAT) Guard", "Govt Tax Portal API Sync (GSTR-2B)", "35%", "Unverified Tax Amount Block"),
        ("UC5", "Post-Payment (B)", "GR/IR Clearing Root-Cause Intelligence", "ML Root Cause Classifier (MR11)", "20%", "Auto Write-off / PO Adjustment"),
        ("UC6", "Post-Payment (B)", "Dynamic Early Payment Discount Optimizer", "Liquidity Cash Yield Optimizer (2/10 Net 30)", "15%", "Dynamic Payment Release")
    ]

    table = doc.add_table(rows=len(matrix_data), cols=6)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    col_widths = [Inches(0.6), Inches(1.3), Inches(1.8), Inches(1.8), Inches(0.7), Inches(1.6)]

    for row_idx, row_data in enumerate(matrix_data):
        row = table.rows[row_idx]
        for col_idx, cell_value in enumerate(row_data):
            cell = row.cells[col_idx]
            cell.width = col_widths[col_idx]
            cell.text = cell_value
            set_cell_margins(cell, top=80, bottom=80, left=80, right=80)
            
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            
            run = p.runs[0] if p.runs else p.add_run(cell_value)
            run.font.size = Pt(9.0)
            
            if row_idx == 0:
                set_cell_background(cell, "1F3864")
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
            else:
                if row_idx % 2 == 1:
                    set_cell_background(cell, "F2F4F4")
                else:
                    set_cell_background(cell, "FFFFFF")

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Section 5: Rebranding & Verification Details
    add_styled_heading(doc, "5. Project Rebranding & Server Information", level=1)
    
    p_info = doc.add_paragraph()
    p_info.add_run("Project Name: ").bold = True
    p_info.add_run("SAP Vendor Intelligence & AP Risk Agent (VIRA)\n")
    p_info.add_run("Server Endpoint: ").bold = True
    p_info.add_run("http://localhost:8000\n")
    p_info.add_run("API Health Endpoint: ").bold = True
    p_info.add_run("http://localhost:8000/api/health\n")
    p_info.add_run("API Pipelines: ").bold = True
    p_info.add_run("POST /api/engine/before | POST /api/engine/after | POST /api/engine/both\n")

    # Save to Downloads and Artifacts
    downloads_docx = r"C:\Users\Varad\Downloads\SAP_Vendor_Intelligence_Architecture_and_Workflow.docx"
    downloads_md = r"C:\Users\Varad\Downloads\SAP_Vendor_Intelligence_Architecture_and_Workflow.md"
    artifact_docx = r"C:\Users\Varad\.gemini\antigravity-cli\brain\519454df-0cdb-42fc-94bd-b5ee6e8747f1\SAP_Vendor_Intelligence_Architecture_and_Workflow.docx"
    artifact_md = r"C:\Users\Varad\.gemini\antigravity-cli\brain\519454df-0cdb-42fc-94bd-b5ee6e8747f1\SAP_Vendor_Intelligence_Architecture_and_Workflow.md"

    doc.save(downloads_docx)
    doc.save(artifact_docx)

    # Write Markdown file
    md_content = """# 🏗️ System Architecture & Detailed Workflow Specification
## SAP Vendor Intelligence & AP Risk Agent (VIRA) — RAG & AI Pipeline Engine
**Version**: 2.0 | **Domain**: SAP S/4HANA Finance, RAG Vector Search & Accounts Payable AI  

---

## 1. End-to-End System Topology

```mermaid
flowchart TD
    subgraph SAP S/4HANA Core ERP
        BP["Vendor Master (BP / LFBK)"]
        FI["FI Ledger (BKPF / BSEG)"]
        MM["MM Purchasing (EKKO / EKPO / RBKP)"]
        PAY["Payment Engine (F110 / MR11)"]
    end

    subgraph SAP Vendor Intelligence Suite (VIRA)
        INGEST["1. SAP Data & Ingestion Engine"]
        RAG["2. RAG Vector Search & Embeddings Engine (all-MiniLM-L6-v2)"]
        PIPE_A["3. Pre-Payment Risk Pipeline A (UC1, UC2, UC7, UC8)"]
        PIPE_B["4. Post-Payment Audit Pipeline B (UC3, UC4, UC5, UC6)"]
    end

    BP --> INGEST
    MM --> INGEST
    FI --> INGEST

    INGEST --> RAG
    RAG --> PIPE_A
    INGEST --> PIPE_B

    PIPE_A --> Block["SAP Payment Block (BSEG-ZLSPR = 'A')"]
    PIPE_A --> DebitNote["Draft SAP Debit Memos (FB65)"]
    PIPE_B --> Recon["Auto-Clearing & Credit Memos"]
```

---

## 2. End-to-End Workflow Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as AP Auditor / SAP System
    participant API as FastAPI Backend (/api/engine/both)
    participant RAG as RAG Vector Engine (rag_engine.py)
    participant PipeA as Before Payment Pipeline A
    participant PipeB as After Payment Pipeline B
    participant UI as Fiori Horizon UI (http://localhost:8000)

    User->>API: POST /api/engine/both
    API->>PipeA: run_before_pipeline(invoice, all_invoices)
    
    PipeA->>RAG: query_contract_clauses(vendor, "rate card price volume rebate")
    RAG-->>PipeA: Return Vector-Matched Contract Clause Chunk
    
    Note over PipeA: Execute UC1 (Bank Fraud), UC2 (Contract RAG), UC7 (Split Invoice), UC8 (Vendor Health)
    PipeA-->>API: BeforePaymentResult (ARI Score & Payment Block Flag)
    
    API->>PipeB: run_after_pipeline(invoice, all_invoices)
    Note over PipeB: Execute UC3 (Statement Recon), UC4 (Tax Portal), UC5 (GR/IR ML), UC6 (Discount Optimizer)
    PipeB-->>API: AfterPaymentResult (Audit & Yield Recommendations)
    
    API-->>UI: Serve Combined JSON Results & Render Dashboard
```

---

## 3. RAG Vector Search Engine Deep-Dive

* **Vector Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
* **Document Ingestion**: Parses contract files from `data/contracts/*.txt`.
* **Cosine Similarity Retrieval**: Calculates similarity vector score:
  $$\text{Similarity} = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}$$
* **Clause Injection**: Injects matched vector clause directly into the invoice audit output.

---

## 4. 8 Use Cases Summary & Weight Matrix

| UC # | Pipeline | Use Case Name | AI / RAG Engine Component | Weight | SAP Action Trigger |
|---|---|---|---|---|---|
| **UC1** | Pre-Payment (A) | Vendor Bank Change Fraud & BEC Guard | Multimodal PDF check & Payroll Match | 35% | Block Payment (`BSEG-ZLSPR = 'A'`) |
| **UC2** | Pre-Payment (A) | Contract Price & Rebate Detector | RAG Vector Search (`rag_engine.py`) | 30% | Draft SAP Debit Memo (`FB65`) |
| **UC7** | Pre-Payment (A) | Split-Invoice & Evasion Duplicate Audit | Levenshtein Fuzzy & Velocity Clustering | 20% | Flag Split Approval Bypass |
| **UC8** | Pre-Payment (A) | Predictive Vendor Health & Insolvency | OSINT & Vendor Health Index (VHI) | 15% | Advance Payment Hold |
| **UC3** | Post-Payment (B) | Vendor Statement Reconciliation | 4-Way Fuzzy Statement Match Engine | 30% | Unapplied Credit Note Recovery |
| **UC4** | Post-Payment (B) | Real-Time Tax Credit (GST/VAT) Guard | Govt Tax Portal API Sync (GSTR-2B) | 35% | Unverified Tax Amount Block |
| **UC5** | Post-Payment (B) | GR/IR Clearing Root-Cause ML | ML Root Cause Classifier (`MR11`) | 20% | Auto Write-off / PO Adjustment |
| **UC6** | Post-Payment (B) | Early Payment Discount Optimizer | Liquidity Cash Yield Optimizer | 15% | Dynamic Payment Release |
"""

    with open(downloads_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(artifact_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("Architecture files successfully generated!")

if __name__ == "__main__":
    build_architecture_doc()
