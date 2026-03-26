import os, re, json, math
from pathlib import Path
from datetime import datetime
from fractions import Fraction

BASE_DIR = Path(__file__).resolve().parent.parent
MOBILE_OUTPUT_DIR = BASE_DIR / "docs"

def _fmt_odds(decimal_odds):
    """Return HTML with both decimal and fractional odds as togglable spans."""
    if not decimal_odds or decimal_odds <= 1: return "-"
    dec_str = f'{decimal_odds:.2f}'
    frac_str = 'Evs' if decimal_odds == 2.0 else f'{Fraction(decimal_odds - 1).limit_denominator(100)}'
    return f'<span class="od">{dec_str}</span><span class="of">{frac_str}</span>'

def _normalize(name):
    if not isinstance(name, str): return ""
    return re.sub(r'[^a-z0-9]', '', re.sub(r'\s*\([a-z]+\)$', '', name.lower().strip(), flags=re.IGNORECASE))

def _get_odds(horse, live_odds):
    if not live_odds or not horse: return None
    n = _normalize(horse)
    if n in live_odds: return live_odds[n]
    for k, v in live_odds.items():
        if n in k or k in n: return v
    return None

def _classify(prob, odds, rank=1, n=10):
    if not odds or odds <= 1.01: return 'PASS', 0, 0, 'WIN'
    implied = 1.0 / odds; edge = (prob - implied) * 100
    if rank != 1 or odds < 2.0 or odds > 50.0 or n > 14 or n < 4: return 'PASS', edge, 0, 'WIN'
    conf = 50
    if 6 <= odds <= 20: conf += 20
    elif 3 <= odds <= 6: conf += 10
    elif 2 <= odds <= 3: conf += 5
    elif odds > 20: conf -= 10
    if 7 <= n <= 10: conf += 15
    elif n <= 6: conf += 5
    if prob > 0.14: conf += 10
    elif prob > 0.12: conf += 5
    if conf >= 75: tier, sp = 'STRONG', 2.0
    elif conf >= 60: tier, sp = 'GOOD', 1.5
    else: tier, sp = 'FAIR', 1.0
    bt = 'E/W' if odds >= 8 and n >= 8 else 'WIN'
    if bt == 'E/W': sp *= 0.8
    return tier, edge, round(sp, 1), bt

def _insights(horse, all_runners, race):
    ins = []
    def sn(v):
        try: return float(v) if v else 0
        except: return 0
    h_ofr = sn(horse.get('ofr'))
    field = [sn(r.get('ofr')) for r in all_runners if sn(r.get('ofr')) > 0]
    if h_ofr > 0 and field and h_ofr == max(field): ins.append('👑 Class Leader')
    form = str(horse.get('form', ''))
    if '1' in form[-2:]: ins.append('🔥 Recent Winner')
    stats = horse.get('stats', {}) or {}
    cs = stats.get('course', {}) or {}
    if sn(cs.get('wins')) > 0: ins.append('📍 Course Specialist')
    lr = sn(horse.get('last_run'))
    if lr >= 100: ins.append(f'⏳ {int(lr)}d Layoff')
    return ins[:3]

def _forecast_tricast(preds, live_odds):
    if len(preds) < 3: return None
    t3 = sum(p['prob'] for p in preds[:3])
    if t3 < 0.35: return None
    r = {'forecast': {'first': preds[0]['horse'], 'second': preds[1]['horse'], 'stake': 0.5, 'conf': t3*100}, 'tricast': None}
    if t3 >= 0.45:
        r['tricast'] = {'horses': [p['horse'] for p in preds[:3]], 'stake': 0.2, 'conf': t3*100}
    return r

