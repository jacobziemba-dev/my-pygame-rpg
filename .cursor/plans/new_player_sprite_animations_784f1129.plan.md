---
name: New player sprite animations
overview: Wire `assets/sprites/new_player/with_outline/` into the player by adding sprite-sheet (or multi-file) loading utilities, mapping assets onto the existing `animations` / `status` keys in `Player`, aligning scale and style with existing world/item art (`assets/sprites/*.png`), and optionally tightening attack/feedback behavior so animations read clearly in-game. Inventory UI work stays scoped per `docs/UI_Update_temp/UI_update_temp.md` and is not part of this task.
todos:
  - id: audit-pngs
    content: Confirm each new PNG is a horizontal strip vs single frame; note frame width and frame count for IDLE/WALK/ATTACK.
    status: completed
  - id: utils-sheet-loader
    content: Add load_frames_from_sheet (or equivalent) in utils.py with scaling to TILE_SIZE.
    status: completed
  - id: player-import-assets
    content: Rewrite Player.import_assets to build animations dict from with_outline/; map to idle/walk_*/attack_* (duplicate or flip for directions).
    status: completed
  - id: player-animate-attack
    content: Adjust Player.animate for non-looping attack sequences and last-frame hold while attacking.
    status: completed
  - id: optional-hurt-death-hitflash
    content: "If desired: wire HURT/DEATH and reconcile hit-flash behavior in Player.draw."
    status: completed
isProject: false
---

# New player sprite animations

## Reference assets and style (scope alignment)

Use these as the **visual baseline** so the animated hero does not clash with the rest of the game:

- **World / props (single PNGs under `assets/sprites/`)**: [`chest.png`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\chest.png) (also used by [`chest.py`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\entities\chest.py)), [`rock.png`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\rock.png), [`stone.png`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\stone.png), [`tree.png`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\tree.png), [`wood.png`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\wood.png) — outlined pixel art, top-down or three-quarter presentation.
- **Items / icons**: [`sword.png`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\sword.png) — relevant when judging attack poses and equipment read at small scale.
- **Legacy static hero reference**: [`player.png`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\player.png) — front-facing single frame; the **animated** set lives in [`assets/sprites/new_player/with_outline/`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\new_player\with_outline) (`IDLE.png`, `WALK.png`, `ATTACK 1.png`, etc.). Code today loads animations from the **folder** [`assets/sprites/player`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\player) via `Entity.load_animations`; that folder may be empty or legacy — implementation should switch to `new_player/with_outline` without assuming the old per-subfolder layout.

**Folder conventions (for later organization; may be empty now):**

- [`assets/sprites/ui`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\ui) — UI chrome; unrelated to player walk cycles unless you add a portrait.
- [`assets/sprites/world`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\world) — tile or map deco; same as above.
- [`data/`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\data) — recipes and saves; no change required for player animation wiring unless you later add data-driven animation metadata (out of scope).

**Related but separate work:** [`docs/UI_Update_temp/UI_update_temp.md`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\docs\UI_Update_temp\UI_update_temp.md) describes inventory grid, tooltips, drag-and-drop, and RS-style interactions. **Do not fold that into this plan** unless you explicitly expand scope; player animation is gameplay/render only.

## Current behavior (what you have today)

- [`Entity.load_animations`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\entities\entity.py) walks each key under a **base folder** and calls [`import_folder`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\core\utils.py), which expects **one subfolder per animation** (e.g. `idle/0.png`, `walk_up/0.png`, …) with optionally many numbered frames.
- [`Player`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\entities\player.py) defines `animations` keys: `idle`, `walk_up` / `walk_down` / `walk_left` / `walk_right`, `attack_up` / `attack_down` / `attack_left` / `attack_right`. [`get_status()`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\entities\player.py) sets those based on movement direction and whether `current_action == "attacking"`.
- [`Player.animate()`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\entities\player.py) **loops** every animation forever; frames are scaled to `(TILE_SIZE, TILE_SIZE)` (32×32 in [`settings.py`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\core\settings.py)).
- [`Player.draw()`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\entities\player.py) **skips drawing entirely** for ~1s after a hit (hit flash), which would hide a `HURT` sprite if you add one unless you change that behavior.

## Your new assets (gap to close)

