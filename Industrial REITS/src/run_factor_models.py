

import os
import pandas as pd
import numpy as np
import statsmodels.api as sm

PROCESSED_DIR = "data/processed"
OUT_TABLES = "outputs/tables"

def ols(y, X):
    Xc = sm.add_constant(X)
    model = sm.OLS(y, Xc, missing="drop").fit()
    return model

def main():
    os.makedirs(OUT_TABLES, exist_ok=True)
    panel = pd.read_csv(os.path.join(PROCESSED_DIR, "weekly_panel.csv"), index_col=0, parse_dates=True)

    # Factor choices
    mkt = "SPY"
    factors = []
    if "d_DGS10" in panel.columns: factors.append("d_DGS10")
    if "d_BAA10Y" in panel.columns: factors.append("d_BAA10Y")
    if "d_term_spread" in panel.columns: factors.append("d_term_spread")
    # Optional macro
    if "yoy_CPIAUCSL" in panel.columns: factors.append("yoy_CPIAUCSL")
    if "yoy_INDPRO" in panel.columns: factors.append("yoy_INDPRO")

    # Target REITs are columns that look like tickers but not benchmarks
    drop_cols = set(factors + [mkt])
    ticker_cols = [c for c in panel.columns if c.isalpha() and c.upper() == c and c not in drop_cols]

    results = []
    for t in ticker_cols:
        if t in ["SPY", "VNQ"]:
            continue
        y = panel[t]
        X = panel[[mkt] + factors].copy()
        model = ols(y, X)

        row = {
            "ticker": t,
            "n_obs": int(model.nobs),
            "r2": float(model.rsquared),
            "alpha_weekly": float(model.params.get("const", np.nan)),
            "beta_mkt": float(model.params.get(mkt, np.nan)),
            "t_beta_mkt": float(model.tvalues.get(mkt, np.nan)),
        }
        for f in factors:
            row[f] = float(model.params.get(f, np.nan))
            row[f"t_{f}"] = float(model.tvalues.get(f, np.nan))
        results.append(row)

    out = pd.DataFrame(results).sort_values("r2", ascending=False)
    outpath = os.path.join(OUT_TABLES, "static_factor_models.csv")
    out.to_csv(outpath, index=False)
    print(f"[OK] Wrote {outpath} | rows={len(out)}")

if __name__ == "__main__":
    main()



