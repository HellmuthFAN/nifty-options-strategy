import pandas as pd
import numpy as np

# CAPITAL ALLOCATION AND PORTFOLIO VALUE CALCULATION EXPLAINED
# ===========================================================

print("="*80)
print("CAPITAL ALLOCATION & PORTFOLIO VALUE CALCULATION")
print("="*80)

# --- UNDERSTANDING THE CAPITAL STRUCTURE ---

print("\n1. INITIAL CAPITAL STRUCTURE")
print("-" * 40)

# In our strategy, we need to understand two types of capital:
initial_nav = 100000  # Starting portfolio value
lot_size = 50  # Assuming 50 shares per lot for Nifty

print(f"Initial Portfolio Value (NAV): ₹{initial_nav:,}")
print(f"Lot Size: {lot_size} shares")

# --- CAPITAL ALLOCATION BREAKDOWN ---

print("\n2. CAPITAL ALLOCATION FOR EACH TRADE")
print("-" * 45)

# Example trade scenario
nifty_price = 24000
strike_price = 23500  # 2% OTM Put
put_premium = 150
margin_required = 120000  # Approximate margin for selling 1 lot of put

print(f"Current Nifty Price: ₹{nifty_price}")
print(f"Strike Price (2% OTM Put): ₹{strike_price}")
print(f"Put Premium Received: ₹{put_premium} per share")
print(f"Margin Required for Put Selling: ₹{margin_required:,}")
print(f"Spot Position Value: ₹{nifty_price * lot_size:,}")

# --- AFTER EACH TRADE: WHAT HAPPENS TO CAPITAL? ---

print("\n3. WHAT HAPPENS AFTER EACH TRADE?")
print("-" * 42)

# Portfolio components tracking
portfolio_components = {
    'cash': initial_nav,
    'spot_positions_value': 0,
    'options_margin_blocked': 0,
    'unrealized_pnl': 0,
    'realized_pnl': 0
}

print("Initial Portfolio Breakdown:")
for component, value in portfolio_components.items():
    print(f"  {component.replace('_', ' ').title()}: ₹{value:,}")

print("\n" + "="*60)
print("TRADE-BY-TRADE CAPITAL CALCULATION EXAMPLE")
print("="*60)

# --- TRADE 1: INITIAL SETUP ---
print("\nTRADE 1: Initial Setup (27-Dec-2012)")
print("-" * 35)

# Initial spot position
spot_entry_price = 5870
spot_position_value = spot_entry_price * lot_size
put_premium_received = 43.1 * lot_size

portfolio_components['spot_positions_value'] = spot_position_value
portfolio_components['cash'] = initial_nav - spot_position_value + put_premium_received
portfolio_components['options_margin_blocked'] = 60000  # Estimated margin

print(f"Action: Buy {lot_size} Nifty at ₹{spot_entry_price}")
print(f"Action: Sell Put (Strike: 5800) for ₹{43.1} premium")
print(f"Spot Position Value: ₹{spot_position_value:,}")
print(f"Premium Received: ₹{put_premium_received:,}")
print(f"Margin Blocked: ₹{portfolio_components['options_margin_blocked']:,}")

current_nav = sum(portfolio_components.values()) - portfolio_components['options_margin_blocked']
print(f"Current NAV: ₹{current_nav:,}")

# --- TRADE SETTLEMENT EXAMPLE ---
print("\nTRADE SETTLEMENT (31-Jan-2013)")
print("-" * 32)

settlement_price = 6034.75
put_expired_otm = settlement_price > 5800

if put_expired_otm:
    print(f"Nifty settled at ₹{settlement_price} > Strike (5800)")
    print("Put option expired OTM → Keep full premium")
    
    # Check if spot position hit 3% target
    target_price = spot_entry_price * 1.03
    spot_hit_target = settlement_price >= target_price
    
    if spot_hit_target:
        print(f"Spot position hit 3% target (₹{target_price:.2f})")
        spot_profit = (target_price - spot_entry_price) * lot_size
        portfolio_components['realized_pnl'] += spot_profit + put_premium_received
        portfolio_components['spot_positions_value'] = 0  # Closed position
        portfolio_components['options_margin_blocked'] = 0  # Released margin
        portfolio_components['cash'] = initial_nav + portfolio_components['realized_pnl']
        
        print(f"Spot Profit: ₹{spot_profit:,}")
        print(f"Option Profit: ₹{put_premium_received:,}")
        print(f"Total Realized P&L: ₹{portfolio_components['realized_pnl']:,}")

new_nav = sum(portfolio_components.values()) - portfolio_components['options_margin_blocked']
print(f"New NAV: ₹{new_nav:,}")

# --- PORTFOLIO VALUE CALCULATION METHODOLOGY ---

print("\n" + "="*60)
print("PORTFOLIO VALUE CALCULATION METHODOLOGY")
print("="*60)

