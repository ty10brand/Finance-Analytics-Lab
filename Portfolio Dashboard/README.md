

# Portfolio Backtesting Dashboard

## Overview

This project is a Python-based portfolio backtesting dashboard that evaluates the historical performance of a hypothetical equity portfolio against benchmark ETFs. The project downloads historical market data, calculates portfolio-level returns, computes key risk and performance metrics, and exports a polished static HTML dashboard with interactive charts and tables.

The initial version of the dashboard analyzes an equal-weight technology-oriented portfolio consisting of:

* AAPL
* MSFT
* NVDA
* AMZN
* GOOGL

The portfolio is compared against the following benchmarks:

* SPY
* VOO
* VUG

The dashboard assumes an initial investment of `$100,000` and evaluates portfolio growth over the selected backtesting period.

## Project Purpose

The purpose of this project is to demonstrate a practical quant finance workflow in Python, including:

* Historical price data collection
* Return calculation
* Portfolio construction
* Benchmark comparison
* Risk and performance analytics
* Static HTML dashboard generation
* Interactive financial visualization

This project is intended for educational and portfolio-building purposes. It is not financial advice.

## Features

The dashboard includes:

* Growth of `$100,000` chart
* Portfolio vs benchmark comparison
* Performance metrics table
* Total return
* CAGR
* Annualized volatility
* Sharpe ratio
* Maximum drawdown
* Beta vs SPY
* Annual alpha vs SPY
* Annual returns chart
* Monthly returns table
* Drawdown analysis
* Rolling one-year return
* Rolling one-year volatility
* Correlation matrix
* Portfolio allocation chart
* Static HTML dashboard output
* Dark-mode tabbed dashboard design

## Technologies Used

* Python
* pandas
* NumPy
* yfinance
* Plotly
* HTML
* CSS
* JavaScript

## Project Structure

```text
Portfolio Dashboard/
│
├── Portfolio Dashboard v1.py
├── Portfolio Dashboard v2.py
│
├── outputs/
│   ├── portfolio_backtest_dashboard.html
│   └── portfolio_backtest_dashboard_v2.html
│
└── README.md
```

## Main Files

### `Portfolio Dashboard v1.py`

The first version of the dashboard. This version produces a clean static HTML report with summary cards, charts, and tables.

### `Portfolio Dashboard v2.py`

The second version of the dashboard. This version adds a dark-mode design, tabbed navigation, additional analytics, and a more polished user interface.

### `outputs/portfolio_backtest_dashboard_v2.html`

The generated static HTML dashboard. This file can be opened directly in a web browser and does not require a backend server.

## Installation

Before running the project, install the required Python packages:

```bash
pip install pandas numpy yfinance plotly requests
```

If using Anaconda on Windows, the command may look like:

```powershell
C:\Users\yourname\anaconda3\python.exe -m pip install pandas numpy yfinance plotly requests
```

## Recommended Library Versions

The project was tested using:

```text
numpy 1.26.4
pandas 2.2.3
yfinance 1.3.0
requests 2.32.3
plotly 5.24.1
```

## Customizing the Portfolio

To test a different portfolio, edit the `PORTFOLIO_WEIGHTS` dictionary in the Python script:

```python
PORTFOLIO_WEIGHTS = {
    "AAPL": 0.20,
    "MSFT": 0.20,
    "NVDA": 0.20,
    "AMZN": 0.20,
    "GOOGL": 0.20,
}
```

Weights must sum to `1.00`.

For example:

```python
PORTFOLIO_WEIGHTS = {
    "COST": 0.25,
    "WMT": 0.25,
    "AMZN": 0.25,
    "TGT": 0.25,
}
```

## Customizing Benchmarks

Benchmarks can be changed in the `BENCHMARKS` dictionary:

```python
BENCHMARKS = {
    "SPY": "SPY",
    "VOO": "VOO",
    "VUG": "VUG",
}
```

Example alternative benchmarks:

```python
BENCHMARKS = {
    "SPY": "SPY",
    "QQQ": "QQQ",
    "DIA": "DIA",
}
```

## Key Metrics

### Total Return

Measures the full-period percentage return of the portfolio.

### CAGR

Compound annual growth rate. This shows the annualized return over the full backtest period.

### Annualized Volatility

Measures the standard deviation of daily returns annualized using 252 trading days.

### Sharpe Ratio

Measures risk-adjusted performance using an assumed annual risk-free rate.

### Maximum Drawdown

Measures the largest peak-to-trough decline during the backtest period.

### Beta vs SPY

Measures the portfolio's sensitivity to the SPY benchmark.

### Annual Alpha vs SPY

Estimates annualized excess return relative to the expected return implied by the portfolio's beta versus SPY.

## Notes on Data

This project uses `yfinance` to download historical market data from Yahoo Finance. Since `yfinance` relies on public Yahoo Finance endpoints, data downloads may occasionally fail due to rate limits, network issues, or changes in Yahoo's data access behavior.

If data downloads fail, possible solutions include:

* Wait and rerun the script later
* Try a different network or phone hotspot
* Reduce the number of repeated download attempts
* Save downloaded data locally as CSV files
* Use a paid or API-key-based data provider

## Limitations

This project is a simplified educational backtester. It currently does not include:

* Transaction costs
* Taxes
* Slippage
* Bid/ask spreads
* Rebalancing schedules
* Dividend reinvestment assumptions beyond adjusted prices
* Survivorship bias correction
* Position-level trade simulation
* Short selling
* Margin
* Real-time data
* Portfolio optimization

## Future Improvements

Potential future enhancements include:

* Add user-defined rebalancing frequency
* Add transaction cost assumptions
* Add dividend analysis
* Add Monte Carlo simulation
* Add efficient frontier optimization
* Add Sortino ratio
* Add Calmar ratio
* Add downside deviation
* Add value-at-risk
* Add conditional value-at-risk
* Add rolling beta and rolling alpha
* Add downloadable report exports
* Add Streamlit or Flask web app version
* Add local CSV caching
* Add support for API-key-based data providers

## Disclaimer

This project is for educational and research purposes only. It is not investment advice, financial advice, or a recommendation to buy or sell any security. Historical performance does not guarantee future results.


