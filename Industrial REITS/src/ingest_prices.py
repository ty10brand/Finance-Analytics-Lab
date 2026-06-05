

import os
import yaml
import pandas as pd
import yfinance as yf

DATA_DIR = "data/raw"

def load_tickers(path="config/tickers.yaml"):
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    reits = cfg.get("reits", [])
    benchmarks = cfg.get("benchmarks", [])
    return sorted(set(reits + benchmarks))

def download_prices(tickers, start="2010-01-01"):
    df = yf.download(
        tickers=tickers,
        start=start,
        auto_adjust=True,
        progress=False
    )["Close"]
    if isinstance(df, pd.Series):
        df = df.to_frame()
    df = df.dropna(how="all")
    df.columns = [c.upper() for c in df.columns]
    return df

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    tickers = load_tickers()
    prices = download_prices(tickers)
    outpath = os.path.join(DATA_DIR, "prices_daily.csv")
    prices.to_csv(outpath)
    print(f"[OK] Wrote {outpath} | shape={prices.shape}")

if __name__ == "__main__":
    main()