def calculate_portfolio_value(cash, spot_positions, realized_pnl, unrealized_pnl, current_nifty_price):
    """
    Calculate total portfolio value at any point in time
    """
    # Market value of spot positions
    if len(spot_positions) > 0:
        spot_market_value = sum([pos['quantity'] * current_nifty_price for pos in spot_positions])
    else:
        spot_market_value = 0
    
    # Total portfolio value
    total_value = cash + spot_market_value + realized_pnl + unrealized_pnl
    
    return {
        'cash': cash,
        'spot_market_value': spot_market_value,
        'realized_pnl': realized_pnl,
        'unrealized_pnl': unrealized_pnl,
        'total_nav': total_value
    }

# Example calculation
current_positions = [{'quantity': 50, 'entry_price': 24000}]
current_nifty = 24500
cash_balance = 50000
realized_pnl = 25000
unrealized_pnl = (24500 - 24000) * 50  # Unrealized gain on current position

portfolio_value = calculate_portfolio_value(
    cash_balance, current_positions, realized_pnl, unrealized_pnl, current_nifty
)

print(f"\nEXAMPLE PORTFOLIO CALCULATION:")
print(f"Cash Balance: ₹{portfolio_value['cash']:,}")
print(f"Spot Positions Market Value: ₹{portfolio_value['spot_market_value']:,}")
print(f"Realized P&L: ₹{portfolio_value['realized_pnl']:,}")
print(f"Unrealized P&L: ₹{portfolio_value['unrealized_pnl']:,}")
print(f"TOTAL NAV: ₹{portfolio_value['total_nav']:,}")

# --- KEY CONCEPTS EXPLAINED ---

print("\n" + "="*60)
print("KEY CONCEPTS IN CAPITAL ALLOCATION")
print("="*60)

concepts = {
    "NAV (Net Asset Value)": "Total portfolio worth = Cash + Market Value of Holdings + All P&L",
    "Realized P&L": "Actual profits/losses from closed trades (added to cash)",
    "Unrealized P&L": "Paper profits/losses on open positions (marked-to-market)",
    "Margin Blocked": "Cash blocked by broker for options selling (not available for other trades)",
    "Free Cash": "Available cash for new trades = Total Cash - Margin Blocked",
    "Portfolio Return": "(Current NAV - Initial NAV) / Initial NAV * 100"
}

for concept, explanation in concepts.items():
    print(f"\n{concept}:")
    print(f"  {explanation}")

# --- CUMULATIVE RETURNS CALCULATION ---

print("\n" + "="*60)
print("HOW CUMULATIVE RETURNS ARE CALCULATED")
print("="*60)

# Sample trade history showing NAV progression
trade_history = [
    {'date': '2012-12-27', 'trade_pnl': 0, 'cumulative_pnl': 0, 'nav': 100000},
    {'date': '2013-01-31', 'trade_pnl': 2500, 'cumulative_pnl': 2500, 'nav': 102500},
    {'date': '2013-02-28', 'trade_pnl': 1800, 'cumulative_pnl': 4300, 'nav': 104300},
    {'date': '2013-03-28', 'trade_pnl': -1200, 'cumulative_pnl': 3100, 'nav': 103100},
    {'date': '2013-04-25', 'trade_pnl': 3200, 'cumulative_pnl': 6300, 'nav': 106300},
]

print("Sample NAV Progress:")
print("Date         Trade P&L    Cumulative P&L    NAV        Return%")
print("-" * 65)

for trade in trade_history:
    return_pct = (trade['nav'] / 100000 - 1) * 100
    print(f"{trade['date']}     {trade['trade_pnl']:>6}        {trade['cumulative_pnl']:>8}      {trade['nav']:>8}    {return_pct:>6.2f}%")

# --- CAGR CALCULATION ---

print(f"\nCAGR CALCULATION:")
print("-" * 20)
initial_value = 100000
final_value = 106300
years = 0.33  # 4 months ≈ 0.33 years
cagr = (final_value / initial_value) ** (1/years) - 1

print(f"Initial Value: ₹{initial_value:,}")
print(f"Final Value: ₹{final_value:,}")
print(f"Time Period: {years:.2f} years")
print(f"CAGR = ({final_value}/{initial_value})^(1/{years}) - 1")
print(f"CAGR = {cagr:.2%}")

print("\n" + "="*60)
print("IMPORTANT NOTES")
print("="*60)

notes = [
    "1. NAV includes both realized and unrealized P&L",
    "2. Options margin is blocked capital (not available for other uses)",
    "3. Spot positions are marked-to-market daily",
    "4. Each successful trade increases available capital for next trade",
    "5. Strategy compounds returns by reinvesting profits",
    "6. CAGR accounts for time value of money",
    "7. Real trading involves transaction costs not included here"
]

for note in notes:
    print(note)

print(f"\nThis methodology ensures accurate tracking of:")
print("• Capital utilization efficiency")
print("• Risk-adjusted returns")
print("• Portfolio growth over time")
print("• Comparison with benchmark returns")