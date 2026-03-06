# Custom Pokémon Sprites

Place custom `.png` sprite files here for Pokémon that don't have Showdown sprites.

## File naming

| File | Purpose |
|------|---------|
| `{pokemon-name}.png` | Normal sprite |
| `{pokemon-name}-shiny.png` | Shiny sprite (optional) |

Use the same slug format as the Pokémon's name in `pokemon.json`, e.g.:
- `iron-leaves.png`
- `iron-leaves-shiny.png`
- `walking-wake.png`

Special case: Paldean Tauros form pages use `*-breed` names internally, but
`tauros-paldea-aqua.png`, `tauros-paldea-blaze.png`, and
`tauros-paldea-combat.png` are also accepted automatically.

The loader also supports common short-form aliases used by sprite packs
(`-f`, `-lowkey`, `-rapidstrike`, etc.) so files can follow either Pokédex
slugs or Showdown-style shorthand.

## Registering sprites

No manual registry step is required. The generator auto-detects all `.png` files in this folder.

Then re-run the generator:
```
python3 tools/generate_pokemon_pages.py
```

## How it works

- Pages for Pokémon in `CUSTOM_SPRITES` use `../sprites/pokemon/{name}.png` as the primary
  sprite, with Showdown gen5 as the first fallback.
- The shiny toggle button works the same way — it swaps to `{name}-shiny.png` if the name
  is in `CUSTOM_SPRITES_SHINY`, otherwise falls back to the Showdown shiny sprite.
- Custom sprites also appear in evo chain nodes and the family web row.
