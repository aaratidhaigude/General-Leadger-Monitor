"""
UC14 GL Anomaly Detection Agent — Mock SAP Service & Fallback Unit Tests
========================================================================
Run: python tests/test_mock_sap.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock.mock_data import get_mock_data, reset_mock_data
from mock.mock_sap_service import MockSAPService
from agent.data_loader import UC14DataLoader
from agent.scoring_engine import ScoringEngine


def test_mock_data_structure():
    postings, baselines, bank_entries = get_mock_data()
    assert len(postings) == 30, f"Expected 30 mock postings, got {len(postings)}"
    assert len(baselines) == 15, f"Expected 15 mock baselines, got {len(baselines)}"
    assert len(bank_entries) == 15, f"Expected 15 mock bank entries, got {len(bank_entries)}"
    print("  PASS  Mock Data Structure: 30 postings, 15 baselines, 15 bank entries verified.")


def test_data_loader_mock_fallback():
    # Force data loader to point to non-existent path
    loader = UC14DataLoader(excel_path="data/non_existent_file.xlsx")
    loader.load()
    assert len(loader.postings) == 30, "Mock fallback should have loaded 30 postings"
    assert ("400100", "DR") in loader._baselines, "Historical baseline for (400100, DR) should exist"
    print("  PASS  Data Loader Mock Fallback: Successfully loaded in-memory mock dataset when file missing.")


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
    assert actions["INVESTIGATE"] > 0, "Should have investigate decisions"
    assert actions["DAILY_REPORT"] > 0, "Should have daily report decisions"
    print(f"  PASS  Scoring On Mock Postings: {actions} verified across all 3 tiers.")


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
    # FB03
    r_fb03 = sap.execute_sap_action(doc_no="5000001", action_code="FB03")
    assert r_fb03["success"] is True

    # FBV0 (Approve parked doc 5000012)
    r_fbv0 = sap.execute_sap_action(doc_no="5000012", action_code="FBV0")
    assert r_fbv0["success"] is True

    # SM21 (Check error on failed doc 5000007)
    r_sm21 = sap.execute_sap_action(doc_no="5000007", action_code="SM21")
    assert r_sm21["success"] is True
    assert "Gateway Timeout" in r_sm21["message"]

    # FREEZE duplicate doc 5000017
    r_freeze = sap.execute_sap_action(doc_no="5000017", action_code="FREEZE")
    assert r_freeze["success"] is True

    # Check audit log
    logs = sap.get_audit_logs()
    assert len(logs) >= 4, f"Expected at least 4 audit logs, got {len(logs)}"
    print("  PASS  Mock SAP Actions & Audit: FB03, FBV0, SM21, FREEZE and audit trail validated.")


def main():
    print("\n" + "=" * 60)
    print("  UC14 GL Anomaly Agent — Mock SAP & Fallback Unit Tests")
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
