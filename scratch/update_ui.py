"""
Script to update app.py with enhanced Risk Calculation Guide modal, GL Account Clustering, 
and detailed step-by-step ARI breakdown card in the inspection drawer.
"""
import re

app_path = r"c:\Users\arati\Downloads\uc14_agent 1\uc14_agent\ui\app.py"
dashboard_path = r"c:\Users\arati\Downloads\uc14_agent 1\dashboard.html"

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

print(f"Current app.py length: {len(content)} bytes")
