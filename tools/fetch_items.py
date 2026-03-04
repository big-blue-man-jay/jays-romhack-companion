#!/usr/bin/env python3
"""
Fetch item data from PokeAPI and convert it into the Companion ItemDex seed format.

By default this writes to data/items-pokeapi.json. The live ItemDex is now
maintained directly inside itemdex.html, so treat this file as a reference seed
to copy from instead of a live runtime source.

Examples:
  python3 tools/fetch_items.py
  python3 tools/fetch_items.py --limit 50
  python3 tools/fetch_items.py --output data/items-pokeapi.json
  python3 tools/fetch_items.py --version-group heartgold-soulsilver
"""

import argparse
import json
import re
import ssl
import sys
import time
import urllib.request
from pathlib import Path

_SSL_CTX = ssl._create_unverified_context()

TOOLS_DIR = Path(__file__).resolve().parent
SITE_DIR = TOOLS_DIR.parent
DATA_DIR = SITE_DIR / "data"
API_ROOT = "https://pokeapi.co/api/v2"

POCKET_TAGS = {
    "misc": "Utility",
    "medicine": "Medicine",
    "pokeballs": "Poke Ball",
    "machines": "Machine",
    "berries": "Berry",
    "mail": "Mail",
    "battle": "Battle Utility",
    "key-items": "Key Item",
    "held-items": "Held Item",
}

ATTRIBUTE_TAGS = {
    "consumable": "Consumable",
    "holdable-active": "Held Item",
    "holdable-passive": "Held Item",
    "usable-in-battle": "Battle Use",
    "usable-overworld": "Overworld Use",
    "plot-advancement": "Story Progression",
}


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20, context=_SSL_CTX) as response:
                return json.loads(response.read())
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1)


def paginate(url):
    next_url = url
    while next_url:
        payload = fetch_json(next_url)
        for row in payload.get("results", []):
            yield row
        next_url = payload.get("next")


def dedupe(values):
    seen = set()
    out = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def slug_to_title(slug):
    parts = slug.replace("_", "-").split("-")
    words = []
    for part in parts:
        if not part:
            continue
        if part.isdigit():
            words.append(part)
        elif len(part) <= 3 and part.isupper():
            words.append(part)
        else:
            words.append(part.capitalize())
    return " ".join(words)


def resource_name(resource):
    if isinstance(resource, dict):
        return resource.get("name", "")
    return ""


def english_text(entries, field):
    for entry in entries or []:
        if entry.get("language", {}).get("name") == "en":
            value = entry.get(field, "")
            if value:
                return value.replace("\n", " ").replace("\f", " ").strip()
    return ""


def english_name(detail):
    return english_text(detail.get("names"), "name") or slug_to_title(detail["name"])


def short_label(name):
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return "ITEM"
    if len(words) == 1:
        cleaned = words[0].upper()
        return cleaned[:4]
    return "".join(word[0].upper() for word in words[:4])


def category_to_tag(category_name):
    if not category_name:
        return None

    if "ball" in category_name:
        return "Poke Ball"
    if "berry" in category_name:
        return "Berry"
    if "mail" in category_name:
        return "Mail"
    if any(token in category_name for token in ("medicine", "healing", "revival", "status-cures", "pp-recovery", "vitamins")):
        return "Medicine"

    return slug_to_title(category_name)


def machine_prefix(slug):
    match = re.fullmatch(r"(tm|hm)(\d+)", slug)
    if not match:
        return None
    return match.group(1).upper(), match.group(2)


def fetch_machine_move(detail, version_group):
    machines = detail.get("machines") or []
    if not machines:
        return None

    selected = None
    if version_group:
        for row in machines:
            if row.get("version_group", {}).get("name") == version_group and row.get("machine", {}).get("url"):
                selected = row
                break

    if selected is None:
        for row in reversed(machines):
            if row.get("machine", {}).get("url"):
                selected = row
                break

    if selected is None:
        return None

    try:
        machine = fetch_json(selected["machine"]["url"])
    except Exception as exc:
        print(f"  WARN: machine lookup failed for {detail['name']}: {exc}")
        return None

    move_name = machine.get("move", {}).get("name")
    return slug_to_title(move_name) if move_name else None


