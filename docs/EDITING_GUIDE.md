# Companion Editing Guide

This folder is a static website. Some pages are edited directly, some pages are generated from scripts, and some pages contain auto-injected data blocks.

If you only remember one rule, use this one:

- Edit source files, not generated output, unless the page is explicitly hand-maintained.

## Folder Map

### Hand-edited pages

- `index.html`
  - Home page UI and content.
- `progression.html`
  - Progression page UI and all progression content on that page.
- `mechanics.html`
  - Mechanics page UI and all mechanics content on that page.
- `tracker.html`
  - Run list / tracker home UI.
  - Uses browser `localStorage` for saved runs.
- `tracker-run.html`
  - Per-run tracker UI and run logic.
  - Uses browser `localStorage` for run state.
- `areadex.html`
  - Hand-maintained AreaDex UI and manual area index entries.
- `itemdex.html`
  - Hand-maintained ItemDex UI and manual item entries.
- `trainerdex.html`
  - Hand-maintained TrainerDex UI and manual trainer entries.
- `areas/sproutower.html`
  - Existing area page. Edit directly.
- `areas/template.html`
  - Template for making new area pages.

### Pages with hand-edited UI but auto-generated data blocks

- `pokedex.html`
  - Edit the layout, styles, and UI logic directly.
  - Do not manually edit the baked `const POKEMON_DATA=...` block.
  - Re-run `tools/generate_pokedex.py` when Pokemon data changes.
- `calculator.html`
  - Edit the layout, styles, and calculator behavior directly.
  - Do not remove or hand-edit the block between:
    - `<!-- CALCDB:START -->`
    - `<!-- CALCDB:END -->`
  - Re-run `tools/generate_calculator.py` when Pokemon / move / ability data changes.

### Generated pages

- `pokemon/*.html`
  - These are generated pages.
  - Do not make permanent UI edits here by hand.
  - Edit `tools/generate_pokemon_pages.py`, then regenerate.

### Data and assets

- `data/`
  - JSON data used by the site and generator scripts.
  - ItemDex and TrainerDex entries are no longer loaded from here; those live directly in `itemdex.html` and `trainerdex.html`.
- `tools/`
  - Generator and fetch scripts used to rebuild the site data or pages.
- `docs/`
  - Project notes and editing reference files.
- `sprites/`
  - Local image assets.
  - Keep this folder in published builds.
- `docs/missing-sprites.md`
  - Reference note for sprite gaps.

## Source Of Truth

Use this table when you want to change something and need to know where to edit it.

| What you want to change | Edit here | Then do this |
|---|---|---|
| Home page UI/content | `index.html` | Publish file |
| Pokedex page UI/filter layout | `pokedex.html` | Publish file |
| Pokedex Pokemon dataset | `data/pokemon.json` and/or `data/custom.json` | Run `python3 tools/generate_pokedex.py` |
| Pokemon detail page UI/layout | `tools/generate_pokemon_pages.py` | Run `python3 tools/generate_pokemon_pages.py` |
| One Pokemon detail page content override | `data/custom.json` | Run `python3 tools/generate_pokemon_pages.py` |
| Calculator UI/controls | `calculator.html` | Publish file |
| Calculator baked data | `data/pokemon.json`, `data/custom.json`, `data/moves.json`, `data/abilities.json` | Run `python3 tools/generate_calculator.py` |
| AreaDex UI and manual area index entries | `areadex.html` | Publish file |
| ItemDex UI and manual item entries | `itemdex.html` | Publish file |
| TrainerDex UI and manual trainer entries | `trainerdex.html` | Publish file |
| Progression page sections | `progression.html` | Publish file |
| Mechanics page sections | `mechanics.html` | Publish file |
| Tracker landing page UI | `tracker.html` | Publish file |
| Tracker run page UI | `tracker-run.html` | Publish file |
| Existing area page content | `areas/*.html` | Publish file |
| New area page template | `areas/template.html` | Copy template to a new file, then edit it |
| Sitewide nav/menu on Pokemon detail pages | `tools/generate_pokemon_pages.py` | Regenerate Pokemon pages |
| Sitewide nav/menu on top-level pages | Each individual `.html` page | Publish files |