def generate_mobile_html(races, predictions_by_race, date_str, live_odds):
    MOBILE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build bankroll config
    try:
        from tipster_v12_premium import load_bankroll_settings
        bcfg = load_bankroll_settings()
    except:
        bcfg = {'bankroll': 1000.0, 'point_value': 1.0, 'commission': 0.05}
    pt = bcfg['point_value']

    # Group by course
    courses = {}
    for race in races:
        c = race['course']
        if c not in courses: courses[c] = {'going': race.get('going', ''), 'races': []}
        courses[c]['races'].append(race)

    # Collect all bets and categorize
    all_bets, bankers, values, punts, big_payouts = [], [], [], [], []
    for race in races:
        rk = f"{race['course']}_{race['off_time']}"
        preds = predictions_by_race.get(rk, [])
        if not preds: continue
        p = preds[0]
        ho = _get_odds(p['horse'], live_odds)
        dec = ho.get('best_decimal') if ho else None
        if not dec or dec <= 1.01: continue
        tier, edge, sp, bt = _classify(p['prob'], dec, 1, len(race['runners']))
        if tier == 'PASS' or sp <= 0: continue
        b = {'horse': p['horse'], 'prob': p['prob'], 'odds': dec, 'edge': edge, 'tier': tier,
             'bt': bt, 'sp': sp, 'stake': round(sp*pt, 2), 'time': race['off_time'], 'course': race['course']}
        all_bets.append(b)
        if tier == 'STRONG': bankers.append(b)
        elif tier == 'GOOD': values.append(b)
        elif tier == 'FAIR': punts.append(b)
        fc = _forecast_tricast(preds, live_odds)
        if fc: fc['time'] = race['off_time']; fc['course'] = race['course']; big_payouts.append(fc)

    all_bets.sort(key=lambda x: x['edge'], reverse=True)
    top_bets = all_bets[:6]
    total_risk = sum(b['stake'] for b in top_bets)

    # Today's Bets cards
    bets_html = ""
    for b in top_bets:
        od = _fmt_odds(b['odds'])
        ec = '#00f5a0' if b['edge'] > 5 else '#00f2fe' if b['edge'] > 3 else '#f093fb'
        tc = {'STRONG': '#00f5a0', 'GOOD': '#00f2fe', 'FAIR': '#f093fb'}.get(b['tier'], '#4b5563')
        bets_html += f'''<div class="bet-card">
<div class="bc-top"><span class="bc-time">{b['time']}</span><span class="bc-course">{b['course']}</span><span class="type-chip tc-{b['bt'].replace('/','').lower()}">{b['bt']}</span></div>
<div class="bc-horse">{b['horse']}</div>
<div class="bc-row"><span class="bc-odds">{od}</span><span class="bc-edge" style="color:{ec}">+{b['edge']:.1f}%</span><span class="bc-stake" style="color:{tc}">{b['sp']}pt £{b['stake']:.0f}</span></div>
</div>'''

    # Category cards
    def cat_cards(items, msg):
        if not items: return f'<div class="cat-empty">{msg}</div>'
        h = ''
        for b in items[:3]:
            od = _fmt_odds(b['odds'])
            h += f'<div class="cc"><div class="cc-t"><span>{b["time"]} {b["course"]}</span><span class="type-chip tc-{b["bt"].replace("/","").lower()}">{b["bt"]}</span></div><div class="cc-h">{b["horse"]}</div><div class="cc-b"><span class="cc-o">{od}</span><span class="cc-e">+{b["edge"]:.1f}%</span><span class="cc-s">{b["sp"]}pt</span></div></div>'
        return h

    # Big Payout cards
    bp_html = ""
    for bp in big_payouts[:4]:
        fc = bp['forecast']
        bp_html += f'<div class="bp-card"><div class="bp-h">{bp["time"]} {bp["course"]} <span class="bp-c">{fc["conf"]:.0f}%</span></div><div class="bp-r">📊 {fc["first"]} → {fc["second"]} <span class="bp-s">{fc["stake"]}pt</span></div>'
        if bp.get('tricast'):
            tc = bp['tricast']
            bp_html += f'<div class="bp-r">🎰 {" / ".join(tc["horses"])} <span class="bp-s">{tc["stake"]}pt</span></div>'
        bp_html += '</div>'

    # Course nav pills
    nav_pills = ''.join(f'<a href="#{re.sub(r"[^a-zA-Z0-9]","",c)}" class="m-pill">{c}</a>' for c in courses)

    # Race + runner cards
    course_html = ""
    for cn, cd in courses.items():
        cid = re.sub(r'[^a-zA-Z0-9]', '', cn)
        race_rows = ""
        for race in cd['races']:
            rk = f"{cn}_{race['off_time']}"
            rid = f"{cid}_{race['off_time'].replace(':','')}"
            preds = predictions_by_race.get(rk, [])
            if not preds: continue
            tp = preds[0]
            tp_pct = f"{tp['prob']*100:.0f}%"
            gap = (tp['prob'] - preds[1]['prob'])*100 if len(preds) > 1 else 0
            badge = f'<span class="r-tag gold">⭐ +{gap:.0f}%</span>' if gap >= 15 else f'<span class="r-tag green">⚡ DOM</span>' if gap >= 8 else ''
            
            runners_html = ""
            nr = len(race['runners'])
            for i, p in enumerate(preds):
                prob_pct = p['prob'] * 100
                hn = p['horse']
                ho = _get_odds(hn, live_odds) if live_odds else None
                ao = ho.get('best_decimal') if ho else None
                po = ho.get('place_decimal') if ho else None
                pt_val = ho.get('place_terms') if ho else None
                ewo = ho.get('ew_decimal') if ho else None
                ewd = ho.get('ew_divisor') if ho else None
                ewp = ho.get('ew_places') if ho else None
                od = _fmt_odds(ao)
                tier, edge, spts, bt = _classify(p['prob'], ao, i+1, nr)
                tc = {'STRONG': '#00f5a0', 'GOOD': '#00f2fe', 'FAIR': '#f093fb', 'PASS': '#4b5563'}[tier]
                tl = f'{tier} {bt}' if tier != 'PASS' else 'PASS'
                fd = p.get('full_data', {})
                form = str(fd.get('form', '-'))[:6]
                jockey = str(fd.get('jockey', 'U/K'))[:15]
                orating = fd.get('ofr', '-')
                ins = _insights(fd, [pp.get('full_data', {}) for pp in preds], race)
                ins_html = ''.join(f'<span class="ib">{x}</span>' for x in ins)
                
                # Sub-odds
                sub = ''
                if po and pt_val: sub += f'<div class="sub-o" style="color:#00f2fe">📍 {po:.2f} ({pt_val}pl)</div>'
                if ewo and ewp:
                    edl = f'1/{int(ewd)}' if ewd else ''
                    sub += f'<div class="sub-o" style="color:#f093fb">🎰 E/W {ewo:.2f} ({edl} {ewp}pl)</div>'
                
                # Stake
                stake_html = ''
                if tier != 'PASS' and spts > 0:
                    sg = spts * bcfg['point_value']
                    stake_html = f'<div class="m-stake" style="color:{tc}">💰 {spts}pt (£{sg:.0f})</div>'

                # Stats JSON for expand
                stats_obj = fd.get('stats', {}) or {}
                sj = json.dumps({
                    'sire': fd.get('sire','-'), 'draw': fd.get('draw','-'), 'headgear': fd.get('headgear',''),
                    'lbs': fd.get('lbs','-'), 'ofr': fd.get('ofr','-'), 'rpr': fd.get('rpr','-'),
                    'ts': fd.get('ts','-'), 'jockey': fd.get('jockey','-'), 'last_run': fd.get('last_run','-'),
                    'form': fd.get('form','-'), 'trainer_rtf': fd.get('trainer_rtf','-'),
                    'course': stats_obj.get('course',{}), 'distance': stats_obj.get('distance',{}),
                    'going': stats_obj.get('going',{}), 'jockey_stats': stats_obj.get('jockey',{}),
                    'trainer_stats': stats_obj.get('trainer',{}),
                }, default=str).replace("'", "&#39;").replace('"', '&quot;')

                extra_cls = ' runner-extra' if i >= 6 else ''
                top_cls = ' top-runner' if i == 0 else ''
                circ_style = 'background:linear-gradient(135deg,#facc15,#eab308);color:#000;' if i == 0 else ''
                
                runners_html += f'''<div class="m-row{top_cls}{extra_cls}" data-horse="{hn}" data-stats="{sj}" data-prob="{p['prob']:.6f}" data-runners="{nr}" onclick="toggleStats(this)">
<div class="m-rank"><div class="m-circ" style="{circ_style}">{i+1}</div></div>
<div class="m-info"><div class="m-name">{hn}</div><div class="m-meta">{jockey} · OR:{orating} · {form}</div><div class="m-ins">{ins_html}</div></div>
<div class="m-right"><div class="m-odds">{od}</div>{sub}<div class="m-chip" style="background:{tc}15;color:{tc};border-color:{tc}40">{tl}</div>{stake_html}<div class="m-prob" style="color:{tc}">{prob_pct:.1f}%</div><div class="m-bar"><div class="m-fill" style="width:{prob_pct}%;background:{tc}"></div></div></div>
<div class="m-stats-panel"></div>
</div>'''

            show_more = f'<div class="show-more" onclick="toggleExtra(this)">▼ Show all {len(preds)} runners</div>' if len(preds) > 6 else ''
            race_rows += f'''<div class="m-race collapsed" id="{rid}">
<div class="m-rh" onclick="toggleRace(this)"><div class="mh-l"><span class="mh-time">{race['off_time']}</span><span class="mh-name">{race['race_name'][:40]}</span></div>
<div class="mh-r"><span class="mh-pick">🏇 {tp['horse'][:18]} ({tp_pct})</span>{badge}<span class="r-tag">{race['distance']}</span><span class="r-tag">{nr}R</span><span class="mh-chev">▼</span></div></div>
<div class="m-rc">{runners_html}{show_more}</div></div>'''

        course_html += f'<section id="{cid}" class="m-cs"><div class="m-cb"><h2>{cn}</h2><span class="m-go">{cd["going"]}</span></div>{race_rows}</section>'

    # Next races for bottom-sheet
    try:
        import pytz
        now = datetime.now(pytz.timezone('Europe/London')).replace(tzinfo=None)
    except:
        now = datetime.now()
    upcoming = []
    for race in races:
        try:
            h, m = map(int, race['off_time'].split(':'))
            if h <= 10: h += 12
            dt = datetime.combine(now.date(), datetime.strptime(f"{h}:{m:02d}", "%H:%M").time())
            if dt > now:
                cid = re.sub(r'[^a-zA-Z0-9]', '', race['course'])
                rid = f"{cid}_{race['off_time'].replace(':','')}"
                upcoming.append((dt, race['off_time'], race['course'], rid))
        except: pass
    upcoming.sort()
    nr_html = ''.join(f'<a href="#{r[3]}" class="nr-item" onclick="openRace(\'{r[3]}\')">'
                       f'<span>{r[2]}</span><span class="nr-t">{r[1]}</span></a>' for r in upcoming) or '<p style="text-align:center;color:#94a3b8;padding:20px">Racing finished for the day.</p>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<meta name="theme-color" content="#030712">
