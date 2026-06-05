

# ============================================================
# Portfolio Backtesting Dashboard - Version 2
# ------------------------------------------------------------
# Dark theme, tabbed HTML dashboard.
#
# Portfolio:
#   AAPL, MSFT, NVDA, AMZN, GOOGL
#
# Benchmarks:
#   SPY, VOO, VUG
#
# Output:
#   outputs/portfolio_backtest_dashboard_v2.html
# ============================================================

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px


# ============================================================
# 1. USER INPUTS
# ============================================================

INITIAL_INVESTMENT = 100_000

START_DATE = "2016-01-01"

# yfinance end date is exclusive.
# This captures through 2025-12-31.
END_DATE = "2026-01-01"

PORTFOLIO_WEIGHTS = {
    "AAPL": 0.20,
    "MSFT": 0.20,
    "NVDA": 0.20,
    "AMZN": 0.20,
    "GOOGL": 0.20,
}

BENCHMARKS = {
    "SPY": "SPY",
    "VOO": "VOO",
    "VUG": "VUG",
}

RISK_FREE_RATE = 0.02

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_HTML = OUTPUT_DIR / "portfolio_backtest_dashboard_v2.html"


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def validate_weights(weights: dict) -> None:
    total_weight = sum(weights.values())

    if not np.isclose(total_weight, 1.0):
        raise ValueError(
            f"Portfolio weights must sum to 1.00. Current sum: {total_weight:.4f}"
        )


def download_price_data(tickers, start_date, end_date) -> pd.DataFrame:
    """
    Downloads adjusted historical prices from yfinance.

    yfinance 1.3.0 may return a MultiIndex with:
        Price level: Close, High, Low, Open, Volume
        Ticker level: AAPL, MSFT, etc.

    Since auto_adjust=True, Close is adjusted.
    """

    print("Downloading historical price data from yfinance...")

    data = yf.download(
        tickers=list(tickers),
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
        threads=False,
        group_by="column"
    )

    if data is None or data.empty:
        raise RuntimeError(
            "yfinance returned no data. This may be a temporary Yahoo rate-limit issue."
        )

    if isinstance(data.columns, pd.MultiIndex):
        if "Close" not in data.columns.get_level_values(0):
            raise ValueError(
                f"Could not find Close prices. Available first-level columns: "
                f"{list(data.columns.get_level_values(0).unique())}"
            )

        prices_df = data["Close"].copy()

    else:
        if "Close" not in data.columns:
            raise ValueError(f"Could not find Close column. Columns: {list(data.columns)}")

        prices_df = data[["Close"]].copy()

        if len(tickers) == 1:
            prices_df.columns = list(tickers)

    prices_df = prices_df.dropna(how="all").ffill().dropna()

    missing = [ticker for ticker in tickers if ticker not in prices_df.columns]

    if missing:
        raise ValueError(f"Missing downloaded price columns for: {missing}")

    print("Download complete.")
    print(prices_df.head())
    print(prices_df.tail())
    print(f"prices_df shape: {prices_df.shape}")

    return prices_df


def calculate_daily_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    if prices_df.empty:
        raise ValueError("prices_df is empty.")

    return prices_df.pct_change().dropna()


def calculate_portfolio_returns(
    returns_df: pd.DataFrame,
    portfolio_weights: dict
) -> pd.Series:

    portfolio_tickers = list(portfolio_weights.keys())

    missing = [ticker for ticker in portfolio_tickers if ticker not in returns_df.columns]

    if missing:
        raise ValueError(f"Missing portfolio tickers in returns_df: {missing}")

    weights_array = np.array([portfolio_weights[ticker] for ticker in portfolio_tickers])

    portfolio_returns = returns_df[portfolio_tickers].dot(weights_array)
    portfolio_returns.name = "Portfolio"

    return portfolio_returns


def calculate_growth_of_investment(
    returns_df: pd.DataFrame,
    initial_investment: float
) -> pd.DataFrame:

    return (1 + returns_df).cumprod() * initial_investment


