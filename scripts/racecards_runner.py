import sys
import os
import re
from datetime import datetime
from pathlib import Path

# Add the parent directory to sys.path so utils imports work
sys.path.append(str(Path(__file__).resolve().parent))

# Import the parse_races function from racecards.py
from racecards import parse_races, get_session
import orjson

def run_scraper(target_date):
    print(f"Starting scheduled scrape for {target_date}...")
    
    session = get_session()
    
    # We construct the URL to scrape all regions for the given date
    # In the original racecards.py, this was done via menu options
    # The direct URL format is: https://www.racingpost.com/racecards/YYYY-MM-DD
    url = f"https://www.racingpost.com/racecards/{target_date}"
    
    print(f"Fetching main racecards page: {url}")
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            print(f"Failed to fetch cards {url}")
            sys.exit(1)
            
        from lxml import html
        doc = html.fromstring(r.content)
        
        # Extract all specific race URLs from the daily page
        hrefs = doc.xpath('//a/@href')
        race_urls = sorted(list(set(
            ['https://www.racingpost.com' + h for h in hrefs 
             if '/racecards/' in h and target_date in h and re.search(r'/\d+$', h)]
        )))
        
        if not race_urls:
             print("No active race links found for this date.")
             sys.exit(1)
             
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error checking schedule: {e}")
        sys.exit(1)
        
    print(f"Found {len(race_urls)} races to scrape. Beginning thread pool...")
    
    races_data = parse_races(session, race_urls, target_date)
    
    if not races_data:
        print("Scrape completed but no full race data was gathered.")
        sys.exit(1)
        
    # Save to the merged format exactly as racecards.py expects
    base_dir = Path(__file__).resolve().parent.parent
    day_file = base_dir / 'racecards' / f'{target_date}_all.json'
    day_file.parent.mkdir(exist_ok=True)
    
    with open(day_file, 'wb') as f:
        f.write(orjson.dumps(races_data, option=orjson.OPT_NON_STR_KEYS))
        
    print(f"Saved {len(race_urls)} races to {day_file}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        # Default to tomorrow if no arg
        from datetime import timedelta
        target_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
    run_scraper(target_date)
