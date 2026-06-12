# NSE Bhavcopy URL Generator
# This script generates direct download URLs for NSE bhavcopy data

from datetime import date, timedelta
import calendar
from dateutil.relativedelta import relativedelta

def generate_bhavcopy_urls(start_year, start_month, end_year, end_month):
    """Generate all possible URLs for bhavcopy data."""
    
    current_date = date(start_year, start_month, 1)
    end_date = date(end_year, end_month, 1)
    
    urls = []
    
    while current_date < end_date:
        year, month = current_date.year, current_date.month
        
        # Get last trading day of the month
        last_day_of_month = calendar.monthrange(year, month)[1]
        
        for day in range(last_day_of_month, 0, -1):
            check_date = date(year, month, day)
            
            # Skip weekends
            if check_date.weekday() >= 5:
                continue
            
            date_str = check_date.strftime('%d%b%Y').upper()
            month_str = check_date.strftime('%b').upper()
            
            # Generate URLs for this date
            base_urls = [
                'https://archives.nseindia.com/content/historical/DERIVATIVES',
                'https://nsearchives.nseindia.com/content/historical/DERIVATIVES', 
                'https://www1.nseindia.com/content/historical/DERIVATIVES',
                'https://www.nseindia.com/content/historical/DERIVATIVES'
            ]
            
            file_patterns = [
                f"fo{date_str}bhav.csv.zip",
                f"fo{date_str}bhav.csv"
            ]
            
            month_urls = []
            for base_url in base_urls:
                for file_pattern in file_patterns:
                    url = f"{base_url}/{year}/{month_str}/{file_pattern}"
                    month_urls.append(url)
            
            urls.append({
                'date': check_date,
                'month': f"{calendar.month_name[month]} {year}",
                'urls': month_urls
            })
            
            # Only get the last trading day
            break
        
        current_date += relativedelta(months=1)
    
    return urls

# Generate URLs for July 2024 to July 2025
urls_data = generate_bhavcopy_urls(2024, 7, 2025, 7)

print("="*80)
print("NSE BHAVCOPY DIRECT DOWNLOAD URLS")
print("July 2024 to July 2025")
print("="*80)

for entry in urls_data:
    print(f"\n📅 {entry['month']} - Last Trading Day: {entry['date']}")
    print("   Direct Download URLs:")
    
    for i, url in enumerate(entry['urls'], 1):
        print(f"   {i:2d}. {url}")
    
    print("   " + "-"*70)

print("\n" + "="*80)
print("USAGE INSTRUCTIONS:")
print("1. Try each URL in order until one works")
print("2. Save the downloaded file as 'manual_data.csv'")
print("3. Place it in the same directory as your analysis script")
print("4. Run the analysis script and choose option 2 when prompted")
print("="*80)

# Also create a test script to check which URLs work
print("\n" + "="*80)
print("TESTING URLS (This will take a few minutes)...")
print("="*80)

import requests
import time

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

working_urls = []

for entry in urls_data:
    print(f"\n🔍 Testing URLs for {entry['month']}...")
    
    for url in entry['urls']:
        try:
            response = session.head(url, timeout=30)  # Use HEAD to avoid downloading
            if response.status_code == 200:
                print(f"   ✅ WORKING: {url}")
                working_urls.append({
                    'date': entry['date'],
                    'month': entry['month'],
                    'url': url
                })
                break  # Found working URL for this month
            else:
                print(f"   ❌ Status {response.status_code}: {url}")
        except Exception as e:
            print(f"   ❌ Error: {url} - {str(e)[:30]}...")
        
        time.sleep(0.5)  # Small delay between requests

print(f"\n" + "="*80)
print("SUMMARY - WORKING URLS:")
print("="*80)

if working_urls:
    for entry in working_urls:
        print(f"📅 {entry['month']}: {entry['url']}")
else:
    print("❌ No working URLs found. You may need to use manual download.")

print("="*80)
