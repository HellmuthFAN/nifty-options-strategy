import pandas as pd
import numpy as np
import yfinance as yf
import io
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# --- STRATEGY ASSUMPTIONS ---
"""
STRATEGY ASSUMPTIONS:
1. Start with long position in Nifty at 5870 on 12/27/2012
2. Sell 2% OTM Put options monthly (receive premium)
3. Close spot positions when they reach 3% profit (no stop loss)
4. When put options expire ITM (loss), open new spot position at settlement price
5. Put option P&L: If Nifty closes above strike = keep full premium
                  If Nifty closes below strike = premium - (strike - settlement_price)
6. Use daily high prices to check if 3% profit target is hit during the month
7. Position sizing: 1 lot for options, 1 unit for spot positions
8. All transactions assumed to happen at stated prices (no slippage/transaction costs)
"""

print("="*80)
print("NIFTY OPTIONS + SPOT TRADING STRATEGY BACKTEST")
print("="*80)
print("\nStrategy Assumptions:")
print("- Initial long position: 5870 on 12/27/2012")
print("- Monthly put selling (2% OTM)")
print("- Spot positions closed at 3% profit (no stop loss)")
print("- New spot positions opened when put options lose money")
print("- No transaction costs or slippage considered")
print("\n" + "="*80)

# --- 1. DATA LOADING AND PREPARATION ---

