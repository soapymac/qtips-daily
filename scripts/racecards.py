#!/usr/bin/env python3
import os
import sys
import time
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
import re
from re import search

# CHANGE: Use curl_cffi instead of standard requests to bypass Cloudflare
from curl_cffi import requests
from lxml import etree, html
from orjson import loads, dumps, OPT_NON_STR_KEYS

# Ensure the 'utils' folder is in the same directory as this script
try:
    from utils.cleaning import normalize_name
    from utils.going import get_surface
    from utils.header import RandomHeader
    from utils.lxml_funcs import find
    from utils.region import get_region
    from utils.stats import Stats
except ImportError as e:
    print(f"Error importing utils: {e}")
    print("Ensure you are running this script from the correct directory containing the 'utils' folder.")
    sys.exit(1)

# Initialize Random Header (Still useful for Referer, though curl_cffi handles User-Agent)
random_header = RandomHeader()

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent
RACECARDS_DIR = BASE_DIR / 'racecards'
MERGED_DIR = BASE_DIR / 'json_racecards_merged'
MASTER_FILE = MERGED_DIR / 'all_racecards_merged.json'

def get_session():
    """Creates a session that impersonates a real Chrome browser with enhanced anti-bot measures."""
    # Use chrome110 for better TLS fingerprint compatibility
    s = requests.Session(impersonate="chrome110")
    
    # Add realistic headers
    s.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Referer': 'https://www.google.com/',
    })
    
    # Pre-warm the session by visiting homepage first
    try:
        s.get('https://www.racingpost.com/', timeout=10)
        time.sleep(1)  # Small delay like a real user
    except:
        pass
    
    return s

def distance_to_furlongs(distance):
    """Converts distance strings (e.g., '2m 1½f') to float furlongs."""
    if not distance:
        return 0.0
    
    clean_dist = distance.strip().replace('¼', '.25').replace('½', '.5').replace('¾', '.75')
    
    total_furlongs = 0.0
    
    if 'm' in clean_dist:
        parts = clean_dist.split('m')
        miles = int(parts[0])
        furlongs_part = parts[1].strip().rstrip('f')
        
        if furlongs_part:
            total_furlongs = (miles * 8) + float(furlongs_part)
        else:
            total_furlongs = miles * 8
    else:
        furlongs_part = clean_dist.rstrip('f')
        if furlongs_part:
            total_furlongs = float(furlongs_part)

    return total_furlongs

def get_accordion(session, url):
    """Fetches the accordion data (stats) for a race."""
    race_id = url.split('/')[-1]
    accordion_url = f'https://www.racingpost.com/racecards/data/accordion/{race_id}'
    
    try:
        r = session.get(accordion_url, timeout=10)
        return html.fromstring(r.content)
    except Exception:
        return html.fromstring("<html></html>")

def get_going_info(session, date):
    """Fetches detailed going and weather from the non-runners page."""
    url = f'https://www.racingpost.com/non-runners/{date}'
    
    try:
        r = session.get(url, timeout=10)
    except Exception:
        return defaultdict(dict)

    going_info = defaultdict(dict)
    if r.status_code != 200:
        return going_info

    try:
        doc = html.fromstring(r.content)
        scripts = doc.xpath('//script[contains(text(), "PRELOADED_STATE")]')
        if not scripts:
            return going_info

        script_content = scripts[0].text
        json_str = ''
        
        if 'var __PRELOADED_STATE__ =' in script_content:
            json_str = script_content.split('var __PRELOADED_STATE__ =')[1]
        elif 'window.PRELOADED_STATE =' in script_content:
            json_str = script_content.split('window.PRELOADED_STATE =')[1]
        
        if not json_str:
            return going_info

        data = loads(json_str.strip().strip(';'))
        
        courses_data = data if isinstance(data, list) else []

        for course in courses_data:
            course_name = course.get('courseName', '')
            
            # Map Course IDs
            course_id = 0
            if course_name == 'Belmont At The Big A':
                course_id = 255
                course_name = 'Aqueduct'
            else:
                url_part = course.get('raceCardsCourseMeetingsUrl', '')
                if url_part:
                    try:
                        course_id = int(url_part.split('/')[2])
                    except (IndexError, ValueError):
                        pass

            if course_id:
                going_str = course.get('going', '')
                going, rail_movements = parse_going(going_str)
                
                going_info[course_id] = {
                    'course': course_name,
                    'going': going,
                    'stalls': course.get('stallsPosition', ''),
                    'rail_movements': rail_movements,
                    'weather': course.get('weather', '')
                }

    except Exception as e:
        print(f"Warning: Error parsing going info: {e}")

    return going_info

def parse_going(going_info):
    going = going_info
    rail_movements = ''
    if 'Rail movements' in going_info:
        going_info = going_info.replace('movements:', 'movements')
        parts = going_info.split('Rail movements')
        going = parts[0].strip().rstrip('(')
        try:
            rail_movements = [x.strip() for x in parts[1].strip().strip(')').split(',')]
        except IndexError:
            pass
    return going, rail_movements