def calculate_cagr(value_series: pd.Series) -> float:
    start_value = value_series.iloc[0]
    end_value = value_series.iloc[-1]

    num_days = (value_series.index[-1] - value_series.index[0]).days
    num_years = num_days / 365.25

    if num_years <= 0:
        return np.nan

    return (end_value / start_value) ** (1 / num_years) - 1


def calculate_max_drawdown(value_series: pd.Series) -> float:
    running_max = value_series.cummax()
    drawdown = value_series / running_max - 1
    return drawdown.min()


def calculate_beta_alpha(
    strategy_returns: pd.Series,
    benchmark_returns: pd.Series,
    risk_free_rate: float
) -> tuple:
    """
    Calculates beta and annualized alpha versus a benchmark.
    Default benchmark should usually be SPY.
    """

    aligned = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()
    aligned.columns = ["strategy", "benchmark"]

    if aligned.empty:
        return np.nan, np.nan

    covariance = np.cov(aligned["strategy"], aligned["benchmark"])[0][1]
    benchmark_variance = np.var(aligned["benchmark"])

    if benchmark_variance == 0:
        return np.nan, np.nan

    beta = covariance / benchmark_variance

    strategy_annual_return = aligned["strategy"].mean() * 252
    benchmark_annual_return = aligned["benchmark"].mean() * 252

    alpha = strategy_annual_return - (
        risk_free_rate + beta * (benchmark_annual_return - risk_free_rate)
    )

    return beta, alpha


def calculate_performance_metrics(
    growth_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    risk_free_rate: float,
    beta_benchmark: str = "SPY"
) -> pd.DataFrame:

    metrics = []

    benchmark_returns = returns_df[beta_benchmark] if beta_benchmark in returns_df.columns else None

    for column in growth_df.columns:
        value_series = growth_df[column].dropna()
        return_series = returns_df[column].dropna()

        beginning_value = value_series.iloc[0]
        ending_value = value_series.iloc[-1]

        total_return = ending_value / beginning_value - 1
        cagr = calculate_cagr(value_series)

        annual_volatility = return_series.std() * np.sqrt(252)

        sharpe_ratio = (
            (return_series.mean() * 252 - risk_free_rate)
            / annual_volatility
            if annual_volatility != 0
            else np.nan
        )

        max_drawdown = calculate_max_drawdown(value_series)

        if benchmark_returns is not None:
            beta, alpha = calculate_beta_alpha(
                strategy_returns=return_series,
                benchmark_returns=benchmark_returns,
                risk_free_rate=risk_free_rate
            )
        else:
            beta, alpha = np.nan, np.nan

        metrics.append({
            "Strategy": column,
            "Beginning Value": beginning_value,
            "Ending Value": ending_value,
            "Total Return": total_return,
            "CAGR": cagr,
            "Annual Volatility": annual_volatility,
            "Sharpe Ratio": sharpe_ratio,
            "Max Drawdown": max_drawdown,
            "Beta vs SPY": beta,
            "Annual Alpha vs SPY": alpha,
        })

    return pd.DataFrame(metrics)


def calculate_annual_returns(returns_df: pd.DataFrame) -> pd.DataFrame:
    annual_returns_df = (1 + returns_df).resample("YE").prod() - 1
    annual_returns_df.index = annual_returns_df.index.year
    annual_returns_df.index.name = "Year"
    return annual_returns_df


def calculate_monthly_returns(returns_df: pd.DataFrame) -> pd.DataFrame:
    monthly_returns_df = (1 + returns_df).resample("ME").prod() - 1
    monthly_returns_df.index.name = "Month"
    return monthly_returns_df


def calculate_drawdowns(growth_df: pd.DataFrame) -> pd.DataFrame:
    return growth_df / growth_df.cummax() - 1


