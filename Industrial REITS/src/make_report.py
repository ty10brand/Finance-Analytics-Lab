

import os
import pandas as pd

OUT_REPORTS = "outputs/reports"
OUT_TABLES = "outputs/tables"

def main():
    os.makedirs(OUT_REPORTS, exist_ok=True)
    df = pd.read_csv(os.path.join(OUT_TABLES, "static_factor_models.csv"))

    # Top 5 “rate sensitive” (most negative d_DGS10)
    top_rate = df.dropna(subset=["d_DGS10"]).sort_values("d_DGS10").head(5)
    # Top 5 “credit sensitive” (most negative d_BAA10Y)
    top_credit = df.dropna(subset=["d_BAA10Y"]).sort_values("d_BAA10Y").head(5)
    # Highest R^2
    top_r2 = df.sort_values("r2", ascending=False).head(5)

    lines = []
    lines.append("# Industrial REIT Factor Lab (v1)\n")
    lines.append("Model: weekly REIT returns ~ SPY + Δ10Y + ΔBBB spread + Δterm spread (+ optional CPI/INDPRO YoY)\n")

    lines.append("## Highest R² (best explained by factors)\n")
    lines.append(top_r2[["ticker","r2","beta_mkt","d_DGS10","d_BAA10Y"]].to_markdown(index=False))
    lines.append("\n## Most rate-sensitive (Δ10Y)\n")
    lines.append(top_rate[["ticker","d_DGS10","t_d_DGS10","r2"]].to_markdown(index=False))
    lines.append("\n## Most credit-sensitive (ΔBBB spread)\n")
    lines.append(top_credit[["ticker","d_BAA10Y","t_d_BAA10Y","r2"]].to_markdown(index=False))

    outpath = os.path.join(OUT_REPORTS, "factor_lab_summary.md")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[OK] Wrote {outpath}")

if __name__ == "__main__":
    main()


