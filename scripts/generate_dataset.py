"""
UC14 GL Anomaly Detection Agent — Excel Benchmark Dataset Generator
========================================================================
Generates data/UC14_GLAnomaly_Dataset.xlsx.
"""
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

NAVY_HEADER = "1C2B3A"
WHITE = "FFFFFF"
LIGHT_GRAY_FILL = "F8FAFC"
SECTION_FILL = "E2E8F0"

HEADER_FONT = Font(name="Arial", size=10, bold=True, color=WHITE)
TITLE_FONT = Font(name="Arial", size=12, bold=True, color=WHITE)
SECTION_FONT = Font(name="Arial", size=11, bold=True, color="0F172A")
DATA_FONT = Font(name="Arial", size=9)

HEADER_FILL = PatternFill("solid", fgColor=NAVY_HEADER)
SEC_FILL = PatternFill("solid", fgColor=SECTION_FILL)
ALT_FILL = PatternFill("solid", fgColor=LIGHT_GRAY_FILL)

THIN_BORDER = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)


def generate():
    from backend.mock.mock_data import _INITIAL_POSTINGS, _INITIAL_BASELINES, _INITIAL_BANK_ENTRIES

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "UC14 - GL Anomaly Agent"

    ws.merge_cells("A1:M1")
    ws["A1"] = "UC14 GL Anomaly Detection Agent — Benchmark Dataset"
    ws["A1"].font = TITLE_FONT
    ws["A1"].fill = HEADER_FILL
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    ws.cell(row=3, column=1, value="SECTION A: CURRENT PERIOD GL POSTINGS (30 ITEMS)").font = SECTION_FONT
    cols_a = ["Document No", "Line Item", "GL Account", "Doc Type", "Company Code", "Posting Date", "Posting Time", "Amount (INR)", "Inter-Company", "IC Partner Co", "IC Partner Amount", "UTR Reference", "Duplicate Flag"]
    for col_idx, col in enumerate(cols_a, 1):
        cell = ws.cell(row=4, column=col_idx, value=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    for row_idx, p in enumerate(_INITIAL_POSTINGS, 5):
        ws.cell(row=row_idx, column=1, value=p["doc_no"])
        ws.cell(row=row_idx, column=2, value=p["line_item"])
        ws.cell(row=row_idx, column=3, value=p["gl_account"])
        ws.cell(row=row_idx, column=4, value=p["doc_type"])
        ws.cell(row=row_idx, column=5, value=p["company_code"])
        ws.cell(row=row_idx, column=6, value=p["posting_date"])
        ws.cell(row=row_idx, column=7, value=p["posting_time"])
        ws.cell(row=row_idx, column=8, value=p["amount_inr"])
        ws.cell(row=row_idx, column=9, value="YES" if p["is_intercompany"] else "NO")
        ws.cell(row=row_idx, column=10, value=p["ic_partner_company"])
        ws.cell(row=row_idx, column=11, value=p["ic_partner_amount"])
        ws.cell(row=row_idx, column=12, value=p["utr_reference"])
        ws.cell(row=row_idx, column=13, value="YES" if p["duplicate_flag"] else "NO")

    ws.cell(row=35, column=1, value="SECTION B: HISTORICAL BASELINE PER GL ACCOUNT + DOC TYPE (15 ROWS)").font = SECTION_FONT
    cols_b = ["GL Account", "Doc Type", "Historical Mean (INR)", "Historical Std Dev (INR)", "Valid Combination"]
    for col_idx, col in enumerate(cols_b, 1):
        cell = ws.cell(row=36, column=col_idx, value=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    for row_idx, b in enumerate(_INITIAL_BASELINES, 37):
        ws.cell(row=row_idx, column=1, value=b["gl_account"])
        ws.cell(row=row_idx, column=2, value=b["doc_type"])
        ws.cell(row=row_idx, column=3, value=b["mean_amount"])
        ws.cell(row=row_idx, column=4, value=b["std_dev_amount"])
        ws.cell(row=row_idx, column=5, value="YES" if b["valid_combination"] else "NO")

    ws.cell(row=52, column=1, value="SECTION C: ELECTRONIC BANK STATEMENT LINE ITEMS / UTR (15 ROWS)").font = SECTION_FONT
    cols_c = ["UTR Reference", "Bank Amount (INR)", "Bank Date"]
    for col_idx, col in enumerate(cols_c, 1):
        cell = ws.cell(row=53, column=col_idx, value=col)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL

    for row_idx, c in enumerate(_INITIAL_BANK_ENTRIES, 54):
        ws.cell(row=row_idx, column=1, value=c["utr_reference"])
        ws.cell(row=row_idx, column=2, value=c["bank_amount"])
        ws.cell(row=row_idx, column=3, value=c["bank_date"])

    for col in ws.columns:
        max_len = max((len(str(cell.value)) if cell.value else 0) for cell in col)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(40, max(12, max_len + 2))

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "UC14_GLAnomaly_Dataset.xlsx")
    wb.save(out_path)
    print(f"Generated benchmark dataset: {out_path}")


if __name__ == "__main__":
    generate()
