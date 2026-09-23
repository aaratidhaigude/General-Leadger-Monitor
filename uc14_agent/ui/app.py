"""
GL Anomaly Detection Agent — Minimalist Enterprise Dashboard (FastAPI)
Start: python run.py --ui  |  Docs: /api/docs  |  BTP: cf push
"""
from __future__ import annotations
import os, sys
from dataclasses import asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from fastapi.middleware.cors import CORSMiddleware

from agent.gl_anomaly_agent import GLAnomalyAgent
from mock.mock_sap_service import mock_sap_service

app = FastAPI(title="GL Anomaly Detection Agent", version="2.1.0", docs_url="/api/docs", redoc_url="/api/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_last_results: Optional[list] = None


def _ensure_results():
    global _last_results
    if not _last_results:
        try:
            agent = GLAnomalyAgent()
            _last_results = agent.run_all()
        except Exception as exc:
            print(f"[App] Notice: agent.run_all() error: {exc}. Loading fallback dataset.")

        if not _last_results:
            from mock.mock_data import get_mock_data
            from agent.scoring_engine import ScoringEngine
            postings, baselines, bank_entries = get_mock_data()
            engine = ScoringEngine()
            _last_results = []
            for p in postings:
                b = baselines.get((p.gl_account, p.doc_type))
                bank = bank_entries.get(p.utr_reference) if p.utr_reference else None
                dec = engine.score_posting(p, b, bank)
                if dec:
                    _last_results.append(dec)
    return _last_results


@app.on_event("startup")
def startup_event():
    print("[App] Pre-loading GL Anomaly scan results into memory on server startup...")
    _ensure_results()


@app.get("/api/health")
def health():
    return {"status": "ok", "agent": "GL Anomaly Detection Agent", "version": "2.1.0"}


@app.get("/api/kpi")
def get_kpi():
    results = _ensure_results()
    flagged_value = sum(d.amount_inr for d in results if d.action != "AUTO_RECONCILE")
    total_val = sum(d.amount_inr for d in results)
    return {
        "posting_count": len(results),
        "total_value_inr": round(total_val, 0),
        "auto_reconcile": sum(1 for d in results if d.action == "AUTO_RECONCILE"),
        "daily_report": sum(1 for d in results if d.action == "DAILY_REPORT"),
        "investigate": sum(1 for d in results if d.action == "INVESTIGATE"),
        "under_process": sum(1 for d in results if getattr(d, 'status', '') == "UNDER_PROCESS"),
        "failed": sum(1 for d in results if getattr(d, 'status', '') == "FAILED"),
        "retried": sum(1 for d in results if getattr(d, 'status', '') == "RETRY_SUCCESS"),
        "flagged_value_inr": round(flagged_value, 0),
    }


@app.post("/api/run")
def run_agent():
    global _last_results
    try:
        agent = GLAnomalyAgent()
        _last_results = agent.run_all()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return get_kpi()


@app.get("/api/results/latest")
def latest_results():
    results = _ensure_results()
    return JSONResponse([asdict(d) for d in results])


@app.get("/api/results/{doc_no}/{line_item}")
def result_for_posting(doc_no: str, line_item: str):
    results = _ensure_results()
    for d in results:
        if str(d.doc_no) == str(doc_no) and str(d.line_item) == str(line_item):
            return asdict(d)
    raise HTTPException(status_code=404, detail=f"{doc_no}/{line_item} not found in the latest run.")


# --- MOCK SAP S/4HANA & ERP ENDPOINTS ---

class MockSAPActionRequest(BaseModel):
    doc_no: str
    action_code: str
    line_item: str = "1"
    user: str = "BTP_USER"


@app.get("/api/mock/sap/bkpf")
def get_mock_bkpf(doc_no: Optional[str] = None, company_code: Optional[str] = None):
    """Simulate SAP BKPF accounting document headers query."""
    return mock_sap_service.query_bkpf(doc_no=doc_no, company_code=company_code)


@app.get("/api/mock/sap/bseg")
def get_mock_bseg(doc_no: Optional[str] = None):
    """Simulate SAP BSEG accounting document line items query."""
    return mock_sap_service.query_bseg(doc_no=doc_no)


@app.get("/api/mock/sap/febep")
def get_mock_febep(utr_reference: Optional[str] = None):
    """Simulate SAP FEBEP electronic bank statement line items query."""
    return mock_sap_service.query_febep(utr_reference=utr_reference)


@app.get("/api/mock/sap/bapi/bank-getlist")
def get_mock_bapi_bank_getlist(country: str = "IN"):
    """Simulate SAP RFC BAPI_BANK_GETLIST."""
    return mock_sap_service.bapi_bank_getlist(bank_country=country)


@app.post("/api/mock/sap/action")
def execute_mock_sap_action(req: MockSAPActionRequest):
    """Simulate executing SAP transactions (FB03, FBV0, SM21, FEBAN, FREEZE, REVERSE)."""
    return mock_sap_service.execute_sap_action(
        doc_no=req.doc_no, action_code=req.action_code, user=req.user, line_item=req.line_item
    )


@app.post("/api/mock/sap/reset")
def reset_mock_sap():
    """Reset mock ERP records and audit logs to initial baseline."""
    global _last_results
    _last_results = None
    res = mock_sap_service.reset()
    _ensure_results()
    return res


@app.get("/api/mock/status")
def mock_status():
    """Check mock ERP service status and record counts."""
    from mock.mock_data import _current_postings, _current_baselines, _current_bank_entries
    return {
        "mock_service_active": True,
        "mock_bkpf_bseg_records": len(_current_postings),
        "mock_baselines_count": len(_current_baselines),
        "mock_febep_bank_items": len(_current_bank_entries),
        "audit_logs_recorded": len(mock_sap_service.get_audit_logs()),
    }


# --- INTERACTIVE AI ENDPOINTS ---

class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat/{doc_no}/{line_item}")
def chat_with_anomaly(doc_no: str, line_item: str, req: ChatRequest):
    results = _ensure_results()
    posting = None
    for d in results:
        if str(d.doc_no) == str(doc_no) and str(d.line_item) == str(line_item):
            posting = d
            break

    if not posting:
        return {"reply": f"Document {doc_no} / Line {line_item} not found in recent scan results."}

    msg = req.message.lower().strip()
    b = posting.ari_breakdown
    z = b.z_score
    amt = posting.amount_inr
    amt_str = f"Rs. {amt:,.0f}"
    status = getattr(posting, 'status', 'POSTED')

    # Check for optional OpenAI API Key if available in environment
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            import urllib.request, json
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                        "role": "system", 
                        "content": f"You are an expert SAP FI-GL audit assistant. You are analyzing Document {doc_no}, Line {line_item}, GL Account {posting.gl_account} ({posting.doc_type}). Amount is {amt_str}, Z-score is {z:.2f}, ARI Risk is {posting.ari:.0f}/100, Action is {posting.action}, Status is {status}, Off-hours is {b.off_hours}, Duplicate is {posting.duplicate_flag}. Explain clearly and concisely in the user's language (Hindi or English)."
                    },
                    {"role": "user", "content": req.message}
                ],
                "max_tokens": 200
            }
            req_obj = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=json.dumps(payload).encode('utf-8'),
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req_obj, timeout=6) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                return {"reply": res_data["choices"][0]["message"]["content"]}
        except Exception:
            pass

    # Intelligent Context-Aware Local Engine (Supports English & Hinglish/Hindi)
    is_hindi = any(w in msg for w in ["kyu", "kyun", "kya", "batao", "kaise", "galti", "kab", "kitna", "hai", "konsa", "bataiye", "dobara", "fail"])

    if any(k in msg for k in ["fail", "failed", "gateway", "timeout", "reversal", "retry", "dobara", "attempt"]):
        if status == "FAILED":
            if is_hindi:
                return {"reply": f"Yeh transaction Attempt 1 mein FAIL ho gaya tha. Reason: '{posting.failure_reason}'. Isko dobara retry kiya gaya hai Doc #{posting.retry_linked_doc} ke roop mein. Action: Verify karein ki pehle attempt ka paisa bank se deduct na hua ho (Double-Debit Risk)."}
            return {"reply": f"This transaction FAILED on Attempt 1. Reason: '{posting.failure_reason}'. Re-attempted under Doc #{posting.retry_linked_doc}. Audit recommendation: Check bank reversal log to eliminate double-debit risk."}
        elif status == "RETRY_SUCCESS":
            if is_hindi:
                return {"reply": f"Yeh ek RETRY transaction (Attempt 2) hai jo successfully complete hua. Iska pehla attempt Doc #{posting.retry_linked_doc} par fail hua tha. Recommendation: Confirm karein ki Attempt 1 ka reversal ho chuka hai."}
            return {"reply": f"This is a SUCCESSFUL RETRY (Attempt 2) linked to failed Doc #{posting.retry_linked_doc}. Ensure Attempt 1 was fully cancelled at the bank before releasing final settlement."}
        else:
            return {"reply": f"Document {doc_no} ka lifecycle status normal '{status}' hai (yeh fail ya retry nahi hua tha)."}

    elif any(k in msg for k in ["process", "processing", "under process", "pending", "park", "parked"]):
        if status == "UNDER_PROCESS":
            if is_hindi:
                return {"reply": f"Document {doc_no} abhi UNDER PROCESS hai. Stage: '{posting.process_stage}'. Yeh entry initiate ho chuki hai, lekin dual approval ya bank clearing settlement baki hai."}
            return {"reply": f"Document {doc_no} is currently UNDER PROCESS. Stage: '{posting.process_stage}'. It is monitored in real-time until posting completion."}
        else:
            return {"reply": f"Document {doc_no} ka status '{status}' hai (yeh under process nahi hai, final posted hai)."}

    elif "z-score" in msg or "z score" in msg or "sigma" in msg or "deviation" in msg:
        if is_hindi:
            return {"reply": f"Is transaction ka Z-score {z:+.2f} (sigma) hai. Iska matlab yeh amount is GL khate ke historical average se {abs(z):.1f} guna standard deviation door hai. Normal range -2 se +2 hoti hai, isliye yeh statistical outlier hai."}
        return {"reply": f"The Z-score is {z:+.2f} (sigma). This measures how many standard deviations this amount deviates from the historical GL average. Anything exceeding +/-3.0 sigma is flagged as an extreme statistical outlier."}

    elif any(k in msg for k in ["why", "reason", "flag", "flagged", "kyu", "kyun", "galti", "problem", "issue"]):
        reasons = []
        if status == "FAILED":
            reasons.append(f"Failed Attempt 1: {posting.failure_reason}")
        if status == "UNDER_PROCESS":
            reasons.append(f"In-Flight Processing: {posting.process_stage}")
        if status == "RETRY_SUCCESS":
            reasons.append(f"Retry linked to failed Doc #{posting.retry_linked_doc}")
        if abs(z) >= 3.0:
            reasons.append(f"Excessive amount deviation (Z = {z:+.2f} sigma)")
        if amt > 10000000:
            reasons.append(f"Materiality threshold exceeded (> Rs. 1 Crore: {amt_str})")
        if b.off_hours:
            reasons.append(f"Off-hours nocturnal posting at {posting.posting_time}")
        if posting.duplicate_flag:
            reasons.append("Duplicate posting detected")
        if posting.is_intercompany and b.ic_balance_score > 50:
            reasons.append(f"Inter-company imbalance with partner {posting.ic_partner_company}")
        if b.bank_matched is False:
            reasons.append("Bank statement entry did not match settled amount")

        reason_txt = " + ".join(reasons) if reasons else "Composite statistical variance across timing and GL parameters."
        if is_hindi:
            return {"reply": f"Document {doc_no} isliye flag hua kyunki: {reason_txt}. Total Risk Index {posting.ari:.0f}/100 hai aur action '{posting.action}' set kiya gaya hai."}
        return {"reply": f"Document {doc_no} was flagged due to: {reason_txt}. Composite Anomaly Risk Index is {posting.ari:.0f}/100 resulting in decision: {posting.action}."}

    elif any(k in msg for k in ["amount", "value", "paisa", "rupay", "kitna", "cost"]):
        if is_hindi:
            return {"reply": f"Is posting ka total amount {amt_str} hai. {'Yeh Rs. 1 Crore ke materiality hard limit se zyada hai, isliye automatic approval freeze ho gaya.' if amt > 10000000 else 'Isko baseline average se compare karke score kiya gaya hai.'}"}
        return {"reply": f"The posted amount is {amt_str}. {'This breaches the Rs. 1 Crore materiality hard limit, enforcing immediate controller review.' if amt > 10000000 else 'This amount has been evaluated against historical GL mean and standard deviation.'}"}

    elif any(k in msg for k in ["time", "timing", "kab", "ghante", "hours", "night", "raat"]):
        if is_hindi:
            return {"reply": f"Yeh document {posting.posting_date} ko {posting.posting_time} baje post hua tha. {'Yeh regular business hours (7 AM - 9 PM) ke bahaar ka off-hours time hai, isliye timing risk factor 100/100 mila hai.' if b.off_hours else 'Yeh regular business hours ke andar post hua tha.'}"}
        return {"reply": f"Posted at {posting.posting_time} on {posting.posting_date}. {'This falls outside normal operating hours (07:00-21:00), triggering an off-hours risk penalty of 100.' if b.off_hours else 'This was posted within normal business hours.'}"}

    elif any(k in msg for k in ["email", "draft", "cfo", "manager", "alert", "khat", "mail"]):
        return {"reply": f"Draft Audit Escalation:\n'To: Finance Controller / CFO\nSubject: Urgent Review — Flagged Document {doc_no}\n\nDocument {doc_no} (Line {line_item}) for GL {posting.gl_account} has been flagged with ARI Risk {posting.ari:.0f}/100.\nAmount: {amt_str} | Z-Score: {z:+.2f} sigma | Status: {status}\nPlease review supporting invoice in SAP (FB03) before releasing payment.'"}

    elif any(k in msg for k in ["remediate", "action", "fix", "karna", "step", "fb03"]):
        if is_hindi:
            return {"reply": f"Recommended SAP Steps:\n1. SAP GUI mein '/nFB03 {doc_no}' run karke line item check karein.\n2. Agar failed/retry hai toh bank reversal confirm karein.\n3. User {posting.company_code} se clarification maangein."}
        return {"reply": f"Recommended Next Steps for Document {doc_no}:\n1. Execute SAP transaction '/nFB03 {doc_no}' to inspect document lines.\n2. If retry transaction, cross-verify bank statement to prevent double deduction.\n3. Request verification from the posting creator."}

    else:
        if is_hindi:
            return {"reply": f"Document {doc_no} (GL: {posting.gl_account}, Amount: {amt_str}, Status: {status}) ka risk score {posting.ari:.0f}/100 hai. Aap mujhse iska Z-score, failure reason, retry link, ya SAP remediation ke baare mein pooch sakte hain."}
        return {"reply": f"Document {doc_no} (GL: {posting.gl_account}, Amount: {amt_str}, Status: {status}) has an Anomaly Risk Index of {posting.ari:.0f}/100 with decision {posting.action}. You can ask about failure reasons, retry tracking, in-process status, or draft audit notes."}