def calculate_rolling_returns(returns_df: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    return (1 + returns_df).rolling(window).apply(np.prod, raw=True) - 1


def calculate_rolling_volatility(returns_df: pd.DataFrame, window: int = 252) -> pd.DataFrame:
    return returns_df.rolling(window).std() * np.sqrt(252)


def format_percent(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.2%}"


def format_currency(value):
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def format_number(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:,.2f}"


# ============================================================
# 3. DARK PLOTLY THEME HELPERS
# ============================================================

def apply_dark_layout(fig, title: str, height: int = 520):
    fig.update_layout(
        title=title,
        template="plotly_dark",
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,15,25,0.90)",
        font=dict(color="#E5E7EB"),
        title_font=dict(size=22, color="#F9FAFB"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(255,255,255,0.08)",
            borderwidth=1
        ),
        margin=dict(l=50, r=30, t=70, b=50)
    )

    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.08)",
        zerolinecolor="rgba(255,255,255,0.12)"
    )

    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.08)",
        zerolinecolor="rgba(255,255,255,0.12)"
    )

    return fig


def make_growth_chart(growth_df: pd.DataFrame):
    fig = go.Figure()

    for column in growth_df.columns:
        width = 4 if column == "Portfolio" else 2
        fig.add_trace(
            go.Scatter(
                x=growth_df.index,
                y=growth_df[column],
                mode="lines",
                name=column,
                line=dict(width=width)
            )
        )

    fig = apply_dark_layout(fig, "Growth of $100,000", height=590)

    fig.update_yaxes(title="Portfolio Value")
    fig.update_xaxes(title="Date")

    return fig


def make_drawdown_chart(drawdown_df: pd.DataFrame):
    fig = go.Figure()

    for column in drawdown_df.columns:
        width = 4 if column == "Portfolio" else 2
        fig.add_trace(
            go.Scatter(
                x=drawdown_df.index,
                y=drawdown_df[column],
                mode="lines",
                name=column,
                line=dict(width=width)
            )
        )

    fig = apply_dark_layout(fig, "Drawdown Analysis", height=540)
    fig.update_yaxes(title="Drawdown", tickformat=".0%")
    fig.update_xaxes(title="Date")

    return fig


def make_annual_returns_chart(annual_returns_df: pd.DataFrame):
    fig = go.Figure()

    for column in annual_returns_df.columns:
        fig.add_trace(
            go.Bar(
                x=annual_returns_df.index,
                y=annual_returns_df[column],
                name=column
            )
        )

    fig = apply_dark_layout(fig, "Annual Returns", height=560)
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Annual Return", tickformat=".0%")
    fig.update_xaxes(title="Year")

    return fig


def make_allocation_chart(portfolio_weights: dict):
    weights_df = pd.DataFrame({
        "Ticker": list(portfolio_weights.keys()),
        "Weight": list(portfolio_weights.values())
    })

    fig = px.pie(
        weights_df,
        names="Ticker",
        values="Weight",
        hole=0.48,
        title="Portfolio Allocation"
    )

    fig = apply_dark_layout(fig, "Portfolio Allocation", height=520)

    return fig


def make_correlation_heatmap(returns_df: pd.DataFrame):
    corr_df = returns_df.corr()

    fig = px.imshow(
        corr_df,
        text_auto=".2f",
        title="Daily Return Correlation Matrix",
        aspect="auto",
        color_continuous_scale="Viridis"
    )

    fig = apply_dark_layout(fig, "Daily Return Correlation Matrix", height=560)

    return fig


def make_rolling_return_chart(rolling_returns_df: pd.DataFrame):
    fig = go.Figure()

    for column in rolling_returns_df.columns:
        width = 4 if column == "Portfolio" else 2
        fig.add_trace(
            go.Scatter(
                x=rolling_returns_df.index,
                y=rolling_returns_df[column],
                mode="lines",
                name=column,
                line=dict(width=width)
            )
        )

    fig = apply_dark_layout(fig, "Rolling 1-Year Return", height=540)
    fig.update_yaxes(title="Rolling Return", tickformat=".0%")
    fig.update_xaxes(title="Date")

    return fig


