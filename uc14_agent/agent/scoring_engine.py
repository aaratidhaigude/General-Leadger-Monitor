"""
UC14 GL Anomaly Detection Agent — Scoring Engine
======================================================
ARI Weights:
  Amount Z-score vs Historical Baseline   35%
  Posting Time (off-hours flag)           25%
  Account Combination Validity            20%
  Materiality (INR amount)                15%
  Inter-Company Balance Check              5%

Decision — explicit business rules drive the action; ARI is the
explainability score shown alongside:

  ARI LOW (< 25)                    → AUTO-RECONCILE
  ARI MEDIUM (25-60)                → DAILY REPORT
  ARI HIGH (> 60) OR amount > 1 Cr  → INVESTIGATE

Hard overrides (force INVESTIGATE regardless of composite ARI):
  Posting amount exceeds ₹1 crore
  Duplicate posting detected

Compatible: SAP BTP Python Runtime · VS Code · SAP BAS
"""
from __future__ import annotations
import os, sys
import uuid
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.settings import (
    ARI_WEIGHTS, ZSCORE_BANDS, MATERIALITY_BANDS,
    OFF_HOURS_SCORE, BUSINESS_HOURS_SCORE, BUSINESS_HOURS_START, BUSINESS_HOURS_END,
    VALID_COMBINATION_SCORE, INVALID_COMBINATION_SCORE,
    IC_BALANCED_SCORE, IC_UNBALANCED_SCORE, IC_NOT_APPLICABLE_SCORE,
    ARI_LOW_MAX, ARI_MEDIUM_MAX, MATERIALITY_HARD_LIMIT_INR,
)
from agent.data_loader import GLPosting, HistoricalBaseline, BankStatementEntry


@dataclass
class ARIBreakdown:
    zscore_score: float
    posting_time_score: float
    account_combination_score: float
    materiality_score: float
    ic_balance_score: float
    ari: float                    # Composite 0-100, higher = more anomalous
    z_score: float
    off_hours: bool
    bank_matched: Optional[bool]  # None if no UTR reference on this posting at all


@dataclass
class GLAnomalyDecision:
    doc_no: str
    line_item: str
    gl_account: str
    doc_type: str
    company_code: str
    posting_date: str
    posting_time: str
    amount_inr: float
    is_intercompany: bool
    ic_partner_company: str
    duplicate_flag: bool
    # Scoring
    ari: float
    ari_breakdown: ARIBreakdown
    # Decision
    action: str                    # AUTO_RECONCILE | DAILY_REPORT | INVESTIGATE
    justification: str
    recommended_action: str
    # SAP actions
    sap_action: str
    audit_trail_ref: str
    # Flags
    hard_override: bool
    status: str = "POSTED"           # POSTED | UNDER_PROCESS | FAILED | RETRY_SUCCESS
    attempt_number: int = 1
    failure_reason: str = ""
    retry_linked_doc: str = ""
    process_stage: str = ""
    alerts: list[str] = field(default_factory=list)