def get_pattern(race_name):
    regex_group = r'(\(|\s)((G|g)rade|(G|g)roup) (\d|[A-Ca-c]|I*)(\)|\s)'
    match = search(regex_group, race_name)
    if match:
        return f'{match.groups()[1]} {match.groups()[4]}'.title().title()
    
    if any(x in race_name.lower() for x in {'listed race', '(listed'}):
        return 'Listed'
    return ''

def get_race_type(doc, race_name, distance):
    fences = find(doc, 'div', 'RC-headerBox__stalls').lower()
    
    if 'hurdle' in fences:
        return 'Hurdle'
    elif 'fence' in fences:
        return 'Chase'
    
    # Logic based on race name and distance
    race_lower = race_name.lower()
    if distance >= 12:
        if any(x in race_lower for x in {'national hunt flat', 'nh flat', 'bumper'}):
            return 'NH Flat'
        if 'hurdle' in race_lower:
            return 'Hurdle'
        if any(x in race_lower for x in {'chase', 'steeplechase'}):
            return 'Chase'
            
    return 'Flat'

def process_single_race(session, url, date, going_info):
    """Worker function to process a single race URL."""
    try:
        # Polite delay
        time.sleep(random.uniform(0.5, 1.5))
        
        # Allow redirects - Racing Post often redirects race URLs
        r = session.get(url, allow_redirects=True, timeout=15)
        
        # Check for Cloudflare block
        if 'Just a moment' in r.text[:500] or 'Checking your browser' in r.text[:500]:
            print(f"Cloudflare block on {url}")
            return None
        
        if r.status_code != 200:
            print(f"Failed to fetch {url} (Status: {r.status_code})")
            return None

        doc = html.fromstring(r.content)
        accordion = get_accordion(session, url)
        stats = Stats(accordion)

        race = {}
        url_split = url.split('/')

        # --- Course Info ---
        race['course'] = find(doc, 'h1', 'RC-courseHeader__name')
        if not race['course']:
             # Fallback for some layouts
             race['course'] = find(doc, 'a', 'RC-courseHeader__name')

        if race['course'] == 'Belmont At The Big A':
            race['course_id'] = 255
            race['course'] = 'Aqueduct'
        else:
            try:
                race['course_id'] = int(url_split[4])
            except (IndexError, ValueError):
                race['course_id'] = 0

        # --- Race ID & Date ---
        try:
            race['race_id'] = int(url_split[7])
            race['date'] = url_split[6]
        except IndexError:
            race['race_id'] = 0
            race['date'] = date

        # --- Race Details ---
        race['off_time'] = find(doc, 'span', 'RC-courseHeader__time')
        race['race_name'] = find(doc, 'span', 'RC-header__raceInstanceTitle')
        race['distance_round'] = find(doc, 'strong', 'RC-header__raceDistanceRound')
        
        raw_dist = find(doc, 'span', 'RC-header__raceDistance')
        race['distance'] = race['distance_round'] if not raw_dist else raw_dist.strip('()')
        race['distance_f'] = distance_to_furlongs(race['distance_round'])

        race['region'] = get_region(str(race['course_id']))
        race['pattern'] = get_pattern(race['race_name'])
        
        race_class = find(doc, 'span', 'RC-header__raceClass')
        race['race_class'] = race_class.strip('()') if race_class else ('Class 1' if race['pattern'] else '')
        
        race['type'] = get_race_type(doc, race['race_name'], race['distance_f'])

        # --- Bands/Prize/Field ---
        try:
            band = find(doc, 'span', 'RC-header__rpAges').strip('()').split()
            race['age_band'] = band[0] if band else None
            race['rating_band'] = band[1] if len(band) > 1 else None
        except AttributeError:
            race['age_band'] = None
            race['rating_band'] = None

        prize_text = find(doc, 'div', 'RC-headerBox__winner').lower()
        race['prize'] = prize_text.split('winner:')[1].strip() if 'winner:' in prize_text else None
        
        field_text = find(doc, 'div', 'RC-headerBox__runners').lower()
        try:
            race['field_size'] = int(field_text.split('runners:')[1].split('(')[0].strip()) if field_text else 0
        except (ValueError, IndexError):
            race['field_size'] = 0

        # --- Going & Weather Merge ---
        c_info = going_info.get(race['course_id'], {})
        race['going_detailed'] = c_info.get('going')
        race['rail_movements'] = c_info.get('rail_movements')
        race['stalls'] = c_info.get('stalls')
        race['weather'] = c_info.get('weather')

        going_on_page = find(doc, 'div', 'RC-headerBox__going').lower()
        if 'going:' in going_on_page:
            race['going'] = going_on_page.split('going:')[1].strip().title()
        else:
            race['going'] = race['going_detailed'] if race['going_detailed'] else ''

        if not race['stalls']:
            stalls_page = find(doc, 'div', 'RC-headerBox__stalls')
            if 'stalls:' in stalls_page.lower():
                race['stalls'] = stalls_page.split('Stalls:')[1].strip()

        race['surface'] = get_surface(race['going'])

        # --- Runners ---
        profile_hrefs = doc.xpath("//a[@data-test-selector='RC-cardPage-runnerName']/@href")
        profile_urls = ['https://www.racingpost.com' + a.split('#')[0] + '/form' for a in profile_hrefs]

        runners = get_runners(session, profile_urls)

        # Parse Runners from HTML
        runner_list = []
        for horse in doc.xpath("//div[contains(@class, ' js-PC-runnerRow')]"):
            try:
                horse_link = find(horse, 'a', 'RC-cardPage-runnerName', attrib='href')
                horse_id = int(horse_link.split('/')[3])
            except (IndexError, ValueError, AttributeError):
                continue
            
            r_data = runners.get(horse_id, {'horse_id': horse_id})
            
            if 'broken_url' in r_data:
                try:
                    sire = find(horse, 'a', 'RC-pedigree__sire').split('(')
                    r_data['sire'] = normalize_name(sire[0])
                except Exception: pass

            # Debug accordion fetch
            print(f"DEBUG: Internal Stats Object - Trainers count: {len(stats.trainers)}")
            print(f"DEBUG: Trainer Keys: {list(stats.trainers.keys())}")
            
            r_data['number'] = _safe_int(find(horse, 'span', 'RC-cardPage-runnerNumber-no', attrib='data-order-no'))
            r_data['draw'] = _safe_int(find(horse, 'span', 'RC-cardPage-runnerNumber-draw', attrib='data-order-draw'))
            r_data['headgear'] = find(horse, 'span', 'RC-cardPage-runnerHeadGear')
            r_data['lbs'] = _safe_int(find(horse, 'span', 'RC-cardPage-runnerWgt-carried', attrib='data-order-wgt'))
            r_data['ofr'] = _safe_int(find(horse, 'span', 'RC-cardPage-runnerOr', attrib='data-order-or'))
            r_data['rpr'] = _safe_int(find(horse, 'span', 'RC-cardPage-runnerRpr', attrib='data-order-rpr'))
            r_data['ts'] = _safe_int(find(horse, 'span', 'RC-cardPage-runnerTs', attrib='data-order-ts'))
            
            # Jockey
            claim = find(horse, 'span', 'RC-cardPage-runnerJockey-allowance')
            jockey_elem = horse.find('.//a[@data-test-selector="RC-cardPage-runnerJockey-name"]')
            if jockey_elem is not None:
                jname = normalize_name(jockey_elem.attrib.get('data-order-jockey', ''))
                r_data['jockey'] = jname + (f'({claim})' if claim else '')
                r_data['jockey_id'] = int(jockey_elem.attrib['href'].split('/')[3]) if 'href' in jockey_elem.attrib else None
            else:
                r_data['jockey'] = None

            r_data['last_run'] = find(horse, 'div', 'RC-cardPage-runnerStats-lastRun')
            r_data['form'] = find(horse, 'span', 'RC-cardPage-runnerForm')
            r_data['trainer_rtf'] = find(horse, 'span', 'RC-cardPage-runnerTrainer-rtf')

            # --- Stats Integration ---
            r_data['stats'] = {}
            if r_data['jockey'] and r_data['jockey'].lower() != 'non-runner':
                try:
                    # Parse trainer_id from HTML if not in r_data
                    if not r_data.get('trainer_id'):
                        trainer_elem = horse.find('.//a[@data-test-selector="RC-cardPage-runnerTrainer-name"]')
                        if trainer_elem is not None:
                            try:
                                r_data['trainer_id'] = int(trainer_elem.attrib['href'].split('/')[3])
                                print(f"DEBUG: Found trainer ID from fallback: {r_data['trainer_id']}")
                            except Exception as e: 
                                print(f"DEBUG: Trainer ID parse error: {e}")
                        else:
                            print("DEBUG: Trainer elem NOT FOUND using selector mechanism")
                            links = horse.xpath('.//a')
                            print(f"DEBUG: Available links in runner row: {[l.get('data-test-selector') for l in links]}")

                    # Use IDs for lookup where possible (matching utils/stats.py logic)
                    horse_id_key = str(r_data.get('horse_id', ''))
                    
                    # For jockey, we rely on name if ID lookup fails or logic in stats.py uses name?
                    # stats.py uses href ID: jockey_trainer_id = href.split('/')[3]
                    # So we MUST use ID for jockeys and trainers too.
                    
                    jockey_id_key = str(r_data.get('jockey_id', ''))
                    trainer_id_key = str(r_data.get('trainer_id', ''))

                    # Fallback to name-based lookup if ID key misses? 
                    # No, stats.py clearly keys by ID. If ID is missing, we can't look it up properly.
                    
                    runner_stats_obj = stats.horses.get(horse_id_key)
                    if hasattr(runner_stats_obj, 'to_dict'):
                        runner_stats = runner_stats_obj.to_dict()
                    else:
                        runner_stats = {'course':{}, 'distance':{}, 'going':{}}
                    
                    r_data['stats'] = {
                        'course': runner_stats.get('course', {}),
                        'distance': runner_stats.get('distance', {}),
                        'going': runner_stats.get('going', {}),
                        'jockey': stats.jockeys.get(jockey_id_key, {}),
                        'trainer': stats.trainers.get(trainer_id_key, {}),
                    }
                except Exception as e: 
                    # print(f"Stats lookup error: {e}") 
                    pass
            
            runner_list.append(r_data)

        race['runners'] = runner_list
        return race

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

