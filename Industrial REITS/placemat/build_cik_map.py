

import json
import os
import re
import requests

OUT_DIR = "data/cik"
OUT_PATH = os.path.join(OUT_DIR, "ticker_cik_map.json")

SEC_TICKER_CIK_URL = "https://www.sec.gov/files/company_tickers.json"

def normalize_ticker(t: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", t.upper().strip())

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    headers = {
        # SEC requests a real UA with contact info
        "User-Agent": "IndustrialREITPlacemat/1.0 (tyler@example.com)",
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov",
    }
    r = requests.get(SEC_TICKER_CIK_URL, headers=headers, timeout=30)
    r.raise_for_status()
    raw = r.json()

    mapping = {}
    # company_tickers.json is a dict keyed by integer-ish strings
    for _, row in raw.items():
        ticker = normalize_ticker(row["ticker"])
        cik_str = str(row["cik_str"]).zfill(10)
        mapping[ticker] = cik_str

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

    print(f"[OK] Wrote {OUT_PATH} | tickers={len(mapping)}")

if __name__ == "__main__":
    main()