class ScoringEngine:
    """ARI scoring engine for UC14 GL anomaly decisions."""

    def __init__(self):
        assert abs(sum(ARI_WEIGHTS.values()) - 1.0) < 1e-6, "ARI_WEIGHTS must sum to 1.0"

    @staticmethod
    def _band_score(value: float, bands: list) -> float:
        for threshold, score in bands:
            if value >= threshold:
                return float(score)
        return float(bands[-1][1])

    @staticmethod
    def _is_off_hours(posting_time: str) -> bool:
        try:
            hour = int(posting_time.split(":")[0])
        except (ValueError, IndexError):
            return False
        return hour < BUSINESS_HOURS_START or hour >= BUSINESS_HOURS_END

    def score_posting(self, posting: GLPosting, baseline: Optional[HistoricalBaseline],
                       bank_entry: Optional[BankStatementEntry]) -> GLAnomalyDecision:
        alerts: list[str] = []

        if baseline and baseline.std_dev_amount > 0:
            z = round((posting.amount_inr - baseline.mean_amount) / baseline.std_dev_amount, 2)
        else:
            z = 0.0
            alerts.append("No historical baseline found for this GL account + document type combination.")
        zscore_score = self._band_score(abs(z), ZSCORE_BANDS)

        off_hours = self._is_off_hours(posting.posting_time)
        posting_time_score = OFF_HOURS_SCORE if off_hours else BUSINESS_HOURS_SCORE

        if baseline is None:
            combination_score = INVALID_COMBINATION_SCORE
            alerts.append("Unknown GL account + document type combination - not in the baseline reference.")
        else:
            combination_score = VALID_COMBINATION_SCORE if baseline.valid_combination else INVALID_COMBINATION_SCORE

        materiality_score = self._band_score(posting.amount_inr, MATERIALITY_BANDS)

        if not posting.is_intercompany:
            ic_score = IC_NOT_APPLICABLE_SCORE
        elif abs(posting.amount_inr - posting.ic_partner_amount) <= max(1.0, 0.005 * posting.amount_inr):
            ic_score = IC_BALANCED_SCORE
        else:
            ic_score = IC_UNBALANCED_SCORE
            alerts.append(f"Inter-company posting does not balance against partner company {posting.ic_partner_company}.")

        ari = round(
            zscore_score * ARI_WEIGHTS["amount_zscore"]
            + posting_time_score * ARI_WEIGHTS["posting_time"]
            + combination_score * ARI_WEIGHTS["account_combination"]
            + materiality_score * ARI_WEIGHTS["materiality"]
            + ic_score * ARI_WEIGHTS["ic_balance"], 1
        )

        bank_matched: Optional[bool] = None
        if posting.utr_reference:
            if bank_entry is None:
                bank_matched = False
                alerts.append(f"No bank statement entry found for UTR {posting.utr_reference}.")
            else:
                bank_matched = abs(bank_entry.bank_amount - posting.amount_inr) <= 1.0

        breakdown = ARIBreakdown(
            zscore_score=zscore_score, posting_time_score=posting_time_score,
            account_combination_score=combination_score, materiality_score=materiality_score,
            ic_balance_score=ic_score, ari=ari, z_score=z, off_hours=off_hours, bank_matched=bank_matched,
        )

        hard_override = False
        if posting.status == "FAILED":
            action = "INVESTIGATE"
            hard_override = True
            justification = f"Transaction Attempt {posting.attempt_number} FAILED: {posting.failure_reason}. Check bank reversal before clearing linked retry Doc #{posting.retry_linked_doc}."
            recommended_action = f"Verify SAP SM21/FEBAN log and ensure no double debit occurred for retry Doc #{posting.retry_linked_doc}."
            sap_action = f"Failed entry logged via SM13/FEBAN — audit hold placed on retry Doc #{posting.retry_linked_doc}."
            alerts.append(f"Failed Attempt: {posting.failure_reason}")
        elif posting.status == "UNDER_PROCESS":
            action = "DAILY_REPORT"
            justification = f"Transaction Under Process: {posting.process_stage}. Monitored in real-time until final settlement."
            recommended_action = "Monitor dual-control signoff (FBV0) or bank clearing transit completion."
            sap_action = "Document Parked in SAP (FBV0) or In-Flight with Bank — pending completion."
            alerts.append(f"In-Flight Stage: {posting.process_stage}")
        elif posting.status == "RETRY_SUCCESS":
            alerts.append(f"Retry Attempt 2 succeeded after prior failure on Doc #{posting.retry_linked_doc}. Verify reversal.")
            if ari < ARI_LOW_MAX:
                action = "DAILY_REPORT"
                justification = f"Retry Succeeded (Attempt 2) linked to failed Doc #{posting.retry_linked_doc}. Flagged for reconciliation verification to prevent double payment."
                recommended_action = f"Verify bank reversal for failed attempt Doc #{posting.retry_linked_doc} before final settlement."
                sap_action = "Reconciled with retry tag — verified against failed attempt log."
            elif ari < ARI_MEDIUM_MAX:
                action = "DAILY_REPORT"
                justification = f"Retry Succeeded (Attempt 2) linked to Doc #{posting.retry_linked_doc}. Moderate baseline variance."
                recommended_action = "Include in daily review digest; verify Attempt 1 reversal."
                sap_action = "Read via BKPF/BSEG — retry audit trail logged."
            else:
                action = "INVESTIGATE"
                justification = f"Retry Succeeded (Attempt 2) linked to Doc #{posting.retry_linked_doc}, with high composite ARI {ari:.1f}."
                recommended_action = "Immediate review for both attempt failure and high anomaly risk."
                sap_action = "SAP Workflow Alert triggered — Controller notification sent."
        elif posting.duplicate_flag:
            action = "INVESTIGATE"
            hard_override = True
            justification = "Duplicate posting detected - frozen pending manual release, regardless of the composite risk score."
            recommended_action = "Freeze the posting and alert the Finance Manager immediately to confirm before release."
            sap_action = "Posting flagged for hold via SAP Workflow Alert - no auto-release."
        elif posting.amount_inr > MATERIALITY_HARD_LIMIT_INR:
            action = "INVESTIGATE"
            hard_override = True
            justification = f"Posting amount Rs.{posting.amount_inr:,.0f} exceeds the Rs.1 crore materiality threshold - escalated regardless of the composite risk score."
            recommended_action = "Immediate Finance Manager alert."
            sap_action = "SAP Workflow Alert triggered - Finance Manager notified immediately."
        elif ari < ARI_LOW_MAX:
            action = "AUTO_RECONCILE"
            bank_note = "bank match confirmed" if bank_matched else ("no bank reference on this posting" if posting.utr_reference == "" else "bank match pending")
            justification = f"ARI {ari:.1f} - amount within normal range for this GL account, business-hours posting, valid combination ({bank_note})."
            recommended_action = "Confirm bank match and mark reconciled on the period-end dashboard."
            sap_action = "Matched against FEBEP bank statement line item - reconciled, no manual action needed."
        elif ari < ARI_MEDIUM_MAX:
            action = "DAILY_REPORT"
            justification = f"ARI {ari:.1f} - some deviation from the normal pattern, not severe enough for immediate escalation."
            recommended_action = "Included in the 7am exception report to the AP/AR team; same-day review SLA."
            sap_action = "Read via BKPF/BSEG - included in daily exception report, no automated write."
        else:
            action = "INVESTIGATE"
            justification = f"ARI {ari:.1f} - significant deviation across multiple factors (amount, timing, account combination)."
            recommended_action = "Immediate Finance Manager alert for review."
            sap_action = "SAP Workflow Alert triggered - Finance Manager notified immediately."

        audit_ref = f"ARI-{uuid.uuid4().hex[:10].upper()}"

        return GLAnomalyDecision(
            doc_no=posting.doc_no, line_item=posting.line_item, gl_account=posting.gl_account,
            doc_type=posting.doc_type, company_code=posting.company_code, posting_date=posting.posting_date,
            posting_time=posting.posting_time, amount_inr=posting.amount_inr,
            is_intercompany=posting.is_intercompany, ic_partner_company=posting.ic_partner_company,
            duplicate_flag=posting.duplicate_flag, ari=ari, ari_breakdown=breakdown,
            action=action, justification=justification, recommended_action=recommended_action,
            sap_action=sap_action, audit_trail_ref=audit_ref,
            hard_override=hard_override, status=posting.status, attempt_number=posting.attempt_number,
            failure_reason=posting.failure_reason, retry_linked_doc=posting.retry_linked_doc,
            process_stage=posting.process_stage, alerts=alerts,
        )
