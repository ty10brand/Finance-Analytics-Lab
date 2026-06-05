

import os
import pandas as pd
import matplotlib.pyplot as plt

OUT_REPORTS = "outputs/reports"
OUT_TABLES = "outputs/tables"

def make_excel(df: pd.DataFrame, outpath: str):
    with pd.ExcelWriter(outpath, engine="openpyxl") as writer:
        # Summary tables
        top_rate = df.dropna(subset=["d_DGS10"]).sort_values("d_DGS10").head(10)
        top_credit = df.dropna(subset=["d_BAA10Y"]).sort_values("d_BAA10Y").head(10)
        top_r2 = df.sort_values("r2", ascending=False).head(10)

        top_r2.to_excel(writer, sheet_name="Top_R2", index=False)
        top_rate.to_excel(writer, sheet_name="Top_Rate_Sens", index=False)
        top_credit.to_excel(writer, sheet_name="Top_Credit_Sens", index=False)

        # Full table
        df.to_excel(writer, sheet_name="Static_Models_All", index=False)

def make_linkedin_sharecard(df: pd.DataFrame, outpath: str):
    top_rate = df.dropna(subset=["d_DGS10"]).sort_values("d_DGS10").head(5)
    top_credit = df.dropna(subset=["d_BAA10Y"]).sort_values("d_BAA10Y").head(5)
    top_r2 = df.sort_values("r2", ascending=False).head(5)

    def fmt_table(sub, cols):
        # Convert to short strings for plotting
        tmp = sub[cols].copy()
        for c in tmp.columns:
            tmp[c] = tmp[c].map(lambda x: "" if pd.isna(x) else f"{x:.3f}" if isinstance(x, (int, float)) else str(x))
        return tmp

    t1 = fmt_table(top_r2, ["ticker", "r2", "beta_mkt", "d_DGS10", "d_BAA10Y"])
    t2 = fmt_table(top_rate, ["ticker", "d_DGS10", "t_d_DGS10", "r2"])
    t3 = fmt_table(top_credit, ["ticker", "d_BAA10Y", "t_d_BAA10Y", "r2"])

    plt.figure(figsize=(12, 7))
    plt.axis("off")

    plt.text(0.01, 0.96, "Industrial REIT Factor Lab (v1)", fontsize=18, weight="bold")
    plt.text(0.01, 0.92, "Weekly returns ~ SPY + Δ10Y + ΔBBB spread + Δterm spread", fontsize=10)

    # Draw tables
    y = 0.82
    plt.text(0.01, y, "Highest R² (best explained by factors)", fontsize=12, weight="bold")
    table1 = plt.table(cellText=t1.values, colLabels=t1.columns, loc="upper left", bbox=[0.01, y-0.22, 0.98, 0.18])
    table1.auto_set_font_size(False); table1.set_fontsize(9)

    y2 = 0.54
    plt.text(0.01, y2, "Most rate-sensitive (Δ10Y)", fontsize=12, weight="bold")
    table2 = plt.table(cellText=t2.values, colLabels=t2.columns, loc="upper left", bbox=[0.01, y2-0.22, 0.48, 0.18])
    table2.auto_set_font_size(False); table2.set_fontsize(9)

    plt.text(0.51, y2, "Most credit-sensitive (ΔBBB spread)", fontsize=12, weight="bold")
    table3 = plt.table(cellText=t3.values, colLabels=t3.columns, loc="upper left", bbox=[0.51, y2-0.22, 0.48, 0.18])
    table3.auto_set_font_size(False); table3.set_fontsize(9)

    plt.text(0.01, 0.05, "Note: Coefficients are regression estimates; Δ10Y and ΔBBB are weekly changes.",
             fontsize=9)

    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()

def main():
    os.makedirs(OUT_REPORTS, exist_ok=True)
    df = pd.read_csv(os.path.join(OUT_TABLES, "static_factor_models.csv"))

    xlsx_path = os.path.join(OUT_REPORTS, "factor_lab_summary.xlsx")
    png_path = os.path.join(OUT_REPORTS, "linkedin_sharecard.png")

    make_excel(df, xlsx_path)
    make_linkedin_sharecard(df, png_path)

    print(f"[OK] Wrote {xlsx_path}")
    print(f"[OK] Wrote {png_path}")

if __name__ == "__main__":
    main()