def build_display_name(detail, move_name):
    base_name = english_name(detail)
    prefix = machine_prefix(detail["name"])
    if prefix and move_name:
        return f"{prefix[0]}{prefix[1]} {move_name}"
    return base_name


def build_description(detail, move_name):
    effect = english_text(detail.get("effect_entries"), "short_effect")
    if effect:
        return effect
    if move_name and machine_prefix(detail["name"]):
        return f"Teaches {move_name}."
    category = resource_name(detail.get("category"))
    if category:
        return f"PokeAPI seed entry for {slug_to_title(category).lower()} items."
    return "PokeAPI seed entry."


def build_type_tags(detail, move_name):
    tags = []

    prefix = machine_prefix(detail["name"])
    if prefix:
        tags.append(prefix[0])

    pocket_name = resource_name(detail.get("pocket"))
    pocket_tag = POCKET_TAGS.get(pocket_name, slug_to_title(pocket_name))
    if pocket_tag != "Machine" or not prefix:
        tags.append(pocket_tag)

    tags.append(category_to_tag(resource_name(detail.get("category"))))

    for attr in detail.get("attributes") or []:
        tags.append(ATTRIBUTE_TAGS.get(attr.get("name")))

    if move_name and prefix:
        tags.append("Battle Utility")

    if not tags:
        tags.append("Utility")

    return dedupe(tags)


def build_record(detail, version_group):
    move_name = fetch_machine_move(detail, version_group)
    display_name = build_display_name(detail, move_name)
    source_attrs = [row.get("name") for row in detail.get("attributes") or [] if row.get("name")]
    category_name = resource_name(detail.get("category")) or None
    pocket_name = resource_name(detail.get("pocket")) or None

    return {
        "id": detail["name"],
        "name": display_name,
        "icon": (detail.get("sprites") or {}).get("default") or "",
        "iconLabel": short_label(display_name),
        "description": build_description(detail, move_name),
        "typeTags": build_type_tags(detail, move_name),
        "acquisitions": [],
        "source": {
            "pokeapiId": detail.get("id"),
            "apiUrl": f"{API_ROOT}/item/{detail['name']}/",
            "cost": detail.get("cost"),
            "category": category_name,
            "pocket": pocket_name,
            "attributes": source_attrs,
            "teachesMove": move_name,
        },
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch PokeAPI items into Companion ItemDex seed JSON.")
    parser.add_argument(
        "--output",
        default=str(DATA_DIR / "items-pokeapi.json"),
        help="Output JSON path (default: data/items-pokeapi.json).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only fetch the first N items (useful for testing).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.05,
        help="Seconds to wait between item requests (default: 0.05).",
    )
    parser.add_argument(
        "--version-group",
        default="heartgold-soulsilver",
        help="Preferred version group for TM/HM machine lookups (default: heartgold-soulsilver).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (BASE_DIR / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching item index from PokeAPI...")
    item_refs = list(paginate(f"{API_ROOT}/item/?limit=100"))
    if args.limit > 0:
        item_refs = item_refs[: args.limit]
    total = len(item_refs)
    print(f"Items queued: {total}")

    records = []
    for idx, ref in enumerate(item_refs, start=1):
        name = ref.get("name", "")
        url = ref.get("url")
        if not url:
            print(f"  WARN: skipping item without detail URL: {name}")
            continue

        try:
            detail = fetch_json(url)
            records.append(build_record(detail, args.version_group))
        except Exception as exc:
            print(f"  WARN: failed {name}: {exc}")
        else:
            if idx == 1 or idx % 25 == 0 or idx == total:
                print(f"  fetched {idx}/{total}")

        if args.delay > 0 and idx < total:
            time.sleep(args.delay)

    records.sort(key=lambda row: (row["source"]["pokeapiId"] or sys.maxsize, row["id"]))
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(records, handle, indent=2, ensure_ascii=False)

    print(f"Wrote {len(records)} item entries to {output_path}")


if __name__ == "__main__":
    main()