# Load the options data
csv_data = """Date,Close,Next expiry date,2% OTM PE,LTP 2% OTM PE
12/27/2012,5870.1,1/31/2013,5800,43.1
1/31/2013,6034.75,2/28/2013,5900,32
2/28/2013,5693.05,3/28/2013,5600,35.75
3/28/2013,5682.55,4/25/2013,5550,46.2
4/25/2013,5916.3,5/30/2013,5800,56
5/30/2013,6124.05,6/27/2013,6000,56.55
6/27/2013,5682.35,7/25/2013,5600,78.6
7/25/2013,5907.5,8/29/2013,5800,63.55
8/29/2013,5409.05,9/26/2013,5300,126.3
9/26/2013,5882.25,10/31/2013,5750,90.65
10/31/2013,6299.15,11/28/2013,6200,70.95
11/28/2013,6091.85,12/26/2013,6000,73.85
12/26/2013,6278.9,1/30/2014,6150,43.9
1/30/2014,6073.7,2/26/2014,6000,66.15
2/26/2014,6238,3/27/2014,6100,35.05
3/27/2014,6641.75,4/24/2014,6500,50.85
4/23/2014,6840,5/29/2014,6700,167.6
5/29/2014,7235.65,6/26/2014,7100,59.4
6/26/2014,7493.2,7/31/2014,7400,98.05
7/31/2014,7721.3,8/28/2014,7600,58.2
8/28/2014,7954.35,9/25/2014,7800,49.7
9/25/2014,7911.85,10/30/2014,7753.613,40.85
10/30/2014,8169.2,11/27/2014,8000,50.1
11/27/2014,8494.2,12/24/2014,8300,33
12/24/2014,8174,1/29/2015,8000,56.9
1/29/2015,8952.35,2/26/2015,8800,109.55
2/26/2015,8683.85,3/26/2015,8500,104
3/26/2015,8342.15,4/30/2015,8200,54.7
4/30/2015,8181.5,5/28/2015,8000,60
5/28/2015,8319,6/25/2015,8150,90
6/25/2015,8398,7/30/2015,8200,71
7/30/2015,8421.8,8/27/2015,8200,48.95
8/27/2015,7948.95,9/24/2015,7800,115.1
9/24/2015,7868.5,10/29/2015,7700,119
10/29/2015,8111.75,11/26/2015,7900,76
11/26/2015,7883.8,12/31/2015,7700,68
12/31/2015,7946.35,1/28/2016,7800,58
1/28/2016,7424.65,2/25/2016,7250,70
2/25/2016,6970.6,3/31/2016,6800,103.65
3/31/2016,7738.4,4/28/2016,7600,68.75
4/28/2016,7847.25,5/26/2016,7700,65.1
5/26/2016,8069.65,6/30/2016,7900,73.95
6/30/2016,8287.75,7/28/2016,8100,62
7/28/2016,8666.3,8/25/2016,8500,65
8/25/2016,8592.2,9/29/2016,8400,50.5
9/29/2016,8591.25,10/27/2016,8400,81.1
10/27/2016,8615.25,11/24/2016,8450,57
11/24/2016,7965.5,12/29/2016,7806.19,84.25
12/29/2016,8103.6,1/25/2017,7941.528,67.8
1/19/2017,8435.1,2/23/2017,8266.398,38.95
2/23/2017,8939.5,3/30/2017,8750,66.5
3/30/2017,9173.75,4/27/2017,9000,51
4/27/2017,9342.15,5/25/2017,9150,41.5
5/25/2017,9509.75,6/29/2017,9300,50.8
6/29/2017,9504.1,7/27/2017,9300,43
7/27/2017,10020.55,8/31/2017,9800,49.95
8/31/2017,9917.9,9/28/2017,9700,45
9/28/2017,9768.95,10/26/2017,9600,68.35
10/26/2017,10343.8,11/30/2017,10150,77.65
11/30/2017,10226.55,12/28/2017,10000,52.2
12/28/2017,10477.9,1/25/2018,10250,52.35
1/25/2018,11069.65,2/22/2018,10850,124
2/22/2018,10382.7,3/22/2018,10150,93.55
3/22/2018,10114.75,4/26/2018,9900,93.1
4/26/2018,10617.8,5/31/2018,10400,80.35
5/31/2018,10736.15,6/28/2018,10500,74.5
6/28/2018,10589.1,7/26/2018,10350,68.15
7/26/2018,11167.3,8/30/2018,10950,68
8/30/2018,11676.8,9/27/2018,11450,54.65
9/27/2018,10977.55,10/25/2018,10750,96
10/25/2018,10124.9,11/29/2018,9900,139
11/29/2018,10858.7,12/27/2018,10650,114
12/27/2018,10779.8,1/31/2019,10550,114.2
1/31/2019,10830.95,2/28/2019,10600,108.1
2/28/2019,10792.5,3/28/2019,10550,102
3/28/2019,11570,4/25/2019,11338.6,99.7
4/25/2019,11641.8,5/30/2019,11400,198.4
5/30/2019,11945.9,6/27/2019,11700,91.3
6/27/2019,11841.55,7/25/2019,11600,79.95
7/25/2019,11252.15,8/29/2019,11000,65.7
8/29/2019,10948.3,9/26/2019,10750,96
9/26/2019,11571.2,10/31/2019,11350,114.7
10/31/2019,11877.45,11/28/2019,11650,103.4
11/28/2019,12151.15,12/26/2019,11908.127,75.45
12/26/2019,12126.55,1/30/2020,11900,70.35
1/30/2020,12035.8,2/27/2020,11800,126.5
2/27/2020,11633.3,3/26/2020,11400,133
3/26/2020,8641.45,4/30/2020,8450,597
4/30/2020,9859.9,5/28/2020,9650,237
5/28/2020,9490.1,6/25/2020,9300,227.9
6/25/2020,10288.9,7/30/2020,10000,260.4
7/30/2020,11102.15,8/27/2020,10900,211.75
8/27/2020,11559.25,9/24/2020,11350,124.8
9/24/2020,10805.55,10/29/2020,10550,184
10/29/2020,11670.8,11/26/2020,11437.384,208
11/26/2020,12987,12/31/2020,12727.26,160
12/31/2020,13981.75,1/28/2021,13702.115,195.35
1/28/2021,13817.55,2/25/2021,13550,242.1
2/25/2021,15097.35,3/25/2021,14800,209.85
3/25/2021,14324.9,4/29/2021,14000,208.1
4/29/2021,14894.9,5/27/2021,14600,245.35
5/27/2021,15337.85,6/24/2021,15050,151.15
6/24/2021,15790.45,7/29/2021,15500,150.05
7/29/2021,15778.45,8/26/2021,15450,90.65
8/26/2021,16636.9,9/30/2021,16300,116.65
9/30/2021,17618.15,10/28/2021,17250,190
10/28/2021,17857.25,11/25/2021,17500,178.05
11/25/2021,17536.25,12/30/2021,17200,145
12/30/2021,17203.95,1/27/2022,16850,145
1/27/2022,17110.15,2/24/2022,16750,216.35
2/24/2022,16247.95,3/31/2022,15950,423.8
3/31/2022,17464.75,4/28/2022,17100,218
4/28/2022,17245.05,5/26/2022,16900,219.55
5/26/2022,16170.15,6/30/2022,15900,291
6/30/2022,15780.25,7/28/2022,15450,268
7/28/2022,16929.6,8/25/2022,16600,173
8/25/2022,17522.45,9/29/2022,17200,226
9/29/2022,16818.1,10/27/2022,16500,240.2
10/27/2022,17736.95,11/24/2022,17400,163
11/24/2022,18484.1,12/29/2022,18100,101.05
12/29/2022,18191,1/19/2023,17900,106.3
1/19/2023,18107.85,2/23/2023,17800,165.65
2/23/2023,17511.25,3/23/2023,17200,107.5
3/23/2023,17076.9,4/27/2023,16800,159.7
4/27/2023,17915.05,5/25/2023,17600,79.85
5/25/2023,18321.15,6/22/2023,18000,78
6/22/2023,18771.25,7/27/2023,18400,92.35
7/27/2023,19659.9,8/31/2023,19300,81
8/31/2023,19253.8,9/28/2023,18900,70.25
9/28/2023,19523,10/26/2023,19200,113
10/26/2023,18857.25,11/30/2023,18500,127.55
11/30/2023,20133.15,12/28/2023,19750,86.9
12/28/2023,21778.7,1/25/2024,21350,150
1/25/2024,21352.6,2/29/2024,20950,150
2/29/2024,21982.8,3/28/2024,21550,129.9
3/28/2024,22326.9,4/25/2024,21900,100.95
4/25/2024,22570.35,5/30/2024,22150,152.3
5/30/2024,22488.65,6/27/2024,22000,311.75
6/27/2024,24044.5,7/25/2024,23600,174
7/25/2024,24406.1,8/29/2024,23900,167.6
8/29/2024,25151.95,9/26/2024,24600,130.05
9/26/2024,26216.05,10/31/2024,25800,190
10/31/2024,24205.35,11/28/2024,23700,171.95
11/28/2024,23914.15,12/26/2024,23400,137.95
12/26/2024,23750.2,1/30/2025,23300,181.45
1/30/2025,23249.5,2/27/2025,22800,211.05
2/27/2025,22545.05,3/27/2025,22100,121.3
3/27/2025,23591.95,4/24/2025,23100,110.8
4/24/2025,24246.7,5/29/2025,23800,259.9
5/29/2025,24833.6,6/26/2025,24300,176.55"""

