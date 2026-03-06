#!/usr/bin/env python3
"""
Regenerate pokedex.html with pokemon data baked in.
Run this whenever pokemon.json or custom.json changes.
  python3 tools/generate_pokedex.py
"""

import json, re
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
SITE_DIR = TOOLS_DIR.parent
DATA_DIR = SITE_DIR / 'data'
OUT_FILE = SITE_DIR / 'pokedex.html'
MOVE_BUCKETS = ('levelup', 'egg', 'tm', 'tutor')


def normalize_moves_block(moves):
    moves = moves if isinstance(moves, dict) else {}
    return {bucket: list(moves.get(bucket, [])) for bucket in MOVE_BUCKETS}


def copy_move_bucket(bucket):
    copied = []
    for entry in bucket:
        if isinstance(entry, dict):
            copied.append(dict(entry))
        else:
            copied.append(entry)
    return copied


def resolve_primary_species_entry(current, candidate, species_name):
    if current is None:
        return candidate
    current_exact = current['name'] == species_name
    candidate_exact = candidate['name'] == species_name
    if candidate_exact and not current_exact:
        return candidate
    if candidate_exact == current_exact and candidate['id'] < current['id']:
        return candidate
    return current


def inherit_form_moves(rows):
    source_by_species = {}
    for row in rows:
        species_name = row.get('species_name', row['name'])
        source_by_species[species_name] = resolve_primary_species_entry(
            source_by_species.get(species_name), row, species_name
        )

    inherited_rows = 0
    for row in rows:
        species_name = row.get('species_name', row['name'])
        source = source_by_species.get(species_name)
        row_moves = normalize_moves_block(row.get('moves'))
        if source is row:
            row['moves'] = row_moves
            continue

        source_moves = normalize_moves_block(source.get('moves'))
        changed = False
        for bucket in MOVE_BUCKETS:
            if not row_moves[bucket] and source_moves[bucket]:
                row_moves[bucket] = copy_move_bucket(source_moves[bucket])
                changed = True
        row['moves'] = row_moves
        if changed:
            inherited_rows += 1

    return inherited_rows

# ── Load + merge data ────────────────────────────────────────────
print("Loading data…")
with open(DATA_DIR / 'pokemon.json', encoding='utf-8') as f:
    pkmn_data = json.load(f)
with open(DATA_DIR / 'custom.json', encoding='utf-8') as f:
    custom_data = json.load(f)

# Entries to exclude entirely from the Pokédex
EXCLUDE_NAMES = {
    'eiscue-noice',         # cosmetic form, base eiscue covers it
    # Pikachu costume/cap variants — keep only base + Gmax
    'pikachu-rock-star', 'pikachu-belle', 'pikachu-pop-star', 'pikachu-phd',
    'pikachu-libre', 'pikachu-cosplay', 'pikachu-original-cap', 'pikachu-hoenn-cap',
    'pikachu-sinnoh-cap', 'pikachu-unova-cap', 'pikachu-kalos-cap',
    'pikachu-alola-cap', 'pikachu-partner-cap', 'pikachu-world-cap',
    # ── ROM hack custom megas not included in this Romhack ────────
    # Gen I
    'raichu-mega-x', 'raichu-mega-y', 'clefable-mega', 'victreebel-mega', 'starmie-mega',
    'dragonite-mega',
    # Gen II
    'meganium-mega', 'feraligatr-mega', 'skarmory-mega', 'chimecho-mega',
    # Gen III — keep absol-mega (official), exclude Z variant only
    'absol-mega-z', 'staraptor-mega',
    # Gen IV — keep garchomp-mega and lucario-mega (official), exclude Z variants only
    'garchomp-mega-z', 'lucario-mega-z',
    'froslass-mega', 'heatran-mega', 'darkrai-mega',
    # Gen V
    'emboar-mega', 'excadrill-mega', 'scolipede-mega', 'scrafty-mega',
    'eelektross-mega', 'chandelure-mega', 'golurk-mega',
    # Gen VI
    'chesnaught-mega', 'delphox-mega', 'greninja-mega', 'pyroar-mega',
    'floette-mega', 'meowstic-mega', 'barbaracle-mega', 'dragalge-mega',
    'hawlucha-mega', 'malamar-mega',
    # Gen VII
    'zygarde-mega', 'crabominable-mega', 'golisopod-mega', 'drampa-mega',
    'magearna-mega', 'magearna-original-mega', 'zeraora-mega',
    # Gen VIII
    'falinks-mega',
    # Gen IX
    'scovillain-mega', 'glimmora-mega', 'baxcalibur-mega',
    'tatsugiri-curly-mega', 'tatsugiri-droopy-mega', 'tatsugiri-stretchy-mega',
    # ── Ability-only / cosmetic alternate forms (redundant with base entry) ──
    'greninja-battle-bond',           # just an ability, covered by base greninja
    'zygarde-10-power-construct',     # same as zygarde-10 with different ability
    'zygarde-50-power-construct',     # same as zygarde-50 with different ability
    'rockruff-own-tempo',             # ability variant only
    'mimikyu-busted',                 # post-hit cosmetic form only
    'oinkologne-female',              # gender variant — one entry is enough
    # ── Koraidon ride forms (all functionally identical to base) ──
    'koraidon-limited-build', 'koraidon-sprinting-build',
    'koraidon-swimming-build', 'koraidon-gliding-build',
    # ── Miraidon drive forms (all functionally identical to base) ──
    'miraidon-low-power-mode', 'miraidon-drive-mode',
    'miraidon-aquatic-mode', 'miraidon-glide-mode',
    # ── Forms shown only in Relations tab of the base entry ──
    'maushold-family-of-three',       # shown as form on maushold-family-of-four page
    'dudunsparce-three-segment',      # shown as form on dudunsparce-two-segment page
}

