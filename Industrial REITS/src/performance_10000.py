

import os
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

RAW_DIR = "data/raw"
OUT_CHARTS = "outputs/charts"

DEFAULT_START = "2010-01-01"
INITIAL_INVESTMENT = 10_000

def load_tickers(path="config/tickers.yaml"):
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    reits = [t.upper() for t in cfg.get("reits", [])]
    benchmarks = [t.upper() for t in cfg.get("benchmarks", [])]
    return reits, benchmarks

def load_prices():
    path = os.path.join(RAW_DIR, "prices_daily.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing {path}. Run: python src/ingest_prices.py")
    prices = pd.read_csv(path, index_col=0, parse_dates=True).sort_index()
    prices = prices.dropna(axis=1, how="all")
    return prices

def to_monthly_last(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.resample("M").last()

def growth_of_investment(prices: pd.DataFrame, initial=10_000) -> pd.DataFrame:
    """
    Growth of $initial invested at the first valid observation for each column.
    Uses adjusted prices (auto_adjust=True) -> dividend-adjusted, total-return-like.
    """
    out = pd.DataFrame(index=prices.index)
    for c in prices.columns:
        s = prices[c].dropna()
        if s.empty:
            continue
        base = s.iloc[0]
        out[c] = (prices[c] / base) * initial
    return out

def _legend_outside(ax, ncol=4):
    # Put legend outside plot area
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.01, 0.5),
        borderaxespad=0.0,
        ncol=ncol,
        fontsize=9,
        frameon=False
    )

def plot_all_with_legend(growth: pd.DataFrame, tickers: list, outpath: str, title: str):
    fig, ax = plt.subplots(figsize=(14, 7))
    for t in tickers:
        if t in growth.columns:
            ax.plot(growth.index, growth[t], linewidth=1.5, label=t)

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Value ($)")
    _legend_outside(ax, ncol=2 if len(tickers) > 14 else 3)

    fig.tight_layout()
    fig.savefig(outpath, dpi=180, bbox_inches="tight")
    plt.close(fig)

def animate_lines(growth: pd.DataFrame, tickers: list, outpath: str, title: str, legend=True, fps=25):
    g = growth[tickers].dropna(how="all")
    x = g.index.to_pydatetime()

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel("Value ($)")

    ax.set_xlim(g.index.min(), g.index.max())
    ymax = np.nanmax(g.values)
    ax.set_ylim(0, ymax * 1.05)

    lines = {}
    for t in tickers:
        line, = ax.plot([], [], linewidth=2, label=t)
        lines[t] = line

    if legend:
        # Legend outside → reserve space on the right so it doesn't get clipped
        _legend_outside(ax, ncol=2 if len(tickers) > 14 else 3)
        fig.subplots_adjust(right=0.78)  # leaves room for outside legend

    def update(frame):
        for t in tickers:
            y = g[t].values[:frame+1]
            lines[t].set_data(x[:frame+1], y)
        return list(lines.values())

    anim = FuncAnimation(fig, update, frames=len(g.index), interval=30, blit=True)

    # Critical: ensure the saved frames include the outside legend
    anim.save(
        outpath,
        writer=PillowWriter(fps=fps),
        savefig_kwargs={"bbox_inches": "tight", "pad_inches": 0.3}
    )
    plt.close(fig)

def pick_top_bottom(growth: pd.DataFrame, reits: list, end_date=None, top_n=5, bottom_n=5):
    g = growth[reits].dropna(how="all")
    if end_date is None:
        end_date = g.dropna(how="all").index.max()
    last = g.loc[end_date].dropna()
    top = last.sort_values(ascending=False).head(top_n).index.tolist()
    bottom = last.sort_values(ascending=True).head(bottom_n).index.tolist()
    return top, bottom

def plot_top_bottom(growth: pd.DataFrame, reits: list, benchmarks: list, out_png: str, out_gif: str,
                    top_n=5, bottom_n=5):
    top, bottom = pick_top_bottom(growth, reits, top_n=top_n, bottom_n=bottom_n)

    # Ensure VNQ + SPY included if present
    keep = []
    for t in top + bottom + benchmarks:
        if t in growth.columns and t not in keep:
            keep.append(t)

    title = f"Top {top_n} + Bottom {bottom_n} Industrial REITs vs Benchmarks\nGrowth of ${INITIAL_INVESTMENT:,} (monthly, adjusted prices)"
    plot_all_with_legend(growth, keep, out_png, title)
    animate_lines(growth, keep, out_gif, title, legend=True)

