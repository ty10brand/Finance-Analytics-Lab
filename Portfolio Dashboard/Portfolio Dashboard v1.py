

# ============================================================
# Portfolio Backtesting Static HTML Dashboard
# ------------------------------------------------------------
# Hypothetical portfolio:
#   AAPL, MSFT, NVDA, AMZN, GOOGL
#
# Benchmarks:
#   SPY = S&P 500 ETF
#   VOO = Vanguard S&P 500 ETF
#   VUG = Vanguard Growth ETF
#
# Data source order:
#   1. yfinance multi-ticker
#   2. yfinance ticker-by-ticker
#   3. Direct Stooq CSV through requests
#
# Output:
#   outputs/portfolio_backtest_dashboard.html
# ============================================================

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from datetime import datetime
from io import StringIO

import numpy as np
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
import plotly.express as px


# ============================================================
# 1. USER INPUTS
# ============================================================

INITIAL_INVESTMENT = 100_000

START_DATE = "2016-01-01"

# End date is exclusive for yfinance.
# For Stooq, we will pass the same date and it should still work.
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

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_HTML = OUTPUT_DIR / "portfolio_backtest_dashboard.html"


# ============================================================
# 2. HELPER FUNCTIONS
# ============================================================

def validate_weights(weights: dict) -> None:
    """
    Makes sure portfolio weights add to 100%.
    """
    total_weight = sum(weights.values())

    if not np.isclose(total_weight, 1.0):
        raise ValueError(
            f"Portfolio weights must sum to 1.00. Current sum: {total_weight:.4f}"
        )


def download_single_stooq_csv(ticker: str, start_date: str, end_date: str) -> pd.Series:
    """
    Direct Stooq CSV downloader.

    This bypasses pandas-datareader and pulls CSV text directly.

    Example Stooq symbol:
        AAPL -> aapl.us
        SPY  -> spy.us
    """

    symbol = f"{ticker.lower()}.us"

    start_clean = start_date.replace("-", "")
    end_clean = end_date.replace("-", "")

    url = (
        "https://stooq.com/q/d/l/"
        f"?s={symbol}&d1={start_clean}&d2={end_clean}&i=d"
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers, timeout=30)

    print(f"  Stooq HTTP status for {ticker}: {response.status_code}")
    print(f"  First 120 characters returned: {response.text[:120]}")

    if response.status_code != 200:
        raise RuntimeError(f"Stooq HTTP error {response.status_code} for {ticker}")

    expected_header = "Date,Open,High,Low,Close,Volume"

    if expected_header not in response.text[:300]:
        raise RuntimeError(
            f"Stooq did not return CSV data for {ticker}. "
            f"Returned text begins with: {response.text[:300]}"
        )

    df = pd.read_csv(StringIO(response.text))

    if df.empty:
        raise RuntimeError(f"Stooq returned an empty CSV for {ticker}")

    required_cols = {"Date", "Close"}

    if not required_cols.issubset(set(df.columns)):
        raise RuntimeError(
            f"Stooq CSV for {ticker} is missing required columns. "
            f"Columns returned: {list(df.columns)}"
        )

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.set_index("Date").sort_index()

    close_series = df["Close"].copy()
    close_series.name = ticker

    return close_series