def _safe_int(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

# ==================== PAST DATE (RESULTS PAGE) FUNCTIONS ====================

def get_past_courses(session, date):
    """Parse the results listing page for a past date to get courses and race URLs."""
    results_url = f'https://www.racingpost.com/results/{date}'
    print(f"Fetching results listing from {results_url}...")
    
    try:
        r = session.get(results_url, timeout=15)
        if r.status_code != 200:
            print(f"Failed to fetch results listing (Status: {r.status_code})")
            return {}
    except Exception as e:
        print(f"Error fetching results listing: {e}")
        return {}
    
    doc = html.fromstring(r.content)
    title = doc.find('.//title')
    if title is not None:
        print(f"Page Title: {title.text_content()}")
    
    # Extract all result race links: /results/{course_id}/{course_name}/{date}/{race_id}
    all_hrefs = doc.xpath('//a/@href')
    result_links = sorted(set(
        h for h in all_hrefs 
        if '/results/' in h and re.search(r'/\d+$', h) and date in h
    ))
    
    if not result_links:
        print("No race result links found.")
        return {}
    
    # Group by course
    courses = {}
    for link in result_links:
        # /results/12/chepstow/2026-02-13/911474
        parts = link.strip('/').split('/')
        # parts: ['results', '12', 'chepstow', '2026-02-13', '911474']
        if len(parts) >= 5:
            course_name = parts[2].replace('-', ' ').title()
            # Clean up (AW), (IRE) etc
            course_name = course_name.replace(' Aw', ' (AW)').replace(' Ire', ' (IRE)').replace(' Fr', ' (FR)').replace(' Uae', ' (UAE)')
            full_url = 'https://www.racingpost.com' + link if not link.startswith('http') else link
            
            if valid_course(course_name.lower()):
                if course_name not in courses:
                    courses[course_name] = []
                courses[course_name].append(full_url)
    
    return courses


def process_single_result(session, url, date, going_info):
    """Parse a single result page into the same format as process_single_race."""
    try:
        time.sleep(random.uniform(0.5, 1.5))
        r = session.get(url, allow_redirects=True, timeout=15)
        
        if 'Just a moment' in r.text[:500]:
            print(f"Cloudflare block on {url}")
            return None
        if r.status_code != 200:
            print(f"Failed to fetch {url} (Status: {r.status_code})")
            return None
        
        doc = html.fromstring(r.content)
        race = {}
        url_split = url.split('/')
        
        # --- Course Info ---
        course_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName__name")]')
        race['course'] = course_el[0].text_content().strip() if course_el else ''
        
        try:
            race['course_id'] = int(url_split[4])
        except (IndexError, ValueError):
            race['course_id'] = 0
        
        # --- Race ID & Date ---
        try:
            race['race_id'] = int(url_split[7])
            race['date'] = url_split[6]
        except (IndexError, ValueError):
            race['race_id'] = 0
            race['date'] = date
        
        # --- Race Details ---
        time_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName__time")]')
        race['off_time'] = time_el[0].text_content().strip() if time_el else ''
        
        title_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName__title")]')
        race['race_name'] = title_el[0].text_content().strip() if title_el else ''
        
        # Distance - results page has two elements:
        #   _distanceFull: "(2m3f98yds)" (precise, in parens) - is a CHILD of _distance
        #   _distance: direct text has short format like "2m3½f"
        # We use .text (direct text only) to avoid including the child _distanceFull text
        dist_full_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName_distanceFull")]')
        dist_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName_distance") and not(contains(@class, "Full"))]')
        if dist_el:
            # Use .text to get only direct text (not child text)
            raw_text = dist_el[0].text or ''
            # Also try tail text of child elements
            if not raw_text.strip():
                # Fallback: get all text but strip parens
                raw_text = dist_el[0].text_content()
            dist_clean = re.sub(r'\([^)]*\)', '', raw_text).strip()
            dist_clean = re.sub(r'\d+yds?', '', dist_clean).strip()  # remove yards portion
            race['distance_round'] = dist_clean if dist_clean else raw_text.strip()
            race['distance'] = dist_full_el[0].text_content().strip().strip('()') if dist_full_el else race['distance_round']
            race['distance_f'] = distance_to_furlongs(race['distance_round'])
        else:
            race['distance_round'] = ''
            race['distance'] = ''
            race['distance_f'] = 0.0
        
        # Region
        race['region'] = get_region(str(race['course_id']))
        race['pattern'] = get_pattern(race['race_name'])
        
        # Class
        class_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName_class")]')
        if class_el:
            race['race_class'] = class_el[0].text_content().strip().strip('()')
        else:
            race['race_class'] = 'Class 1' if race['pattern'] else ''
        
        # Race type from fences/hurdles indicator
        hurdles_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName_hurdles")]')
        fences_text = hurdles_el[0].text_content().strip().lower() if hurdles_el else ''
        if 'hurdle' in fences_text:
            race['type'] = 'Hurdle'
        elif 'fence' in fences_text:
            race['type'] = 'Chase'
        else:
            race_lower = race['race_name'].lower()
            if race['distance_f'] >= 12:
                if any(x in race_lower for x in {'national hunt flat', 'nh flat', 'bumper'}):
                    race['type'] = 'NH Flat'
                elif 'hurdle' in race_lower:
                    race['type'] = 'Hurdle'
                elif any(x in race_lower for x in {'chase', 'steeplechase'}):
                    race['type'] = 'Chase'
                else:
                    race['type'] = 'Flat'
            else:
                race['type'] = 'Flat'
        
        # Age band
        age_band_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName_ratingBandAndAgesAllowed")]')
        if age_band_el:
            band_text = age_band_el[0].text_content().strip().strip('()').split()
            race['age_band'] = band_text[0] if band_text else None
            race['rating_band'] = band_text[1] if len(band_text) > 1 else None
        else:
            race['age_band'] = None
            race['rating_band'] = None
        
        # Prize money
        prize_el = doc.xpath('//*[@data-test-selector="text-prizeMoney"]')
        if prize_el:
            prize_text = prize_el[0].text_content().strip()
            # Extract first prize value
            match = re.search(r'1st[\s:]*[\u00a3$]?([\d,.]+)', prize_text)
            race['prize'] = match.group(0).strip() if match else prize_text[:50]
        else:
            race['prize'] = None
        
        # Field size
        info_el = doc.xpath('//*[contains(@class, "rp-raceInfo")]')
        if info_el:
            info_text = info_el[0].text_content().strip().lower()
            match = re.search(r'(\d+)\s*ran', info_text)
            race['field_size'] = int(match.group(1)) if match else 0
        else:
            race['field_size'] = 0
        
        # Going
        going_el = doc.xpath('//*[contains(@class, "rp-raceTimeCourseName_condition")]')
        race['going'] = going_el[0].text_content().strip().title() if going_el else ''
        
        # Going/weather from going_info
        c_info = going_info.get(race['course_id'], {})
        race['going_detailed'] = c_info.get('going', race['going'])
        race['rail_movements'] = c_info.get('rail_movements', '')
        race['stalls'] = c_info.get('stalls', '')
        race['weather'] = c_info.get('weather', '')
        race['surface'] = get_surface(race['going'])
        
        # --- Runners ---
        runner_list = []
        runners = doc.xpath('//tr[contains(@class, "rp-horseTable__mainRow")]')
        
        for horse in runners:
            r_data = {}
            
            # Horse name and ID
            name_el = horse.xpath('.//a[contains(@class, "rp-horseTable__horse__name")]')
            if name_el:
                r_data['name'] = normalize_name(name_el[0].text_content().strip())
                href = name_el[0].get('href', '')
                try:
                    r_data['horse_id'] = int(href.split('/')[3])
                except (IndexError, ValueError):
                    r_data['horse_id'] = 0
            else:
                continue
            
            # Number (saddle cloth)
            scn_el = horse.xpath('.//*[contains(@class, "rp-horseTable__saddleClothNo")]')
            r_data['number'] = _safe_int(scn_el[0].text_content().strip().rstrip('.')) if scn_el else None
            
            # Draw
            draw_el = horse.xpath('.//*[contains(@class, "rp-horseTable__pos__draw")]')
            draw_text = draw_el[0].text_content().strip().strip('()') if draw_el else ''
            r_data['draw'] = _safe_int(draw_text) if draw_text else None
            
            # Position (result)
            pos_el = horse.xpath('.//*[contains(@class, "rp-horseTable__pos__number")]')
            r_data['position'] = pos_el[0].text_content().strip() if pos_el else ''
            
            # SP
            sp_el = horse.xpath('.//*[contains(@class, "rp-horseTable__horse__price")]')
            r_data['sp'] = sp_el[0].text_content().strip() if sp_el else ''
            
            # Weight
            wgt_el = horse.xpath('.//*[contains(@class, "rp-horseTable__wgt")]')
            r_data['lbs'] = _safe_int(wgt_el[0].text_content().strip()) if wgt_el else None
            
            # Age
            age_el = horse.xpath('.//*[contains(@class, "rp-horseTable__spanNarrow_age")]')
            r_data['age'] = _safe_int(age_el[0].text_content().strip()) if age_el else None
            
            # Headgear
            hg_el = horse.xpath('.//*[contains(@class, "rp-horseTable__headGear")]')
            r_data['headgear'] = hg_el[0].text_content().strip() if hg_el else None
            
            # Jockey and Trainer from human links
            humans = horse.xpath('.//a[contains(@class, "rp-horseTable__human__link")]')
            seen_ids = set()
            unique_humans = []
            for h in humans:
                h_href = h.get('href', '')
                if h_href not in seen_ids:
                    seen_ids.add(h_href)
                    unique_humans.append(h)
            
            if len(unique_humans) >= 1:
                r_data['jockey'] = normalize_name(unique_humans[0].text_content().strip())
                try:
                    r_data['jockey_id'] = int(unique_humans[0].get('href', '').split('/')[3])
                except (IndexError, ValueError):
                    r_data['jockey_id'] = None
            
            if len(unique_humans) >= 2:
                r_data['trainer'] = normalize_name(unique_humans[1].text_content().strip())
                try:
                    r_data['trainer_id'] = int(unique_humans[1].get('href', '').split('/')[3])
                except (IndexError, ValueError):
                    r_data['trainer_id'] = None
            
            # Silk image
            silk_el = horse.xpath('.//img[contains(@class, "rp-horseTable__silk")]/@src')
            r_data['silk_url'] = silk_el[0] if silk_el else None
            
            runner_list.append(r_data)
        
        race['runners'] = runner_list
        return race
    
    except Exception as e:
        print(f"Error processing result {url}: {e}")
        import traceback
        traceback.print_exc()
        return None


def parse_result_races(session, race_urls, date):
    """Parse result pages (past dates) using ThreadPool, same structure as parse_races."""
    races = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    
    print("Fetching detailed going and weather information...")
    going_info = get_going_info(session, date)
    print(f"Weather info fetched for {len(going_info)} courses.")
    
    total_races = len(race_urls)
    print(f"Starting scrape for {total_races} result pages using ThreadPool (Max 5 workers)...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_single_result, session, url, date, going_info): url for url in race_urls}
        
        completed_count = 0
        for future in as_completed(futures):
            completed_count += 1
            race_data = future.result()
            
            if race_data:
                races[race_data['region']][race_data['course']][race_data['off_time']] = race_data
                print(f"[{completed_count}/{total_races}] Processed: {race_data['course']} - {race_data['off_time']}")
            else:
                print(f"[{completed_count}/{total_races}] Failed to process a result.")
    
    return races

# ==================== RACECARD (CURRENT/FUTURE) FUNCTIONS ====================

def parse_races(session, race_urls, date):
    races = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    print("Fetching detailed going and weather information...")
    going_info = get_going_info(session, date)
    print(f"Weather info fetched for {len(going_info)} courses.")

    total_races = len(race_urls)
    print(f"Starting scrape for {total_races} races using ThreadPool (Max 5 workers)...")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_single_race, session, url, date, going_info): url for url in race_urls}
        
        completed_count = 0
        for future in as_completed(futures):
            completed_count += 1
            race_data = future.result()
            
            if race_data:
                # Add to structure
                races[race_data['region']][race_data['course']][race_data['off_time']] = race_data
                print(f"[{completed_count}/{total_races}] Processed: {race_data['course']} - {race_data['off_time']}")
            else:
                print(f"[{completed_count}/{total_races}] Failed to process a race.")

    return races

