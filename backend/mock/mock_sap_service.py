"""
UC14 GL Anomaly Detection Agent — Mock SAP S/4HANA & ERP Services
Provides high-fidelity mock interfaces for SAP FI-GL tables (BKPF, BSEG, FEBEP),
RFC BAPIs (BAPI_BANK_GETLIST, BAPI_ACC_DOCUMENT_REV_POST), and GUI transaction actions.
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from backend.mock.mock_data import (
    _current_postings, _current_baselines, _current_bank_entries,
    reset_mock_data, get_mock_postings, get_mock_baselines, get_mock_bank_entries
)


class MockSAPService:
    def __init__(self):
        self._action_logs: list[dict] = []

    def reset(self):
        """Reset mock data and audit trail to default state."""
        reset_mock_data()
        self._action_logs = []
        return {"status": "success", "message": "SAP Mock ERP and bank statements reset to pristine state."}

    def query_bkpf(self, doc_no: Optional[str] = None, company_code: Optional[str] = None) -> list[dict]:
        """Simulate SAP BKPF header query."""
        results = []
        for p in _current_postings:
            if doc_no and p["doc_no"] != doc_no:
                continue
            if company_code and p["company_code"] != company_code:
                continue
            results.append({
                "MANDT": "100",
                "BUKRS": p["company_code"],
                "BELNR": p["doc_no"],
                "GJAHR": "2026",
                "BLART": p["doc_type"],
                "BLDAT": p["posting_date"],
                "BUDAT": p["posting_date"],
                "CPUTM": p["posting_time"],
                "USNAM": "INTELLIGENCE_BOT",
                "TCODE": "FB01",
                "WAERS": "INR",
                "BKTXT": f"GL Posting {p['doc_no']}",
                "BSTAT": "V" if p.get("status") == "UNDER_PROCESS" else "",
            })
        return results

    def query_bseg(self, doc_no: Optional[str] = None) -> list[dict]:
        """Simulate SAP BSEG line item query."""
        results = []
        for p in _current_postings:
            if doc_no and p["doc_no"] != doc_no:
                continue
            results.append({
                "MANDT": "100",
                "BUKRS": p["company_code"],
                "BELNR": p["doc_no"],
                "GJAHR": "2026",
                "BUZEI": p["line_item"],
                "HKONT": p["gl_account"],
                "DMBTR": p["amount_inr"],
                "SHKZG": "S" if p["amount_inr"] >= 0 else "H",
                "XNEGP": "X" if p.get("duplicate_flag") else "",
                "KIDNO": p.get("utr_reference", ""),
                "VBUND": p.get("ic_partner_company", ""),
                "STATUS": p.get("status", "POSTED"),
                "STAGE": p.get("process_stage", ""),
            })
        return results

    def query_febep(self, utr_reference: Optional[str] = None) -> list[dict]:
        """Simulate SAP FEBEP query."""
        results = []
        for b in _current_bank_entries:
            if utr_reference and b["utr_reference"] != utr_reference:
                continue
            results.append({
                "MANDT": "100",
                "KUKEY": "BK202609",
                "ESNUM": b["utr_reference"],
                "VALUT": b["bank_date"],
                "KWBTR": b["bank_amount"],
                "WAERS": "INR",
                "CHECT": b["utr_reference"],
                "VGEXT": "NEFT/RTGS INCOMING/OUTGOING",
            })
        return results

    def bapi_bank_getlist(self, bank_country: str = "IN") -> dict:
        """Simulate RFC: BAPI_BANK_GETLIST."""
        banks = [
            {"BANK_CTRY": bank_country, "BANK_KEY": "HDFC0001", "BANK_NAME": "HDFC Bank Ltd (Treasury)"},
            {"BANK_CTRY": bank_country, "BANK_KEY": "ICIC0002", "BANK_NAME": "ICICI Bank Corporate Clearing"},
            {"BANK_CTRY": bank_country, "BANK_KEY": "SBIN0003", "BANK_NAME": "State Bank of India (Commercial)"},
        ]
        return {
            "RETURN": {"TYPE": "S", "CODE": "000", "MESSAGE": "Bank list retrieved successfully."},
            "BANK_LIST": banks,
            "TOTAL_BANKS": len(banks),
        }

    def execute_sap_action(self, doc_no: str, action_code: str, user: str = "BTP_USER", line_item: str = "1") -> dict:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        audit_id = f"SAP-{uuid.uuid4().hex[:8].upper()}"

        matched = False
        target_posting = None
        for p in _current_postings:
            if p["doc_no"] == doc_no and p["line_item"] == line_item:
                matched = True
                target_posting = p
                break

        if not matched:
            return {
                "success": False,
                "audit_ref": audit_id,
                "message": f"Document {doc_no} / line {line_item} not found in SAP BSEG table."
            }

        action_code = action_code.upper()
        if action_code == "FB03":
            resp_msg = f"SAP FB03: Display Document {doc_no} executed. Line item {line_item} (GL: {target_posting['gl_account']}) loaded into SAP GUI Session."
        elif action_code == "FBV0":
            target_posting["status"] = "POSTED"
            target_posting["process_stage"] = "Approved & Posted in SAP (FBV0)"
            resp_msg = f"SAP FBV0: Dual-Control approval completed for Parked Document {doc_no}. Status transitioned to POSTED."
        elif action_code == "SM21":
            reason = target_posting.get("failure_reason", "No system errors recorded")
            resp_msg = f"SAP SM21: System log inspected for Doc {doc_no}. Trace: '{reason}'. Gateway status: HEALTHY."
        elif action_code == "FEBAN":
            utr = target_posting.get("utr_reference", "N/A")
            resp_msg = f"SAP FEBAN: Post-processing bank clearing item for UTR '{utr}' completed. Clearing document created."
        elif action_code in ("FREEZE", "BLOCK"):
            target_posting["duplicate_flag"] = False
            target_posting["process_stage"] = "Payment Block 'A' Applied (Finance Controller Freeze)"
            resp_msg = f"SAP BSEG: Payment Block 'A' placed on Document {doc_no}. Line locked against automatic payment run F110."
        elif action_code == "REVERSE":
            rev_doc = f"600{doc_no[-4:]}"
            target_posting["status"] = "REVERSED"
            target_posting["process_stage"] = f"Reversed by Doc #{rev_doc} via BAPI_ACC_DOCUMENT_REV_POST"
            resp_msg = f"SAP FB08: Document {doc_no} reversed. Reversal Document #{rev_doc} posted successfully."
        else:
            resp_msg = f"SAP Custom Action '{action_code}' executed on Document {doc_no} by {user}."

        log_entry = {
            "audit_id": audit_id,
            "timestamp": ts,
            "user": user,
            "doc_no": doc_no,
            "line_item": line_item,
            "action": action_code,
            "result_message": resp_msg,
        }
        self._action_logs.append(log_entry)

        return {
            "success": True,
            "audit_ref": audit_id,
            "action": action_code,
            "doc_no": doc_no,
            "message": resp_msg,
            "timestamp": ts,
        }

    def get_audit_logs(self, doc_no: Optional[str] = None) -> list[dict]:
        if doc_no:
            return [l for l in self._action_logs if l["doc_no"] == doc_no]
        return self._action_logs


mock_sap_service = MockSAPService()
