"""
UC14 GL Anomaly Detection Agent — Mock SAP Service & Fallback Unit Tests
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mock.mock_data import get_mock_data, reset_mock_data
from backend.mock.mock_sap_service import MockSAPService
from backend.agent.data_loader import UC14DataLoader
from backend.agent.scoring_engine import ScoringEngine


def test_mock_data_structure():
    postings, baselines, bank_entries = get_mock_data()
    assert len(postings) == 30, f"Expected 30 mock postings, got {len(postings)}"
    assert len(baselines) == 15, f"Expected 15 mock baselines, got {len(baselines)}"
    assert len(bank_entries) == 15, f"Expected 15 mock bank entries, got {len(bank_entries)}"
    print("  PASS  Mock Data Structure: 30 postings, 15 baselines, 15 bank entries verified.")


def test_data_loader_mock_fallback():
    loader = UC14DataLoader(excel_path="data/non_existent_file.xlsx")
    loader.load()
    assert len(loader.postings) > 0, "DataLoader should have loaded postings"
    print("  PASS  Data Loader Ingestion: Successfully loaded dataset.")


def test_scoring_on_mock_postings():
    loader = UC14DataLoader(excel_path="data/non_existent_file.xlsx").load()
    engine = ScoringEngine()

    actions = {"AUTO_RECONCILE": 0, "DAILY_REPORT": 0, "INVESTIGATE": 0}
    for p in loader.postings:
        base = loader.get_baseline(p.gl_account, p.doc_type)
        bank = loader.get_bank_entry(p.utr_reference) if p.utr_reference else None
        decision = engine.score_posting(p, base, bank)
        actions[decision.action] = actions.get(decision.action, 0) + 1

    assert actions["AUTO_RECONCILE"] > 0, "Should have auto-reconcile decisions"
    print(f"  PASS  Scoring On Mock Postings: {actions} verified.")


def test_mock_sap_service_queries():
    sap = MockSAPService()
    bkpf = sap.query_bkpf()
    assert len(bkpf) == 30, f"Expected 30 BKPF headers, got {len(bkpf)}"

    bseg = sap.query_bseg(doc_no="5000007")
    assert len(bseg) == 1, "Expected 1 BSEG line item for doc 5000007"
    assert bseg[0]["STATUS"] == "FAILED"

    febep = sap.query_febep()
    assert len(febep) == 15, "Expected 15 FEBEP items"

    bapi = sap.bapi_bank_getlist()
    assert bapi["RETURN"]["TYPE"] == "S"
    assert len(bapi["BANK_LIST"]) >= 3
    print("  PASS  Mock SAP Service Queries: BKPF, BSEG, FEBEP, BAPI_BANK_GETLIST all returned valid data.")


def test_mock_sap_actions_and_audit():
    sap = MockSAPService()
    r_fb03 = sap.execute_sap_action(doc_no="5000001", action_code="FB03")
    assert r_fb03["success"] is True

    r_fbv0 = sap.execute_sap_action(doc_no="5000012", action_code="FBV0")
    assert r_fbv0["success"] is True

    r_sm21 = sap.execute_sap_action(doc_no="5000007", action_code="SM21")
    assert r_sm21["success"] is True

    r_freeze = sap.execute_sap_action(doc_no="5000017", action_code="FREEZE")
    assert r_freeze["success"] is True

    logs = sap.get_audit_logs()
    assert len(logs) >= 4, f"Expected at least 4 audit logs, got {len(logs)}"
    print("  PASS  Mock SAP Actions & Audit: FB03, FBV0, SM21, FREEZE and audit trail validated.")


def main():
    print("\n" + "=" * 60)
    print("  UC14 GL Anomaly Agent — Mock SAP Unit Tests")
    print("=" * 60)
    test_mock_data_structure()
    test_data_loader_mock_fallback()
    test_scoring_on_mock_postings()
    test_mock_sap_service_queries()
    test_mock_sap_actions_and_audit()
    print("=" * 60)
    print("  ALL MOCK TESTS PASSED SUCCESSFULLY (5/5)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
