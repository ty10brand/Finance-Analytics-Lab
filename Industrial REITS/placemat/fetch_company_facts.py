

import json
import os
import requests

OUT_DIR = "data/sec_facts"
SEC_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

def fetch_company_facts(cik: str, user_agent: str) -> dict:
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov",
    }
    url = SEC_FACTS_URL.format(cik=cik)
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--cik", required=True, help="10-digit CIK (zero padded)")
    p.add_argument("--user-agent", required=True, help="e.g. Name/Project (email@domain.com)")
    args = p.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    data = fetch_company_facts(args.cik, args.user_agent)

    outpath = os.path.join(OUT_DIR, f"companyfacts_{args.cik}.json")
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(data, f)

    print(f"[OK] Wrote {outpath}")

if __name__ == "__main__":
    main()