def get_runners(session, profile_urls):
    runners = {}
    for url in profile_urls:
        runner = {}
        try:
            r = session.get(url, timeout=5)
            doc = html.fromstring(r.content)
            
            scripts = doc.xpath('//script[contains(text(), "PRELOADED_STATE")]')
            if not scripts: raise ValueError("No State")

            content = scripts[0].text
            json_str = ''
            if 'window.PRELOADED_STATE =' in content:
                json_str = content.split('window.PRELOADED_STATE =')[1]
            elif 'var __PRELOADED_STATE__ =' in content:
                json_str = content.split('var __PRELOADED_STATE__ =')[1]
            
            js = loads(json_str.split('\n')[0].strip().strip(';'))
            profile = js.get('profile', {})

            runner['horse_id'] = profile.get('horseUid')
            runner['name'] = normalize_name(profile.get('horseName', ''))
            runner['dob'] = profile.get('horseDateOfBirth', '').split('T')[0]
            runner['sex'] = profile.get('horseSex')
            runner['sex_code'] = profile.get('horseSexCode')
            runner['colour'] = profile.get('horseColour')
            runner['region'] = profile.get('horseCountryOriginCode')
            runner['dam'] = normalize_name(profile.get('damHorseName', ''))
            runner['sire'] = normalize_name(profile.get('sireHorseName', ''))
            runner['damsire'] = normalize_name(profile.get('damSireHorseName', ''))
            runner['trainer'] = normalize_name(profile.get('trainerName', ''))
            runner['trainer_id'] = profile.get('trainerUid')
            runner['owner'] = normalize_name(profile.get('ownerName', ''))
            
            age_raw = str(profile.get('age', '0'))
            runner['age'] = int(age_raw.split('-')[0]) if '-' in age_raw else int(age_raw) if age_raw.isdigit() else 0

            runner['prev_trainers'] = profile.get('previousTrainers', [])
            runner['prev_owners'] = profile.get('previousOwners', [])
            
            med = profile.get('medical', [])
            runner['medical'] = [{'date': m.get('medicalDate', '').split('T')[0], 'type': m.get('medicalType')} for m in med]

        except Exception:
            try:
                split = url.split('/')
                runner['horse_id'] = int(split[5])
                runner['name'] = split[6].replace('-', ' ').title()
                runner['broken_url'] = url
            except Exception:
                continue

        if 'horse_id' in runner:
            runners[runner['horse_id']] = runner
            
    return runners