Under [`assets/sprites/new_player/with_outline/`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\assets\sprites\new_player\with_outline) you have **one PNG per logical animation** (`IDLE`, `WALK`, `RUN`, `JUMP`, `HURT`, `DEFEND`, `DEATH`, `ATTACK 1`–`3`) — not the folder-per-animation layout the loader expects. Those files are very often **horizontal sprite strips** (multiple frames in one image). The implementation depends on which is true:

| If each file is… | What to implement |
|------------------|-------------------|
| A **strip** (width = N × frame_width) | Add a small helper that loads the PNG and **splits** it into N frames (same height), then scales each frame to 32×32. |
| **Single frame** per file | Treat each “animation” as a **1-frame list** so it still works; movement will look static until you add more frames or a strip. |

**First concrete step (before coding):** open one of `IDLE.png` / `WALK.png` in an image editor or check dimensions — if width is a multiple of a consistent frame width (often 32, 64, or 128), plan on strip-splitting.

## Recommended implementation

### 1. Loading utilities ([`src/core/utils.py`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\core\utils.py))

- Add something like `load_frames_from_sheet(path, frame_width, scale_to)` → `list[surface]` that:
  - Loads with `convert_alpha()`, derives frame count from `surface.get_width() // frame_width`, uses `subsurface` per frame.
  - If you prefer **not** to hardcode `frame_width`, add an optional parameter or a constant in `settings` after measuring one asset.
- Keep existing `import_folder` unchanged for other entities.

### 2. Player-specific asset wiring ([`src/entities/player.py`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\entities\player.py))

- Replace the generic `load_animations('assets/sprites/player', …)` call with a dedicated `import_assets()` that:
  - Points at `assets/sprites/new_player/with_outline/` (use [`get_path`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\core\utils.py) for robust paths).
  - Builds **lists of frames** per source file (`IDLE` → idle, `WALK` or `RUN` → all four `walk_*` keys — game has one move speed, so pick one; e.g. use `WALK` for walking).
  - **Maps four directions:** if the art is **single-facing** (common), assign the **same** frame list to `walk_up`, `walk_down`, `walk_left`, `walk_right` (and same for `attack_*`). Optionally `pygame.transform.flip` for `walk_left` / `attack_left` only if the art reads as facing right.
  - **Attacks:** map `ATTACK 1.png`, `ATTACK 2.png`, `ATTACK 3.png` to `attack_*` — simplest v1: use **one** strip (e.g. `ATTACK 1`) for all directions; v2: rotate which strip is used per combat tick for variety (requires storing `attack_variant` on hit tick).
- Ensure a **fallback** if a file is missing (keep colored rect via `Entity.draw`) so the game never silently shows nothing.

### 3. Animation playback tweaks (same file)

- **Attack looping:** today attack anim loops continuously while attacking, which can look like a buzzsaw. Prefer **non-looping** attack playback: when `status` starts with `attack_`, advance frames once through the strip then **hold the last frame** until `current_action` leaves `"attacking"`. That may be a small override of `animate()` only for `Player`, or a `loop` flag on the active animation.
- **Optional extras** (only if you want them in v1): `HURT` on damage (short timer in `take_damage`), `DEATH` during [`GameManager`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\core\game_manager.py) fade — note that during `ui.is_fading` the main update path may not call `player.update`, so death anim may need to be driven from the fade branch or by updating animation in `draw` — scope this only if you care about death/hurt beyond idle/walk/attack.

### 4. Hit-flash vs HURT sprite

- Decide: keep **invisible flash** (current), replace with **HURT** frames briefly, or **reduce opacity** instead of skipping draw. This is a one-place change in `Player.draw()`.

## Files to touch

- [`src/core/utils.py`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\core\utils.py) — sheet splitter (+ optional shared scale helper).
- [`src/entities/player.py`](c:\Users\ziemb\Documents\Github\my-pygame-rpg\src\entities\player.py) — `import_assets`, `get_status` (only if adding new statuses), `animate` (non-loop attack), `draw` (hit feedback).

## Out of scope (unless you ask)

- `JUMP` / `DEFEND` — no matching gameplay state in the current player logic; would need new actions or keybinds.
- Changing `TILE_SIZE` or collision rect to match larger art — only needed if you want native resolution sprites without scaling.