def download_price_data(tickers, start_date, end_date) -> pd.DataFrame:
    """
    Downloads historical close price data.

    Data source order:
    1. yfinance multi-ticker download
    2. yfinance ticker-by-ticker download
    3. Direct Stooq CSV fallback

    Returns:
        prices_df: DataFrame of close or adjusted close prices.
    """

    print("Downloading historical price data...")

    tickers = list(tickers)

    # --------------------------------------------------------
    # Attempt 1: yfinance multi-ticker download
    # --------------------------------------------------------
    try:
        print("Trying yfinance multi-ticker download...")

        data = yf.download(
            tickers=tickers,
            start=start_date,
            end=end_date,
            auto_adjust=True,
            progress=False,
            threads=False,
            group_by="column"
        )

        if data is not None and not data.empty:
            if isinstance(data.columns, pd.MultiIndex):
                if "Close" in data.columns.get_level_values(0):
                    prices_df = data["Close"].copy()
                elif "Adj Close" in data.columns.get_level_values(0):
                    prices_df = data["Adj Close"].copy()
                else:
                    raise ValueError("Could not find Close or Adj Close in yfinance data.")
            else:
                prices_df = data[["Close"]].copy()
                prices_df.columns = tickers

            prices_df = prices_df.dropna(how="all").ffill().dropna()

            if not prices_df.empty:
                print("yfinance multi-ticker download succeeded.")
                return prices_df

    except Exception as e:
        print(f"yfinance multi-ticker download failed. Reason: {e}")

    # --------------------------------------------------------
    # Attempt 2: yfinance ticker-by-ticker fallback
    # --------------------------------------------------------
    print("Trying yfinance ticker-by-ticker download...")

    price_series = {}

    for ticker in tickers:
        try:
            print(f"Downloading {ticker} from yfinance...")

            single = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                auto_adjust=True,
                progress=False,
                threads=False
            )

            if single is None or single.empty:
                print(f"  No yfinance data returned for {ticker}.")
                continue

            if isinstance(single.columns, pd.MultiIndex):
                if "Close" in single.columns.get_level_values(0):
                    s = single["Close"]
                    if isinstance(s, pd.DataFrame):
                        s = s.iloc[:, 0]
                    price_series[ticker] = s
                elif "Adj Close" in single.columns.get_level_values(0):
                    s = single["Adj Close"]
                    if isinstance(s, pd.DataFrame):
                        s = s.iloc[:, 0]
                    price_series[ticker] = s
                else:
                    print(f"  No Close or Adj Close column found for {ticker}.")
            else:
                if "Close" in single.columns:
                    price_series[ticker] = single["Close"]
                elif "Adj Close" in single.columns:
                    price_series[ticker] = single["Adj Close"]
                else:
                    print(f"  No Close or Adj Close column found for {ticker}.")

        except Exception as e:
            print(f"  yfinance failed for {ticker}. Reason: {e}")

    prices_df = pd.DataFrame(price_series)
    prices_df = prices_df.dropna(how="all").ffill().dropna()

    if not prices_df.empty:
        print("yfinance ticker-by-ticker download succeeded.")
        return prices_df

    # --------------------------------------------------------
    # Attempt 3: Direct Stooq CSV fallback
    # --------------------------------------------------------
    print("yfinance failed. Trying direct Stooq CSV fallback...")

    stooq_series = {}

    for ticker in tickers:
        try:
            print(f"Downloading {ticker} from direct Stooq CSV...")

            stooq_series[ticker] = download_single_stooq_csv(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date
            )

        except Exception as e:
            print(f"  Direct Stooq CSV failed for {ticker}. Reason: {e}")

    prices_df = pd.DataFrame(stooq_series)
    prices_df = prices_df.dropna(how="all").ffill().dropna()

    if prices_df.empty:
        raise RuntimeError(
            "\nNo usable price data was downloaded from yfinance or direct Stooq CSV.\n\n"
            "This is a data access issue, not a portfolio math issue.\n\n"
            "Likely causes:\n"
            "1. Yahoo Finance and Stooq requests are being blocked or redirected.\n"
            "2. Your network is returning an HTML/security page instead of CSV/JSON data.\n"
            "3. SSL/certificate/network settings are interfering with Python requests.\n\n"
            "Next steps:\n"
            "1. Look at the printed line: 'First 120 characters returned'.\n"
            "2. If it starts with '<html>' or an error page, the request is being blocked/redirected.\n"
            "3. Try a non-work/non-school network or phone hotspot.\n"
            "4. Later, use a stable API such as Alpha Vantage, Tiingo, Polygon, or Nasdaq Data Link.\n"
        )

    missing_tickers = [ticker for ticker in tickers if ticker not in prices_df.columns]

    if missing_tickers:
        print(f"Warning: missing tickers from price data: {missing_tickers}")

    print("Direct Stooq CSV fallback succeeded.")

    return prices_df


