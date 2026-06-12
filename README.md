# Nifty Options Strategy — Systematic Put-Writing with Drawdown Accumulation

A monthly Nifty-50 options strategy, backtested from **Dec 2012 to mid-2025** and
benchmarked against buy-and-hold. The strategy collects option premium by writing
out-of-the-money puts and **adds long exposure after losses** — a "penalizer" /
dip-accumulation rule.

> **Note:** this is *not* a straddle. It is a short-put + spot-accumulation
> strategy (see logic below).

---

## Strategy logic

- Hold a **long Nifty spot** position.
- **Sell 2% OTM puts monthly** and collect the premium.
- **Exit spot at +3% profit** (profit-taking; no stop loss).
- **Loss-triggered accumulation ("penalizer"):** whenever a written put expires
  **in-the-money** (a loss), open a **new long spot position** at the settlement
  price — so drawdowns *increase* exposure.
- **Put settlement:** keep the full premium if Nifty closes above the strike;
  otherwise the P&L is `premium − (strike − settlement)`.
- Performance is compared against a Nifty **buy-and-hold** benchmark.

---

## Files

| File | Purpose |
|------|---------|
| `src/nifty_options_backtest.py` | Event-driven backtest — month-end option data + Nifty OHLC (via Yahoo Finance), produces NAV, CAGR, win-rate, yearly P&L and a buy-and-hold comparison; writes an Excel report |
| `src/nifty_options_updated.py`  | Pulls month-end NIFTY OTM option premia from the NSE F&O bhavcopy with multi-endpoint fallbacks |
| `src/nse_url_generator.py`      | Generates and tests NSE bhavcopy download URLs (last trading day per month) |
| `src/capital_calculation_explanation.py` | Walkthrough of the capital-allocation / NAV / CAGR methodology |

## Data sources

- **Option premia:** NSE F&O bhavcopy (month-end, last trading day).
- **Spot OHLC:** Yahoo Finance `^NSEI`.

## Running

```bash
pip install pandas numpy yfinance requests openpyxl python-dateutil
python src/nifty_options_backtest.py
```

## Caveats

The backtest assumes **no transaction costs, taxes, or slippage** and perfect fills
at the stated month-end prices. Real-world results — especially for a frequent
put-writing strategy — would be materially lower. For research / educational use.

## Tech

Python · pandas · NumPy · yfinance · requests
