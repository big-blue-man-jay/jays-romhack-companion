#!/usr/bin/env python3
"""
Regenerate calculator.html with Pokémon, move, and ability data baked in.
Run this whenever pokemon.json, moves.json, abilities.json, or custom.json changes:
    python3 tools/generate_calculator.py
"""

import json, re
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
SITE_DIR = TOOLS_DIR.parent
DATA_DIR = SITE_DIR / 'data'
OUT_FILE = SITE_DIR / 'calculator.html'

# ── Load raw data ───────────────────────────────────────────────────────────
print("Loading data…")
with open(DATA_DIR / 'pokemon.json',   encoding='utf-8') as f: pkmn_raw  = json.load(f)
with open(DATA_DIR / 'custom.json',    encoding='utf-8') as f: custom_raw = json.load(f)
with open(DATA_DIR / 'moves.json',     encoding='utf-8') as f: moves_raw  = json.load(f)
with open(DATA_DIR / 'abilities.json', encoding='utf-8') as f: abil_raw   = json.load(f)

# ── Apply custom overrides (same pattern as generate_pokedex.py) ────────────
custom_map = {e['name']: e for e in custom_raw
              if 'name' in e and not e.get('_comment')}
merged = []
for p in pkmn_raw:
    entry = dict(p)
    if p['name'] in custom_map:
        for k, v in custom_map[p['name']].items():
            if k not in ('_comment', '_comment2', 'name'):
                entry[k] = v
    merged.append(entry)

# ── Build compact PKMN_DB ───────────────────────────────────────────────────
# Format: {slug: [hp, atk, def, spa, spd, spe, type1, type2, displayName, [abilities]]}
pkmn_db = {}
for p in merged:
    if not (p.get('stats') and p.get('types')):
        continue
    s  = p['stats']
    t  = p['types']
    t2 = t[1] if len(t) > 1 else ''
    ao = p.get('abilities', {})
    ab = ao.get('normal', []) + ([ao['hidden']] if ao.get('hidden') else [])
    pkmn_db[p['name']] = [
        s['hp'], s['atk'], s['def'], s['spa'], s['spd'], s['spe'],
        t[0], t2,
        p.get('display_name', p['name']),
        ab
    ]

# ── Build compact MOVE_DB ───────────────────────────────────────────────────
# Format: {slug: {n, t, c, bp?}}  c = 'P'|'S'|'X'
move_db = {}
for slug, m in moves_raw.items():
    cat = m.get('category', 'status').lower()
    c   = 'P' if cat == 'physical' else ('S' if cat == 'special' else 'X')
    entry = {'n': m.get('name', slug), 't': m.get('type', 'Normal'), 'c': c}
    bp = m.get('power')
    if bp:
        entry['bp'] = bp
    if m.get('drain'):
        entry['drain'] = m['drain']
    move_db[slug] = entry

# ── Name indexes (display name → slug) ─────────────────────────────────────
pkmn_idx = {}
for slug, d in pkmn_db.items():
    name = d[8]
    if name not in pkmn_idx:
        pkmn_idx[name] = slug

move_idx = {}
for slug, d in move_db.items():
    name = d['n']
    if name not in move_idx:
        move_idx[name] = slug

# ── Ability list ────────────────────────────────────────────────────────────
abil_display = {}   # slug → display name (Title Case)
for slug in abil_raw:
    abil_display[slug] = slug.replace('-', ' ').title()

abil_keys = sorted(abil_raw.keys())

# ── Serialize ───────────────────────────────────────────────────────────────
sep = (',', ':')
block = (
    '/* ══ AUTO-GENERATED CALC DATA ══ run tools/generate_calculator.py to update ══ */\n'
    f'const PKMN_DB={json.dumps(pkmn_db, separators=sep, ensure_ascii=False)};\n'
    f'const PKMN_IDX={json.dumps(pkmn_idx, separators=sep, ensure_ascii=False)};\n'
    f'const MOVE_DB={json.dumps(move_db, separators=sep, ensure_ascii=False)};\n'
    f'const MOVE_IDX={json.dumps(move_idx, separators=sep, ensure_ascii=False)};\n'
    f'const ABIL_DISP={json.dumps(abil_display, separators=sep, ensure_ascii=False)};\n'
    '/* ══ END CALC DATA ══ */'
)

# ── Inject between markers in calculator.html ────────────────────────────────
START  = '<!-- CALCDB:START -->'
END    = '<!-- CALCDB:END -->'
INJECT = f'{START}\n<script>\n{block}\n</script>\n{END}'

print("Reading calculator.html…")
html = OUT_FILE.read_text(encoding='utf-8')

if START in html:
    pattern  = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.DOTALL)
    new_html = pattern.sub(INJECT, html)
else:
    # First run: place before </head>
    new_html = html.replace('</head>', f'{INJECT}\n</head>', 1)

OUT_FILE.write_text(new_html, encoding='utf-8')
print(f"✓ {len(pkmn_db):,} Pokémon · {len(move_db):,} moves · {len(abil_keys):,} abilities injected into calculator.html")
