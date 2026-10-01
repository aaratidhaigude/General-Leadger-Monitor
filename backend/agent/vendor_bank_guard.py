"""
GL Monitor — Vendor Bank Detail Change Guard (LFBK Audit)
==========================================================
Detects if a vendor's bank account details (SAP table LFBK / Business Partner)
were recently modified. Cross-references against upcoming invoices & payment runs.

Risk Logic:
  < 7 days since change  → Score 100 → HIGH → Auto Payment Block
  7-30 days since change → Score 70  → MEDIUM → Goes to Review Queue
  > 30 days since change → Score 0   → Clean
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class VendorBankGuardResult:
    has_recent_change: bool
    days_since_change: int
    change_date: str
    changed_by: str
    old_bank_account: str
    new_bank_account: str
    old_bank_key: str
    new_bank_key: str
    score: float            # 0-100 ARI sub-score
    risk_level: str         # HIGH | MEDIUM | CLEAN
    reason: str


_LFBK_CACHE: Optional[list[dict]] = None


def _load_lfbk_changes() -> list[dict]:
    """Load LFBK change log from mock file (or SAP CDHDR/CDPOS in production)."""
    global _LFBK_CACHE
    if _LFBK_CACHE is not None:
        return _LFBK_CACHE

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    mock_path = os.path.join(base_dir, "mock_data", "mock_lfbk_changes.json")

    if os.path.exists(mock_path):
        with open(mock_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            _LFBK_CACHE = data.get("lfbk_changes", [])
    else:
        _LFBK_CACHE = []

    return _LFBK_CACHE


def check_vendor_bank_change(
    vendor_code: str,
    vendor_name: str,
    reference_date: Optional[str] = None
) -> VendorBankGuardResult:
    """
    Checks if vendor's bank account was recently changed in LFBK.

    Args:
        vendor_code: SAP Vendor Code (LIFNR) e.g. "V10001"
        vendor_name: Vendor name for lookup if vendor_code not in LFBK
        reference_date: Date to compare against (defaults to today)

    Returns:
        VendorBankGuardResult with risk score and change details
    """
    changes = _load_lfbk_changes()

    if reference_date:
        try:
            ref_date = datetime.strptime(reference_date, "%Y-%m-%d").date()
        except ValueError:
            ref_date = date.today()
    else:
        ref_date = date.today()

    # Find matching vendor in change log
    matched_change: Optional[dict] = None
    for change in changes:
        if (change.get("vendor_code") == vendor_code or
                change.get("vendor_name", "").lower() == vendor_name.lower()):
            matched_change = change
            break

    if matched_change is None:
        return VendorBankGuardResult(
            has_recent_change=False,
            days_since_change=-1,
            change_date="",
            changed_by="",
            old_bank_account="",
            new_bank_account="",
            old_bank_key="",
            new_bank_key="",
            score=0.0,
            risk_level="CLEAN",
            reason="No recent bank account changes found for this vendor."
        )

    # Use pre-computed days if available, else compute
    days_since = matched_change.get("days_since_change", -1)
    if days_since < 0:
        try:
            change_dt = datetime.strptime(matched_change["change_date"], "%Y-%m-%d").date()
            days_since = (ref_date - change_dt).days
        except Exception:
            days_since = 999

    # Score based on days since change
    if days_since < 7:
        score = 100.0
        risk_level = "HIGH"
        reason = (f"CRITICAL: Vendor bank account changed {days_since} day(s) ago "
                  f"by {matched_change.get('changed_by', 'UNKNOWN')}. "
                  f"Old: {matched_change.get('old_bank_account', '')} → "
                  f"New: {matched_change.get('new_bank_account', '')}. "
                  f"Auto Payment Block applied.")
    elif days_since <= 30:
        score = 70.0
        risk_level = "MEDIUM"
        reason = (f"WARNING: Vendor bank account changed {days_since} day(s) ago "
                  f"by {matched_change.get('changed_by', 'UNKNOWN')}. "
                  f"Old: {matched_change.get('old_bank_account', '')} → "
                  f"New: {matched_change.get('new_bank_account', '')}. "
                  f"Requires manual review before payment.")
    else:
        score = 0.0
        risk_level = "CLEAN"
        reason = (f"Bank account change was {days_since} day(s) ago — beyond 30-day risk window. "
                  f"Cleared for payment.")

    return VendorBankGuardResult(
        has_recent_change=(days_since <= 30),
        days_since_change=days_since,
        change_date=matched_change.get("change_date", ""),
        changed_by=matched_change.get("changed_by", ""),
        old_bank_account=matched_change.get("old_bank_account", ""),
        new_bank_account=matched_change.get("new_bank_account", ""),
        old_bank_key=matched_change.get("old_bank_key", ""),
        new_bank_key=matched_change.get("new_bank_key", ""),
        score=score,
        risk_level=risk_level,
        reason=reason
    )


def invalidate_cache():
    """Call this to reload LFBK data (e.g., after a live SAP refresh)."""
    global _LFBK_CACHE
    _LFBK_CACHE = None
