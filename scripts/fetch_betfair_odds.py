#!/usr/bin/env python3
"""
Betfair UK Horse Racing Odds Fetcher
======================================
Uses betfairlightweight library to fetch live odds from Betfair exchange.

Requirements:
1. Betfair account (free to create)
2. App Key from Betfair Developer Portal
3. Account credentials (username/password)

Usage:
    python fetch_betfair_odds.py --username YOUR_USERNAME --password YOUR_PASSWORD --app_key YOUR_APP_KEY

Or set environment variables:
    BETFAIR_USERNAME, BETFAIR_PASSWORD, BETFAIR_APP_KEY
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded credentials from {env_path}")
except ImportError:
    pass  # python-dotenv not installed, will use CLI args or env vars

try:
    import betfairlightweight
except ImportError:
    print("ERROR: betfairlightweight not installed. Run: python -m pip install betfairlightweight")
    sys.exit(1)


# Output directory
SCRIPT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = SCRIPT_DIR / "live_odds"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_credentials():
    """Get Betfair credentials from environment or command line."""
    parser = argparse.ArgumentParser(description='Fetch UK Horse Racing Odds from Betfair')
    parser.add_argument('--username', type=str, default=os.environ.get('BETFAIR_USERNAME', ''),
                        help='Betfair username')
    parser.add_argument('--password', type=str, default=os.environ.get('BETFAIR_PASSWORD', ''),
                        help='Betfair password')
    parser.add_argument('--app_key', type=str, default=os.environ.get('BETFAIR_APP_KEY', ''),
                        help='Betfair app key')
    parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                        help='Date to fetch odds for (YYYY-MM-DD)')
    args = parser.parse_args()
    
    if not all([args.username, args.password, args.app_key]):
        print("\n" + "="*70)
        print("  BETFAIR CREDENTIALS REQUIRED")
        print("="*70)
        print("""
To use this script, you need Betfair account credentials:

1. CREATE A BETFAIR ACCOUNT (if you don't have one):
   https://register.betfair.com/

2. GET AN APP KEY (free):
   - Login to Betfair
   - Go to: https://developer.betfair.com/account/apps
   - Create a new application
   - Copy your App Key

3. RUN THIS SCRIPT WITH CREDENTIALS:
   python fetch_betfair_odds.py --username YOUR_EMAIL --password YOUR_PASSWORD --app_key YOUR_APP_KEY

   Or set environment variables:
   set BETFAIR_USERNAME=your_email
   set BETFAIR_PASSWORD=your_password
   set BETFAIR_APP_KEY=your_app_key
""")
        print("="*70)
        sys.exit(1)
    
    return args


def normalize_horse_name(name):
    """Normalize horse name for matching."""
    import re
    if not name:
        return ''
    name = name.lower().strip()
    name = re.sub(r'\s*\([a-z]+\)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def fetch_horse_racing_odds(trading, target_date):
    """Fetch horse racing WIN + PLACE + EACH_WAY odds for UK/IRE races on the target date."""
    print(f"\n[1] Fetching horse racing markets for {target_date}...")

    # Parse date
    date_obj = datetime.strptime(target_date, '%Y-%m-%d')
    start_time = date_obj.replace(hour=0, minute=0, second=0)
    end_time = date_obj.replace(hour=23, minute=59, second=59)

    time_filter = {
        'from': start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'to': end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    }

    # ── Fetch WIN markets ──
    win_filter = {
        'eventTypeIds': ['7'],
        'marketCountries': ['GB', 'IE'],
        'marketStartTime': time_filter,
        'marketTypeCodes': ['WIN']
    }

    try:
        win_markets = trading.betting.list_market_catalogue(
            filter=win_filter,
            market_projection=['RUNNER_DESCRIPTION', 'EVENT', 'COMPETITION', 'MARKET_START_TIME'],
            max_results=100
        )
    except Exception as e:
        print(f"   Error fetching WIN markets: {e}")
        win_markets = []

    print(f"   Found {len(win_markets)} WIN markets")

    # ── Fetch PLACE markets ──
    place_filter = {
        'eventTypeIds': ['7'],
        'marketCountries': ['GB', 'IE'],
        'marketStartTime': time_filter,
        'marketTypeCodes': ['PLACE']
    }

    try:
        place_markets = trading.betting.list_market_catalogue(
            filter=place_filter,
            market_projection=['RUNNER_DESCRIPTION', 'EVENT', 'COMPETITION', 'MARKET_START_TIME',
                               'MARKET_DESCRIPTION'],
            max_results=100
        )
    except Exception as e:
        print(f"   Error fetching PLACE markets: {e}")
        place_markets = []

    print(f"   Found {len(place_markets)} PLACE markets")

    # ── Fetch EACH_WAY markets ──
    ew_filter = {
        'eventTypeIds': ['7'],
        'marketCountries': ['GB', 'IE'],
        'marketStartTime': time_filter,
        'marketTypeCodes': ['EACH_WAY']
    }

    try:
        ew_markets = trading.betting.list_market_catalogue(
            filter=ew_filter,
            market_projection=['RUNNER_DESCRIPTION', 'EVENT', 'COMPETITION', 'MARKET_START_TIME',
                               'MARKET_DESCRIPTION'],
            max_results=100
        )
    except Exception as e:
        print(f"   Error fetching EACH_WAY markets: {e}")
        ew_markets = []

    print(f"   Found {len(ew_markets)} EACH_WAY markets")

    if not win_markets and not place_markets and not ew_markets:
        return {}

    # ── Helper to fetch odds for a list of markets ──
    def fetch_books(market_list):
        books = {}
        ids = [m.market_id for m in market_list]
        for i in range(0, len(ids), 40):
            chunk = ids[i:i+40]
            try:
                mbs = trading.betting.list_market_book(
                    market_ids=chunk,
                    price_projection={'priceData': ['EX_BEST_OFFERS']}
                )
                for mb in mbs:
                    books[mb.market_id] = mb
            except Exception as e:
                print(f"   Error fetching odds chunk: {e}")
        return books

    # ── Get WIN odds ──
    print(f"\n[2] Fetching WIN odds for {len(win_markets)} markets...")
    win_books = fetch_books(win_markets)

    all_odds = {}

    for cat in win_markets:
        mb = win_books.get(cat.market_id)
        if not mb:
            continue

        event_name = cat.event.name if cat.event else ''
        market_start = cat.market_start_time.strftime('%H:%M') if cat.market_start_time else ''
        course = event_name.split()[0] if ' ' in event_name else event_name

        for runner in mb.runners:
            runner_info = next((r for r in cat.runners if r.selection_id == runner.selection_id), None)
            if not runner_info:
                continue

            horse_name = runner_info.runner_name
            norm_name = normalize_horse_name(horse_name)

            best_back = None
            if runner.ex and runner.ex.available_to_back:
                prices = sorted(runner.ex.available_to_back, key=lambda x: x.price, reverse=True)
                if prices:
                    best_back = prices[0].price

            if best_back and best_back > 1:
                all_odds[norm_name] = {
                    'name': horse_name,
                    'course': course,
                    'time': market_start,
                    'race': event_name,
                    'market_id': mb.market_id,
                    'selection_id': runner.selection_id,
                    'fractional': f"{best_back:.2f}",
                    'decimal': best_back,
                    'place_decimal': None,
                    'place_terms': None,
                    'place_market_id': None,
                    'ew_decimal': None,
                    'ew_divisor': None,
                    'ew_places': None,
                    'ew_market_id': None
                }

    # ── Get PLACE odds and merge ──
    if place_markets:
        print(f"\n[3] Fetching PLACE odds for {len(place_markets)} markets...")
        place_books = fetch_books(place_markets)
        place_count = 0

        for cat in place_markets:
            mb = place_books.get(cat.market_id)
            if not mb:
                continue

            # Extract number of places from market description
            num_places = None
            try:
                if hasattr(cat, 'description') and cat.description:
                    # e.g. "Each Way: 1/4 odds, 3 places"
                    desc = str(cat.description)
                    if hasattr(cat.description, 'each_way_divisor'):
                        pass
                    # Betfair place markets have numberOfPlaces in description
                    if hasattr(cat.description, 'number_of_places'):
                        num_places = cat.description.number_of_places
            except:
                pass

            # Fallback: estimate from number of runners
            if not num_places:
                num_runners = len(mb.runners)
                if num_runners <= 7:
                    num_places = 2
                elif num_runners <= 15:
                    num_places = 3
                else:
                    num_places = 4

            for runner in mb.runners:
                runner_info = next((r for r in cat.runners if r.selection_id == runner.selection_id), None)
                if not runner_info:
                    continue

                horse_name = runner_info.runner_name
                norm_name = normalize_horse_name(horse_name)

                best_back = None
                if runner.ex and runner.ex.available_to_back:
                    prices = sorted(runner.ex.available_to_back, key=lambda x: x.price, reverse=True)
                    if prices:
                        best_back = prices[0].price

                if best_back and best_back > 1:
                    if norm_name in all_odds:
                        all_odds[norm_name]['place_decimal'] = best_back
                        all_odds[norm_name]['place_terms'] = num_places
                        all_odds[norm_name]['place_market_id'] = mb.market_id
                        place_count += 1
                    else:
                        # Horse in place market but not win (rare)
                        event_name = cat.event.name if cat.event else ''
                        market_start = cat.market_start_time.strftime('%H:%M') if cat.market_start_time else ''
                        course = event_name.split()[0] if ' ' in event_name else event_name
                        all_odds[norm_name] = {
                            'name': horse_name,
                            'course': course,
                            'time': market_start,
                            'race': event_name,
                            'market_id': None,
                            'selection_id': runner.selection_id,
                            'fractional': None,
                            'decimal': None,
                            'place_decimal': best_back,
                            'place_terms': num_places,
                            'place_market_id': mb.market_id,
                            'ew_decimal': None,
                            'ew_divisor': None,
                            'ew_places': None,
                            'ew_market_id': None
                        }
                        place_count += 1

        print(f"   Matched place odds for {place_count} horses")

    # ── Get EACH_WAY odds and merge ──
    if ew_markets:
        print(f"\n[4] Fetching EACH_WAY odds for {len(ew_markets)} markets...")
        ew_books = fetch_books(ew_markets)
        ew_count = 0

        for cat in ew_markets:
            mb = ew_books.get(cat.market_id)
            if not mb:
                continue

            # Extract E/W terms from market description
            ew_divisor = None
            ew_places = None
            try:
                if hasattr(cat, 'description') and cat.description:
                    if hasattr(cat.description, 'each_way_divisor'):
                        ew_divisor = cat.description.each_way_divisor
                    if hasattr(cat.description, 'number_of_places'):
                        ew_places = cat.description.number_of_places
            except:
                pass

            event_name = cat.event.name if cat.event else ''
            market_start = cat.market_start_time.strftime('%H:%M') if cat.market_start_time else ''
            course = event_name.split()[0] if ' ' in event_name else event_name

            for runner in mb.runners:
                runner_info = next((r for r in cat.runners if r.selection_id == runner.selection_id), None)
                if not runner_info:
                    continue

                horse_name = runner_info.runner_name
                norm_name = normalize_horse_name(horse_name)

                best_back = None
                if runner.ex and runner.ex.available_to_back:
                    prices = sorted(runner.ex.available_to_back, key=lambda x: x.price, reverse=True)
                    if prices:
                        best_back = prices[0].price

                if best_back and best_back > 1:
                    if norm_name in all_odds:
                        all_odds[norm_name]['ew_decimal'] = best_back
                        all_odds[norm_name]['ew_divisor'] = ew_divisor
                        all_odds[norm_name]['ew_places'] = ew_places
                        all_odds[norm_name]['ew_market_id'] = mb.market_id
                        ew_count += 1
                    else:
                        all_odds[norm_name] = {
                            'name': horse_name,
                            'course': course,
                            'time': market_start,
                            'race': event_name,
                            'market_id': None,
                            'selection_id': runner.selection_id,
                            'fractional': None,
                            'decimal': None,
                            'place_decimal': None,
                            'place_terms': None,
                            'place_market_id': None,
                            'ew_decimal': best_back,
                            'ew_divisor': ew_divisor,
                            'ew_places': ew_places,
                            'ew_market_id': mb.market_id
                        }
                        ew_count += 1

        print(f"   Matched E/W odds for {ew_count} horses")

    return all_odds


def main():
    args = get_credentials()
    
    print("="*70)
    print("  BETFAIR UK HORSE RACING ODDS FETCHER")
    print("="*70)
    print(f"\n  Username: {args.username}")
    print(f"  Date: {args.date}")
    
    # Create trading client
    print("\n[0] Connecting to Betfair...")
    
    try:
        trading = betfairlightweight.APIClient(
            username=args.username,
            password=args.password,
            app_key=args.app_key
        )
        
        # Interactive login (no certs required)
        trading.login_interactive()
        print("   Connected successfully!")
        
    except Exception as e:
        print(f"   ERROR: Failed to connect to Betfair: {e}")
        print("\n   Possible issues:")
        print("   - Incorrect username/password/app_key")
        print("   - Betfair account not verified")
        print("   - App key not activated")
        sys.exit(1)
    
    try:
        # Fetch odds
        odds = fetch_horse_racing_odds(trading, args.date)
        
        # Save results
        if odds:
            output = {
                'date': args.date,
                'source': 'betfair',
                'fetched_at': datetime.now().isoformat(),
                'horse_count': len(odds),
                'odds_count': sum(1 for h in odds.values() if h['decimal'] > 0),
                'odds': odds
            }
            
            output_file = OUTPUT_DIR / f'odds_{args.date}_betfair.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print(f"\n[3] Results saved to: {output_file}")
            print(f"    Total horses: {len(odds)}")
            print(f"    With odds: {output['odds_count']}")
            
            # Show sample
            print("\n    Sample odds:")
            for i, (norm_name, data) in enumerate(list(odds.items())[:5]):
                print(f"      {data['name']:25} | {data['course']:15} | {data['time']:5} | {data['decimal']:.2f}")
        else:
            print("\n   No odds found for the specified date.")
    
    finally:
        # Logout
        try:
            trading.logout()
        except:
            pass
    
    print("\n" + "="*70)
    print("  DONE")
    print("="*70)


if __name__ == '__main__':
    main()
