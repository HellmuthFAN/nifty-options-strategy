# ==============================================================================
#  NIFTY Month-End 1-Month OTM Call Premium Analysis (NSE + Alternative Sources)
#  Updated to handle NSE's authentication changes and provide fallback options
# ==============================================================================

import requests
import pandas as pd
from datetime import date, timedelta
import time
import calendar
from io import BytesIO
import zipfile
from dateutil.relativedelta import relativedelta
import json
import warnings
from urllib.parse import quote
import os
warnings.filterwarnings('ignore')

# ==============================================================================
#                               CONFIGURATION
# ==============================================================================
START_YEAR = 2024
START_MONTH = 7
END_YEAR = 2025
END_MONTH = 7  # Up to July 2025

OTM_PERCENTAGES = [0.01, 0.02, 0.03] # +1%, +2%, +3%
# ==============================================================================

def get_next_month_monthly_expiry(current_date: date) -> date:
    """Precisely calculates the expiry date (last Thursday) of the month AFTER the given current_date."""
    next_month_date = current_date + relativedelta(months=1)
    year, month = next_month_date.year, next_month_date.month
    last_day = calendar.monthrange(year, month)[1]
    expiry_date = date(year, month, last_day)
    while expiry_date.weekday() != 3:
        expiry_date -= timedelta(days=1)
    return expiry_date

def setup_robust_nse_session():
    """Set up a session with enhanced authentication handling for NSE."""
    session = requests.Session()
    
    # More comprehensive headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"'
    }
    
    session.headers.update(headers)
    
    try:
        print("  -> Initializing NSE session with enhanced authentication...")
        
        # Step 1: Visit main page to get initial cookies
        main_response = session.get('https://www.nseindia.com', timeout=30)
        main_response.raise_for_status()
        print("  -> Main page loaded successfully")
        
        # Step 2: Visit market data page to establish session
        market_response = session.get('https://www.nseindia.com/market-data', timeout=30)
        market_response.raise_for_status()
        print("  -> Market data page loaded")
        
        # Step 3: Visit derivatives page
        derivatives_response = session.get('https://www.nseindia.com/market-data/derivatives-market', timeout=30)
        derivatives_response.raise_for_status()
        print("  -> Derivatives page loaded")
        
        # Step 4: Try to get an API response to validate session
        test_url = 'https://www.nseindia.com/api/market-data-pre-open?key=NIFTY'
        session.headers.update({'Referer': 'https://www.nseindia.com/market-data/derivatives-market'})
        
        test_response = session.get(test_url, timeout=30)
        if test_response.status_code == 200:
            print("  -> ✅ Session validation successful!")
            return session
        else:
            print(f"  -> ⚠️  Session validation returned status: {test_response.status_code}")
            return session  # Return anyway, might work for historical data
            
    except Exception as e:
        print(f"  -> ❌ Session setup failed: {e}")
        return session  # Return basic session as fallback

