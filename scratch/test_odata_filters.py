import requests
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()

url = "https://192.168.1.55:44300/sap/opu/odata/sap/ZGLANOMALYV_CDS/ZGLANOMALYV"

# Credentials to test
creds = [
    ("Int_Arti", "Welcome@12345"),
    ("INT_Prithvi", "Pst@576400")
]

filters = [
    "CompanyCode eq 'GT01'",
    "", # No filter
]

for u, p in creds:
    print(f"\n================ USER: {u} ================")
    for f in filters:
        params = {"sap-client": "200", "$top": "500"}
        if f:
            params["$filter"] = f
        try:
            r = requests.get(url, auth=HTTPBasicAuth(u, p), verify=False, timeout=10, params=params, headers={"Accept": "application/json"})
            if r.status_code == 200:
                data = r.json().get("d", {}).get("results", [])
                ccs = set(x.get("CompanyCode") for x in data)
                doc_types = set(x.get("AccountingDocumentType") for x in data)
                print(f"Filter: '{f}' => 200 OK | Records: {len(data)} | CoCodes: {sorted(list(ccs))} | DocTypes: {sorted(list(doc_types))}")
            else:
                print(f"Filter: '{f}' => HTTP {r.status_code}")
        except Exception as err:
            print(f"Filter: '{f}' => Error: {err}")