def plot_vs_vnq_small_multiples(growth: pd.DataFrame, reits: list, vnq_ticker="VNQ", out_png="",
                               cols=3):
    if vnq_ticker not in growth.columns:
        raise ValueError(f"{vnq_ticker} not found in data (add it under benchmarks in config/tickers.yaml).")

    # Only keep REITs we have
    reits = [t for t in reits if t in growth.columns]
    n = len(reits)
    if n == 0:
        raise ValueError("No REIT tickers found in growth data.")

    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(16, 4.5 * rows), sharex=True, sharey=False)
    axes = np.array(axes).reshape(-1)

    for i, t in enumerate(reits):
        ax = axes[i]
        ax.plot(growth.index, growth[vnq_ticker], linewidth=2, label=vnq_ticker)
        ax.plot(growth.index, growth[t], linewidth=2, label=t)
        ax.set_title(f"{t} vs {vnq_ticker}")
        ax.set_ylabel("Value ($)")
        ax.legend(fontsize=9, frameon=False)

    # Hide empty panels
    for j in range(i + 1, len(axes)):
        axes[j].axis("off")

    fig.suptitle(f"Each Industrial REIT vs {vnq_ticker} — Growth of ${INITIAL_INVESTMENT:,} (monthly, adjusted prices)",
                 fontsize=16, y=1.01)
    fig.tight_layout()
    fig.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)

def animate_vs_vnq(growth: pd.DataFrame, reits: list, vnq_ticker="VNQ", out_dir="outputs/charts/vs_vnq_gifs"):
    os.makedirs(out_dir, exist_ok=True)
    if vnq_ticker not in growth.columns:
        raise ValueError(f"{vnq_ticker} not found in data.")

    for t in reits:
        if t not in growth.columns:
            continue
        keep = [vnq_ticker, t]
        title = f"{t} vs {vnq_ticker}\nGrowth of ${INITIAL_INVESTMENT:,} (monthly, adjusted prices)"
        out_gif = os.path.join(out_dir, f"growth_{t}_vs_{vnq_ticker}.gif")
        animate_lines(growth, keep, out_gif, title, legend=True, fps=25)

def main():
    os.makedirs(OUT_CHARTS, exist_ok=True)

    reits, benchmarks = load_tickers()
    prices = load_prices()

    # Keep only tickers we care about
    keep = [t for t in (reits + benchmarks) if t in prices.columns]
    if not keep:
        raise ValueError("No matching tickers found in prices_daily.csv. Check config/tickers.yaml.")

    prices = prices[keep].loc[prices.index >= pd.to_datetime(DEFAULT_START)]
    prices_m = to_monthly_last(prices)
    growth = growth_of_investment(prices_m, initial=INITIAL_INVESTMENT)

    # 1) Full universe plot + animation (with legend)
    all_tickers = [t for t in (reits + benchmarks) if t in growth.columns]
    png_all = os.path.join(OUT_CHARTS, "growth_10000_all.png")
    gif_all = os.path.join(OUT_CHARTS, "growth_10000_all.gif")
    title_all = f"Growth of ${INITIAL_INVESTMENT:,} (monthly, adjusted prices) — All tickers"
    plot_all_with_legend(growth, all_tickers, png_all, title_all)
    animate_lines(growth, all_tickers, gif_all, title_all, legend=True)

    # 2) Top 5 + Bottom 5 + benchmarks (clean)
    png_tb = os.path.join(OUT_CHARTS, "growth_10000_top5_bottom5.png")
    gif_tb = os.path.join(OUT_CHARTS, "growth_10000_top5_bottom5.gif")
    plot_top_bottom(growth, reits=[t for t in reits if t in growth.columns],
                    benchmarks=[t for t in benchmarks if t in growth.columns],
                    out_png=png_tb, out_gif=gif_tb, top_n=5, bottom_n=5)

    # 3) Each REIT vs VNQ (small multiples + per-ticker GIFs)
    png_vs = os.path.join(OUT_CHARTS, "growth_10000_vs_VNQ_grid.png")
    plot_vs_vnq_small_multiples(growth, reits=[t for t in reits if t in growth.columns],
                                vnq_ticker="VNQ", out_png=png_vs, cols=3)

    animate_vs_vnq(growth, reits=[t for t in reits if t in growth.columns],
                   vnq_ticker="VNQ", out_dir=os.path.join(OUT_CHARTS, "vs_vnq_gifs"))

    print(f"[OK] Wrote {png_all}")
    print(f"[OK] Wrote {gif_all}")
    print(f"[OK] Wrote {png_tb}")
    print(f"[OK] Wrote {gif_tb}")
    print(f"[OK] Wrote {png_vs}")
    print(f"[OK] Wrote per-ticker GIFs to outputs/charts/vs_vnq_gifs/")

if __name__ == "__main__":
    main()