## Where To Edit UI

### 1. Top-level static pages

These pages are mostly self-contained. Their HTML, CSS, and JS live in the same file:

- `index.html`
- `progression.html`
- `mechanics.html`
- `tracker.html`
- `tracker-run.html`
- `areadex.html`
- `itemdex.html`
- `trainerdex.html`

For these pages:

- Change markup in the HTML body for layout/content changes.
- Change the `<style>` block for visual changes.
- Change the bottom `<script>` block for behavior changes.
- Publish the edited file directly.

There is no generator step for these pages.

For the manual dex pages specifically:

- `areadex.html` stores its live entries in `AREADEX_SOURCE`
- `itemdex.html` stores its live entries in `ITEMBASE_SOURCE`
- `trainerdex.html` stores its live entries in `TRAINERDEX_SOURCE`
- starter copy blocks now live in the `Manual Entry Templates` section of this guide, not in the page UI

### 2. `pokedex.html`

`pokedex.html` is partly hand-edited and partly generated.

Safe to edit directly:

- page layout
- filters
- cards
- CSS
- UI JavaScript
- menu/header links

Do not hand-edit:

- the baked `const POKEMON_DATA=...` script block

That block is rebuilt by `tools/generate_pokedex.py`.

If you change only the UI, you can just publish `pokedex.html`.

If you change Pokemon data:

1. Edit `data/pokemon.json` or `data/custom.json`
2. Run `python3 tools/generate_pokedex.py`
3. Publish `pokedex.html`

### 3. `calculator.html`

`calculator.html` is also partly hand-edited and partly generated.

Safe to edit directly:

- calculator layout
- panels
- buttons
- box logic
- battle math UI behavior
- styles
- menus

Do not break or delete the auto-generated block between:

- `<!-- CALCDB:START -->`
- `<!-- CALCDB:END -->`

That block is rebuilt by `tools/generate_calculator.py`.

If you change only the UI/logic, publish `calculator.html`.

If you change Pokemon, move, or ability data:

1. Edit the relevant files in `data/`
2. Run `python3 tools/generate_calculator.py`
3. Publish `calculator.html`

### 4. `pokemon/*.html` detail pages

These are generated from `tools/generate_pokemon_pages.py`.

Do not hand-edit individual Pokemon pages if you want the change to survive regeneration.

For detail page UI changes, edit:

- `tools/generate_pokemon_pages.py`

That includes:

- page layout
- stat cards
- moves display
- strategy section
- menu structure
- page scripts
- page CSS

Then regenerate:

- `python3 tools/generate_pokemon_pages.py`

You can also regenerate only specific pages:

- `python3 tools/generate_pokemon_pages.py blaziken venusaur`

### 5. Area pages

Current area files:

- `areas/sproutower.html`
- `areas/template.html`

Use `areas/template.html` as the base for new area pages. Existing area pages do not auto-sync from the template.

That means:

- editing `areas/template.html` only affects future copied pages
- editing `areas/sproutower.html` only affects that page

If you want a template change applied to all existing area pages, update each existing area file too.

## Where To Add / Delete / Adjust Data Blocks

### `data/custom.json` (main manual override file)

This is the most important manual data file.

Use it for:

- ROM hack changes to Pokemon stats, typing, moves, abilities, evolutions
- per-Pokemon notes
- strategy blocks
- manual item lists
- custom dex entries
- one-off overrides without re-fetching base data

Rules:

- Every real override entry needs `"name": "pokemon-slug"`.
- Keys starting with `_` are treated like comments/notes and ignored by generators.
- Any non-underscore field can override the matching field from `data/pokemon.json`.

Examples of useful fields you can add or replace:

- `stats`
- `types`
- `abilities`
- `moves`
- `evolutions`
- `items`
- `notes`
- `dex_entry`
- `strategy`
- `changed`
- `meta`

Current strategy format example:

```json
{
  "name": "blaziken",
  "strategy": {
    "summary": "Optional short paragraph",
    "showdown": "Blaziken @ Leftovers\nAbility: Blaze\nTera Type: Fire\nAdamant Nature\n- Protect\n- Flare Blitz\n- Close Combat\n- Swords Dance",
    "bullets": [
      "Strength or warning point 1",
      "Strength or warning point 2"
    ]
  }
}
```

When `strategy` is present:

- Pokemon detail pages use it in the Strategy panel
- the `Export` button comes from the page generator UI

After editing `data/custom.json`, usually regenerate:

- `python3 tools/generate_pokemon_pages.py`

Also regenerate these when the changed fields affect them:

- `python3 tools/generate_pokedex.py`
- `python3 tools/generate_calculator.py`

### `data/pokemon.json` (base Pokemon dataset)

This is the large base dataset generated by `fetch_pokedex.py`.

Use it when you want to replace the whole fetched source dataset, not just patch one Pokemon.

Typical use:

- full refresh from PokeAPI
- inspecting the base data before deciding whether an override belongs in `custom.json`

In most day-to-day edits, prefer `data/custom.json` over manually editing this file.

If `data/pokemon.json` changes, regenerate:

- `python3 tools/generate_pokedex.py`
- `python3 tools/generate_pokemon_pages.py`
- `python3 tools/generate_calculator.py`

### `data/dex_entries.json`

This is the fetched dex flavor text database.

Use it when:

- refreshing flavor text from PokeAPI

Normal workflow:

1. Run `python3 fetch_dex_entries.py`
2. Run `python3 tools/generate_pokemon_pages.py`

Important:

- If a Pokemon has `dex_entry` in `data/custom.json`, that custom text wins.

### `data/moves.json`

Used by:

- Pokemon detail pages
- calculator data generation

Use it for:

- move names
- type/category/power/accuracy/PP
- descriptions
- move flags relevant to battle logic

If it changes, regenerate:

- `python3 tools/generate_pokemon_pages.py`
- `python3 tools/generate_calculator.py`

### `data/abilities.json`

Used by:

- Pokemon detail pages
- calculator data generation

Use it for:

- ability names
- short descriptions

If it changes, regenerate:

- `python3 tools/generate_pokemon_pages.py`
- `python3 tools/generate_calculator.py`

### `data/egg_groups.json`

Used by:

- `tools/generate_pokedex.py`
- `tools/generate_pokemon_pages.py`

If it changes, regenerate:

- `python3 tools/generate_pokedex.py`
- `python3 tools/generate_pokemon_pages.py`

## Fetch / Rebuild Scripts

Run these from inside the `Companion` folder.

### Refresh raw data from PokeAPI

- `python3 fetch_pokedex.py`
  - Rebuilds `data/pokemon.json`
  - Requires internet
  - Requires `requests`
- `python3 fetch_moves.py`
  - Rebuilds `data/moves.json`
  - Requires internet
- `python3 fetch_abilities.py`
  - Rebuilds `data/abilities.json`
  - Requires internet
  - Requires `requests`
- `python3 fetch_dex_entries.py`
  - Rebuilds `data/dex_entries.json`
  - Requires internet
  - Requires `requests`

After fetches, regenerate the affected HTML pages.

### Rebuild HTML outputs

- `python3 tools/generate_pokedex.py`
  - Re-bakes Pokemon data into `pokedex.html`
- `python3 tools/generate_pokemon_pages.py`
  - Rebuilds every file in `pokemon/`
- `python3 tools/generate_pokemon_pages.py blaziken`
  - Rebuilds only one named Pokemon page
- `python3 tools/generate_calculator.py`
  - Re-bakes compact battle data into `calculator.html`

