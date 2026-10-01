"""
GL Monitor — UTR & Bank Narrative Parser (MT940 / CAMT Field 86)
================================================================
Parses messy, unstructured bank statement narrative strings (Field 86 in MT940)
to extract UTR numbers, vendor names, and invoice references.
Then fuzzy-matches them against SAP open items to determine clearing status.

Supported payment modes:
  NEFT: N + 12-22 digits
  RTGS: R + 12-22 digits
  IMPS: P + 10-16 digits
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
from fuzzywuzzy import fuzz


@dataclass
class UTRParseResult:
    raw_narrative: str
    utr_found: bool
    utr_number: str
    payment_mode: str          # NEFT | RTGS | IMPS | UNKNOWN
    extracted_vendor_name: str
    extracted_invoice_ref: str
    extracted_amount: Optional[float]
    match_status: str          # AUTO_CLEAR | REVIEW | UNMATCHED | NO_UTR
    matched_doc_no: str
    matched_invoice_no: str
    vendor_match_score: float  # 0-100
    invoice_match_score: float # 0-100
    score: float               # 0-100 ARI sub-score
    reason: str


# ── UTR Regex Patterns ────────────────────────────────────────────────────────
_NEFT_PATTERN = re.compile(r'\bN(\d{12,22})\b', re.IGNORECASE)
_RTGS_PATTERN = re.compile(r'\bR(\d{12,22})\b', re.IGNORECASE)
_IMPS_PATTERN = re.compile(r'\bP(\d{10,16})\b', re.IGNORECASE)

# Invoice reference patterns
_INVOICE_PATTERNS = [
    re.compile(r'INV[/\-\s]?(\w{4,20})', re.IGNORECASE),
    re.compile(r'INV\.(\w{4,20})', re.IGNORECASE),
    re.compile(r'REF[/\-\s]?(\w{4,20})', re.IGNORECASE),
    re.compile(r'PAY[/\-\s]?(\w{4,20})', re.IGNORECASE),
    re.compile(r'\b(\d{5,10})\b'),  # Standalone 5-10 digit invoice numbers
]

# Vendor name noise words to strip
_VENDOR_NOISE = re.compile(
    r'\b(M/S|MS|PVT|LTD|PRIVATE|LIMITED|CO|CORP|CORPORATION|INC|LLC|NEFT|RTGS|IMPS|TRF|CR|DR|'
    r'PAYMENT|PAY|INV|REF|AMT|DT|DATE|BANK)\b',
    re.IGNORECASE
)


def _extract_utr(narrative: str) -> tuple[str, str, str]:
    """Returns (full_utr_with_prefix, utr_digits, payment_mode)."""
    m = _NEFT_PATTERN.search(narrative)
    if m:
        return f"N{m.group(1)}", m.group(1), "NEFT"
    m = _RTGS_PATTERN.search(narrative)
    if m:
        return f"R{m.group(1)}", m.group(1), "RTGS"
    m = _IMPS_PATTERN.search(narrative)
    if m:
        return f"P{m.group(1)}", m.group(1), "IMPS"
    return "", "", "UNKNOWN"


def _extract_invoice_ref(narrative: str) -> str:
    """Extracts invoice reference from narrative."""
    for pattern in _INVOICE_PATTERNS:
        m = pattern.search(narrative)
        if m:
            return m.group(1) if m.lastindex else m.group(0)
    return ""


def _clean_vendor_name(narrative: str, utr: str) -> str:
    """
    Strips UTR, payment mode prefixes, invoice refs, and noise words
    to isolate vendor name from narrative.
    """
    cleaned = narrative
    # Remove UTR number
    if utr:
        cleaned = cleaned.replace(utr, "")
    # Remove NEFT/RTGS/IMPS prefixes
    cleaned = re.sub(r'\b(NEFT|RTGS|IMPS)[/\-\s]?', '', cleaned, flags=re.IGNORECASE)
    # Remove invoice references
    cleaned = re.sub(r'INV[/\-\s]?\w{4,20}', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'REF[/\-\s]?\w{4,20}', '', cleaned, flags=re.IGNORECASE)
    # Remove amounts like 6,75,000 or 675000
    cleaned = re.sub(r'[\d,]+\.\d{2}', '', cleaned)
    cleaned = re.sub(r'\b[\d,]{5,}\b', '', cleaned)
    # Remove noise
    cleaned = _VENDOR_NOISE.sub('', cleaned)
    # Remove separators
    cleaned = re.sub(r'[\-/\|]+', ' ', cleaned)
    # Collapse whitespace
    cleaned = ' '.join(cleaned.split()).strip()
    return cleaned


def _extract_amount_from_narrative(narrative: str) -> Optional[float]:
    """Tries to extract amount from narrative text like '6,75,000' or '675000.00'."""
    # Pattern: number with commas and optional decimal
    m = re.search(r'\b(\d{1,3}(?:,\d{2,3})+(?:\.\d{2})?)\b', narrative)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            pass
    m = re.search(r'\b(\d{5,10}(?:\.\d{2})?)\b', narrative)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def parse_utr_narrative(
    raw_narrative: str,
    expected_utr: str,
    expected_vendor: str,
    expected_amount: float,
    open_invoices: list[dict]
) -> UTRParseResult:
    """
    Parses a Field 86 MT940 narrative string and matches against SAP open items.

    Args:
        raw_narrative: The raw Field 86 text from MT940/CAMT
        expected_utr: UTR reference from SAP posting (may be partial/empty)
        expected_vendor: Vendor name from SAP open item
        expected_amount: Expected amount from SAP open item
        open_invoices: List of SAP open item dicts with keys: doc_no, invoice_no, vendor, amount_inr

    Returns:
        UTRParseResult with extraction details and match status
    """
    # Step 1: Extract UTR
    utr_full, utr_digits, payment_mode = _extract_utr(raw_narrative)

    utr_found = bool(utr_full)

    # Step 2: Extract vendor name from narrative
    extracted_vendor = _clean_vendor_name(raw_narrative, utr_full)

    # Step 3: Extract invoice reference
    extracted_invoice = _extract_invoice_ref(raw_narrative)

    # Step 4: Extract amount from narrative
    extracted_amount = _extract_amount_from_narrative(raw_narrative)

    # Step 5: UTR match check — if UTR in narrative matches SAP posting
    utr_match = False
    if utr_found and expected_utr:
        # Normalize both: strip N/R/P prefix, compare digits
        norm_expected = re.sub(r'^[NRP]', '', expected_utr.strip())
        utr_match = (utr_digits == norm_expected or utr_full == expected_utr)

    # Step 6: Vendor fuzzy match
    vendor_score = 0.0
    if extracted_vendor and expected_vendor:
        vendor_score = float(fuzz.token_set_ratio(
            extracted_vendor.lower(), expected_vendor.lower()
        ))

    # Step 7: Invoice fuzzy match against open items
    best_invoice_match: Optional[dict] = None
    best_invoice_score = 0.0
    for inv in open_invoices:
        inv_no = str(inv.get("invoice_no", ""))
        if extracted_invoice and inv_no:
            score = float(fuzz.partial_ratio(
                re.sub(r'[\-/\s]', '', extracted_invoice.lower()),
                re.sub(r'[\-/\s]', '', inv_no.lower())
            ))
            if score > best_invoice_score:
                best_invoice_score = score
                best_invoice_match = inv

    # Step 8: Final match determination
    matched_doc = best_invoice_match.get("doc_no", "") if best_invoice_match else ""
    matched_inv = best_invoice_match.get("invoice_no", "") if best_invoice_match else ""

    if utr_match and vendor_score >= 70 and best_invoice_score >= 70:
        match_status = "AUTO_CLEAR"
        ari_score = 5.0
        reason = (f"UTR matched, vendor '{extracted_vendor}' matched {vendor_score:.0f}%, "
                  f"invoice ref matched {best_invoice_score:.0f}%. Safe to auto-clear.")
    elif utr_match and vendor_score >= 50:
        match_status = "REVIEW"
        ari_score = 40.0
        reason = (f"UTR matched but invoice reference match is weak ({best_invoice_score:.0f}%). "
                  f"Manual clearing recommended.")
    elif vendor_score >= 60:
        match_status = "REVIEW"
        ari_score = 65.0
        reason = (f"No UTR match. Vendor partially matched ({vendor_score:.0f}%). "
                  f"Narrative parsing extracted: '{extracted_vendor}'. Manual clearing required.")
    else:
        match_status = "UNMATCHED"
        ari_score = 90.0
        reason = (f"Cannot match bank narrative to any SAP open item. "
                  f"UTR found: {utr_found}. Extracted vendor: '{extracted_vendor}'. "
                  f"Manual investigation required.")

    return UTRParseResult(
        raw_narrative=raw_narrative,
        utr_found=utr_found,
        utr_number=utr_full,
        payment_mode=payment_mode,
        extracted_vendor_name=extracted_vendor,
        extracted_invoice_ref=extracted_invoice,
        extracted_amount=extracted_amount,
        match_status=match_status,
        matched_doc_no=matched_doc,
        matched_invoice_no=matched_inv,
        vendor_match_score=vendor_score,
        invoice_match_score=best_invoice_score,
        score=ari_score,
        reason=reason
    )
