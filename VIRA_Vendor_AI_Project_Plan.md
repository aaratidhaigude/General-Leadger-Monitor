# VIRA — Project Plan
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
