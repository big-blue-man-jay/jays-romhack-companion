"""
fetch_pokedex.py
Fetches all Pokemon data from PokeAPI and builds data/pokemon.json
Run once from your Companion folder: python3 tools/fetch_pokedex.py

Requirements: pip3 install requests
"""

import requests
import json
import time
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────────

SITE_DIR    = Path(__file__).resolve().parent.parent
OUTPUT_DIR  = SITE_DIR / "data"
OUTPUT_FILE = OUTPUT_DIR / "pokemon.json"
ERROR_LOG   = OUTPUT_DIR / "fetch_errors.log"

# Forms to EXCLUDE (pattern/colour variants, type-only forms)
EXCLUDED_FORM_SUFFIXES = [
    # Vivillon patterns
    "icy-snow", "polar", "tundra", "continental", "garden", "elegant",
    "meadow", "modern", "marine", "archipelago", "high-plains", "sandstorm",
    "river", "monsoon", "savanna", "sun", "ocean", "jungle", "fancy", "poke-ball",
    # Minior
    "red-meteor", "orange-meteor", "yellow-meteor", "green-meteor",
    "blue-meteor", "indigo-meteor", "violet-meteor",
    "red", "orange", "yellow", "green", "blue", "indigo", "violet",
    # Alcremie
    "ruby-cream", "matcha-cream", "mint-cream", "lemon-cream",
    "salted-cream", "ruby-swirl", "caramel-swirl", "rainbow-swirl",
    # Unown letters
    "a","b","c","d","e","f","g","h","i","j","k","l","m",
    "n","o","p","q","r","s","t","u","v","w","x","y","z",
    "exclamation","question",
    # Arceus/Silvally types
    "bug","dark","dragon","electric","fairy","fighting","fire","flying",
    "ghost","grass","ground","ice","normal","poison","psychic","rock",
    "steel","water",
    # Spinda
    "spinda",
    # Basculin forms that are just colour
    "blue-striped", "white-striped",
]

# Forms to INCLUDE even if they match a suffix above
FORCE_INCLUDE = [
    "deoxys-attack","deoxys-defense","deoxys-speed",
]

STAT_MAP = {
    "hp": "hp", "attack": "atk", "defense": "def",
    "special-attack": "spa", "special-defense": "spd", "speed": "spe"
}

session = requests.Session()
session.headers.update({"User-Agent": "JaysRomhack-PokedexBuilder/1.0"})

errors = []

# ── HELPERS ─────────────────────────────────────────────────────────────────

def get(url, retries=3):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return None
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(1)
    return None


def should_exclude_form(pokemon_name, species_name):
    """Return True if this form should be excluded."""
    if pokemon_name in FORCE_INCLUDE:
        return False
    if pokemon_name == species_name:
        return False  # base form always included

    suffix = pokemon_name.replace(species_name + "-", "")

    # Exclude pure colour/pattern suffixes
    if suffix in EXCLUDED_FORM_SUFFIXES:
        return True

    # Exclude totem forms
    if suffix.startswith("totem"):
        return True

    # Exclude starter-cap pikachu
    if species_name == "pikachu" and suffix in [
        "original","hoenn","sinnoh","unova","kalos","alola","partner","world","starter"
    ]:
        return True

    return False


def parse_stats(stats_data):
    return {STAT_MAP[s["stat"]["name"]]: s["base_stat"]
            for s in stats_data if s["stat"]["name"] in STAT_MAP}


def parse_types(types_data):
    return [t["type"]["name"].capitalize()
            for t in sorted(types_data, key=lambda x: x["slot"])]


def parse_abilities(abilities_data):
    result = {"normal": [], "hidden": None}
    for a in abilities_data:
        name = a["ability"]["name"].replace("-", " ").title()
        if a["is_hidden"]:
            result["hidden"] = name
        else:
            result["normal"].append(name)
    return result


