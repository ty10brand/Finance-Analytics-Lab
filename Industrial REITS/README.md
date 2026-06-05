

# Industrial REIT Factor Lab

This repo builds an industrial REIT factor lab:
- Weekly returns for industrial REITs + benchmarks
- Weekly macro factors from FRED (rates, term spread, credit spreads)
- Static and rolling factor regressions
- Outputs: tables, charts, and a markdown report

## Quickstart
```bash
pip install -r requirements.txt
python src/ingest_prices.py
python src/ingest_fred.py
python src/build_weekly_panel.py
python src/run_factor_models.py
python src/rolling_models.py
python src/make_report.py


# Industrial REIT Factor Lab

A reproducible Python workflow to analyze **industrial REIT** equity performance through a **macro + rates + credit** lens.

This repo builds a “REIT analyst-style” factor lab:
- Pulls **daily prices** for industrial REITs + benchmarks (SPY, VNQ)
- Pulls **macro series** from FRED (10Y, 2Y, term spread, credit spread proxies, CPI/INDPRO optional)
- Converts everything into a clean **weekly panel**
- Runs:
  - **Static factor regressions** by ticker
  - **Rolling 52-week sensitivities** (market beta + rate/credit sensitivity)
- Exports tables, charts, and shareable summary outputs for GitHub + LinkedIn

---

## Universe (default)
Industrial REITs:
`PLD, REXR, EGP, STAG, TRNO, FR, COLD, LINE, LXP, PLYM, ILPT`

Benchmarks:
`SPY` (market proxy), `VNQ` (broad REIT proxy)

You can edit these in: `config/tickers.yaml`

---

## Factor model (v1)

Weekly returns model:

**REIT_return ~ SPY + Δ10Y + ΔBBB_spread + Δterm_spread (+ optional CPI/INDPRO YoY)**

Where:
- `Δ10Y` is weekly change in 10Y Treasury yield (FRED: DGS10)
- `ΔBBB_spread` is a corporate credit spread proxy (FRED series configured in `config/fred_series.yaml`)
- `Δterm_spread` is weekly change in (10Y - 2Y)

This is not “price prediction.” It’s a **sensitivity / exposure** framework to understand:
- which REITs behave like **bond proxies** (rate-sensitive)
- which are more exposed to **credit risk**
- how exposures change across **rate regimes** (rolling windows)

---

## Outputs

After running the pipeline, you should see:

### Tables
- `outputs/tables/static_factor_models.csv`  
  Static regression results per ticker (R², beta_mkt, rate/credit coefficients, t-stats)

- `outputs/tables/rolling_betas_<TICKER>.csv`  
  Rolling 52-week coefficients per ticker

### Charts
- `outputs/charts/rolling_<TICKER>.png`  
  Rolling market beta + rolling rate sensitivity (when available)

### Reports
- `outputs/reports/factor_lab_summary.md`  
  GitHub-friendly summary tables (Top R² / Most rate-sensitive / Most credit-sensitive)

Optional “share outputs”:
- `outputs/reports/factor_lab_summary.xlsx` (Excel workbook)
- `outputs/reports/linkedin_sharecard.png` (single-image summary for posting)

---



