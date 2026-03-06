#!/usr/bin/env python3
"""
Generate individual Pokémon HTML pages.
  python3 tools/generate_pokemon_pages.py              # all pages
  python3 tools/generate_pokemon_pages.py bulbasaur    # specific names
"""

import json, sys, re
from pathlib import Path
from html import escape

TOOLS_DIR  = Path(__file__).resolve().parent
SITE_DIR   = TOOLS_DIR.parent
DATA_DIR   = SITE_DIR / 'data'
OUTPUT_DIR = SITE_DIR / 'pokemon'
MOVE_BUCKETS = ('levelup', 'egg', 'tm', 'tutor')
CUSTOM_SPRITE_DIR = SITE_DIR / 'sprites' / 'pokemon'

TYPE_COLORS = {
    'Normal':('#A8A878','#fff'),'Fire':('#F08030','#fff'),'Water':('#6890F0','#fff'),
    'Electric':('#F8D030','#333'),'Grass':('#78C850','#fff'),'Ice':('#98D8D8','#333'),
    'Fighting':('#C03028','#fff'),'Poison':('#A040A0','#fff'),'Ground':('#E0C068','#333'),
    'Flying':('#A890F0','#fff'),'Psychic':('#F85888','#fff'),'Bug':('#A8B820','#fff'),
    'Rock':('#B8A038','#fff'),'Ghost':('#705898','#fff'),'Dragon':('#7038F8','#fff'),
    'Dark':('#705848','#fff'),'Steel':('#B8B8D0','#333'),'Fairy':('#EE99AC','#fff'),
}
STAT_COLORS = {'HP':'#FC6C6D','Atk':'#F5A073','Def':'#F5D782','SpA':'#86BFFF','SpD':'#96D9D6','Spe':'#F85888'}

# ── CUSTOM SPRITE REGISTRY (auto-discovered) ──────────────────────
# Any file named:
#   sprites/pokemon/{name}.png
#   sprites/pokemon/{name}-shiny.png
# is picked up automatically.
def discover_custom_sprites():
    normal = set()
    shiny = set()
    if not CUSTOM_SPRITE_DIR.exists():
        return normal, shiny
    for sprite_file in CUSTOM_SPRITE_DIR.glob('*.png'):
        stem = sprite_file.stem.lower()
        if stem in {'readme', 'placeholder'}:
            continue
        if stem.endswith('-shiny'):
            base_name = stem[:-6]
            if base_name:
                shiny.add(base_name)
            continue
        normal.add(stem)
    return normal, shiny


CUSTOM_SPRITES, CUSTOM_SPRITES_SHINY = discover_custom_sprites()

LOCAL_SPRITE_NAME_MAP = {
    'basculegion-female': 'basculegion-f',
    'basculegion-male': 'basculegion',
    'basculin-blue-striped': 'basculin-bluestriped',
    'basculin-white-striped': 'basculin-whitestriped',
    'basculin-red-striped': 'basculin',
    'darmanitan-galar-zen': 'darmanitan-galarzen',
    'enamorus-incarnate': 'enamorus',
    'indeedee-female': 'indeedee-f',
    'indeedee-male': 'indeedee',
    'maushold-family-of-four': 'maushold-four',
    'maushold-family-of-three': 'maushold-four',
    'meowstic-female': 'meowstic-f',
    'meowstic-male': 'meowstic',
    'mimikyu-disguised': 'mimikyu',
    'morpeko-full-belly': 'morpeko',
    'morpeko-hangry': 'morpeko',
    'necrozma-dawn': 'necrozma-dawnwings',
    'necrozma-dusk': 'necrozma-duskmane',
    'ogerpon': 'ogerpon-teal',
    'ogerpon-cornerstone-mask': 'ogerpon-cornerstone',
    'ogerpon-hearthflame-mask': 'ogerpon-hearthflame',
    'ogerpon-wellspring-mask': 'ogerpon-wellspring',
    'oinkologne-female': 'oinkologne-f',
    'oinkologne-male': 'oinkologne',
    'oricorio-pom-pom': 'oricorio-pompom',
    'palafin-hero': 'palafin',
    'palafin-zero': 'palafin',
    'squawkabilly-blue-plumage': 'squawkabilly-blue',
    'squawkabilly-green-plumage': 'squawkabilly',
    'squawkabilly-white-plumage': 'squawkabilly-white',
    'squawkabilly-yellow-plumage': 'squawkabilly-yellow',
    'tatsugiri-curly': 'tatsugiri',
    'tatsugiri-droopy': 'tatsugiri',
    'tatsugiri-stretchy': 'tatsugiri',
    'tauros-paldea-aqua-breed': 'tauros-paldea-aqua',
    'tauros-paldea-blaze-breed': 'tauros-paldea-blaze',
    'tauros-paldea-combat-breed': 'tauros-paldea-combat',
    'toxtricity-amped': 'toxtricity',
    'toxtricity-amped-gmax': 'toxtricity-gmax',
    'toxtricity-low-key': 'toxtricity-lowkey',
    'toxtricity-low-key-gmax': 'toxtricity-gmax',
    'urshifu-rapid-strike': 'urshifu-rapidstrike',
    'urshifu-rapid-strike-gmax': 'urshifu-rapidstrikegmax',
    'urshifu-single-strike': 'urshifu',
    'urshifu-single-strike-gmax': 'urshifu-gmax',
    'zygarde-50': 'zygarde',
}


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

def type_badge(t, size=12):
    bg, fg = TYPE_COLORS.get(t, ('#888','#fff'))
    return f'<span class="type-badge" style="background:{bg};color:{fg};font-size:{size}px">{escape(t)}</span>'

def fmt_method(method):
    if not method: return ''
    t, v = method.get('type',''), str(method.get('value',''))
    if t == 'level':
        if v == '?': return 'Special'   # fallback; most real cases are in EVO_METHOD_OVERRIDES
        return f'Lv.&nbsp;{v}'
    if t == 'item':       return escape(v)
    if t == 'friendship':
        if v == 'day':   return '&#9829;&nbsp;Friendship&nbsp;(Day)'
        if v == 'night': return '&#9829;&nbsp;Friendship&nbsp;(Night)'
        return '&#9829;&nbsp;Friendship'
    if t == 'trade':      return 'Trade' + (f'&nbsp;({escape(v)})' if v else '')
    if t == 'use-move':             return 'Use Move'
    if t == 'agile-style-move':     return 'Agile Style Move'
    if t == 'strong-style-move':    return 'Strong Style Move'
    if t == 'recoil-damage':        return 'Take Recoil Damage'
    if t == 'take-damage':          return 'Take Damage'
    if t == 'three-critical-hits':  return '3 Critical Hits'
    if t == 'three-defeated-bisharp': return 'Defeat 3 Bisharp'
    if t == 'shed':                 return 'Shed (empty&nbsp;slot)'
    if t == 'spin':                 return 'Spin'
    if t == 'gimmmighoul-coins':    return '999 Gimmighoul Coins'
    if t == 'tower-of-darkness':    return 'Tower of Darkness'
    if t == 'tower-of-waters':      return 'Tower of Waters'
    if t == 'other':                return 'Special'
    return escape(v) if v else 'Special'


def item_slug(name):
    """Showdown item icon slug: lowercase, no spaces or punctuation."""
    return re.sub(r'[^a-z0-9]', '', name.lower())

