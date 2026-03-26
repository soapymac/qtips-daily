#!/usr/bin/env python3
"""
Tipster V12 Premium Edition
===========================
Powered by CatBoost V11 Model + Ranking-Based Strategy

Features:
- Live Betfair & RapidAPI odds integration
- Premium ultra-modern styling (glassmorphism, vibrant gradients)
- Smart probability calibration via Isotonic Regression
- Dominance badges & dynamic ROI color coding
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
import ast
import webbrowser
import warnings
warnings.filterwarnings('ignore')

from mobile_generator import generate_mobile_html

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent
RACECARDS_DIR = BASE_DIR / "racecards"
OUTPUT_DIR = BASE_DIR / "Grok_V12_Tips"
OUTPUT_DIR.mkdir(exist_ok=True)
MODEL_DIR = BASE_DIR / "Grok_V11"
LIVE_ODDS_DIR = BASE_DIR / "live_odds"

def normalize_horse_name(name):
    """Normalize horse name for exact matching with JSON odds."""
    if not isinstance(name, str) or not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r'\s*\([a-z]+\)$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def load_live_odds(date_str):
    """Load live odds from Betfair and RapidAPI json files."""
    parsed_odds = {}
    odds_files = [
        (LIVE_ODDS_DIR / f"odds_{date_str}_betfair.json", "betfair"),
        (LIVE_ODDS_DIR / f"odds_{date_str}_rapidapi.json", "rapidapi"),
    ]
    
    for odds_file, source in odds_files:
        if not odds_file.exists(): continue
        try:
            with open(odds_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            raw_odds = data.get('odds', {})
            for norm_name, horse_data in raw_odds.items():
                if norm_name in parsed_odds: continue
                fractional_raw = horse_data.get('fractional', '')
                best_decimal = None
                
                if isinstance(fractional_raw, str) and fractional_raw.startswith('['):
                    try:
                        bookie_data_list = ast.literal_eval(fractional_raw)
                        for bd in bookie_data_list:
                            odd_val = float(bd.get('odd', 0))
                            if odd_val > 1 and (best_decimal is None or odd_val > best_decimal):
                                best_decimal = odd_val
                    except: pass
                
                if best_decimal is None and horse_data.get('decimal', 0) > 0:
                    best_decimal = horse_data['decimal']
                
                if best_decimal and best_decimal > 1:
                    horse_name = horse_data.get('name', '')
                    place_dec = horse_data.get('place_decimal')
                    place_terms = horse_data.get('place_terms')
                    parsed_odds[norm_name] = {
                        'original_name': horse_name, 'best_decimal': best_decimal, 'source': source,
                        'place_decimal': place_dec, 'place_terms': place_terms,
                        'ew_decimal': horse_data.get('ew_decimal'),
                        'ew_divisor': horse_data.get('ew_divisor'),
                        'ew_places': horse_data.get('ew_places')
                    }
                    simple_name = normalize_horse_name(horse_name)
                    if simple_name != norm_name and simple_name not in parsed_odds:
                        parsed_odds[simple_name] = parsed_odds[norm_name]
        except Exception as e:
            print(f"Error loading odds {odds_file.name}: {e}")
            
    return parsed_odds

def get_horse_odds(horse_name, live_odds):
    if not live_odds or not horse_name: return None
    norm_name = normalize_horse_name(horse_name)
    if norm_name in live_odds: return live_odds[norm_name]
    for key, data in live_odds.items():
        if norm_name in key or key in norm_name: return data
    return None

def format_odds_display(decimal_odds):
    """Return HTML with both decimal and fractional odds as togglable spans."""
    if not decimal_odds or decimal_odds <= 1: return None
    from fractions import Fraction
    dec_str = f'{decimal_odds:.2f}'
    if decimal_odds == 2.0:
        frac_str = 'Evs'
    else:
        frac = Fraction(decimal_odds - 1).limit_denominator(100)
        frac_str = f'{frac.numerator}/{frac.denominator}'
    return f'<span class="odds-dec">{dec_str}</span><span class="odds-frac">{frac_str}</span>'

def load_v11_artifacts():
    print("[OK] Loading Grok V11 Model & Calibrator...")
    from catboost import CatBoostClassifier
    model = CatBoostClassifier()
    model.load_model(str(MODEL_DIR / 'catboost_v11.cbm'))
    calibrator = joblib.load(str(MODEL_DIR / 'isotonic_calibrator_v11.joblib'))
    features = joblib.load(str(MODEL_DIR / 'features_v11.joblib'))
    return model, calibrator, features

def safe_float(x):
    try:
        if isinstance(x, str): x = x.replace('%', '').strip()
        return float(x)
    except: return np.nan

def parse_form_metrics(form):
    if pd.isna(form) or str(form).strip() == '':
        return 0, 0, 10.0
    clean = ''.join(c for c in str(form).upper() if c.isdigit())
    if not clean:
        return 0, 0, 10.0
    recent = [int(c) for c in clean[-6:]]
    wins = sum(1 for p in recent if p == 1)
    places = sum(1 for p in recent if p <= 3)
    avg_pos = sum(recent) / len(recent) if recent else 10.0
    return wins, places, avg_pos

def prepare_v11_features(races, features_list):
    """
    Simulate the exact data preparation steps performed in train_model_v11.py.
    This creates the DataFrame for inference.
    """
    rows = []
    
    for race in races:
        course = str(race.get('course', '')).lower()
        race_id = f"test_{course}_{race.get('off_time', '')}"
        
        for r in race.get('runners', []):
            stats = r.get('stats', {}) or {}
            form_str = r.get('form', '')
            wins, places, avg_pos = parse_form_metrics(form_str)
            
            base = {
                'race_id': race_id,
                'horse_name': r.get('name', ''),
                
                # Raw
                'pre_age': r.get('age'),
                'pre_sex': r.get('sex'),
                'pre_draw': r.get('draw'),
                'pre_lbs': r.get('lbs'),
                'pre_ofr': r.get('ofr'),
                'pre_rpr': r.get('rpr'),
                'pre_ts': r.get('ts'),
                
                # Form / History
                'pre_last_run_days': r.get('last_run'),
                'pre_form': form_str,
                'form_wins_last6': wins,
                'form_places_last6': places,
                'form_avg_pos_last6': avg_pos,
                
                # Categoricals
                'pre_jockey': r.get('jockey'),
                'pre_trainer': r.get('trainer'),
                'going': race.get('going'),
                'class': race.get('race_class'),
                'hg': r.get('headgear'),
                
                # Stats
                'pre_trainer_rtf': r.get('trainer_rtf'),
                'pre_trainer_14_runs': r.get('trainer_14_days', {}).get('runs', 0),
                'pre_trainer_14_wins': r.get('trainer_14_days', {}).get('wins', 0),
            }
            
            # Specialist Stats
            for st in ['course', 'distance', 'going', 'jockey', 'trainer']:
                s = stats.get(st, {})
                runs = float(s.get('runs', 0) or 0)
                wins = float(s.get('wins', 0) or 0)
                base[f'pre_{st}_strike'] = wins / max(runs, 1.0)
                
            rows.append(base)
            
    df = pd.DataFrame(rows)
    if len(df) == 0: return df
    
    # Feature Engineering (V11)
    for col in ['pre_ofr', 'pre_rpr', 'pre_ts', 'pre_lbs', 'pre_last_run_days']:
        df[col] = df[col].apply(safe_float).fillna(0)
        
    group = df.groupby('race_id')
    for col in ['pre_ofr', 'pre_rpr', 'pre_ts', 'pre_lbs', 'pre_last_run_days']:
        df[f'{col}_z'] = group[col].transform(lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0).fillna(0)
        df[f'{col}_rank'] = group[col].rank(ascending=False, method='min')
        
    df['speed_composite'] = (df['pre_ofr'] + df['pre_rpr'] + df['pre_ts']) / 3
    df['speed_composite_rank'] = group['speed_composite'].rank(ascending=False)
    
    # Clean Categoricals
    for cat in ['pre_sex', 'pre_jockey', 'pre_trainer', 'going', 'class', 'hg']:
        if cat not in df.columns: df[cat] = "Missing"
        df[cat] = df[cat].astype(str).fillna("Missing")
        
    # Ensure all numerical features exist and are float
    for f in features_list:
        if f not in df.columns: df[f] = 0.0
        if f not in ['pre_sex', 'pre_jockey', 'pre_trainer', 'going', 'class', 'hg']:
            df[f] = pd.to_numeric(df[f], errors='coerce').fillna(0.0)
            
    return df


def load_racecards(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    filename = Path(json_path).name
    match = re.match(r'(\d{4}-\d{2}-\d{2})', filename)
    date_str = match.group(1) if match else datetime.now().strftime('%Y-%m-%d')
    
    races = []
    for region, courses in data.items():
        if not courses: continue
        for course_name, course_races in courses.items():
            if not course_races: continue
            for off_time, race_info in course_races.items():
                if not race_info: continue
                runners = [r for r in race_info.get('runners', []) if r.get('jockey') != 'Non-Runner']
                if runners:
                    races.append({
                        'date': date_str, 'region': region, 'course': course_name,
                        'off_time': off_time, 'race_name': race_info.get('race_name', ''),
                        'race_class': race_info.get('race_class', ''),
                        'distance': race_info.get('distance', ''),
                        'distance_f': race_info.get('distance_f', 0),
                        'going': race_info.get('going', ''),
                        'type': race_info.get('type', 'Flat'),
                        'runners': runners
                    })
    
    races.sort(key=lambda x: x['off_time'])
    return races, date_str
    
BANKROLL_FILE = OUTPUT_DIR / 'bankroll_settings.json'

def load_bankroll_settings():
    defaults = {'bankroll': 1000.0, 'point_value': 1.0, 'commission': 0.05}
    if BANKROLL_FILE.exists():
        try:
            with open(BANKROLL_FILE, 'r') as f:
                d = json.load(f)
            for k, v in defaults.items():
                if k not in d: d[k] = v
            return d
        except: pass
    return defaults

def save_bankroll_settings(cfg):
    with open(BANKROLL_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

def fractional_kelly(prob, decimal_odds, cap=0.05):
    if not decimal_odds or decimal_odds <= 1.01 or prob <= 0:
        return 0.0
    b = decimal_odds - 1.0
    q = 1.0 - prob
    kelly = (prob * b - q) / b
    if kelly <= 0:
        return 0.0
    half_kelly = kelly * 0.5
    return min(cap, half_kelly)

def classify_bet(prob, decimal_odds, pred_rank=1, n_runners=10):
    """V12 Ranking-based bet classification."""
    if not decimal_odds or decimal_odds <= 1.01:
        return 'PASS', 0, 0, 'WIN'
    implied = 1.0 / decimal_odds
    edge = prob - implied
    edge_pct = edge * 100
    if pred_rank != 1:
        return 'PASS', edge_pct, 0, 'WIN'
    if decimal_odds < 2.0 or decimal_odds > 50.0:
        return 'PASS', edge_pct, 0, 'WIN'
    if n_runners > 14 or n_runners < 4:
        return 'PASS', edge_pct, 0, 'WIN'
    confidence = 50
    if 6.0 <= decimal_odds <= 20.0: confidence += 20
    elif 3.0 <= decimal_odds <= 6.0: confidence += 10
    elif 2.0 <= decimal_odds <= 3.0: confidence += 5
    elif decimal_odds > 20.0: confidence -= 10
    if 7 <= n_runners <= 10: confidence += 15
    elif n_runners <= 6: confidence += 5
    if prob > 0.14: confidence += 10
    elif prob > 0.12: confidence += 5
    if confidence >= 75:
        tier, stake_pts = 'STRONG', 2.0
    elif confidence >= 60:
        tier, stake_pts = 'GOOD', 1.5
    else:
        tier, stake_pts = 'FAIR', 1.0
    if decimal_odds >= 8.0 and n_runners >= 8:
        bet_type = 'E/W'
        stake_pts *= 0.8
    else:
        bet_type = 'WIN'
    return tier, edge_pct, round(stake_pts, 1), bet_type

def calculate_dutch_stakes(probs, odds_list, total_stake):
    if len(probs) != 2 or len(odds_list) != 2:
        return [total_stake / 2] * 2
    inv = [1.0 / o if o > 1 else 1 for o in odds_list]
    total_inv = sum(inv)
    return [total_stake * (i / total_inv) for i in inv]

def select_race_bets(preds, live_odds_map, bankroll_cfg, n_runners=10):
    """V12: Only bet on model's #1 ranked horse per race."""
    pt = bankroll_cfg['point_value']
    comm = bankroll_cfg['commission']
    if not preds:
        return []
    p = preds[0]
    h_odds_data = get_horse_odds(p['horse'], live_odds_map)
    dec_odds = h_odds_data.get('best_decimal') if h_odds_data else None
    if not dec_odds or dec_odds <= 1.01:
        return []
    tier, edge_pct, stake_pts, bet_type = classify_bet(
        p['prob'], dec_odds, pred_rank=1, n_runners=n_runners
    )
    if tier == 'PASS' or stake_pts <= 0:
        return []
    net_odds = 1 + (dec_odds - 1) * (1 - comm)
    return [{
        'horse': p['horse'], 'prob': p['prob'], 'odds': dec_odds,
        'edge_pct': edge_pct, 'tier': tier, 'bet_type': bet_type,
        'stake_pts': round(stake_pts, 1),
        'stake_gbp': round(stake_pts * pt, 2),
        'net_return': round(stake_pts * pt * (net_odds - 1), 2),
        'full_data': p.get('full_data', {})
    }]

