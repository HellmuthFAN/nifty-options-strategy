# Systematic Nifty Put-Writing Strategy — Backtest & P&L Attribution

A 12-year event-driven backtest (2013–2025, 149 monthly cycles) of a systematic Nifty
index **put-writing strategy**, with full P&L attribution. Built in Python — spot data
from Yahoo Finance, option premia from the NSE F&O bhavcopy.

---

## Strategy (the "wheel")

- Each monthly expiry, **write (sell) a 2% OTM Nifty put** and collect the premium.
- If it expires **OTM** → keep the full premium and re-write the next month.
- If it is **assigned (ITM)** → convert into a **long index position** at settlement and
  **hold it to recovery**, squaring off at **+3%** (no stop loss).
- NAV is tracked on a **one-NIFTY-unit capital basis**.

## Results *(verified, one NIFTY unit of capital)*

| Metric | Value |
|---|---|
| Cumulative return | **~294%** |
| CAGR | **11.7%** |
| Sharpe (rf = 0) | **~1.2** |
| Max drawdown | **−21%** (Mar 2020, COVID) |
| Positive months | **82%** |
| Buy-and-hold CAGR (benchmark) | ~12.4% |

## The key finding — where the profit actually comes from

Full P&L attribution over the 12 years:

| Leg | NIFTY pts | Share |
|---|---:|---:|
| Premium collected (OTM puts) | +13,539 | |
| Assignment losses (ITM puts) | −9,238 | |
| **Net option leg** | **+4,301** | **25%** |
| **Spot recovery leg** | **+12,984** | **75%** |
| **Total** | **+17,285** | **100%** |

**~75% of the profit comes from riding assigned positions back up (mean-reversion), not
from the option premium.** This is really a *conditional long-beta / mean-reversion bet
wearing a put-selling costume* — and it in fact slightly **underperforms buy-and-hold
(−0.6%/yr)**, because the +3% take-profit caps the upside.

## Caveats *(read before trusting the Sharpe)*

- **No margin model.** Short-put margin (SPAN + ELM) balloons during the exact vol spike
  that assigns you — in March 2020 that could have forced liquidation at the −21% trough,
  before any recovery.
- **No costs / slippage.** The thin +4,301 net option leg is the most fragile part; a few
  points of bid–ask per put eats into it directly.
- **Regime-dependent.** The edge relies on V-shaped recoveries; the 2013–25 sample is a
  near-uninterrupted Indian bull market.

## Files

| File | Purpose |
|------|---------|
| `src/nifty_options_backtest.py` | Canonical event-driven backtest — NAV, CAGR, Sharpe, max-drawdown, P&L attribution, buy-and-hold comparison (runs on Yahoo Finance data) |
| `src/nifty_options_updated.py` | Pulls month-end NIFTY option premia from the NSE F&O bhavcopy (multi-endpoint fallback) |
| `src/nse_url_generator.py` | Builds and tests NSE bhavcopy download URLs |
| `src/capital_calculation_explanation.py` | NAV / capital-allocation methodology walkthrough |

## Run

```bash
pip install pandas numpy yfinance requests openpyxl python-dateutil
python src/nifty_options_backtest.py
```

## Tech

Python · pandas · NumPy · yfinance · NSE F&O bhavcopy