## Tracker Data Notes

The tracker pages do not store runs in `data/*.json`.

They save to browser `localStorage`, including keys such as:

- `theme`
- `nuzlocke_runs`
- `nuzlocke_active_run`
- `nuzlocke_entries_<runId>`

That means:

- publishing updated HTML does not automatically migrate a user's saved runs
- clearing browser storage will remove saved tracker state
- if you want export/import for runs, that needs to be built in the tracker UI

`tracker-run.html` also includes a hardcoded `STARTERS` array in its script for starter suggestions. If you want to change that suggestion list, edit `tracker-run.html` directly.

## Common Edit Workflows

### Change a Pokemon page layout

1. Edit `tools/generate_pokemon_pages.py`
2. Run `python3 tools/generate_pokemon_pages.py`
3. Publish the `pokemon/` folder

### Add strategy notes for one Pokemon

1. Add or update that Pokemon entry in `data/custom.json`
2. Put the strategy data under `strategy` (or `notes` for a simple fallback)
3. Run `python3 tools/generate_pokemon_pages.py`
4. Publish the affected page(s) in `pokemon/`

### Change Pokedex stats or learnsets globally

1. Edit `data/custom.json` for manual overrides, or `data/pokemon.json` for base data
2. Run:
   - `python3 tools/generate_pokedex.py`
   - `python3 tools/generate_pokemon_pages.py`
   - `python3 tools/generate_calculator.py`
3. Publish the updated HTML

### Add a new area page

1. Copy `areas/template.html` to a new slug, for example `areas/ilexforest.html`
2. Edit the copied file
3. Add links to it from any navigation that should reach it
4. Publish the new file

### Change menu links across the whole site

There is no single shared header include.

You need to update:

- top-level hand-edited pages individually
- existing area pages individually
- `areas/template.html` for future area pages
- `tools/generate_pokemon_pages.py` for Pokemon detail pages

Then regenerate Pokemon pages if that generator was changed.

## What To Publish

Publish the static site contents of the `Companion` folder, preserving the folder structure.

Required for the live site:

- all top-level `*.html` files
- `pokemon/`
- `areas/`
- `data/`
- `sprites/`

Optional for the live site but useful in source control:

- `tools/generate_*.py`
- `tools/fetch_*.py`
- `docs/missing-sprites.md`
- this guide

If you manually upload files to a host, upload the contents of `Companion`, not just one page in isolation.

## How To Publish / Preview

### Local preview

From inside the `Companion` folder:

```bash
python3 -m http.server
```

Then open:

- `http://localhost:8000/`

### Important hosting rule

Use an HTTP-based host or local server.

Do not rely on opening pages with `file://` if you want everything to work correctly.

Reason:

- Pokemon detail pages still fetch `data/moves.json` and `data/abilities.json` at runtime when available
- some browser security rules block those fetches from `file://`

### Static hosting options

This site can be deployed to any static host, including:

- GitHub Pages
- Netlify
- Cloudflare Pages
- manual upload to a normal web server

No Python server is required in production. The Python scripts are only build tools.

## Safe / Unsafe Edits

Safe:

- editing hand-maintained HTML files for UI/content
- editing `data/custom.json` for targeted overrides
- editing `tools/generate_pokemon_pages.py` for Pokemon page UI
- editing `areas/template.html` before creating new area pages

Unsafe unless you know you mean it:

- hand-editing `pokemon/*.html` and then later regenerating them
- hand-editing the baked `POKEMON_DATA` block in `pokedex.html`
- hand-editing the baked calc block in `calculator.html`
- deleting `data/` or `sprites/` before publishing
- assuming `areas/template.html` updates existing area pages automatically

## Quick Checklist Before You Upload

1. Make the source edits in the correct file.
2. Run the required generator scripts.
3. Preview the site with `python3 -m http.server`.
4. Check the edited page and at least one Pokemon detail page if data changed.
5. Upload the full `Companion` folder contents with the same folder structure.