def download_bhavcopy_direct_api(report_date: date, session: requests.Session):
    """Try to download using NSE's direct API endpoints."""
    try:
        date_str = report_date.strftime('%d-%m-%Y')
        
        # Try the historical data API endpoint
        api_url = f'https://www.nseindia.com/api/historical/fo/derivatives'
        params = {
            'from': date_str,
            'to': date_str,
            'instrumentType': 'OPTIDX,FUTIDX',
            'symbol': 'NIFTY'
        }
        
        response = session.get(api_url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                df = pd.DataFrame(data['data'])
                print(f"    -> ✅ Downloaded {len(df)} records via direct API")
                return df
                
    except Exception as e:
        print(f"    -> Direct API failed: {e}")
    
    return None

def download_bhavcopy_reports_api(report_date: date, session: requests.Session):
    """Try using the reports API with better authentication."""
    try:
        date_str = report_date.strftime('%d-%b-%Y')
        
        # First, get the reports page to establish context
        reports_url = 'https://www.nseindia.com/all-reports-derivatives'
        session.get(reports_url, timeout=30)
        
        # Update headers for API call
        session.headers.update({
            'Referer': reports_url,
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        # Try the reports API
        api_url = 'https://www.nseindia.com/api/reports'
        params = {
            'archives': json.dumps([{
                "name": "F&O - Bhavcopy(csv)",
                "type": "archives",
                "category": "derivatives",
                "section": "equity"
            }]),
            'date': date_str,
            'type': 'equity',
            'mode': 'single'
        }
        
        response = session.get(api_url, params=params, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0 and 'file' in data[0]:
                download_url = data[0]['file']
                print(f"    -> Found download URL: {download_url[:50]}...")
                
                # Download the file
                file_response = session.get(download_url, timeout=60)
                file_response.raise_for_status()
                
                # Handle zip or direct CSV
                if download_url.endswith('.zip'):
                    with zipfile.ZipFile(BytesIO(file_response.content)) as z:
                        with z.open(z.namelist()[0]) as f:
                            df = pd.read_csv(f)
                else:
                    df = pd.read_csv(BytesIO(file_response.content))
                
                df.columns = df.columns.str.strip()
                print(f"    -> ✅ Downloaded {len(df)} records via reports API")
                return df
                
    except Exception as e:
        print(f"    -> Reports API failed: {e}")
    
    return None

def download_bhavcopy_archive_urls(report_date: date, session: requests.Session):
    """Try multiple archive URL patterns with both ZIP and CSV formats."""
    date_str = report_date.strftime('%d%b%Y').upper()
    
    # Multiple URL patterns to try (both ZIP and CSV)
    base_urls = [
        'https://archives.nseindia.com/content/historical/DERIVATIVES',
        'https://nsearchives.nseindia.com/content/historical/DERIVATIVES',
        'https://www1.nseindia.com/content/historical/DERIVATIVES',
        'https://www.nseindia.com/content/historical/DERIVATIVES'
    ]
    
    # Try both ZIP and CSV formats
    file_patterns = [
        f"fo{date_str}bhav.csv.zip",
        f"fo{date_str}bhav.csv"
    ]
    
    for base_url in base_urls:
        for file_pattern in file_patterns:
            try:
                url = f"{base_url}/{report_date.year}/{report_date.strftime('%b').upper()}/{file_pattern}"
                print(f"    -> Trying: {url}")
                
                response = session.get(url, timeout=60)
                response.raise_for_status()
                
                # Handle both ZIP and CSV files
                if file_pattern.endswith('.zip'):
                    try:
                        with zipfile.ZipFile(BytesIO(response.content)) as z:
                            with z.open(z.namelist()[0]) as f:
                                df = pd.read_csv(f)
                                df.columns = df.columns.str.strip()
                                print(f"    -> ✅ Downloaded {len(df)} records from ZIP archive")
                                return df
                    except zipfile.BadZipFile:
                        # Sometimes ZIP files are actually CSV, try reading as CSV
                        df = pd.read_csv(BytesIO(response.content))
                        df.columns = df.columns.str.strip()
                        print(f"    -> ✅ Downloaded {len(df)} records from CSV (mislabeled as ZIP)")
                        return df
                else:
                    # Direct CSV file
                    df = pd.read_csv(BytesIO(response.content))
                    df.columns = df.columns.str.strip()
                    print(f"    -> ✅ Downloaded {len(df)} records from CSV archive")
                    return df
                    
            except Exception as e:
                print(f"    -> URL failed: {str(e)[:50]}...")
                continue
    
    return None

def download_bhavcopy_for_date(report_date: date, session: requests.Session):
    """Try multiple methods to download bhavcopy data."""
    print(f"  -> Attempting to download data for {report_date}...")
    
    # Method 1: Direct API
    df = download_bhavcopy_direct_api(report_date, session)
    if df is not None:
        return df
    
    # Method 2: Reports API
    df = download_bhavcopy_reports_api(report_date, session)
    if df is not None:
        return df
    
    # Method 3: Archive URLs
    df = download_bhavcopy_archive_urls(report_date, session)
    if df is not None:
        return df
    
    print(f"  -> ❌ All methods failed for {report_date}")
    return None

def get_manual_data_for_date(report_date: date):
    """Provide manual data entry option when automatic download fails."""
    print(f"\n📝 MANUAL DATA ENTRY for {report_date}")
    print("Please visit: https://www.nseindia.com/all-reports-derivatives")
    print("And download the F&O Bhavcopy for the above date manually.")
    print("Save it as 'manual_data.csv' in the same directory as this script.")
    
    # Check if manual file exists
    if os.path.exists('manual_data.csv'):
        try:
            df = pd.read_csv('manual_data.csv')
            df.columns = df.columns.str.strip()
            print(f"  -> ✅ Loaded manual data: {len(df)} records")
            return df
        except Exception as e:
            print(f"  -> ❌ Error reading manual data: {e}")
    
    return None

def get_last_trading_day_data(year: int, month: int, session: requests.Session):
    """Find and download the last trading day data for a given month."""
    last_day_of_month = calendar.monthrange(year, month)[1]
    
    for day in range(last_day_of_month, 0, -1):
        current_date = date(year, month, day)
        
        # Skip weekends
        if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
            continue
            
        print(f"\n-> Checking for data on {current_date} ({calendar.day_name[current_date.weekday()]})...")
        
        # Try automatic download
        df = download_bhavcopy_for_date(current_date, session)
        
        if df is not None:
            print(f"    ✅ SUCCESS: Found data for {current_date}")
            return df, current_date
        
        # If automatic fails, offer manual option
        print(f"    -> Automatic download failed. Trying manual data option...")
        df = get_manual_data_for_date(current_date)
        
        if df is not None:
            return df, current_date
        
        # Small delay before trying next date
        time.sleep(2)
    
    return None, None

def process_options_data(df, spot_price, target_expiry, trade_date):
    """Process the options data to extract premiums."""
    
    # Standardize column names
    column_mapping = {
        'EXPIRY_DT': 'EXPIRY_DT',
        'EXPIRY_DATE': 'EXPIRY_DT',
        'OPTION_TYP': 'OPTION_TYP',
        'OPTIONTYPE': 'OPTION_TYP',
        'STRIKE_PR': 'STRIKE_PR',
        'STRIKE_PRICE': 'STRIKE_PR',
        'STRIKE': 'STRIKE_PR'
    }
    
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # Parse expiry dates
    try:
        df['EXPIRY_DT'] = pd.to_datetime(df['EXPIRY_DT'], format='%d-%b-%Y', errors='coerce')
        if df['EXPIRY_DT'].isna().all():
            # Try alternative formats
            df['EXPIRY_DT'] = pd.to_datetime(df['EXPIRY_DT'], format='%Y-%m-%d', errors='coerce')
    except Exception as e:
        print(f"    -> Error parsing expiry dates: {e}")
        return None
    
    # Filter call options for target expiry
    calls = df[
        (df['INSTRUMENT'].isin(['OPTIDX', 'OPTSTK'])) & 
        (df['SYMBOL'] == 'NIFTY') &
        (df['OPTION_TYP'] == 'CE') & 
        (df['EXPIRY_DT'].dt.date == target_expiry)
    ]
    
    if calls.empty:
        print(f"    -> No call options found for expiry {target_expiry}")
        print(f"    -> Available expiries: {sorted(df['EXPIRY_DT'].dt.date.unique())}")
        return None
    
    result_row = {
        'Month End Date': trade_date.strftime('%Y-%m-%d'),
        'Nifty Spot (Proxy)': round(spot_price, 2),
        'Target Expiry': target_expiry.strftime('%Y-%m-%d')
    }
    
    # Calculate premiums for each OTM percentage
    for pct in OTM_PERCENTAGES:
        target_strike = spot_price * (1 + pct)
        
        # Find closest strike
        strike_diff = (calls['STRIKE_PR'] - target_strike).abs()
        if not strike_diff.empty:
            closest_idx = strike_diff.idxmin()
            closest_option = calls.loc[closest_idx]
            
            result_row[f'+{int(pct*100)}% Strike'] = closest_option['STRIKE_PR']
            result_row[f'+{int(pct*100)}% Premium'] = round(closest_option['CLOSE'], 2)
            
            print(f"    -> +{int(pct*100)}%: Strike {closest_option['STRIKE_PR']}, Premium {closest_option['CLOSE']:.2f}")
    
    return result_row

def main():
    """Main execution function."""
    print("="*80)
    print("NIFTY Month-End Options Premium Analysis")
    print(f"Period: {START_MONTH}/{START_YEAR} to {END_MONTH}/{END_YEAR}")
    print("="*80)
    
    # Setup session
    session = setup_robust_nse_session()
    
    analysis_results = []
    
    # Process each month
    current_date = date(START_YEAR, START_MONTH, 1)
    end_date = date(END_YEAR, END_MONTH, 1)
    
    while current_date < end_date:
        year, month = current_date.year, current_date.month
        
        print(f"\n{'='*50}")
        print(f"Processing Month: {calendar.month_name[month]} {year}")
        print(f"{'='*50}")
        
        # Get last trading day data for the month
        month_end_df, trade_date = get_last_trading_day_data(year, month, session)
        
        if month_end_df is None:
            print(f"❌ Could not get data for {calendar.month_name[month]} {year}")
            
            # Ask user if they want to continue or provide manual data
            print("\nOptions:")
            print("1. Skip this month and continue")
            print("2. Provide manual data (save as 'manual_data.csv')")
            print("3. Exit")
            
            choice = input("Enter your choice (1/2/3): ").strip()
            
            if choice == '2':
                df = get_manual_data_for_date(date(year, month, 1))
                if df is not None:
                    month_end_df = df
                    trade_date = date(year, month, calendar.monthrange(year, month)[1])
                    while trade_date.weekday() >= 5:
                        trade_date -= timedelta(days=1)
                else:
                    current_date += relativedelta(months=1)
                    continue
            elif choice == '3':
                break
            else:
                current_date += relativedelta(months=1)
                continue
        
        # Get NIFTY futures data for spot price proxy
        nifty_futures = month_end_df[
            (month_end_df['INSTRUMENT'] == 'FUTIDX') & 
            (month_end_df['SYMBOL'] == 'NIFTY')
        ]
        
        if nifty_futures.empty:
            print(f"    -> No NIFTY futures data found for {trade_date}")
            current_date += relativedelta(months=1)
            continue
        
        # Get spot price from nearest expiry future
        spot_price = nifty_futures.sort_values(by='EXPIRY_DT').iloc[0]['CLOSE']
        
        # Calculate target expiry
        target_expiry = get_next_month_monthly_expiry(trade_date)
        print(f"    -> Spot Price: {spot_price:.2f}")
        print(f"    -> Target Expiry: {target_expiry}")
        
        # Process options data
        result_row = process_options_data(month_end_df, spot_price, target_expiry, trade_date)
        
        if result_row is not None:
            analysis_results.append(result_row)
            print(f"    -> ✅ Successfully processed {calendar.month_name[month]} {year}")
        else:
            print(f"    -> ❌ Failed to process options data for {calendar.month_name[month]} {year}")
        
        # Move to next month
        current_date += relativedelta(months=1)
        
        # Delay between months
        time.sleep(3)
    
    # Save results
    if not analysis_results:
        print("\n❌ No data could be analyzed for the specified period.")
        return
    
    final_df = pd.DataFrame(analysis_results)
    output_filename = f"NIFTY_MonthEnd_Premia_{START_YEAR}-{START_MONTH:02d}_to_{END_YEAR}-{END_MONTH:02d}.xlsx"
    
    try:
        final_df.to_excel(output_filename, index=False, sheet_name='Month_End_Premia')
        print(f"\n" + "="*80)
        print(f"✅ SUCCESS! Analysis completed.")
        print(f"   Report saved as: '{output_filename}'")
        print(f"   Total months analyzed: {len(analysis_results)}")
        print("="*80)
        
        # Display summary
        print("\n📊 SUMMARY:")
        print(final_df.to_string(index=False))
        
    except Exception as e:
        print(f"\n❌ ERROR saving Excel file: {e}")
        print("Displaying results instead:")
        print(final_df.to_string(index=False))
        
        # Save as CSV as fallback
        csv_filename = output_filename.replace('.xlsx', '.csv')
        final_df.to_csv(csv_filename, index=False)
        print(f"Results saved as CSV: {csv_filename}")

if __name__ == "__main__":
    main()