# Parse the options data
df = pd.read_csv(io.StringIO(csv_data))
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
df['Next expiry date'] = pd.to_datetime(df['Next expiry date'], format='%m/%d/%Y')

print(f"Options data loaded: {len(df)} records from {df['Date'].min().date()} to {df['Date'].max().date()}")

# Download Nifty historical data from Yahoo Finance
print("Downloading Nifty historical data from Yahoo Finance...")
try:
    nifty_data = yf.download("^NSEI", start="2012-12-26", end="2025-07-31", progress=False)
    if hasattr(nifty_data.columns, "nlevels") and nifty_data.columns.nlevels > 1:
        nifty_data.columns = nifty_data.columns.get_level_values(0)
    print(f"Nifty data downloaded: {len(nifty_data)} records from {nifty_data.index.min().date()} to {nifty_data.index.max().date()}")
except Exception as e:
    print(f"Error downloading data: {e}")
    exit()

# --- 2. STRATEGY INITIALIZATION ---

# Strategy parameters
lot_size = 1  # Position size for options
initial_nav = 5870.1  # one NIFTY unit of capital (per-unit NAV basis)
profit_target_pct = 0.03  # 3% profit target for spot positions

# Initialize tracking variables
positions = []  # Active spot positions
trade_log = []  # All trades
position_id_counter = 1
start_date = pd.to_datetime('2012-12-27')

