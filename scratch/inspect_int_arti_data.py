import requests
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()

url = "https://192.168.1.55:44300/sap/opu/odata/sap/ZGLANOMALYV_CDS/ZGLANOMALYV"
user = "Int_Arti"
pwd = "Welcome@12345"

# 1. Fetch top 500 without company code filter to see available company codes
res = requests.get(
    url,
    auth=HTTPBasicAuth(user, pwd),
    verify=False,
    timeout=10,
    params={"sap-client": "200", "$top": "500"},
    headers={"Accept": "application/json"}
)

if res.status_code == 200:
    results = res.json().get("d", {}).get("results", [])
    print(f"Total live records fetched for User {user}: {len(results)}")
    
    company_codes = set(r.get("CompanyCode") for r in results if r.get("CompanyCode"))
    doc_types = set(r.get("AccountingDocumentType") for r in results if r.get("AccountingDocumentType"))
    
    print("Available Company Codes:", sorted(list(company_codes)))
    print("Available Accounting Document Types:", sorted(list(doc_types)))
    
    # Check CompanyCode GT01 specifically
    gt01_records = [r for r in results if r.get("CompanyCode") == "GT01"]
    print(f"\nGT01 Record Count: {len(gt01_records)}")
    if gt01_records:
        gt01_doc_types = set(r.get("AccountingDocumentType") for r in gt01_records)
        print("GT01 Document Types:", sorted(list(gt01_doc_types)))
        print("Sample GT01 Record:", gt01_records[0])
else:
    print(f"Error HTTP {res.status_code}: {res.text}")