def valid_course(course):
    invalid = ['free to air', 'worldwide stakes', '(arab)']
    return all(x not in course for x in invalid)

def parse_selection(selection, total):
    if not selection or selection.lower() == 'all':
        return list(range(1, total + 1))
    numbers = set()
    for part in selection.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                numbers.update(range(max(1, start), min(total, end) + 1))
            except ValueError: continue
        else:
            try:
                num = int(part)
                if 1 <= num <= total: numbers.add(num)
            except ValueError: continue
    return sorted(numbers)

def merge_to_master(new_file_path):
    print(f"\nMerging {new_file_path.name} into master file...")
    
    # Ensure directory exists
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    
    merged_data = {}
    if MASTER_FILE.exists():
        try:
            with open(MASTER_FILE, 'r', encoding='utf-8') as f:
                merged_data = json.load(f)
        except Exception as e:
            print(f"Error reading master file: {e}")

    try:
        with open(new_file_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
            
        filename = new_file_path.name
        date_str = filename.split('_')[0]
        
        # Simple validation
        try:
             datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
             print(f"Could not parse date from {filename}, using filename as key.")
             date_str = filename.replace('.json', '')

        if date_str not in merged_data:
            merged_data[date_str] = {}

        # Merge logic: Date -> Region -> Course -> OffTime
        for region, courses in new_data.items():
            if region not in merged_data[date_str]:
                merged_data[date_str][region] = {}
            
            for course_name, races in courses.items():
                if course_name not in merged_data[date_str][region]:
                    merged_data[date_str][region][course_name] = {}
                
                for off_time, race_info in races.items():
                    merged_data[date_str][region][course_name][off_time] = race_info

        with open(MASTER_FILE, 'w', encoding='utf-8') as f:
            json.dump(merged_data, f, indent=2, ensure_ascii=False)
            
        print(f"SUCCESS: Merged into {MASTER_FILE}")

    except Exception as e:
        print(f"Error during merge: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Racing Post Scraper')
    parser.add_argument('--days', type=int, help='Days offset (0=Today, 1=Tomorrow, -1=Yesterday, etc)', default=None)
    parser.add_argument('--date', type=str, help='Exact date in YYYY-MM-DD format (e.g. 2026-02-13)', default=None)
    parser.add_argument('--all', action='store_true', help='Select all courses automatically')
    parser.add_argument('--merge', action='store_true', help='Automatically merge to master file')
    
    args = parser.parse_args()
    
    print("--- RP Scraper ---")
    
    # Date Selection
    today = datetime.now()
    
    if args.date:
        # Exact date provided
        try:
            date_obj = datetime.strptime(args.date, '%Y-%m-%d')
            date = args.date
            choice = (date_obj.date() - today.date()).days
            print(f"Using exact date: {date} ({choice:+d} days from today)")
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD.")
            return
    elif args.days is not None:
        choice = args.days
        date_obj = today + timedelta(days=choice)
        date = date_obj.strftime("%Y-%m-%d")
        print(f"Using days offset: {choice:+d} -> {date}")
    else:
        print("-1: Yesterday")
        print(" 0: Today")
        print(" 1: Tomorrow")
        print(" 2: Day After Tomorrow")
        try:
             choice = int(input("Enter days offset: ").strip())
        except ValueError:
             print("Invalid input, defaulting to 0")
             choice = 0
        date_obj = today + timedelta(days=choice)
        date = date_obj.strftime("%Y-%m-%d")
    
    print(f"Scraping for: {date}")

    session = get_session()
    base_url = 'https://www.racingpost.com/racecards'
    
    is_past = choice < 0
    
    if choice == 0:
        racecard_url = base_url
    elif choice == 1:
        racecard_url = f'{base_url}/tomorrow'
    else:
        racecard_url = f'{base_url}/{date}'

    print(f"Fetching courses for {date} from {racecard_url}...")
    
    # === PAST DATE FLOW ===
    if is_past:
        print(f"\n*** PAST DATE MODE - scraping from results pages ***")
        courses = get_past_courses(session, date)
        
        if not courses:
            print("\nNo valid courses found for this date.")
            return
        
        course_list = sorted(courses.keys())
        for i, course in enumerate(course_list, 1):
            print(f"{i}. {course} ({len(courses[course])} races)")
        
        # Course Selection
        if args.all:
            print("\nAuto-selecting ALL courses.")
            selected_indices = list(range(1, len(course_list) + 1))
        else:
            selection = input("\nEnter course numbers (e.g., 1,3-5) or press Enter for all: ").strip()
            selected_indices = parse_selection(selection, len(course_list))
        
        selected_courses = [course_list[i - 1] for i in selected_indices]
        race_urls = []
        for course in selected_courses:
            race_urls.extend(courses[course])
        race_urls = sorted(list(set(race_urls)))
        
        if not race_urls:
            print("No races selected.")
            return
        
        races = parse_result_races(session, race_urls, date)
    
    # === TODAY/FUTURE FLOW (existing) ===
    else:
        print(f"Fetching courses for {date} from {racecard_url}...")
        try:
            r = session.get(racecard_url, timeout=15)
            print(f"Status: {r.status_code}")
            doc = html.fromstring(r.content)
            title = doc.find('.//title')
            if title is not None:
                 print(f"Page Title: {title.text_content()}")
        except Exception as e:
            print(f"Critical Error connecting to Racing Post: {e}")
            return

        courses = {}
        meetings = doc.xpath('//section[@data-accordion-row]')
        if not meetings:
             meetings = doc.xpath('//div[contains(@class, "RC-meetingItem")]')

        for meeting in meetings:
            try:
                course_elem = meeting.xpath(".//span[contains(@class, 'RC-accordion__courseName')]")
                if not course_elem:
                     course_elem = meeting.xpath(".//a[contains(@class, 'RC-meetingItem__link')]")

                if course_elem:
                    course_text = course_elem[0].text_content().strip()
                    course_lower = course_text.lower()
                
                    if valid_course(course_lower):
                        course_display = ' '.join(course_text.split()).title()
                        race_links = meeting.xpath(".//a[contains(@class, 'RC-meetingItem__link')]/@href")
                        course_races = sorted(list(set(
                            [('https://www.racingpost.com' + l if not l.startswith('http') else l) for l in race_links]
                        )))
                        if course_races:
                            courses[course_display] = course_races
            except IndexError:
                continue

        if not courses:
            print("\nNo valid courses found.")
            print("If the Page Title above says 'Just a moment...', Cloudflare is blocking you.")
            print("Ensure 'curl_cffi' is installed: pip install curl_cffi")
            return

        course_list = sorted(courses.keys())
        for i, course in enumerate(course_list, 1):
            print(f"{i}. {course} ({len(courses[course])} races)")

        if args.all:
            print("\nAuto-selecting ALL courses.")
            selected_indices = list(range(1, len(course_list) + 1))
        else:
            selection = input("\nEnter course numbers (e.g., 1,3-5) or press Enter for all: ").strip()
            selected_indices = parse_selection(selection, len(course_list))
        
        selected_courses = [course_list[i - 1] for i in selected_indices]
        race_urls = []
        for course in selected_courses:
            race_urls.extend(courses[course])
        race_urls = sorted(list(set(race_urls)))

        if not race_urls:
            print("No races selected.")
            return

        races = parse_races(session, race_urls, date)

    # === OUTPUT (shared) ===
    RACECARDS_DIR.mkdir(parents=True, exist_ok=True)

    if len(selected_indices) == len(course_list):
        suffix = "all"
    else:
        suffixes = [c.lower().replace(' ', '_').replace('(', '').replace(')', '') for c in selected_courses]
        suffix = '_'.join(suffixes[:3])
        if len(selected_courses) > 3: suffix += "_etc"
            
    filename = f"{date}_{suffix}.json"
    output_path = RACECARDS_DIR / filename

    try:
        with open(output_path, 'wb') as f:
            f.write(dumps(races, option=OPT_NON_STR_KEYS))
        print(f"\nSUCCESS: Saved data for {len(selected_courses)} courses to:")
        print(f"-> {output_path}")
    except Exception as e:
        print(f"Error saving file: {e}")

    # Prompt for merge
    if output_path.exists():
        if args.merge:
            merge_to_master(output_path)
        else:
            try:
                ask = input("\nadd card to merged racecards? y/n: ").strip().lower()
                if ask == 'y':
                    merge_to_master(output_path)
            except KeyboardInterrupt:
                pass

    # ── Auto-fetch Betfair odds ──
    betfair_script = Path(__file__).parent / 'fetch_betfair_odds.py'
    if betfair_script.exists():
        print(f"\n{'='*50}")
        print(f"  AUTO-FETCHING BETFAIR ODDS FOR {date}")
        print(f"{'='*50}")
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, str(betfair_script), '--date', date],
                cwd=str(betfair_script.parent),
                timeout=120
            )
            if result.returncode == 0:
                print(f"\n✅ Betfair odds fetched successfully for {date}")
            else:
                print(f"\n⚠️ Betfair odds fetch exited with code {result.returncode}")
                print("   (This is OK if you haven't set up Betfair credentials yet)")
        except subprocess.TimeoutExpired:
            print("\n⚠️ Betfair odds fetch timed out after 120s")
        except Exception as e:
            print(f"\n⚠️ Could not fetch Betfair odds: {e}")
    else:
        print(f"\n[INFO] Betfair odds script not found at {betfair_script}")


if __name__ == '__main__':
    main()