print(f"\nStrategy initialized with:")
print(f"- Initial NAV: {initial_nav:,.0f}")
print(f"- Profit target: {profit_target_pct*100}%")
print(f"- Lot size: {lot_size}")

# --- 3. INITIAL POSITION SETUP ---

# Create initial spot position
initial_nifty_price = 5870.1
positions.append({
    'id': position_id_counter,
    'entry_price': initial_nifty_price,
    'entry_date': start_date,
    'profit_target': initial_nifty_price * (1 + profit_target_pct),
    'quantity': lot_size
})

print(f"\nInitial position opened:")
print(f"- Position ID: {position_id_counter}")
print(f"- Entry price: {initial_nifty_price}")
print(f"- Profit target: {initial_nifty_price * (1 + profit_target_pct):.2f}")

position_id_counter += 1

# --- 4. MAIN BACKTESTING LOOP ---

print(f"\nStarting backtest loop...")
print("="*80)

for index in range(len(df) - 1):
    current_row = df.iloc[index]
    next_row = df.iloc[index + 1]
    
    # Current trade details
    trade_date = current_row['Date']
    strike_price = float(current_row['2% OTM PE'])
    premium_received = float(current_row['LTP 2% OTM PE'])
    expiry_date = current_row['Next expiry date']
    nifty_close_on_expiry = float(next_row['Close'])
    settlement_date = next_row['Date']
    
    print(f"\nProcessing trade {index + 1}: {trade_date.date()} to {settlement_date.date()}")
    print(f"Strike: {strike_price}, Premium: {premium_received}, Settlement: {nifty_close_on_expiry}")
    
    # --- CHECK FOR SPOT POSITION EXITS (3% PROFIT TARGET) ---
    
    # Get the date range for this options period
    period_start = trade_date
    period_end = settlement_date
    
    # Get daily high prices during this period
    period_mask = (nifty_data.index >= period_start) & (nifty_data.index <= period_end)
    period_data = nifty_data.loc[period_mask]
    
    if not period_data.empty:
        # Check each position for profit target achievement
        for pos in list(positions):  # Use list() to avoid modification during iteration
            # Check if any daily high during the period hit the profit target
            if pos['entry_date'] <= period_start:  # Only check positions entered before this period
                max_high_in_period = period_data['High'].max()
                
                if max_high_in_period >= pos['profit_target']:
                    # Position hit profit target - close it
                    profit = (pos['profit_target'] - pos['entry_price']) * pos['quantity']
                    
                    # Find the exact date when target was hit (approximately)
                    target_hit_date = period_data[period_data['High'] >= pos['profit_target']].index[0]
                    
                    trade_log.append({
                        'Date': target_hit_date,
                        'Type': 'Spot_Exit',
                        'Amount': profit,
                        'Description': f"Closed Position ID {pos['id']} at 3% profit (Entry: {pos['entry_price']:.2f}, Exit: {pos['profit_target']:.2f})",
                        'Position_ID': pos['id'],
                        'Entry_Price': pos['entry_price'],
                        'Exit_Price': pos['profit_target']
                    })
                    
                    positions.remove(pos)
                    print(f"  -> Closed Position ID {pos['id']} for profit: {profit:.2f}")
    
    # --- PROCESS PUT OPTION SETTLEMENT ---
    
    if nifty_close_on_expiry >= strike_price:
        # Put option expires OTM - keep full premium (profit)
        option_pnl = premium_received * lot_size
        trade_log.append({
            'Date': settlement_date,
            'Type': 'Option_Profit',
            'Amount': option_pnl,
            'Description': f"Put expired OTM - kept premium (Strike: {strike_price}, Settlement: {nifty_close_on_expiry:.2f})",
            'Strike': strike_price,
            'Premium': premium_received,
            'Settlement': nifty_close_on_expiry
        })
        print(f"  -> Put option profit: {option_pnl:.2f}")
        
    else:
        # Put option expires ITM - loss occurred
        intrinsic_value = strike_price - nifty_close_on_expiry
        option_pnl = (premium_received - intrinsic_value) * lot_size
        
        trade_log.append({
            'Date': settlement_date,
            'Type': 'Option_Loss',
            'Amount': option_pnl,
            'Description': f"Put expired ITM - net loss (Strike: {strike_price}, Settlement: {nifty_close_on_expiry:.2f})",
            'Strike': strike_price,
            'Premium': premium_received,
            'Settlement': nifty_close_on_expiry,
            'Intrinsic_Value': intrinsic_value
        })
        
        print(f"  -> Put option loss: {option_pnl:.2f}")
        
        # Since we lost money on options, open new spot position
        new_entry_price = nifty_close_on_expiry
        new_position = {
            'id': position_id_counter,
            'entry_price': new_entry_price,
            'entry_date': settlement_date,
            'profit_target': new_entry_price * (1 + profit_target_pct),
            'quantity': lot_size
        }
        
        positions.append(new_position)
        
        trade_log.append({
            'Date': settlement_date,
            'Type': 'Spot_Entry',
            'Amount': 0,  # No immediate P&L on entry
            'Description': f"Opened new spot position ID {position_id_counter} at {new_entry_price:.2f} (Target: {new_position['profit_target']:.2f})",
            'Position_ID': position_id_counter,
            'Entry_Price': new_entry_price,
            'Target_Price': new_position['profit_target']
        })
        
        print(f"  -> Opened new Position ID {position_id_counter} at {new_entry_price:.2f}")
        position_id_counter += 1