@app.get("/api/remediate/{doc_no}/{line_item}")
def get_remediation(doc_no: str, line_item: str):
    results = _ensure_results()
    for d in results:
        if str(d.doc_no) == str(doc_no) and str(d.line_item) == str(line_item):
            actions = [
                {"label": f"Inspect in SAP GUI (FB03)", "command": f"/nFB03 {doc_no}", "code": "FB03"},
                {"label": f"Check Bank Statement (FEBAN)", "command": f"/nFEBAN", "code": "FEBAN"}
            ]
            if getattr(d, 'status', '') == 'FAILED':
                actions.append({"label": f"Check Bank Rejection (SM21)", "command": f"/nSM21", "code": "SM21"})
                actions.append({"label": f"Inspect Retry Doc #{d.retry_linked_doc}", "command": f"/nFB03 {d.retry_linked_doc}", "code": "RETRY-DOC"})
            elif getattr(d, 'status', '') == 'UNDER_PROCESS':
                actions.append({"label": f"View Parked Doc (FBV0)", "command": f"/nFBV0 {doc_no}", "code": "FBV0"})
                actions.append({"label": "Dual Approval Workflow", "command": f"/nSBWP", "code": "WORKFLOW"})
            elif d.amount_inr > 10000000:
                actions.append({"label": "Escalate to CFO (Materiality > 1 Cr)", "command": f"MAIL CFO: URGENT_DOC_{doc_no}", "code": "ESCALATE"})
            elif d.is_intercompany:
                actions.append({"label": f"Reconcile Inter-Co with {d.ic_partner_company}", "command": f"PING_TEAMS: {d.ic_partner_company}_FINANCE", "code": "INTER-CO"})
            return {"actions": actions[:4]}
    return {"actions": [{"label": "Standard SAP Audit", "command": f"/nFB03 {doc_no}", "code": "FB03"}]}


class SimulateRequest(BaseModel):
    amount_inr: float


@app.post("/api/simulate/{doc_no}/{line_item}")
def simulate_anomaly(doc_no: str, line_item: str, req: SimulateRequest):
    _ensure_results()
    agent = GLAnomalyAgent()
    agent.loader.load()
    posting = agent.loader.get_posting(doc_no, line_item)
    if posting is None:
        raise HTTPException(status_code=404, detail="Posting not found.")

    posting.amount_inr = req.amount_inr
    baseline = agent.loader.get_baseline(posting.gl_account, posting.doc_type)
    bank_entry = agent.loader.get_bank_entry(posting.utr_reference) if posting.utr_reference else None

    decision = agent.engine.score_posting(posting, baseline, bank_entry)
    return asdict(decision)




def get_dashboard_html() -> str:
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "dashboard.html"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard.html"),
        os.path.join(os.getcwd(), "dashboard.html"),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>Error: dashboard.html not found</h1>"


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(get_dashboard_html())