def item_slug_pokeapi(name):
    """PokeAPI item sprite slug: lowercase, spaces→hyphens, strip punctuation."""
    slug = name.lower()
    slug = re.sub(r"['\.,]", '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug

def collect_evo_items(evolutions):
    """Return ordered-unique list of item names used in this pokemon's evo chain.
    Any trade evolution always includes 'Linking Cord' as the first item."""
    seen, out = set(), []
    has_trade = any(evo.get('method', {}).get('type') == 'trade' for evo in evolutions)
    if has_trade:
        seen.add('Linking Cord')
        out.append('Linking Cord')
    for evo in evolutions:
        m = evo.get('method', {})
        if m.get('type') in ('item', 'trade') and m.get('value'):
            v = m['value']
            if v not in seen:
                seen.add(v)
                out.append(v)
    return out


# ── EVO METHOD OVERRIDES ─────────────────────────────────────────────────────
# Correct labels for evolutions stored as level:"?" in the raw data.
# Key: (from_name, to_name)  Value: arrow label HTML (plain text, no escaping needed)
EVO_METHOD_OVERRIDES = {
    # ── Friendship ──────────────────────────────────────────────────────────
    ('pichu',     'pikachu'):           '&#9829;&nbsp;Friendship',
    ('cleffa',    'clefairy'):          '&#9829;&nbsp;Friendship',
    ('igglybuff', 'jigglypuff'):        '&#9829;&nbsp;Friendship',
    ('golbat',    'crobat'):            '&#9829;&nbsp;Friendship',
    ('chansey',   'blissey'):           '&#9829;&nbsp;Friendship',
    ('togepi',    'togetic'):           '&#9829;&nbsp;Friendship',
    ('eevee',     'espeon'):            '&#9829;&nbsp;Friendship&nbsp;(Day)',
    ('eevee',     'umbreon'):           '&#9829;&nbsp;Friendship&nbsp;(Night)',
    ('eevee',     'sylveon'):           '&#9829;&nbsp;Friendship',
    ('azurill',   'marill'):            '&#9829;&nbsp;Friendship',
    ('budew',     'roselia'):           '&#9829;&nbsp;Friendship&nbsp;(Day)',
    ('buneary',   'lopunny'):           '&#9829;&nbsp;Friendship',
    ('riolu',     'lucario'):           '&#9829;&nbsp;Friendship&nbsp;(Day)',
    ('chingling', 'chimecho'):          '&#9829;&nbsp;Friendship&nbsp;(Night)',
    ('woobat',    'swoobat'):           '&#9829;&nbsp;Friendship',
    ('swadloon',  'leavanny'):          '&#9829;&nbsp;Friendship',
    ('munchlax',  'snorlax'):           '&#9829;&nbsp;Friendship',
    ('bonsly',    'sudowoodo'):         '&#9829;&nbsp;Friendship',
    ('mime-jr',   'mr-mime'):           '&#9829;&nbsp;Friendship',
    ('happiny',   'chansey'):           '&#9829;&nbsp;Friendship',
    ('rellor',    'rabsca'):            '&#9829;&nbsp;Friendship',
    ('pawmo',     'pawmot'):            '&#9829;&nbsp;Friendship',
    ('bramblin',  'brambleghast'):      '&#9829;&nbsp;Friendship',
    ('type-null', 'silvally'):          '&#9829;&nbsp;Friendship',
    ('snom',      'frosmoth'):          '&#9829;&nbsp;Friendship&nbsp;(Night)',
    # ── Level up + know a move ──────────────────────────────────────────────
    ('aipom',     'ambipom'):           'Lv.up&nbsp;+&nbsp;Double Hit',
    ('piloswine', 'mamoswine'):         'Lv.up&nbsp;+&nbsp;Ancient Power',
    ('lickitung', 'lickilicky'):        'Lv.up&nbsp;+&nbsp;Rollout',
    ('tangela',   'tangrowth'):         'Lv.up&nbsp;+&nbsp;Ancient Power',
    ('yanma',     'yanmega'):           'Lv.up&nbsp;+&nbsp;Ancient Power',
    ('steenee',   'tsareena'):          'Lv.up&nbsp;+&nbsp;Stomp',
    ('clobbopus', 'grapploct'):         'Lv.up&nbsp;+&nbsp;Taunt',
    ('poipole',   'naganadel'):         'Lv.up&nbsp;+&nbsp;Dragon Pulse',
    ('girafarig', 'farigiraf'):         'Lv.up&nbsp;+&nbsp;Twin Beam',
    ('dunsparce', 'dudunsparce-two-segment'):   'Lv.up&nbsp;+&nbsp;Hyper Drill',
    ('dunsparce', 'dudunsparce-three-segment'): 'Lv.up&nbsp;+&nbsp;Hyper Drill&nbsp;(rare)',
    # ── Level up + held item ────────────────────────────────────────────────
    ('gligar',    'gliscor'):           'Lv.up&nbsp;+&nbsp;Razor Fang&nbsp;(Night)',
    ('sneasel',   'weavile'):           'Lv.up&nbsp;+&nbsp;Razor Claw&nbsp;(Night)',
    ('sneasel',   'sneasler'):          'Lv.up&nbsp;+&nbsp;Razor Claw&nbsp;(Day)',
    # ── Level up + special location ─────────────────────────────────────────
    ('magneton',  'magnezone'):         'Lv.up&nbsp;(Magnetic Field)',
    ('nosepass',  'probopass'):         'Lv.up&nbsp;(Magnetic Field)',
    ('charjabug', 'vikavolt'):          'Lv.up&nbsp;(Special Location)',
    ('crabrawler', 'crabominable'):     'Lv.up&nbsp;(Cold Location)',
    # ── Level up + party condition ──────────────────────────────────────────
    ('mantyke',   'mantine'):           'Lv.up&nbsp;+&nbsp;Remoraid in party',
    # ── Maushold (other = random on level up) ───────────────────────────────
    ('tandemaus', 'maushold-family-of-four'):   'Lv.&nbsp;25',
    ('tandemaus', 'maushold-family-of-three'):  'Lv.&nbsp;25&nbsp;(rare)',
    # ── Regional form special methods ────────────────────────────────────────
    ('rattata-alola',   'raticate-alola'):       'Lv.&nbsp;20&nbsp;(Night)',
    ('meowth-alola',    'persian-alola'):        '&#9829;&nbsp;Friendship',
    ('cubone',          'marowak-alola'):        'Lv.&nbsp;28&nbsp;(Night)',
    ('koffing',         'weezing-galar'):        'Lv.&nbsp;35',
    ('farfetchd-galar', 'sirfetchd'):            '3&nbsp;Critical&nbsp;Hits',
    ('mime-jr',         'mr-mime-galar'):        'Lv.up&nbsp;+&nbsp;Mimic',
    ('linoone-galar',   'obstagoon'):            'Lv.&nbsp;35&nbsp;(Night)',
    ('sneasel-hisui',   'sneasler'):             'Lv.up&nbsp;+&nbsp;Razor Claw&nbsp;(Day)',
    ('yamask-galar',    'runerigus'):            '49&nbsp;damage&nbsp;taken',
    ('qwilfish-hisui',  'overqwil'):             'Strong Style&nbsp;Barb Barrage',
}

# ── MEGA STONE MAP ────────────────────────────────────────────────────────────
# Maps mega/primal form name → the item required to trigger that form.
# Used to auto-populate Related Items on any page in the species line.
MEGA_STONE_MAP = {
    # Gen I
    'venusaur-mega':      'Venusaurite',
    'charizard-mega-x':   'Charizardite X',
    'charizard-mega-y':   'Charizardite Y',
    'blastoise-mega':     'Blastoisinite',
    'beedrill-mega':      'Beedrillite',
    'pidgeot-mega':       'Pidgeotite',
    'alakazam-mega':      'Alakazite',
    'slowbro-mega':       'Slowbronite',
    'gengar-mega':        'Gengarite',
    'kangaskhan-mega':    'Kangaskhanite',
    'pinsir-mega':        'Pinsirite',
    'gyarados-mega':      'Gyaradosite',
    'aerodactyl-mega':    'Aerodactylite',
    'mewtwo-mega-x':      'Mewtwonite X',
    'mewtwo-mega-y':      'Mewtwonite Y',
    # Gen II
    'ampharos-mega':      'Ampharosite',
    'steelix-mega':       'Steelixite',
    'scizor-mega':        'Scizorite',
    'heracross-mega':     'Heracronite',
    'houndoom-mega':      'Houndoominite',
    'tyranitar-mega':     'Tyranitarite',
    # Gen III
    'sceptile-mega':      'Sceptilite',
    'blaziken-mega':      'Blazikenite',
    'swampert-mega':      'Swampertite',
    'gardevoir-mega':     'Gardevoirite',
    'mawile-mega':        'Mawilite',
    'aggron-mega':        'Aggronite',
    'medicham-mega':      'Medichamite',
    'manectric-mega':     'Manectite',
    'sharpedo-mega':      'Sharpedonite',
    'camerupt-mega':      'Cameruptite',
    'altaria-mega':       'Altarianite',
    'banette-mega':       'Banettite',
    'absol-mega':         'Absolite',
    'glalie-mega':        'Glalitite',
    'salamence-mega':     'Salamencite',
    'metagross-mega':     'Metagrossite',
    'latias-mega':        'Latiasite',
    'latios-mega':        'Latiosite',
    # Gen IV
    'garchomp-mega':      'Garchompite',
    'lucario-mega':       'Lucarionite',
    'abomasnow-mega':     'Abomasite',
    # Gen VI
    'lopunny-mega':       'Lopunnite',
    'gallade-mega':       'Galladite',
    'audino-mega':        'Audinite',
    'diancie-mega':       'Diancite',
    'sableye-mega':       'Sablenite',
    # Primal reversions (items, not technically mega stones but same concept)
    'groudon-primal':     'Red Orb',
    'kyogre-primal':      'Blue Orb',
}

# ── ITEM LOCATIONS ────────────────────────────────────────────────────────────
# Stub: maps item name → area slug for linking to ../areas/{slug}.html
# Populate this when area pages are built.
ITEM_LOCATIONS = {
    # e.g. 'Venusaurite': 'celadon-city',
}

def stat_bar(label, value, max_val=255):
    color = STAT_COLORS.get(label, '#AAB2BA')
    pct   = min(100, value / max_val * 100)
    return (f'<div class="stat-row">'
            f'<span class="stat-lbl">{label}</span>'
            f'<span class="stat-val" style="color:{color}">{value}</span>'
            f'<div class="stat-track"><div class="stat-fill" style="width:{pct:.1f}%;background:{color}"></div></div>'
            f'</div>')

def move_slug(name):
    return name.lower().replace(' ','-').replace("'",'').replace('.',''). replace('é','e').replace('–','-')

def ability_slug(name):
    return name.lower().replace(' ', '-').replace("'", '').replace('.', '')

def sd_sprite(name, species_name):
    """Showdown sprite filename: strip hyphens from the species part only, keep form suffix.
    e.g. sd_sprite('venusaur-mega','venusaur') → 'venusaur-mega'
         sd_sprite('mr-mime','mr-mime')        → 'mrmime'
         sd_sprite('tapu-koko','tapu-koko')    → 'tapukoko'
         sd_sprite('oricorio-baile','oricorio')→ 'oricorio-baile'
    """
    species_id = re.sub(r'[^a-z0-9]', '', species_name.lower())
    suffix     = name[len(species_name):]  # e.g. '' or '-mega' or '-wash'
    return species_id + suffix

def custom_sprite_candidates(name, species_name):
    candidates = []
    seen = set()

    def add(value):
        value = (value or '').strip().lower()
        if not value or value in seen:
            return
        seen.add(value)
        candidates.append(value)

    add(name)
    mapped = LOCAL_SPRITE_NAME_MAP.get(name)
    if mapped:
        add(mapped)
    add(species_name)
    add(sd_sprite(name, species_name))

    if name.endswith('-breed'):
        add(name[:-6])

    for base in list(candidates):
        if base.endswith('-female'):
            add(base.replace('-female', '-f'))
        if base.endswith('-male'):
            add(base.replace('-male', '-m'))
            add(base.replace('-male', ''))
        if base.endswith('-blue-striped'):
            add(base.replace('-blue-striped', '-bluestriped'))
        if base.endswith('-white-striped'):
            add(base.replace('-white-striped', '-whitestriped'))
        if base.endswith('-zen-mode'):
            add(base.replace('-zen-mode', '-zen'))
            add(base.replace('-zen-mode', 'zen'))
        if base.endswith('-disguised'):
            add(base.replace('-disguised', ''))
        if base.endswith('-hangry'):
            add(base.replace('-hangry', ''))
        if base.endswith('-full-belly'):
            add(base.replace('-full-belly', ''))
        if base.endswith('-incarnate'):
            add(base.replace('-incarnate', ''))
        if base.endswith('-plumage'):
            add(base.replace('-plumage', ''))
        if base.endswith('-mask'):
            add(base.replace('-mask', ''))
        if base.endswith('-family-of-four'):
            add(base.replace('-family-of-four', '-four'))
        if base.endswith('-family-of-three'):
            add(base.replace('-family-of-three', '-three'))
            add(base.replace('-family-of-three', '-four'))
        if base.endswith('-low-key'):
            add(base.replace('-low-key', '-lowkey'))
        if base.endswith('-rapid-strike'):
            add(base.replace('-rapid-strike', '-rapidstrike'))
        if base.endswith('-rapid-strike-gmax'):
            add(base.replace('-rapid-strike-gmax', '-rapidstrikegmax'))

    return candidates


def resolve_custom_sprite_key(name, species_name, pool):
    for candidate in custom_sprite_candidates(name, species_name):
        if candidate in pool:
            return candidate
    return None

def sprite_urls(name, species_name):
    """Return (normal_url, shiny_url, fallback_url) for a Pokémon sprite.
    Paths are relative to the pokemon/ directory (i.e. pages at pokemon/NAME.html).
    Names in CUSTOM_SPRITES use local sprites/pokemon/ files with Showdown as fallback.
    """
    sid  = sd_sprite(name, species_name)
    sd_n  = f'https://play.pokemonshowdown.com/sprites/gen5/{sid}.png'
    sd_s  = f'https://play.pokemonshowdown.com/sprites/gen5-shiny/{sid}.png'
    sd_fb = f'https://play.pokemonshowdown.com/sprites/dex/{sid}.png'

    custom_normal = resolve_custom_sprite_key(name, species_name, CUSTOM_SPRITES)
    custom_shiny = resolve_custom_sprite_key(name, species_name, CUSTOM_SPRITES_SHINY)

    if custom_normal:
        normal   = f'../sprites/pokemon/{custom_normal}.png'
        fallback = sd_n          # Showdown gen5 as first fallback
    else:
        normal   = sd_n
        fallback = sd_fb         # Showdown dex as first fallback

    shiny = f'../sprites/pokemon/{custom_shiny}-shiny.png' if custom_shiny else sd_s
    return normal, shiny, fallback

# ── EVO CHAIN (header, with mega/gmax injection) ─────────────────
def find_extra_forms(base_name, all_names):
    """Find mega / gmax forms for a base pokemon name."""
    forms = []
    for suffix, label in [('-mega', 'Mega'), ('-mega-x', 'Mega X'), ('-mega-y', 'Mega Y'), ('-gmax', 'Gmax')]:
        form_name = base_name + suffix
        if form_name in all_names:
            forms.append((form_name, label))
    return forms

def build_evo_chain_header(evolutions, current_name, name_map, all_names, name_to_species=None):
    if not evolutions and not find_extra_forms(current_name, all_names):
        # Check if current IS a mega/gmax form
        base = current_name.split('-mega')[0].split('-gmax')[0]
        if base != current_name and base in name_map:
            label = 'Mega' if '-mega' in current_name else 'Gmax'
            return f'''<div class="evo-chain-h">
                {_c_node(base, current_name, name_map, name_to_species)}{_c_arrow(label)}
                {_c_node(current_name, current_name, name_map, name_to_species)}</div>'''
        return ''

    # ── Deduplicate: for each (from, to) pair, prefer a real method over level:"?"
    seen_pairs = {}
    deduped = []
    for evo in evolutions:
        pair = (evo['from'], evo['to'])
        m = evo.get('method', {})
        is_question = m.get('type') == 'level' and str(m.get('value', '')) == '?'
        if pair not in seen_pairs:
            seen_pairs[pair] = (len(deduped), is_question)
            deduped.append(evo)
        elif is_question:
            pass  # already have an equal or better entry
        elif seen_pairs[pair][1]:
            # Existing was a '?' — replace with this real method
            idx = seen_pairs[pair][0]
            deduped[idx] = evo
            seen_pairs[pair] = (idx, False)
    evolutions = deduped

    from_map    = {}
    all_targets = set()
    for evo in evolutions:
        all_targets.add(evo['to'])
        from_map.setdefault(evo['from'], []).append(evo)

    roots = set(from_map.keys()) - all_targets
    if not roots:
        root = evolutions[0]['from'] if evolutions else current_name
    elif current_name in roots:
        root = current_name
    else:
        REGIONAL = ('-alola', '-galar', '-hisui', '-paldea')
        def can_reach(r, target, visited=None):
            if visited is None: visited = set()
            if r in visited: return False
            visited.add(r)
            if r == target: return True
            return any(can_reach(e['to'], target, visited) for e in from_map.get(r, []))
        curr_tag = next((t for t in REGIONAL if t in current_name), None)
        reachable = [r for r in roots if can_reach(r, current_name)]
        if reachable:
            if curr_tag:
                same = [r for r in reachable if curr_tag in r]
                root = sorted(same)[0] if same else sorted(reachable)[0]
            else:
                plain = [r for r in reachable if not any(t in r for t in REGIONAL)]
                root = sorted(plain)[0] if plain else sorted(reachable)[0]
        else:
            root = sorted(roots)[0]

    def traverse(name):
        node     = _c_node(name, current_name, name_map, name_to_species)
        children = from_map.get(name, [])

        # If terminal node, check for mega/gmax forms
        extra = find_extra_forms(name, all_names) if not children else []

        if not children and not extra:
            return node

        # Combine normal children + extra forms
        all_branches = []
        for evo in children:
            # Use override label if available, else fall back to fmt_method
            label = EVO_METHOD_OVERRIDES.get((evo['from'], evo['to'])) \
                    or fmt_method(evo.get('method'))
            all_branches.append(_c_arrow(label) + traverse(evo['to']))
        for form_name, form_label in extra:
            all_branches.append(_c_arrow(form_label) + _c_node(form_name, current_name, name_map, name_to_species))

        if len(all_branches) == 1:
            return node + all_branches[0]

        if len(all_branches) >= 4:
            # Wide mode: labeled grid — method name above sprite, no arrows between siblings.
            # A single → connects the parent to the whole group so it reads as
            # "parent → all of these" rather than a chain.
            wide_items = []
            for evo in children:
                label = EVO_METHOD_OVERRIDES.get((evo['from'], evo['to'])) \
                        or fmt_method(evo.get('method'))
                child_node = _c_node(evo['to'], current_name, name_map, name_to_species)
                wide_items.append(
                    f'<div class="evo-c-wide-item">'
                    f'<span class="evo-c-mth">{label}</span>{child_node}</div>')
            for form_name, form_label in extra:
                child_node = _c_node(form_name, current_name, name_map, name_to_species)
                wide_items.append(
                    f'<div class="evo-c-wide-item">'
                    f'<span class="evo-c-mth">{form_label}</span>{child_node}</div>')
            grid = f'<div class="evo-c-branches-wide">{"".join(wide_items)}</div>'
            connector = '<span class="evo-c-arw evo-c-wide-arr">\u2192</span>'
            return node + connector + grid

        # 2–3 branches: clean vertical stack (unchanged)
        branches = ''.join(f'<div class="evo-c-branch">{b}</div>' for b in all_branches)
        return node + f'<div class="evo-c-branches">{branches}</div>'

    return f'<div class="evo-chain-h">{traverse(root)}</div>'

def _c_node(name, current_name, name_map, name_to_species=None):
    raw     = name_map.get(name, name.replace('-',' ').title())
    # Strip parenthetical form labels (e.g. "Venusaur (Gmax)") — the arrow already clarifies the form
    display = escape(re.sub(r'\s*\([^)]+\)\s*$', '', raw).strip())
    cls     = ' evo-c-cur' if name == current_name else ''
    species = (name_to_species or {}).get(name, name)
    spr_n, spr_s, dex_fb = sprite_urls(name, species)
    return (f'<a href="{name}.html" class="evo-c-node{cls}">'
            f'<img class="evo-c-spr" src="{spr_n}" data-normal="{spr_n}" data-shiny="{spr_s}" alt="{display}" '
            f'onerror="if(!this.dataset.tried){{this.dataset.tried=1;this.src=\'{dex_fb}\'}}else{{this.onerror=null;this.src=\'https://play.pokemonshowdown.com/sprites/gen5/substitute.png\'}}">'
            f'<span class="evo-c-lbl">{display}</span></a>')

def _c_arrow(label):
    return f'<div class="evo-c-arr"><span class="evo-c-mth">{label}</span><span class="evo-c-arw">→</span></div>'

def build_family_web(current_name, evolutions, name_map, all_names,
                     species_forms_map, name_to_species, species_id_map):
    """Flat sprite row of ALL Pokémon in the evolutionary family:
    every node in the evo chain + all their alternate forms (regionals, megas, gmax, etc.).
    Shown below a divider in Pokédex order. Returns '' if the family has only 1 member."""
    # 1. Collect every name that appears in the evo chain
    chain_names = {current_name}
    for evo in evolutions:
        chain_names.add(evo.get('from', ''))
        chain_names.add(evo.get('to', ''))
    chain_names.discard('')

    # 2. Expand each chain name to all its forms
    family: set = set()
    for n in chain_names:
        sp = (name_to_species or {}).get(n, n)
        for form in species_forms_map.get(sp, [n]):
            if form in all_names:
                family.add(form)
        # Also pick up megas / gmax that may not live in species_forms_map
        for form_name, _ in find_extra_forms(n, all_names):
            if form_name in all_names:
                family.add(form_name)

    if len(family) <= 1:
        return ''

    # 3. Sort: base national dex id ascending, then by name for same-species forms
    def sort_key(n):
        sp  = (name_to_species or {}).get(n, n)
        sid = species_id_map.get(sp, 9999)
        return (sid, n)
    sorted_family = sorted(family, key=sort_key)

    # 4. Render — reuse _c_node so custom sprites + current highlight + shiny all work
    nodes = ''.join(_c_node(n, current_name, name_map, name_to_species) for n in sorted_family)
    return f'<div class="family-web">{nodes}</div>'


# ── PAGE GENERATOR ────────────────────────────────────────────────
def generate_page(p, name_map, all_names, species_forms_map, species_id_map, name_to_species=None, ability_db=None, move_db=None):
    name        = p['name']
    display     = escape(p['display_name'])
    species_name = p.get('species_name', name)
    # Use base national dex number for display (e.g. deoxys-attack → #386)
    display_id  = species_id_map.get(species_name, p['id'])
    dex_num     = str(display_id).zfill(4)
    genus       = escape(p.get('genus',''))
    generation  = escape(p.get('generation',''))
    types       = p.get('types', [])
    stats       = p.get('stats', {})
    abilities   = p.get('abilities', {})
    evolutions  = p.get('evolutions', [])
    moves       = p.get('moves', {})
    changed     = p.get('changed', False)
    meta        = p.get('meta', False)
    notes       = p.get('notes', '').strip()
    strategy    = p.get('strategy', {})
    dex_entry   = p.get('dex_entry', '').strip()
    custom_items = p.get('items', [])   # manually specified items in custom.json

    sprite_url, shiny_url, sprite_fallback = sprite_urls(name, species_name)
    total      = sum(stats.values())
    types_html = ' '.join(type_badge(t) for t in types)

    flags_html = ''
    if changed: flags_html += '<span class="page-flag flag-mod">MODIFIED</span>'
    if meta:    flags_html += '<span class="page-flag flag-meta">META</span>'

    stats_html = ''.join(stat_bar(l, stats.get(k,0)) for l,k in
        [('HP','hp'),('Atk','atk'),('Def','def'),('SpA','spa'),('SpD','spd'),('Spe','spe')])
    stats_html += f'<div class="stat-total"><span class="stat-total-lbl">Total</span><span class="stat-total-val">{total}</span></div>'

    # Abilities — build items with desc placeholder (JS fills from abilities.json)
    normal_abs = abilities.get('normal', [])
    hidden_ab  = abilities.get('hidden')
    abs_items = []
    def _ab_desc(name):
        if not ability_db: return ''
        info = ability_db.get(ability_slug(name), '')
        if isinstance(info, str): return info
        return info.get('desc') or info.get('short_effect') or ''

    for a in normal_abs:
        slug = ability_slug(a)
        desc = _ab_desc(a)
        abs_items.append(f'<div class="ability-item" data-slug="{slug}">'
                         f'<span class="ability-name">{escape(a)}</span>'
                         f'<span class="ability-desc" id="ab-{slug}">{escape(desc)}</span></div>')
    if hidden_ab:
        slug = ability_slug(hidden_ab)
        desc = _ab_desc(hidden_ab)
        abs_items.append(f'<div class="ability-item ability-ha" data-slug="{slug}">'
                         f'<div class="ability-name-row"><span class="ability-name">{escape(hidden_ab)}</span>'
                         f'<span class="ha-tag">HA</span></div>'
                         f'<span class="ability-desc" id="ab-{slug}">{escape(desc)}</span></div>')
    abs_html = '\n'.join(abs_items)

    evo_html    = build_evo_chain_header(evolutions, name, name_map, all_names, name_to_species)
    family_html = build_family_web(name, evolutions, name_map, all_names,
                                   species_forms_map, name_to_species, species_id_map)
    evo_section = (f'<div class="evo-combined">{evo_html}{family_html}</div>'
                   if (evo_html or family_html) else '')

    # ── Dex Entry + Related Items section ──────────────────────────
    dex_entry_html = (f'<p class="dex-entry-text">{escape(dex_entry)}</p>'
                      if dex_entry else '<p class="dex-entry-empty">No Pokédex entry available.</p>')

    # Collect regular items: evo-chain items first, then any custom ones
    evo_items     = collect_evo_items(evolutions)
    regular_items = list(dict.fromkeys(evo_items + list(custom_items)))  # dedup, preserve order

    # Collect mega stones for every species in the evo family (pre-evos share stones too).
    # Build the full set of species names present in the chain.
    chain_species = {species_name}
    for evo in evolutions:
        chain_species.add(evo.get('from', ''))
        chain_species.add(evo.get('to', ''))
    chain_species.discard('')
    # Traverse current species first, then the rest (deterministic order)
    ordered_chain = [species_name] + sorted(chain_species - {species_name})
    mega_stone_items = []
    seen_stones = set()
    for chain_name in ordered_chain:
        for form_name, _ in find_extra_forms(chain_name, all_names):
            stone = MEGA_STONE_MAP.get(form_name)
            if stone and stone not in seen_stones:
                seen_stones.add(stone)
                mega_stone_items.append(stone)
    # Also include the stone if the current page IS itself a mega form
    own_stone = MEGA_STONE_MAP.get(name)
    if own_stone and own_stone not in seen_stones:
        seen_stones.add(own_stone)
        mega_stone_items.append(own_stone)

    def _item_node(item):
        LOCAL_SPRITES = {"Linking Cord": "../sprites/items/linking-cord.png"}
        if item in LOCAL_SPRITES:
            src_pa = LOCAL_SPRITES[item]
            onerr_local = "this.onerror=null;this.style.display='none'"
            icon = f'<img class="item-icon" src="{src_pa}" alt="{escape(item)}" onerror="{onerr_local}">'
            label = f'<span class="item-name">{escape(item)}</span>'
            return f'<div class="item-entry">{icon}{label}</div>'
        slug_pa = item_slug_pokeapi(item)   # PokeAPI  — primary
        slug_sd = item_slug(item)           # Showdown — fallback
        area    = ITEM_LOCATIONS.get(item)
        src_pa  = f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/{slug_pa}.png'
        src_sd  = f'https://play.pokemonshowdown.com/sprites/itemicons/{slug_sd}.png'
        # Two-stage fallback: PokeAPI → Showdown → hide
        onerr   = (f"if(!this.dataset.tried){{this.dataset.tried=1;this.src='{src_sd}'}}"
                   f"else{{this.onerror=null;this.style.display='none'}}")
        icon    = (f'<img class="item-icon" src="{src_pa}" alt="{escape(item)}" onerror="{onerr}">')
        label   = f'<span class="item-name">{escape(item)}</span>'
        if area:
            return (f'<a href="../areas/{area}.html" class="item-entry item-entry-link">'
                    f'{icon}{label}</a>')
        return f'<div class="item-entry">{icon}{label}</div>'

    # Flat combined list — regular items first, then mega stones. No sub-labels.
    all_items_combined = list(dict.fromkeys(regular_items + mega_stone_items))
    if all_items_combined:
        nodes = ''.join(_item_node(i) for i in all_items_combined)
        items_body_html = f'<div class="items-list">{nodes}</div>'
    else:
        items_body_html = '<p class="dex-entry-empty">—</p>'

    # Embed move list as JS
    lv_moves    = [{'level':m['level'],'slug':move_slug(m['move']),'name':m['move']} for m in moves.get('levelup',[])]
    egg_moves   = [{'slug':move_slug(m),'name':m} for m in moves.get('egg',[])]
    tm_moves    = [{'slug':move_slug(m),'name':m} for m in moves.get('tm',[])]
    tutor_moves = [{'slug':move_slug(m),'name':m} for m in moves.get('tutor',[])]
    move_data_js = json.dumps({'levelup':lv_moves,'egg':egg_moves,'tm':tm_moves,'tutor':tutor_moves}, separators=(',',':'))

    # Bake move details (type/power/acc/pp/desc) for this Pokémon's moves at generation time.
    # This makes the learnset work on file:// where fetch() is blocked by the browser.
    all_slugs = {r['slug'] for r in lv_moves + egg_moves + tm_moves + tutor_moves}
    baked_moves: dict = {}
    if move_db:
        for slug in all_slugs:
            entry = move_db.get(slug)
            if entry and entry.get('type', '?') != '?':
                desc = entry.get('desc', '')
                # Substitute $effect_chance placeholder if we have the value stored;
                # otherwise strip it cleanly so it never shows raw in the UI.
                effect_chance = entry.get('effect_chance')
                if '$effect_chance' in desc:
                    if effect_chance:
                        desc = desc.replace('$effect_chance', str(effect_chance))
                    else:
                        # Remove the placeholder (e.g. "30% chance" → just strip token)
                        import re as _re
                        desc = _re.sub(r'\$effect_chance%?', '??%', desc)
                baked_moves[slug] = {
                    'name':     entry.get('name', slug),
                    'type':     entry.get('type', '?'),
                    'category': entry.get('category', 'status'),
                    'power':    entry.get('power'),
                    'accuracy': entry.get('accuracy'),
                    'pp':       entry.get('pp'),
                    'desc':     desc,
                }
    baked_move_db_js = json.dumps(baked_moves, separators=(',',':'))

    strategy_parts = []
    if isinstance(strategy, dict):
        summary = str(strategy.get('summary', '')).strip()
        showdown = str(strategy.get('showdown', '')).strip()
        bullets = strategy.get('bullets', [])

        if summary:
            strategy_parts.append(f'<p class="strategy-text">{escape(summary)}</p>')

        if showdown:
            strategy_parts.append(
                '<div class="strategy-set-box">'
                '<div class="strategy-set-head">'
                '<span class="strategy-set-label">Showdown Set</span>'
                '<button class="strategy-export-btn" type="button" onclick="exportStrategySet(this)">Export</button>'
                '</div>'
                f'<pre class="strategy-set-code" tabindex="0">{escape(showdown)}</pre>'
                '</div>'
            )

        bullet_items = []
        if isinstance(bullets, list):
            for bullet in bullets:
                text = str(bullet).strip()
                if text:
                    bullet_items.append(f'<li>{escape(text)}</li>')
        if bullet_items:
            strategy_parts.append(
                '<div class="strategy-notes-wrap">'
                '<div class="strategy-notes-title">Notes</div>'
                f'<ul class="strategy-bullets">{"".join(bullet_items)}</ul>'
                '</div>'
            )
    elif isinstance(strategy, str):
        text = strategy.strip()
        if text:
            strategy_parts.append(f'<p class="strategy-text">{escape(text)}</p>')

    if not strategy_parts:
        if notes:
            strategy_parts.append(f'<p class="strategy-text">{escape(notes)}</p>')
        else:
            strategy_parts.append('<p class="strategy-empty">No strategy notes yet.</p>')

    strategy_html = ''.join(strategy_parts)

    all_type_list = ['Normal','Fire','Water','Electric','Grass','Ice','Fighting','Poison',
                     'Ground','Flying','Psychic','Bug','Rock','Ghost','Dragon','Dark','Steel','Fairy']
    type_pills_html = ''.join(
        f'<span class="mv-tp" data-type="{t}" style="background:{TYPE_COLORS.get(t,("#888",""))[0]};color:{TYPE_COLORS.get(t,("","#fff"))[1]}" onclick="toggleMvType(\'{t}\',this)">{t}</span>'
        for t in all_type_list
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{display} — Pokédex — Jay's Romhack</title>
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{{--bg:#161A1F;--surface:#20262D;--surface2:#272E37;--border:#313943;--text:#E9EDF1;--text-muted:#AAB2BA;--accent:#8E9CAA;--main:#AEB8C2;--highlight:#C8D2DB;}}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;font-size:14px;line-height:1.6;min-height:100vh;}}

  /* HEADER */
  .page-header{{background:var(--surface);border-bottom:2px solid var(--border);padding:0 32px;display:flex;align-items:center;justify-content:space-between;height:52px;position:sticky;top:0;z-index:100;}}
  .romhack-title{{font-family:'Press Start 2P',monospace;font-size:11px;color:var(--accent);letter-spacing:1px;text-shadow:0 0 20px rgba(142,156,170,0.3);white-space:nowrap;flex-shrink:0;}}
  .header-right{{display:flex;align-items:center;gap:10px;flex-shrink:0;}}
  .menu-btn{{display:flex;align-items:center;gap:8px;padding:6px 14px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-family:'DM Mono',monospace;font-size:11px;cursor:pointer;transition:all 0.2s;user-select:none;}}
  .menu-btn:hover{{border-color:var(--main);color:var(--main);}}
  .menu-icon{{display:flex;flex-direction:column;gap:3px;}}
  .menu-icon span{{display:block;width:14px;height:1.5px;background:currentColor;border-radius:1px;}}
  .theme-toggle{{display:flex;align-items:center;gap:8px;padding:6px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;cursor:pointer;transition:all 0.2s;user-select:none;}}
  .theme-toggle:hover{{border-color:var(--accent);}}
  .toggle-track{{width:32px;height:18px;background:var(--border);border-radius:9px;position:relative;transition:background 0.2s;}}
  .toggle-track.active{{background:var(--main);}}
  .toggle-thumb{{width:12px;height:12px;background:white;border-radius:50%;position:absolute;top:3px;left:3px;transition:transform 0.2s;box-shadow:0 1px 3px rgba(0,0,0,0.3);}}
  .toggle-track.active .toggle-thumb{{transform:translateX(14px);}}
  .theme-label{{font-family:'DM Mono',monospace;font-size:11px;color:var(--text-muted);}}
  .menu-overlay{{position:fixed;top:72px;right:32px;width:220px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px;z-index:200;display:none;box-shadow:0 8px 32px rgba(0,0,0,0.4);}}
  .menu-overlay.open{{display:block;animation:menuIn .15s ease;}}
  @keyframes menuIn{{from{{opacity:0;transform:translateY(-6px);}}to{{opacity:1;transform:translateY(0);}}}}
  .menu-section-title{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:1px;color:var(--text-muted);text-transform:uppercase;padding:0 8px;margin-bottom:4px;margin-top:12px;}}
  .menu-section-title:first-child{{margin-top:0;}}
  .menu-link{{display:flex;align-items:center;padding:8px;border-radius:6px;font-family:'DM Sans',sans-serif;font-size:13px;color:var(--text);text-decoration:none;transition:all .15s;}}
  .menu-link:hover{{background:rgba(255,255,255,.06);color:var(--main);}}
  .menu-divider{{height:1px;background:var(--border);margin:8px 0;}}

  /* LAYOUT */
  .back-bar{{max-width:1000px;margin:0 auto;padding:20px 32px 0;}}
  .back-link{{font-family:'DM Mono',monospace;font-size:11px;color:var(--text-muted);text-decoration:none;display:inline-flex;align-items:center;gap:6px;transition:color .15s;}}
  .back-link:hover{{color:var(--main);}}
  .page-body{{max-width:1000px;margin:0 auto;padding:20px 32px 80px;display:flex;flex-direction:column;gap:24px;}}

  /* POKEMON HEADER */
  .poke-header{{position:relative;display:grid;grid-template-columns:auto 1fr auto;gap:24px;align-items:center;background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px;}}

  /* Shiny button — hover reveal */
  .shiny-btn{{position:absolute;top:10px;left:10px;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:4px 9px;font-size:15px;line-height:1;cursor:pointer;opacity:0;transition:opacity .2s,background .2s,border-color .2s;z-index:2;color:var(--text);}}
  .poke-header:hover .shiny-btn{{opacity:1;}}
  .shiny-btn.active{{opacity:1!important;background:rgba(248,208,48,.12);border-color:rgba(248,208,48,.45);}}
  .shiny-btn.active::after{{content:'';}}

  /* Sprite */
  .sprite-wrap{{flex-shrink:0;text-align:center;}}
  .sprite-img{{width:128px;height:128px;image-rendering:pixelated;object-fit:contain;transition:transform .15s;}}
  .sprite-img.shiny{{}}

  /* Info */
  .poke-info{{display:flex;flex-direction:column;gap:8px;min-width:160px;}}
  .poke-dex{{font-family:'DM Mono',monospace;font-size:11px;color:var(--text-muted);letter-spacing:1px;}}
  .poke-name{{font-family:'Press Start 2P',monospace;font-size:18px;color:var(--text);letter-spacing:1px;line-height:1.4;}}
  .poke-genus{{font-family:'DM Mono',monospace;font-size:11px;color:var(--text-muted);}}
  .poke-types-row{{display:flex;gap:6px;flex-wrap:wrap;}}
  .type-badge{{font-family:'DM Mono',monospace;font-weight:500;padding:3px 10px;border-radius:4px;letter-spacing:.3px;}}
  .poke-flags{{display:flex;gap:6px;flex-wrap:wrap;}}
  .page-flag{{font-family:'DM Mono',monospace;font-size:10px;padding:3px 8px;border-radius:4px;font-weight:500;}}
  .flag-mod{{background:rgba(201,168,106,.15);color:#C9A86A;border:1px solid rgba(201,168,106,.35);}}
  .flag-meta{{background:rgba(120,170,220,.15);color:#78AADC;border:1px solid rgba(120,170,220,.35);}}

  /* EVO CHAIN in header — larger */
  .evo-combined{{display:flex;flex-direction:column;gap:8px;justify-content:center;}}
  .evo-chain-h{{display:flex;align-items:center;flex-wrap:wrap;gap:4px;justify-content:flex-end;}}
  .evo-c-node{{display:flex;flex-direction:column;align-items:center;gap:5px;text-decoration:none;color:var(--text-muted);transition:color .15s;padding:5px;border-radius:8px;}}
  .evo-c-node:hover{{color:var(--main);background:rgba(255,255,255,.04);}}
  .evo-c-cur{{color:var(--highlight)!important;}}
  .evo-c-cur .evo-c-spr{{border-color:var(--main);}}
  .evo-c-spr{{width:68px;height:68px;image-rendering:pixelated;object-fit:contain;background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:4px;}}
  .evo-c-lbl{{font-family:'DM Mono',monospace;font-size:10px;text-align:center;max-width:72px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
  .evo-c-arr{{display:flex;flex-direction:column;align-items:center;gap:1px;color:var(--text-muted);padding:0 3px;}}
  .evo-c-mth{{font-family:'DM Mono',monospace;font-size:9px;color:var(--accent);text-align:center;white-space:nowrap;}}
  .evo-c-arw{{font-size:16px;line-height:1;}}
  .evo-c-wide-arr{{font-size:20px;align-self:center;padding:0 2px;flex-shrink:0;}}
  .evo-c-branches{{display:flex;flex-direction:column;gap:6px;}}
  .evo-c-branches-wide{{display:grid;grid-template-columns:repeat(3,auto);gap:8px 6px;align-items:start;}}
  .evo-c-wide-item{{display:flex;flex-direction:column;align-items:center;gap:1px;}}
  .evo-c-wide-item .evo-c-mth{{margin-bottom:2px;}}
  .evo-c-branch{{display:flex;align-items:center;}}
  .family-web{{display:flex;flex-wrap:wrap;gap:4px;align-items:flex-start;padding-top:8px;border-top:1px solid var(--border);}}

  /* SECONDARY ROW */
  .poke-secondary{{display:grid;grid-template-columns:1fr 1fr;gap:20px;}}
  .poke-section{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px 22px;display:flex;flex-direction:column;gap:12px;}}
  .section-head{{display:flex;align-items:center;gap:14px;}}
  .section-lbl{{font-family:'DM Mono',monospace;font-size:10px;font-weight:500;letter-spacing:1.5px;text-transform:uppercase;color:var(--text-muted);flex-shrink:0;}}
  .section-line{{flex:1;height:1px;background:var(--border);}}

  /* Stats */
  .stat-row{{display:grid;grid-template-columns:36px 36px 1fr;align-items:center;gap:10px;}}
  .stat-lbl{{font-family:'DM Mono',monospace;font-size:11px;color:var(--text-muted);text-align:right;}}
  .stat-val{{font-family:'DM Mono',monospace;font-size:12px;font-weight:500;text-align:right;}}
  .stat-track{{height:8px;background:var(--surface2);border-radius:4px;overflow:hidden;}}
  .stat-fill{{height:100%;border-radius:4px;}}
  .stat-total{{display:flex;justify-content:space-between;align-items:center;padding-top:10px;border-top:1px solid var(--border);margin-top:4px;}}
  .stat-total-lbl{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--text-muted);}}
  .stat-total-val{{font-family:'DM Mono',monospace;font-size:13px;font-weight:500;color:var(--highlight);}}

  /* Abilities — sized for max 3 items */
  .abilities-list{{display:flex;flex-direction:column;gap:8px;flex:1;}}
  .ability-item{{padding:10px 14px;background:var(--surface2);border-radius:8px;display:flex;flex-direction:column;gap:4px;flex:1;min-height:0;}}
  .ability-name-row{{display:flex;align-items:center;gap:8px;}}
  .ability-name{{font-family:'DM Mono',monospace;font-size:12px;color:var(--highlight);font-weight:500;}}
  .ability-desc{{font-size:12px;color:var(--text-muted);line-height:1.5;}}
  .ability-ha{{border:1px dashed var(--border);background:transparent;}}
  .ability-ha .ability-name{{color:var(--text-muted);}}
  .ha-tag{{font-family:'DM Mono',monospace;font-size:9px;color:var(--accent);padding:1px 5px;border:1px solid var(--border);border-radius:3px;letter-spacing:.5px;flex-shrink:0;}}

  /* LEARNSET */
  .learnset-wrap{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:20px 22px;display:flex;flex-direction:column;gap:14px;}}
  .mv-filters{{display:flex;flex-direction:column;gap:8px;}}
  .mv-frow{{display:flex;align-items:center;gap:6px;flex-wrap:wrap;}}
  .mv-fbtn{{font-family:'DM Mono',monospace;font-size:10px;padding:4px 10px;background:var(--surface2);border:1px solid var(--border);border-radius:5px;color:var(--text-muted);cursor:pointer;transition:all .15s;user-select:none;}}
  .mv-fbtn:hover{{color:var(--text);border-color:var(--main);}}
  .mv-fbtn.active{{color:var(--main);border-color:var(--main);background:rgba(174,184,194,.08);}}
  .mv-search{{background:var(--surface2);border:1px solid var(--border);border-radius:5px;padding:5px 10px;color:var(--text);font-family:'DM Mono',monospace;font-size:11px;outline:none;width:160px;transition:border-color .2s;}}
  .mv-search::placeholder{{color:var(--text-muted);}}
  .mv-search:focus{{border-color:var(--main);}}
  .mv-tp{{font-family:'DM Mono',monospace;font-size:9px;font-weight:500;padding:2px 7px;border-radius:3px;cursor:pointer;opacity:.35;transition:opacity .15s,transform .1s;user-select:none;}}
  .mv-tp:hover{{opacity:.6;}}
  .mv-tp.active{{opacity:1;transform:scale(1.06);}}
  .mv-count{{font-family:'DM Mono',monospace;font-size:10px;color:var(--text-muted);margin-left:auto;flex-shrink:0;}}
  .mv-sep{{width:1px;background:var(--border);height:18px;flex-shrink:0;}}

  .mv-table-wrap{{overflow-x:auto;}}
  .mv-table{{width:100%;border-collapse:collapse;min-width:640px;}}
  .mv-table th{{font-family:'DM Mono',monospace;font-size:12px;letter-spacing:.5px;text-transform:uppercase;color:var(--text);padding:10px 10px;text-align:left;border-bottom:2px solid var(--border);white-space:nowrap;user-select:none;}}
  .mv-table th.num{{text-align:right;}}
  .mv-row td{{padding:7px 10px;border-bottom:1px solid rgba(49,57,67,.4);vertical-align:middle;font-size:13px;}}
  .mv-row:hover td{{background:rgba(255,255,255,.025);}}
  .mv-row:last-child td{{border-bottom:none;}}
  .mv-td-name{{font-family:'DM Mono',monospace;font-size:12px;color:var(--highlight);white-space:nowrap;}}
  .mv-td-num{{font-family:'DM Mono',monospace;font-size:11px;text-align:right;color:var(--text-muted);}}
  .mv-td-desc{{font-size:12px;color:var(--text-muted);max-width:280px;}}
  .mv-src{{font-family:'DM Mono',monospace;font-size:9px;font-weight:500;padding:2px 6px;border-radius:3px;white-space:nowrap;}}
  .mv-tbadge{{font-family:'DM Mono',monospace;font-size:9px;font-weight:500;padding:2px 6px;border-radius:3px;white-space:nowrap;}}
  .mv-cat{{font-family:'DM Mono',monospace;font-size:11px;font-weight:500;}}
  .mv-cat-img{{height:16px;image-rendering:pixelated;vertical-align:middle;display:block;}}
  .mv-empty-row{{font-family:'DM Mono',monospace;font-size:12px;color:var(--text-muted);text-align:center;padding:24px !important;}}

  /* DEX ENTRY + STRATEGY + RELATED ITEMS */
  .dex-items-row{{display:flex;flex-direction:column;background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden;}}
  .dex-top-grid{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);}}
  .dex-entry-section,.strategy-section{{padding:20px 22px;display:flex;flex-direction:column;gap:10px;min-width:0;}}
  .strategy-section{{border-left:1px solid var(--border);}}
  .row-divider{{height:1px;background:var(--border);flex-shrink:0;}}
  .items-section{{padding:20px 22px;display:flex;flex-direction:column;gap:10px;}}
  .dex-entry-text{{font-size:13px;color:var(--text-muted);line-height:1.75;font-style:italic;}}
  .dex-entry-empty{{font-family:'DM Mono',monospace;font-size:12px;color:var(--text-muted);opacity:.5;}}
  .strategy-text{{font-size:13px;color:var(--text-muted);line-height:1.75;}}
  .strategy-empty{{font-family:'DM Mono',monospace;font-size:12px;color:var(--text-muted);opacity:.5;}}
  .strategy-set-box{{display:flex;flex-direction:column;gap:10px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;padding:12px 14px;}}
  .strategy-set-head{{display:flex;align-items:center;justify-content:space-between;gap:10px;}}
  .strategy-set-label{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--text-muted);}}
  .strategy-export-btn{{padding:5px 10px;background:transparent;border:1px solid var(--border);border-radius:6px;color:var(--text-muted);font-family:'DM Mono',monospace;font-size:10px;cursor:pointer;transition:all .15s;}}
  .strategy-export-btn:hover,.strategy-export-btn.copied{{border-color:var(--main);color:var(--main);}}
  .strategy-set-code{{margin:0;padding:10px 12px;background:rgba(0,0,0,.12);border:1px solid rgba(255,255,255,.05);border-radius:8px;font-family:'DM Mono',monospace;font-size:11px;line-height:1.7;color:var(--highlight);white-space:pre-wrap;word-break:break-word;user-select:text;}}
  .strategy-set-code.is-selected{{border-color:var(--main);box-shadow:0 0 0 1px rgba(174,184,194,.18) inset;}}
  .strategy-notes-wrap{{display:flex;flex-direction:column;gap:8px;}}
  .strategy-notes-title{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:1px;text-transform:uppercase;color:var(--text-muted);}}
  .strategy-bullets{{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:6px;color:var(--text-muted);font-size:13px;line-height:1.65;}}
  .strategy-bullets li::marker{{color:var(--main);}}
  .items-list{{display:flex;flex-wrap:wrap;gap:6px;}}
  .item-entry{{display:flex;align-items:center;gap:10px;padding:6px 10px;background:var(--surface2);border-radius:7px;text-decoration:none;}}
  .item-entry-link{{cursor:pointer;transition:border-color .15s,background .15s;border:1px solid transparent;}}
  .item-entry-link:hover{{border-color:var(--main);background:rgba(255,255,255,.04);}}
  .item-icon{{width:24px;height:24px;image-rendering:pixelated;object-fit:contain;flex-shrink:0;}}
  .item-name{{font-family:'DM Mono',monospace;font-size:12px;color:var(--highlight);}}
  body.light .dex-items-row{{background:#F5EBDD;border-color:#D4C4A8;}}
  body.light .strategy-section{{border-color:#D4C4A8;}}
  body.light .strategy-set-box{{background:#EDE0CC;border-color:#D4C4A8;}}
  body.light .strategy-set-code{{background:rgba(255,255,255,.35);border-color:rgba(122,107,85,.12);}}
  body.light .row-divider{{background:#D4C4A8;}}
  body.light .item-entry{{background:#EDE0CC;}}

  /* LIGHT */
  body.light{{--bg:#FCF8F1;--surface:#F5EBDD;--surface2:#EDE0CC;--border:#D4C4A8;--text:#2C2416;--text-muted:#7A6B55;--accent:#C9A86A;--main:#B8944E;--highlight:#7a5020;}}
  body.light .page-header{{background:#F5EBDD;border-color:#D4C4A8;}}
  body.light .romhack-title{{color:#C9A86A;text-shadow:none;}}
  body.light .menu-overlay{{background:#F5EBDD;box-shadow:0 8px 32px rgba(74,64,50,.15);}}
  body.light .menu-link{{color:#4A4032;}} body.light .menu-link:hover{{background:rgba(0,0,0,.05);color:#C9A86A;}}
  body.light .menu-btn{{background:#EDE0CC;border-color:#D4C4A8;color:#4A4032;}} body.light .menu-btn:hover{{border-color:#C9A86A;color:#C9A86A;}}
  body.light .theme-toggle{{background:#EDE0CC;border-color:#D4C4A8;}}
  body.light .poke-header{{background:#F5EBDD;border-color:#D4C4A8;}}
  body.light .evo-c-spr{{background:#EDE0CC;border-color:#D4C4A8;}} body.light .evo-c-cur .evo-c-spr{{border-color:#C9A86A;}}
  body.light .poke-section, body.light .learnset-wrap{{background:#F5EBDD;border-color:#D4C4A8;}}
  body.light .ability-item{{background:#EDE0CC;}} body.light .ability-ha{{background:transparent;border-color:#D4C4A8;}}
  body.light .stat-track{{background:#EDE0CC;}}
  body.light .mv-fbtn{{background:#EDE0CC;border-color:#D4C4A8;}} body.light .mv-fbtn.active{{background:rgba(201,168,106,.1);border-color:#C9A86A;color:#B8944E;}}
  body.light .mv-search{{background:#EDE0CC;border-color:#D4C4A8;color:#2C2416;}} body.light .mv-search:focus{{border-color:#C9A86A;}}
  body.light .mv-row:hover td{{background:rgba(0,0,0,.02);}} body.light .mv-row td{{border-color:rgba(212,196,168,.5);}}
  body.light .mv-table th{{border-color:#D4C4A8;}}
  @media(max-width:720px){{
    .poke-header{{grid-template-columns:1fr;}}
    .poke-secondary{{grid-template-columns:1fr;}}
    .evo-chain-h{{justify-content:flex-start;}}
    .dex-top-grid{{grid-template-columns:1fr;}}
    .strategy-section{{border-left:none;border-top:1px solid var(--border);}}
  }}
</style>
</head>
<body>

<header class="page-header">
  <span class="romhack-title">Jay's Romhack</span>
  <div class="header-right">
    <div class="theme-toggle" onclick="toggleTheme()">
      <div class="toggle-track" id="toggleTrack"><div class="toggle-thumb"></div></div>
      <span class="theme-label" id="themeLabel">Dark</span>
    </div>
    <div class="menu-btn" onclick="toggleMenu()">
      <div class="menu-icon"><span></span><span></span><span></span></div>
      Menu
    </div>
  </div>
</header>

<div class="menu-overlay" id="menuOverlay">
  <div class="menu-section-title">Navigation</div>
  <a href="../index.html" class="menu-link">Home</a>
  <a href="../areadex.html" class="menu-link">Area Sheets</a>
  <a href="../pokedex.html" class="menu-link">Pokedex</a>
  <a href="../trainerdex.html" class="menu-link">TrainerDex</a>
  <a href="../itemdex.html" class="menu-link">ItemDex</a>
  <a href="../progression.html" class="menu-link">Progression</a>
  <a href="../mechanics.html" class="menu-link">Mechanics</a>
  <a href="../calculator.html" class="menu-link">Battle Calculator</a>
  <a href="../tracker.html" class="menu-link">Nuzlocke Tracker</a>
</div>

<div class="back-bar"><a href="../pokedex.html" class="back-link">← Back to Pokédex</a></div>

<div class="page-body">

  <div class="poke-header">
    <button class="shiny-btn" id="shinyBtn" onclick="toggleShiny()" title="Toggle Shiny">✨</button>
    <div class="sprite-wrap">
      <img class="sprite-img" id="mainSprite" src="{sprite_url}" alt="{display}"
           data-fallback="{sprite_fallback}"
           onerror="if(!this.dataset.tried){{this.dataset.tried=1;this.src=this.dataset.fallback}}else{{this.onerror=null;this.src='https://play.pokemonshowdown.com/sprites/gen5/substitute.png'}}">
    </div>
    <div class="poke-info">
      <span class="poke-dex">#{dex_num} · Gen {generation} · {genus}</span>
      <h1 class="poke-name">{display}</h1>
      <div class="poke-types-row">{types_html}</div>
      {f'<div class="poke-flags">{flags_html}</div>' if flags_html else ''}
    </div>
    {f'<div>{evo_section}</div>' if evo_section else '<div></div>'}
  </div>

  <div class="dex-items-row">
    <div class="dex-top-grid">
      <div class="dex-entry-section">
        <div class="section-head"><span class="section-lbl">Pokédex Entry</span><div class="section-line"></div></div>
        {dex_entry_html}
      </div>
      <div class="strategy-section">
        <div class="section-head"><span class="section-lbl">Strategy</span><div class="section-line"></div></div>
        {strategy_html}
      </div>
    </div>
    <div class="row-divider"></div>
    <div class="items-section">
      <div class="section-head"><span class="section-lbl">Related Items</span><div class="section-line"></div></div>
      {items_body_html}
    </div>
  </div>

  <div class="poke-secondary">
    <div class="poke-section">
      <div class="section-head"><span class="section-lbl">Base Stats</span><div class="section-line"></div></div>
      {stats_html}
    </div>
    <div class="poke-section">
      <div class="section-head"><span class="section-lbl">Abilities</span><div class="section-line"></div></div>
      <div class="abilities-list">{abs_html}</div>
    </div>
  </div>

  <div class="learnset-wrap">
    <div class="section-head"><span class="section-lbl">Learnset</span><div class="section-line"></div></div>
    <div class="mv-filters">
      <div class="mv-frow">
        <button class="mv-fbtn active" data-group="source" data-val="all" onclick="toggleSrc(this)">All</button>
        <button class="mv-fbtn" data-group="source" data-val="levelup" onclick="toggleSrc(this)">Level Up</button>
        <button class="mv-fbtn" data-group="source" data-val="tm" onclick="toggleSrc(this)">TM / HM</button>
        <button class="mv-fbtn" data-group="source" data-val="egg" onclick="toggleSrc(this)">Egg</button>
        <button class="mv-fbtn" data-group="source" data-val="tutor" onclick="toggleSrc(this)">Tutor</button>
        <div class="mv-sep"></div>
        <button class="mv-fbtn active" data-group="cat" data-val="all" onclick="toggleCat(this)">All</button>
        <button class="mv-fbtn" data-group="cat" data-val="physical" onclick="toggleCat(this)" style="color:#F5A073">Phys</button>
        <button class="mv-fbtn" data-group="cat" data-val="special" onclick="toggleCat(this)" style="color:#86BFFF">Spec</button>
        <button class="mv-fbtn" data-group="cat" data-val="status" onclick="toggleCat(this)" style="color:#96D9D6">Stat</button>
        <input class="mv-search" id="mvSearch" type="text" placeholder="Search moves…" oninput="renderTable()">
        <span class="mv-count" id="mvCount"></span>
      </div>
      <div class="mv-frow">{type_pills_html}</div>
    </div>
    <div class="mv-table-wrap">
      <table class="mv-table">
        <thead><tr>
          <th>Src</th><th>Move</th><th>Type</th><th>Cat</th>
          <th class="num">Pwr</th><th class="num">Acc</th><th class="num">PP</th><th>Description</th>
        </tr></thead>
        <tbody id="mvTableBody"><tr><td colspan="8" class="mv-empty-row">Loading…</td></tr></tbody>
      </table>
    </div>
  </div>
</div>

<script>
const MOVE_DATA = {move_data_js};
// Move details baked in at generation time — works on file:// without a server.
// If moves.json loads successfully at runtime it will override (more complete data).
const BAKED_MOVE_DB = {baked_move_db_js};
const SPRITE_N = "{sprite_url}";
const SPRITE_S = "{shiny_url}";
let shiny = false;
let moveDb = BAKED_MOVE_DB, abilityDb = {{}};
let tableRows = [];
let activeSources = new Set();   // empty = all
let activeCats    = new Set();
let activeTypes   = new Set();

const TC = {{Normal:'#A8A878',Fire:'#F08030',Water:'#6890F0',Electric:'#F8D030',Grass:'#78C850',Ice:'#98D8D8',Fighting:'#C03028',Poison:'#A040A0',Ground:'#E0C068',Flying:'#A890F0',Psychic:'#F85888',Bug:'#A8B820',Rock:'#B8A038',Ghost:'#705898',Dragon:'#7038F8',Dark:'#705848',Steel:'#B8B8D0',Fairy:'#EE99AC'}};
const TT = {{Electric:'#333',Ice:'#333',Ground:'#333',Steel:'#333'}};
const CS = {{physical:{{c:'#F5A073',l:'Phys'}},special:{{c:'#86BFFF',l:'Spec'}},status:{{c:'#96D9D6',l:'Stat'}}}};
const SS = {{levelup:{{c:'#86BFFF',b:'rgba(134,191,255,.12)',l:'LV'}},tm:{{c:'#A878FA',b:'rgba(168,120,250,.12)',l:'TM'}},egg:{{c:'#F5A073',b:'rgba(245,160,115,.12)',l:'EGG'}},tutor:{{c:'#78C850',b:'rgba(120,200,80,.12)',l:'TUT'}}}};

function exportStrategySet(btn) {{
  if (!btn) return;
  const wrap = btn.closest('.strategy-set-box');
  const code = wrap ? wrap.querySelector('.strategy-set-code') : null;
  if (!code) return;

  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(code);
  selection.removeAllRanges();
  selection.addRange(range);

  code.classList.add('is-selected');
  if (code._clearSelectionTimer) clearTimeout(code._clearSelectionTimer);
  code._clearSelectionTimer = setTimeout(() => code.classList.remove('is-selected'), 1400);

  const resetBtn = (copied) => {{
    btn.textContent = copied ? 'Copied' : 'Export';
    btn.classList.toggle('copied', copied);
    setTimeout(() => {{
      btn.textContent = 'Export';
      btn.classList.remove('copied');
    }}, 1200);
  }};

  if (navigator.clipboard && window.isSecureContext) {{
    navigator.clipboard.writeText(code.textContent).then(() => resetBtn(true)).catch(() => resetBtn(false));
  }} else {{
    resetBtn(false);
  }}
}}

// ── SHINY ──
const spriteEl = document.getElementById('mainSprite');
function toggleShiny() {{
  shiny = !shiny;
  // Main sprite
  spriteEl.src = shiny ? SPRITE_S : SPRITE_N;
  spriteEl.classList.toggle('shiny', shiny);
  // Evo chain sprites (includes family-web nodes, which also use .evo-c-spr)
  document.querySelectorAll('.evo-c-spr').forEach(img => {{
    img.src = shiny ? img.dataset.shiny : img.dataset.normal;
  }});
  // Button state
  document.getElementById('shinyBtn').classList.toggle('active', shiny);
}}

function esc(s) {{ return s ? String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') : ''; }}
function srcBadge(s, lv) {{
  const x = SS[s]||{{c:'#aaa',b:'rgba(0,0,0,.1)',l:s}};
  const label = (s==='levelup'&&lv) ? `Lv.${{lv}}` : x.l;
  return `<span class="mv-src" style="color:${{x.c}};background:${{x.b}}">${{label}}</span>`;
}}
function typeBadge(t) {{ if(!t||t==='?') return '<span class="mv-tbadge" style="background:#444;color:#aaa">?</span>'; return `<span class="mv-tbadge" style="background:${{TC[t]||'#888'}};color:${{TT[t]||'#fff'}}">${{t}}</span>`; }}
const CAT_IMGS = {{
  physical: 'https://play.pokemonshowdown.com/sprites/categories/Physical.png',
  special:  'https://play.pokemonshowdown.com/sprites/categories/Special.png',
  status:   'https://play.pokemonshowdown.com/sprites/categories/Status.png',
}};
function catBadge(c) {{
  const src = CAT_IMGS[c];
  if (src) return `<img class="mv-cat-img" src="${{src}}" alt="${{c}}" title="${{c[0].toUpperCase()+c.slice(1)}}">`;
  return `<span class="mv-cat" style="color:#aaa">?</span>`;
}}

// ── DATA LOADING ──
// moveDb is pre-initialised from BAKED_MOVE_DB so the table renders immediately.
// The fetches below succeed only when served via a local server (not file://) and
// give us the full move database; they are silent no-ops on file://.
async function init() {{
  try {{
    const fetched = await fetch('../data/moves.json').then(r=>r.json());
    if (fetched && Object.keys(fetched).length > 0) moveDb = fetched;
  }} catch(e) {{}}
  try {{
    abilityDb = await fetch('../data/abilities.json').then(r=>r.json());
    document.querySelectorAll('.ability-item').forEach(el => {{
      const slug = el.dataset.slug;
      const info = abilityDb[slug];
      if (info) {{
        const desc = typeof info === 'string' ? info : (info.desc || info.short_effect || '');
        const descEl = el.querySelector('.ability-desc');
        if (descEl && desc) descEl.textContent = desc;
      }}
    }});
  }} catch(e) {{}}
  buildRows();
  renderTable();
}}

function buildRows() {{
  tableRows = [];
  function add(list, src) {{
    list.forEach(m => {{
      const db = moveDb[m.slug] || {{}};
      tableRows.push({{src, level: src==='levelup'?m.level:null, name: db.name||m.name, slug: m.slug,
        type: db.type||'?', cat: db.category||'status', power: db.power??null,
        acc: db.accuracy??null, pp: db.pp??null, desc: db.desc||''}});
    }});
  }}
  add(MOVE_DATA.levelup,'levelup'); add(MOVE_DATA.egg,'egg'); add(MOVE_DATA.tm,'tm'); add(MOVE_DATA.tutor,'tutor');
  const ord={{levelup:0,egg:1,tm:2,tutor:3}};
  tableRows.sort((a,b) => {{
    if(a.src!==b.src) return (ord[a.src]||9)-(ord[b.src]||9);
    if(a.src==='levelup') return (a.level||0)-(b.level||0);
    return a.name.localeCompare(b.name);
  }});
}}

function getFiltered() {{
  const q = document.getElementById('mvSearch').value.toLowerCase().trim();
  return tableRows.filter(r => {{
    if (activeSources.size > 0 && !activeSources.has(r.src)) return false;
    if (activeCats.size > 0 && !activeCats.has(r.cat)) return false;
    if (activeTypes.size > 0 && !activeTypes.has(r.type)) return false;
    if (q && !r.name.toLowerCase().includes(q)) return false;
    return true;
  }});
}}

function renderTable() {{
  const rows = getFiltered();
  const tbody = document.getElementById('mvTableBody');
  document.getElementById('mvCount').textContent = rows.length + ' move' + (rows.length!==1?'s':'');
  if (!rows.length) {{ tbody.innerHTML = '<tr><td colspan="8" class="mv-empty-row">No moves match filters.</td></tr>'; return; }}
  tbody.innerHTML = rows.map(r => `<tr class="mv-row">
    <td>${{srcBadge(r.src, r.level)}}</td>
    <td class="mv-td-name">${{esc(r.name)}}</td>
    <td>${{typeBadge(r.type)}}</td>
    <td>${{catBadge(r.cat)}}</td>
    <td class="mv-td-num">${{r.power??'—'}}</td>
    <td class="mv-td-num">${{r.acc!=null?r.acc+'%':'—'}}</td>
    <td class="mv-td-num">${{r.pp??'—'}}</td>
    <td class="mv-td-desc">${{esc(r.desc)}}</td>
  </tr>`).join('');
}}

// ── MULTI-SELECT FILTERS (union) ──
function toggleSrc(el) {{
  const val = el.dataset.val;
  if (val === 'all') {{
    activeSources.clear();
    document.querySelectorAll('[data-group="source"]').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
  }} else {{
    // Remove "All" active
    document.querySelector('[data-group="source"][data-val="all"]').classList.remove('active');
    if (activeSources.has(val)) {{
      activeSources.delete(val);
      el.classList.remove('active');
    }} else {{
      activeSources.add(val);
      el.classList.add('active');
    }}
    // If none left, re-activate All
    if (activeSources.size === 0) {{
      document.querySelector('[data-group="source"][data-val="all"]').classList.add('active');
    }}
  }}
  renderTable();
}}

function toggleCat(el) {{
  const val = el.dataset.val;
  if (val === 'all') {{
    activeCats.clear();
    document.querySelectorAll('[data-group="cat"]').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
  }} else {{
    document.querySelector('[data-group="cat"][data-val="all"]').classList.remove('active');
    if (activeCats.has(val)) {{
      activeCats.delete(val);
      el.classList.remove('active');
    }} else {{
      activeCats.add(val);
      el.classList.add('active');
    }}
    if (activeCats.size === 0) {{
      document.querySelector('[data-group="cat"][data-val="all"]').classList.add('active');
    }}
  }}
  renderTable();
}}

function toggleMvType(type, el) {{
  if (activeTypes.has(type)) {{
    activeTypes.delete(type);
    el.classList.remove('active');
  }} else {{
    activeTypes.add(type);
    el.classList.add('active');
  }}
  renderTable();
}}

// ── THEME ──
const toggleTrack=document.getElementById('toggleTrack');
const themeLabel=document.getElementById('themeLabel');
const menu=document.getElementById('menuOverlay');
function toggleTheme(){{ document.body.classList.toggle('light'); const l=document.body.classList.contains('light'); toggleTrack.classList.toggle('active',l); themeLabel.textContent=l?'Light':'Dark'; localStorage.setItem('theme',l?'light':'dark'); }}
function toggleMenu(){{ menu.classList.toggle('open'); }}
document.addEventListener('click',e=>{{ if(!e.target.closest('.menu-overlay')&&!e.target.closest('.menu-btn')) menu.classList.remove('open'); }});
if(localStorage.getItem('theme')==='light'){{ document.body.classList.add('light'); toggleTrack.classList.add('active'); themeLabel.textContent='Light'; }}

init();
</script>
</body>
</html>'''


# ── MAIN ─────────────────────────────────────────────────────────
def main():
    print("Loading data…")
    with open(DATA_DIR / 'pokemon.json', encoding='utf-8') as f:
        pkmn_data = json.load(f)
    with open(DATA_DIR / 'custom.json', encoding='utf-8') as f:
        custom_data = json.load(f)

    custom_map = {c['name']: c for c in custom_data if 'name' in c}

    ability_db = {}
    ability_db_file = DATA_DIR / 'abilities.json'
    if ability_db_file.exists():
        with open(ability_db_file, encoding='utf-8') as f:
            ability_db = json.load(f)
        print(f"  Ability descriptions loaded: {len(ability_db)}")
    else:
        print("  abilities.json not found — ability descriptions will be empty")

    move_db = {}
    move_db_file = DATA_DIR / 'moves.json'
    if move_db_file.exists():
        with open(move_db_file, encoding='utf-8') as f:
            move_db = json.load(f)
        complete = sum(1 for v in move_db.values() if v.get('type', '?') != '?')
        print(f"  Move DB loaded: {len(move_db)} moves ({complete} complete, {len(move_db)-complete} with type='?')")
    else:
        print("  moves.json not found — run fetch_moves.py to populate")

    # Synthetic base forms missing from pokemon.json
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
    existing_names = {p['name'] for p in pkmn_data}
    for entry in SYNTHETIC_ENTRIES:
        if entry['name'] not in existing_names:
            pkmn_data.append(entry)

    # Same exclusion list as generate_pokedex.py — keeps evo chains clean
    EXCLUDE_NAMES = {
        'eiscue-noice',
        'pikachu-rock-star', 'pikachu-belle', 'pikachu-pop-star', 'pikachu-phd',
        'pikachu-libre', 'pikachu-cosplay', 'pikachu-original-cap', 'pikachu-hoenn-cap',
        'pikachu-sinnoh-cap', 'pikachu-unova-cap', 'pikachu-kalos-cap',
        'pikachu-alola-cap', 'pikachu-partner-cap', 'pikachu-world-cap',
        # ROM hack custom megas not included in this Romhack
        'raichu-mega-x', 'raichu-mega-y', 'clefable-mega', 'victreebel-mega', 'starmie-mega',
        'dragonite-mega',
        'meganium-mega', 'feraligatr-mega', 'skarmory-mega', 'chimecho-mega',
        'absol-mega-z', 'staraptor-mega',
        'garchomp-mega-z', 'lucario-mega-z',
        'froslass-mega', 'heatran-mega', 'darkrai-mega',
        'emboar-mega', 'excadrill-mega', 'scolipede-mega', 'scrafty-mega',
        'eelektross-mega', 'chandelure-mega', 'golurk-mega',
        'chesnaught-mega', 'delphox-mega', 'greninja-mega', 'pyroar-mega',
        'floette-mega', 'meowstic-mega', 'barbaracle-mega', 'dragalge-mega',
        'hawlucha-mega', 'malamar-mega',
        'zygarde-mega', 'crabominable-mega', 'golisopod-mega', 'drampa-mega',
        'magearna-mega', 'magearna-original-mega', 'zeraora-mega',
        'falinks-mega',
        'scovillain-mega', 'glimmora-mega', 'baxcalibur-mega',
        'tatsugiri-curly-mega', 'tatsugiri-droopy-mega', 'tatsugiri-stretchy-mega',
        # ── Ability-only / cosmetic alternate forms ──
        'greninja-battle-bond',
        'zygarde-10-power-construct',
        'zygarde-50-power-construct',
        'rockruff-own-tempo',
        'mimikyu-busted',
        'oinkologne-female',
        # ── Koraidon ride forms ──
        'koraidon-limited-build', 'koraidon-sprinting-build',
        'koraidon-swimming-build', 'koraidon-gliding-build',
        # ── Miraidon drive forms ──
        'miraidon-low-power-mode', 'miraidon-drive-mode',
        'miraidon-aquatic-mode', 'miraidon-glide-mode',
        # NOTE: maushold-family-of-three and dudunsparce-three-segment are intentionally
        # NOT here — they keep their individual pages so the forms section on the base
        # entry can link to them. They are excluded from the dex grid only.
    }
    pkmn_data = [p for p in pkmn_data if p['name'] not in EXCLUDE_NAMES]

    name_map        = {p['name']: p['display_name'] for p in pkmn_data}
    all_names       = set(name_map.keys())
    name_to_species = {p['name']: p.get('species_name', p['name']) for p in pkmn_data}

    # species_name → base national dex ID (for display numbers)
    species_id_map = {}
    for p in pkmn_data:
        sn = p.get('species_name', p['name'])
        if p['id'] <= 1025:
            species_id_map[sn] = p['id']
    species_id_map.setdefault('deoxys', 386)

    merged = []
    for p in pkmn_data:
        ov = custom_map.get(p['name'], {})
        row = {**p}
        for k, v in ov.items():
            if not k.startswith('_'): row[k] = v
        merged.append(row)

    # Merge dex entries from dex_entries.json (if present)
    dex_entries_file = DATA_DIR / 'dex_entries.json'
    if dex_entries_file.exists():
        with open(dex_entries_file, encoding='utf-8') as f:
            dex_entries_map = json.load(f)
        count = 0
        for row in merged:
            if not row.get('dex_entry'):  # don't overwrite custom.json entries
                entry = dex_entries_map.get(row['name']) or dex_entries_map.get(row.get('species_name', ''), '')
                if entry:
                    row['dex_entry'] = entry
                    count += 1
        print(f"  Dex entries merged: {count} Pokémon")
    else:
        print("  dex_entries.json not found — run fetch_dex_entries.py to populate")

    # species_name → ordered list of all form names (for formes section)
    from collections import defaultdict
    species_forms_map = defaultdict(list)
    for p in merged:
        sn = p.get('species_name', p['name'])
        species_forms_map[sn].append(p['name'])
    # Sort each group by raw id so base comes first
    id_lookup = {p['name']: p['id'] for p in merged}
    for sn in species_forms_map:
        species_forms_map[sn].sort(key=lambda n: id_lookup.get(n, 99999))

    inherited_forms = inherit_form_moves(merged)
    if inherited_forms:
        print(f"  Inherited base movepools for {inherited_forms} form entries")

    targets = sys.argv[1:]
    if targets:
        merged = [p for p in merged if p['name'] in targets]
        if not merged:
            print(f"No Pokémon found for: {targets}"); return

    OUTPUT_DIR.mkdir(exist_ok=True)
    total = len(merged)
    print(f"Generating {total} page(s)…")

    for i, p in enumerate(merged, 1):
        html = generate_page(p, name_map, all_names, species_forms_map, species_id_map, name_to_species, ability_db=ability_db, move_db=move_db)
        (OUTPUT_DIR / f"{p['name']}.html").write_text(html, encoding='utf-8')
        if i % 100 == 0 or i == total:
            print(f"  {i}/{total}…")

    print(f"Done! → {OUTPUT_DIR}/")

if __name__ == '__main__':
    main()