def generate_forecast_tricast(preds, live_odds_map):
    if len(preds) < 3:
        return None
    top3_prob = sum(p['prob'] for p in preds[:3])
    if top3_prob < 0.35:
        return None
    fc = {'type': 'FORECAST', 'first': preds[0]['horse'], 'second': preds[1]['horse'],
          'stake_pts': 0.5, 'confidence': top3_prob * 100}
    result = {'forecast': fc, 'tricast': None}
    if top3_prob >= 0.45:
        result['tricast'] = {
            'type': 'TRICAST BOX', 'horses': [p['horse'] for p in preds[:3]],
            'stake_pts': 0.2, 'confidence': top3_prob * 100}
    return result

def generate_horse_insights(horse, all_runners, race_info):
    insights = []
    def safe_num(val):
        try: return float(val) if val else 0
        except: return 0
    h_ofr = safe_num(horse.get('ofr'))
    field_ofr = [safe_num(r.get('ofr')) for r in all_runners if safe_num(r.get('ofr')) > 0]
    if h_ofr > 0 and field_ofr and h_ofr == max(field_ofr):
         insights.append({'icon': '👑', 'text': f'Class Leader (OR {int(h_ofr)})'})
    form = str(horse.get('form', ''))
    if '1' in form[-2:]:
        insights.append({'icon': '🔥', 'text': 'Recent Winner'})
    stats = horse.get('stats', {}) or {}
    course_stats = stats.get('course', {}) or {}
    if safe_num(course_stats.get('wins')) > 0:
        insights.append({'icon': '📍', 'text': 'Course Specialist'})
    last_run = safe_num(horse.get('last_run'))
    if last_run >= 100:
        insights.append({'icon': '⏳', 'text': f'{int(last_run)} Day Layoff'})
    return insights[:3]

