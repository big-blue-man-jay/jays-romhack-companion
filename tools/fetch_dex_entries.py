#!/usr/bin/env python3
"""
fetch_dex_entries.py
Fetches Pokédex flavor text from PokeAPI → data/dex_entries.json

Maps every Pokémon name → a single English dex entry string.
Prioritises HeartGold/SoulSilver text (fitting for a HG ROM hack),
then falls back to any English entry if HG/SS isn't available.

Run locally (requires internet):
    python3 tools/fetch_dex_entries.py

Incremental: already-fetched species are skipped on re-run.
After running, re-generate pages:
    python3 tools/generate_pokemon_pages.py
"""

import json, time
from pathlib import Path

try:
    import requests
except ImportError:
    raise SystemExit("Missing 'requests' library. Run:  pip3 install requests")

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

# Preferred game order — HG/SS first, then chronologically newer games
PREFERRED_VERSIONS = [
    'heartgold', 'soulsilver',
    'black-2', 'white-2',
    'x', 'y',
    'omega-ruby', 'alpha-sapphire',
    'sun', 'moon',
    'ultra-sun', 'ultra-moon',
    'sword', 'shield',
    'scarlet', 'violet',
    # older fallbacks
    'black', 'white',
    'platinum', 'diamond', 'pearl',
    'firered', 'leafgreen',
    'emerald', 'ruby', 'sapphire',
    'crystal', 'gold', 'silver',
    'yellow', 'red', 'blue',
]

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
            if attempt == retries - 1:
                raise
            time.sleep(1.5)


def clean_text(s):
    """Remove control characters / form feeds that PokeAPI sometimes includes."""
    return s.replace('\n', ' ').replace('\f', ' ').replace('\u00ad', '').strip()


def best_entry(flavor_text_entries):
    """Pick the best English flavor text from a list of entries."""
    en = [e for e in flavor_text_entries if e.get('language', {}).get('name') == 'en']
    if not en:
        return ''
    by_version = {e['version']['name']: clean_text(e['flavor_text']) for e in en}
    for v in PREFERRED_VERSIONS:
        if v in by_version and by_version[v]:
            return by_version[v]
    return clean_text(en[0]['flavor_text'])


def main():
    print("Loading pokemon.json…")
    with open(DATA_DIR / 'pokemon.json', encoding='utf-8') as f:
        pkmn = json.load(f)

    # Collect unique species names; map species → all pokemon names that use it
    species_to_names = {}
    for p in pkmn:
        sp = p.get('species_name', p['name'])
        species_to_names.setdefault(sp, []).append(p['name'])

    out_path = DATA_DIR / 'dex_entries.json'
    existing = {}
    if out_path.exists():
        with open(out_path, encoding='utf-8') as f:
            existing = json.load(f)

    results = dict(existing)

    # Only fetch species where at least one pokemon entry is missing OR empty
    todo_species = [
        sp for sp, names in species_to_names.items()
        if any(n not in results or not results.get(n, '').strip() for n in names)
    ]

    total = len(todo_species)
    print(f"Unique species: {len(species_to_names)}  |  Need to fetch: {total}")

    for i, sp in enumerate(sorted(todo_species), 1):
        try:
            data = fetch_json(f"https://pokeapi.co/api/v2/pokemon-species/{sp}/")
            if data is None:
                print(f"  WARN: species '{sp}' not found (404)")
                entry = ''
            else:
                entry = best_entry(data.get('flavor_text_entries', []))
        except Exception as e:
            print(f"  WARN: {sp}: {e}")
            entry = ''

        # Assign the same entry to all pokemon sharing this species
        for pokemon_name in species_to_names[sp]:
            results[pokemon_name] = entry

        if i % 50 == 0 or i == total:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"  {i}/{total} species done  ({len(results)} pokemon entries saved)")
        else:
            time.sleep(0.1)  # be polite to PokeAPI

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    filled = sum(1 for v in results.values() if v)
    print(f"\nDone! {len(results)} entries → {out_path}")
    print(f"  {filled} with text, {len(results)-filled} empty (regional/unknown)")
    print("\nNext: run  python3 tools/generate_pokemon_pages.py  to bake entries into pages.")


if __name__ == '__main__':
    main()