<title>Q-Tips V12 Mobile | {date_str}</title>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#030712;--g:rgba(15,23,42,0.6);--gb:rgba(255,255,255,0.08);--t:#f8fafc;--tm:#94a3b8;--p:#00f2fe;--a:#4facfe;--s:#00f5a0;--gold:#facc15;--r:16px}}
*{{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
body{{background:var(--bg);background-image:radial-gradient(circle at top right,rgba(79,172,254,0.1),transparent 40%);color:var(--t);font-family:'Plus Jakarta Sans',sans-serif;padding-bottom:100px;overflow-x:hidden}}
h1,h2,h3,h4{{font-family:'Outfit',sans-serif}}
.top-bar{{position:fixed;top:0;width:100%;z-index:100;background:rgba(3,7,18,0.85);backdrop-filter:blur(20px);border-bottom:1px solid var(--gb);padding:12px 16px;display:flex;align-items:center;justify-content:space-between}}
.logo{{font-size:1.2rem;font-weight:900;font-family:'Outfit';background:linear-gradient(135deg,var(--p),var(--a));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.nav-r{{display:flex;gap:8px;align-items:center}}
.live-dot{{width:6px;height:6px;background:var(--s);border-radius:50%;box-shadow:0 0 8px var(--s);animation:pulse 1.5s infinite}}
@keyframes pulse{{0%{{opacity:1}}50%{{opacity:.3}}100%{{opacity:1}}}}
.btn-of{{background:rgba(255,255,255,0.08);color:var(--tm);border:1px solid var(--gb);padding:6px 12px;border-radius:10px;font-weight:600;cursor:pointer;font-size:.8rem}}
.cs{{position:fixed;top:52px;width:100%;z-index:99;background:rgba(15,23,42,0.4);backdrop-filter:blur(10px);border-bottom:1px solid var(--gb);padding:8px 16px;display:flex;gap:8px;overflow-x:auto;scrollbar-width:none}}
.cs::-webkit-scrollbar{{display:none}}
.m-pill{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.1);color:var(--tm);padding:5px 14px;border-radius:16px;text-decoration:none;font-size:.82rem;font-weight:500;white-space:nowrap}}
.m-pill:active{{background:var(--p);color:var(--bg);border-color:var(--p)}}
.mc{{max-width:100%;margin:0 auto;padding:108px 12px 20px}}
.bets-panel{{background:linear-gradient(135deg,rgba(250,204,21,0.08),rgba(0,242,254,0.05));border:1px solid rgba(250,204,21,0.25);border-radius:var(--r);margin-bottom:20px;overflow:hidden}}
.bets-hdr{{background:linear-gradient(135deg,rgba(250,204,21,0.15),rgba(0,245,160,0.08));padding:14px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid rgba(250,204,21,0.2)}}
.bets-hdr h2{{font-size:1.1rem;color:var(--gold)}}
.bets-hdr .risk{{font-size:.85rem;color:var(--tm)}}
.bets-hdr .risk strong{{color:var(--s)}}
.bet-card{{padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.03)}}
.bc-top{{display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:.8rem}}
.bc-time{{font-weight:800;font-family:'Outfit';color:white}}
.bc-course{{color:var(--tm);font-weight:500}}
.bc-horse{{font-size:1.05rem;font-weight:700;margin-bottom:6px}}
.bc-row{{display:flex;align-items:center;gap:12px;font-size:.9rem}}
.bc-odds{{font-family:'Outfit';font-weight:800}}
.bc-edge{{font-weight:800;font-family:'Outfit'}}
.bc-stake{{margin-left:auto;font-weight:700;font-size:.85rem}}
.type-chip{{padding:3px 8px;border-radius:5px;font-size:.7rem;font-weight:800;display:inline-block}}
.tc-win{{background:rgba(0,245,160,0.15);color:#00f5a0;border:1px solid rgba(0,245,160,0.3)}}
.tc-ew{{background:rgba(0,242,254,0.15);color:#00f2fe;border:1px solid rgba(0,242,254,0.3)}}
.bets-empty{{padding:20px;text-align:center;color:var(--tm);font-size:.9rem}}
.cats{{display:flex;gap:10px;overflow-x:auto;scrollbar-width:none;margin-bottom:20px;padding-bottom:6px}}
.cats::-webkit-scrollbar{{display:none}}
.cat-s{{min-width:85%;background:var(--g);border:1px solid var(--gb);border-radius:var(--r);overflow:hidden;scroll-snap-align:start}}
.cat-h{{padding:12px 16px;border-bottom:1px solid var(--gb);display:flex;align-items:center;gap:8px}}
.cat-h h3{{font-size:1rem}}
.cat-h.bk{{background:linear-gradient(135deg,rgba(0,245,160,0.1),transparent)}}
.cat-h.vl{{background:linear-gradient(135deg,rgba(0,242,254,0.1),transparent)}}
.cat-h.pt{{background:linear-gradient(135deg,rgba(240,147,251,0.1),transparent)}}
.cat-bd{{padding:10px}}
.cc{{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-radius:10px;padding:12px;margin-bottom:8px}}
.cc-t{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;font-size:.78rem;color:var(--tm)}}
.cc-h{{font-size:1rem;font-weight:700;margin-bottom:6px}}
.cc-b{{display:flex;gap:10px;align-items:center;font-size:.82rem}}
.cc-o{{font-weight:800;font-family:'Outfit'}}
.cc-e{{color:var(--p);font-weight:700}}
.cc-s{{color:var(--tm);margin-left:auto;font-weight:600}}
.cat-empty{{padding:16px;text-align:center;color:var(--tm);font-size:.85rem}}
.bp-panel{{background:var(--g);border:1px solid var(--gb);border-radius:var(--r);margin-bottom:20px;overflow:hidden}}
.bp-title{{padding:14px 16px;border-bottom:1px solid var(--gb);cursor:pointer;display:flex;align-items:center;justify-content:space-between}}
.bp-title h3{{color:#f093fb;font-size:1rem}}
.bp-body{{padding:10px}}
.bp-body.collapsed{{display:none}}
.bp-card{{background:rgba(240,147,251,0.05);border:1px solid rgba(240,147,251,0.15);border-radius:10px;padding:12px;margin-bottom:8px}}
.bp-h{{font-weight:700;font-size:.9rem;margin-bottom:6px}}
.bp-c{{color:#f093fb;font-size:.78rem;margin-left:6px}}
.bp-r{{padding:4px 0;font-size:.85rem;display:flex;align-items:center;gap:6px}}
.bp-s{{margin-left:auto;font-weight:700;color:var(--gold)}}
.bp-empty{{padding:16px;text-align:center;color:var(--tm);font-size:.85rem}}
.m-cs{{margin-bottom:24px;scroll-margin-top:100px}}
.m-cb{{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:1px solid var(--gb);padding-bottom:10px;margin-bottom:14px}}
.m-cb h2{{font-size:1.6rem;font-weight:800}}
.m-go{{color:var(--p);font-weight:700;text-transform:uppercase;letter-spacing:1px;font-size:.75rem}}
.m-race{{background:var(--g);border:1px solid var(--gb);border-radius:var(--r);margin-bottom:10px;overflow:hidden;box-shadow:0 6px 20px rgba(0,0,0,0.3)}}
.m-race.collapsed .m-rc{{display:none}}
.m-race.collapsed .mh-chev{{transform:rotate(0)}}
.m-race:not(.collapsed) .mh-chev{{transform:rotate(180deg)}}
.m-rh{{padding:14px 16px;background:rgba(30,41,59,0.4);display:flex;flex-direction:column;gap:6px;border-bottom:1px solid var(--gb);cursor:pointer}}
.mh-l{{display:flex;align-items:center;gap:10px;flex-wrap:wrap}}
.mh-time{{color:white;font-size:1.3rem;font-weight:800;font-family:'Outfit'}}
.mh-name{{color:var(--tm);font-size:.82rem;font-weight:500}}
.mh-r{{display:flex;gap:6px;align-items:center;flex-wrap:wrap}}
.mh-pick{{color:var(--gold);font-weight:700;font-size:.8rem}}
.mh-chev{{color:var(--tm);font-size:.8rem;transition:transform .3s;margin-left:auto}}
.r-tag{{padding:4px 8px;border-radius:6px;font-size:.72rem;font-weight:700;background:rgba(255,255,255,0.1);color:var(--tm)}}
.r-tag.gold{{background:rgba(250,204,21,0.2);color:var(--gold);border:1px solid rgba(250,204,21,0.4)}}
.r-tag.green{{background:rgba(0,245,160,0.2);color:var(--s);border:1px solid rgba(0,245,160,0.4)}}
.m-rc{{padding:8px}}
.m-row{{display:grid;grid-template-columns:36px 1fr 90px;align-items:center;padding:12px 8px;border-radius:10px;margin-bottom:4px;cursor:pointer;position:relative}}
.m-row:active{{background:rgba(255,255,255,0.03)}}
.top-runner{{background:linear-gradient(90deg,rgba(255,255,255,0.03),transparent)}}
.m-row.runner-extra{{display:none!important}}
.m-rc.expanded .m-row.runner-extra{{display:grid!important}}
.show-more{{text-align:center;padding:10px;color:var(--p);font-weight:700;font-size:.85rem;cursor:pointer;border-top:1px solid var(--gb)}}
.m-rank{{display:flex;justify-content:center}}
.m-circ{{width:28px;height:28px;border-radius:50%;background:rgba(255,255,255,0.1);display:flex;align-items:center;justify-content:center;font-weight:800;font-size:.85rem;color:var(--tm)}}
.m-info{{padding:0 8px}}
.m-name{{font-size:.95rem;font-weight:700;margin-bottom:2px}}
.m-meta{{font-size:.72rem;color:var(--tm);margin-bottom:4px}}
.m-ins{{display:flex;gap:4px;flex-wrap:wrap}}
.ib{{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.05);padding:2px 6px;border-radius:12px;font-size:.65rem;color:#cbd5e1}}
.m-right{{text-align:right}}
.m-odds{{font-size:.95rem;font-weight:800;margin-bottom:4px;font-family:'Outfit'}}
.sub-o{{font-size:.65rem;margin-top:1px}}
.m-chip{{display:inline-block;padding:2px 6px;border-radius:4px;font-size:.65rem;font-weight:800;border:1px solid;margin-top:2px}}
.m-stake{{font-size:.68rem;margin-top:2px;font-weight:700}}
.m-prob{{font-size:1rem;font-weight:800;font-family:'Outfit';margin-top:2px}}
.m-bar{{width:100%;height:4px;background:rgba(255,255,255,0.1);border-radius:2px;overflow:hidden;margin-top:2px}}
.m-fill{{height:100%;border-radius:2px}}
.m-stats-panel{{display:none;grid-column:1/-1;margin-top:8px;padding:10px;background:rgba(0,0,0,0.4);border:1px solid rgba(255,255,255,0.1);border-radius:10px}}
.m-row.show-stats .m-stats-panel{{display:block}}
.sp-title{{font-size:.72rem;color:var(--tm);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}}
.sp-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:8px}}
.sp-item{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:6px;padding:6px;text-align:center}}
.sp-lbl{{font-size:.6rem;color:var(--tm);font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:1px}}
.sp-val{{font-size:.95rem;font-weight:800;font-family:'Outfit'}}
.sp-2col{{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px}}
.sp-box{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:6px;padding:8px}}
.sp-box-lbl{{font-size:.65rem;color:var(--tm);font-weight:600;text-transform:uppercase;margin-bottom:3px}}
.sp-box-val{{font-weight:700;font-size:.85rem;margin-bottom:2px}}
.sp-box-sub{{font-size:.72rem;color:var(--tm)}}
.sp-rec{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-bottom:6px}}
.sp-rec-item{{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:6px;padding:6px;text-align:center}}
.sp-rec-lbl{{font-size:.6rem;color:var(--tm);font-weight:600;text-transform:uppercase;margin-bottom:2px}}
.sp-rec-val{{font-size:.85rem;font-weight:800}}
.sp-rec-bar{{height:3px;background:rgba(255,255,255,0.1);border-radius:2px;margin-top:3px;overflow:hidden}}
.sp-rec-fill{{height:100%;border-radius:2px}}
.sp-rec-sr{{font-size:.65rem;color:var(--tm);margin-top:1px}}
.of{{display:none}}
body.frac .od{{display:none}}
body.frac .of{{display:inline}}
.mo{{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.8);backdrop-filter:blur(8px);z-index:1000;display:flex;align-items:flex-end;opacity:0;pointer-events:none;transition:opacity .3s}}
.mo.active{{opacity:1;pointer-events:auto}}
.mo-c{{background:#0f172a;width:100%;max-height:80vh;border-top-left-radius:20px;border-top-right-radius:20px;border-top:1px solid var(--gb);transform:translateY(100%);transition:transform .4s cubic-bezier(.2,.8,.2,1);display:flex;flex-direction:column}}
.mo.active .mo-c{{transform:translateY(0)}}
.mo-h{{display:flex;justify-content:space-between;align-items:center;padding:16px 20px 8px;border-bottom:1px dashed var(--gb)}}
.mo-h h2{{font-family:'Outfit';font-size:1.2rem}}
.mo-x{{background:none;border:none;color:var(--tm);font-size:1.3rem;cursor:pointer}}
.mo-b{{padding:16px 20px;overflow-y:auto;padding-bottom:env(safe-area-inset-bottom)}}
.nr-item{{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:rgba(59,130,246,0.05);border-radius:10px;margin-bottom:8px;border:1px solid rgba(59,130,246,0.2);text-decoration:none;color:var(--t);font-weight:600}}
.nr-t{{font-family:'Outfit';font-size:1.1rem;color:#60A5FA}}
.pos-badge{{display:inline-block;padding:2px 8px;border-radius:5px;font-size:.7rem;font-weight:900;margin-left:6px;vertical-align:middle}}
.pos-badge.gold{{background:linear-gradient(135deg,#facc15,#eab308);color:#000;box-shadow:0 0 8px rgba(250,204,21,0.5)}}
.pos-badge.silver{{background:linear-gradient(135deg,#94a3b8,#e2e8f0);color:#000}}
.pos-badge.bronze{{background:linear-gradient(135deg,#b45309,#f59e0b);color:#fff}}
.pos-badge.unplaced{{background:transparent;color:#64748b;border:1px dashed #334155}}
.m-row.winner{{background:linear-gradient(90deg,rgba(250,204,21,0.12),rgba(250,204,21,0.04))!important;border:1px solid rgba(250,204,21,0.3);border-radius:10px}}
.m-row.placed{{background:rgba(148,163,184,0.06);border:1px solid rgba(148,163,184,0.2);border-radius:10px}}
.m-row.lost{{opacity:.45}}
.btn-res{{background:linear-gradient(135deg,#f093fb,#f5576c);color:white;border:none;padding:6px 12px;border-radius:10px;font-weight:700;cursor:pointer;font-size:.78rem;transition:all .2s}}
.res-bar{{position:fixed;bottom:60px;left:0;right:0;background:rgba(3,7,18,0.95);backdrop-filter:blur(10px);border-top:1px solid var(--gb);padding:8px 16px;display:flex;align-items:center;justify-content:center;gap:10px;z-index:100}}
.bn{{position:fixed;bottom:0;left:0;right:0;height:60px;background:rgba(3,7,18,0.95);backdrop-filter:blur(20px);border-top:1px solid rgba(255,255,255,0.05);display:flex;justify-content:space-around;align-items:center;padding-bottom:env(safe-area-inset-bottom);z-index:100}}
.bn a{{display:flex;flex-direction:column;align-items:center;gap:3px;color:var(--tm);text-decoration:none;font-size:.6rem;font-weight:600;text-transform:uppercase;opacity:.7}}
.bn a.act{{color:var(--s);opacity:1}}
.bn .ni{{font-size:1.2rem}}
</style>
</head>
<body>
<div class="top-bar">
<div class="logo">Q-TIPS V12</div>
<div class="nav-r"><div class="live-dot"></div><span style="font-size:.8rem;color:var(--tm);margin:0 6px">{date_str}</span>
<button class="btn-of" id="odds-toggle" onclick="toggleOdds()">Fractional</button></div>
</div>
<div class="cs">{nav_pills}</div>
<div class="mc">
<div class="bets-panel">
<div class="bets-hdr"><h2>TODAY'S BETS</h2><div class="risk">Risk: <strong>&pound;{total_risk:.0f}</strong> ({len(top_bets)})</div></div>
{bets_html if bets_html else '<div class="bets-empty">No qualifying bets</div>'}
</div>
<div class="cats">
<div class="cat-s"><div class="cat-h bk"><h3>STRONG</h3></div><div class="cat-bd">{cat_cards(bankers, 'No STRONG picks')}</div></div>
<div class="cat-s"><div class="cat-h vl"><h3>GOOD</h3></div><div class="cat-bd">{cat_cards(values, 'No GOOD picks')}</div></div>
<div class="cat-s"><div class="cat-h pt"><h3>FAIR</h3></div><div class="cat-bd">{cat_cards(punts, 'No FAIR picks')}</div></div>
</div>
<div class="bp-panel">
<div class="bp-title" onclick="this.nextElementSibling.classList.toggle('collapsed')"><h3>Big-Payout Plays</h3><span style="color:var(--tm)">&#9660;</span></div>
<div class="bp-body">{bp_html if bp_html else '<div class="bp-empty">No forecast/tricast plays today</div>'}</div>
</div>
{course_html}
</div>
<div class="res-bar">
<button class="btn-res" id="res-btn" onclick="checkResults()">Check Results</button>
<span id="res-status" style="font-size:.75rem;color:var(--tm)"></span>
</div>
<div class="bn">
<a href="#" class="act" onclick="document.querySelectorAll('.mo').forEach(function(m){{m.classList.remove('active')}})"><span class="ni">&#x1F4CA;</span><span>Cards</span></a>
<a href="#" onclick="openModal('nrModal')"><span class="ni">&#x23F1;</span><span>Next Off</span></a>
</div>
<div class="mo" id="nrModal"><div class="mo-c"><div class="mo-h"><h2>Next Races</h2><button class="mo-x" onclick="closeModal('nrModal')">&#x2715;</button></div><div class="mo-b">{nr_html}</div></div></div>
<script>
(function(){{if(localStorage.getItem('v12m_odds')==='frac'){{document.body.classList.add('frac');document.getElementById('odds-toggle').textContent='Decimal'}}}})();
function toggleOdds(){{var b=document.getElementById('odds-toggle');document.body.classList.toggle('frac');var f=document.body.classList.contains('frac');b.textContent=f?'Decimal':'Fractional';localStorage.setItem('v12m_odds',f?'frac':'dec')}}
function toggleRace(h){{var b=h.closest('.m-race'),w=b.classList.contains('collapsed');document.querySelectorAll('.m-race').forEach(function(r){{r.classList.add('collapsed')}});if(w){{b.classList.remove('collapsed');b.scrollIntoView({{behavior:'smooth',block:'start'}})}}}}
function toggleExtra(btn){{var c=btn.closest('.m-rc');c.classList.toggle('expanded');if(c.classList.contains('expanded'))btn.textContent='Show less';else btn.textContent='Show all runners'}}
function toggleStats(row){{if(event.target.closest('.show-more'))return;var w=row.classList.contains('show-stats');row.closest('.m-rc').querySelectorAll('.m-row.show-stats').forEach(function(r){{r.classList.remove('show-stats')}});if(w)return;var p=row.querySelector('.m-stats-panel');if(!p)return;var s;try{{s=JSON.parse(row.dataset.stats||'{{}}')}}catch(e){{return}}
var h='<div class="sp-title">Horse Profile</div><div class="sp-grid">';
var rats=[['OR',s.ofr,'#facc15'],['RPR',s.rpr,'#00f2fe'],['TS',s.ts,'#00f5a0'],['Wt',s.lbs?s.lbs+'lbs':'-','#94a3b8'],['Draw',s.draw,'#f093fb'],['Days',s.last_run,parseInt(s.last_run)>=60?'#ef4444':'#00f5a0']];
for(var i=0;i<rats.length;i++)h+='<div class="sp-item"><div class="sp-lbl">'+rats[i][0]+'</div><div class="sp-val" style="color:'+rats[i][2]+'">'+(rats[i][1]||'-')+'</div></div>';
h+='</div>';
var js=s.jockey_stats||{{}},ts2=s.trainer_stats||{{}};
h+='<div class="sp-2col"><div class="sp-box"><div class="sp-box-lbl">Jockey</div><div class="sp-box-val" style="color:white">'+s.jockey+'</div><div class="sp-box-sub">14d: '+(js.last_14_wins_pct||'-')+' | Ovr: '+(js.ovr_wins_pct||'-')+'</div></div>';
h+='<div class="sp-box"><div class="sp-box-lbl">Trainer (RTF: '+(s.trainer_rtf?s.trainer_rtf+'%':'-')+')</div><div class="sp-box-sub">14d: '+(ts2.last_14_wins_pct||'-')+' | Ovr: '+(ts2.ovr_wins_pct||'-')+'</div></div></div>';
var fm=s.form||'-',fh='';for(var ci=0;ci<fm.toString().length;ci++){{var ch=fm.toString()[ci];var c2='var(--tm)';if(ch==='1')c2='#facc15';else if(ch==='2'||ch==='3')c2='#00f5a0';else if(ch==='4'||ch==='5')c2='#00f2fe';else if(ch==='-')c2='#64748b';fh+='<span style="font-weight:800;font-family:Outfit;color:'+c2+';margin-right:2px">'+ch+'</span>'}}
h+='<div class="sp-2col"><div class="sp-box"><div class="sp-box-lbl">Form</div>'+fh+'</div><div class="sp-box"><div class="sp-box-lbl">Sire</div><div class="sp-box-val" style="color:white">'+(s.sire||'-')+'</div></div></div>';
h+='<div class="sp-rec">';
var recs=[['Course',s.course],['Distance',s.distance],['Going',s.going]];
for(var ri=0;ri<recs.length;ri++){{var d=recs[ri][1]||{{}};var rn=d.runs||'0',wn=d.wins||'0';var wp=parseInt(rn)>0?((parseInt(wn)/parseInt(rn))*100).toFixed(0):'0';var bc=parseInt(wn)>0?'#00f5a0':'#4b5563';h+='<div class="sp-rec-item"><div class="sp-rec-lbl">'+recs[ri][0]+'</div><div class="sp-rec-val">'+wn+'/'+rn+'</div><div class="sp-rec-bar"><div class="sp-rec-fill" style="width:'+wp+'%;background:'+bc+'"></div></div><div class="sp-rec-sr">'+wp+'%</div></div>'}}
h+='</div>';p.innerHTML=h;row.classList.add('show-stats')}}
function openModal(id){{document.querySelectorAll('.mo').forEach(function(m){{m.classList.remove('active')}});document.getElementById(id).classList.add('active')}}
function closeModal(id){{document.getElementById(id).classList.remove('active')}}
function openRace(rid){{closeModal('nrModal');var t=document.getElementById(rid);if(!t)return;var pb=t.closest('.m-cs');if(pb)pb.querySelectorAll('.m-race').forEach(function(r){{r.classList.add('collapsed')}});t.classList.remove('collapsed');setTimeout(function(){{t.scrollIntoView({{behavior:'smooth',block:'start'}})}},250)}}
var RD='{date_str}';
var CLOUD='https://horse-results.onrender.com';
function nn(n){{return n?n.toLowerCase().replace(/[^a-z0-9]/g,''):''}}
async function pollResults(){{
var btn=document.getElementById('res-btn'),stat=document.getElementById('res-status');
btn.textContent='Loading...';btn.style.opacity='.6';
var secs=0;var timer=setInterval(function(){{secs++;btn.textContent='Loading... '+secs+'s'}},1000);
var maxPolls=40;
for(var attempt=0;attempt<maxPolls;attempt++){{
try{{
var r=await fetch(CLOUD+'/api/results/'+RD);
if(!r.ok)throw new Error('API '+r.status);
var d=await r.json();
stat.textContent=d.progress||'Working...';
if(d.count>0)applyResults(d.results);
if(d.status==='done'&&d.count>0){{
clearInterval(timer);
localStorage.setItem('v12r_'+RD,JSON.stringify(d.results));
btn.textContent=d.count+' loaded';
btn.style.background='linear-gradient(135deg,#00f5a0,#00d2ff)';btn.style.color='#000';btn.style.opacity='1';
stat.textContent='Done ('+secs+'s)';
return;
}}
if(d.status==='done'&&d.count===0){{
clearInterval(timer);
btn.textContent='No results';btn.style.opacity='1';stat.textContent='No results found for '+RD;
setTimeout(function(){{btn.textContent='Check Results';btn.style.background='';stat.textContent=''}},5000);
return;
}}
}}catch(e){{
stat.textContent='Connecting... '+e.message;
}}
await new Promise(function(res){{setTimeout(res,3000)}});
}}
clearInterval(timer);
btn.textContent='Timed out';btn.style.background='#ef4444';btn.style.opacity='1';
stat.textContent='Server took too long';
setTimeout(function(){{btn.textContent='Check Results';btn.style.background='';stat.textContent=''}},5000);
}}
function applyResults(R){{
document.querySelectorAll('.m-row[data-horse]').forEach(function(row){{
var hn=row.getAttribute('data-horse');var m=R[nn(hn)];if(!m)return;
var pos=m.pos,sp=m.dec||0,c=row.querySelector('.m-circ'),ne=row.querySelector('.m-name');
row.classList.remove('winner','placed','lost');
if(pos===1){{row.classList.add('winner');if(c){{c.textContent='1st';c.style.background='linear-gradient(135deg,#facc15,#eab308)';c.style.color='#000';c.style.boxShadow='0 0 12px rgba(250,204,21,0.5)'}}if(ne)ne.innerHTML=hn+' <span class="pos-badge gold">1st</span>'}}
else if(pos===2){{row.classList.add('placed');if(c){{c.textContent='2nd';c.style.background='linear-gradient(135deg,#94a3b8,#e2e8f0)';c.style.color='#000'}}if(ne)ne.innerHTML=hn+' <span class="pos-badge silver">2nd</span>'}}
else if(pos===3){{row.classList.add('placed');if(c){{c.textContent='3rd';c.style.background='linear-gradient(135deg,#b45309,#f59e0b)';c.style.color='#fff'}}if(ne)ne.innerHTML=hn+' <span class="pos-badge bronze">3rd</span>'}}
else if(pos>3&&pos<=6){{row.classList.add('lost');if(c)c.textContent=pos;if(ne)ne.innerHTML=hn+' <span class="pos-badge unplaced">'+pos+'th</span>'}}
else if(pos>6){{row.classList.add('lost');if(c)c.textContent=pos>0?pos:'-'}}
if(sp>0){{var oe=row.querySelector('.m-odds');if(oe&&!oe.querySelector('.sp-tag'))oe.innerHTML+='<div class="sp-tag" style="margin-top:2px;padding:2px 6px;background:rgba(0,245,160,0.1);border:1px solid rgba(0,245,160,0.3);border-radius:4px;display:inline-block;font-size:.7rem"><span style="color:#94a3b8">SP</span> <span style="color:#00f5a0;font-weight:800">'+sp.toFixed(2)+'</span></div>'}}
}});}}
function checkResults(){{
var c=localStorage.getItem('v12r_'+RD);
if(c){{try{{var r=JSON.parse(c);if(Object.keys(r).length>0){{applyResults(r);var btn=document.getElementById('res-btn');btn.textContent='Cached ('+Object.keys(r).length+')';btn.style.background='linear-gradient(135deg,#00f5a0,#00d2ff)';btn.style.color='#000';document.getElementById('res-status').textContent='Tap again to refresh';btn.onclick=function(){{localStorage.removeItem('v12r_'+RD);btn.textContent='Check Results';btn.style.background='';btn.style.color='white';btn.onclick=function(){{checkResults()}};pollResults()}};return}}}}catch(e){{}}}}
pollResults();}}
document.addEventListener('DOMContentLoaded',function(){{var c=localStorage.getItem('v12r_'+RD);if(c){{try{{var r=JSON.parse(c);if(Object.keys(r).length>0){{applyResults(r);document.getElementById('res-btn').textContent='Cached ('+Object.keys(r).length+')';document.getElementById('res-btn').style.background='linear-gradient(135deg,#00f5a0,#00d2ff)';document.getElementById('res-btn').style.color='#000';document.getElementById('res-status').textContent='Cached results'}}}}catch(e){{}}}}}});
</script>
</body>
</html>'''

    out_file = MOBILE_OUTPUT_DIR / f"tips_mobile_{date_str}.html"
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(html)
    return str(out_file)
