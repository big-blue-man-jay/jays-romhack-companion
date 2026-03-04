#!/usr/bin/env python3
"""
Fetch move data from PokeAPI and save to data/moves.json.
Run this once locally (takes ~3-5 min).
  python3 tools/fetch_moves.py

Options:
  --fresh-desc   Re-fetch descriptions for all already-complete entries
                 (useful when you want to update to Gen 9 flavor text without
                  re-fetching every stat from scratch)
"""

import json, sys, urllib.request, urllib.error, time, ssl, re
from pathlib import Path

# Bypass SSL verification — safe for PokeAPI fetches on machines with cert issues
_SSL_CTX = ssl._create_unverified_context()

TOOLS_DIR = Path(__file__).resolve().parent
DATA_DIR  = TOOLS_DIR.parent / 'data'

# Preferred game versions for flavor text, newest first.
# We walk this list and return the first English entry we find.
VERSION_PREF = [
    'scarlet', 'violet',                      # Gen 9
    'sword', 'shield',                        # Gen 8
    'sun', 'moon', 'ultra-sun', 'ultra-moon', # Gen 7
    'x', 'y', 'omega-ruby', 'alpha-sapphire', # Gen 6
]

def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(1)

def move_slug(name):
    return (name.lower()
            .replace(' ', '-')
            .replace("'", '')
            .replace('.', '')
            .replace('é', 'e')
            .replace('–', '-'))

def get_en(entries, field='short_effect'):
    """Return first English value of `field` from a list of language entries."""
    for e in entries:
        if e.get('language', {}).get('name') == 'en':
            return e.get(field, '').replace('\n', ' ').replace('\f', ' ').strip()
    return ''

def get_flavor_text(entries):
    """
    Pick the best English flavor text from flavor_text_entries, preferring
    newer games (Gen 9 first).  Falls back to any English entry if none of
    the preferred versions are present.
    """
    # Build a quick lookup: version_name → cleaned text
    by_version = {}
    for e in entries:
        if e.get('language', {}).get('name') != 'en':
            continue
        ver  = e.get('version_group', {}).get('name', '') or e.get('version', {}).get('name', '')
        text = e.get('flavor_text', '').replace('\n', ' ').replace('\f', ' ').strip()
        if ver and text:
            by_version[ver] = text

    for ver in VERSION_PREF:
        if ver in by_version:
            return by_version[ver]

    # Fall back to any entry (last one in the list is usually most recent)
    if by_version:
        return list(by_version.values())[-1]
    return ''

def sub_effect_chance(text, chance):
    """Replace $effect_chance placeholder with the actual percentage."""
    if chance and '$effect_chance' in text:
        text = text.replace('$effect_chance', str(chance))
    return text

# Only the flags that actually matter for damage/ability calculations.
# contact  → Flame Body, Iron Barbs, Rough Skin, Poison Point, etc.
# punch    → Iron Fist
# sound    → Soundproof, Punk Rock
# bite     → Strong Jaw
# bullet   → Bulletproof
# powder   → Overcoat, Safety Goggles
# protect  → blocked by Protect/Detect/Spiky Shield
# recharge → requires recharge turn (Hyper Beam etc.)
RELEVANT_FLAGS = {'contact', 'punch', 'sound', 'bite', 'bullet', 'powder', 'protect', 'recharge'}

def build_desc(d):
    """
    Build the best description for a move:
      1. Gen 9 flavor text (VERSION_PREF order) — most accurate for current game
      2. Any other flavor text (newest available)
      3. short_effect as last resort (may contain $effect_chance placeholder)
    """
    chance = (d.get('meta') or {}).get('effect_chance') or d.get('effect_chance')

    # Try flavor text first (Gen 9 preferred)
    desc = get_flavor_text(d.get('flavor_text_entries', []))

    # Fall back to effect short_effect
    if not desc:
        desc = get_en(d.get('effect_entries', []), 'short_effect')
        desc = sub_effect_chance(desc, chance)

    return desc[:200]