def make_rolling_volatility_chart(rolling_volatility_df: pd.DataFrame):
    fig = go.Figure()

    for column in rolling_volatility_df.columns:
        width = 4 if column == "Portfolio" else 2
        fig.add_trace(
            go.Scatter(
                x=rolling_volatility_df.index,
                y=rolling_volatility_df[column],
                mode="lines",
                name=column,
                line=dict(width=width)
            )
        )

    fig = apply_dark_layout(fig, "Rolling 1-Year Volatility", height=540)
    fig.update_yaxes(title="Rolling Volatility", tickformat=".0%")
    fig.update_xaxes(title="Date")

    return fig


# ============================================================
# 4. HTML HELPERS
# ============================================================

def dataframe_to_html_table(df: pd.DataFrame) -> str:
    return df.to_html(
        index=False,
        classes="data-table",
        border=0,
        escape=False
    )


def build_dashboard_html(
    metrics_df: pd.DataFrame,
    annual_returns_df: pd.DataFrame,
    monthly_returns_df: pd.DataFrame,
    portfolio_weights: dict,
    growth_chart,
    drawdown_chart,
    annual_returns_chart,
    allocation_chart,
    correlation_chart,
    rolling_return_chart,
    rolling_volatility_chart
) -> str:

    portfolio_metrics = metrics_df[metrics_df["Strategy"] == "Portfolio"].iloc[0]
    spy_metrics = metrics_df[metrics_df["Strategy"] == "SPY"].iloc[0]

    display_metrics_df = metrics_df.copy()

    display_metrics_df["Beginning Value"] = display_metrics_df["Beginning Value"].apply(format_currency)
    display_metrics_df["Ending Value"] = display_metrics_df["Ending Value"].apply(format_currency)
    display_metrics_df["Total Return"] = display_metrics_df["Total Return"].apply(format_percent)
    display_metrics_df["CAGR"] = display_metrics_df["CAGR"].apply(format_percent)
    display_metrics_df["Annual Volatility"] = display_metrics_df["Annual Volatility"].apply(format_percent)
    display_metrics_df["Sharpe Ratio"] = display_metrics_df["Sharpe Ratio"].apply(format_number)
    display_metrics_df["Max Drawdown"] = display_metrics_df["Max Drawdown"].apply(format_percent)
    display_metrics_df["Beta vs SPY"] = display_metrics_df["Beta vs SPY"].apply(format_number)
    display_metrics_df["Annual Alpha vs SPY"] = display_metrics_df["Annual Alpha vs SPY"].apply(format_percent)

    allocation_df = pd.DataFrame({
        "Ticker": list(portfolio_weights.keys()),
        "Weight": list(portfolio_weights.values())
    })

    allocation_df["Weight"] = allocation_df["Weight"].apply(format_percent)

    display_annual_returns_df = annual_returns_df.copy().reset_index()

    for col in display_annual_returns_df.columns:
        if col != "Year":
            display_annual_returns_df[col] = display_annual_returns_df[col].apply(format_percent)

    display_monthly_returns_df = monthly_returns_df.copy().reset_index()
    display_monthly_returns_df["Month"] = display_monthly_returns_df["Month"].dt.strftime("%Y-%m")

    for col in display_monthly_returns_df.columns:
        if col != "Month":
            display_monthly_returns_df[col] = display_monthly_returns_df[col].apply(format_percent)

    metrics_table_html = dataframe_to_html_table(display_metrics_df)
    allocation_table_html = dataframe_to_html_table(allocation_df)

    annual_returns_table_html = display_annual_returns_df.to_html(
        index=False,
        classes="data-table",
        border=0
    )

    monthly_returns_table_html = display_monthly_returns_df.tail(36).to_html(
        index=False,
        classes="data-table",
        border=0
    )

    growth_chart_html = growth_chart.to_html(full_html=False, include_plotlyjs="cdn")
    drawdown_chart_html = drawdown_chart.to_html(full_html=False, include_plotlyjs=False)
    annual_returns_chart_html = annual_returns_chart.to_html(full_html=False, include_plotlyjs=False)
    allocation_chart_html = allocation_chart.to_html(full_html=False, include_plotlyjs=False)
    correlation_chart_html = correlation_chart.to_html(full_html=False, include_plotlyjs=False)
    rolling_return_chart_html = rolling_return_chart.to_html(full_html=False, include_plotlyjs=False)
    rolling_volatility_chart_html = rolling_volatility_chart.to_html(full_html=False, include_plotlyjs=False)

    portfolio_outperformance = portfolio_metrics["CAGR"] - spy_metrics["CAGR"]

    run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Portfolio Backtesting Dashboard V2</title>

    <style>
        :root {{
            --bg: #05070d;
            --panel: rgba(15, 23, 42, 0.88);
            --panel-solid: #0f172a;
            --panel-soft: rgba(30, 41, 59, 0.75);
            --text: #e5e7eb;
            --muted: #94a3b8;
            --faint: #64748b;
            --border: rgba(148, 163, 184, 0.20);
            --accent: #38bdf8;
            --accent2: #a78bfa;
            --green: #22c55e;
            --red: #ef4444;
            --gold: #f59e0b;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: Inter, Segoe UI, Arial, Helvetica, sans-serif;
            background:
                radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 32%),
                radial-gradient(circle at top right, rgba(167, 139, 250, 0.16), transparent 28%),
                linear-gradient(135deg, #020617 0%, #05070d 45%, #0f172a 100%);
            color: var(--text);
        }}

        .hero {{
            padding: 42px 54px 30px 54px;
            border-bottom: 1px solid var(--border);
            position: relative;
            overflow: hidden;
        }}

        .hero::after {{
            content: "";
            position: absolute;
            right: -120px;
            top: -120px;
            width: 420px;
            height: 420px;
            background: radial-gradient(circle, rgba(56,189,248,0.18), transparent 65%);
            pointer-events: none;
        }}

        .eyebrow {{
            color: var(--accent);
            letter-spacing: 0.18em;
            text-transform: uppercase;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 12px;
        }}

        .hero h1 {{
            font-size: 42px;
            line-height: 1.05;
            margin: 0;
            color: #ffffff;
        }}

        .hero p {{
            max-width: 900px;
            margin-top: 14px;
            color: var(--muted);
            font-size: 16px;
            line-height: 1.6;
        }}

        .hero-meta {{
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-top: 22px;
        }}

        .pill {{
            border: 1px solid var(--border);
            background: rgba(15, 23, 42, 0.62);
            border-radius: 999px;
            padding: 9px 13px;
            color: #cbd5e1;
            font-size: 13px;
        }}

        .container {{
            padding: 28px 54px 54px 54px;
        }}

        .tabs {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 24px;
            position: sticky;
            top: 0;
            z-index: 20;
            padding: 14px 0;
            background: linear-gradient(180deg, rgba(5,7,13,0.98), rgba(5,7,13,0.72));
            backdrop-filter: blur(12px);
        }}

        .tab-button {{
            border: 1px solid var(--border);
            background: rgba(15, 23, 42, 0.70);
            color: var(--muted);
            padding: 11px 15px;
            border-radius: 999px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.18s ease;
        }}

        .tab-button:hover {{
            border-color: rgba(56,189,248,0.65);
            color: #ffffff;
            transform: translateY(-1px);
        }}

        .tab-button.active {{
            background: linear-gradient(135deg, rgba(56,189,248,0.26), rgba(167,139,250,0.25));
            border-color: rgba(56,189,248,0.75);
            color: #ffffff;
            box-shadow: 0 0 24px rgba(56,189,248,0.12);
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 18px;
            margin-bottom: 22px;
        }}

        .card {{
            background: linear-gradient(180deg, rgba(15,23,42,0.92), rgba(15,23,42,0.70));
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 22px;
            box-shadow: 0 18px 50px rgba(0,0,0,0.24);
            position: relative;
            overflow: hidden;
        }}

        .card::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(56,189,248,0.08), transparent 45%, rgba(167,139,250,0.08));
            pointer-events: none;
        }}

        .card h3 {{
            margin: 0;
            color: var(--muted);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            position: relative;
        }}

        .card .value {{
            margin-top: 11px;
            font-size: 31px;
            font-weight: 800;
            color: #ffffff;
            position: relative;
        }}

        .card .sub {{
            margin-top: 8px;
            color: var(--faint);
            font-size: 13px;
            position: relative;
        }}

        .section {{
            background: rgba(15,23,42,0.72);
            border: 1px solid var(--border);
            border-radius: 24px;
            padding: 25px;
            margin-bottom: 22px;
            box-shadow: 0 18px 50px rgba(0,0,0,0.26);
        }}

        .section h2 {{
            margin: 0 0 15px 0;
            font-size: 24px;
            color: #ffffff;
        }}

        .section p {{
            color: var(--muted);
            line-height: 1.65;
        }}

        .two-col {{
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 22px;
        }}

        .data-table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
            overflow: hidden;
            border-radius: 14px;
        }}

        .data-table th {{
            background: rgba(30,41,59,0.95);
            color: #ffffff;
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        .data-table td {{
            padding: 12px;
            border-bottom: 1px solid rgba(148,163,184,0.13);
            color: #cbd5e1;
        }}

        .data-table tr:nth-child(even) td {{
            background: rgba(15,23,42,0.40);
        }}

        .data-table tr:hover td {{
            background: rgba(56,189,248,0.08);
        }}

        .callout {{
            border: 1px solid rgba(56,189,248,0.28);
            background: linear-gradient(135deg, rgba(56,189,248,0.12), rgba(167,139,250,0.08));
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 22px;
            color: #cbd5e1;
            line-height: 1.65;
        }}

        .footer {{
            color: var(--faint);
            text-align: center;
            padding: 30px 54px 44px 54px;
            font-size: 13px;
        }}

        @media (max-width: 1100px) {{
            .summary-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}

            .two-col {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 700px) {{
            .hero, .container, .footer {{
                padding-left: 22px;
                padding-right: 22px;
            }}

            .hero h1 {{
                font-size: 32px;
            }}

            .summary-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>

<body>

    <div class="hero">
        <div class="eyebrow">Quant Finance / Portfolio Backtesting</div>
        <h1>Portfolio Backtesting Dashboard V2</h1>
        <p>
            A dark-mode static HTML dashboard comparing an equal-weight technology portfolio against SPY, VOO, and VUG.
            Built in Python with pandas, yfinance, and Plotly.
        </p>

        <div class="hero-meta">
            <div class="pill">Initial Investment: {format_currency(INITIAL_INVESTMENT)}</div>
            <div class="pill">Period: {START_DATE} to 2025-12-31</div>
            <div class="pill">Portfolio: AAPL / MSFT / NVDA / AMZN / GOOGL</div>
            <div class="pill">Benchmarks: SPY / VOO / VUG</div>
        </div>
    </div>

    <div class="container">

        <div class="tabs">
            <button class="tab-button active" onclick="openTab(event, 'overview')">Overview</button>
            <button class="tab-button" onclick="openTab(event, 'growth')">Growth</button>
            <button class="tab-button" onclick="openTab(event, 'risk')">Risk</button>
            <button class="tab-button" onclick="openTab(event, 'returns')">Returns</button>
            <button class="tab-button" onclick="openTab(event, 'allocation')">Allocation</button>
            <button class="tab-button" onclick="openTab(event, 'data')">Data Tables</button>
        </div>

        <div id="overview" class="tab-content active">

            <div class="summary-grid">
                <div class="card">
                    <h3>Portfolio Ending Value</h3>
                    <div class="value">{format_currency(portfolio_metrics["Ending Value"])}</div>
                    <div class="sub">Growth of {format_currency(INITIAL_INVESTMENT)}</div>
                </div>

                <div class="card">
                    <h3>Total Return</h3>
                    <div class="value">{format_percent(portfolio_metrics["Total Return"])}</div>
                    <div class="sub">Full-period cumulative return</div>
                </div>

                <div class="card">
                    <h3>CAGR</h3>
                    <div class="value">{format_percent(portfolio_metrics["CAGR"])}</div>
                    <div class="sub">SPY CAGR: {format_percent(spy_metrics["CAGR"])}</div>
                </div>

                <div class="card">
                    <h3>Sharpe Ratio</h3>
                    <div class="value">{format_number(portfolio_metrics["Sharpe Ratio"])}</div>
                    <div class="sub">Assumes {format_percent(RISK_FREE_RATE)} risk-free rate</div>
                </div>
            </div>

            <div class="summary-grid">
                <div class="card">
                    <h3>Max Drawdown</h3>
                    <div class="value">{format_percent(portfolio_metrics["Max Drawdown"])}</div>
                    <div class="sub">Worst peak-to-trough decline</div>
                </div>

                <div class="card">
                    <h3>Annual Volatility</h3>
                    <div class="value">{format_percent(portfolio_metrics["Annual Volatility"])}</div>
                    <div class="sub">Annualized daily volatility</div>
                </div>

                <div class="card">
                    <h3>Beta vs SPY</h3>
                    <div class="value">{format_number(portfolio_metrics["Beta vs SPY"])}</div>
                    <div class="sub">Market sensitivity estimate</div>
                </div>

                <div class="card">
                    <h3>CAGR Spread vs SPY</h3>
                    <div class="value">{format_percent(portfolio_outperformance)}</div>
                    <div class="sub">Portfolio CAGR minus SPY CAGR</div>
                </div>
            </div>

            <div class="section">
                <h2>Executive Interpretation</h2>
                <p>
                    This dashboard evaluates a concentrated five-stock portfolio against broad-market and growth ETF
                    benchmarks. The portfolio is equally weighted across AAPL, MSFT, NVDA, AMZN, and GOOGL. Performance
                    is compared against SPY, VOO, and VUG using growth of capital, CAGR, volatility, Sharpe ratio,
                    beta, alpha, and drawdown metrics.
                </p>
                <p>
                    The purpose of this project is not to recommend the portfolio, but to demonstrate a clean quant
                    finance backtesting workflow: price data collection, return calculation, portfolio construction,
                    benchmark comparison, risk analytics, and dashboard reporting.
                </p>
            </div>
        </div>

        <div id="growth" class="tab-content">
            <div class="section">
                <h2>Growth of Capital</h2>
                {growth_chart_html}
            </div>

            <div class="section">
                <h2>Rolling 1-Year Return</h2>
                {rolling_return_chart_html}
            </div>
        </div>

        <div id="risk" class="tab-content">
            <div class="section">
                <h2>Drawdown Analysis</h2>
                {drawdown_chart_html}
            </div>

            <div class="section">
                <h2>Rolling 1-Year Volatility</h2>
                {rolling_volatility_chart_html}
            </div>

            <div class="section">
                <h2>Correlation Matrix</h2>
                {correlation_chart_html}
            </div>
        </div>

        <div id="returns" class="tab-content">
            <div class="section">
                <h2>Annual Returns</h2>
                {annual_returns_chart_html}
            </div>

            <div class="section">
                <h2>Annual Return Table</h2>
                {annual_returns_table_html}
            </div>
        </div>

        <div id="allocation" class="tab-content">
            <div class="two-col">
                <div class="section">
                    <h2>Portfolio Allocation</h2>
                    {allocation_chart_html}
                </div>

                <div class="section">
                    <h2>Holdings</h2>
                    {allocation_table_html}
                </div>
            </div>
        </div>

        <div id="data" class="tab-content">
            <div class="section">
                <h2>Performance Metrics</h2>
                {metrics_table_html}
            </div>

            <div class="section">
                <h2>Recent Monthly Returns</h2>
                <p>The table below shows the most recent 36 monthly returns in the backtest period.</p>
                {monthly_returns_table_html}
            </div>
        </div>

    </div>

    <div class="footer">
        Generated on {run_timestamp}. For educational and research purposes only. Not investment advice.
    </div>

    <script>
        function openTab(evt, tabName) {{
            var i, tabcontent, tabbuttons;

            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {{
                tabcontent[i].classList.remove("active");
            }}

            tabbuttons = document.getElementsByClassName("tab-button");
            for (i = 0; i < tabbuttons.length; i++) {{
                tabbuttons[i].classList.remove("active");
            }}

            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");

            setTimeout(function() {{
                if (window.Plotly) {{
                    var graphs = document.getElementsByClassName("plotly-graph-div");
                    for (var j = 0; j < graphs.length; j++) {{
                        Plotly.Plots.resize(graphs[j]);
                    }}
                }}
            }}, 150);
        }}
    </script>

</body>
</html>
"""

    return html


# ============================================================
# 5. MAIN SCRIPT
# ============================================================

def main():
    validate_weights(PORTFOLIO_WEIGHTS)

    portfolio_tickers = list(PORTFOLIO_WEIGHTS.keys())
    benchmark_tickers = list(BENCHMARKS.values())

    all_tickers = portfolio_tickers + benchmark_tickers

    prices_df = download_price_data(
        tickers=all_tickers,
        start_date=START_DATE,
        end_date=END_DATE
    )

    returns_df = calculate_daily_returns(prices_df)

    portfolio_returns = calculate_portfolio_returns(
        returns_df=returns_df,
        portfolio_weights=PORTFOLIO_WEIGHTS
    )

    benchmark_names = list(BENCHMARKS.keys())
    benchmark_returns_df = returns_df[benchmark_names].copy()

    combined_returns_df = pd.concat(
        [portfolio_returns, benchmark_returns_df],
        axis=1
    ).dropna()

    growth_df = calculate_growth_of_investment(
        returns_df=combined_returns_df,
        initial_investment=INITIAL_INVESTMENT
    )

    metrics_df = calculate_performance_metrics(
        growth_df=growth_df,
        returns_df=combined_returns_df,
        risk_free_rate=RISK_FREE_RATE,
        beta_benchmark="SPY"
    )

    annual_returns_df = calculate_annual_returns(combined_returns_df)
    monthly_returns_df = calculate_monthly_returns(combined_returns_df)
    drawdown_df = calculate_drawdowns(growth_df)

    rolling_returns_df = calculate_rolling_returns(combined_returns_df, window=252)
    rolling_volatility_df = calculate_rolling_volatility(combined_returns_df, window=252)

    growth_chart = make_growth_chart(growth_df)
    drawdown_chart = make_drawdown_chart(drawdown_df)
    annual_returns_chart = make_annual_returns_chart(annual_returns_df)
    allocation_chart = make_allocation_chart(PORTFOLIO_WEIGHTS)
    correlation_chart = make_correlation_heatmap(combined_returns_df)
    rolling_return_chart = make_rolling_return_chart(rolling_returns_df)
    rolling_volatility_chart = make_rolling_volatility_chart(rolling_volatility_df)

    dashboard_html = build_dashboard_html(
        metrics_df=metrics_df,
        annual_returns_df=annual_returns_df,
        monthly_returns_df=monthly_returns_df,
        portfolio_weights=PORTFOLIO_WEIGHTS,
        growth_chart=growth_chart,
        drawdown_chart=drawdown_chart,
        annual_returns_chart=annual_returns_chart,
        allocation_chart=allocation_chart,
        correlation_chart=correlation_chart,
        rolling_return_chart=rolling_return_chart,
        rolling_volatility_chart=rolling_volatility_chart
    )

    OUTPUT_HTML.write_text(dashboard_html, encoding="utf-8")

    print("\nBacktest dashboard V2 complete.")
    print(f"Dashboard saved to: {OUTPUT_HTML.resolve()}")

    print("\nPerformance Metrics:")
    print(metrics_df.to_string(index=False))


if __name__ == "__main__":
    main()