def calculate_daily_returns(prices_df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts price data into daily return data.
    """
    if prices_df.empty:
        raise ValueError("prices_df is empty. Cannot calculate returns.")

    returns_df = prices_df.pct_change().dropna()
    return returns_df


def calculate_portfolio_returns(
    returns_df: pd.DataFrame,
    portfolio_weights: dict
) -> pd.Series:
    """
    Calculates weighted portfolio daily returns.
    """
    portfolio_tickers = list(portfolio_weights.keys())

    missing = [ticker for ticker in portfolio_tickers if ticker not in returns_df.columns]

    if missing:
        raise ValueError(
            f"The following portfolio tickers are missing from returns_df: {missing}"
        )

    weights_array = np.array([portfolio_weights[ticker] for ticker in portfolio_tickers])

    portfolio_returns = returns_df[portfolio_tickers].dot(weights_array)
    portfolio_returns.name = "Portfolio"

    return portfolio_returns


def calculate_growth_of_investment(
    returns_df: pd.DataFrame,
    initial_investment: float
) -> pd.DataFrame:
    """
    Converts daily returns into cumulative dollar-value growth.
    """
    if returns_df.empty:
        raise ValueError("returns_df is empty. Cannot calculate growth of investment.")

    growth_df = (1 + returns_df).cumprod() * initial_investment
    return growth_df


def calculate_cagr(value_series: pd.Series) -> float:
    """
    Calculates compound annual growth rate.
    """
    if value_series.empty:
        return np.nan

    start_value = value_series.iloc[0]
    end_value = value_series.iloc[-1]

    num_days = (value_series.index[-1] - value_series.index[0]).days
    num_years = num_days / 365.25

    if num_years <= 0:
        return np.nan

    cagr = (end_value / start_value) ** (1 / num_years) - 1
    return cagr


def calculate_max_drawdown(value_series: pd.Series) -> float:
    """
    Calculates max drawdown from a dollar-value series.
    """
    if value_series.empty:
        return np.nan

    running_max = value_series.cummax()
    drawdown = value_series / running_max - 1
    max_drawdown = drawdown.min()

    return max_drawdown


def calculate_performance_metrics(
    growth_df: pd.DataFrame,
    returns_df: pd.DataFrame,
    risk_free_rate: float
) -> pd.DataFrame:
    """
    Calculates summary performance metrics for portfolio and benchmarks.
    """
    if growth_df.empty:
        raise ValueError("growth_df is empty. Cannot calculate performance metrics.")

    if returns_df.empty:
        raise ValueError("returns_df is empty. Cannot calculate performance metrics.")

    metrics = []

    for column in growth_df.columns:
        value_series = growth_df[column].dropna()
        return_series = returns_df[column].dropna()

        if value_series.empty or return_series.empty:
            continue

        beginning_value = value_series.iloc[0]
        ending_value = value_series.iloc[-1]

        total_return = ending_value / beginning_value - 1
        cagr = calculate_cagr(value_series)

        annual_volatility = return_series.std() * np.sqrt(252)

        if annual_volatility and annual_volatility != 0:
            sharpe_ratio = (
                (return_series.mean() * 252 - risk_free_rate)
                / annual_volatility
            )
        else:
            sharpe_ratio = np.nan

        max_drawdown = calculate_max_drawdown(value_series)

        metrics.append({
            "Strategy": column,
            "Beginning Value": beginning_value,
            "Ending Value": ending_value,
            "Total Return": total_return,
            "CAGR": cagr,
            "Annual Volatility": annual_volatility,
            "Sharpe Ratio": sharpe_ratio,
            "Max Drawdown": max_drawdown,
        })

    metrics_df = pd.DataFrame(metrics)

    if metrics_df.empty:
        raise ValueError("metrics_df is empty. No valid metrics could be calculated.")

    return metrics_df


def calculate_annual_returns(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates annual returns from daily returns.
    """
    annual_returns_df = (1 + returns_df).resample("YE").prod() - 1
    annual_returns_df.index = annual_returns_df.index.year
    annual_returns_df.index.name = "Year"

    return annual_returns_df


def calculate_monthly_returns(returns_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates monthly returns from daily returns.
    """
    monthly_returns_df = (1 + returns_df).resample("ME").prod() - 1
    monthly_returns_df.index.name = "Month"

    return monthly_returns_df


def calculate_drawdowns(growth_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates drawdown series for each strategy.
    """
    drawdown_df = growth_df / growth_df.cummax() - 1
    return drawdown_df


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
# 3. PLOTLY CHART FUNCTIONS
# ============================================================

def make_growth_chart(growth_df: pd.DataFrame):
    fig = go.Figure()

    for column in growth_df.columns:
        fig.add_trace(
            go.Scatter(
                x=growth_df.index,
                y=growth_df[column],
                mode="lines",
                name=column
            )
        )

    fig.update_layout(
        title="Growth of $100,000",
        xaxis_title="Date",
        yaxis_title="Portfolio Value",
        hovermode="x unified",
        template="plotly_white",
        height=550
    )

    return fig


def make_drawdown_chart(drawdown_df: pd.DataFrame):
    fig = go.Figure()

    for column in drawdown_df.columns:
        fig.add_trace(
            go.Scatter(
                x=drawdown_df.index,
                y=drawdown_df[column],
                mode="lines",
                name=column
            )
        )

    fig.update_layout(
        title="Drawdown Analysis",
        xaxis_title="Date",
        yaxis_title="Drawdown",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        yaxis_tickformat=".0%"
    )

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

    fig.update_layout(
        title="Annual Returns",
        xaxis_title="Year",
        yaxis_title="Annual Return",
        barmode="group",
        template="plotly_white",
        height=550,
        yaxis_tickformat=".0%"
    )

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
        title="Portfolio Allocation"
    )

    fig.update_layout(
        template="plotly_white",
        height=450
    )

    return fig


def make_correlation_heatmap(returns_df: pd.DataFrame):
    corr_df = returns_df.corr()

    fig = px.imshow(
        corr_df,
        text_auto=".2f",
        title="Daily Return Correlation Matrix",
        aspect="auto"
    )

    fig.update_layout(
        template="plotly_white",
        height=550
    )

    return fig


# ============================================================
# 4. HTML DASHBOARD BUILDER
# ============================================================

def dataframe_to_html_table(df: pd.DataFrame, table_id: str = "") -> str:
    """
    Converts DataFrame to clean HTML table.
    """
    return df.to_html(
        index=False,
        classes="data-table",
        border=0,
        table_id=table_id,
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
    correlation_chart
) -> str:
    """
    Builds full HTML dashboard as a string.
    """

    portfolio_metrics = metrics_df[metrics_df["Strategy"] == "Portfolio"].iloc[0]

    display_metrics_df = metrics_df.copy()

    display_metrics_df["Beginning Value"] = display_metrics_df["Beginning Value"].apply(format_currency)
    display_metrics_df["Ending Value"] = display_metrics_df["Ending Value"].apply(format_currency)
    display_metrics_df["Total Return"] = display_metrics_df["Total Return"].apply(format_percent)
    display_metrics_df["CAGR"] = display_metrics_df["CAGR"].apply(format_percent)
    display_metrics_df["Annual Volatility"] = display_metrics_df["Annual Volatility"].apply(format_percent)
    display_metrics_df["Sharpe Ratio"] = display_metrics_df["Sharpe Ratio"].apply(format_number)
    display_metrics_df["Max Drawdown"] = display_metrics_df["Max Drawdown"].apply(format_percent)

    allocation_df = pd.DataFrame({
        "Ticker": list(portfolio_weights.keys()),
        "Weight": list(portfolio_weights.values())
    })

    allocation_df["Weight"] = allocation_df["Weight"].apply(format_percent)

    display_annual_returns_df = annual_returns_df.copy()
    display_annual_returns_df = display_annual_returns_df.reset_index()

    for col in display_annual_returns_df.columns:
        if col != "Year":
            display_annual_returns_df[col] = display_annual_returns_df[col].apply(format_percent)

    display_monthly_returns_df = monthly_returns_df.copy()
    display_monthly_returns_df = display_monthly_returns_df.reset_index()
    display_monthly_returns_df["Month"] = display_monthly_returns_df["Month"].dt.strftime("%Y-%m")

    for col in display_monthly_returns_df.columns:
        if col != "Month":
            display_monthly_returns_df[col] = display_monthly_returns_df[col].apply(format_percent)

    growth_chart_html = growth_chart.to_html(full_html=False, include_plotlyjs="cdn")
    drawdown_chart_html = drawdown_chart.to_html(full_html=False, include_plotlyjs=False)
    annual_returns_chart_html = annual_returns_chart.to_html(full_html=False, include_plotlyjs=False)
    allocation_chart_html = allocation_chart.to_html(full_html=False, include_plotlyjs=False)
    correlation_chart_html = correlation_chart.to_html(full_html=False, include_plotlyjs=False)

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

    run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Portfolio Backtesting Dashboard</title>

    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            background-color: #f5f7fa;
            color: #1f2937;
            margin: 0;
            padding: 0;
        }}

        .header {{
            background: linear-gradient(135deg, #111827, #1f2937);
            color: white;
            padding: 32px 48px;
        }}

        .header h1 {{
            margin: 0;
            font-size: 34px;
        }}

        .header p {{
            margin-top: 8px;
            color: #d1d5db;
            font-size: 16px;
        }}

        .container {{
            padding: 32px 48px;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 32px;
        }}

        .card {{
            background: white;
            border-radius: 16px;
            padding: 22px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        }}

        .card h3 {{
            margin: 0;
            font-size: 14px;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .card .value {{
            margin-top: 10px;
            font-size: 28px;
            font-weight: bold;
            color: #111827;
        }}

        .section {{
            background: white;
            border-radius: 16px;
            padding: 28px;
            margin-bottom: 28px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        }}

        .section h2 {{
            margin-top: 0;
            color: #111827;
            font-size: 24px;
        }}

        .data-table {{
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
            margin-top: 16px;
        }}

        .data-table th {{
            background-color: #111827;
            color: white;
            padding: 10px;
            text-align: left;
        }}

        .data-table td {{
            border-bottom: 1px solid #e5e7eb;
            padding: 10px;
        }}

        .data-table tr:nth-child(even) {{
            background-color: #f9fafb;
        }}

        .note {{
            background-color: #eef2ff;
            border-left: 5px solid #4f46e5;
            padding: 18px;
            border-radius: 8px;
            margin-bottom: 28px;
            line-height: 1.6;
        }}

        .footer {{
            color: #6b7280;
            font-size: 13px;
            padding: 24px 48px;
            text-align: center;
        }}

        @media (max-width: 900px) {{
            .summary-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>

<body>

    <div class="header">
        <h1>Portfolio Backtesting Dashboard</h1>
        <p>Hypothetical equity portfolio compared against SPY, VOO, and VUG</p>
    </div>

    <div class="container">

        <div class="note">
            <strong>Backtest setup:</strong>
            This analysis assumes an initial investment of {format_currency(INITIAL_INVESTMENT)}
            from {START_DATE} through 2025-12-31. The hypothetical portfolio is equally weighted across
            AAPL, MSFT, NVDA, AMZN, and GOOGL. Benchmark comparisons include SPY, VOO, and VUG.
            The script first attempts yfinance data and then falls back to direct Stooq CSV data if needed.
        </div>

        <div class="summary-grid">
            <div class="card">
                <h3>Portfolio Ending Value</h3>
                <div class="value">{format_currency(portfolio_metrics["Ending Value"])}</div>
            </div>

            <div class="card">
                <h3>Total Return</h3>
                <div class="value">{format_percent(portfolio_metrics["Total Return"])}</div>
            </div>

            <div class="card">
                <h3>CAGR</h3>
                <div class="value">{format_percent(portfolio_metrics["CAGR"])}</div>
            </div>

            <div class="card">
                <h3>Sharpe Ratio</h3>
                <div class="value">{format_number(portfolio_metrics["Sharpe Ratio"])}</div>
            </div>
        </div>

        <div class="section">
            <h2>Growth of $100,000</h2>
            {growth_chart_html}
        </div>

        <div class="section">
            <h2>Performance Metrics</h2>
            {metrics_table_html}
        </div>

        <div class="section">
            <h2>Drawdown Analysis</h2>
            {drawdown_chart_html}
        </div>

        <div class="section">
            <h2>Annual Returns</h2>
            {annual_returns_chart_html}
            {annual_returns_table_html}
        </div>

        <div class="section">
            <h2>Portfolio Allocation</h2>
            {allocation_chart_html}
            {allocation_table_html}
        </div>

        <div class="section">
            <h2>Correlation Matrix</h2>
            {correlation_chart_html}
        </div>

        <div class="section">
            <h2>Recent Monthly Returns</h2>
            <p>The table below shows the most recent 36 monthly returns in the backtest period.</p>
            {monthly_returns_table_html}
        </div>

        <div class="section">
            <h2>Interpretation</h2>
            <p>
                This dashboard shows how a concentrated five-stock technology-oriented portfolio would have performed
                relative to broad-market and growth benchmarks. The portfolio's ending value, CAGR, Sharpe ratio,
                volatility, and drawdown metrics help evaluate both return potential and risk.
            </p>

            <p>
                SPY and VOO represent broad S&P 500 ETF exposure, while VUG represents a growth-oriented benchmark.
                Comparing the custom portfolio against these benchmarks helps show whether the concentrated portfolio
                meaningfully outperformed simpler passive index strategies.
            </p>

            <p>
                For a stronger quant finance project, the next improvements would include rebalancing assumptions,
                transaction costs, dividend treatment, rolling Sharpe ratios, beta/alpha calculations, downside deviation,
                Sortino ratio, and Monte Carlo simulation.
            </p>
        </div>

    </div>

    <div class="footer">
        Generated on {run_timestamp}. For educational and research purposes only. Not investment advice.
    </div>

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

    # --------------------------------------------------------
    # Download prices into a DataFrame
    # --------------------------------------------------------
    prices_df = download_price_data(
        tickers=all_tickers,
        start_date=START_DATE,
        end_date=END_DATE
    )

    if prices_df.empty:
        raise RuntimeError("prices_df is empty. Cannot run backtest.")

    print("\nDownloaded price data:")
    print(prices_df.head())
    print(prices_df.tail())
    print(f"prices_df shape: {prices_df.shape}")

    # --------------------------------------------------------
    # Rename benchmark ticker columns for readability
    # --------------------------------------------------------
    rename_map = {ticker: name for name, ticker in BENCHMARKS.items()}
    prices_df = prices_df.rename(columns=rename_map)

    # --------------------------------------------------------
    # Calculate returns
    # --------------------------------------------------------
    returns_df = calculate_daily_returns(prices_df)

    if returns_df.empty:
        raise RuntimeError("returns_df is empty. Cannot run backtest.")

    # --------------------------------------------------------
    # Calculate portfolio returns
    # --------------------------------------------------------
    portfolio_returns = calculate_portfolio_returns(
        returns_df=returns_df,
        portfolio_weights=PORTFOLIO_WEIGHTS
    )

    benchmark_names = list(BENCHMARKS.keys())

    missing_benchmarks = [
        benchmark for benchmark in benchmark_names
        if benchmark not in returns_df.columns
    ]

    if missing_benchmarks:
        raise ValueError(
            f"The following benchmarks are missing from returns_df: {missing_benchmarks}"
        )

    benchmark_returns_df = returns_df[benchmark_names].copy()

    combined_returns_df = pd.concat(
        [portfolio_returns, benchmark_returns_df],
        axis=1
    ).dropna()

    if combined_returns_df.empty:
        raise RuntimeError("combined_returns_df is empty. Cannot run backtest.")

    print("\nCombined returns:")
    print(combined_returns_df.head())
    print(combined_returns_df.tail())
    print(f"combined_returns_df shape: {combined_returns_df.shape}")

    # --------------------------------------------------------
    # Growth of $100,000
    # --------------------------------------------------------
    growth_df = calculate_growth_of_investment(
        returns_df=combined_returns_df,
        initial_investment=INITIAL_INVESTMENT
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------
    metrics_df = calculate_performance_metrics(
        growth_df=growth_df,
        returns_df=combined_returns_df,
        risk_free_rate=RISK_FREE_RATE
    )

    annual_returns_df = calculate_annual_returns(combined_returns_df)
    monthly_returns_df = calculate_monthly_returns(combined_returns_df)
    drawdown_df = calculate_drawdowns(growth_df)

    # --------------------------------------------------------
    # Create charts
    # --------------------------------------------------------
    growth_chart = make_growth_chart(growth_df)
    drawdown_chart = make_drawdown_chart(drawdown_df)
    annual_returns_chart = make_annual_returns_chart(annual_returns_df)
    allocation_chart = make_allocation_chart(PORTFOLIO_WEIGHTS)
    correlation_chart = make_correlation_heatmap(combined_returns_df)

    # --------------------------------------------------------
    # Build HTML dashboard
    # --------------------------------------------------------
    dashboard_html = build_dashboard_html(
        metrics_df=metrics_df,
        annual_returns_df=annual_returns_df,
        monthly_returns_df=monthly_returns_df,
        portfolio_weights=PORTFOLIO_WEIGHTS,
        growth_chart=growth_chart,
        drawdown_chart=drawdown_chart,
        annual_returns_chart=annual_returns_chart,
        allocation_chart=allocation_chart,
        correlation_chart=correlation_chart
    )

    OUTPUT_HTML.write_text(dashboard_html, encoding="utf-8")

    # --------------------------------------------------------
    # Console outputs
    # --------------------------------------------------------
    print("\nBacktest complete.")
    print(f"Dashboard saved to: {OUTPUT_HTML.resolve()}")

    print("\nPerformance Metrics:")
    print(metrics_df.to_string(index=False))

    print("\nDataFrames created in memory:")
    print("prices_df")
    print("returns_df")
    print("combined_returns_df")
    print("growth_df")
    print("metrics_df")
    print("annual_returns_df")
    print("monthly_returns_df")
    print("drawdown_df")


if __name__ == "__main__":
    main()



