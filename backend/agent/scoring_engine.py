"""
UC14 GL Anomaly Detection Agent — Scoring Engine
======================================================
Calculates real-time Anomaly Risk Index (ARI, 0-100) and executes business rules.
"""
from __future__ import annotations
import os, sys, uuid
from dataclasses import dataclass, field
from typing import Optional

from backend.config.settings import (
    ARI_WEIGHTS, ZSCORE_BANDS, MATERIALITY_BANDS,
    OFF_HOURS_SCORE, BUSINESS_HOURS_SCORE, BUSINESS_HOURS_START, BUSINESS_HOURS_END,
    VALID_COMBINATION_SCORE, INVALID_COMBINATION_SCORE,
    IC_BALANCED_SCORE, IC_UNBALANCED_SCORE, IC_NOT_APPLICABLE_SCORE,
    ARI_LOW_MAX, ARI_MEDIUM_MAX, MATERIALITY_HARD_LIMIT_INR,
)
from backend.agent.data_loader import GLPosting, HistoricalBaseline, BankStatementEntry


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
    bank_matched: Optional[bool]  # None if no UTR reference
    mean_amount: float = 0.0
    std_dev_amount: float = 0.0


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
    ari: float
    ari_breakdown: ARIBreakdown
    action: str                    # AUTO_RECONCILE | DAILY_REPORT | INVESTIGATE
    justification: str
    recommended_action: str
    sap_action: str
    audit_trail_ref: str
    hard_override: bool
    status: str = "POSTED"           # POSTED | UNDER_PROCESS | FAILED | RETRY_SUCCESS
    attempt_number: int = 1
    failure_reason: str = ""
    retry_linked_doc: str = ""
    process_stage: str = ""
    alerts: list[str] = field(default_factory=list)


class ScoringEngine:
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

        mean_val = baseline.mean_amount if baseline else 0.0
        std_val = baseline.std_dev_amount if baseline else 0.0

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
            alerts.append("Unknown GL account + document type combination.")
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
            mean_amount=mean_val, std_dev_amount=std_val
        )

        hard_override = False
        if posting.status == "FAILED":
            action = "INVESTIGATE"
            hard_override = True
            justification = f"Transaction Attempt {posting.attempt_number} FAILED: {posting.failure_reason}."
            recommended_action = f"Verify SAP SM21 log for retry Doc #{posting.retry_linked_doc}."
            sap_action = f"Audit hold placed on retry Doc #{posting.retry_linked_doc}."
            alerts.append(f"Failed Attempt: {posting.failure_reason}")
        elif posting.status == "UNDER_PROCESS":
            action = "DAILY_REPORT"
            justification = f"Transaction Under Process: {posting.process_stage}."
            recommended_action = "Monitor dual-control signoff (FBV0) or bank settlement."
            sap_action = "Document Parked in SAP (FBV0) or In-Flight."
            alerts.append(f"In-Flight Stage: {posting.process_stage}")
        elif posting.status == "RETRY_SUCCESS":
            alerts.append(f"Retry Attempt 2 succeeded after prior failure on Doc #{posting.retry_linked_doc}.")
            if ari < ARI_LOW_MAX:
                action = "DAILY_REPORT"
                justification = f"Retry Succeeded (Attempt 2) linked to failed Doc #{posting.retry_linked_doc}."
                recommended_action = f"Verify bank reversal for failed attempt Doc #{posting.retry_linked_doc}."
                sap_action = "Reconciled with retry tag."
            elif ari < ARI_MEDIUM_MAX:
                action = "DAILY_REPORT"
                justification = f"Retry Succeeded linked to Doc #{posting.retry_linked_doc}."
                recommended_action = "Include in daily review digest."
                sap_action = "Read via BKPF/BSEG."
            else:
                action = "INVESTIGATE"
                justification = f"Retry Succeeded linked to Doc #{posting.retry_linked_doc} with high ARI {ari:.1f}."
                recommended_action = "Immediate review for failure and high risk."
                sap_action = "SAP Workflow Alert triggered."
        elif posting.duplicate_flag:
            action = "INVESTIGATE"
            hard_override = True
            justification = "Duplicate posting detected - frozen pending manual release."
            recommended_action = "Freeze posting and alert Finance Manager."
            sap_action = "Posting flagged for hold via SAP Workflow Alert."
        elif posting.amount_inr > MATERIALITY_HARD_LIMIT_INR:
            action = "INVESTIGATE"
            hard_override = True
            justification = f"Posting amount Rs.{posting.amount_inr:,.0f} exceeds Rs.1 crore materiality threshold."
            recommended_action = "Immediate Finance Manager alert."
            sap_action = "SAP Workflow Alert triggered - Finance Manager notified."
        elif ari < ARI_LOW_MAX:
            action = "AUTO_RECONCILE"
            bank_note = "bank match confirmed" if bank_matched else ("no bank reference" if posting.utr_reference == "" else "bank match pending")
            justification = f"ARI {ari:.1f} - amount within normal range, business-hours ({bank_note})."
            recommended_action = "Confirm bank match and mark reconciled."
            sap_action = "Matched against FEBEP bank statement - reconciled."
        elif ari < ARI_MEDIUM_MAX:
            action = "DAILY_REPORT"
            justification = f"ARI {ari:.1f} - minor deviation from normal pattern."
            recommended_action = "Included in 7am exception report to AP/AR team."
            sap_action = "Read via BKPF/BSEG - included in daily report."
        else:
            action = "INVESTIGATE"
            justification = f"ARI {ari:.1f} - significant deviation across multiple factors."
            recommended_action = "Immediate Finance Manager alert."
            sap_action = "SAP Workflow Alert triggered."

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
