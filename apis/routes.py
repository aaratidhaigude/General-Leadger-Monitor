"""
GL Monitor — API Routes (v2.0 — Full Redesign)
===============================================
Endpoints:
  GET  /api/pull                  → Pull all invoices (SAP live or mock)
  POST /api/engine/before         → Run Before Payment pipeline
  POST /api/engine/after          → Run After Payment pipeline
  POST /api/engine/both           → Run both pipelines in parallel
  GET  /api/review/queue          → Get all MEDIUM + HIGH items
  POST /api/review/approve        → Approve a flagged item
  POST /api/review/reject         → Reject a flagged item
  GET  /api/report/download       → Download Excel/PDF report
  GET  /api/health                → Health check
"""
from __future__ import annotations
import json
import os
import io
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from backend.agent.pipeline_before import run_before_pipeline, BeforePaymentResult
from backend.agent.pipeline_after import run_after_pipeline, AfterPaymentResult

router = APIRouter()

# ── In-memory state (replace with DB in production) ──────────────────────────
_all_invoices: list[dict] = []
_before_results: list[dict] = []
_after_results: list[dict] = []
_review_actions: dict[str, dict] = {}   # doc_no -> {action, note, timestamp, user}
_run_history: list[dict] = []


def _load_mock_invoices() -> list[dict]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mock_path = os.path.join(base_dir, "mock_data", "mock_invoices.json")
    if os.path.exists(mock_path):
        with open(mock_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _result_to_dict(result) -> dict:
    """Converts pipeline result dataclass to a JSON-serializable dict."""
    d = {}
    for k, v in result.__dict__.items():
        if hasattr(v, '__dict__'):
            d[k] = _result_to_dict(v)
        elif isinstance(v, list):
            d[k] = [_result_to_dict(i) if hasattr(i, '__dict__') else i for i in v]
        else:
            d[k] = v
    return d


# ── Models ────────────────────────────────────────────────────────────────────
class ReviewActionRequest(BaseModel):
    doc_no: str
    action: str        # approve | reject
    note: Optional[str] = ""


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/api/health")
def health_check():
    return {"status": "ok", "version": "2.0.0", "timestamp": datetime.now().isoformat()}


@router.get("/api/pull")
def pull_invoices(use_mock: bool = Query(default=True)):
    """Pull all invoices from SAP or mock data and split into before/after."""
    global _all_invoices, _before_results, _after_results
    _all_invoices = _load_mock_invoices()
    _before_results = []
    _after_results = []

    before = [inv for inv in _all_invoices if inv.get("sap_status") in ("V", "A")]
    after = [inv for inv in _all_invoices if inv.get("sap_status") == "Z"]

    return {
        "total": len(_all_invoices),
        "before_payment_count": len(before),
        "after_payment_count": len(after),
        "invoices": _all_invoices,
        "pulled_at": datetime.now().isoformat(),
        "source": "MOCK" if use_mock else "SAP_LIVE"
    }


@router.post("/api/reset")
def reset_demo():
    """Reset the demo state to clean."""
    global _all_invoices, _before_results, _after_results, _review_actions, _run_history
    _all_invoices = []
    _before_results = []
    _after_results = []
    _review_actions = {}
    
    _run_history.append({
        "run_id": f"DEMO-RESET-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "pipeline": "RESET",
        "timestamp": datetime.now().isoformat(),
        "total": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "blocked": 0,
        "note": "Demo state reset"
    })
    return {"status": "success", "message": "Demo state reset successfully"}


@router.post("/api/engine/before")
def run_before_engine():
    """Run Before Payment pipeline on all Parked/Posted invoices."""
    global _before_results, _run_history, _all_invoices

    if not _all_invoices:
        _all_invoices = _load_mock_invoices()

    before_invoices = [inv for inv in _all_invoices if inv.get("sap_status") in ("V", "A")]

    results = []
    for inv in before_invoices:
        result = run_before_pipeline(inv, _all_invoices)
        results.append(_result_to_dict(result))

    _before_results = results

    # Stats
    high = sum(1 for r in results if r["tier"] == "HIGH")
    medium = sum(1 for r in results if r["tier"] == "MEDIUM")
    low = sum(1 for r in results if r["tier"] == "LOW")
    blocked = sum(1 for r in results if r["payment_block_applied"])

    run_record = {
        "run_id": f"BEF-RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "pipeline": "BEFORE",
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "high": high,
        "medium": medium,
        "low": low,
        "blocked": blocked
    }
    _run_history.append(run_record)

    return {
        "run_id": run_record["run_id"],
        "pipeline": "BEFORE_PAYMENT",
        "total_processed": len(results),
        "high_count": high,
        "medium_count": medium,
        "low_count": low,
        "auto_blocked_count": blocked,
        "results": results
    }


@router.post("/api/engine/after")
def run_after_engine():
    """Run After Payment pipeline on all Cleared invoices."""
    global _after_results, _run_history, _all_invoices

    if not _all_invoices:
        _all_invoices = _load_mock_invoices()

    after_invoices = [inv for inv in _all_invoices if inv.get("sap_status") == "Z"]

    results = []
    for inv in after_invoices:
        result = run_after_pipeline(inv, _all_invoices)
        results.append(_result_to_dict(result))

    _after_results = results

    high = sum(1 for r in results if r["tier"] == "HIGH")
    medium = sum(1 for r in results if r["tier"] == "MEDIUM")
    low = sum(1 for r in results if r["tier"] == "LOW")

    run_record = {
        "run_id": f"AFT-RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "pipeline": "AFTER",
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "high": high,
        "medium": medium,
        "low": low,
        "blocked": 0
    }
    _run_history.append(run_record)

    return {
        "run_id": run_record["run_id"],
        "pipeline": "AFTER_PAYMENT",
        "total_processed": len(results),
        "high_count": high,
        "medium_count": medium,
        "low_count": low,
        "results": results
    }


@router.post("/api/engine/both")
def run_both_engines():
    """Run both Before and After pipelines."""
    before = run_before_engine()
    after = run_after_engine()
    return {
        "before_payment": before,
        "after_payment": after,
        "total_processed": before["total_processed"] + after["total_processed"],
        "total_high": before["high_count"] + after["high_count"],
        "total_medium": before["medium_count"] + after["medium_count"],
        "total_low": before["low_count"] + after["low_count"],
    }


@router.get("/api/review/queue")
def get_review_queue():
    """Get all MEDIUM and HIGH items from both pipelines."""
    queue = []

    for r in _before_results:
        if r["tier"] in ("HIGH", "MEDIUM"):
            action = _review_actions.get(r["doc_no"], {})
            queue.append({**r, "pipeline": "BEFORE", "review_action": action})

    for r in _after_results:
        if r["tier"] in ("HIGH", "MEDIUM"):
            action = _review_actions.get(r["doc_no"], {})
            queue.append({**r, "pipeline": "AFTER", "review_action": action})

    # Sort by ARI descending
    queue.sort(key=lambda x: x["ari"], reverse=True)

    return {
        "total_in_queue": len(queue),
        "pending_review": sum(1 for q in queue if not q["review_action"]),
        "approved": sum(1 for q in queue if q["review_action"].get("action") == "approve"),
        "rejected": sum(1 for q in queue if q["review_action"].get("action") == "reject"),
        "queue": queue
    }


@router.post("/api/review/approve")
def approve_item(req: ReviewActionRequest):
    """Approve a flagged item and remove its payment block."""
    _review_actions[req.doc_no] = {
        "action": "approve",
        "note": req.note or "",
        "timestamp": datetime.now().isoformat(),
        "user": "FINANCE_USER"
    }
    return {"status": "approved", "doc_no": req.doc_no, "message": "Payment block removed. Invoice approved for payment."}


@router.post("/api/review/reject")
def reject_item(req: ReviewActionRequest):
    """Permanently reject and block a flagged item."""
    _review_actions[req.doc_no] = {
        "action": "reject",
        "note": req.note or "",
        "timestamp": datetime.now().isoformat(),
        "user": "FINANCE_USER"
    }
    return {"status": "rejected", "doc_no": req.doc_no, "message": "Invoice permanently blocked. Audit trail logged."}


@router.get("/api/report/download")
def download_report(
    format: str = Query(default="excel", description="excel or pdf"),
    period: str = Query(default="this_month", description="this_month | last_3m | last_6m")
):
    """Generate and download Excel or PDF report for the selected period."""
    try:
        all_results = _before_results + _after_results
        total_high = sum(1 for r in all_results if r.get("tier") == "HIGH")
        total_medium = sum(1 for r in all_results if r.get("tier") == "MEDIUM")
        total_low = sum(1 for r in all_results if r.get("tier") == "LOW")
        total_blocked = sum(1 for r in _before_results if r.get("payment_block_applied"))
        total_value = sum(r.get("amount_inr", 0) for r in all_results)

        if format.lower() == "pdf":
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(A4), leftMargin=30, rightMargin=30, topMargin=30, bottomMargin=30)
            styles = getSampleStyleSheet()
            
            elements = []
            title_style = ParagraphStyle("ReportTitle", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#1F3864"))
            elements.append(Paragraph(f"GL Monitor — Anomaly & Payment Risk Report ({period.replace('_', ' ').title()})", title_style))
            elements.append(Paragraph(f"Generated on {datetime.now().strftime('%d %b %Y, %H:%M:%S')}", styles["Normal"]))
            elements.append(Spacer(1, 15))
            
            summary_data = [
                ["Total Invoices", "High Risk", "Medium Risk", "Low Risk", "Auto-Blocked", "Total Value (INR)"],
                [str(len(all_results)), str(total_high), str(total_medium), str(total_low), str(total_blocked), f"Rs. {total_value:,.0f}"]
            ]
            sum_table = Table(summary_data, colWidths=[120, 90, 90, 90, 100, 160])
            sum_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, 1), [colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(sum_table)
            elements.append(Spacer(1, 20))
            
            elements.append(Paragraph("<b>Flagged Invoices (High & Medium Risk)</b>", styles["Heading2"]))
            flagged = [r for r in all_results if r.get("tier") in ("HIGH", "MEDIUM")]
            if not flagged:
                elements.append(Paragraph("No High or Medium risk items detected.", styles["Normal"]))
            else:
                flag_data = [["Doc No", "Vendor", "Amount (INR)", "ARI Score", "Tier", "Block", "Audit Reference"]]
                for r in flagged:
                    flag_data.append([
                        r.get("doc_no", ""),
                        r.get("vendor", "")[:30],
                        f"Rs. {r.get('amount_inr', 0):,.0f}",
                        f"{r.get('ari', 0):.1f}",
                        r.get("tier", ""),
                        "YES" if r.get("payment_block_applied") else "NO",
                        r.get("audit_ref", "")
                    ])
                flag_table = Table(flag_data, colWidths=[80, 180, 110, 70, 70, 60, 160])
                flag_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                elements.append(flag_table)
                
            doc.build(elements)
            pdf_buffer.seek(0)
            filename = f"GL_Monitor_Report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )

        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        wb = openpyxl.Workbook()

        # ── Summary Sheet ──
        ws_sum = wb.active
        ws_sum.title = "Summary"

        header_fill = PatternFill("solid", fgColor="1F3864")
        header_font = Font(color="FFFFFF", bold=True, size=12)

        ws_sum["A1"] = "GL Monitor — Analysis Report"
        ws_sum["A1"].font = Font(bold=True, size=16, color="1F3864")
        ws_sum["A2"] = f"Period: {period.replace('_', ' ').title()}"
        ws_sum["A3"] = f"Generated: {datetime.now().strftime('%d %b %Y %H:%M:%S')}"
        ws_sum["A5"] = "Summary Statistics"
        ws_sum["A5"].font = Font(bold=True, size=13)

        stats = [
            ("Total Invoices Processed", len(all_results)),
            ("Total Invoice Value (INR)", f"₹{total_value:,.0f}"),
            ("HIGH Risk Invoices", total_high),
            ("MEDIUM Risk Invoices", total_medium),
            ("LOW Risk Invoices", total_low),
            ("Auto Payment Blocks Applied", total_blocked),
            ("Before Payment Processed", len(_before_results)),
            ("After Payment Processed", len(_after_results)),
        ]

        for i, (label, value) in enumerate(stats, start=6):
            ws_sum[f"A{i}"] = label
            ws_sum[f"B{i}"] = value
            ws_sum[f"A{i}"].font = Font(bold=True)

        # ── Before Payment Sheet ──
        ws_bef = wb.create_sheet("Before Payment")
        bef_headers = ["Doc No", "Invoice No", "Vendor", "Amount (INR)", "GL Account",
                        "Doc Type", "Posting Date", "ARI Score", "Tier", "Payment Block",
                        "Duplicate Flag", "Bank Change", "Audit Ref", "Alerts"]
        for col, h in enumerate(bef_headers, 1):
            cell = ws_bef.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        tier_fills = {
            "HIGH": PatternFill("solid", fgColor="FFD7D7"),
            "MEDIUM": PatternFill("solid", fgColor="FFF3CD"),
            "LOW": PatternFill("solid", fgColor="D4EDDA"),
        }

        for row_idx, r in enumerate(_before_results, 2):
            dup = r.get("duplicate_result", {}) or {}
            bank = r.get("bank_guard_result", {}) or {}
            row_data = [
                r.get("doc_no", ""), r.get("invoice_no", ""), r.get("vendor", ""),
                r.get("amount_inr", 0), r.get("gl_account", ""), r.get("doc_type", ""),
                r.get("posting_date", ""), r.get("ari", 0), r.get("tier", ""),
                "YES" if r.get("payment_block_applied") else "NO",
                dup.get("duplicate_type", "CLEAN"), bank.get("risk_level", "CLEAN"),
                r.get("audit_ref", ""), " | ".join(r.get("alerts", []))
            ]
            fill = tier_fills.get(r.get("tier", "LOW"), tier_fills["LOW"])
            for col_idx, val in enumerate(row_data, 1):
                cell = ws_bef.cell(row=row_idx, column=col_idx, value=val)
                cell.fill = fill

        for col in range(1, len(bef_headers) + 1):
            ws_bef.column_dimensions[get_column_letter(col)].width = 20

        # ── After Payment Sheet ──
        ws_aft = wb.create_sheet("After Payment")
        aft_headers = ["Doc No", "Invoice No", "Vendor", "Amount (INR)", "GL Account",
                        "Doc Type", "Posting Date", "ARI Score", "Tier", "UTR Match",
                        "Bank Variance %", "IC Balance", "Audit Ref", "Alerts"]
        for col, h in enumerate(aft_headers, 1):
            cell = ws_aft.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for row_idx, r in enumerate(_after_results, 2):
            utr = r.get("utr_result", {}) or {}
            row_data = [
                r.get("doc_no", ""), r.get("invoice_no", ""), r.get("vendor", ""),
                r.get("amount_inr", 0), r.get("gl_account", ""), r.get("doc_type", ""),
                r.get("posting_date", ""), r.get("ari", 0), r.get("tier", ""),
                utr.get("match_status", "N/A"), round(r.get("bank_variance_pct", 0), 2),
                "YES" if r.get("ic_balance_ok") else ("N/A" if not r.get("is_intercompany") else "NO"),
                r.get("audit_ref", ""), " | ".join(r.get("alerts", []))
            ]
            fill = tier_fills.get(r.get("tier", "LOW"), tier_fills["LOW"])
            for col_idx, val in enumerate(row_data, 1):
                cell = ws_aft.cell(row=row_idx, column=col_idx, value=val)
                cell.fill = fill

        for col in range(1, len(aft_headers) + 1):
            ws_aft.column_dimensions[get_column_letter(col)].width = 20

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f"GL_Monitor_Report_{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/api/history")
def get_run_history():
    """Get log of all past engine runs."""
    return {"history": list(reversed(_run_history))}


@router.get("/api/stats")
def get_stats():
    """Get current summary statistics for dashboard KPI cards."""
    all_results = _before_results + _after_results
    return {
        "total_pulled": len(_all_invoices),
        "before_count": len(_before_results),
        "after_count": len(_after_results),
        "high_count": sum(1 for r in all_results if r.get("tier") == "HIGH"),
        "medium_count": sum(1 for r in all_results if r.get("tier") == "MEDIUM"),
        "low_count": sum(1 for r in all_results if r.get("tier") == "LOW"),
        "auto_blocked": sum(1 for r in _before_results if r.get("payment_block_applied")),
        "pending_review": sum(
            1 for r in all_results
            if r.get("tier") in ("HIGH", "MEDIUM")
            and r.get("doc_no") not in _review_actions
        ),
        "total_value_inr": sum(r.get("amount_inr", 0) for r in all_results),
        "engine_run": len(_run_history) > 0
    }
