"""
SAP Vendor Intelligence Agent (VIRA) — Before Payment Pipeline (Pipeline A)
=============================================================================
Orchestrator for all pre-payment vendor risk checks on Parked (V) and Posted (A) invoices.

4 Active Steps:
  Step 1: Vendor Bank Account Change Fraud & BEC Guard (UC1)
  Step 2: AI Contract Price & Volume Rebate Leakage Detector (UC2)
  Step 3: Split-Invoice & Evasion Duplicate Posting Audit (UC7)
  Step 4: Predictive Vendor Health & Insolvency Risk Monitor (UC8)

ARI Tier Thresholds:
  > 70  → HIGH    → Auto Payment Block (BSEG-ZLSPR = 'A')
  50-70 → MEDIUM  → Review Queue
  < 50  → LOW     → Safe / Clear
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Optional

from backend.agent.vendor_bank_guard import check_vendor_bank_change, VendorBankGuardResult
from backend.agent.contract_auditor import audit_contract_pricing, ContractAuditResult
from backend.agent.split_invoice_audit import check_split_invoice, SplitInvoiceResult
from backend.agent.vendor_health_monitor import evaluate_vendor_health, VendorHealthResult


# ── Weights for Before Payment Pipeline (4 Vendor Validations) ──────────────
BEFORE_WEIGHTS = {
    "bank_change_guard":    0.35,   # Highest: Bank fraud is most serious
    "contract_auditor":      0.30,   # Contract overbilling & rebate leakage
    "split_invoice_audit":  0.20,   # Evasion & fuzzy duplicate check
    "vendor_health_monitor": 0.15,   # Insolvency & credit risk
}

ARI_HIGH = 70.0
ARI_MEDIUM = 50.0


@dataclass
class BeforePaymentStep:
    step_no: int
    step_name: str
    raw_score: float        # 0-100
    weighted_score: float   # raw_score * weight
    weight: float
    detail: str


@dataclass
class BeforePaymentResult:
    doc_no: str
    invoice_no: str
    vendor: str
    vendor_code: str
    amount_inr: float
    gl_account: str
    doc_type: str
    posting_date: str
    posting_time: str
    sap_status: str

    # Scores
    ari: float
    tier: str               # HIGH | MEDIUM | LOW
    steps: list[BeforePaymentStep]

    # Hard overrides
    hard_override: bool
    payment_block_applied: bool   # BSEG-ZLSPR = 'A'
    override_reason: str

    # Sub-results
    bank_guard_result: Optional[VendorBankGuardResult]
    contract_result: Optional[ContractAuditResult]
    split_result: Optional[SplitInvoiceResult]
    health_result: Optional[VendorHealthResult]

    # Meta
    audit_ref: str
    alerts: list[str] = field(default_factory=list)


def run_before_pipeline(invoice: dict, all_invoices: list[dict]) -> BeforePaymentResult:
    """
    Runs the complete Before Payment Vendor Risk Assessment Pipeline (4 Vendor Steps).
    """
    steps: list[BeforePaymentStep] = []
    alerts: list[str] = []

    doc_no = str(invoice.get("doc_no", ""))
    invoice_no = str(invoice.get("invoice_no", ""))
    vendor = str(invoice.get("vendor", ""))
    vendor_code = str(invoice.get("vendor_code", ""))
    amount_inr = float(invoice.get("amount_inr", 0))
    gl_account = str(invoice.get("gl_account", "401000"))
    doc_type = str(invoice.get("doc_type", "KR"))
    posting_date = str(invoice.get("posting_date", ""))
    posting_time = str(invoice.get("posting_time", "09:00"))
    sap_status = str(invoice.get("sap_status", "A"))
    contract_ref = str(invoice.get("contract_ref", "CNT-2026-001"))
    contract_rate = float(invoice.get("contract_rate_inr", amount_inr / max(1.0, float(invoice.get("qty", 10)))))
    qty = float(invoice.get("qty", 10))
    ytd_volume = float(invoice.get("ytd_volume_inr", amount_inr * 12))

    # ── Step 1: Vendor Bank Guard (UC1) ───────────────────────────────────────
    bank_guard = check_vendor_bank_change(vendor_code=vendor_code, vendor_name=vendor)
    w1 = BEFORE_WEIGHTS["bank_change_guard"]
    ws1 = bank_guard.score * w1

    steps.append(BeforePaymentStep(
        step_no=1,
        step_name="Vendor Bank Account Change Fraud & BEC Guard (UC1)",
        raw_score=bank_guard.score,
        weighted_score=round(ws1, 2),
        weight=w1,
        detail=bank_guard.reason
    ))
    if bank_guard.has_recent_change:
        alerts.append(f"⚠️ Bank Guard: {bank_guard.reason}")

    # ── Step 2: Contract Price & Volume Rebate Auditor (UC2) ──────────────────
    contract_res = audit_contract_pricing(
        contract_ref=contract_ref,
        contract_rate=contract_rate,
        invoiced_amount=amount_inr,
        qty=qty,
        ytd_volume_inr=ytd_volume
    )
    w2 = BEFORE_WEIGHTS["contract_auditor"]
    ws2 = contract_res.score * w2

    steps.append(BeforePaymentStep(
        step_no=2,
        step_name="AI Contract Price & Volume Rebate Leakage Detector (UC2)",
        raw_score=contract_res.score,
        weighted_score=round(ws2, 2),
        weight=w2,
        detail=contract_res.reason
    ))
    if contract_res.draft_debit_memo:
        alerts.append(f"📜 Contract Leakage: {contract_res.reason}")

    # ── Step 3: Split-Invoice & Evasion Duplicate Audit (UC7) ─────────────────
    split_res = check_split_invoice(
        doc_no=doc_no,
        invoice_no=invoice_no,
        vendor=vendor,
        amount_inr=amount_inr,
        all_invoices=all_invoices
    )
    w3 = BEFORE_WEIGHTS["split_invoice_audit"]
    ws3 = split_res.score * w3

    steps.append(BeforePaymentStep(
        step_no=3,
        step_name="Split-Invoice & Evasion Duplicate Posting Audit (UC7)",
        raw_score=split_res.score,
        weighted_score=round(ws3, 2),
        weight=w3,
        detail=split_res.reason
    ))
    if split_res.fuzzy_duplicate_detected or split_res.is_split_detected:
        alerts.append(f"🔴 Evasion Audit: {split_res.reason}")

    # ── Step 4: Predictive Vendor Health & Insolvency Risk Monitor (UC8) ──────
    health_res = evaluate_vendor_health(vendor=vendor, vendor_code=vendor_code, amount_inr=amount_inr)
    w4 = BEFORE_WEIGHTS["vendor_health_monitor"]
    ws4 = health_res.score * w4

    steps.append(BeforePaymentStep(
        step_no=4,
        step_name="Predictive Vendor Health & Insolvency Risk Monitor (UC8)",
        raw_score=health_res.score,
        weighted_score=round(ws4, 2),
        weight=w4,
        detail=health_res.reason
    ))
    if health_res.insolvency_risk_level == "HIGH":
        alerts.append(f"🚨 Vendor Health Alert: {health_res.reason}")

    # ── Composite ARI Score ───────────────────────────────────────────────────
    ari = round(ws1 + ws2 + ws3 + ws4, 1)

    # ── Hard Overrides ────────────────────────────────────────────────────────
    hard_override = False
    payment_block = False
    override_reason = ""

    if bank_guard.risk_level == "HIGH":
        hard_override = True
        payment_block = True
        ari = max(ari, 90.0)
        override_reason = f"Vendor bank changed {bank_guard.days_since_change} days ago. SAP Payment Block 'A' applied to BSEG-ZLSPR."
        alerts.append(f"🚨 HARD BLOCK: {override_reason}")

    if split_res.fuzzy_duplicate_detected:
        hard_override = True
        payment_block = True
        ari = 100.0
        override_reason = f"Fuzzy duplicate invoice detected. SAP Payment Block 'A' applied."

    if health_res.advance_payment_block:
        hard_override = True
        payment_block = True
        ari = max(ari, 85.0)
        if not override_reason:
            override_reason = f"Vendor '{vendor}' shows severe insolvency risk. Advance payment blocked."

    # ── Risk Tier Determination ───────────────────────────────────────────────
    if ari > ARI_HIGH or hard_override:
        tier = "HIGH"
    elif ari >= ARI_MEDIUM:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    return BeforePaymentResult(
        doc_no=doc_no,
        invoice_no=invoice_no,
        vendor=vendor,
        vendor_code=vendor_code,
        amount_inr=amount_inr,
        gl_account=gl_account,
        doc_type=doc_type,
        posting_date=posting_date,
        posting_time=posting_time,
        sap_status=sap_status,
        ari=ari,
        tier=tier,
        steps=steps,
        hard_override=hard_override,
        payment_block_applied=payment_block,
        override_reason=override_reason,
        bank_guard_result=bank_guard,
        contract_result=contract_res,
        split_result=split_res,
        health_result=health_res,
        audit_ref=f"BEF-{uuid.uuid4().hex[:10].upper()}",
        alerts=alerts,
    )
