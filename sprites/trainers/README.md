Trainer portraits for Area Sheets and TrainerDex live here.

Use one shared sprite library by trainer class, not by area.

Recommended structure:

- `sprites/trainers/classes/`
- `sprites/trainers/portraits/` (optional, for larger TrainerDex art later)

Recommended class filenames:

- `elder.png`
- `sage.png`
- `ace-trainer.png`
- `bug-catcher.png`
- `falkner.png`

Area sheets and TrainerDex should both point at the same shared class art whenever possible.
Only create special one-off files when a trainer truly needs unique artwork.

Keep trainer images small, transparent PNGs when possible.
HGSS battle sprites usually fit well at around 56x56 to 80x80 display size.
