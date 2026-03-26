#!/usr/bin/env python3
"""
Cloud Betfair Odds Fetcher (REST API)
=====================================
Uses Betfair's REST API directly instead of betfairlightweight,
which calls the 'interactive' login endpoint that gets blocked by cloud IPs.

This script uses the global SSO endpoint + Exchange API directly.
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

SCRIPT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = SCRIPT_DIR / "live_odds"
OUTPUT_DIR.mkdir(exist_ok=True)

BETFAIR_LOGIN_URL = "https://identitysso.betfair.com/api/login"
BETFAIR_API_URL = "https://api.betfair.com/exchange/betting/rest/v1.0"
BETFAIR_KEEP_ALIVE = "https://identitysso.betfair.com/api/keepAlive"
BETFAIR_LOGOUT = "https://identitysso.betfair.com/api/logout"


def normalize_horse_name(name):
    if not name:
        return ''
    name = name.lower().strip()
    name = re.sub(r'\s*\([a-z]+\)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name


def betfair_login(username, password, app_key):
    """Login to Betfair using the global (non-interactive) SSO endpoint."""
    print(f"[0] Logging into Betfair (global SSO)...")
    
    headers = {
        'X-Application': app_key,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
    }
    data = {
        'username': username,
        'password': password,
    }
    
    r = requests.post(BETFAIR_LOGIN_URL, headers=headers, data=data, timeout=15)
    
    if r.status_code != 200:
        print(f"   Login HTTP error: {r.status_code}")
        print(f"   Response: {r.text[:500]}")
        return None
    
    try:
        resp = r.json()
    except:
        # Maybe got HTML redirect - try with different accept header
        print(f"   Got non-JSON response, trying alternative...")
        headers['Accept'] = 'application/json'
        headers['User-Agent'] = 'Mozilla/5.0'
        r = requests.post(BETFAIR_LOGIN_URL, headers=headers, data=data, timeout=15)
        try:
            resp = r.json()
        except:
            print(f"   Still non-JSON response: {r.text[:200]}")
            return None
    
    token = resp.get('token')
    status = resp.get('loginStatus') or resp.get('status')
    
    if token and status == 'SUCCESS':
        print(f"   ✅ Connected! Session token: {token[:10]}...")
        return token
    else:
        print(f"   ❌ Login failed: {status}")
        print(f"   Error: {resp.get('error', 'Unknown')}")
        return None


def betfair_api(session_token, app_key, operation, params):
    """Call a Betfair Exchange API operation."""
    url = f"{BETFAIR_API_URL}/{operation}/"
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    
    r = requests.post(url, headers=headers, json=params, timeout=30)
    
    if r.status_code != 200:
        print(f"   API error ({operation}): {r.status_code} - {r.text[:200]}")
        return None
    
    return r.json()


def fetch_odds(session_token, app_key, target_date):
    """Fetch WIN, PLACE and E/W odds for UK/IRE horse racing."""
    date_str = target_date
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    start = date_obj.strftime('%Y-%m-%dT00:00:00Z')
    end = date_obj.strftime('%Y-%m-%dT23:59:59Z')
    
    # --- Fetch WIN market catalogue ---
    print(f"\n[1] Fetching WIN markets for {date_str}...")
    win_filter = {
        'filter': {
            'eventTypeIds': ['7'],
            'marketCountries': ['GB', 'IE'],
            'marketStartTime': {'from': start, 'to': end},
            'marketTypeCodes': ['WIN'],
        },
        'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT', 'MARKET_START_TIME'],
        'maxResults': '100',
    }
    
    win_cats = betfair_api(session_token, app_key, 'listMarketCatalogue', win_filter) or []
    print(f"   Found {len(win_cats)} WIN markets")
    
    if not win_cats:
        return {}
    
    # --- Fetch WIN odds ---
    print(f"\n[2] Fetching WIN odds...")
    market_ids = [m['marketId'] for m in win_cats]
    all_odds = {}
    
    for i in range(0, len(market_ids), 40):
        chunk = market_ids[i:i+40]
        book_params = {
            'marketIds': chunk,
            'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
        }
        books = betfair_api(session_token, app_key, 'listMarketBook', book_params) or []
        
        books_by_id = {b['marketId']: b for b in books}
        
        for cat in win_cats:
            if cat['marketId'] not in books_by_id:
                continue
            book = books_by_id[cat['marketId']]
            
            event_name = cat.get('event', {}).get('name', '')
            market_start = cat.get('marketStartTime', '')
            if market_start:
                try:
                    dt = datetime.fromisoformat(market_start.replace('Z', '+00:00'))
                    market_time = dt.strftime('%H:%M')
                except:
                    market_time = ''
            else:
                market_time = ''
            
            course = event_name.split()[0] if ' ' in event_name else event_name
            
            runners_map = {r['selectionId']: r for r in cat.get('runners', [])}
            
            for runner in book.get('runners', []):
                sel_id = runner['selectionId']
                runner_info = runners_map.get(sel_id)
                if not runner_info:
                    continue
                
                horse_name = runner_info.get('runnerName', '')
                norm_name = normalize_horse_name(horse_name)
                
                best_back = None
                ex = runner.get('ex', {})
                backs = ex.get('availableToBack', [])
                if backs:
                    backs_sorted = sorted(backs, key=lambda x: x['price'], reverse=True)
                    best_back = backs_sorted[0]['price']
                
                if best_back and best_back > 1:
                    all_odds[norm_name] = {
                        'name': horse_name,
                        'course': course,
                        'time': market_time,
                        'race': event_name,
                        'market_id': cat['marketId'],
                        'selection_id': sel_id,
                        'fractional': f"{best_back:.2f}",
                        'decimal': best_back,
                        'place_decimal': None,
                        'place_terms': None,
                        'place_market_id': None,
                        'ew_decimal': None,
                        'ew_divisor': None,
                        'ew_places': None,
                        'ew_market_id': None,
                    }
    
    # --- Fetch PLACE markets and merge ---
    print(f"\n[3] Fetching PLACE markets...")
    place_filter = {
        'filter': {
            'eventTypeIds': ['7'],
            'marketCountries': ['GB', 'IE'],
            'marketStartTime': {'from': start, 'to': end},
            'marketTypeCodes': ['PLACE'],
        },
        'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT', 'MARKET_START_TIME', 'MARKET_DESCRIPTION'],
        'maxResults': '100',
    }
    place_cats = betfair_api(session_token, app_key, 'listMarketCatalogue', place_filter) or []
    print(f"   Found {len(place_cats)} PLACE markets")
    
    if place_cats:
        place_ids = [m['marketId'] for m in place_cats]
        place_count = 0
        for i in range(0, len(place_ids), 40):
            chunk = place_ids[i:i+40]
            book_params = {
                'marketIds': chunk,
                'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
            }
            books = betfair_api(session_token, app_key, 'listMarketBook', book_params) or []
            books_by_id = {b['marketId']: b for b in books}
            
            for cat in place_cats:
                if cat['marketId'] not in books_by_id:
                    continue
                book = books_by_id[cat['marketId']]
                
                num_places = None
                desc = cat.get('description', {})
                if isinstance(desc, dict):
                    num_places = desc.get('numberOfPlaces')
                
                if not num_places:
                    num_runners = len(book.get('runners', []))
                    num_places = 2 if num_runners <= 7 else 3 if num_runners <= 15 else 4
                
                runners_map = {r['selectionId']: r for r in cat.get('runners', [])}
                for runner in book.get('runners', []):
                    sel_id = runner['selectionId']
                    runner_info = runners_map.get(sel_id)
                    if not runner_info:
                        continue
                    horse_name = runner_info.get('runnerName', '')
                    norm_name = normalize_horse_name(horse_name)
                    
                    ex = runner.get('ex', {})
                    backs = ex.get('availableToBack', [])
                    if backs:
                        best = sorted(backs, key=lambda x: x['price'], reverse=True)[0]['price']
                        if best > 1 and norm_name in all_odds:
                            all_odds[norm_name]['place_decimal'] = best
                            all_odds[norm_name]['place_terms'] = num_places
                            place_count += 1
        print(f"   Matched place odds for {place_count} horses")
    
    return all_odds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', default=os.environ.get('BETFAIR_USERNAME', ''))
    parser.add_argument('--password', default=os.environ.get('BETFAIR_PASSWORD', ''))
    parser.add_argument('--app_key', default=os.environ.get('BETFAIR_APP_KEY', ''))
    parser.add_argument('--date', default=(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
    args = parser.parse_args()
    
    if not all([args.username, args.password, args.app_key]):
        print("ERROR: Betfair credentials required (env vars or --username/--password/--app_key)")
        sys.exit(1)
    
    print("=" * 60)
    print("  BETFAIR ODDS FETCHER (Cloud-Compatible REST API)")
    print("=" * 60)
    print(f"  Date: {args.date}")
    
    token = betfair_login(args.username, args.password, args.app_key)
    if not token:
        sys.exit(1)
    
    try:
        odds = fetch_odds(token, args.app_key, args.date)
        
        if odds:
            output = {
                'date': args.date,
                'source': 'betfair',
                'fetched_at': datetime.now().isoformat(),
                'horse_count': len(odds),
                'odds_count': sum(1 for h in odds.values() if h.get('decimal', 0) > 0),
                'odds': odds,
            }
            
            out_file = OUTPUT_DIR / f'odds_{args.date}_betfair.json'
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Saved {len(odds)} horses to: {out_file}")
            for i, (_, d) in enumerate(list(odds.items())[:5]):
                print(f"   {d['name']:25} | {d['course']:15} | {d['time']:5} | {d['decimal']:.2f}")
        else:
            print("\n⚠️ No odds found")
    
    finally:
        try:
            requests.post(BETFAIR_LOGOUT, headers={
                'X-Application': args.app_key,
                'X-Authentication': token,
                'Accept': 'application/json',
            }, timeout=5)
        except:
            pass
    
    print(f"\n{'='*60}")
    print("  DONE")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
