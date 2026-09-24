# UC14 — GL Anomaly Detection Agent

Finance / SAP FI-GL. Same backend architecture as UC7–UC12 from the 20 AI
Agent UCs library — config-driven Excel sections, a dataclass-based
scoring engine, a Perceive→Reason→Act→Learn orchestrator, a full unit
test suite. **The UI is a sixth distinct design** — a dark monitoring
console with a diverging Z-score bar per posting, since this is a
real-time surveillance problem ("which of today's postings deviate from
normal?"), not a queue, grid, table, scorecard, or search feed like any
of the prior five UCs. See `ui/app.py`'s module docstring for the
reasoning.

## SAP integration — verified clean this time

Unlike UC11 (`BAPI_VENDOREV_SAVEMS`) and UC12 (`BAPI_REQUISITION_GETINFO`,
`MDG_BS_ANAF_CR_PROCESS`), this use case's master-spec SAP integration
line checked out completely: `BAPI_BANK_GETLIST` and table `FEBEP`
(Electronic Bank Statement Line Items) are both genuinely real, confirmed
by search before use, not assumed. `BKPF`/`BSEG` are core, universally-known
SAP FI tables that didn't need verification. Nothing needed correcting
here — worth stating plainly rather than only ever reporting the
fabrications.

## What it does

Scores every GL posting against a statistical baseline (mean/std dev per
GL account + document type), matches it against the bank statement where
applicable, and produces an **Anomaly Risk Index (ARI)**, 0–100, higher =
more anomalous:

| Rule | Action |
|---|---|
| ARI LOW (< 25) | **AUTO-RECONCILE** — bank match confirmed, no action needed |
| ARI MEDIUM (25–60) | **DAILY REPORT** — 7am exception report to AP/AR, same-day SLA |
| ARI HIGH (> 60) OR amount > ₹1 crore | **INVESTIGATE** — immediate Finance Manager alert |

ARI Weights: Amount Z-score vs Baseline 35% · Posting Time (off-hours) 25%
· Account Combination Validity 20% · Materiality 15% · Inter-Company
Balance Check 5%.

Hard overrides, checked before the score bands: a posting **over ₹1
crore** always escalates regardless of composite ARI (the master spec
calls this out as an explicit materiality line, not something to leave
to the weighted score alone), and a **duplicate posting** is always
frozen for manual release.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python scripts/generate_dataset.py     # 4-section demo dataset
python tests/test_scoring.py           # 13 unit tests
python run.py                          # batch run, writes to results/
python run.py --doc 5000001 --line 1   # single posting, verbose
python run.py --ui                     # monitor at http://localhost:8000
```

## Dataset layout (data/UC14_GLAnomaly_Dataset.xlsx)

- **Section B** (written first) — Historical Baseline per GL Account +
  Doc Type (15 combinations, mean/std dev/valid-combination flag)
- **Section C** — Bank Statement Entries / UTR — populated dynamically
  from whichever Section A postings actually reference a UTR, so every
  reference resolves to a real entry (a couple deliberately mismatched to
  exercise the "bank match pending" path)
- **Section A** — GL Line Items for the current period (30 postings),
  deliberately spread ~50% normal / ~30% moderate deviation / ~20%
  severe (large Z-score, over ₹1 crore, duplicate, or intercompany
  imbalance) — the same controlled-distribution approach used since UC8
- **Section D** — Agent Output Reference — prior-period actuals for
  Learn-phase comparison, not agent input

## Current demo run

30 postings → 17 auto-reconciled, 8 on the daily exception report, 5
escalated to investigate — a believable spread, majority auto-reconciled
(as a real GL should mostly be), with meaningful representation across
all three tiers. All 13 tests pass on a clean-room run.