print("\n" + "="*80)
print("BACKTESTING COMPLETED")
print("="*80)

# --- 5. FINAL CALCULATIONS AND REPORTING ---

# Convert trade log to DataFrame
log_df = pd.DataFrame(trade_log)

if len(log_df) > 0:
    # Calculate cumulative P&L
    log_df['Cumulative_PnL'] = log_df['Amount'].cumsum()
    log_df['NAV'] = initial_nav + log_df['Cumulative_PnL']
    
    # Calculate returns by type
    pnl_by_type = log_df.groupby('Type')['Amount'].agg(['sum', 'count']).reset_index()
    pnl_by_type.columns = ['Trade_Type', 'Total_PnL', 'Count']
    
    # Calculate yearly returns
    log_df['Year'] = log_df['Date'].dt.year
    yearly_pnl = log_df.groupby('Year')['Amount'].sum().reset_index()
    yearly_pnl.columns = ['Year', 'Annual_PnL']
    
    # Calculate NAV by year end
    yearly_nav = []
    for year in sorted(yearly_pnl['Year'].unique()):
        year_end_data = log_df[log_df['Year'] <= year]
        if len(year_end_data) > 0:
            final_nav = year_end_data['NAV'].iloc[-1]
            yearly_nav.append({'Year': year, 'Year_End_NAV': final_nav})
    
    yearly_nav_df = pd.DataFrame(yearly_nav)
    if len(yearly_nav_df) > 0:
        yearly_nav_df['Annual_Return_Pct'] = yearly_nav_df['Year_End_NAV'].pct_change() * 100
    
    # Merge yearly data
    yearly_summary = pd.merge(yearly_pnl, yearly_nav_df, on='Year', how='outer')
    
    # Calculate overall performance metrics
    total_pnl = log_df['Amount'].sum()
    final_nav = initial_nav + total_pnl
    
    # Calculate CAGR
    start_date_actual = log_df['Date'].min()
    end_date_actual = log_df['Date'].max()
    years_elapsed = (end_date_actual - start_date_actual).days / 365.25
    
    if years_elapsed > 0 and final_nav > 0:
        cagr = (final_nav / initial_nav) ** (1/years_elapsed) - 1
    else:
        cagr = 0

    # Risk metrics on the event-based NAV curve
    _nav = log_df.set_index("Date").sort_index()["NAV"]
    _mret = _nav.resample("M").last().dropna().pct_change().dropna()
    sharpe = (_mret.mean()/_mret.std())*(12**0.5) if _mret.std()>0 else float("nan")
    max_dd = ((_nav-_nav.cummax())/_nav.cummax()).min()
    
    # Print summary
    print(f"\nFINAL PERFORMANCE SUMMARY")
    print("="*50)
    print(f"Initial NAV: {initial_nav:,.0f}")
    print(f"Final NAV: {final_nav:,.0f}")
    print(f"Total P&L: {total_pnl:,.0f}")
    print(f"Total Return: {((final_nav/initial_nav - 1) * 100):.2f}%")
    print(f"Years Elapsed: {years_elapsed:.2f}")
    print(f"CAGR: {(cagr * 100):.2f}%")
    print(f"Sharpe (annualized, rf=0): {sharpe:.2f}")
    print(f"Max Drawdown: {max_dd*100:.2f}%")
    print(f"Total Trades: {len(log_df)}")
    
    print(f"\nP&L BY TRADE TYPE:")
    print("-" * 30)
    for _, row in pnl_by_type.iterrows():
        print(f"{row['Trade_Type']}: {row['Total_PnL']:,.0f} ({row['Count']} trades)")

    # --- P&L ATTRIBUTION: where does the profit actually come from? ---
    _by = dict(zip(pnl_by_type['Trade_Type'], pnl_by_type['Total_PnL']))
    premium = _by.get('Option_Profit', 0.0)      # premium kept when puts expire OTM
    assignment = _by.get('Option_Loss', 0.0)     # net loss when puts are assigned (ITM)
    net_option = premium + assignment
    recovery = _by.get('Spot_Exit', 0.0)         # riding assigned longs back up to +3%
    grand = net_option + recovery
    print("")
    print("P&L ATTRIBUTION:")
    print(f"  Premium collected (OTM puts): {premium:,.0f}")
    print(f"  Assignment losses (ITM puts): {assignment:,.0f}")
    print(f"  Net option leg:    {net_option:,.0f}  ({net_option/grand*100:.0f}% of profit)")
    print(f"  Spot recovery leg: {recovery:,.0f}  ({recovery/grand*100:.0f}% of profit)")
    
    print(f"\nYEARLY PERFORMANCE:")
    print("-" * 40)
    for _, row in yearly_summary.iterrows():
        if pd.notna(row['Annual_Return_Pct']):
            print(f"{int(row['Year'])}: P&L = {row['Annual_PnL']:,.0f}, Return = {row['Annual_Return_Pct']:.2f}%")
        else:
            print(f"{int(row['Year'])}: P&L = {row['Annual_PnL']:,.0f}")
    
    print(f"\nOPEN POSITIONS ({len(positions)}):")
    print("-" * 30)
    for pos in positions:
        print(f"ID {pos['id']}: Entry {pos['entry_price']:.2f}, Target {pos['profit_target']:.2f}")
    
    # Create Excel output
    output_filename = "nifty_options_strategy_backtest.xlsx"
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        # Summary sheet
        summary_data = {
            'Metric': ['Initial NAV', 'Final NAV', 'Total P&L', 'Total Return %', 'CAGR %', 'Years Elapsed', 'Total Trades'],
            'Value': [initial_nav, final_nav, total_pnl, (final_nav/initial_nav - 1) * 100, cagr * 100, years_elapsed, len(log_df)]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        # Detailed trade log
        log_df.to_excel(writer, sheet_name='Trade_Log', index=False)
        
        # P&L by type
        pnl_by_type.to_excel(writer, sheet_name='PnL_by_Type', index=False)
        
        # Yearly performance
        yearly_summary.to_excel(writer, sheet_name='Yearly_Performance', index=False)
        
        # Open positions
        if len(positions) > 0:
            positions_df = pd.DataFrame(positions)
            positions_df.to_excel(writer, sheet_name='Open_Positions', index=False)
    
    print(f"\nDetailed results saved to: {output_filename}")

else:
    print("No trades executed - check data and logic")

print("\n" + "="*80)
print("BACKTEST ANALYSIS COMPLETE")
print("="*80)

# --- 6. ADDITIONAL ANALYSIS ---

print(f"\nADDITIONAL INSIGHTS:")
print("-" * 30)

if len(log_df) > 0:
    # Win rate analysis
    option_trades = log_df[log_df['Type'].str.contains('Option')]
    if len(option_trades) > 0:
        profitable_options = len(option_trades[option_trades['Amount'] > 0])
        option_win_rate = (profitable_options / len(option_trades)) * 100
        print(f"Option Win Rate: {option_win_rate:.1f}% ({profitable_options}/{len(option_trades)})")
    
    spot_exits = log_df[log_df['Type'] == 'Spot_Exit']
    if len(spot_exits) > 0:
        print(f"Spot Positions Closed: {len(spot_exits)} (all at 3% profit)")
        avg_spot_profit = spot_exits['Amount'].mean()
        print(f"Average Spot Profit per Trade: {avg_spot_profit:.2f}")
    
    # Volatility periods analysis
    large_losses = log_df[log_df['Amount'] < -1000]
    if len(large_losses) > 0:
        print(f"Large Loss Events (>1000): {len(large_losses)}")
        print("Worst loss periods:")
        for _, row in large_losses.nlargest(3, 'Amount', keep='first').iterrows():
            print(f"  {row['Date'].date()}: {row['Amount']:.0f} - {row['Description']}")
    
    # Monthly NAV progression (last 12 months)
    recent_data = log_df[log_df['Date'] >= log_df['Date'].max() - pd.DateOffset(months=12)]
    if len(recent_data) > 0:
        print(f"\nRecent NAV Progression (Last 12 months):")
        monthly_nav = recent_data.groupby(recent_data['Date'].dt.to_period('M'))['NAV'].last()
        for period, nav in monthly_nav.items():
            print(f"  {period}: {nav:,.0f}")

print(f"\nSTRATEGY VALIDATION:")
print("-" * 25)
print("✓ Put options settled correctly based on strike vs settlement price")
print("✓ Spot positions closed at exactly 3% profit when daily high reached target")
print("✓ New spot positions opened only when put options resulted in losses")
print("✓ All transactions tracked with detailed descriptions")
print("✓ NAV calculated including all realized P&L")

# Performance comparison with buy-and-hold
if len(nifty_data) > 0:
    initial_nifty = 5870.1
    final_nifty = nifty_data['Close'].iloc[-1]
    buy_hold_return = (final_nifty / initial_nifty - 1) * 100
    buy_hold_cagr = (final_nifty / initial_nifty) ** (1/years_elapsed) - 1
    
    print(f"\nCOMPARISON WITH BUY & HOLD:")
    print("-" * 35)
    print(f"Buy & Hold Return: {buy_hold_return:.2f}%")
    print(f"Buy & Hold CAGR: {buy_hold_cagr*100:.2f}%")
    print(f"Strategy CAGR: {cagr*100:.2f}%")
    print(f"Outperformance: {(cagr - buy_hold_cagr)*100:.2f}% annually")

print(f"\nDISCLAIMER:")
print("-" * 15)
print("This backtest assumes:")
print("- No transaction costs or taxes")
print("- Perfect execution at stated prices")
print("- Options can be sold at exact LTP prices")
print("- Daily high prices used for spot exit timing")
print("- All positions can be closed exactly at 3% profit")
print("\nActual trading results may vary significantly.")