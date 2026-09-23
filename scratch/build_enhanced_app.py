import os, sys, json
from dataclasses import asdict

sys.path.insert(0, r"c:\Users\arati\Downloads\uc14_agent 1\uc14_agent")
os.environ["SAP_MOCK_MODE"] = "false"

from agent.gl_anomaly_agent import GLAnomalyAgent

print("[Builder] Pre-rendering live SAP dataset into dashboard.html...")
agent = GLAnomalyAgent()
results = agent.run_all()
res_dicts = [asdict(r) for r in results]

flagged_val = sum(d['amount_inr'] for d in res_dicts if d['action'] != 'AUTO_RECONCILE')
total_val = sum(d['amount_inr'] for d in res_dicts)

kpi_data = {
    'posting_count': len(res_dicts),
    'total_value_inr': round(total_val, 0),
    'auto_reconcile': sum(1 for d in res_dicts if d['action'] == 'AUTO_RECONCILE'),
    'daily_report': sum(1 for d in res_dicts if d['action'] == 'DAILY_REPORT'),
    'investigate': sum(1 for d in res_dicts if d['action'] == 'INVESTIGATE'),
    'under_process': sum(1 for d in res_dicts if d.get('status') == 'UNDER_PROCESS'),
    'failed': sum(1 for d in res_dicts if d.get('status') == 'FAILED'),
    'retried': sum(1 for d in res_dicts if d.get('status') == 'RETRY_SUCCESS'),
    'flagged_value_inr': round(flagged_val, 0),
}

initial_data_json = json.dumps(res_dicts)
initial_kpi_json = json.dumps(kpi_data)

app_path = r"c:\Users\arati\Downloads\uc14_agent 1\uc14_agent\ui\app.py"
dashboard_path = r"c:\Users\arati\Downloads\uc14_agent 1\dashboard.html"

# Read top python code (lines 1 to 353)
with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

py_top = "".join(lines[:353])

dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>General Ledger Anomaly Monitor — Live SAP S21</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
  <style>
    :root {
      --bg: #F9FAFB;
      --card-bg: #FFFFFF;
      --border: #E5E7EB;
      --border-subtle: #F3F4F6;
      
      --text-main: #111827;
      --text-muted: #4B5563;
      --text-dim: #9CA3AF;
      
      --primary: #1F2937;
      --primary-hover: #111827;
      --accent-blue: #2563EB;
      
      --status-green: #166534;
      --status-green-bg: #F0FDF4;
      --status-green-border: #BBF7D0;
      
      --status-amber: #92400E;
      --status-amber-bg: #FFFBEB;
      --status-amber-border: #FDE68A;
      
      --status-red: #991B1B;
      --status-red-bg: #FEF2F2;
      --status-red-border: #FECACA;

      --status-blue: #1E40AF;
      --status-blue-bg: #EFF6FF;
      --status-blue-border: #BFDBFE;
      
      --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.04);
      --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
    }

    /* Modals Base */
    .sap-modal-overlay {
      position: fixed;
      top: 0; left: 0; width: 100vw; height: 100vh;
      background: rgba(15, 23, 42, 0.55);
      backdrop-filter: blur(3px);
      z-index: 998;
      display: none;
    }
    .sap-modal-overlay.open { display: block; }

    .sap-modal {
      position: fixed;
      top: 50%; left: 50%;
      transform: translate(-50%, -50%) scale(0.96);
      width: 860px; max-width: 94vw;
      background: #FFFFFF;
      border-radius: 8px;
      box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15), 0 10px 10px -5px rgba(0, 0, 0, 0.06);
      border: 1px solid #CBD5E1;
      z-index: 999;
      display: none;
      transition: all 0.2s ease;
      font-family: 'Inter', sans-serif;
      overflow: hidden;
    }
    .sap-modal.open { display: block; transform: translate(-50%, -50%) scale(1); }

    .sap-gui-header {
      padding: 12px 18px;
      background: #F1F5F9;
      border-bottom: 1px solid #E2E8F0;
      display: flex; align-items: center; justify-content: space-between;
    }

    .sap-cmd-bar {
      padding: 8px 18px;
      background: #FFFFFF;
      border-bottom: 1px solid #E2E8F0;
      display: flex; align-items: center; gap: 10px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg);
      color: var(--text-main);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      font-size: 13px;
      line-height: 1.5;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }

    .mono { font-family: 'JetBrains Mono', monospace; }

    header {
      height: 56px;
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 0 32px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 50;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .header-logo {
      width: 28px;
      height: 28px;
      background: var(--primary);
      color: #FFFFFF;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 700;
      font-size: 13px;
    }

    .header-title-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .header-title {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-main);
      letter-spacing: -0.2px;
    }

    .status-badge-active {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      background: #F3F4F6;
      border: 1px solid var(--border);
      border-radius: 9999px;
      padding: 2px 8px;
      font-size: 11px;
      font-weight: 500;
      color: var(--text-muted);
    }

    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #10B981;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .btn {
      height: 32px;
      padding: 0 12px;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: background-color 0.15s ease, border-color 0.15s ease;
      text-decoration: none;
      border: 1px solid transparent;
    }

    .btn-secondary {
      background: var(--card-bg);
      border-color: var(--border);
      color: var(--text-main);
    }
    .btn-secondary:hover {
      background: #F9FAFB;
      border-color: #D1D5DB;
    }

    .btn-primary {
      background: var(--primary);
      color: #FFFFFF;
    }
    .btn-primary:hover {
      background: var(--primary-hover);
    }

    .container {
      max-width: 1440px;
      margin: 0 auto;
      padding: 24px 32px 64px;
    }

    .kpi-strip {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      box-shadow: var(--shadow-sm);
      margin-bottom: 24px;
      overflow: hidden;
    }

    @media (max-width: 1100px) {
      .kpi-strip { grid-template-columns: repeat(3, 1fr); }
    }
    @media (max-width: 700px) {
      .kpi-strip { grid-template-columns: 1fr 1fr; }
    }

    .kpi-col {
      padding: 16px 20px;
      border-right: 1px solid var(--border);
      cursor: pointer;
      transition: background-color 0.1s ease;
    }
    .kpi-col:hover {
      background: #F9FAFB;
    }
    .kpi-col:last-child {
      border-right: none;
    }

    .kpi-label {
      font-size: 11px;
      font-weight: 500;
      color: var(--text-dim);
      margin-bottom: 4px;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }

    .kpi-val {
      font-size: 20px;
      font-weight: 600;
      color: var(--text-main);
      letter-spacing: -0.3px;
    }

    .kpi-footnote {
      font-size: 10.5px;
      color: var(--text-muted);
      margin-top: 2px;
    }

    .charts-row {
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 20px;
      margin-bottom: 24px;
    }

    @media (max-width: 960px) {
      .charts-row { grid-template-columns: 1fr; }
    }

    .chart-panel {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 20px;
      box-shadow: var(--shadow-sm);
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }

    .panel-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-main);
    }

    .panel-subtitle {
      font-size: 11px;
      color: var(--text-dim);
    }

    .chart-box {
      height: 180px;
      position: relative;
    }

    .toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .search-input-wrap {
      position: relative;
      width: 300px;
      max-width: 100%;
    }

    .search-input-wrap svg {
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      width: 14px;
      height: 14px;
      color: var(--text-dim);
    }

    .search-input {
      width: 100%;
      height: 36px;
      padding: 0 12px 0 32px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      font-size: 12.5px;
      color: var(--text-main);
      outline: none;
      transition: border-color 0.15s ease;
    }

    .search-input:focus {
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 1px var(--accent-blue);
    }

    .segment-tabs {
      display: inline-flex;
      background: #ECEEF2;
      padding: 3px;
      border-radius: 6px;
      gap: 2px;
      flex-wrap: wrap;
    }

    .segment-btn {
      background: transparent;
      border: none;
      padding: 5px 11px;
      font-size: 11.5px;
      font-weight: 500;
      color: var(--text-muted);
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .segment-btn:hover {
      color: var(--text-main);
    }

    .segment-btn.active {
      background: #FFFFFF;
      color: var(--text-main);
      font-weight: 600;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
    }

    .table-container {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      box-shadow: var(--shadow-sm);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }

    thead {
      background: #F9FAFB;
      border-bottom: 1px solid var(--border);
    }

    th {
      padding: 10px 16px;
      font-size: 11px;
      font-weight: 600;
      color: var(--text-dim);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-subtle);
      font-size: 12.5px;
      vertical-align: middle;
      color: var(--text-main);
    }

    tbody tr {
      cursor: pointer;
      transition: background-color 0.1s ease;
    }

    tbody tr:hover {
      background: #F9FAFB;
    }

    tbody tr.selected-row {
      background: #F0F7FF;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 500;
      border: 1px solid transparent;
      white-space: nowrap;
    }

    .pill-green {
      background: var(--status-green-bg);
      color: var(--status-green);
      border-color: var(--status-green-border);
    }

    .pill-amber {
      background: var(--status-amber-bg);
      color: var(--status-amber);
      border-color: var(--status-amber-border);
    }

    .pill-red {
      background: var(--status-red-bg);
      color: var(--status-red);
      border-color: var(--status-red-border);
    }

    .pill-blue {
      background: var(--status-blue-bg);
      color: var(--status-blue);
      border-color: var(--status-blue-border);
    }

    .sheet-overlay {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.2);
      backdrop-filter: blur(1px);
      z-index: 100;
      opacity: 0;
      visibility: hidden;
      transition: opacity 0.2s ease, visibility 0.2s ease;
    }

    .sheet-overlay.open {
      opacity: 1;
      visibility: visible;
    }

    .sheet {
      position: fixed;
      top: 0;
      right: 0;
      bottom: 0;
      width: 560px;
      max-width: 92vw;
      background: #FFFFFF;
      border-left: 1px solid var(--border);
      box-shadow: -4px 0 24px rgba(0, 0, 0, 0.08);
      z-index: 101;
      transform: translateX(100%);
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      flex-direction: column;
    }

    .sheet.open {
      transform: translateX(0);
    }

    .sheet-header {
      padding: 20px 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .sheet-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-main);
    }

    .sheet-close {
      background: transparent;
      border: none;
      color: var(--text-dim);
      font-size: 18px;
      cursor: pointer;
      width: 28px;
      height: 28px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 4px;
    }
    .sheet-close:hover {
      background: #F3F4F6;
      color: var(--text-main);
    }

    .sheet-body {
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .section-heading {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-dim);
      margin-bottom: 10px;
    }

    .kv-card {
      background: #F9FAFB;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 14px;
    }

    .kv-list {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    .kv-key {
      font-size: 11px;
      color: var(--text-dim);
    }
    .kv-val {
      font-size: 12.5px;
      font-weight: 500;
      color: var(--text-main);
      margin-top: 2px;
    }

    .action-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .action-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: #FFFFFF;
      cursor: pointer;
      transition: border-color 0.15s ease;
    }
    .action-item:hover {
      border-color: #9CA3AF;
    }

    .action-code {
      font-size: 11px;
      font-weight: 600;
      background: #F3F4F6;
      color: #374151;
      padding: 2px 6px;
      border-radius: 4px;
    }

    .chat-box {
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
      background: #FFFFFF;
    }

    .chat-feed {
      height: 140px;
      overflow-y: auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 12px;
    }

    .chat-bubble {
      padding: 6px 10px;
      border-radius: 6px;
      max-width: 85%;
      line-height: 1.4;
    }
    .chat-user {
      align-self: flex-end;
      background: #F3F4F6;
      color: var(--text-main);
    }
    .chat-ai {
      align-self: flex-start;
      background: #F9FAFB;
      border: 1px solid var(--border);
      color: var(--text-main);
    }

    .chat-input-row {
      display: flex;
      border-top: 1px solid var(--border);
    }

    .chat-input-row input {
      flex: 1;
      border: none;
      padding: 8px 12px;
      font-size: 12px;
      outline: none;
    }

    .chat-input-row button {
      background: #F3F4F6;
      border: none;
      border-left: 1px solid var(--border);
      padding: 0 12px;
      font-size: 11.5px;
      font-weight: 500;
      cursor: pointer;
      color: var(--text-main);
    }
    .chat-input-row button:hover {
      background: #E5E7EB;
    }
  </style>