def main():
    fresh_desc = '--fresh-desc' in sys.argv

    print("Loading pokemon.json…")
    with open(DATA_DIR / 'pokemon.json', encoding='utf-8') as f:
        pkmn = json.load(f)

    # Collect unique move slugs + compute sources (which learn methods exist across all Pokémon)
    move_map    = {}   # slug → display_name
    sources_map = {}   # slug → set of learn method strings

    for p in pkmn:
        mvs = p.get('moves', {})
        for lv in mvs.get('levelup', []):
            slug = move_slug(lv['move'])
            move_map[slug] = lv['move']
            sources_map.setdefault(slug, set()).add('levelup')
        for m in mvs.get('egg', []):
            slug = move_slug(m)
            move_map[slug] = m
            sources_map.setdefault(slug, set()).add('egg')
        for m in mvs.get('tm', []):
            slug = move_slug(m)
            move_map[slug] = m
            sources_map.setdefault(slug, set()).add('tm')
        for m in mvs.get('tutor', []):
            slug = move_slug(m)
            move_map[slug] = m
            sources_map.setdefault(slug, set()).add('tutor')

    print(f"Unique moves to fetch: {len(move_map)}")

    # Resume support — only skip entries that already have the full new schema.
    # With --fresh-desc, we still re-fetch descriptions for complete entries.
    out_path = DATA_DIR / 'moves.json'
    existing = {}
    if out_path.exists():
        with open(out_path, encoding='utf-8') as f:
            raw = json.load(f)
        existing = {k: v for k, v in raw.items() if 'type' in v and 'priority' in v and v.get('type') != '?'}
        print(f"Resuming: {len(existing)} already complete.")

    if fresh_desc:
        # Re-fetch ALL known moves (to update descriptions), but keep stats from cache
        print("--fresh-desc mode: re-fetching descriptions for all moves.")
        results  = {}
        slugs    = sorted(move_map.keys())
    else:
        results = dict(existing)
        slugs   = [s for s in sorted(move_map.keys()) if s not in existing]

    total = len(slugs)
    print(f"Need to fetch: {total}")

    for i, slug in enumerate(slugs, 1):
        try:
            d = fetch_json(f"https://pokeapi.co/api/v2/move/{slug}/")

            desc  = build_desc(d)
            flags = sorted({f['name'] for f in d.get('flags', [])} & RELEVANT_FLAGS)

            meta     = d.get('meta') or {}
            min_hits = meta.get('min_hits')
            max_hits = meta.get('max_hits')
            multihit = [min_hits, max_hits] if min_hits and max_hits else None
            drain    = meta.get('drain') or 0

            if fresh_desc and slug in existing:
                # Keep all stats from cache, only update the description
                entry = dict(existing[slug])
                entry['desc']    = desc
                entry['sources'] = sorted(sources_map.get(slug, []))
                results[slug]    = entry
            else:
                results[slug] = {
                    'name':          move_map.get(slug, d['name'].replace('-', ' ').title()),
                    'type':          d['type']['name'].capitalize(),
                    'category':      d['damage_class']['name'],
                    'power':         d.get('power'),
                    'accuracy':      d.get('accuracy'),
                    'pp':            d.get('pp'),
                    'priority':      d.get('priority', 0),
                    'effect_chance': meta.get('effect_chance') or d.get('effect_chance'),
                    'flags':         flags,
                    'target':        d['target']['name'],
                    'multihit':      multihit,
                    'drain':         drain if drain != 0 else None,
                    'desc':          desc,
                    'sources':       sorted(sources_map.get(slug, [])),
                }

        except Exception as e:
            print(f"  WARN: failed {slug}: {e}")
            if slug not in results:   # don't overwrite good cached data on transient errors
                results[slug] = {
                    'name':     move_map.get(slug, slug),
                    'type':     '?',
                    'category': 'status',
                    'power':    None,
                    'accuracy': None,
                    'pp':       None,
                    'priority': 0,
                    'flags':    [],
                    'target':   'selected-pokemon',
                    'multihit': None,
                    'drain':    None,
                    'desc':     '',
                    'sources':  sorted(sources_map.get(slug, [])),
                }

        if i % 50 == 0 or i == total:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, separators=(',', ':'))
            print(f"  {i}/{total} fetched — saved.")
        else:
            time.sleep(0.08)  # ~12 req/s, well within PokeAPI's 100 req/min limit

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, separators=(',', ':'))
    print(f"\nDone! {len(results)} moves saved → {out_path}  ({out_path.stat().st_size // 1024} KB)")

if __name__ == '__main__':
    main()
