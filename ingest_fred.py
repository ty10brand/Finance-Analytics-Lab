

import os
import yaml
import pandas as pd
import requests

DATA_DIR = "data/raw"

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"

def load_fred_series(path="config/fred_series.yaml"):
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    return list(cfg.keys())

def fetch_fred_series(series_id: str, session: requests.Session) -> pd.Series:
    url = FRED_CSV_URL.format(series_id=series_id)
    r = session.get(url, timeout=30)
    r.raise_for_status()

    text = r.text.strip()

    # If FRED returns an HTML page (rate-limited, blocked, blocked by network, etc.), fail loudly with context
    if text[:15].lower().startswith("<!doctype html") or "<html" in text[:200].lower():
        raise RuntimeError(
            f"FRED returned HTML instead of CSV for {series_id}. "
            f"First 200 chars:\n{text[:200]}"
        )

    from io import StringIO
    df = pd.read_csv(StringIO(text))

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Find the date column (FRED commonly uses 'observation_date' for this endpoint)
    date_col = None
    for c in df.columns:
        cu = c.strip().lower()
        if cu in ("date", "observation_date"):
            date_col = c
            break

    if date_col is None:
        raise RuntimeError(
            f"Could not find date column for {series_id}. Columns={df.columns.tolist()} "
            f"First 200 chars:\n{text[:200]}"
        )

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.set_index(date_col)

    # The value column is usually the series_id; handle casing differences safely
    value_col = None
    for c in df.columns:
        if c.strip().upper() == series_id.upper():
            value_col = c
            break

    if value_col is None:
        # Fall back: pick the first non-date column
        non_date_cols = [c for c in df.columns if c != date_col]
        if not non_date_cols:
            raise RuntimeError(
                f"No value column found for {series_id}. Columns={df.columns.tolist()} "
                f"First 200 chars:\n{text[:200]}"
            )
        value_col = non_date_cols[0]

    s = pd.to_numeric(df[value_col], errors="coerce")  # '.' becomes NaN
    s.name = series_id
    return s

def download_fred(series_ids, start="2010-01-01") -> pd.DataFrame:
    start = pd.to_datetime(start)
    with requests.Session() as session:
        series_list = []
        for sid in series_ids:
            s = fetch_fred_series(sid, session)
            s = s.loc[s.index >= start]
            series_list.append(s)
    df = pd.concat(series_list, axis=1).sort_index()
    return df

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    series_ids = load_fred_series()
    fred = download_fred(series_ids)

    outpath = os.path.join(DATA_DIR, "fred_daily.csv")
    fred.to_csv(outpath)
    print(f"[OK] Wrote {outpath} | shape={fred.shape}")

if __name__ == "__main__":
    main()


