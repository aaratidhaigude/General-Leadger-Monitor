"""
GL Monitor — Fuzzy Duplicate Invoice Detector
==============================================
Detects near-identical duplicate invoices that SAP's standard BSIP check misses.
Uses Levenshtein distance on normalized invoice numbers to catch variants like:
  INV-98412  vs  INV 98412  vs  INV/98412  vs  INV98412A
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
from Levenshtein import distance as levenshtein_distance


@dataclass
class DuplicateCheckResult:
    is_duplicate: bool
    duplicate_type: str          # EXACT | NEAR | FUZZY | CLEAN
    matched_doc_no: str
    matched_invoice_no: str
    matched_vendor: str
    levenshtein_distance: int
    confidence_pct: float        # 0-100%
    score: float                 # 0-100 ARI sub-score
    reason: str


def normalize_invoice_number(invoice_no: str) -> str:
    """
    Strips all separators (spaces, dashes, slashes, dots) and lowercases.
    'INV-98412' -> 'inv98412'
    'INV/98412/23-24' -> 'inv9841223-24' -> 'inv984122324'
    """
    normalized = invoice_no.lower()
    normalized = re.sub(r'[\s\-/\\.]+', '', normalized)
    return normalized


def check_fuzzy_duplicate(
    new_doc_no: str,
    new_invoice_no: str,
    new_vendor: str,
    new_amount: float,
    existing_invoices: list[dict]
) -> DuplicateCheckResult:
    """
    Checks the new invoice against all existing posted invoices.

    Args:
        new_doc_no: SAP Document Number of the new invoice
        new_invoice_no: Raw invoice number string from vendor
        new_vendor: Vendor name
        new_amount: Invoice amount in INR
        existing_invoices: List of already-posted invoice dicts with keys:
                          doc_no, invoice_no, vendor, amount_inr

    Returns:
        DuplicateCheckResult with risk score and match details
    """
    norm_new = normalize_invoice_number(new_invoice_no)

    best_match: Optional[dict] = None
    best_distance: int = 999
    best_norm_existing: str = ""

    for inv in existing_invoices:
        # Skip self-comparison
        if inv.get("doc_no") == new_doc_no:
            continue

        # Only compare same vendor (same vendor code or same vendor name)
        if inv.get("vendor", "").lower() != new_vendor.lower():
            continue

        # Only compare similar amounts (within ±10%)
        existing_amount = float(inv.get("amount_inr", 0))
        if existing_amount > 0:
            amount_diff_pct = abs(new_amount - existing_amount) / existing_amount
            if amount_diff_pct > 0.10:
                continue

        norm_existing = normalize_invoice_number(str(inv.get("invoice_no", "")))
        dist = levenshtein_distance(norm_new, norm_existing)

        if dist < best_distance:
            best_distance = dist
            best_match = inv
            best_norm_existing = norm_existing

    if best_match is None or best_distance > 5:
        return DuplicateCheckResult(
            is_duplicate=False,
            duplicate_type="CLEAN",
            matched_doc_no="",
            matched_invoice_no="",
            matched_vendor="",
            levenshtein_distance=best_distance if best_match else -1,
            confidence_pct=0.0,
            score=0.0,
            reason="No duplicate found."
        )

    # Calculate confidence: lower distance = higher confidence
    max_len = max(len(norm_new), len(best_norm_existing), 1)
    similarity = 1.0 - (best_distance / max_len)
    confidence_pct = round(similarity * 100, 1)

    if best_distance == 0:
        dup_type = "EXACT"
        score = 100.0
        reason = f"Exact duplicate of Doc {best_match['doc_no']} (Invoice: {best_match['invoice_no']}). Normalized both to '{norm_new}'."
    elif best_distance <= 2:
        dup_type = "NEAR"
        score = 85.0
        reason = (f"Near-duplicate of Doc {best_match['doc_no']} (Invoice: {best_match['invoice_no']}). "
                  f"Edit distance={best_distance}, confidence={confidence_pct}%.")
    else:
        dup_type = "FUZZY"
        score = 60.0
        reason = (f"Fuzzy match with Doc {best_match['doc_no']} (Invoice: {best_match['invoice_no']}). "
                  f"Edit distance={best_distance}, confidence={confidence_pct}%.")

    return DuplicateCheckResult(
        is_duplicate=True,
        duplicate_type=dup_type,
        matched_doc_no=str(best_match.get("doc_no", "")),
        matched_invoice_no=str(best_match.get("invoice_no", "")),
        matched_vendor=str(best_match.get("vendor", "")),
        levenshtein_distance=best_distance,
        confidence_pct=confidence_pct,
        score=score,
        reason=reason
    )
