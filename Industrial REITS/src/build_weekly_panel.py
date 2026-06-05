

import os
import pandas as pd
import numpy as np

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

def to_weekly_last(df):
    return df.resample("W-FRI").last()

def pct_change(df):
    return df.pct_change()

def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    prices = pd.read_csv(os.path.join(RAW_DIR, "prices_daily.csv"), index_col=0, parse_dates=True)
    fred = pd.read_csv(os.path.join(RAW_DIR, "fred_daily.csv"), index_col=0, parse_dates=True)

    # Weekly prices → weekly returns
    prices_w = to_weekly_last(prices)
    rets_w = pct_change(prices_w)

    # Weekly macro
    fred_w = to_weekly_last(fred)

    # Rate changes in DECIMAL terms:
    # yields/spreads are in percent; convert weekly changes from % to decimal:
    # Example: +0.10% (10 bps) becomes 0.0010 in decimal
    rate_cols = [c for c in fred_w.columns if c in ["DGS10", "DGS2", "BAA10Y"]]
    macro = pd.DataFrame(index=fred_w.index)

    for c in rate_cols:
        macro[f"d_{c}"] = fred_w[c].diff() / 100.0  # percent → decimal change

    # Term spread (10Y-2Y) in decimal, and its weekly change
    if "DGS10" in fred_w.columns and "DGS2" in fred_w.columns:
        term_spread = (fred_w["DGS10"] - fred_w["DGS2"]) / 100.0
        macro["term_spread"] = term_spread
        macro["d_term_spread"] = term_spread.diff()

    # Optional: YoY inflation and YoY industrial production growth (monthly series; forward filled)
    for c in ["CPIAUCSL", "INDPRO"]:
        if c in fred.columns:
            # Monthly series: compute YoY change at monthly frequency, then align to weekly
            s = fred[c].dropna()
            yoy = s.pct_change(12)
            yoy_w = yoy.resample("W-FRI").ffill()
            macro[f"yoy_{c}"] = yoy_w

    panel = rets_w.join(macro, how="inner").dropna()

    panel_path = os.path.join(PROCESSED_DIR, "weekly_panel.csv")
    panel.to_csv(panel_path)
    print(f"[OK] Wrote {panel_path} | shape={panel.shape}")

if __name__ == "__main__":
    main()



