import requests
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()

users = ["Int_Arti", "INT_ARTI", "int_arti", "INT_Prithvi"]
passwords = ["Welcome@12345", "Pst@576400"]

v4_url = "http://192.168.1.55:8000/sap/opu/odata4/sap/z_gl_anomaly_sb/srvd_a2x/sap/z_gl_anomaly_sd/0001/GLAnomalyData?sap-client=200&$top=10"
v2_url = "https://192.168.1.55:44300/sap/opu/odata/sap/ZGLANOMALYV_CDS/ZGLANOMALYV?sap-client=200&$top=5"

print("--- TESTING SAP OData V4 (http://192.168.1.55:8000) ---")
for u in users:
    for p in passwords:
        try:
            r = requests.get(v4_url, auth=HTTPBasicAuth(u, p), timeout=5, headers={"Accept": "application/json"})
            print(f"V4 | User: {u} | Pass: {p} => Status: {r.status_code}")
            if r.status_code == 200:
                print("   V4 SUCCESS Payload sample:", r.json())
        except Exception as e:
            print(f"V4 | User: {u} | Pass: {p} => Error: {e}")

print("\n--- TESTING SAP OData V2 (https://192.168.1.55:44300) ---")
for u in users:
    for p in passwords:
        try:
            r = requests.get(v2_url, auth=HTTPBasicAuth(u, p), verify=False, timeout=5, headers={"Accept": "application/json"})
            print(f"V2 | User: {u} | Pass: {p} => Status: {r.status_code}")
            if r.status_code == 200:
                results = r.json().get("d", {}).get("results", [])
                print(f"   V2 SUCCESS! Records fetched: {len(results)}")
        except Exception as e:
            print(f"V2 | User: {u} | Pass: {p} => Error: {e}")
