"""
UC14 GL Anomaly Detection Agent — Unit Tests
==================================================
Run: python tests/test_scoring.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.data_loader import GLPosting, HistoricalBaseline, BankStatementEntry
from agent.scoring_engine import ScoringEngine


def make_posting(amount=850000, posting_time="11:00", gl="400100", doc_type="DR",
                  is_ic=False, ic_partner_amount=0.0, utr="", duplicate=False):
    return GLPosting(
        doc_no="5000001", line_item="1", gl_account=gl, doc_type=doc_type, company_code="IN01",
        posting_date="2026-01-15", posting_time=posting_time, amount_inr=amount,
        is_intercompany=is_ic, ic_partner_company="DE01" if is_ic else "", ic_partner_amount=ic_partner_amount,
        utr_reference=utr, duplicate_flag=duplicate,
    )


def make_baseline(mean=850000, std=180000, valid=True, gl="400100", doc_type="DR"):
    return HistoricalBaseline(gl_account=gl, doc_type=doc_type, mean_amount=mean, std_dev_amount=std,
                               valid_combination=valid)


def test_normal_posting_auto_reconciles():
    posting = make_posting(amount=860000, posting_time="11:00")
    baseline = make_baseline(mean=850000, std=180000)
    d = ScoringEngine().score_posting(posting, baseline, None)
    assert d.action == "AUTO_RECONCILE", f"expected AUTO_RECONCILE, got {d.action} (ARI={d.ari})"
    print(f"  Normal posting: ARI={d.ari:.1f} -> {d.action}  OK")


def test_large_zscore_investigate_or_report():
    posting = make_posting(amount=850000 + 180000 * 4, posting_time="11:00")  # 4 std dev out
    baseline = make_baseline(mean=850000, std=180000)
    d = ScoringEngine().score_posting(posting, baseline, None)
    assert d.action in ("DAILY_REPORT", "INVESTIGATE"), f"expected DAILY_REPORT or INVESTIGATE, got {d.action}"
    print(f"  4 std-dev deviation: ARI={d.ari:.1f} -> {d.action}  OK")


def test_over_1cr_forces_investigate():
    posting = make_posting(amount=15_000_000, posting_time="11:00")
    baseline = make_baseline(mean=850000, std=180000)
    d = ScoringEngine().score_posting(posting, baseline, None)
    assert d.action == "INVESTIGATE"
    assert d.hard_override
    print(f"  Amount > Rs.1 crore -> hard override INVESTIGATE (ARI={d.ari:.1f})  OK")


def test_duplicate_forces_investigate():
    posting = make_posting(amount=860000, duplicate=True)
    baseline = make_baseline(mean=850000, std=180000)
    d = ScoringEngine().score_posting(posting, baseline, None)
    assert d.action == "INVESTIGATE"
    assert d.hard_override
    print(f"  Duplicate posting -> hard override INVESTIGATE  OK")


def test_off_hours_raises_ari():
    baseline = make_baseline(mean=850000, std=180000)
    p_business = make_posting(amount=860000, posting_time="11:00")
    p_off_hours = make_posting(amount=860000, posting_time="03:00")
    d_business = ScoringEngine().score_posting(p_business, baseline, None)
    d_off = ScoringEngine().score_posting(p_off_hours, baseline, None)
    assert d_off.ari > d_business.ari, f"off-hours ARI ({d_off.ari}) should exceed business-hours ARI ({d_business.ari})"
    print(f"  Off-hours ARI={d_off.ari:.1f} > business-hours ARI={d_business.ari:.1f}  OK")


def test_invalid_combination_raises_ari():
    p = make_posting(amount=5000, gl="999999", doc_type="SA")
    baseline_valid = make_baseline(mean=5000, std=8000, valid=True, gl="999999", doc_type="SA")
    baseline_invalid = make_baseline(mean=5000, std=8000, valid=False, gl="999999", doc_type="SA")
    d_valid = ScoringEngine().score_posting(p, baseline_valid, None)
    d_invalid = ScoringEngine().score_posting(p, baseline_invalid, None)
    assert d_invalid.ari > d_valid.ari
    print(f"  Invalid combination ARI={d_invalid.ari:.1f} > valid combination ARI={d_valid.ari:.1f}  OK")


def test_ic_imbalance_raises_ari():
    baseline = make_baseline(mean=500000, std=210000, gl="210600", doc_type="SA")
    p_balanced = make_posting(amount=500000, gl="210600", doc_type="SA", is_ic=True, ic_partner_amount=500000)
    p_unbalanced = make_posting(amount=500000, gl="210600", doc_type="SA", is_ic=True, ic_partner_amount=650000)
    d_balanced = ScoringEngine().score_posting(p_balanced, baseline, None)
    d_unbalanced = ScoringEngine().score_posting(p_unbalanced, baseline, None)
    assert d_unbalanced.ari > d_balanced.ari
    print(f"  IC unbalanced ARI={d_unbalanced.ari:.1f} > IC balanced ARI={d_balanced.ari:.1f}  OK")


def test_bank_match_detected():
    baseline = make_baseline(mean=850000, std=180000)
    p = make_posting(amount=860000, utr="UTR999")
    bank_entry = BankStatementEntry(utr_reference="UTR999", bank_amount=860000, bank_date="2026-01-15")
    d = ScoringEngine().score_posting(p, baseline, bank_entry)
    assert d.ari_breakdown.bank_matched is True
    print(f"  Bank entry matches posting amount -> bank_matched=True  OK")


def test_bank_mismatch_flagged():
    baseline = make_baseline(mean=850000, std=180000)
    p = make_posting(amount=860000, utr="UTR999")
    d = ScoringEngine().score_posting(p, baseline, None)  # no bank entry found at all
    assert d.ari_breakdown.bank_matched is False
    assert any("no bank statement entry" in a.lower() for a in d.alerts)
    print(f"  No bank entry found for UTR -> bank_matched=False, alert logged  OK")


def test_audit_trail_ref_generated():
    posting = make_posting()
    baseline = make_baseline()
    d = ScoringEngine().score_posting(posting, baseline, None)
    assert d.audit_trail_ref.startswith("ARI-")
    print(f"  Audit ref generated: {d.audit_trail_ref}  OK")


def test_ari_weights_sum_to_one():
    from config.settings import ARI_WEIGHTS
    total = sum(ARI_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-6, f"weights sum to {total}, expected 1.0"
    print(f"  ARI_WEIGHTS sum to {total:.2f}  OK")


def test_no_baseline_still_processes():
    posting = make_posting(gl="UNKNOWN", doc_type="ZZ")
    d = ScoringEngine().score_posting(posting, None, None)
    assert d.action in ("AUTO_RECONCILE", "DAILY_REPORT", "INVESTIGATE")
    assert any("no historical baseline" in a.lower() for a in d.alerts)
    print(f"  No baseline found -> ARI={d.ari:.1f}, action={d.action}, alert logged  OK")


def test_full_pipeline_excel():
    from agent.data_loader import UC14DataLoader
    loader = UC14DataLoader()
    try:
        loader.load()
    except FileNotFoundError:
        print("  [SKIP] Excel not found — run scripts/generate_dataset.py first")
        return

    engine = ScoringEngine()
    posting = loader.postings[0]
    baseline = loader.get_baseline(posting.gl_account, posting.doc_type)
    bank_entry = loader.get_bank_entry(posting.utr_reference) if posting.utr_reference else None
    d = engine.score_posting(posting, baseline, bank_entry)

    assert d.doc_no == posting.doc_no
    assert 0 <= d.ari <= 100
    assert d.action in ("AUTO_RECONCILE", "DAILY_REPORT", "INVESTIGATE")
    assert d.audit_trail_ref.startswith("ARI-")
    print(f"  {posting.doc_no}/{posting.line_item}: ARI={d.ari:.1f} -> {d.action}  OK")


if __name__ == "__main__":
    TESTS = [
        test_normal_posting_auto_reconciles, test_large_zscore_investigate_or_report,
        test_over_1cr_forces_investigate, test_duplicate_forces_investigate,
        test_off_hours_raises_ari, test_invalid_combination_raises_ari,
        test_ic_imbalance_raises_ari, test_bank_match_detected, test_bank_mismatch_flagged,
        test_audit_trail_ref_generated, test_ari_weights_sum_to_one,
        test_no_baseline_still_processes, test_full_pipeline_excel,
    ]
    passed = 0
    print("\n" + "=" * 60)
    print("  UC14 GL Anomaly Detection Agent — Unit Tests")
    print("=" * 60)
    for t in TESTS:
        name = t.__name__.replace("test_", "").replace("_", " ").title()
        try:
            t()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}  — {e}")
        except Exception as e:
            print(f"  ERROR {name}  — {e}")
    print("=" * 60)
    print(f"  {passed}/{len(TESTS)} tests passed")
    print("=" * 60)