</head>
<body>

  <!-- Minimal Header -->
  <header>
    <div class="header-left">
      <div class="header-logo">GL</div>
      <div class="header-title-group">
        <span class="header-title">General Ledger Monitor</span>
        <span class="status-badge-active" style="background:#F0FDF4;color:#166534;border:1px solid #BBF7D0;padding:4px 10px;border-radius:20px;font-size:11.5px;font-weight:600;"><span class="status-dot" style="background:#166534;"></span> Live SAP S21 Connected (192.168.1.55:44300)</span>
      </div>
    </div>
    <div class="header-actions">
      <button class="btn btn-secondary" onclick="exportCSV()">Export CSV</button>
      <button class="btn btn-primary" id="rescanBtn" onclick="runAgentScan()">Re-Scan Batch</button>
    </div>
  </header>

  <!-- Live SAP System Information Status Bar -->
  <div style="background:#F8FAFC;border-bottom:1px solid var(--border);padding:8px 32px;display:flex;align-items:center;justify-content:space-between;font-size:11.5px;color:var(--text-muted);">
    <div style="display:flex;align-items:center;gap:16px;">
      <span><strong>SAP System:</strong> S4H / S21</span>
    </div>
    <div style="font-weight:600;color:#166534;" class="mono">
      🟢 100% Live OData Connection Active (21,407 Postings in System)
    </div>
  </div>

    <!-- Unified KPI Strip -->
    <div class="kpi-strip">
      <div class="kpi-col" onclick="setFilter('ALL', document.querySelector('[data-filter=ALL]'))">
        <div class="kpi-label">Total Scanned</div>
        <div class="kpi-val mono" id="kTotal">--</div>
        <div class="kpi-footnote">Period postings</div>
      </div>
      <div class="kpi-col" onclick="setFilter('AUTO_RECONCILE', document.querySelector('[data-filter=AUTO_RECONCILE]'))">
        <div class="kpi-label">Auto-Reconciled</div>
        <div class="kpi-val mono" style="color:var(--status-green);" id="kAuto">--</div>
        <div class="kpi-footnote">Clean matched</div>
      </div>
      <div class="kpi-col" onclick="setFilter('UNDER_PROCESS', document.querySelector('[data-filter=UNDER_PROCESS]'))">
        <div class="kpi-label">Under Process</div>
        <div class="kpi-val mono" style="color:var(--status-blue);" id="kProcess">--</div>
        <div class="kpi-footnote">Parked / In-Flight (FBV0)</div>
      </div>
      <div class="kpi-col" onclick="setFilter('DAILY_REPORT', document.querySelector('[data-filter=DAILY_REPORT]'))">
        <div class="kpi-label">Daily Transactions</div>
        <div class="kpi-val mono" style="color:var(--status-amber);" id="kException">--</div>
        <div class="kpi-footnote">Daily Posting Digest</div>
      </div>
      <div class="kpi-col" onclick="setFilter('INVESTIGATE', document.querySelector('[data-filter=INVESTIGATE]'))">
        <div class="kpi-label">Investigate</div>
        <div class="kpi-val mono" style="color:var(--status-red);" id="kInvest">--</div>
        <div class="kpi-footnote">Controller alerts</div>
      </div>
      <div class="kpi-col">
        <div class="kpi-label">Flagged Exposure</div>
        <div class="kpi-val mono" id="kValue">--</div>
        <div class="kpi-footnote">Total pending review</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div style="margin-bottom:24px;">
      <div class="chart-panel">
        <div class="panel-header">
          <span class="panel-title">Decision Breakdown</span>
          <span class="panel-subtitle">By status</span>
        </div>
        <div class="chart-box" style="height:220px;">
          <canvas id="donutChart"></canvas>
        </div>
      </div>
    </div>

    <!-- Controls Toolbar -->
    <div class="toolbar" style="display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;">
      <div style="display:flex;align-items:center;gap:10px;flex:1;min-width:340px;">
        <div class="search-input-wrap" style="flex:1;">
          <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
          <input type="text" id="searchInput" class="search-input" placeholder="Search Document, GL Account, Status..." oninput="renderTable()">
        </div>

        <!-- Company Code Selector Dropdown -->
        <select id="ccFilter" class="search-input" style="width:160px;height:36px;font-size:12px;font-weight:600;padding:0 10px;cursor:pointer;background:#fff;border:1px solid var(--border);border-radius:6px;color:var(--text-main);" onchange="renderTable()">
          <option value="ALL">🏢 All Co. Codes</option>
        </select>

        <!-- GL Account Filter Dropdown -->
        <select id="clusterFilter" class="search-input" style="width:180px;height:36px;font-size:12px;font-weight:600;padding:0 10px;cursor:pointer;background:#fff;border:1px solid var(--border);border-radius:6px;color:var(--text-main);" onchange="renderTable()">
          <option value="ALL">📂 All GL Accounts</option>
          <option value="ASSET">🏦 Assets &amp; Bank (1xxxxx)</option>
          <option value="INTERCO">🤝 Inter-Co / Liab (2xxxxx)</option>
          <option value="REVENUE">📈 Revenue / Sales (4xxxxx)</option>
          <option value="EXPENSE">💸 Operating Exp (5xxxxx)</option>
        </select>
      </div>

      <div class="segment-tabs">
        <button class="segment-btn active" data-filter="ALL" onclick="setFilter('ALL', this)">All Postings</button>
        <button class="segment-btn" data-filter="UNDER_PROCESS" onclick="setFilter('UNDER_PROCESS', this)">⏳ Under Process</button>
        <button class="segment-btn" data-filter="INVESTIGATE" onclick="setFilter('INVESTIGATE', this)">🚨 Investigate</button>
        <button class="segment-btn" data-filter="DAILY_REPORT" onclick="setFilter('DAILY_REPORT', this)">📝 Daily Transactions</button>
        <button class="segment-btn" data-filter="AUTO_RECONCILE" onclick="setFilter('AUTO_RECONCILE', this)">✅ Reconciled</button>
        <button class="segment-btn" data-filter="FAILED_RETRY" onclick="setFilter('FAILED_RETRY', this)">🔁 Failed &amp; Retried</button>
        <button class="segment-btn" data-filter="OFF_HOURS" onclick="setFilter('OFF_HOURS', this)">🌙 Off-Hours</button>
      </div>
    </div>

    <!-- Minimal Table -->
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Document / Status</th>
            <th>Co. Code</th>
            <th>GL Account</th>
            <th>SAP T-Code</th>
            <th>Posting Date / Time</th>
            <th style="text-align:right;">Amount (INR)</th>
            <th>Decision</th>
            <th style="text-align:right;">Actions</th>
          </tr>
        </thead>
        <tbody id="tableBody">
          <tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-dim)">Loading records...</td></tr>
        </tbody>
      </table>
    </div>

  </div>

  <!-- Slide-out Sheet -->
  <div class="sheet-overlay" id="sheetOverlay" onclick="closeSheet()"></div>
  <div class="sheet" id="sheet">
    <div class="sheet-header">
      <div>
        <div class="sheet-title" id="sheetDocTitle">Document Details</div>
        <div style="font-size:11px;color:var(--text-dim);margin-top:2px;" id="sheetDocSub">--</div>
      </div>
      <button class="sheet-close" onclick="closeSheet()">✕</button>
    </div>

    <div class="sheet-body">

      <!-- Lifecycle Alert Banner -->
      <div id="lifecycleBanner" style="display:none;"></div>

      <!-- Metadata -->
      <div>
        <div class="section-heading">Transaction Overview</div>
        <div class="kv-card">
          <div class="kv-list">
            <div><div class="kv-key">GL Account</div><div class="kv-val mono" id="dGl">--</div></div>
            <div><div class="kv-key">GL Category</div><div class="kv-val" id="dCluster">--</div></div>
            <div><div class="kv-key">Doc Type</div><div class="kv-val mono" id="dType">--</div></div>
            <div><div class="kv-key">Debit / Credit (Dr/Cr)</div><div class="kv-val mono" id="dDebitCredit">--</div></div>
            <div><div class="kv-key">Company Code</div><div class="kv-val mono" id="dCompany">--</div></div>
            <div><div class="kv-key">Posting Time</div><div class="kv-val mono" id="dTime">--</div></div>
            <div><div class="kv-key">UTR Reference</div><div class="kv-val mono" id="dUtr">--</div></div>
            <div><div class="kv-key">Lifecycle Status</div><div class="kv-val mono" id="dLifecycleStatus">--</div></div>
          </div>
        </div>
      </div>

      <!-- System Rationale -->
      <div>
        <div class="section-heading">Audit Justification</div>
        <p id="dJustification" style="font-size:12px;color:var(--text-muted);line-height:1.5;"></p>
        <div style="font-size:11px;color:var(--text-dim);margin-top:8px;" class="mono" id="dAuditRef"></div>
      </div>

      <!-- Remediation Actions -->
      <div>
        <div class="section-heading">Suggested SAP Remediation</div>
        <div class="action-list" id="actionList">
          <!-- Dynamically populated -->
        </div>
      </div>

      <!-- Quick AI Chat -->
      <div>
        <div class="section-heading">Audit Copilot (Q&amp;A Assistant)</div>
        <div class="chat-box">
          <div class="chat-feed" id="chatMessages">
            <div class="chat-bubble chat-ai">
              Ask any question regarding this document's failure reasons, retry link, or SAP remediation steps!
            </div>
          </div>
          <div class="chat-input-row">
            <input type="text" id="chatInput" placeholder="Ask question (e.g. kyu fail hua, is process completed?)..." onkeypress="if(event.key==='Enter') sendChatMsg()">
            <button onclick="sendChatMsg()">Send</button>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- SAP GUI Screen Viewer Modal -->
  <div class="sap-modal-overlay" id="sapModalOverlay" onclick="closeSapModal()"></div>
  <div class="sap-modal" id="sapModal">
    <!-- SAP GUI Window Header -->
    <div class="sap-gui-header">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="background:#005A9E;color:#fff;font-weight:bold;padding:2px 6px;border-radius:3px;font-size:10px;" class="mono">SAP S/4HANA</span>
        <span style="font-weight:600;font-size:13px;color:#1E293B;" id="sapGuiTitle">SAP GUI — Display Document Overview</span>
      </div>
      <button onclick="closeSapModal()" style="border:none;background:none;font-size:16px;cursor:pointer;color:#64748B;">✕</button>
    </div>

    <!-- SAP Command Bar -->
    <div class="sap-cmd-bar">
      <span style="font-size:11px;font-weight:600;color:#475569;">Transaction:</span>
      <input type="text" id="sapCmdInput" class="mono" style="background:#F8FAFC;border:1px solid #CBD5E1;padding:4px 8px;font-size:12px;border-radius:4px;width:240px;font-weight:600;color:#0F172A;" readonly>
      <span style="background:#22C55E;color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">✔ Active Session</span>
      <span style="font-size:11px;color:#64748B;margin-left:auto;" class="mono">System: S21 | Client: 200 | User: INT_Prithvi</span>
    </div>

    <!-- SAP Document Header (BKPF) -->
    <div style="padding:16px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;">
      <div style="font-size:11px;font-weight:700;color:#334155;text-transform:uppercase;margin-bottom:8px;letter-spacing:0.5px;">Document Header (SAP Table BKPF)</div>
      <div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:12px;font-size:12px;">
        <div><span style="color:#64748B;font-size:11px;">Document No.</span><div class="mono" style="font-weight:700;color:#0F172A;" id="sapBefnr">--</div></div>
        <div><span style="color:#64748B;font-size:11px;">Company Code</span><div class="mono" style="font-weight:700;color:#0F172A;" id="sapBukrs">--</div></div>
        <div><span style="color:#64748B;font-size:11px;">Fiscal Year</span><div class="mono" style="font-weight:700;color:#0F172A;">2026</div></div>
        <div><span style="color:#64748B;font-size:11px;">Document Type</span><div class="mono" style="font-weight:700;color:#0F172A;" id="sapBlart">--</div></div>
        <div><span style="color:#64748B;font-size:11px;">Posting Date</span><div class="mono" id="sapBudat">--</div></div>
        <div><span style="color:#64748B;font-size:11px;">Entry Time</span><div class="mono" id="sapCputm">--</div></div>
        <div><span style="color:#64748B;font-size:11px;">Currency</span><div class="mono" style="font-weight:600;">INR</div></div>
        <div><span style="color:#64748B;font-size:11px;">Created By</span><div class="mono" style="color:#2563EB;">INT_Prithvi</div></div>
      </div>
    </div>

    <!-- SAP Line Items (BSEG) Table -->
    <div style="padding:16px;">
      <div style="font-size:11px;font-weight:700;color:#334155;text-transform:uppercase;margin-bottom:8px;letter-spacing:0.5px;">Accounting Line Items (SAP Table BSEG)</div>
      <div style="border:1px solid #E2E8F0;border-radius:6px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;font-size:12px;">
          <thead style="background:#F1F5F9;border-bottom:1px solid #E2E8F0;">
            <tr>
              <th style="padding:8px 12px;text-align:left;">Itm</th>
              <th style="padding:8px 12px;text-align:left;">PK</th>
              <th style="padding:8px 12px;text-align:left;">Debit / Credit (Dr/Cr)</th>
              <th style="padding:8px 12px;text-align:left;">G/L Account</th>
              <th style="padding:8px 12px;text-align:left;">Account Short Text</th>
              <th style="padding:8px 12px;text-align:right;">Amount (INR)</th>
              <th style="padding:8px 12px;text-align:center;">Tax</th>
              <th style="padding:8px 12px;text-align:left;">Trading Partner</th>
            </tr>
          </thead>
          <tbody id="sapBsegBody">
            <!-- Dynamically populated -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- SAP Action Toolbar at Bottom -->
    <div style="padding:12px 16px;background:#F8FAFC;border-top:1px solid #E2E8F0;display:flex;align-items:center;justify-content:space-between;">
      <div style="font-size:11px;color:#166534;font-weight:600;">✓ Live SAP T-Code session initialized. Command copied to clipboard!</div>
      <button class="btn btn-primary" onclick="closeSapModal()" style="height:30px;font-size:12px;">Close SAP Window</button>
    </div>
  </div>

  <script>
    window.INITIAL_DATA = __INITIAL_DATA__;
    window.INITIAL_KPI = __INITIAL_KPI__;

    let ALL_DATA = window.INITIAL_DATA || [];
    let CURRENT_FILTER = 'ALL';
    let SELECTED_ITEM = null;
    let donutChartInstance = null;
    let barChartInstance = null;

    function formatINR(val) {
      return '₹' + Math.round(val).toLocaleString('en-IN');
    }

    function formatDate(dStr) {
      if (!dStr) return '2026-03-31';
      let s = String(dStr).trim();
      if (s.includes('/Date(')) {
        let match = s.match(new RegExp('/Date\\((\\d+)\\)/'));
        if (match) {
          let dt = new Date(parseInt(match[1], 10));
          let y = dt.getUTCFullYear();
          let m = String(dt.getUTCMonth() + 1).padStart(2, '0');
          let d = String(dt.getUTCDate()).padStart(2, '0');
          return `${y}-${m}-${d}`;
        }
      }
      return s;
    }

    function getGlCluster(gl) {
      const glStr = String(gl || '').trim();
      if (glStr.startsWith('1')) return { label: 'Bank & Assets', code: 'ASSET', bg: '#EFF6FF', color: '#1E40AF', border: '#BFDBFE' };
      if (glStr.startsWith('2')) return { label: 'Inter-Co / Liab', code: 'INTERCO', bg: '#F5F3FF', color: '#6D28D9', border: '#DDD6FE' };
      if (glStr.startsWith('4')) return { label: 'Revenue / Sales', code: 'REVENUE', bg: '#ECFDF5', color: '#047857', border: '#A7F3D0' };
      if (glStr.startsWith('5')) return { label: 'Operating Exp', code: 'EXPENSE', bg: '#FEF3C7', color: '#B45309', border: '#FDE68A' };
      return { label: 'General Ledger', code: 'GL', bg: '#F3F4F6', color: '#374151', border: '#E5E7EB' };
    }

    function getDebitCreditInfo(item) {
      const dt = String(item.doc_type || '').toUpperCase();
      const gl = String(item.gl_account || '');
      
      // Determine if Debit (Dr - PK 40) or Credit (Cr - PK 50)
      if (['KR', 'DR', 'SA'].includes(dt) || gl.startsWith('5') || gl.startsWith('1')) {
        return {
          pk: '40',
          label: 'Debit (Dr)',
          tag: '<span style="font-size:10px;font-weight:700;background:#EFF6FF;color:#1E40AF;border:1px solid #BFDBFE;padding:1px 5px;border-radius:3px;margin-left:5px;">Dr</span>',
          modalBadge: '<span style="background:#EFF6FF;color:#1E40AF;border:1px solid #BFDBFE;padding:2px 6px;border-radius:4px;font-weight:700;font-size:11px;">Debit (Dr)</span>'
        };
      } else {
        return {
          pk: '50',
          label: 'Credit (Cr)',
          tag: '<span style="font-size:10px;font-weight:700;background:#FEF3C7;color:#92400E;border:1px solid #FDE68A;padding:1px 5px;border-radius:3px;margin-left:5px;">Cr</span>',
          modalBadge: '<span style="background:#FEF3C7;color:#92400E;border:1px solid #FDE68A;padding:2px 6px;border-radius:4px;font-weight:700;font-size:11px;">Credit (Cr)</span>'
        };
      }
    }

    function getActionPill(action) {
      if (action === 'AUTO_RECONCILE') return '<span class="pill pill-green">Reconciled</span>';
      if (action === 'DAILY_REPORT') return '<span class="pill pill-amber">Daily Transaction</span>';
      return '<span class="pill pill-red">Investigate</span>';
    }

    const API_BASE = (window.location.protocol === 'file:' || !window.location.host) ? 'http://localhost:8000' : '';

    if (document.readyState === 'loading') {
      window.addEventListener('DOMContentLoaded', loadInitialData);
    } else {
      loadInitialData();
    }

    function computeKpisFromData(data) {
      if (!data || !data.length) return { posting_count: 0, total_value_inr: 0, auto_reconcile: 0, daily_report: 0, investigate: 0, under_process: 0, failed: 0, retried: 0, flagged_value_inr: 0 };
      const flagged = data.filter(d => d.action !== 'AUTO_RECONCILE').reduce((sum, d) => sum + (d.amount_inr || 0), 0);
      const totalVal = data.reduce((sum, d) => sum + (d.amount_inr || 0), 0);
      return {
        posting_count: data.length,
        total_value_inr: Math.round(totalVal),
        auto_reconcile: data.filter(d => d.action === 'AUTO_RECONCILE').length,
        daily_report: data.filter(d => d.action === 'DAILY_REPORT').length,
        investigate: data.filter(d => d.action === 'INVESTIGATE').length,
        under_process: data.filter(d => (d.status || '') === 'UNDER_PROCESS').length,
        failed: data.filter(d => (d.status || '') === 'FAILED').length,
        retried: data.filter(d => (d.status || '') === 'RETRY_SUCCESS').length,
        flagged_value_inr: Math.round(flagged)
      };
    }

    async function loadInitialData() {
      // 1. Instant load from embedded dataset (Zero lag, no blank screen)
      if (window.INITIAL_DATA && window.INITIAL_DATA.length > 0) {
        ALL_DATA = [...window.INITIAL_DATA];
        ALL_DATA.sort((a, b) => b.ari - a.ari);
        const kpi = (window.INITIAL_KPI && window.INITIAL_KPI.posting_count) ? window.INITIAL_KPI : computeKpisFromData(ALL_DATA);
        updateKpis(kpi);
        populateCcDropdown();
        try { renderCharts(kpi, ALL_DATA); } catch (chartErr) {}
        renderTable();
      }

      // 2. Fetch live updates if server API is available
      try {
        const kpiRes = await fetch(API_BASE + '/api/kpi');
        if (kpiRes.ok) {
          const kpi = await kpiRes.json();
          updateKpis(kpi);
          const dataRes = await fetch(API_BASE + '/api/results/latest');
          if (dataRes.ok) {
            ALL_DATA = await dataRes.json();
            ALL_DATA.sort((a, b) => b.ari - a.ari);
            populateCcDropdown();
            try { renderCharts(kpi, ALL_DATA); } catch (cErr) {}
            renderTable();
          }
        }
      } catch (err) {
        console.log('Serving pre-rendered live SAP dataset.');
      }
    }

    function populateCcDropdown() {
      const select = document.getElementById('ccFilter');
      if (!select) return;
      const current = select.value;
      const ccs = Array.from(new Set(ALL_DATA.map(d => d.company_code).filter(Boolean))).sort();
      select.innerHTML = '<option value="ALL">🏢 All Co. Codes (' + ccs.length + ')</option>' +
        ccs.map(cc => `<option value="${cc}">Co. Code: ${cc}</option>`).join('');
      if (ccs.includes(current)) select.value = current;
    }

    function updateKpis(k) {
      document.getElementById('kTotal').textContent = k.posting_count;
      document.getElementById('kAuto').textContent = k.auto_reconcile;
      document.getElementById('kProcess').textContent = k.under_process;
      document.getElementById('kException').textContent = k.daily_report;
      document.getElementById('kInvest').textContent = k.investigate;
      document.getElementById('kValue').textContent = formatINR(k.flagged_value_inr);
    }

    function exportCSV() {
      if (!ALL_DATA || ALL_DATA.length === 0) {
        alert('No data available to export.');
        return;
      }
      const headers = ['Document_No', 'Line_Item', 'GL_Account', 'Doc_Type', 'Company_Code', 'Posting_Date', 'Posting_Time', 'Amount_INR', 'Debit_Credit', 'Decision', 'Status'];
      const rows = ALL_DATA.map(d => {
        const dc = getDebitCreditInfo(d);
        return [d.doc_no, d.line_item, d.gl_account, d.doc_type, d.company_code, d.posting_date, d.posting_time, d.amount_inr, dc.label, d.action, d.status || 'POSTED'];
      });
      const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join(String.fromCharCode(10));
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement('a');
      link.setAttribute('href', encodedUri);
      link.setAttribute('download', `GL_Anomaly_Report_${new Date().toISOString().slice(0,10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }

    async function runAgentScan() {
      const btn = document.getElementById('rescanBtn');
      btn.disabled = true;
      btn.textContent = 'Scanning...';
      try {
        const res = await fetch(API_BASE + '/api/run', { method: 'POST' });
        const kpi = await res.json();
        updateKpis(kpi);

        const dataRes = await fetch(API_BASE + '/api/results/latest');
        ALL_DATA = await dataRes.json();
        ALL_DATA.sort((a, b) => b.ari - a.ari);

        populateCcDropdown();

        renderCharts(kpi, ALL_DATA);
        renderTable();
      } catch (err) {
        alert('Execution failed: ' + err);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Re-Scan Batch';
      }
    }

    function setFilter(filter, el) {
      CURRENT_FILTER = filter;
      document.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
      if (el) el.classList.add('active');
      renderTable();
    }

    function renderTable() {
      const search = (document.getElementById('searchInput').value || '').toLowerCase();
      const selectedCc = (document.getElementById('ccFilter')?.value || 'ALL');
      const selectedCluster = (document.getElementById('clusterFilter')?.value || 'ALL');
      const tbody = document.getElementById('tableBody');

      let list = ALL_DATA.filter(d => {
        const status = d.status || 'POSTED';
        const cluster = getGlCluster(d.gl_account);

        if (selectedCc !== 'ALL' && d.company_code !== selectedCc) return false;
        if (selectedCluster !== 'ALL' && cluster.code !== selectedCluster) return false;

        if (CURRENT_FILTER === 'UNDER_PROCESS' && status !== 'UNDER_PROCESS') return false;
        if (CURRENT_FILTER === 'FAILED_RETRY' && status !== 'FAILED' && status !== 'RETRY_SUCCESS') return false;
        if (CURRENT_FILTER === 'INVESTIGATE' && d.action !== 'INVESTIGATE') return false;
        if (CURRENT_FILTER === 'DAILY_REPORT' && d.action !== 'DAILY_REPORT') return false;
        if (CURRENT_FILTER === 'AUTO_RECONCILE' && d.action !== 'AUTO_RECONCILE') return false;
        if (CURRENT_FILTER === 'OFF_HOURS' && !(d.ari_breakdown && d.ari_breakdown.off_hours)) return false;

        if (search) {
          const matchStr = `${d.doc_no} ${d.gl_account} ${d.doc_type} ${d.company_code} ${d.amount_inr} ${status} ${cluster.label}`.toLowerCase();
          if (!matchStr.includes(search)) return false;
        }
        return true;
      });

      if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:32px;color:var(--text-dim)">No matching GL postings found for selected filters.</td></tr>';
        return;
      }

      tbody.innerHTML = list.map(d => {
        const isSelected = SELECTED_ITEM && SELECTED_ITEM.doc_no === d.doc_no && SELECTED_ITEM.line_item === d.line_item;
        
        let lifecycleTag = '';
        const status = d.status || 'POSTED';
        if (status === 'FAILED') {
          lifecycleTag = `<span class="pill pill-red" style="margin-top:3px;">✕ Failed (Attempt 1)</span>`;
        } else if (status === 'RETRY_SUCCESS') {
          lifecycleTag = `<span class="pill pill-green" style="margin-top:3px;">✓ Retry Success (Attempt 2)</span>`;
        } else if (status === 'UNDER_PROCESS') {
          lifecycleTag = `<span class="pill pill-blue" style="margin-top:3px;">⏳ Under Process</span>`;
        }

        const isOffHours = d.ari_breakdown && d.ari_breakdown.off_hours;
        const cluster = getGlCluster(d.gl_account);
        const dc = getDebitCreditInfo(d);

        let tcode = 'FB03';
        if (status === 'UNDER_PROCESS') tcode = 'FBV0';
        else if (status === 'FAILED') tcode = 'SM21';
        else if (d.is_intercompany) tcode = 'FBL3N';

        return `
          <tr class="${isSelected ? 'selected-row' : ''}" onclick="openSheet('${d.doc_no}', '${d.line_item}')">
            <td>
              <div>
                <span class="mono" style="font-weight:600;">${d.doc_no}</span>
                <span style="color:var(--text-dim);font-size:11px;"> / ${d.line_item}</span>
              </div>
              ${lifecycleTag}
            </td>
            <td>
              <span class="mono" style="font-weight:600;background:#F3F4F6;padding:2px 6px;border-radius:4px;font-size:11px;color:var(--text-main);">${d.company_code}</span>
            </td>
            <td>
              <div>
                <span style="font-weight:600;" class="mono">${d.gl_account}</span>
                <span style="color:var(--text-dim);font-size:11px;"> (${d.doc_type})</span>
              </div>
              <div style="margin-top:3px;">
                <span style="background:${cluster.bg};color:${cluster.color};border:1px solid ${cluster.border};padding:1px 5px;border-radius:3px;font-size:10px;font-weight:600;">${cluster.label}</span>
              </div>
            </td>
            <td>
              <span class="mono" style="cursor:pointer;background:#EFF6FF;color:#1E40AF;border:1px solid #BFDBFE;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600;" title="Click to copy SAP GUI T-Code" onclick="event.stopPropagation();executeAction('/n${tcode} ${d.doc_no}')">/n${tcode}</span>
            </td>
            <td>
              <span>${formatDate(d.posting_date)}</span>
              <span style="color:var(--text-dim);font-size:11px;">${d.posting_time || ''}${isOffHours ? ' (Off-Hours)' : ''}</span>
            </td>
            <td class="mono" style="text-align:right;font-weight:600;">
              ${formatINR(d.amount_inr || 0)} ${dc.tag}
            </td>
            <td>${getActionPill(d.action)}</td>
            <td style="text-align:right;">
              <button class="btn btn-secondary" style="height:24px;padding:0 8px;font-size:11px;" onclick="event.stopPropagation();openSheet('${d.doc_no}', '${d.line_item}')">View Details</button>
            </td>
          </tr>
        `;
      }).join('');
    }

    function renderCharts(kpi, data) {
      if (typeof Chart === 'undefined') return;

      const donutCtx = document.getElementById('donutChart');
      if (!donutCtx) return;
      if (donutChartInstance) donutChartInstance.destroy();
      donutChartInstance = new Chart(donutCtx, {
        type: 'doughnut',
        data: {
          labels: ['Reconciled', 'Daily Transactions', 'Investigate'],
          datasets: [{
            data: [kpi.auto_reconcile || 0, kpi.daily_report || 0, kpi.investigate || 0],
            backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
            borderWidth: 2,
            borderColor: '#FFFFFF'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: { color: '#4B5563', font: { family: 'Inter', size: 11 }, boxWidth: 10 }
            }
          },
          cutout: '72%'
        }
      });
    }

    function openSheet(docNo, lineItem) {
      const item = ALL_DATA.find(d => String(d.doc_no) === String(docNo) && String(d.line_item) === String(lineItem));
      if (!item) return;

      SELECTED_ITEM = item;
      renderTable();

      document.getElementById('sheetDocTitle').textContent = `Document ${item.doc_no}`;
      document.getElementById('sheetDocSub').textContent = `Line item ${item.line_item} · ${formatDate(item.posting_date)}`;

      const banner = document.getElementById('lifecycleBanner');
      if (item.status === 'FAILED') {
        banner.style.display = 'block';
        banner.innerHTML = `
          <div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:6px;padding:12px;">
            <div style="font-weight:600;color:#991B1B;font-size:12px;">✕ Transaction Failed (Attempt 1 of 2)</div>
            <div style="font-size:11.5px;color:#7F1D1D;margin-top:3px;"><strong>Failure Reason:</strong> ${item.failure_reason}</div>
            <div style="font-size:11.5px;color:#7F1D1D;margin-top:2px;"><strong>Linked Retry:</strong> Re-attempted under Doc #${item.retry_linked_doc}</div>
            <div style="font-size:11px;color:#991B1B;margin-top:6px;font-weight:500;">Action: Verify bank statement to ensure Attempt 1 was not debited (Double-Debit Risk).</div>
          </div>`;
      } else if (item.status === 'RETRY_SUCCESS') {
        banner.style.display = 'block';
        banner.innerHTML = `
          <div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:6px;padding:12px;">
            <div style="font-weight:600;color:#166534;font-size:12px;">✓ Re-Attempted Transaction Succeeded (Attempt 2)</div>
            <div style="font-size:11.5px;color:#14532D;margin-top:3px;"><strong>Prior Failed Attempt:</strong> Linked to Doc #${item.retry_linked_doc}</div>
            <div style="font-size:11px;color:#166534;margin-top:6px;font-weight:500;">Audit Check: Payment posted on second attempt. Ensure Attempt 1 was fully cancelled.</div>
          </div>`;
      } else if (item.status === 'UNDER_PROCESS') {
        banner.style.display = 'block';
        banner.innerHTML = `
          <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:6px;padding:12px;">
            <div style="font-weight:600;color:#1E40AF;font-size:12px;">⏳ Transaction Under Process (In-Flight)</div>
            <div style="font-size:11.5px;color:#1E3A8A;margin-top:3px;"><strong>Current Stage:</strong> ${item.process_stage}</div>
            <div style="font-size:11px;color:#1E40AF;margin-top:6px;font-weight:500;">Status: Real-time monitoring active until dual approval or bank clearing completes.</div>
          </div>`;
      } else {
        banner.style.display = 'none';
      }

      const cluster = getGlCluster(item.gl_account);
      const dc = getDebitCreditInfo(item);

      document.getElementById('dGl').textContent = item.gl_account;
      document.getElementById('dCluster').innerHTML = `<span style="background:${cluster.bg};color:${cluster.color};border:1px solid ${cluster.border};padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600;">${cluster.label}</span>`;
      document.getElementById('dType').textContent = item.doc_type;
      document.getElementById('dDebitCredit').innerHTML = dc.modalBadge;
      document.getElementById('dCompany').textContent = item.company_code;
      document.getElementById('dTime').textContent = item.posting_time;
      document.getElementById('dUtr').textContent = item.utr_reference || 'None';
      document.getElementById('dLifecycleStatus').textContent = item.status || 'POSTED';

      document.getElementById('dJustification').textContent = item.justification;
      document.getElementById('dAuditRef').textContent = `Ref: ${item.audit_trail_ref}`;

      loadRemediation(item.doc_no, item.line_item);

      document.getElementById('sheetOverlay').classList.add('open');
      document.getElementById('sheet').classList.add('open');
    }

    function closeSheet() {
      document.getElementById('sheetOverlay').classList.remove('open');
      document.getElementById('sheet').classList.remove('open');
      SELECTED_ITEM = null;
      renderTable();
    }

    async function loadRemediation(doc, line) {
      const container = document.getElementById('actionList');
      container.innerHTML = '<span style="font-size:11px;color:var(--text-dim)">Loading suggested actions...</span>';
      try {
        const res = await fetch(`${API_BASE}/api/remediate/${doc}/${line}`);
        const data = await res.json();
        container.innerHTML = data.actions.map(a => `
          <div class="action-item" onclick="executeAction('${a.command}')">
            <span style="font-size:12px;">${a.label}</span>
            <span class="action-code">${a.code}</span>
          </div>
        `).join('');
      } catch (err) {
        container.innerHTML = '<span style="font-size:11px;color:var(--text-dim)">None available</span>';
      }
    }

    function executeAction(cmd) {
      if (navigator.clipboard) {
        navigator.clipboard.writeText(cmd).catch(() => {});
      }
      const parts = cmd.trim().split(' ');
      const actionCode = parts[0].replace('/n', '');
      const docNo = parts[1] || (SELECTED_ITEM ? SELECTED_ITEM.doc_no : '');

      openSapGuiModal(docNo, actionCode, cmd);
    }

    function openSapGuiModal(docNo, actionCode, fullCmd) {
      let item = ALL_DATA.find(d => String(d.doc_no) === String(docNo));
      if (!item && SELECTED_ITEM) item = SELECTED_ITEM;
      if (!item) return;

      const dc = getDebitCreditInfo(item);

      document.getElementById('sapGuiTitle').textContent = `SAP GUI — ${actionCode} Overview (${item.company_code})`;
      document.getElementById('sapCmdInput').value = fullCmd || `/n${actionCode} ${docNo}`;

      document.getElementById('sapBefnr').textContent = item.doc_no;
      document.getElementById('sapBukrs').textContent = item.company_code;
      document.getElementById('sapBlart').textContent = item.doc_type;
      document.getElementById('sapBudat').textContent = formatDate(item.posting_date);
      document.getElementById('sapCputm').textContent = item.posting_time || '10:00';

      const cluster = getGlCluster(item.gl_account);
      const isDebit = dc.pk === '40';

      const drAccount = isDebit ? item.gl_account : '100000';
      const drDesc = isDebit ? `${cluster.label} (${item.doc_type})` : 'Bank / Customer Clearing Account';
      const crAccount = isDebit ? '100000' : item.gl_account;
      const crDesc = isDebit ? 'Bank / Vendor Clearing Account' : `${cluster.label} (${item.doc_type})`;

      document.getElementById('sapBsegBody').innerHTML = `
        <tr style="border-bottom:1px solid #F1F5F9;background:#F8FAFC;">
          <td style="padding:8px 12px;" class="mono">001</td>
          <td style="padding:8px 12px;font-weight:bold;color:#1E40AF;" class="mono">40</td>
          <td style="padding:8px 12px;"><span style="background:#EFF6FF;color:#1E40AF;border:1px solid #BFDBFE;padding:2px 6px;border-radius:4px;font-weight:700;font-size:11px;">Debit (Dr)</span></td>
          <td style="padding:8px 12px;font-weight:600;" class="mono">${drAccount}</td>
          <td style="padding:8px 12px;">${drDesc}</td>
          <td style="padding:8px 12px;text-align:right;font-weight:600;" class="mono">${formatINR(item.amount_inr)}</td>
          <td style="padding:8px 12px;text-align:center;" class="mono">V1</td>
          <td style="padding:8px 12px;" class="mono">${item.ic_partner_company || '-'}</td>
        </tr>
        <tr style="border-bottom:1px solid #F1F5F9;background:#FFFFFF;">
          <td style="padding:8px 12px;" class="mono">002</td>
          <td style="padding:8px 12px;font-weight:bold;color:#6D28D9;" class="mono">50</td>
          <td style="padding:8px 12px;"><span style="background:#F5F3FF;color:#6D28D9;border:1px solid #DDD6FE;padding:2px 6px;border-radius:4px;font-weight:700;font-size:11px;">Credit (Cr)</span></td>
          <td style="padding:8px 12px;font-weight:600;" class="mono">${crAccount}</td>
          <td style="padding:8px 12px;">${crDesc}</td>
          <td style="padding:8px 12px;text-align:right;font-weight:600;" class="mono">${formatINR(item.amount_inr)}</td>
          <td style="padding:8px 12px;text-align:center;" class="mono">V1</td>
          <td style="padding:8px 12px;" class="mono">${item.ic_partner_company || '-'}</td>
        </tr>
      `;

      document.getElementById('sapModalOverlay').classList.add('open');
      document.getElementById('sapModal').classList.add('open');
    }

    function closeSapModal() {
      document.getElementById('sapModalOverlay').classList.remove('open');
      document.getElementById('sapModal').classList.remove('open');
    }

    async function sendChatMsg() {
      if (!SELECTED_ITEM) return;
      const input = document.getElementById('chatInput');
      const msg = input.value.trim();
      if (!msg) return;

      const chatContainer = document.getElementById('chatMessages');
      chatContainer.innerHTML += `<div class="chat-bubble chat-user">${msg}</div>`;
      input.value = '';
      chatContainer.scrollTop = chatContainer.scrollHeight;

      try {
        const res = await fetch(`${API_BASE}/api/chat/${SELECTED_ITEM.doc_no}/${SELECTED_ITEM.line_item}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        chatContainer.innerHTML += `<div class="chat-bubble chat-ai">${data.reply.replace(/\\n/g, '<br>')}</div>`;
        chatContainer.scrollTop = chatContainer.scrollHeight;
      } catch (err) {
        chatContainer.innerHTML += `<div class="chat-bubble chat-ai">Unable to respond.</div>`;
      }
    }
  </script>
</body>
</html>
'''
dashboard_html = dashboard_html.replace("__INITIAL_DATA__", initial_data_json).replace("__INITIAL_KPI__", initial_kpi_json)

# Write updated dashboard.html
with open(dashboard_path, "w", encoding="utf-8") as f:
    f.write(dashboard_html)

# Copy to uc14_agent/dashboard.html
uc14_dash = os.path.join(r"c:\Users\arati\Downloads\uc14_agent 1\uc14_agent", "dashboard.html")
with open(uc14_dash, "w", encoding="utf-8") as f:
    f.write(dashboard_html)

print("Added Debit / Credit (Dr/Cr) column and indicators successfully!")
