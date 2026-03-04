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

## Registering sprites

After adding files here, open `tools/generate_pokemon_pages.py` and add the names to the
registry sets near the top of the file:

```python
CUSTOM_SPRITES: set = {
    'iron-leaves',
    'walking-wake',
    # ...
}

CUSTOM_SPRITES_SHINY: set = {
    'iron-leaves',   # only if you also added iron-leaves-shiny.png
}
```

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
