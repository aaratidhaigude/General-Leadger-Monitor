"""
SAP Vendor Intelligence Agent (VIRA) — After Payment Pipeline (Pipeline B)
============================================================================
Orchestrator for all post-payment vendor audit & reconciliation checks on Cleared (Z) invoices.

4 Active Steps:
  Step 1: Vendor Statement Reconciliation & Unapplied Credit Recovery (UC3)
  Step 2: Real-Time Tax Credit (GST/VAT) Mismatch & ITC Guard (UC4)
  Step 3: AI GR/IR Clearing Root-Cause Intelligence (UC5)
  Step 4: Dynamic Early Payment Discount & Working Capital Optimizer (UC6)

ARI Tier Thresholds:
  > 70  → HIGH    → Audit Hold / Manual Investigation
  50-70 → MEDIUM  → Review Queue
  < 50  → LOW     → Safe / Reconciled
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Optional

from backend.agent.statement_reconciler import reconcile_vendor_statement, StatementReconResult
from backend.agent.tax_mismatch_guard import check_tax_portal_status, TaxMismatchResult
from backend.agent.grir_intelligence import analyze_grir_item, GRIRIntelligenceResult
from backend.agent.discount_optimizer import optimize_early_payment, DiscountOptimizationResult


# ── Weights for After Payment Pipeline (4 Vendor Validations) ───────────────
AFTER_WEIGHTS = {
    "tax_mismatch_guard":   0.35,   # Highest: Input Tax Credit (ITC) loss is cash loss
    "statement_reconciler": 0.30,   # Statement reconciliation & credit notes
    "grir_intelligence":   0.20,   # GR/IR clearing root cause
    "discount_optimizer":   0.15,   # Early payment yield optimization
}

ARI_HIGH = 70.0
ARI_MEDIUM = 50.0


@dataclass
class AfterPaymentStep:
    step_no: int
    step_name: str
    raw_score: float
    weighted_score: float
    weight: float
    detail: str


@dataclass
class AfterPaymentResult:
    doc_no: str
    invoice_no: str
    vendor: str
    amount_inr: float
    gl_account: str
    doc_type: str
    posting_date: str
    sap_status: str

    # Scores
    ari: float
    tier: str               # HIGH | MEDIUM | LOW
    steps: list[AfterPaymentStep]

    # Sub-results
    recon_result: Optional[StatementReconResult]
    tax_result: Optional[TaxMismatchResult]
    grir_result: Optional[GRIRIntelligenceResult]
    discount_result: Optional[DiscountOptimizationResult]

    # Meta
    audit_ref: str
    alerts: list[str] = field(default_factory=list)


def run_after_pipeline(invoice: dict, all_invoices: list[dict]) -> AfterPaymentResult:
    """
    Runs the complete After Payment Vendor Reconciliation Pipeline (4 Vendor Steps).
    """
    steps: list[AfterPaymentStep] = []
    alerts: list[str] = []

    doc_no = str(invoice.get("doc_no", ""))
    invoice_no = str(invoice.get("invoice_no", ""))
    vendor = str(invoice.get("vendor", ""))
    amount_inr = float(invoice.get("amount_inr", 0))
    gl_account = str(invoice.get("gl_account", "401000"))
    doc_type = str(invoice.get("doc_type", "KR"))
    posting_date = str(invoice.get("posting_date", ""))
    sap_status = str(invoice.get("sap_status", "Z"))

    # ── Step 1: Vendor Statement Reconciliation (UC3) ─────────────────────────
    recon_res = reconcile_vendor_statement(doc_no=doc_no, invoice_no=invoice_no, vendor=vendor, amount_inr=amount_inr)
    w1 = AFTER_WEIGHTS["statement_reconciler"]
    ws1 = recon_res.score * w1

    steps.append(AfterPaymentStep(
        step_no=1,
        step_name="Vendor Statement Reconciliation & Unapplied Credit Recovery (UC3)",
        raw_score=recon_res.score,
        weighted_score=round(ws1, 2),
        weight=w1,
        detail=recon_res.reason
    ))
    if recon_res.missing_credit_note:
        alerts.append(f"📄 Unapplied Credit: {recon_res.reason}")

    # ── Step 2: Real-Time Tax Credit (GST/VAT) Mismatch Guard (UC4) ───────────
    tax_res = check_tax_portal_status(doc_no=doc_no, vendor=vendor, amount_inr=amount_inr)
    w2 = AFTER_WEIGHTS["tax_mismatch_guard"]
    ws2 = tax_res.score * w2

    steps.append(AfterPaymentStep(
        step_no=2,
        step_name="Real-Time Tax Credit (GST/VAT) Mismatch Guard (UC4)",
        raw_score=tax_res.score,
        weighted_score=round(ws2, 2),
        weight=w2,
        detail=tax_res.reason
    ))
    if tax_res.portal_status != "FILED":
        alerts.append(f"⚖️ Tax Portal Risk: {tax_res.reason}")

    # ── Step 3: AI GR/IR Clearing Root Cause Intelligence (UC5) ───────────────
    grir_res = analyze_grir_item(doc_no=doc_no, doc_type=doc_type, vendor=vendor, posting_date=posting_date, amount_inr=amount_inr)
    w3 = AFTER_WEIGHTS["grir_intelligence"]
    ws3 = grir_res.score * w3

    steps.append(AfterPaymentStep(
        step_no=3,
        step_name="AI GR/IR Clearing Root-Cause Intelligence (UC5)",
        raw_score=grir_res.score,
        weighted_score=round(ws3, 2),
        weight=w3,
        detail=f"{grir_res.root_cause_summary} → {grir_res.recommended_action}"
    ))
    if grir_res.variance_type != "BALANCED":
        alerts.append(f"🔍 GR/IR Variance: {grir_res.root_cause_summary}")

    # ── Step 4: Dynamic Early Payment Discount Optimizer (UC6) ────────────────
    disc_res = optimize_early_payment(doc_no=doc_no, amount_inr=amount_inr, vendor=vendor, posting_date=posting_date)
    w4 = AFTER_WEIGHTS["discount_optimizer"]
    ws4 = disc_res.score * w4

    steps.append(AfterPaymentStep(
        step_no=4,
        step_name="Dynamic Early Payment Discount & Working Capital Optimizer (UC6)",
        raw_score=disc_res.score,
        weighted_score=round(ws4, 2),
        weight=w4,
        detail=disc_res.recommendation
    ))
    if disc_res.discount_pct > 0:
        alerts.append(f"💰 Early Pay Savings Opportunity: {disc_res.recommendation}")

    # ── Composite ARI Score ───────────────────────────────────────────────────
    ari = round(ws1 + ws2 + ws3 + ws4, 1)

    # ── Tier ──────────────────────────────────────────────────────────────────
    if ari > ARI_HIGH or tax_res.tax_payment_block:
        tier = "HIGH"
    elif ari >= ARI_MEDIUM:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return AfterPaymentResult(
        doc_no=doc_no,
        invoice_no=invoice_no,
        vendor=vendor,
        amount_inr=amount_inr,
        gl_account=gl_account,
        doc_type=doc_type,
        posting_date=posting_date,
        sap_status=sap_status,
        ari=ari,
        tier=tier,
        steps=steps,
        recon_result=recon_res,
        tax_result=tax_res,
        grir_result=grir_res,
        discount_result=disc_res,
        audit_ref=f"AFT-{uuid.uuid4().hex[:10].upper()}",
        alerts=alerts,
    )
