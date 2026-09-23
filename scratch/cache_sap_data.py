import os
import sys
import json
import requests
from requests.auth import HTTPBasicAuth

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings()

url = "https://192.168.1.55:44300/sap/opu/odata/sap/ZGLANOMALYV_CDS/ZGLANOMALYV"
credentials = [
    ("INT_Prithvi", "Pst@576400"),
    ("Int_Arti", "Welcome@12345")
]

data = []
for u, p in credentials:
    try:
        print(f"Connecting to SAP S21 with user '{u}'...")
        res = requests.get(
            url,
            auth=HTTPBasicAuth(u, p),
            verify=False,
            timeout=10,
            params={"sap-client": "200", "$filter": "CompanyCode eq 'GT01'", "$top": "500"},
            headers={"Accept": "application/json"}
        )
        if res.status_code == 200:
            data = res.json().get("d", {}).get("results", [])
            print(f"Successfully fetched {len(data)} LIVE records from SAP S21 for user '{u}'!")
            break
        else:
            print(f"HTTP {res.status_code} for user {u}")
    except Exception as err:
        print(f"Connection error for {u}: {err}")

from datetime import datetime, timezone

def clean_date(val):
    if not val: return '2026-03-31'
    val_str = str(val).strip()
    if '/Date(' in val_str:
        try:
            ts_str = val_str.split('/Date(')[1].split(')/')[0]
            ts_ms = int(ts_str.replace('+', '-').split('-')[0])
            dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return '2026-03-31'
    return val_str

if data:
    for rec in data:
        rec['PostingDate'] = clean_date(rec.get('PostingDate'))

    target_paths = [
        r"c:\Users\arati\Downloads\uc14_agent 1\uc14_agent\data\sap_live_cache.json",
        r"c:\Users\arati\Downloads\uc14_agent 1\data\sap_live_cache.json"
    ]
    for path in target_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(data)} records to {path}")
else:
    print("Failed to fetch live data from SAP.")
