"""
UC14 GL Anomaly Detection Agent — Standalone Mock Dataset
Provides rich mock data for SAP S/4HANA FI-GL postings, historical baselines,
and electronic bank statements (FEBEP / UTR) when running on SAP BTP Cloud Foundry.
"""
from __future__ import annotations
import copy
from agent.data_loader import GLPosting, HistoricalBaseline, BankStatementEntry

# 15 SAP FI Historical Baselines per GL Account & Document Type
_INITIAL_BASELINES: list[dict] = [
    {"gl_account": "400100", "doc_type": "DR", "mean_amount": 850000.0, "std_dev_amount": 180000.0, "valid_combination": True},
    {"gl_account": "400200", "doc_type": "DR", "mean_amount": 1200000.0, "std_dev_amount": 350000.0, "valid_combination": True},
    {"gl_account": "500200", "doc_type": "SA", "mean_amount": 620000.0, "std_dev_amount": 140000.0, "valid_combination": True},
    {"gl_account": "600100", "doc_type": "SA", "mean_amount": 2100000.0, "std_dev_amount": 95000.0, "valid_combination": True},
    {"gl_account": "700300", "doc_type": "KR", "mean_amount": 45000.0, "std_dev_amount": 22000.0, "valid_combination": True},
    {"gl_account": "700400", "doc_type": "KR", "mean_amount": 18000.0, "std_dev_amount": 9000.0, "valid_combination": True},
    {"gl_account": "800100", "doc_type": "ZP", "mean_amount": 3500.0, "std_dev_amount": 1800.0, "valid_combination": True},
    {"gl_account": "210500", "doc_type": "KR", "mean_amount": 380000.0, "std_dev_amount": 160000.0, "valid_combination": True},
    {"gl_account": "110200", "doc_type": "DR", "mean_amount": 410000.0, "std_dev_amount": 175000.0, "valid_combination": True},
    {"gl_account": "999999", "doc_type": "SA", "mean_amount": 5000.0, "std_dev_amount": 8000.0, "valid_combination": False},
    {"gl_account": "600200", "doc_type": "SA", "mean_amount": 310000.0, "std_dev_amount": 85000.0, "valid_combination": True},
    {"gl_account": "700500", "doc_type": "KR", "mean_amount": 95000.0, "std_dev_amount": 40000.0, "valid_combination": True},
    {"gl_account": "800200", "doc_type": "SA", "mean_amount": 12000.0, "std_dev_amount": 25000.0, "valid_combination": True},
    {"gl_account": "210600", "doc_type": "SA", "mean_amount": 500000.0, "std_dev_amount": 210000.0, "valid_combination": True},
    {"gl_account": "110300", "doc_type": "SA", "mean_amount": 500000.0, "std_dev_amount": 210000.0, "valid_combination": True},
]

# 15 Bank Statement Line Items (FEBEP Table representation)
_INITIAL_BANK_ENTRIES: list[dict] = [
    {"utr_reference": "UTR500000", "bank_amount": 845000.0, "bank_date": "2026-09-15"},
    {"utr_reference": "UTR500001", "bank_amount": 1210000.0, "bank_date": "2026-09-15"},
    {"utr_reference": "UTR500002", "bank_amount": 618000.0, "bank_date": "2026-09-14"},
    {"utr_reference": "UTR500003", "bank_amount": 2105000.0, "bank_date": "2026-09-14"},
    {"utr_reference": "UTR500004", "bank_amount": 44500.0, "bank_date": "2026-09-14"},
    {"utr_reference": "UTR500005", "bank_amount": 18200.0, "bank_date": "2026-09-13"},
    {"utr_reference": "UTR500006", "bank_amount": 3480.0, "bank_date": "2026-09-13"},
    {"utr_reference": "UTR500007", "bank_amount": 379000.0, "bank_date": "2026-09-13"},
    {"utr_reference": "UTR500008", "bank_amount": 412000.0, "bank_date": "2026-09-12"},
    {"utr_reference": "UTR500009", "bank_amount": 308000.0, "bank_date": "2026-09-12"},
    {"utr_reference": "UTR500010", "bank_amount": 94000.0, "bank_date": "2026-09-11"},
    {"utr_reference": "UTR500011", "bank_amount": 12500.0, "bank_date": "2026-09-11"},
    {"utr_reference": "UTR500012", "bank_amount": 850000.0, "bank_date": "2026-09-10"},
    {"utr_reference": "UTR500013", "bank_amount": 620000.0, "bank_date": "2026-09-10"},
    {"utr_reference": "UTR500014", "bank_amount": 510000.0, "bank_date": "2026-09-09"},
]

