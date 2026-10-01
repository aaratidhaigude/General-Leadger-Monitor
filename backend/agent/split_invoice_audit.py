"""
UC7: Split-Invoice & Evasion Duplicate Posting Audit
=====================================================
Uses fuzzy text matching (Levenshtein/N-gram) and velocity clustering to detect split-billing evasion.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class SplitInvoiceResult:
    is_split_detected: bool
    fuzzy_duplicate_detected: bool
    matched_doc_no: str
    similarity_pct: float
    score: float             # 0-100 (higher = high evasion risk)
    reason: str

def levenshtein_ratio(s1: str, s2: str) -> float:
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    len1, len2 = len(s1), len(s2)
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost
            )
    dist = dp[len1][len2]
    return 1.0 - (dist / max(len1, len2))

def check_split_invoice(
    doc_no: str,
    invoice_no: str,
    vendor: str,
    amount_inr: float,
    all_invoices: list[dict],
    approval_threshold_inr: float = 500_000
) -> SplitInvoiceResult:
    # 1. Fuzzy Duplicate check
    fuzzy_dup = False
    matched_doc = ""
    max_sim = 0.0

    for inv in all_invoices:
        if str(inv.get("doc_no")) == doc_no:
            continue
        if str(inv.get("vendor", "")).lower() == vendor.lower():
            other_inv_no = str(inv.get("invoice_no", ""))
            sim = levenshtein_ratio(invoice_no, other_inv_no)
            if sim > max_sim:
                max_sim = sim
                matched_doc = str(inv.get("doc_no"))
            if sim > 0.85 and abs(float(inv.get("amount_inr", 0)) - amount_inr) < 1.0:
                fuzzy_dup = True

    # 2. Split-billing velocity check (multiple invoices just under approval threshold)
    same_vendor_recent = [
        inv for inv in all_invoices
        if str(inv.get("vendor", "")).lower() == vendor.lower()
        and str(inv.get("doc_no")) != doc_no
        and 0.7 * approval_threshold_inr <= float(inv.get("amount_inr", 0)) < approval_threshold_inr
    ]

    is_split = (amount_inr < approval_threshold_inr) and (len(same_vendor_recent) >= 2)

    if fuzzy_dup:
        score = 95.0
        reason = f"Fuzzy Duplicate Invoice detected! Invoice '{invoice_no}' matches Doc #{matched_doc} ({max_sim*100:.0f}% similarity)."
    elif is_split:
        score = 80.0
        reason = f"Split-Billing Evasion suspect: {len(same_vendor_recent)+1} invoices under ₹5L threshold for {vendor}."
    else:
        score = 5.0
        reason = "Clean transaction — no split-billing pattern or fuzzy duplicate detected."

    return SplitInvoiceResult(
        is_split_detected=is_split,
        fuzzy_duplicate_detected=fuzzy_dup,
        matched_doc_no=matched_doc,
        similarity_pct=round(max_sim * 100, 1),
        score=score,
        reason=reason
    )