def parse_moves(moves_data):
    levelup = []
    egg     = []
    tm      = []
    tutor   = []

    for m in moves_data:
        move_name = m["move"]["name"].replace("-", " ").title()
        for vgd in m["version_group_details"]:
            method = vgd["move_learn_method"]["name"]
            vg     = vgd["version_group"]["name"]

            # Use scarlet-violet (gen 9) as primary, fall back to any
            if vg not in ("scarlet-violet", "the-teal-mask", "the-indigo-disk"):
                continue

            if method == "level-up":
                level = vgd["level_learned_at"]
                # Avoid duplicates
                if not any(e["move"] == move_name for e in levelup):
                    levelup.append({"level": level, "move": move_name})
            elif method == "egg":
                if move_name not in egg:
                    egg.append(move_name)
            elif method == "machine":
                if move_name not in tm:
                    tm.append(move_name)
            elif method == "tutor":
                if move_name not in tutor:
                    tutor.append(move_name)

    # Sort level up by level
    levelup.sort(key=lambda x: x["level"])

    return {
        "levelup": levelup,
        "egg":     sorted(egg),
        "tm":      sorted(tm),
        "tutor":   sorted(tutor),
    }


def parse_evolution_chain(chain_data, target_name):
    """Walk the evo chain and return a flat list of evolution stages."""
    evolutions = []

    def walk(node, stage=1):
        species_name = node["species"]["name"]
        evo_details  = []
        for detail in node["evolves_to"]:
            for ed in detail.get("evolution_details", [{}]):
                trigger = ed.get("trigger", {}).get("name", "")
                method  = {}
                if trigger == "level-up":
                    method["type"] = "level"
                    method["value"] = ed.get("min_level") or "?"
                elif trigger == "use-item":
                    item = ed.get("item", {})
                    method["type"] = "item"
                    method["value"] = item.get("name", "?").replace("-", " ").title() if item else "?"
                elif trigger == "trade":
                    method["type"] = "trade"
                    item = ed.get("held_item", {})
                    method["value"] = item.get("name", "").replace("-", " ").title() if item else ""
                else:
                    method["type"] = trigger
                    method["value"] = ""
                evolutions.append({
                    "from":   species_name,
                    "to":     detail["species"]["name"],
                    "method": method,
                })
            walk(detail, stage + 1)

    walk(chain_data)
    return evolutions


def get_display_name(pokemon_name, species_name):
    """Convert api name to display name e.g. rattata-alola -> Rattata (Alola)"""
    if pokemon_name == species_name:
        return pokemon_name.replace("-", " ").title()

    suffix = pokemon_name.replace(species_name + "-", "")
    base   = species_name.replace("-", " ").title()

    # Known suffix -> label mappings
    label_map = {
        "mega":        "Mega",
        "mega-x":      "Mega X",
        "mega-y":      "Mega Y",
        "gmax":        "Gigantamax",
        "alola":       "Alolan",
        "galar":       "Galarian",
        "hisui":       "Hisuian",
        "paldea":      "Paldean",
        "attack":      "Attack Forme",
        "defense":     "Defense Forme",
        "speed":       "Speed Forme",
        "origin":      "Origin Forme",
        "sky":         "Sky Forme",
        "therian":     "Therian Forme",
        "incarnate":   "Incarnate Forme",
        "black":       "Black Kyurem",
        "white":       "White Kyurem",
        "resolute":    "Resolute Forme",
        "pirouette":   "Pirouette Forme",
        "aria":        "Aria Forme",
        "ash":         "Ash-Greninja",
        "10":          "10% Forme",
        "complete":    "Complete Forme",
        "dusk":        "Dusk Forme",
        "midnight":    "Midnight Forme",
        "original":    "Original Color",
        "school":      "School Forme",
        "busted":      "Busted Form",
        "starter":     "Starter",
        "hangry":      "Hangry Mode",
        "full-belly":  "Full Belly Mode",
        "hero":        "Hero of Many Battles",
        "crowned":     "Crowned",
        "eternamax":   "Eternamax",
        "rapid-strike":"Rapid Strike",
        "single-strike":"Single Strike",
        "ice":         "Ice Rider",
        "shadow":      "Shadow Rider",
        "apex":        "Apex Build",
        "roaming":     "Roaming Form",
        "combat":      "Combat Breed",
        "blaze":       "Blaze Breed",
        "aqua":        "Aqua Breed",
    }

    label = label_map.get(suffix, suffix.replace("-", " ").title())
    return f"{base} ({label})"


# ── FETCH EVOLUTION CHAINS (cached) ─────────────────────────────────────────

evo_chain_cache = {}

def fetch_evo_chain(species_data):
    url = species_data.get("evolution_chain", {}).get("url")
    if not url:
        return []
    if url in evo_chain_cache:
        return evo_chain_cache[url]
    chain_data = get(url)
    if not chain_data:
        return []
    result = parse_evolution_chain(chain_data["chain"], "")
    evo_chain_cache[url] = result
    return result


