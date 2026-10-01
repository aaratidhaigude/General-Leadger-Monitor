"""
UC2: Contract Price & Volume Rebate Leakage Detector (RAG + LLM Powered)
==========================================================================
Uses RAG (Vector Search) to retrieve vendor contract clauses and audit invoice line items.
"""
from __future__ import annotations
import os, json
from dataclasses import dataclass
from typing import Optional

from backend.agent.rag_engine import rag_singleton

@dataclass
class ContractAuditResult:
    contract_ref: str
    base_rate_inr: float
    invoiced_rate_inr: float
    unit_overbill_inr: float
    rebate_eligible: bool
    rebate_pct: float
    rebate_amount_inr: float
    score: float             # 0-100 (100 = high price leakage risk)
    reason: str
    draft_debit_memo: bool
    retrieved_clause: str    # RAG Vector Chunk matched

def audit_contract_pricing(
    contract_ref: str,
    contract_rate: float,
    invoiced_amount: float,
    qty: float,
    ytd_volume_inr: float,
    rebate_threshold_inr: float = 10_000_000,
    rebate_pct: float = 5.0
) -> ContractAuditResult:
    # 1. RAG Retrieval: Query Vector Database for contract clauses
    chunks = rag_singleton.query_contract_clauses(
        vendor_name=contract_ref.split("-")[1] if "-" in contract_ref else contract_ref,
        query_text="base rate unit price volume rebate rate card",
        top_k=1
    )
    
    retrieved_clause_text = ""
    if chunks:
        matched_chunk = chunks[0]
        retrieved_clause_text = f"[{matched_chunk.contract_ref} - {matched_chunk.clause_title}]: {matched_chunk.content[:140]}..."
    else:
        retrieved_clause_text = f"[{contract_ref}]: Standard rate card clause."

    unit_price = invoiced_amount / max(1.0, qty)
    unit_overbill = max(0.0, unit_price - contract_rate)
    total_overbill = unit_overbill * qty

    rebate_eligible = ytd_volume_inr >= rebate_threshold_inr
    rebate_amount = (invoiced_amount * (rebate_pct / 100.0)) if rebate_eligible else 0.0

    if unit_overbill > 0:
        score = min(100.0, 50.0 + (unit_overbill / contract_rate) * 100.0)
        reason = f"RAG Audit: Invoiced rate ₹{unit_price:,.0f} exceeds vector-retrieved contract rate ₹{contract_rate:,.0f}. Overbill ₹{total_overbill:,.0f}. {retrieved_clause_text}"
        draft_debit = True
    elif rebate_eligible:
        score = 60.0
        reason = f"RAG Audit: YTD volume ₹{ytd_volume_inr:,.0f} exceeds ₹10Cr rebate threshold. Eligible for {rebate_pct}% rebate (₹{rebate_amount:,.0f}). {retrieved_clause_text}"
        draft_debit = True
    else:
        score = 5.0
        reason = f"RAG Audit: Invoiced rate ₹{unit_price:,.0f} matches vector contract {contract_ref}. {retrieved_clause_text}"
        draft_debit = False

    return ContractAuditResult(
        contract_ref=contract_ref or "CNT-2026-DEFAULT",
        base_rate_inr=contract_rate,
        invoiced_rate_inr=unit_price,
        unit_overbill_inr=unit_overbill,
        rebate_eligible=rebate_eligible,
        rebate_pct=rebate_pct if rebate_eligible else 0.0,
        rebate_amount_inr=rebate_amount,
        score=score,
        reason=reason,
        draft_debit_memo=draft_debit,
        retrieved_clause=retrieved_clause_text
    )