## Manual Entry Templates

The live ItemDex and TrainerDex pages no longer show copy panels. Use the starter blocks below instead.

Rules:

- Each block below is a single object, not the full array.
- Paste ItemDex blocks into `ITEMBASE_SOURCE` inside `itemdex.html`.
- Paste TrainerDex blocks into `TRAINERDEX_SOURCE` inside `trainerdex.html`.
- Duplicate and trim acquisition rows or team slots as needed.

### ItemDex Templates

#### TM Template

```json
{
  "id": "tm-[move-slug]",
  "displayId": "[Assign Item Number]",
  "name": "TM [Move Name]",
  "icon": "https://play.pokemonshowdown.com/sprites/itemicons/tm.png",
  "iconLabel": "TM",
  "description": "Teaches [Move Name].",
  "typeTags": ["TM", "Battle Utility"],
  "acquisitions": [
    {
      "location": "[Area Name]",
      "methodTags": ["Ground Pickup", "One-Time"],
      "requirementTags": ["[Badge or HM]"],
      "notes": "[Placement notes or alternate source]"
    }
  ]
}
```

#### HM Template

```json
{
  "id": "hm-[move-slug]",
  "displayId": "[Assign Item Number]",
  "name": "HM [Move Name]",
  "icon": "https://play.pokemonshowdown.com/sprites/itemicons/hm.png",
  "iconLabel": "HM",
  "description": "Teaches [Move Name].",
  "typeTags": ["HM", "Key Item", "Traversal"],
  "acquisitions": [
    {
      "location": "[Story Reward Location]",
      "methodTags": ["Reward", "One-Time"],
      "requirementTags": ["Story Progression"],
      "notes": "[Who gives it and what gate it unlocks]"
    }
  ]
}
```

#### Key Item Template

```json
{
  "id": "[key-item-slug]",
  "displayId": "[Assign Item Number]",
  "name": "[Key Item Name]",
  "icon": "",
  "iconLabel": "KEY",
  "description": "[What this item does in your hack.]",
  "typeTags": ["Key Item"],
  "acquisitions": [
    {
      "location": "[NPC / Area]",
      "methodTags": ["Gift", "One-Time"],
      "requirementTags": ["Story Progression"],
      "notes": "[Exact trigger or story milestone]"
    }
  ]
}
```

#### Held Item Template

```json
{
  "id": "[held-item-slug]",
  "displayId": "[Assign Item Number]",
  "name": "[Held Item Name]",
  "icon": "",
  "iconLabel": "HELD",
  "description": "[Short effect summary.]",
  "typeTags": ["Held Item"],
  "acquisitions": [
    {
      "location": "[Area Name]",
      "methodTags": ["Hidden Pickup", "One-Time"],
      "requirementTags": ["[Requirement]"],
      "notes": "[Where to look or how to farm it]"
    },
    {
      "location": "[Farm or Shop]",
      "methodTags": ["Repeatable"],
      "requirementTags": [],
      "notes": "[Optional second source]"
    }
  ]
}
```

#### Evolution Item Template

```json
{
  "id": "[evolution-item-slug]",
  "displayId": "[Assign Item Number]",
  "name": "[Evolution Item Name]",
  "icon": "",
  "iconLabel": "EVO",
  "description": "[What evolves with this item.]",
  "typeTags": ["Evolution Item"],
  "acquisitions": [
    {
      "location": "[Shop / Route / Cave]",
      "methodTags": ["Ground Pickup", "One-Time"],
      "requirementTags": [],
      "notes": "[Primary source]"
    }
  ]
}
```

#### Medicine Template

```json
{
  "id": "[medicine-slug]",
  "displayId": "[Assign Item Number]",
  "name": "[Medicine Name]",
  "icon": "",
  "iconLabel": "MED",
  "description": "[Effect summary.]",
  "typeTags": ["Medicine"],
  "acquisitions": [
    {
      "location": "[Area Name]",
      "methodTags": ["Ground Pickup", "One-Time"],
      "requirementTags": [],
      "notes": "[Visible or hidden pickup details]"
    }
  ]
}
```