# ── MAIN FETCH ───────────────────────────────────────────────────────────────

def fetch_all_pokemon():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Fetching Pokemon list...")
    all_pokemon = []
    url = "https://pokeapi.co/api/v2/pokemon?limit=2000"
    data = get(url)
    if not data:
        print("ERROR: Could not fetch Pokemon list")
        return

    raw_list = data["results"]
    print(f"Found {len(raw_list)} Pokemon entries. Filtering forms...")

    # First pass — get species for each entry to check form eligibility
    entries_to_fetch = []
    for entry in raw_list:
        name = entry["name"]
        entries_to_fetch.append(name)

    print(f"Processing {len(entries_to_fetch)} entries...\n")

    processed = []
    skipped   = 0

    for i, name in enumerate(entries_to_fetch):
        print(f"  [{i+1}/{len(entries_to_fetch)}] {name}", end="\r")

        try:
            poke_data = get(f"https://pokeapi.co/api/v2/pokemon/{name}")
            if not poke_data:
                errors.append(f"404: {name}")
                skipped += 1
                continue

            species_name = poke_data["species"]["name"]

            # Check if we should exclude this form
            if should_exclude_form(name, species_name):
                skipped += 1
                continue

            # Fetch species data
            species_data = get(poke_data["species"]["url"])
            if not species_data:
                errors.append(f"No species data: {name}")
                skipped += 1
                continue

            # Get English genus and flavor text
            genus = ""
            for g in species_data.get("genera", []):
                if g["language"]["name"] == "en":
                    genus = g["genus"]
                    break

            # Evolution chain
            evolutions = fetch_evo_chain(species_data)

            entry = {
                "id":           poke_data["id"],
                "name":         name,
                "display_name": get_display_name(name, species_name),
                "species_name": species_name,
                "genus":        genus,
                "generation":   species_data.get("generation", {}).get("name", "").replace("generation-", "").upper(),
                "types":        parse_types(poke_data["types"]),
                "stats":        parse_stats(poke_data["stats"]),
                "abilities":    parse_abilities(poke_data["abilities"]),
                "evolutions":   evolutions,
                "moves":        parse_moves(poke_data["moves"]),
                # Custom fields — populated by custom.json overrides
                "changed":      False,
                "meta":         False,
                "notes":        "",
            }

            processed.append(entry)

            # Be polite to the API
            time.sleep(0.1)

        except Exception as e:
            errors.append(f"Error on {name}: {str(e)}")
            skipped += 1
            continue

    # Sort by ID
    processed.sort(key=lambda x: x["id"])

    print(f"\n\nDone. {len(processed)} Pokemon saved, {skipped} skipped.")

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)

    print(f"Saved to {OUTPUT_FILE}")

    # Write errors
    if errors:
        with open(ERROR_LOG, "w") as f:
            f.write("\n".join(errors))
        print(f"{len(errors)} errors logged to {ERROR_LOG}")

    # Also create empty custom.json if it doesn't exist
    custom_file = OUTPUT_DIR / "custom.json"
    if not custom_file.exists():
        example = [
            {
                "_comment": "Add entries here for Pokemon you have customized.",
                "_comment2": "Only include fields you want to OVERRIDE from the base data.",
                "name": "rattata",
                "changed": True,
                "moves": {
                    "levelup": [
                        {"level": 1, "move": "Tackle"},
                        {"level": 1, "move": "Tail Whip"},
                        {"level": 4, "move": "Quick Attack"},
                        {"level": 7, "move": "Focus Energy"},
                        {"level": 10, "move": "Bite"},
                        {"level": 13, "move": "Super Fang"},
                        {"level": 16, "move": "Sucker Punch"},
                        {"level": 20, "move": "Body Slam"},
                        {"level": 24, "move": "Crunch"},
                        {"level": 28, "move": "Double-Edge"}
                    ],
                    "egg": ["Thunder Wave", "Counter", "Flame Wheel"],
                    "tm": [],
                    "tutor": []
                },
                "notes": "Rattata has been rebalanced for the early game."
            }
        ]
        with open(custom_file, "w", encoding="utf-8") as f:
            json.dump(example, f, ensure_ascii=False, indent=2)
        print(f"Created example custom.json at {custom_file}")


if __name__ == "__main__":
    fetch_all_pokemon()
