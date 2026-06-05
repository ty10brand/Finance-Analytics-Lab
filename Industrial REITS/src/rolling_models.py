

import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

PROCESSED_DIR = "data/processed"
OUT_TABLES = "outputs/tables"
OUT_CHARTS = "outputs/charts"

def rolling_ols(y, X, window=52):
    betas = []
    idx = []
    for i in range(window, len(y) + 1):
        ys = y.iloc[i-window:i]
        Xs = X.iloc[i-window:i]
        Xc = sm.add_constant(Xs)
        model = sm.OLS(ys, Xc, missing="drop").fit()
        betas.append(model.params)
        idx.append(y.index[i-1])
    out = pd.DataFrame(betas, index=idx)
    return out

def main():
    os.makedirs(OUT_TABLES, exist_ok=True)
    os.makedirs(OUT_CHARTS, exist_ok=True)

    panel = pd.read_csv(os.path.join(PROCESSED_DIR, "weekly_panel.csv"), index_col=0, parse_dates=True)

    mkt = "SPY"
    rate = "d_DGS10"
    credit = "d_BAA10Y"

    if mkt not in panel.columns:
        raise ValueError("SPY not found in weekly_panel.csv (check tickers.yaml)")

    factors = [mkt]
    if rate in panel.columns: factors.append(rate)
    if credit in panel.columns: factors.append(credit)

    ticker_cols = [c for c in panel.columns if c.isalpha() and c.upper() == c and c not in factors and not c.startswith("d_")]

    window = 52
    for t in ticker_cols:
        if t in ["SPY", "VNQ"]:
            continue

        y = panel[t].dropna()
        X = panel.loc[y.index, factors].dropna()
        y = y.loc[X.index]

        if len(y) < window + 20:
            continue

        betas = rolling_ols(y, X, window=window)
        betas_path = os.path.join(OUT_TABLES, f"rolling_betas_{t}.csv")
        betas.to_csv(betas_path)

        # Plot market beta and rate sensitivity (if available)
        plt.figure()
        if mkt in betas.columns:
            plt.plot(betas.index, betas[mkt], label="Market beta (SPY)")
        if rate in betas.columns:
            plt.plot(betas.index, betas[rate], label="Rate sensitivity (Δ10Y)")
        plt.title(f"{t}: Rolling {window}-week sensitivities")
        plt.legend()
        plt.tight_layout()
        fig_path = os.path.join(OUT_CHARTS, f"rolling_{t}.png")
        plt.savefig(fig_path, dpi=160)
        plt.close()

        print(f"[OK] {t} rolling outputs → {betas_path} and {fig_path}")

if __name__ == "__main__":
    main()


