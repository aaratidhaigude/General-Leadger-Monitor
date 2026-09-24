import requests
from requests.auth import HTTPBasicAuth

requests.packages.urllib3.disable_warnings()

v2_url = "https://192.168.1.55:44300/sap/opu/odata/sap/ZGLANOMALYV_CDS/ZGLANOMALYV"

creds = [
    ("INT_Prithvi", "Pst@576400"),
    ("Int_Arti", "Welcome@12345")
]

for user, pwd in creds:
    print(f"Testing User: {user} ...")
    try:
        r = requests.get(
            v2_url,
            auth=HTTPBasicAuth(user, pwd),
            verify=False,
            timeout=10,
            params={"sap-client": "200", "$filter": "CompanyCode eq 'GT01'", "$top": "500"},
            headers={"Accept": "application/json"}
        )
        print(f"User: {user} | Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json().get("d", {}).get("results", [])
            print(f"   SUCCESS! Records: {len(data)}")
    except Exception as e:
        print(f"User: {user} | Error: {e}")
