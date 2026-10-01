"""
UC14 GL Anomaly Detection Agent — Configuration
=====================================================
Finance / SAP FI-GL
Scores every GL posting against a statistical baseline (mean/std dev per
GL account + document type), auto-reconciles normal patterns against the
bank statement, and surfaces genuine outliers same-day instead of during
a manual month-end line-by-line review — producing an Anomaly Risk Index
(ARI), 0-100, higher = more anomalous.

ARI Weights:
  Amount Z-score vs Historical Baseline   35%
  Posting Time (off-hours flag)           25%
  Account Combination Validity            20%
  Materiality (INR amount)                15%
  Inter-Company Balance Check              5%

Decision — explicit business rules drive the action; ARI is the
explainability score shown alongside:

  ARI LOW (< 25)                    → AUTO-RECONCILE  (bank match confirmed)
  ARI MEDIUM (25-60)                → DAILY REPORT     (7am exception report, same-day SLA)
  ARI HIGH (> 60) OR amount > 1 Cr  → INVESTIGATE      (Finance Manager alert, freeze if duplicate)
"""
from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

# ── Excel Dataset Settings ────────────────────────────────────────────────────
EXCEL_FILE = "backend/data/UC14_GLAnomaly_Dataset.xlsx"
SHEET_NAME = "UC14 - GL Anomaly Agent"

SEC_A_HEADER = 4;  SEC_A_START = 5;  SEC_A_END = 34      # GL Line Items — current period (30 postings)
SEC_B_HEADER = 36; SEC_B_START = 37; SEC_B_END = 51       # Historical Baseline per GL Account + Doc Type (15 rows)
SEC_C_HEADER = 53; SEC_C_START = 54; SEC_C_END = 68       # Bank Statement Entries / UTR (15 rows)
SEC_D_HEADER = 70; SEC_D_START = 71; SEC_D_END = 100      # Agent Output Reference (30 rows)

# ── ARI Weights (sum to 1.0) ──────────────────────────────────────────────────
ARI_WEIGHTS = {
    "amount_zscore":         0.35,
    "posting_time":          0.25,
    "account_combination":   0.20,
    "materiality":            0.15,
    "ic_balance":             0.05,
}

# ── Banded sub-scores ─────────────────────────────────────────────────────────
ZSCORE_BANDS = [   # (min_abs_z, score)
    (3.0, 100), (2.0, 70), (1.0, 40), (0.0, 10),
]
MATERIALITY_BANDS = [   # (min_amount_inr, score)
    (10_000_000, 100), (1_000_000, 60), (100_000, 30), (0, 10),
]
OFF_HOURS_SCORE = 100.0
BUSINESS_HOURS_SCORE = 10.0
BUSINESS_HOURS_START = 7    # 07:00
BUSINESS_HOURS_END = 21     # 21:00

VALID_COMBINATION_SCORE = 10.0
INVALID_COMBINATION_SCORE = 90.0

IC_BALANCED_SCORE = 10.0
IC_UNBALANCED_SCORE = 100.0
IC_NOT_APPLICABLE_SCORE = 10.0

# ── Decision thresholds ────────────────────────────────────────────────────────
ARI_LOW_MAX = 25.0
ARI_MEDIUM_MAX = 60.0
MATERIALITY_HARD_LIMIT_INR = 10_000_000   # ₹1 crore

# ── BTP Deployment & Live SAP Credentials ─────────────────────────────────────
BTP_APP_NAME = "uc14-gl-anomaly-agent"
BTP_RUNTIME = "python_buildpack"
BTP_MEMORY = "512M"
API_PORT = int(os.environ.get("PORT", 8000))
ENABLE_MOCK_FALLBACK = os.environ.get("ENABLE_MOCK_FALLBACK", os.environ.get("SAP_MOCK_MODE", "false")).lower() in ("true", "1", "yes")

# SAP Live Connection Settings
SAP_BASE_URL = os.environ.get("SAP_BASE_URL", "https://192.168.1.55:44300")
SAP_CLIENT = os.environ.get("SAP_CLIENT", "200")
SAP_USERNAME = os.environ.get("SAP_USERNAME", "INT_Prithvi")
SAP_PASSWORD = os.environ.get("SAP_PASSWORD", "Pst@576400")
SAP_VERIFY_SSL = os.environ.get("SAP_VERIFY_SSL", "false").lower() in ("true", "1", "yes")