# 30 Curated GL Postings with realistic distribution (normal, moderate deviation, severe outliers, lifecycle statuses)
_INITIAL_POSTINGS: list[dict] = [
    # 1. Normal auto-reconcile
    {"doc_no": "5000000", "line_item": "1", "gl_account": "400100", "doc_type": "DR", "company_code": "IN01",
     "posting_date": "2026-09-15", "posting_time": "10:15", "amount_inr": 845000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500000", "duplicate_flag": False},
    # 2. Normal auto-reconcile
    {"doc_no": "5000001", "line_item": "1", "gl_account": "400200", "doc_type": "DR", "company_code": "IN01",
     "posting_date": "2026-09-15", "posting_time": "11:30", "amount_inr": 1210000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500001", "duplicate_flag": False},
    # 3. Normal auto-reconcile
    {"doc_no": "5000002", "line_item": "1", "gl_account": "500200", "doc_type": "SA", "company_code": "IN02",
     "posting_date": "2026-09-14", "posting_time": "14:20", "amount_inr": 618000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500002", "duplicate_flag": False},
    # 4. Normal auto-reconcile
    {"doc_no": "5000003", "line_item": "1", "gl_account": "600100", "doc_type": "SA", "company_code": "IN01",
     "posting_date": "2026-09-14", "posting_time": "09:45", "amount_inr": 2105000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500003", "duplicate_flag": False},
    # 5. Normal auto-reconcile
    {"doc_no": "5000004", "line_item": "1", "gl_account": "700300", "doc_type": "KR", "company_code": "IN01",
     "posting_date": "2026-09-14", "posting_time": "16:10", "amount_inr": 44500.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500004", "duplicate_flag": False},
    # 6. Off-hours moderate variance -> Daily Report
    {"doc_no": "5000005", "line_item": "1", "gl_account": "700400", "doc_type": "KR", "company_code": "IN02",
     "posting_date": "2026-09-13", "posting_time": "23:45", "amount_inr": 35000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 7. Normal small value
    {"doc_no": "5000006", "line_item": "1", "gl_account": "800100", "doc_type": "ZP", "company_code": "IN01",
     "posting_date": "2026-09-13", "posting_time": "12:10", "amount_inr": 3480.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500006", "duplicate_flag": False},
    # 8. FAILED attempt (Bank Gateway Timeout)
    {"doc_no": "5000007", "line_item": "1", "gl_account": "210500", "doc_type": "KR", "company_code": "IN01",
     "posting_date": "2026-09-13", "posting_time": "15:22", "amount_inr": 380000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False,
     "status": "FAILED", "attempt_number": 1, "failure_reason": "Bank Gateway Timeout (HTTP 504 on UTR-998811)",
     "retry_linked_doc": "5000008"},
    # 9. RETRY SUCCESS (linked to 5000007)
    {"doc_no": "5000008", "line_item": "1", "gl_account": "210500", "doc_type": "KR", "company_code": "IN01",
     "posting_date": "2026-09-13", "posting_time": "15:45", "amount_inr": 380000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500007", "duplicate_flag": False,
     "status": "RETRY_SUCCESS", "attempt_number": 2, "retry_linked_doc": "5000007"},
    # 10. Normal receivable
    {"doc_no": "5000009", "line_item": "1", "gl_account": "110200", "doc_type": "DR", "company_code": "IN02",
     "posting_date": "2026-09-12", "posting_time": "11:00", "amount_inr": 412000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500008", "duplicate_flag": False},
    # 11. Invalid combination (Suspense Account) -> High ARI / Daily Report
    {"doc_no": "5000010", "line_item": "1", "gl_account": "999999", "doc_type": "SA", "company_code": "IN01",
     "posting_date": "2026-09-12", "posting_time": "17:05", "amount_inr": 28000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 12. Normal contract labour
    {"doc_no": "5000011", "line_item": "1", "gl_account": "600200", "doc_type": "SA", "company_code": "IN01",
     "posting_date": "2026-09-12", "posting_time": "13:40", "amount_inr": 308000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500009", "duplicate_flag": False},
    # 13. UNDER PROCESS (Parked in SAP FBV0 awaiting approval)
    {"doc_no": "5000012", "line_item": "1", "gl_account": "700500", "doc_type": "KR", "company_code": "IN01",
     "posting_date": "2026-09-11", "posting_time": "16:50", "amount_inr": 94000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500010", "duplicate_flag": False,
     "status": "UNDER_PROCESS", "process_stage": "Parked in SAP (FBV0): Awaiting Dual-Control Approval"},
    # 14. PROCESS COMPLETED (Previously Parked in FBV0, now Approved & Posted)
    {"doc_no": "5000013", "line_item": "1", "gl_account": "800200", "doc_type": "SA", "company_code": "IN02",
     "posting_date": "2026-09-11", "posting_time": "10:10", "amount_inr": 12500.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500011", "duplicate_flag": False,
     "status": "PROCESS_COMPLETED", "process_stage": "Approval Completed: Parked Doc Posted in SAP (FBV0)"},
    # 15. Inter-company balanced -> Auto-reconcile
    {"doc_no": "5000014", "line_item": "1", "gl_account": "210600", "doc_type": "SA", "company_code": "IN01",
     "posting_date": "2026-09-11", "posting_time": "14:15", "amount_inr": 500000.0, "is_intercompany": True,
     "ic_partner_company": "DE01", "ic_partner_amount": 500000.0, "utr_reference": "", "duplicate_flag": False},
    # 16. Inter-company unbalanced -> Investigate / Daily Report
    {"doc_no": "5000015", "line_item": "1", "gl_account": "110300", "doc_type": "SA", "company_code": "IN01",
     "posting_date": "2026-09-10", "posting_time": "15:30", "amount_inr": 510000.0, "is_intercompany": True,
     "ic_partner_company": "US01", "ic_partner_amount": 720000.0, "utr_reference": "", "duplicate_flag": False},
    # 17. HARD OVERRIDE: Materiality > ₹1 Crore -> Force INVESTIGATE
    {"doc_no": "5000016", "line_item": "1", "gl_account": "400100", "doc_type": "DR", "company_code": "IN01",
     "posting_date": "2026-09-10", "posting_time": "11:00", "amount_inr": 18500000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 18. HARD OVERRIDE: Duplicate Posting -> Force INVESTIGATE & Freeze
    {"doc_no": "5000017", "line_item": "1", "gl_account": "400100", "doc_type": "DR", "company_code": "IN01",
     "posting_date": "2026-09-10", "posting_time": "10:15", "amount_inr": 845000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500000", "duplicate_flag": True},
    # 19. Large Z-Score (>4 sigma) -> High ARI
    {"doc_no": "5000018", "line_item": "1", "gl_account": "500200", "doc_type": "SA", "company_code": "IN02",
     "posting_date": "2026-09-09", "posting_time": "14:00", "amount_inr": 1450000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 20. UNDER PROCESS (NEFT In-Flight Transit)
    {"doc_no": "5000019", "line_item": "1", "gl_account": "210500", "doc_type": "KR", "company_code": "IN01",
     "posting_date": "2026-09-09", "posting_time": "16:40", "amount_inr": 375000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500014", "duplicate_flag": False,
     "status": "UNDER_PROCESS", "process_stage": "In-Flight: Electronic Bank NEFT Settlement in Transit"},
    # 21. Normal revenue
    {"doc_no": "5000020", "line_item": "1", "gl_account": "400200", "doc_type": "DR", "company_code": "IN01",
     "posting_date": "2026-09-08", "posting_time": "10:00", "amount_inr": 1180000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 22. Off-hours + Moderate Z-Score -> Daily Report
    {"doc_no": "5000021", "line_item": "1", "gl_account": "600100", "doc_type": "SA", "company_code": "IN01",
     "posting_date": "2026-09-08", "posting_time": "02:15", "amount_inr": 2350000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 23. Normal travel
    {"doc_no": "5000022", "line_item": "1", "gl_account": "700300", "doc_type": "KR", "company_code": "IN02",
     "posting_date": "2026-09-07", "posting_time": "11:20", "amount_inr": 48000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 24. Normal supplies
    {"doc_no": "5000023", "line_item": "1", "gl_account": "700400", "doc_type": "KR", "company_code": "IN01",
     "posting_date": "2026-09-07", "posting_time": "14:10", "amount_inr": 19500.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 25. Normal payment
    {"doc_no": "5000024", "line_item": "1", "gl_account": "800100", "doc_type": "ZP", "company_code": "IN01",
     "posting_date": "2026-09-06", "posting_time": "12:45", "amount_inr": 3600.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 26. Bank mismatch (UTR cited but amount differs from bank statement)
    {"doc_no": "5000025", "line_item": "1", "gl_account": "400100", "doc_type": "DR", "company_code": "IN01",
     "posting_date": "2026-09-06", "posting_time": "15:00", "amount_inr": 920000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "UTR500012", "duplicate_flag": False},
    # 27. Normal contract
    {"doc_no": "5000026", "line_item": "1", "gl_account": "600200", "doc_type": "SA", "company_code": "IN02",
     "posting_date": "2026-09-05", "posting_time": "13:15", "amount_inr": 315000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 28. Software licenses
    {"doc_no": "5000027", "line_item": "1", "gl_account": "700500", "doc_type": "KR", "company_code": "IN01",
     "posting_date": "2026-09-05", "posting_time": "16:00", "amount_inr": 98000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 29. FX Gain
    {"doc_no": "5000028", "line_item": "1", "gl_account": "800200", "doc_type": "SA", "company_code": "IN01",
     "posting_date": "2026-09-04", "posting_time": "11:50", "amount_inr": 14000.0, "is_intercompany": False,
     "ic_partner_company": "", "ic_partner_amount": 0.0, "utr_reference": "", "duplicate_flag": False},
    # 30. Inter-company receivable balanced
    {"doc_no": "5000029", "line_item": "1", "gl_account": "110300", "doc_type": "SA", "company_code": "IN02",
     "posting_date": "2026-09-04", "posting_time": "14:30", "amount_inr": 490000.0, "is_intercompany": True,
     "ic_partner_company": "SG01", "ic_partner_amount": 490000.0, "utr_reference": "", "duplicate_flag": False},
]

# Runtime in-memory state
_current_postings: list[dict] = copy.deepcopy(_INITIAL_POSTINGS)
_current_baselines: list[dict] = copy.deepcopy(_INITIAL_BASELINES)
_current_bank_entries: list[dict] = copy.deepcopy(_INITIAL_BANK_ENTRIES)


def reset_mock_data():
    global _current_postings, _current_baselines, _current_bank_entries
    _current_postings = copy.deepcopy(_INITIAL_POSTINGS)
    _current_baselines = copy.deepcopy(_INITIAL_BASELINES)
    _current_bank_entries = copy.deepcopy(_INITIAL_BANK_ENTRIES)


def get_mock_postings() -> list[GLPosting]:
    return [GLPosting(**d) for d in _current_postings]


def get_mock_baselines() -> dict[tuple, HistoricalBaseline]:
    baselines = {}
    for d in _current_baselines:
        b = HistoricalBaseline(**d)
        baselines[(b.gl_account, b.doc_type)] = b
    return baselines


def get_mock_bank_entries() -> dict[str, BankStatementEntry]:
    entries = {}
    for d in _current_bank_entries:
        e = BankStatementEntry(**d)
        entries[e.utr_reference] = e
    return entries


def get_mock_data():
    return get_mock_postings(), get_mock_baselines(), get_mock_bank_entries()