#### Shop Item Template

```json
{
  "id": "[shop-item-slug]",
  "displayId": "[Assign Item Number]",
  "name": "[Shop Item Name]",
  "icon": "",
  "iconLabel": "SHOP",
  "description": "[What the item is for.]",
  "typeTags": ["Utility"],
  "acquisitions": [
    {
      "location": "[Shop Name]",
      "methodTags": ["Shop", "Repeatable"],
      "requirementTags": ["[Badge / Story Gate]"],
      "notes": "[Stock unlock conditions or pricing notes]"
    }
  ]
}
```

### TrainerDex Templates

#### Route Trainer Template

```json
{
  "id": "[trainer-slug]",
  "displayId": "[Assign Trainer Number]",
  "name": "[Trainer Name]",
  "trainerClass": "[Trainer Class]",
  "area": "[Area Name]",
  "chapter": "[Story Window]",
  "tags": ["Route", "Single"],
  "reward": "None",
  "notes": "[Optional notes about AI, opening turns, or gimmicks]",
  "team": [
    {
      "slot": 1,
      "name": "[Pokemon]",
      "level": 1,
      "item": "",
      "ability": "",
      "moves": ["[Move 1]"]
    }
  ]
}
```

#### Boss Trainer Template

```json
{
  "id": "[boss-slug]",
  "displayId": "[Assign Trainer Number]",
  "name": "[Boss Name]",
  "trainerClass": "[Boss Class]",
  "area": "[Boss Arena]",
  "chapter": "[Gym / Story Gate]",
  "tags": ["Boss", "Single", "Story"],
  "reward": "[Badge / TM / Key Unlock]",
  "notes": "[Main prep notes, weather, lead pressure, or surprise coverage]",
  "team": [
    {
      "slot": 1,
      "name": "[Lead Pokemon]",
      "level": 1,
      "item": "[Held Item]",
      "ability": "[Ability]",
      "moves": ["[Move 1]", "[Move 2]", "[Move 3]", "[Move 4]"]
    }
  ]
}
```

#### Double Battle Template

```json
{
  "id": "[double-trainer-slug]",
  "displayId": "[Assign Trainer Number]",
  "name": "[Pair Name]",
  "trainerClass": "[Trainer Pair Class]",
  "area": "[Area Name]",
  "chapter": "[Story Window]",
  "tags": ["Double", "Story"],
  "reward": "None",
  "notes": "[Document AI pairings, Fake Out pressure, field effects, or openers]",
  "battleLink": {
    "battleId": "[shared-battle-id]",
    "partnerId": "[partner-trainer-id]",
    "side": "left",
    "sharedLabel": "[Shared Double Battle Label]"
  },
  "team": [
    {
      "slot": 1,
      "name": "[Pokemon A]",
      "level": 1,
      "item": "",
      "ability": "",
      "moves": ["[Move 1]"]
    },
    {
      "slot": 2,
      "name": "[Pokemon B]",
      "level": 1,
      "item": "",
      "ability": "",
      "moves": ["[Move 1]"]
    }
  ]
}
```

#### Rematch / Postgame Template

```json
{
  "id": "[rematch-slug]",
  "displayId": "[Assign Trainer Number]",
  "name": "[Trainer Name]",
  "trainerClass": "[Trainer Class]",
  "area": "[Area Name]",
  "chapter": "Postgame",
  "tags": ["Rematch", "Single", "Optional"],
  "reward": "[Reward if any]",
  "notes": "[What changed from the first fight and how the rematch unlocks]",
  "team": [
    {
      "slot": 1,
      "name": "[Pokemon]",
      "level": 1,
      "item": "",
      "ability": "",
      "moves": ["[Move 1]"]
    }
  ]
}
```
