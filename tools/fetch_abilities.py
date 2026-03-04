#!/usr/bin/env python3
"""
Fetch ability descriptions from PokeAPI → data/abilities.json
Run locally: python3 tools/fetch_abilities.py  (~1 min)
"""

import json, time
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("Missing 'requests' library. Run:  pip3 install requests")

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

session = requests.Session()
session.headers.update({"User-Agent": "JaysRomhack-PokedexBuilder/1.0"})

def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return None
            else:
                r.raise_for_status()
        except Exception as e:
            if attempt == retries - 1: raise
            time.sleep(1)

def ability_slug(name):
    return name.lower().replace(' ', '-').replace("'", '').replace('.', '')

def get_en(entries, field='short_effect'):
    for e in entries:
        if e.get('language', {}).get('name') == 'en':
            return e.get(field, '').replace('\n', ' ').replace('\f', ' ').strip()
    return ''

def main():
    print("Loading pokemon.json…")
    with open(DATA_DIR / 'pokemon.json', encoding='utf-8') as f:
        pkmn = json.load(f)

    slugs = {}
    for p in pkmn:
        for a in p.get('abilities', {}).get('normal', []):
            slugs[ability_slug(a)] = a
        h = p.get('abilities', {}).get('hidden')
        if h: slugs[ability_slug(h)] = h

    print(f"Unique abilities: {len(slugs)}")

    out_path = DATA_DIR / 'abilities.json'
    existing = {}
    if out_path.exists():
        with open(out_path, encoding='utf-8') as f:
            existing = json.load(f)

    results = dict(existing)
    todo = [s for s in sorted(slugs.keys()) if s not in existing]
    total = len(todo)
    print(f"Need to fetch: {total}")

    for i, slug in enumerate(todo, 1):
        try:
            d = fetch_json(f"https://pokeapi.co/api/v2/ability/{slug}/")
            desc = get_en(d.get('effect_entries', []), 'short_effect')
            if not desc:
                desc = get_en(d.get('flavor_text_entries', []), 'flavor_text')
            results[slug] = {'name': slugs.get(slug, slug), 'desc': desc[:200]}
        except Exception as e:
            print(f"  WARN: {slug}: {e}")
            results[slug] = {'name': slugs.get(slug, slug), 'desc': ''}
        if i % 30 == 0 or i == total:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, separators=(',', ':'))
            print(f"  {i}/{total} saved.")
        else:
            time.sleep(0.08)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, separators=(',', ':'))
    print(f"Done! {len(results)} abilities → {out_path}")

if __name__ == '__main__':
    main()