def generate_premium_html(races, predictions_by_race, date_str, live_odds=None, available_dates=None, bankroll_cfg=None):
    if available_dates is None: available_dates = [date_str]
    if bankroll_cfg is None: bankroll_cfg = load_bankroll_settings()
    pt = bankroll_cfg['point_value']

    courses = {}
    for race in races:
        c = race['course']
        if c not in courses: courses[c] = {'going': race['going'], 'races': []}
        courses[c]['races'].append(race)

    nav_html = ''.join([f'<a href="#{re.sub(r"[^a-zA-Z0-9]", "", c)}" class="glass-pill">{c}</a>' for c in courses.keys()])

    # ── Build actionable bets per race ──
    all_bets = []
    bankers, values, punts = [], [], []
    big_payouts = []

    for race in races:
        race_key = f"{race['course']}_{race['off_time']}"
        preds = predictions_by_race.get(race_key, [])
        if not preds: continue
        race_bets = select_race_bets(preds, live_odds, bankroll_cfg, n_runners=len(race['runners']))
        for b in race_bets:
            b['time'] = race['off_time']
            b['course'] = race['course']
            b['race_name'] = race.get('race_name', '')
        all_bets.extend(race_bets)
        for b in race_bets:
            if b['tier'] == 'STRONG': bankers.append(b)
            elif b['tier'] == 'GOOD': values.append(b)
            elif b['tier'] == 'FAIR': punts.append(b)
        fc = generate_forecast_tricast(preds, live_odds)
        if fc:
            fc['time'] = race['off_time']
            fc['course'] = race['course']
            big_payouts.append(fc)

    all_bets.sort(key=lambda x: x['edge_pct'], reverse=True)
    top_bets = all_bets[:6]
    total_risk = sum(b['stake_gbp'] for b in top_bets)

    # ── Today's Bets table ──
    bets_rows = ""
    for b in top_bets:
        odds_disp = format_odds_display(b['odds']) or '-'
        dutch_warn = ' <span class="dutch-warn">⚠️ DUTCH</span>' if b.get('is_dutch') else ''
        edge_color = '#00f5a0' if b['edge_pct'] > 5 else '#00f2fe' if b['edge_pct'] > 3 else '#f093fb'
        bets_rows += f'''<tr>
            <td class="td-time">{b['time']}<br><span class="td-course">{b['course']}</span></td>
            <td class="td-horse">{b['horse']}{dutch_warn}</td>
            <td class="td-odds">{odds_disp}</td>
            <td class="td-edge" style="color:{edge_color}">+{b['edge_pct']:.1f}%</td>
            <td class="td-stake">{b['stake_pts']}pt<br><span class="td-gbp">£{b['stake_gbp']:.0f}</span></td>
            <td class="td-type"><span class="type-chip type-{b['bet_type'].replace('/', '').replace(' ', '').lower()}">{b['bet_type']}</span></td>
            <td class="td-risk">£{b['stake_gbp']:.0f}</td>
        </tr>'''

    # ── Category cards ──
    def make_cat_cards(items, empty_msg):
        if not items:
            return f'<div class="cat-empty">{empty_msg}</div>'
        h = ''
        for b in items[:4]:
            odds_disp = format_odds_display(b['odds']) or '-'
            h += f'''<div class="cat-card">
                <div class="cc-top"><span class="cc-time">{b['time']} {b['course']}</span><span class="cc-type type-chip type-{b['bet_type'].replace('/', '').replace(' ', '').lower()}">{b['bet_type']}</span></div>
                <div class="cc-horse">{b['horse']}</div>
                <div class="cc-bottom"><span class="cc-odds">{odds_disp}</span><span class="cc-edge">+{b['edge_pct']:.1f}% edge</span><span class="cc-stake">{b['stake_pts']}pt (£{b['stake_gbp']:.0f})</span></div>
            </div>'''
        return h

    bankers_html = make_cat_cards(bankers, 'No STRONG confidence picks today')
    values_html = make_cat_cards(values, 'No GOOD confidence picks today')
    punts_html = make_cat_cards(punts, 'No FAIR confidence picks today')

    # ── Big Payout Plays ──
    bp_html = ''
    for bp in big_payouts[:4]:
        fc = bp.get('forecast', {})
        tc = bp.get('tricast')
        bp_html += f'''<div class="bp-card">
            <div class="bp-header">{bp['time']} {bp['course']} <span class="bp-conf">{fc['confidence']:.0f}% top-3 conf</span></div>
            <div class="bp-row"><span class="bp-label">📊 FORECAST</span> {fc['first']} → {fc['second']} <span class="bp-stake">{fc['stake_pts']}pt</span></div>'''
        if tc:
            bp_html += f'<div class="bp-row"><span class="bp-label">🎰 TRICAST BOX</span> {" / ".join(tc["horses"])} <span class="bp-stake">{tc["stake_pts"]}pt</span></div>'
        bp_html += '</div>'

    # ── Date options ──
    date_options = ""
    for d in sorted(available_dates, reverse=True):
        selected = "selected" if d == date_str else ""
        date_options += f'<option value="tips_{d}.html" {selected}>{d}</option>'

    # ── Race detail cards ──
    course_html = ""
    for course_name, course_data in courses.items():
        course_id = re.sub(r'[^a-zA-Z0-9]', '', course_name)
        race_rows = ""
        for race in course_data['races']:
            race_key = f"{race['course']}_{race['off_time']}"
            race_id = f"{course_id}_{race['off_time'].replace(':', '')}"
            preds = predictions_by_race.get(race_key, [])
            if not preds: continue
            top_prob = preds[0]['prob'] * 100
            second_prob = preds[1]['prob'] * 100 if len(preds) > 1 else 0
            gap = top_prob - second_prob
            race_badge = ""
            card_glow = ""
            if gap >= 15:
                race_badge = f'<span class="race-tag auth-tag">⭐ +{gap:.0f}% GAP</span>'
                card_glow = "race-block-gold"
            elif gap >= 8:
                race_badge = f'<span class="race-tag clear-tag">⚡ DOMINANT</span>'
            runners_html = ""
            total_preds = len(preds)
            for i, p in enumerate(preds):
                prob_pct = p['prob'] * 100
                horse_name = p['horse']
                h_odds_data = get_horse_odds(horse_name, live_odds) if live_odds else None
                actual_odds = h_odds_data.get('best_decimal') if h_odds_data else None
                place_odds_val = h_odds_data.get('place_decimal') if h_odds_data else None
                place_terms_val = h_odds_data.get('place_terms') if h_odds_data else None
                ew_odds_val = h_odds_data.get('ew_decimal') if h_odds_data else None
                ew_divisor_val = h_odds_data.get('ew_divisor') if h_odds_data else None
                ew_places_val = h_odds_data.get('ew_places') if h_odds_data else None
                odds_display = format_odds_display(actual_odds) or "-"
                tier, edge_pct, _, bet_type = classify_bet(p['prob'], actual_odds, pred_rank=i+1, n_runners=len(race['runners']))
                tier_colors = {'STRONG': '#00f5a0', 'GOOD': '#00f2fe', 'FAIR': '#f093fb', 'PASS': '#4b5563'}
                t_color = tier_colors.get(tier, '#4b5563')
                tier_label = f'{tier} {bet_type}' if tier != 'PASS' else 'PASS'
                insights_html = ""
                insights = generate_horse_insights(p.get('full_data', {}), [pp['full_data'] for pp in preds], race)
                for ins in insights:
                    insights_html += f'<span class="insight-bubble">{ins["icon"]} {ins["text"]}</span>'
                form = str(p.get('full_data', {}).get('form', '-'))[:6]
                jockey = str(p.get('full_data', {}).get('jockey', 'U/K'))[:15]
                orating = p.get('full_data', {}).get('ofr', '-')
                extra_cls = ' runner-extra' if i >= 8 else ''
                po_attr = f' data-place-odds="{place_odds_val:.2f}"' if place_odds_val else ''
                pt_attr = f' data-place-terms="{place_terms_val}"' if place_terms_val else ''
                ew_attr = f' data-ew-odds="{ew_odds_val:.2f}"' if ew_odds_val else ''
                ewd_attr = f' data-ew-divisor="{ew_divisor_val}"' if ew_divisor_val else ''
                ewp_attr = f' data-ew-places="{ew_places_val}"' if ew_places_val else ''
                # Bet suggestion data for P/L calculation
                stake_pts = 0
                if tier != 'PASS' and actual_odds:
                    if tier == 'STRONG': stake_pts = 2.0
                    elif tier == 'GOOD': stake_pts = 1.5
                    else: stake_pts = 1.0
                    if bet_type == 'E/W': stake_pts *= 0.8
                    stake_pts = round(stake_pts, 1)
                bet_attrs = f' data-tier="{tier}" data-stake-pts="{stake_pts}" data-bet-type="{bet_type}" data-win-odds="{actual_odds:.2f}"' if tier != 'PASS' and actual_odds else ''
                # E/W / Place odds for main line
                sub_odds_html = ''
                if place_odds_val and place_terms_val:
                    sub_odds_html += f'<div style="font-size:0.7rem; color:#00f2fe; margin-top:2px;">📍 {place_odds_val:.2f} <span style="color:#64748b">({place_terms_val}pl)</span></div>'
                if ew_odds_val and ew_places_val:
                    ew_div_label = f'1/{int(ew_divisor_val)}' if ew_divisor_val else ''
                    sub_odds_html += f'<div style="font-size:0.7rem; color:#f093fb; margin-top:2px;">🎰 E/W {ew_odds_val:.2f} <span style="color:#64748b">({ew_div_label} {ew_places_val}pl)</span></div>'
                elif bet_type == 'E/W' and actual_odds and actual_odds >= 6.0:
                    n_runners = len(race['runners'])
                    est_places = 3 if n_runners <= 15 else 4
                    sub_odds_html += f'<div style="font-size:0.7rem; color:#f093fb; margin-top:2px;">🎰 E/W suggested <span style="color:#64748b">({est_places}pl est)</span></div>'
                stake_html = ''
                if tier != 'PASS' and stake_pts > 0:
                    stake_gbp = stake_pts * bankroll_cfg['point_value']
                    stake_html = f'<div style="font-size:0.7rem; color:{t_color}; margin-top:3px; font-weight:700;">💰 {stake_pts}pt (£{stake_gbp:.0f})</div>'
                # Build stats JSON for the expanded panel
                fd = p.get('full_data', {})
                stats_obj = fd.get('stats', {}) or {}
                stats_json = json.dumps({
                    'sire': fd.get('sire', '-'),
                    'draw': fd.get('draw', '-'),
                    'number': fd.get('number', '-'),
                    'headgear': fd.get('headgear', ''),
                    'lbs': fd.get('lbs', '-'),
                    'ofr': fd.get('ofr', '-'),
                    'rpr': fd.get('rpr', '-'),
                    'ts': fd.get('ts', '-'),
                    'jockey': fd.get('jockey', '-'),
                    'last_run': fd.get('last_run', '-'),
                    'form': fd.get('form', '-'),
                    'trainer_rtf': fd.get('trainer_rtf', '-'),
                    'course': stats_obj.get('course', {}),
                    'distance': stats_obj.get('distance', {}),
                    'going': stats_obj.get('going', {}),
                    'jockey_stats': stats_obj.get('jockey', {}),
                    'trainer_stats': stats_obj.get('trainer', {}),
                }, default=str).replace("'", "&#39;").replace('"', '&quot;')
                runners_html += f'''<div class="runner-row {'top-runner' if i==0 else ''}{extra_cls}" data-horse="{horse_name}" data-prob="{p['prob']:.6f}" data-runners="{len(race['runners'])}" data-pt-value="{bankroll_cfg['point_value']:.0f}" data-commission="{bankroll_cfg['commission']:.2f}"{po_attr}{pt_attr}{ew_attr}{ewd_attr}{ewp_attr}{bet_attrs} data-stats="{stats_json}" onclick="toggleTargetOdds(this)">
                    <div class="rank-col"><div class="circ-rank" style="{'background: linear-gradient(135deg, #facc15, #eab308); color: #000;' if i==0 else ''}">{i+1}</div></div>
                    <div class="name-col"><h4>{horse_name}</h4><p>{jockey} • OR: {orating} • {form}</p><div class="insight-row">{insights_html}</div></div>
                    <div class="odds-col"><div class="odds-val">{odds_display}</div>{sub_odds_html}<div class="advice-chip" style="background: {t_color}15; color: {t_color}; border-color: {t_color}40;">{tier_label}</div>{stake_html}</div>
                    <div class="prob-col"><div class="prob-val" style="color: {t_color}">{prob_pct:.1f}%</div><div class="track-bg"><div class="track-fill" style="width: {prob_pct}%; background: {t_color};"></div></div></div>
                    <div class="target-panel"></div>
                    <div class="pl-panel"></div>
                </div>'''
            show_more_btn = ''
            if total_preds > 8:
                show_more_btn = f'<div class="show-more-btn" onclick="toggleExtra(this)">▼ Show all {total_preds} runners</div>'
            top1_name = preds[0]['horse'] if preds else ''
            top1_prob = f"{preds[0]['prob']*100:.0f}%" if preds else ''
            race_rows += f'''<div class="race-block {card_glow} collapsed" id="{race_id}">
                <div class="race-header" onclick="toggleRace(this)"><div class="rh-left"><h3>{race['off_time']}</h3><span class="rh-desc">{race['race_name'][:45]}</span></div>
                <div class="rh-right"><span class="rh-pick">🏇 {top1_name} ({top1_prob})</span>{race_badge}<span class="race-tag base-tag">{race['distance']}</span><span class="race-tag base-tag">{len(race['runners'])} Run</span><span class="rh-chevron">▼</span></div></div>
                <div class="runner-container">{runners_html}{show_more_btn}</div></div>'''
        course_html += f'''<section id="{course_id}" class="course-section"><div class="course-banner"><h2>{course_name}</h2><span class="course-going">{course_data['going']}</span></div>{race_rows}</section>'''

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Q-Tips V12 | AI Racing Intelligence</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{ --bg: #030712; --glass-bg: rgba(15,23,42,0.6); --glass-border: rgba(255,255,255,0.08); --text-main: #f8fafc; --text-mut: #94a3b8; --primary: #00f2fe; --accent: #4facfe; --success: #00f5a0; --gold: #facc15; --card-radius: 20px; }}
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ background-color:var(--bg); background-image:radial-gradient(circle at top right,rgba(79,172,254,0.1),transparent 40%),radial-gradient(circle at bottom left,rgba(0,242,254,0.05),transparent 40%); color:var(--text-main); font-family:'Plus Jakarta Sans',sans-serif; min-height:100vh; background-attachment:fixed; }}
        h1,h2,h3,h4 {{ font-family:'Outfit',sans-serif; }}
        .glass-nav {{ position:fixed; top:0; width:100%; z-index:100; background:rgba(3,7,18,0.7); backdrop-filter:blur(20px); border-bottom:1px solid var(--glass-border); padding:15px 30px; display:flex; align-items:center; justify-content:space-between; }}
        .nav-logo {{ font-size:1.5rem; font-weight:900; font-family:'Outfit'; background:linear-gradient(135deg,var(--primary),var(--accent)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
        .nav-controls {{ display:flex; gap:12px; align-items:center; }}
        .glass-select {{ background:rgba(255,255,255,0.05); color:white; border:1px solid var(--glass-border); padding:8px 16px; border-radius:12px; font-family:inherit; outline:none; cursor:pointer; }}
        .glass-select option {{ background:var(--bg); }}
        .btn-check,.btn-settings {{ background:linear-gradient(135deg,#f093fb,#f5576c); color:white; border:none; padding:8px 20px; border-radius:12px; font-weight:600; cursor:pointer; box-shadow:0 4px 15px rgba(245,87,108,0.3); transition:transform 0.2s; font-size:0.9rem; }}
        .btn-check:hover,.btn-settings:hover {{ transform:translateY(-2px); }}
        .btn-settings {{ background:linear-gradient(135deg,#4facfe,#00f2fe); font-size:0.85rem; padding:8px 14px; }}
        .track-scroller {{ position:fixed; top:68px; width:100%; z-index:99; background:rgba(15,23,42,0.4); backdrop-filter:blur(10px); border-bottom:1px solid var(--glass-border); padding:10px 30px; display:flex; gap:12px; overflow-x:auto; scrollbar-width:none; }}
        .track-scroller::-webkit-scrollbar {{ display:none; }}
        .glass-pill {{ background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1); color:var(--text-mut); padding:6px 16px; border-radius:20px; text-decoration:none; font-size:0.9rem; font-weight:500; white-space:nowrap; transition:all 0.3s; }}
        .glass-pill:hover {{ background:var(--primary); color:var(--bg); border-color:var(--primary); }}
        .main-container {{ max-width:1300px; margin:0 auto; padding:140px 20px 50px; }}

        /* Today's Bets */
        .bets-panel {{ background:linear-gradient(135deg,rgba(250,204,21,0.08),rgba(0,242,254,0.05)); border:1px solid rgba(250,204,21,0.25); border-radius:var(--card-radius); padding:0; margin-bottom:30px; overflow:hidden; }}
        .bets-title {{ background:linear-gradient(135deg,rgba(250,204,21,0.15),rgba(0,245,160,0.08)); padding:18px 24px; display:flex; align-items:center; justify-content:space-between; border-bottom:1px solid rgba(250,204,21,0.2); }}
        .bets-title h2 {{ font-size:1.4rem; color:var(--gold); }}
        .bets-title .risk-total {{ font-size:1rem; color:var(--text-mut); }}
        .bets-title .risk-total strong {{ color:#00f5a0; }}
        .bets-table {{ width:100%; border-collapse:collapse; }}
        .bets-table th {{ text-align:left; padding:12px 16px; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; color:var(--text-mut); border-bottom:1px solid var(--glass-border); font-weight:600; }}
        .bets-table td {{ padding:14px 16px; border-bottom:1px solid rgba(255,255,255,0.03); font-size:0.95rem; }}
        .bets-table tr:hover {{ background:rgba(255,255,255,0.02); }}
        .td-time {{ white-space:nowrap; font-weight:700; font-family:'Outfit'; }}
        .td-course {{ font-size:0.8rem; color:var(--text-mut); font-weight:400; }}
        .td-horse {{ font-weight:700; font-size:1.05rem; }}
        .td-odds {{ font-family:'Outfit'; font-weight:800; color:white; font-size:1.1rem; }}
        .td-edge {{ font-weight:800; font-family:'Outfit'; font-size:1.1rem; }}
        .td-stake {{ font-weight:700; }}
        .td-gbp {{ font-size:0.8rem; color:var(--text-mut); }}
        .td-risk {{ font-weight:700; color:var(--gold); }}
        .type-chip {{ padding:4px 10px; border-radius:6px; font-size:0.75rem; font-weight:800; display:inline-block; }}
        .type-win {{ background:rgba(0,245,160,0.15); color:#00f5a0; border:1px solid rgba(0,245,160,0.3); }}
        .type-ew {{ background:rgba(0,242,254,0.15); color:#00f2fe; border:1px solid rgba(0,242,254,0.3); }}
        .type-dutchwin {{ background:rgba(240,147,251,0.15); color:#f093fb; border:1px solid rgba(240,147,251,0.3); }}
        .dutch-warn {{ color:#f093fb; font-size:0.8rem; margin-left:6px; }}
        .bets-empty {{ padding:30px; text-align:center; color:var(--text-mut); font-size:1rem; }}

        /* Category Sections */
        .cats-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-bottom:30px; }}
        .cat-section {{ background:var(--glass-bg); border:1px solid var(--glass-border); border-radius:var(--card-radius); overflow:hidden; }}
        .cat-header {{ padding:16px 20px; border-bottom:1px solid var(--glass-border); display:flex; align-items:center; gap:10px; }}
        .cat-header h3 {{ font-size:1.1rem; }}
        .cat-header.banker {{ background:linear-gradient(135deg,rgba(0,245,160,0.1),transparent); }}
        .cat-header.value {{ background:linear-gradient(135deg,rgba(0,242,254,0.1),transparent); }}
        .cat-header.punt {{ background:linear-gradient(135deg,rgba(240,147,251,0.1),transparent); }}
        .cat-body {{ padding:12px; }}
        .cat-card {{ background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:12px; padding:14px; margin-bottom:10px; transition:all 0.3s; }}
        .cat-card:hover {{ background:rgba(255,255,255,0.05); border-color:rgba(255,255,255,0.15); transform:translateY(-2px); }}
        .cc-top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }}
        .cc-time {{ font-size:0.8rem; color:var(--text-mut); font-weight:500; }}
        .cc-horse {{ font-size:1.1rem; font-weight:700; margin-bottom:8px; }}
        .cc-bottom {{ display:flex; gap:12px; align-items:center; font-size:0.85rem; }}
        .cc-odds {{ font-weight:800; color:white; font-family:'Outfit'; }}
        .cc-edge {{ color:var(--primary); font-weight:700; }}
        .cc-stake {{ color:var(--text-mut); margin-left:auto; font-weight:600; }}
        .cat-empty {{ padding:20px; text-align:center; color:var(--text-mut); font-size:0.9rem; }}

        /* Big Payout Plays */
        .bp-panel {{ background:var(--glass-bg); border:1px solid var(--glass-border); border-radius:var(--card-radius); margin-bottom:30px; overflow:hidden; }}
        .bp-title {{ padding:16px 20px; border-bottom:1px solid var(--glass-border); display:flex; align-items:center; justify-content:space-between; cursor:pointer; user-select:none; }}
        .bp-title h3 {{ color:#f093fb; font-size:1.1rem; }}
        .bp-body {{ padding:12px; }}
        .bp-body.collapsed {{ display:none; }}
        .bp-card {{ background:rgba(240,147,251,0.05); border:1px solid rgba(240,147,251,0.15); border-radius:12px; padding:14px; margin-bottom:10px; }}
        .bp-header {{ font-weight:700; margin-bottom:8px; font-size:0.95rem; }}
        .bp-conf {{ color:#f093fb; font-size:0.8rem; margin-left:8px; }}
        .bp-row {{ padding:6px 0; font-size:0.9rem; display:flex; align-items:center; gap:8px; }}
        .bp-label {{ font-weight:800; font-size:0.75rem; padding:3px 8px; border-radius:4px; background:rgba(240,147,251,0.15); color:#f093fb; }}
        .bp-stake {{ margin-left:auto; font-weight:700; color:var(--gold); }}
        .bp-empty {{ padding:20px; text-align:center; color:var(--text-mut); font-size:0.9rem; }}

        /* Bankroll Modal */
        .modal-overlay {{ position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.7); backdrop-filter:blur(4px); z-index:1000; display:none; align-items:center; justify-content:center; }}
        .modal-overlay.show {{ display:flex; }}
        .modal-box {{ background:#0f172a; border:1px solid var(--glass-border); border-radius:var(--card-radius); width:90%; max-width:420px; padding:30px; box-shadow:0 20px 40px rgba(0,0,0,0.6); }}
        .modal-box h2 {{ font-size:1.3rem; margin-bottom:20px; color:white; }}
        .modal-field {{ margin-bottom:16px; }}
        .modal-field label {{ display:block; font-size:0.85rem; color:var(--text-mut); margin-bottom:6px; font-weight:600; }}
        .modal-field input {{ width:100%; background:rgba(255,255,255,0.05); border:1px solid var(--glass-border); color:white; padding:10px 14px; border-radius:10px; font-size:1rem; font-family:inherit; outline:none; }}
        .modal-field input:focus {{ border-color:var(--primary); }}
        .modal-actions {{ display:flex; gap:12px; margin-top:20px; }}
        .modal-actions button {{ flex:1; padding:10px; border-radius:10px; font-weight:700; cursor:pointer; border:none; font-size:0.95rem; }}
        .modal-save {{ background:linear-gradient(135deg,#00f5a0,#00f2fe); color:#000; }}
        .modal-cancel {{ background:rgba(255,255,255,0.1); color:white; }}

        /* Race Detail Cards */
        .course-section {{ margin-bottom:40px; scroll-margin-top:120px; }}
        .course-banner {{ display:flex; justify-content:space-between; align-items:flex-end; border-bottom:1px solid var(--glass-border); padding-bottom:12px; margin-bottom:24px; }}
        .course-banner h2 {{ font-size:2.2rem; font-weight:800; }}
        .course-going {{ color:var(--primary); font-weight:700; text-transform:uppercase; letter-spacing:2px; font-size:0.85rem; }}
        .race-block {{ background:var(--glass-bg); border:1px solid var(--glass-border); border-radius:var(--card-radius); margin-bottom:12px; overflow:hidden; box-shadow:0 10px 30px rgba(0,0,0,0.3); transition:all 0.3s; }}
        .race-block:hover {{ border-color:rgba(255,255,255,0.15); }}
        .race-block-gold {{ box-shadow:0 0 30px rgba(250,204,21,0.1); border-color:rgba(250,204,21,0.3); }}
        .race-block.collapsed .runner-container {{ display:none; }}
        .race-block.collapsed .rh-chevron {{ transform:rotate(0deg); }}
        .race-block:not(.collapsed) .rh-chevron {{ transform:rotate(180deg); }}
        .race-header {{ padding:20px 24px; background:rgba(30,41,59,0.4); display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--glass-border); cursor:pointer; user-select:none; transition:background 0.2s; }}
        .race-header:hover {{ background:rgba(30,41,59,0.6); }}
        .rh-left h3 {{ color:white; font-size:1.6rem; margin-bottom:4px; display:inline-block; margin-right:12px; }}
        .rh-desc {{ color:var(--text-mut); font-size:0.9rem; font-weight:500; }}
        .rh-pick {{ color:var(--gold); font-weight:700; font-size:0.85rem; margin-right:8px; }}
        .rh-chevron {{ color:var(--text-mut); font-size:0.85rem; margin-left:6px; transition:transform 0.3s; }}
        .runner-row.runner-extra {{ display:none !important; }}
        .runner-container.expanded .runner-row.runner-extra {{ display:grid !important; }}
        .show-more-btn {{ text-align:center; padding:12px; color:var(--primary); font-weight:700; font-size:0.9rem; cursor:pointer; border-top:1px solid var(--glass-border); transition:background 0.2s; }}
        .show-more-btn:hover {{ background:rgba(0,242,254,0.05); }}
        .rh-right {{ display:flex; gap:10px; align-items:center; }}
        .race-tag {{ padding:6px 12px; border-radius:8px; font-size:0.8rem; font-weight:700; }}
        .base-tag {{ background:rgba(255,255,255,0.1); color:var(--text-mut); }}
        .auth-tag {{ background:rgba(250,204,21,0.2); color:var(--gold); border:1px solid rgba(250,204,21,0.4); }}
        .clear-tag {{ background:rgba(0,245,160,0.2); color:var(--success); border:1px solid rgba(0,245,160,0.4); }}
        .runner-container {{ padding:10px; }}
        .runner-row {{ display:grid; grid-template-columns:50px 1fr 100px 120px; align-items:center; padding:16px; border-radius:12px; margin-bottom:6px; transition:background 0.2s; cursor:pointer; position:relative; }}
        .runner-row:hover {{ background:rgba(255,255,255,0.03); }}
        .top-runner {{ background:linear-gradient(90deg,rgba(255,255,255,0.03),transparent); }}
        .target-panel {{ display:none; grid-column:1/-1; margin-top:10px; padding:12px 16px; background:rgba(0,0,0,0.4); border:1px solid rgba(255,255,255,0.1); border-radius:10px; }}
        .runner-row.show-targets .target-panel {{ display:block; }}
        .tp-title {{ font-size:0.8rem; color:var(--text-mut); font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px; }}
        .tp-grid {{ display:flex; gap:12px; flex-wrap:wrap; }}
        .tp-item {{ background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px 14px; min-width:140px; flex:1; }}
        .tp-item.tp-qualifies {{ border-color:rgba(0,245,160,0.4); background:rgba(0,245,160,0.08); }}
        .tp-tier {{ font-size:0.75rem; font-weight:800; margin-bottom:4px; }}
        .tp-tier.tp-banker {{ color:#00f5a0; }}
        .tp-tier.tp-value {{ color:#00f2fe; }}
        .tp-tier.tp-punt {{ color:#f093fb; }}
        .tp-odds {{ font-size:1.1rem; font-weight:800; color:white; font-family:'Outfit'; }}
        .tp-note {{ font-size:0.75rem; color:var(--text-mut); margin-top:2px; }}
        .tp-na {{ color:var(--text-mut); font-size:0.85rem; font-style:italic; }}
        .tp-divider {{ grid-column:1/-1; border-top:1px solid rgba(255,255,255,0.08); margin:6px 0; width:100%; }}
        .tp-section {{ grid-column:1/-1; font-size:0.8rem; color:var(--gold); font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-top:4px; }}
        .tp-place {{ border-color:rgba(0,242,254,0.2); }}
        .tp-place .tp-tier {{ color:var(--primary); }}
        .tp-place.tp-qualifies {{ border-color:rgba(0,242,254,0.5); background:rgba(0,242,254,0.08); }}
        .circ-rank {{ width:32px; height:32px; border-radius:50%; background:rgba(255,255,255,0.1); display:flex; align-items:center; justify-content:center; font-weight:800; color:var(--text-mut); }}
        .name-col h4 {{ font-size:1.15rem; margin-bottom:4px; color:white; }}
        .name-col p {{ font-size:0.85rem; color:var(--text-mut); margin-bottom:6px; }}
        .insight-row {{ display:flex; gap:8px; flex-wrap:wrap; }}
        .insight-bubble {{ background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.05); padding:4px 10px; border-radius:20px; font-size:0.75rem; color:#cbd5e1; }}
        .pos-badge {{ font-size:0.85rem; padding:2px 8px; border-radius:6px; font-weight:800; margin-left:10px; text-transform:uppercase; display:inline-block; vertical-align:middle; }}
        .pos-badge.gold {{ background:linear-gradient(135deg,#facc15,#eab308); color:#000; box-shadow:0 0 10px rgba(250,204,21,0.5); }}
        .pos-badge.placed {{ background:rgba(255,255,255,0.1); color:#e2e8f0; border:1px solid rgba(255,255,255,0.2); }}
        .pos-badge.unplaced {{ background:transparent; color:#64748b; font-weight:500; border:1px dashed #334155; }}
        .odds-col {{ text-align:right; padding-right:20px; }}
        .odds-val {{ font-size:1.1rem; font-weight:800; margin-bottom:6px; color:white; }}
        .advice-chip {{ display:inline-block; padding:4px 8px; border-radius:6px; font-size:0.75rem; font-weight:800; border:1px solid; }}
        .prob-col {{ text-align:right; }}
        .prob-val {{ font-size:1.4rem; font-weight:800; margin-bottom:6px; font-family:'Outfit'; }}
        .track-bg {{ width:100%; height:6px; background:rgba(255,255,255,0.1); border-radius:3px; overflow:hidden; }}
        .track-fill {{ height:100%; border-radius:3px; }}
        @media(max-width:1000px) {{ .cats-grid {{ grid-template-columns:1fr; }} }}
        .odds-frac {{ display:none; }}
        body.frac-mode .odds-dec {{ display:none; }}
        body.frac-mode .odds-frac {{ display:inline; }}
        .btn-odds {{ background:rgba(255,255,255,0.08); color:var(--text-mut); border:1px solid var(--glass-border); padding:8px 14px; border-radius:12px; font-weight:600; cursor:pointer; font-size:0.85rem; transition:all 0.2s; }}
        .btn-odds:hover {{ border-color:var(--primary); color:white; }}
        .btn-refresh {{ background:linear-gradient(135deg,#00f5a0,#00d2ff); color:#000; border:none; padding:8px 14px; border-radius:12px; font-weight:700; cursor:pointer; font-size:0.85rem; transition:all 0.2s; }}
        .btn-refresh:hover {{ transform:translateY(-2px); box-shadow:0 4px 15px rgba(0,245,160,0.3); }}
        .btn-refresh.loading {{ opacity:0.6; pointer-events:none; }}
        @media(max-width:900px) {{ .main-container {{ padding-top:130px; }} .runner-row {{ grid-template-columns:40px 1fr 80px; }} .prob-col {{ display:none; }} }}
    </style>
</head>
<body>
    <nav class="glass-nav">
        <div class="nav-logo">Q-TIPS V12</div>
        <div class="nav-controls">
            <select class="glass-select" onchange="window.location.href=this.value">{date_options}</select>
            <button class="btn-odds" id="odds-toggle" onclick="toggleOddsFormat()">Fractional</button>
            <button class="btn-refresh" id="refresh-btn" onclick="refreshOdds()">🔄 Refresh Odds</button>
            <button class="btn-settings" onclick="showPLSummary()">📊 P/L</button>
            <button class="btn-check" onclick="checkResults()">Check Results</button>
        </div>
    </nav>
    <div class="track-scroller">{nav_html}</div>

    <div class="main-container">
        <!-- TODAY'S BETS -->
        <div class="bets-panel">
            <div class="bets-title">
                <h2>💰 TODAY'S BETS — PLACE THESE NOW</h2>
                <div class="risk-total">Total Risk: <strong>£{total_risk:.0f}</strong> ({len(top_bets)} bets)</div>
            </div>
            {f'<table class="bets-table"><thead><tr><th>Time</th><th>Horse</th><th>Odds</th><th>Edge</th><th>Stake</th><th>Type</th><th>Risk</th></tr></thead><tbody>{bets_rows}</tbody></table>' if bets_rows else '<div class="bets-empty">No qualifying bets found — check odds are loaded</div>'}
        </div>

        <!-- CATEGORY SECTIONS -->
        <div class="cats-grid">
            <div class="cat-section"><div class="cat-header banker"><h3>💪 STRONG</h3></div><div class="cat-body">{bankers_html}</div></div>
            <div class="cat-section"><div class="cat-header value"><h3>👍 GOOD</h3></div><div class="cat-body">{values_html}</div></div>
            <div class="cat-section"><div class="cat-header punt"><h3>🎯 FAIR</h3></div><div class="cat-body">{punts_html}</div></div>
        </div>

        <!-- BIG PAYOUT PLAYS -->
        <div class="bp-panel">
            <div class="bp-title" onclick="this.nextElementSibling.classList.toggle('collapsed')"><h3>🎰 Big-Payout Plays (Forecasts & Tricasts)</h3><span style="color:var(--text-mut)">▼</span></div>
            <div class="bp-body">{bp_html if bp_html else '<div class="bp-empty">No qualifying forecast/tricast plays today</div>'}</div>
        </div>

        <!-- RACE DETAILS -->
        {course_html}
    </div>

    <!-- P/L SUMMARY MODAL -->
    <div id="pl-modal" class="modal-overlay" onclick="if(event.target===this) this.classList.remove('show')">
        <div class="modal-box" style="max-width:650px;max-height:80vh;overflow-y:auto;">
            <h2>📊 Day P/L Summary</h2>
            <div id="pl-content" style="color:#94a3b8;text-align:center;padding:20px;">Click "Check Results" first to see your P/L breakdown</div>
            <div class="modal-actions">
                <button class="modal-cancel" onclick="document.getElementById('pl-modal').classList.remove('show')">Close</button>
            </div>
        </div>
    </div>

    <script>
        const REPORT_DATE = '{date_str}';
        const API_BASE = 'http://localhost:5123';
        let resultsChecked = false;

        function scrollToHorse(horseName) {{
            document.getElementById('pl-modal').classList.remove('show');
            const rows = document.querySelectorAll('.runner-row[data-horse]');
            for (let i = 0; i < rows.length; i++) {{
                if (rows[i].dataset.horse === horseName) {{
                    const raceBlock = rows[i].closest('.race-block');
                    if (raceBlock && raceBlock.classList.contains('collapsed')) {{
                        toggleRace(raceBlock.querySelector('.race-header'));
                    }}
                    setTimeout(() => {{
                        rows[i].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        const oldBg = rows[i].style.background;
                        rows[i].style.background = 'rgba(99,102,241,0.3)';
                        setTimeout(() => rows[i].style.background = oldBg, 1500);
                    }}, 300);
                    break;
                }}
            }}
        }}

        // Odds format toggle
        (function() {{
            if (localStorage.getItem('v11_odds_mode') === 'frac') {{
                document.body.classList.add('frac-mode');
                document.getElementById('odds-toggle').textContent = 'Decimal';
            }}
        }})();
        function toggleOddsFormat() {{
            const btn = document.getElementById('odds-toggle');
            document.body.classList.toggle('frac-mode');
            const isFrac = document.body.classList.contains('frac-mode');
            btn.textContent = isFrac ? 'Decimal' : 'Fractional';
            localStorage.setItem('v11_odds_mode', isFrac ? 'frac' : 'dec');
        }}

        async function refreshOdds() {{
            const btn = document.getElementById('refresh-btn');
            btn.classList.add('loading');
            btn.innerHTML = '⏳ Fetching odds...';
            try {{
                const resp = await fetch(`${{API_BASE}}/api/refresh-odds/${{REPORT_DATE}}`);
                if (!resp.ok) throw new Error(`Server error ${{resp.status}}`);
                const data = await resp.json();
                if (data.success) {{
                    btn.innerHTML = '✅ Reloading...';
                    btn.style.background = 'linear-gradient(135deg,#facc15,#eab308)';
                    setTimeout(() => window.location.reload(), 1000);
                }} else {{
                    const failStep = data.steps.find(s => !s.ok);
                    throw new Error(failStep ? failStep.msg : 'Unknown error');
                }}
            }} catch (err) {{
                console.error('Refresh error:', err);
                btn.innerHTML = '❌ ' + err.message;
                btn.style.background = '#f5576c';
                setTimeout(() => {{
                    btn.innerHTML = '🔄 Refresh Odds';
                    btn.style.background = '';
                    btn.classList.remove('loading');
                }}, 3000);
            }}
        }}

        function toggleRace(header) {{
            const block = header.closest('.race-block');
            const wasCollapsed = block.classList.contains('collapsed');
            // Collapse all races first (accordion)
            document.querySelectorAll('.race-block').forEach(b => b.classList.add('collapsed'));
            // If it was collapsed, open it
            if (wasCollapsed) {{
                block.classList.remove('collapsed');
                block.scrollIntoView({{ behavior:'smooth', block:'start' }});
            }}
        }}

        function toggleTargetOdds(row) {{
            // Don't trigger if clicking on links or buttons inside
            if (event.target.closest('a, button, .show-more-btn')) return;
            const wasOpen = row.classList.contains('show-targets');
            // Close all open panels in this race
            row.closest('.runner-container').querySelectorAll('.runner-row.show-targets').forEach(r => r.classList.remove('show-targets'));
            if (wasOpen) return;

            const prob = parseFloat(row.dataset.prob);
            if (!prob || prob <= 0) return;
            const panel = row.querySelector('.target-panel');
            if (!panel) return;

            // ── HORSE STATS SECTION ──
            let statsData = null;
            try {{ statsData = JSON.parse(row.dataset.stats || '{{}}'); }} catch(e) {{}}

            let html = '';
            if (statsData) {{
                const s = statsData;
                const hg = s.headgear ? ` <span style="color:#f093fb;font-weight:700">${{s.headgear}}</span>` : '';
                html += `<div style="margin-bottom:14px">`;
                html += `<div class="tp-title">📝 Horse Profile</div>`;

                // Row 1: Key Ratings
                html += `<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(90px,1fr)); gap:8px; margin-bottom:10px">`;
                const ratings = [
                    {{label:'OR', value:s.ofr, color:'#facc15'}},
                    {{label:'RPR', value:s.rpr, color:'#00f2fe'}},
                    {{label:'TS', value:s.ts, color:'#00f5a0'}},
                    {{label:'Weight', value:s.lbs ? s.lbs+'lbs' : '-', color:'#94a3b8'}},
                    {{label:'Draw', value:s.draw, color:'#f093fb'}},
                    {{label:'Days Since', value:s.last_run, color: parseInt(s.last_run)>=60 ? '#ef4444' : '#00f5a0'}},
                ];
                for (const r of ratings) {{
                    html += `<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:8px 10px; text-align:center">`;
                    html += `<div style="font-size:0.65rem; color:var(--text-mut); font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:2px">${{r.label}}</div>`;
                    html += `<div style="font-size:1.1rem; font-weight:800; color:${{r.color}}; font-family:'Outfit'">${{r.value || '-'}}</div>`;
                    html += `</div>`;
                }}
                html += `</div>`;

                // Row 2: Connections
                html += `<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:10px">`;
                // Jockey
                const jStats = s.jockey_stats || {{}};
                const jL14 = jStats.last_14_wins_pct || '-';
                const jOvr = jStats.ovr_wins_pct || '-';
                const jProfit = jStats.ovr_profit || '-';
                html += `<div style="background:rgba(0,242,254,0.05); border:1px solid rgba(0,242,254,0.15); border-radius:8px; padding:10px">`;
                html += `<div style="font-size:0.7rem; color:var(--text-mut); font-weight:600; text-transform:uppercase; margin-bottom:4px">🏇 Jockey</div>`;
                html += `<div style="font-weight:700; color:white; margin-bottom:4px">${{s.jockey}}</div>`;
                html += `<div style="font-size:0.8rem; color:var(--text-mut)">14d: ${{jL14}} • Overall: ${{jOvr}} • P/L: ${{jProfit}}</div>`;
                html += `</div>`;
                // Trainer
                const tStats = s.trainer_stats || {{}};
                const tL14 = tStats.last_14_wins_pct || '-';
                const tOvr = tStats.ovr_wins_pct || '-';
                const tProfit = tStats.ovr_profit || '-';
                const tRtf = s.trainer_rtf ? s.trainer_rtf + '%' : '-';
                html += `<div style="background:rgba(240,147,251,0.05); border:1px solid rgba(240,147,251,0.15); border-radius:8px; padding:10px">`;
                html += `<div style="font-size:0.7rem; color:var(--text-mut); font-weight:600; text-transform:uppercase; margin-bottom:4px">🏫 Trainer (RTF: ${{tRtf}})</div>`;
                html += `<div style="font-size:0.8rem; color:var(--text-mut)">14d: ${{tL14}} • Overall: ${{tOvr}} • P/L: ${{tProfit}}</div>`;
                html += `</div>`;
                html += `</div>`;

                // Row 3: Form & Sire
                html += `<div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:10px">`;
                html += `<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px">`;
                html += `<div style="font-size:0.7rem; color:var(--text-mut); font-weight:600; text-transform:uppercase; margin-bottom:4px">📝 Form${{hg}}</div>`;
                const formStr = s.form || '-';
                let formHtml = '';
                for (const ch of formStr.toString()) {{
                    let col = 'var(--text-mut)';
                    if (ch === '1') col = '#facc15';
                    else if (['2','3'].includes(ch)) col = '#00f5a0';
                    else if (['4','5'].includes(ch)) col = '#00f2fe';
                    else if (ch === '-') col = '#64748b';
                    formHtml += `<span style="font-size:1.2rem; font-weight:800; font-family:'Outfit'; color:${{col}}; margin-right:3px">${{ch}}</span>`;
                }}
                html += formHtml;
                html += `</div>`;
                html += `<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px">`;
                html += `<div style="font-size:0.7rem; color:var(--text-mut); font-weight:600; text-transform:uppercase; margin-bottom:4px">🐎 Sire</div>`;
                html += `<div style="font-weight:600; color:white">${{s.sire || '-'}}</div>`;
                html += `</div>`;
                html += `</div>`;

                // Row 4: Course / Distance / Going record
                html += `<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:6px">`;
                const records = [
                    {{label:'📍 Course', data:s.course}},
                    {{label:'📏 Distance', data:s.distance}},
                    {{label:'🌧️ Going', data:s.going}},
                ];
                for (const rec of records) {{
                    const d = rec.data || {{}};
                    const runs = d.runs || '0';
                    const wins = d.wins || '0';
                    const winPct = parseInt(runs) > 0 ? ((parseInt(wins)/parseInt(runs))*100).toFixed(0) : '0';
                    const barColor = parseInt(wins) > 0 ? '#00f5a0' : '#4b5563';
                    html += `<div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px; text-align:center">`;
                    html += `<div style="font-size:0.65rem; color:var(--text-mut); font-weight:600; text-transform:uppercase; margin-bottom:4px">${{rec.label}}</div>`;
                    html += `<div style="font-size:0.95rem; font-weight:800; color:white">${{wins}}/${{runs}}</div>`;
                    html += `<div style="height:4px; background:rgba(255,255,255,0.1); border-radius:2px; margin-top:4px; overflow:hidden">`;
                    html += `<div style="height:100%; width:${{winPct}}%; background:${{barColor}}; border-radius:2px"></div>`;
                    html += `</div>`;
                    html += `<div style="font-size:0.7rem; color:var(--text-mut); margin-top:2px">${{winPct}}% SR</div>`;
                    html += `</div>`;
                }}
                html += `</div>`;

                html += `</div>`;
                html += '<div class="tp-divider"></div>';
            }}

            // V12: Ranking-based confidence scoring
            const tiers = [];
            const rank = Array.from(row.parentElement.querySelectorAll('.runner-row')).indexOf(row) + 1;
            const N = parseInt(row.dataset.runners) || 0;
            const oddsEl = row.querySelector('.odds-dec');
            const currentOdds = oddsEl ? parseFloat(oddsEl.textContent) : 0;
            
            if (rank === 1 && currentOdds >= 2.0 && currentOdds <= 50.0 && N >= 4 && N <= 14) {{
                let conf = 50;
                if (currentOdds >= 6 && currentOdds <= 20) conf += 20;
                else if (currentOdds >= 3 && currentOdds <= 6) conf += 10;
                else if (currentOdds >= 2 && currentOdds <= 3) conf += 5;
                else if (currentOdds > 20) conf -= 10;
                if (N >= 7 && N <= 10) conf += 15;
                else if (N <= 6) conf += 5;
                if (prob > 0.14) conf += 10;
                else if (prob > 0.12) conf += 5;
                let tierName = 'FAIR', stake = '1.0pt';
                if (conf >= 75) {{ tierName = 'STRONG'; stake = '2.0pt'; }}
                else if (conf >= 60) {{ tierName = 'GOOD'; stake = '1.5pt'; }}
                const betType = (currentOdds >= 8 && N >= 8) ? 'E/W' : 'WIN';
                tiers.push({{ tier: tierName, cls: 'tp-banker', min: 2.0, max: 50.0,
                    note: betType + ' ' + stake + ' | Confidence: ' + conf + '/100 | Field: ' + N + ' runners' }});
            }} else if (rank === 1) {{
                let reason = '';
                if (currentOdds < 2.0) reason = 'Odds too short (min 2.0)';
                else if (currentOdds > 50.0) reason = 'Odds too long (max 50.0)';
                else if (N < 4) reason = 'Too few runners (min 4)';
                else if (N > 14) reason = 'Too many runners (max 14)';
                tiers.push({{ tier: 'FILTERED', cls: 'tp-punt', min: null, note: reason }});
            }} else {{
                tiers.push({{ tier: 'NOT #1 PICK', cls: 'tp-punt', min: null, note: 'Ranked #' + rank + ' - V12 only bets on #1 pick per race' }});
            }}

            html += '<div class="tp-title">📊 Target Odds to Qualify</div><div class="tp-grid">';
            if (tiers.length === 0) {{
                html += '<div class="tp-na">Probability too low to qualify for any bet tier</div>';
            }} else {{
                for (const t of tiers) {{
                    const qualifies = t.min && currentOdds >= t.min;
                    html += `<div class="tp-item ${{qualifies ? 'tp-qualifies' : ''}}">`;
                    html += `<div class="tp-tier ${{t.cls}}">${{t.tier}} ${{qualifies ? '✅' : ''}}</div>`;
                    if (t.min) {{
                        html += `<div class="tp-odds">&ge; ${{t.min.toFixed(2)}}</div>`;
                        if (t.max) html += `<div class="tp-note">up to ${{t.max.toFixed(2)}}</div>`;
                    }} else {{
                        html += `<div class="tp-na">N/A</div>`;
                    }}
                    html += `<div class="tp-note">${{t.note}}</div></div>`;
                }}
            }}
            html += '</div>';

            // ── PLACE BETTING SECTION ──
            // N already declared above in V12 block
            const livePlaceOdds = parseFloat(row.dataset.placeOdds) || 0;
            const livePlaceTerms = parseInt(row.dataset.placeTerms) || 0;

            if (N >= 5) {{
                html += '<div class="tp-divider"></div>';
                html += '<div class="tp-title" style="margin-top:8px">🏇 Exchange Place Markets</div>';

                // Show live Betfair place odds if available
                if (livePlaceOdds > 0) {{
                    const liveImplied = (1 / livePlaceOdds) * 100;
                    const placeTermsLabel = livePlaceTerms > 0 ? `Top ${{livePlaceTerms}}` : 'Place';
                    // Compute estimated place prob for comparison
                    const k = livePlaceTerms || 3;
                    const estPlaceProb = Math.min(0.95, k * prob * N / (N + k - 1));
                    const fairOdds = 1 / estPlaceProb;
                    const hasEdge = livePlaceOdds > fairOdds;

                    html += '<div class="tp-grid">';
                    html += `<div class="tp-item tp-place ${{hasEdge ? 'tp-qualifies' : ''}}" style="min-width:200px">`;
                    html += `<div class="tp-tier" style="color:#00f5a0">🟢 LIVE BETFAIR PLACE (${{placeTermsLabel}}) ${{hasEdge ? '✅ VALUE' : ''}}</div>`;
                    html += `<div class="tp-odds" style="font-size:1.3rem">${{livePlaceOdds.toFixed(2)}}</div>`;
                    html += `<div class="tp-note">Implied: ${{liveImplied.toFixed(1)}}% • Model est: ${{(estPlaceProb*100).toFixed(1)}}%</div>`;
                    html += `<div class="tp-note">Fair: ${{fairOdds.toFixed(2)}} ${{hasEdge ? '• Edge: +' + ((1/fairOdds - 1/livePlaceOdds)*100).toFixed(1) + '%' : '• No edge yet'}}</div>`;
                    html += '</div></div>';
                }}

                html += '<div class="tp-grid" style="margin-top:8px">';

                // Also show estimated odds for all place terms
                const placeTerms = [];
                if (N >= 5 && N <= 7) placeTerms.push({{ k:2, label:'Top 2' }});
                if (N >= 8 && N <= 11) placeTerms.push({{ k:2, label:'Top 2' }}, {{ k:3, label:'Top 3' }});
                if (N >= 12 && N <= 15) placeTerms.push({{ k:3, label:'Top 3' }}, {{ k:4, label:'Top 4' }});
                if (N >= 16 && N <= 19) placeTerms.push({{ k:3, label:'Top 3' }}, {{ k:4, label:'Top 4' }}, {{ k:5, label:'Top 5' }});
                if (N >= 20) placeTerms.push({{ k:3, label:'Top 3' }}, {{ k:4, label:'Top 4' }}, {{ k:5, label:'Top 5' }}, {{ k:6, label:'Top 6' }});

                for (const pt of placeTerms) {{
                    const placeProb = Math.min(0.95, pt.k * prob * N / (N + pt.k - 1));
                    const fairOdds = 1 / placeProb;
                    const minBackOdds = fairOdds * 1.05;
                    let rating, ratingColor;
                    if (placeProb >= 0.60) {{ rating = 'STRONG'; ratingColor = '#00f5a0'; }}
                    else if (placeProb >= 0.40) {{ rating = 'GOOD'; ratingColor = '#00f2fe'; }}
                    else if (placeProb >= 0.25) {{ rating = 'FAIR'; ratingColor = '#facc15'; }}
                    else {{ rating = 'LONG'; ratingColor = '#f093fb'; }}

                    // Check if live place odds for this term show value
                    const liveMatch = (livePlaceTerms === pt.k && livePlaceOdds > 0);
                    const qualifies = liveMatch ? livePlaceOdds >= minBackOdds : false;

                    html += `<div class="tp-item tp-place ${{qualifies ? 'tp-qualifies' : ''}}">`;
                    html += `<div class="tp-tier" style="color:${{ratingColor}}">${{pt.label}} (${{pt.k}} places) ${{qualifies ? '✅' : ''}}</div>`;
                    html += `<div class="tp-odds">≥ ${{minBackOdds.toFixed(2)}}</div>`;
                    html += `<div class="tp-note">Place prob: ${{(placeProb*100).toFixed(1)}}% • Fair: ${{fairOdds.toFixed(2)}}</div>`;
                    if (liveMatch) {{
                        html += `<div class="tp-note" style="color:#00f5a0">Live: ${{livePlaceOdds.toFixed(2)}} ${{qualifies ? '✅ BACK THIS' : ''}}</div>`;
                    }} else {{
                        html += `<div class="tp-note" style="color:${{ratingColor}}">Rating: ${{rating}}</div>`;
                    }}
                    html += '</div>';
                }}
                html += '</div>';
                html += `<div style="margin-top:8px;font-size:0.75rem;color:var(--text-mut)">ℹ️ Field: ${{N}} runners. Min odds include 5% edge buffer.${{livePlaceOdds > 0 ? ' 🟢 = Live Betfair place odds loaded.' : ' No live place odds — estimates shown.'}}</div>`;
            }} else if (N > 0) {{
                html += '<div class="tp-divider"></div>';
                html += `<div style="font-size:0.8rem;color:var(--text-mut);margin-top:6px">⚠️ Only ${{N}} runners — no exchange place market available</div>`;
            }}

            // ── EACH WAY SECTION ──
            const ewOdds = parseFloat(row.dataset.ewOdds) || 0;
            const ewDivisor = parseFloat(row.dataset.ewDivisor) || 0;
            const ewPlaces = parseInt(row.dataset.ewPlaces) || 0;

            if (ewOdds > 0) {{
                html += '<div class="tp-divider"></div>';
                html += '<div class="tp-title" style="margin-top:8px">🎰 Each Way Market (Betfair)</div>';
                
                // Calculate the implied place portion
                const ewPlacePart = ewDivisor > 0 ? 1 + (ewOdds - 1) / ewDivisor : 0;
                const ewImplied = (1 / ewOdds) * 100;
                const placesLabel = ewPlaces > 0 ? `${{ewPlaces}} places` : 'Place';
                const divisorLabel = ewDivisor > 0 ? `1/${{ewDivisor}} odds` : '';
                
                // Compare with model's estimate
                const k = ewPlaces || 3;
                const estPlaceProb = Math.min(0.95, k * prob * N / (N + k - 1));
                const fairEwOdds = 1 / ((prob + estPlaceProb) / 2);
                const hasEdge = ewOdds > fairEwOdds;

                html += '<div class="tp-grid">';
                html += `<div class="tp-item tp-place ${{hasEdge ? 'tp-qualifies' : ''}}" style="min-width:250px">`;
                html += `<div class="tp-tier" style="color:#f093fb">🎰 E/W: ${{divisorLabel}}, ${{placesLabel}} ${{hasEdge ? '✅ VALUE' : ''}}</div>`;
                html += `<div class="tp-odds" style="font-size:1.3rem">${{ewOdds.toFixed(2)}}</div>`;
                html += `<div class="tp-note">Win implied: ${{ewImplied.toFixed(1)}}%</div>`;
                if (ewPlacePart > 0) {{
                    html += `<div class="tp-note">Place part: ${{ewPlacePart.toFixed(2)}}</div>`;
                }}
                html += `<div class="tp-note">Model win: ${{(prob*100).toFixed(1)}}% • Place est: ${{(estPlaceProb*100).toFixed(1)}}%</div>`;
                html += '</div></div>';
            }}

            panel.innerHTML = html;
            row.classList.add('show-targets');
        }}

        function toggleExtra(btn) {{
            const container = btn.closest('.runner-container');
            container.classList.toggle('expanded');
            if (container.classList.contains('expanded')) {{
                btn.textContent = '▲ Show top 8 only';
            }} else {{
                const total = container.querySelectorAll('.runner-row').length;
                btn.textContent = '▼ Show all ' + total + ' runners';
            }}
        }}

        function normalizeHorseName(name) {{
            if (!name) return '';
            return name.toLowerCase().replace(/\\s*\\([^)]+\\)$/, '').replace(/[^a-z0-9]/g, '');
        }}

        async function checkResults() {{
            const btn = document.querySelector('.btn-check');
            btn.innerHTML = resultsChecked ? 'Refreshing...' : 'Loading...';
            btn.style.opacity = '0.7';
            try {{
                let response = await fetch(`${{API_BASE}}/api/cached/${{REPORT_DATE}}`);
                let data;
                if (response.status === 404) {{
                    response = await fetch(`${{API_BASE}}/api/results/${{REPORT_DATE}}`);
                    if (!response.ok) throw new Error('Live scrape failed');
                    data = await response.json();
                }} else if (!response.ok) {{
                    throw new Error('Cache error');
                }} else {{
                    data = await response.json();
                }}
                if (data.success && data.results) {{
                    updatePageWithResults(data.results);
                    resultsChecked = true;
                    btn.innerHTML = `✅ ${{data.count}} horses`;
                    btn.style.background = 'linear-gradient(135deg, #00f5a0, #00d2ff)';
                }} else {{ throw new Error(data.error || 'No results'); }}
            }} catch (err) {{
                console.error('Results error:', err);
                btn.innerHTML = '❌ Offline';
                btn.style.background = '#f5576c';
            }}
            btn.style.opacity = '1';
        }}

        function updatePageWithResults(results) {{
            document.querySelectorAll('.runner-row').forEach(row => {{
                const nameEl = row.querySelector('h4');
                if (!nameEl) return;
                const normName = normalizeHorseName(nameEl.textContent);
                if (results[normName]) {{
                    const res = results[normName];
                    const pos = res.pos;
                    const existingBadge = nameEl.querySelector('.pos-badge');
                    if (existingBadge) existingBadge.remove();
                    let badgeHtml = '';
                    if (pos === 1) {{
                        badgeHtml = '<span class="pos-badge gold">1st</span>';
                        row.style.background = 'rgba(250, 204, 21, 0.15)';
                        row.style.boxShadow = 'inset 4px 0 0 #facc15';
                    }} else if (pos > 1 && pos <= 4) {{
                        const suffix = pos === 2 ? 'nd' : pos === 3 ? 'rd' : 'th';
                        badgeHtml = `<span class="pos-badge placed">${{pos}}${{suffix}}</span>`;
                    }} else if (pos > 4) {{
                        badgeHtml = `<span class="pos-badge unplaced">${{pos}}th</span>`;
                    }} else {{
                        badgeHtml = `<span class="pos-badge unplaced">PU</span>`;
                    }}
                    if (!row.dataset.plainName) row.dataset.plainName = nameEl.textContent;
                    nameEl.innerHTML = row.dataset.plainName + badgeHtml;
                    if (res.dec && res.dec > 0) {{
                        const oddsVal = row.querySelector('.odds-val');
                        if (oddsVal) oddsVal.textContent = 'SP ' + (res.dec - 1).toFixed(2);
                    }}
                }}
            }});
            // Also highlight Today's Bets table
            document.querySelectorAll('.bets-table .td-horse').forEach(td => {{
                const normName = normalizeHorseName(td.textContent);
                if (results[normName]) {{
                    const pos = results[normName].pos;
                    if (pos === 1) {{ td.style.color = '#facc15'; td.innerHTML += ' <span class="pos-badge gold">1st</span>'; }}
                    else if (pos <= 4) {{ td.innerHTML += ` <span class="pos-badge placed">${{pos}}${{pos===2?'nd':pos===3?'rd':'th'}}</span>`; }}
                }}
            }});
        }}

        let plMode = 'normal'; // 'normal' or 'sp'
        
        function togglePLMode() {{
            plMode = (plMode === 'normal') ? 'sp' : 'normal';
            document.querySelectorAll('.runner-row[data-tier]').forEach(r => {{
                const btnPanel = r.querySelector('.pl-panel');
                if (btnPanel && r.dataset.normalPl !== undefined) renderRowPL(r, btnPanel);
            }});
            renderDayPLSummary();
            if (document.getElementById('pl-modal').classList.contains('show')) {{
                showPLSummary();
            }}
        }}
        
        function renderRowPL(row, plPanel) {{
            const tier = row.dataset.tier;
            const stakePts = parseFloat(row.dataset.stakePts) || 0;
            const betType = row.dataset.betType || '';
            const isSP = (plMode === 'sp');
            if (isSP && row.dataset.spPl === undefined) return;
            if (!isSP && row.dataset.normalPl === undefined) return;
            
            const totalPL = parseFloat(isSP ? row.dataset.spPl : row.dataset.normalPl);
            const plDetails = isSP ? row.dataset.spDetails : row.dataset.normalDetails;
            
            const plColor = totalPL >= 0 ? '#00f5a0' : '#ef4444';
            const plSign = totalPL >= 0 ? '+' : '-';
            plPanel.innerHTML = '<div style="margin-top:6px; padding:8px 14px; background:' + plColor + '12; border:1px solid ' + plColor + '35; border-radius:10px; display:inline-flex; align-items:center; gap:10px;">'
                + '<span style="font-size:0.75rem; color:#94a3b8;">' + tier + ' ' + betType + ' ' + stakePts + 'pt:</span>'
                + '<span style="font-size:1.1rem; font-weight:900; color:' + plColor + ';">' + plSign + '\xA3' + Math.abs(totalPL).toFixed(2) + '</span>'
                + '<span style="font-size:0.72rem; color:#94a3b8;">' + plDetails + '</span>'
                + '</div>';
            plPanel.style.display = 'block';
        }}
        
        function renderDayPLSummary() {{
            let totalDayPL = 0; let totalBetsCount = 0; let totalWinsCount = 0; let totalStakedAmt = 0; let totalPlacesCount = 0;
            document.querySelectorAll('.runner-row[data-tier]').forEach(r => {{
                const sp = parseFloat(r.dataset.stakePts) || 0;
                const pv = parseFloat(r.dataset.ptValue) || 1;
                const tier = r.dataset.tier;
                if (tier && tier !== 'PASS' && sp > 0) {{
                    const isSP = (plMode === 'sp');
                    const plData = isSP ? r.dataset.spPl : r.dataset.normalPl;
                    const detailsStr = isSP ? r.dataset.spDetails : r.dataset.normalDetails;
                    if (plData !== undefined) {{
                        totalBetsCount++; totalStakedAmt += sp * pv;
                        totalDayPL += parseFloat(plData);
                        if (detailsStr.includes('\u2714')) {{
                            if (detailsStr.includes('Placed')) totalPlacesCount++;
                            else totalWinsCount++;
                        }}
                    }}
                }}
            }});
            
            if (totalBetsCount > 0) {{
                let summaryDiv = document.getElementById('pl-summary');
                if (!summaryDiv) {{
                    summaryDiv = document.createElement('div');
                    summaryDiv.id = 'pl-summary';
                    const raceArea = document.querySelector('.race-block');
                    if (raceArea && raceArea.parentElement) raceArea.parentElement.insertBefore(summaryDiv, raceArea);
                }}
                const plColor = totalDayPL >= 0 ? '#00f5a0' : '#ef4444';
                const plSign = totalDayPL >= 0 ? '+' : '-';
                const roi = totalStakedAmt > 0 ? ((totalDayPL / totalStakedAmt) * 100).toFixed(1) : '0.0';
                
                let html = '<div style="position:relative; padding:16px 24px; background:linear-gradient(135deg, ' + plColor + '08, ' + plColor + '15); border:2px solid ' + plColor + '40; border-radius:14px; text-align:center; margin:16px 0;">';
                html += '<button onclick="togglePLMode()" style="position:absolute; top:12px; right:16px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.2); color:#fff; border-radius:6px; padding:4px 10px; font-size:0.75rem; cursor:pointer; font-weight:700;">🔄 ' + (plMode === 'sp' ? 'SP Odds' : 'Normal Odds') + '</button>';
                html += '<div style="font-size:0.85rem; color:#94a3b8; margin-bottom:6px;">💰 Day P/L Summary (' + totalBetsCount + ' bets, ' + totalWinsCount + ' winners, \xA3' + totalStakedAmt.toFixed(0) + ' staked)</div>'
                    + '<div style="font-size:2rem; font-weight:900; color:' + plColor + ';">' + plSign + '\xA3' + Math.abs(totalDayPL).toFixed(2) + '</div>'
                    + '<div style="font-size:0.9rem; color:' + plColor + '; margin-top:4px;">ROI: ' + roi + '%</div>'
                    + '</div>';
                summaryDiv.innerHTML = html;
                summaryDiv.style.display = 'block';
            }}
        }}

        function showPLSummary() {{
            const modal = document.getElementById('pl-modal');
            const content = document.getElementById('pl-content');
            const rows = document.querySelectorAll('.runner-row[data-tier]');
            let bets = [];
            let totalPL = 0; let totalStaked = 0; let wins = 0; let places = 0;
            const isSP = (plMode === 'sp');
            
            rows.forEach(r => {{
                const tier = r.dataset.tier;
                if (!tier || tier === 'PASS') return;
                const sp = parseFloat(r.dataset.stakePts) || 0;
                const pv = parseFloat(r.dataset.ptValue) || 1;
                const bt = r.dataset.betType || '';
                const horse = r.dataset.horse || '?';
                
                const plData = isSP ? r.dataset.spPl : r.dataset.normalPl;
                const detailsStr = isSP ? r.dataset.spDetails : r.dataset.normalDetails;
                
                if (plData !== undefined && sp > 0) {{
                    const stakeGbp = sp * pv;
                    const pl = parseFloat(plData);
                    totalStaked += stakeGbp;
                    totalPL += pl;
                    
                    let status = '\u23F3 Pending'; let statusColor = '#94a3b8';
                    if (detailsStr.includes('\u2714')) {{
                        if (detailsStr.includes('Placed')) {{ places++; status = '\u2705 Placed'; statusColor = '#00d2ff'; }}
                        else {{ wins++; status = '\u2705 Won'; statusColor = '#00f5a0'; }}
                    }} else if (detailsStr.includes('\u2718')) {{
                        status = '\u274C Lost'; statusColor = '#ef4444';
                    }}
                    
                    const raceBlock = r.closest('.race-block');
                    let raceTime = '';
                    if (raceBlock) {{
                        const h3 = raceBlock.querySelector('.race-header h3');
                        if (h3) raceTime = h3.textContent.trim();
                    }}
                    bets.push({{ horse, tier, bt, sp, stakeGbp, pl, status, statusColor, raceTime }});
                }}
            }});
            
            if (bets.length === 0) {{
                content.innerHTML = '<div style="color:#94a3b8;text-align:center;padding:20px;">No qualifying bets found for today.<br><br>Bets appear once races have qualifying selections.</div>';
            }} else {{
                const plColor = totalPL >= 0 ? '#00f5a0' : '#ef4444';
                const plSign = totalPL >= 0 ? '+' : '-';
                const roi = totalStaked > 0 ? ((totalPL / totalStaked) * 100).toFixed(1) : '0.0';
                let html = '<div style="position:relative; text-align:center;margin-bottom:16px;padding:12px;background:' + plColor + '10;border:1px solid ' + plColor + '30;border-radius:12px;">';
                html += '<button onclick="togglePLMode()" style="position:absolute; top:8px; right:12px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.2); color:#fff; border-radius:6px; padding:4px 8px; font-size:0.7rem; cursor:pointer; font-weight:700;">🔄 ' + (isSP ? 'SP' : 'Normal') + '</button>';
                html += '<div style="font-size:2rem;font-weight:900;color:' + plColor + ';">' + plSign + '\xA3' + Math.abs(totalPL).toFixed(2) + '</div>'
                    + '<div style="font-size:0.85rem;color:#94a3b8;margin-top:4px;">' + bets.length + ' bets \u2022 ' + wins + ' winners \u2022 ' + places + ' placed \u2022 \xA3' + totalStaked.toFixed(0) + ' staked \u2022 ROI: ' + roi + '%</div>'
                    + '</div>';
                html += '<table style="width:100%;border-collapse:collapse;font-size:0.82rem;">';
                html += '<tr style="color:#64748b;text-align:left;border-bottom:1px solid rgba(255,255,255,0.1);"><th style="padding:6px;">Time</th><th>Horse</th><th>Type</th><th>Stake</th><th>P/L</th><th>Status</th></tr>';
                bets.forEach(b => {{
                    const rowPLColor = b.pl >= 0 ? '#00f5a0' : '#ef4444';
                    const rowPLSign = b.pl >= 0 ? '+' : '';
                    const safeHorse = b.horse.replace(/'/g, "&quot;");
                    html += '<tr style="border-bottom:1px solid rgba(255,255,255,0.05); cursor:pointer; transition:background 0.2s;" onclick="scrollToHorse(&quot;' + safeHorse + '&quot;)" onmouseover="this.style.background=&quot;rgba(255,255,255,0.05)&quot;" onmouseout="this.style.background=&quot;&quot;">';
                    html += '<td style="padding:6px;color:#94a3b8;">' + b.raceTime + '</td>';
                    html += '<td style="padding:6px;color:#e2e8f0;font-weight:600;">' + b.horse + '</td>';
                    html += '<td style="padding:6px;color:#8b5cf6;">' + b.tier + ' ' + b.bt + '</td>';
                    html += '<td style="padding:6px;color:#94a3b8;">\xA3' + b.stakeGbp.toFixed(0) + '</td>';
                    html += '<td style="padding:6px;color:' + rowPLColor + ';font-weight:700;">' + rowPLSign + '\xA3' + Math.abs(b.pl).toFixed(2) + '</td>';
                    html += '<td style="padding:6px;color:' + b.statusColor + ';">' + b.status + '</td>';
                    html += '</tr>';
                }});
                html += '</table>';
                content.innerHTML = html;
            }}
            modal.classList.add('show');
        }}

        async function checkResults(autoLoadOnly = false) {{
            if (resultsChecked && !autoLoadOnly) return;
            const btn = document.querySelector('.btn-check');
            const originalText = btn.textContent;
            
            // Try loading from cache first if autoLoadOnly
            const cacheKey = 'v12_results_' + REPORT_DATE;
            let cachedData = {{}};
            try {{
                const stored = localStorage.getItem(cacheKey);
                if (stored) cachedData = JSON.parse(stored);
            }} catch(e) {{}}

            if (autoLoadOnly) {{
                if (Object.keys(cachedData).length > 0) {{
                    updatePageWithResults(cachedData);
                    btn.textContent = `\u2705 Cached (${{Object.keys(cachedData).length}})`;
                    btn.style.background = 'linear-gradient(135deg, #00f5a0, #00d2ff)';
                    btn.style.color = '#000';
                    resultsChecked = true;
                }}
                return;
            }}
            
            btn.textContent = '\u23F3 Loading...';
            btn.style.opacity = '0.7';
            btn.style.pointerEvents = 'none';
            
            try {{
                // Try cached results first (from CSV), then live scraping as fallback
                let response = await fetch(`${{API_BASE}}/api/cached/${{REPORT_DATE}}`);
                let data = null;
                if (response.ok) {{
                    data = await response.json();
                    if (!data.success || !data.results || Object.keys(data.results).length === 0) {{
                        data = null;
                    }}
                }}
                if (!data) {{
                    response = await fetch(`${{API_BASE}}/api/results/${{REPORT_DATE}}`);
                    if (!response.ok) throw new Error(`Server returned ${{response.status}}`);
                    data = await response.json();
                }}
                
                if (data.success && data.results) {{
                    // Merge fetched results into cached results
                    const mergedResults = {{ ...cachedData, ...data.results }};
                    
                    // Save merged back to cache
                    localStorage.setItem(cacheKey, JSON.stringify(mergedResults));
                    
                    // Update page
                    updatePageWithResults(mergedResults);
                    
                    btn.textContent = `\u2705 ${{Object.keys(mergedResults).length}} horses`;
                    btn.style.background = 'linear-gradient(135deg, #00f5a0, #00d2ff)';
                    btn.style.color = '#000';
                    resultsChecked = true;
                }} else {{
                    throw new Error(data.error || 'No results');
                }}
                
            }} catch (err) {{
                console.error('Results error:', err);
                btn.textContent = '\u274C Offline';
                btn.style.background = '#ef4444';
                alert('Could not fetch new results from server.');
            }}
            
            btn.style.opacity = '1';
            setTimeout(() => {{
                if (!resultsChecked) {{
                    btn.textContent = originalText;
                    btn.style.background = '';
                }}
                btn.style.pointerEvents = 'auto';
            }}, 3000);
        }}

        function normalizeHorseName(name) {{
            if (!name) return '';
            return name.toLowerCase().trim().replace(/\s*\([a-z]+\)$/i, '').replace(/[^a-z0-9]/gi, '').toLowerCase();
        }}

        function updatePageWithResults(results) {{
            const rows = document.querySelectorAll('.runner-row[data-horse]');
            let updated = 0;
            
            rows.forEach(row => {{
                const horseName = row.getAttribute('data-horse');
                const normName = normalizeHorseName(horseName);
                const match = results[normName] || results[horseName];
                
                if (horseName && match) {{
                    const pos = match.pos;
                    const spOdds = match.dec || 0;
                    const rankCell = row.querySelector('.circ-rank');
                    const oddsCell = row.querySelector('.odds-val');
                    const nameEl = row.querySelector('.name-col h4');
                    
                    // Make rank circle bigger
                    if (rankCell) {{
                        rankCell.style.width = '44px';
                        rankCell.style.height = '44px';
                        rankCell.style.fontSize = '1.2rem';
                        let posDisplay = '';
                        if (pos === 1) {{
                            posDisplay = '🥇';
                            rankCell.style.fontSize = '1.5rem';
                            rankCell.style.background = 'linear-gradient(135deg, #facc15, #eab308)';
                            rankCell.style.color = '#000';
                            rankCell.style.boxShadow = '0 0 20px rgba(250,204,21,0.6), 0 0 40px rgba(250,204,21,0.2)';
                            row.style.background = 'linear-gradient(90deg, rgba(250,204,21,0.15), rgba(250,204,21,0.05))';
                            row.style.border = '2px solid rgba(250,204,21,0.4)';
                            row.style.borderRadius = '14px';
                            row.style.animation = 'winnerPulse 2s ease-in-out infinite';
                        }} else if (pos === 2) {{
                            posDisplay = '🥈';
                            rankCell.style.fontSize = '1.4rem';
                            rankCell.style.background = 'linear-gradient(135deg, #94a3b8, #e2e8f0)';
                            rankCell.style.color = '#000';
                            rankCell.style.boxShadow = '0 0 12px rgba(148,163,184,0.4)';
                            row.style.background = 'rgba(148,163,184,0.08)';
                            row.style.border = '1px solid rgba(148,163,184,0.25)';
                            row.style.borderRadius = '14px';
                        }} else if (pos === 3) {{
                            posDisplay = '🥉';
                            rankCell.style.fontSize = '1.4rem';
                            rankCell.style.background = 'linear-gradient(135deg, #b45309, #f59e0b)';
                            rankCell.style.color = '#fff';
                            rankCell.style.boxShadow = '0 0 12px rgba(180,83,9,0.4)';
                            row.style.background = 'rgba(180,83,9,0.08)';
                            row.style.border = '1px solid rgba(180,83,9,0.25)';
                            row.style.borderRadius = '14px';
                        }} else if (pos > 0 && pos <= 6) {{
                            posDisplay = pos;
                            rankCell.style.background = 'rgba(255,255,255,0.08)';
                            rankCell.style.color = '#94a3b8';
                            row.style.opacity = '0.65';
                        }} else {{
                            posDisplay = pos > 0 ? pos : '-';
                            row.style.opacity = '0.35';
                        }}
                        rankCell.innerHTML = posDisplay;
                    }}
                    
                    // Add bold position badge next to horse name
                    if (nameEl && pos > 0) {{
                        let badgeColor = '#64748b'; let badgeBg = 'rgba(100,116,139,0.15)';
                        let label = pos + 'th';
                        if (pos === 1) {{ badgeColor = '#facc15'; badgeBg = 'rgba(250,204,21,0.2)'; label = '1st \u2714'; }}
                        else if (pos === 2) {{ badgeColor = '#cbd5e1'; badgeBg = 'rgba(203,213,225,0.15)'; label = '2nd'; }}
                        else if (pos === 3) {{ badgeColor = '#f59e0b'; badgeBg = 'rgba(245,158,11,0.15)'; label = '3rd'; }}
                        nameEl.innerHTML += ` <span style="display:inline-block; padding:3px 10px; border-radius:6px; font-size:0.8rem; font-weight:900; background:${{badgeBg}}; color:${{badgeColor}}; border:1px solid ${{badgeColor}}40; margin-left:8px; vertical-align:middle;">${{label}}</span>`;
                    }}
                    
                    // Show SP odds prominently
                    if (spOdds > 0 && oddsCell) {{
                        oddsCell.innerHTML += `<div style="margin-top:4px; padding:3px 8px; background:rgba(0,245,160,0.1); border:1px solid rgba(0,245,160,0.3); border-radius:6px; display:inline-block;"><span style="font-size:0.7rem; color:#94a3b8;">SP</span> <span style="font-size:0.9rem; font-weight:800; color:#00f5a0;">${{spOdds.toFixed(2)}}</span></div>`;
                    }}
                    
                    // -- P/L Calculation --
                    const tier = row.dataset.tier;
                    const stakePts = parseFloat(row.dataset.stakePts) || 0;
                    const betType = row.dataset.betType || '';
                    const winOddsData = parseFloat(row.dataset.winOdds) || 0;
                    const ewOddsData = parseFloat(row.dataset.ewOdds) || 0;
                    const ptValue = parseFloat(row.dataset.ptValue) || 1;
                    const commissionRate = parseFloat(row.dataset.commission) || 0.05;
                    const ewDivisorVal = parseFloat(row.dataset.ewDivisor) || 4;
                    const ewPlacesNum = parseInt(row.dataset.ewPlaces) || parseInt(row.dataset.placeTerms) || 3;
                    
                    const normalWinOddsCalc = winOddsData > 1 ? winOddsData : (spOdds > 1 ? spOdds : 0);
                    const spWinOddsCalc = spOdds > 1 ? spOdds : normalWinOddsCalc;
                    
                    if (tier && tier !== 'PASS' && stakePts > 0) {{
                        const stakeGbp = stakePts * ptValue;
                        
                        function calcReturn(winOddsCalc, isSP) {{
                            let tPL = 0; let details = ''; 
                            if (winOddsCalc <= 1) return {{ pl: 0, details: 'waiting for odds', pending: true }};
                            
                            if (betType === 'WIN' || betType === 'DUTCH WIN') {{
                                if (pos === 1) {{
                                    tPL = stakeGbp * (winOddsCalc - 1) * (1 - commissionRate);
                                    details = 'WIN \u2714 at ' + (isSP?'SP ':'') + winOddsCalc.toFixed(2);
                                }} else {{
                                    tPL = -stakeGbp;
                                    details = 'WIN \u2718 lost';
                                }}
                            }} else if (betType === 'E/W') {{
                                const halfStake = stakeGbp / 2;
                                let ewWinOdds = (isSP || ewOddsData <= 1) ? winOddsCalc : ewOddsData;
                                const placeOddsCalc = 1 + (ewWinOdds - 1) / ewDivisorVal;
                                let winPL = -halfStake;
                                let placePL = -halfStake;
                                
                                if (pos === 1) {{
                                    winPL = halfStake * (ewWinOdds - 1) * (1 - commissionRate);
                                    placePL = halfStake * (placeOddsCalc - 1) * (1 - commissionRate);
                                    details = 'E/W WIN+PLACE \u2714 at ' + (isSP?'SP ':'') + ewWinOdds.toFixed(2);
                                }} else if (pos > 0 && pos <= ewPlacesNum) {{
                                    placePL = halfStake * (placeOddsCalc - 1) * (1 - commissionRate);
                                    details = 'E/W Placed ' + pos + (pos===2?'nd':pos===3?'rd':'th') + ' \u2714';
                                }} else {{
                                    details = 'E/W \u2718 not placed';
                                }}
                                tPL = winPL + placePL;
                            }}
                            return {{ pl: tPL, details, pending: false }};
                        }}
                        
                        // Wait to set attributes until the row has both calculations
                        const normRes = calcReturn(normalWinOddsCalc, false);
                        const spRes = calcReturn(spWinOddsCalc, true);
                        if (!normRes.pending) row.dataset.normalPl = normRes.pl.toFixed(2);
                        if (!normRes.pending) row.dataset.normalDetails = normRes.details;
                        if (!spRes.pending) row.dataset.spPl = spRes.pl.toFixed(2);
                        if (!spRes.pending) row.dataset.spDetails = spRes.details;
                        
                        const plPanel = row.querySelector('.pl-panel');
                        if (plPanel && !normRes.pending) {{
                            renderRowPL(row, plPanel);
                        }}
                    }}

                    updated++;
                }}
            }});
            
            renderDayPLSummary();

            // Inject winner pulse animation
            if (!document.getElementById('results-animations')) {{
                const style = document.createElement('style');
                style.id = 'results-animations';
                style.textContent = '@keyframes winnerPulse {{ 0%,100% {{ box-shadow: 0 0 10px rgba(250,204,21,0.1); }} 50% {{ box-shadow: 0 0 25px rgba(250,204,21,0.25); }} }}';
                document.head.appendChild(style);
            }}
            console.log(`Updated ${{updated}} horses with results.`);
        }}

        // --- Auto-load cached results on page load ---
        document.addEventListener('DOMContentLoaded', () => {{
            checkResults(true); 
        }});
    </script>
</body>
</html>'''

    # Inject Magic Hand annotation tool as separate script
    mh_js_path = Path(__file__).parent / 'magic_hand.js'
    if mh_js_path.exists():
        mh_js = mh_js_path.read_text(encoding='utf-8')
        html = html.replace('</body>', f'<script>\n{mh_js}\n</script>\n</body>')

    out_file = OUTPUT_DIR / f'tips_{date_str}.html'
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html)
    generate_mobile_html(races, predictions_by_race, date_str, live_odds)
    return out_file

def main():
    date_str_arg = None
    args = sys.argv[1:]
    if args:
        if args[0] in ['-Date', '-d'] and len(args) > 1:
            date_str_arg = args[1]
    
    json_files = sorted(RACECARDS_DIR.glob('*_all.json'), reverse=True)
    if not json_files:
        print("[ERROR] No racecards found.")
        return
        
    available_dates = []
    for f in json_files:
        m = re.match(r'(\d{4}-\d{2}-\d{2})', f.name)
        if m: available_dates.append(m.group(1))
    
    available_dates = list(dict.fromkeys(available_dates))
    
    target_dates = []
    if date_str_arg:
        target_dates = [date_str_arg]
    else:
        target_dates = available_dates[:10]
        
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    print(f"Targeting {len(target_dates)} dates for Tipster generation.")
    
    model, calibrator, feature_list = load_v11_artifacts()
    bankroll_cfg = load_bankroll_settings()
    save_bankroll_settings(bankroll_cfg)  # Ensure file exists with defaults
    print(f"  Bankroll: £{bankroll_cfg['bankroll']:.0f} | 1pt = £{bankroll_cfg['point_value']:.0f} | Commission: {bankroll_cfg['commission']*100:.1f}%")
    last_desktop_path = None
    
    for date_str in target_dates:
        print(f"\n--- Processing {date_str} ---")
        json_path = RACECARDS_DIR / f"{date_str}_all.json"
        if not json_path.exists():
            print(f"  [WARN] No racecards found at {json_path}")
            continue
            
        races, loaded_date = load_racecards(json_path)
        print(f"  Loaded {len(races)} races.")
        
        live_odds = load_live_odds(date_str)
        print(f"  Loaded live odds for {len(live_odds)} horses.")
        
        df_inf = prepare_v11_features(races, feature_list)
        if len(df_inf) == 0:
            print("  No valid runners found.")
            continue
            
        raw_probs = model.predict_proba(df_inf[feature_list])[:, 1]
        df_inf['calib_prob'] = calibrator.predict(raw_probs)
        
        predictions_by_race = {}
        for race in races:
            race_key = f"{race['course']}_{race['off_time']}"
            r_id = f"test_{str(race['course']).lower()}_{race['off_time']}"
            
            race_df = df_inf[df_inf['race_id'] == r_id]
            if len(race_df) == 0: continue
            
            preds = []
            for _, row in race_df.iterrows():
                prob = row['calib_prob']
                h_name = row['horse_name']
                orig_runner = next((r for r in race['runners'] if r['name'] == h_name), None)
                if orig_runner:
                    preds.append({'horse': h_name, 'prob': prob, 'full_data': orig_runner})
                    
            preds.sort(key=lambda x: x['prob'], reverse=True)
            predictions_by_race[race_key] = preds
            
        print("  Generating desktop HTML...")
        out_path = generate_premium_html(races, predictions_by_race, loaded_date, live_odds, available_dates[:10], bankroll_cfg)
        if not last_desktop_path: last_desktop_path = out_path
        
        if date_str >= current_date_str:
            print("  Generating mobile HTML...")
            generate_mobile_html(races, predictions_by_race, date_str, live_odds)
            
    if last_desktop_path:
        print(f"\n[SUCCESS] Custom Tipster V12 Premium Interface Generated!")
        webbrowser.open(f"file://{last_desktop_path.absolute()}")

if __name__ == '__main__':
    main()