custom_map = {c['name']: c for c in custom_data if 'name' in c}
merged = []
for p in pkmn_data:
    if p['name'] in EXCLUDE_NAMES:
        continue
    ov = custom_map.get(p['name'], {})
    row = {**p}
    for k, v in ov.items():
        if not k.startswith('_'):
            row[k] = v
    merged.append(row)

# ── Compute display_id and base_name ─────────────────────────────
# display_id: show the base national dex number for all forms
# (e.g. rotom-wash id=10009 → display_id=479, venusaur-mega → 3)
species_id_map = {}  # species_name → national dex id (≤1025)
for p in pkmn_data:
    sn = p.get('species_name', p['name'])
    if p['id'] <= 1025:
        species_id_map[sn] = p['id']

# Manual overrides for species whose base form is absent from pokemon.json
species_id_map.setdefault('deoxys', 386)

# ── Inject synthetic base forms missing from pokemon.json ─────────
_dex_atk = next((p for p in pkmn_data if p['name'] == 'deoxys-attack'), {})
SYNTHETIC_ENTRIES = [
    {
        'id': 386, 'name': 'deoxys', 'display_name': 'Deoxys',
        'species_name': 'deoxys', 'genus': 'DNA Pokémon', 'generation': 'III',
        'types': ['Psychic'],
        'stats': {'hp': 50, 'atk': 150, 'def': 50, 'spa': 150, 'spd': 50, 'spe': 150},
        'abilities': {'normal': ['Pressure'], 'hidden': None},
        'evolutions': [],
        'moves': _dex_atk.get('moves', {'levelup': [], 'egg': [], 'tm': [], 'tutor': []}),
        'changed': False, 'meta': False, 'notes': '',
    },
]
existing_names = {p['name'] for p in merged}
for entry in SYNTHETIC_ENTRIES:
    if entry['name'] not in existing_names:
        merged.append(entry)
        print(f"  + Injected synthetic entry: {entry['name']}")

for p in merged:
    sn = p.get('species_name', p['name'])
    p['display_id'] = species_id_map.get(sn, p['id'])
    p['base_name']  = sn   # base species name for sprite fallback

inherited_forms = inherit_form_moves(merged)
if inherited_forms:
    print(f"  Inherited base movepools for {inherited_forms} form entries")

# ── Merge egg groups ─────────────────────────────────────────────
egg_groups_file = DATA_DIR / 'egg_groups.json'
if egg_groups_file.exists():
    with open(egg_groups_file, encoding='utf-8') as f:
        egg_groups_map = json.load(f)
    for p in merged:
        p['egg_groups'] = egg_groups_map.get(p['name'], egg_groups_map.get(p.get('species_name', p['name']), []))
    print(f"  Egg groups merged from egg_groups.json")
else:
    print("  egg_groups.json not found — egg_groups field will be empty")

# Compact JSON — no spaces, ASCII-safe
data_js = json.dumps(merged, separators=(',', ':'), ensure_ascii=True)
print(f"  {len(merged)} Pokémon, {len(data_js)//1024}KB")

# ── Read current pokedex.html ────────────────────────────────────
html = OUT_FILE.read_text(encoding='utf-8')

# ── 1. Inject data constant before the main <script> ─────────────
data_tag = f'<script>\nconst POKEMON_DATA={data_js};\n</script>\n'

# Replace existing injected block if present, else insert before main <script>
if '<script>\nconst POKEMON_DATA=' in html:
    html = re.sub(r'<script>\nconst POKEMON_DATA=.*?;\n</script>\n',
                  lambda _: data_tag, html, flags=re.DOTALL)
else:
    html = html.replace('<script>\nconst TYPE_COLORS', data_tag + '<script>\nconst TYPE_COLORS', 1)

# ── 2. Replace async fetch-based init() with sync embedded version ─
OLD_INIT = '''async function init() {
  try {
    const [pkmnData, customData] = await Promise.all([
      fetch('data/pokemon.json').then(r=>r.json()),
      fetch('data/custom.json').then(r=>r.json())
    ]);
    const customMap = {};
    customData.forEach(c => { if (c.name) customMap[c.name] = c; });
    allPokemon = pkmnData.map(p => {
      const ov = customMap[p.name];
      if (!ov) return p;
      const merged = {...p};
      for (const k of Object.keys(ov)) { if (!k.startsWith('_')) merged[k] = ov[k]; }
      return merged;
    });
    document.getElementById('loadingState').style.display = 'none';
    buildTypePills();
    applyFilters();
  } catch(e) {
    document.getElementById('loadingState').innerHTML = '<span style="color:#F85888">Failed to load Pokédex data.</span>';
  }
}'''

NEW_INIT = '''function init() {
  allPokemon = POKEMON_DATA;
  document.getElementById('loadingState').style.display = 'none';
  buildTypePills();
  applyFilters();
}'''

if OLD_INIT in html:
    html = html.replace(OLD_INIT, NEW_INIT)
    print("  Replaced async init() with embedded version.")
elif 'function init()' in html and 'POKEMON_DATA' in html:
    print("  init() already uses embedded data — skipping replacement.")
else:
    print("  WARNING: Could not find async init() to replace — check pokedex.html manually.")

# ── Write output ─────────────────────────────────────────────────
OUT_FILE.write_text(html, encoding='utf-8')
print(f"Done! → {OUT_FILE}")
