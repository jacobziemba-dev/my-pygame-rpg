---
name: GameManager review fixes
overview: Fix a few combat correctness bugs and reduce per-click/per-tick allocations in `game_manager.py` (especially pathfinding obstacle generation), while preserving the OSRS-like 600ms tick feel and context-menu interactions.
todos:
  - id: cache-water-obstacles
    content: Precompute water collision rects in `TileMap` and switch `GameManager._get_solid_obstacles(full_map=True/False)` to use cached rects.
    status: completed
  - id: fix-contact-damage
    content: Make enemy contact damage apply the same value that is displayed, and award Defense XP only when damage is actually applied.
    status: completed
  - id: combat-message-throttle
    content: Reduce per-tick combat chat spam; keep splats and show only important messages with cooldowns.
    status: completed
  - id: context-menu-verbs
    content: Extend resource node verb mapping for coal/essence/wheat/chicken/cow so right-click options are OSRS-like.
    status: completed
  - id: cleanup-local-imports
    content: (Optional) Remove redundant in-function imports in `show_world_context_menu()`.
    status: completed
isProject: false
---

## Key issues found (why these changes)
- **Major perf risk**: `_get_solid_obstacles(full_map=True)` builds **a `pygame.Rect` for every water tile** on every pathfind / chase call (used in `_pathfind_to_entity()` and `_update_chase_destination()`). That’s O(map_tiles) allocations per click/tick and will dominate runtime as the map grows.
- **Combat correctness bug**: Enemy contact damage awards Defense XP and shows message only when `player.take_damage(dmg)` returns truthy, but the displayed `actual = max(1, dmg - defense)` can disagree with what `take_damage()` actually applied (and you might be awarding XP even if damage is mitigated to 0 depending on `take_damage` internals). Also you compute `dmg` then subtract defense into `actual`, but you never apply `actual` to HP here.
- **Message spam / tick feel**: Melee/ranged/magic currently calls `ui.show_message()` every 600ms (“Hit/Missed/Out of arrows/Not enough runes”). This will flood chatbox and drown out important events (very non-OSRS).
- **Context menu verb gaps**: Resource node verb mapping omits newer nodes you already spawn (`coal_rock`, `essence_rock`, `wheat_field`, `chicken`, `cow`). They’ll show generic “Gather …” rather than OSRS-like verbs.
- **Minor architecture smell**: `show_world_context_menu()` re-imports entity classes inside the function; not a big deal but unnecessary and slightly slower.

## Proposed implementation (minimal refactor, high impact)
### 1) Add cached tile-collision representation for water (biggest win)
- **Where**: `[src/core/tilemap.py](src/core/tilemap.py)` and `[src/core/game_manager.py](src/core/game_manager.py)`.
- **Change**:
  - In `TileMap`, precompute **water collision rects once** after map generation, e.g. `self.water_rects` and optionally `self.water_rects_near_camera(camera_rect, padding_tiles)`.
  - Update `GameManager._get_solid_obstacles()`:
    - When `full_map=True`, return `entity_obstacles + self.tilemap.water_rects` instead of rebuilding.
    - When `full_map=False`, call a `TileMap` helper that returns only nearby water rects without scanning the entire map each frame.
- **Why**: removes repeated rect allocations and nested loops in both click-to-move pathfinding and chase updates.

### 2) Fix enemy contact damage application so HP/XPs/messages match
- **Where**: `[src/core/game_manager.py](src/core/game_manager.py)` around:

```1183:1360:src/core/game_manager.py
for enemy in self.enemies[:]:
    enemy.update(...)
    if enemy.rect.inflate(16, 16).colliderect(self.player.rect):
        dmg = random.randint(1, enemy.max_hit)
        if self.player.take_damage(dmg):
            actual = max(1, dmg - self.player.get_defense())
            self._award_xp("defense", 3, ...)
            self.ui.show_message(f"{enemy.name} hits you for {actual}!")
```

- **Change** (pick one consistent model):
  - Option A (recommended): compute `actual` first and pass `actual` into `take_damage(actual)`. Only award Defense XP if `actual > 0` and damage was applied.
  - Ensure death check/respawn trigger still works.
- **Why**: guarantees the number shown equals the HP reduction and XP trigger logic.

### 3) Throttle combat “Hit/Miss” chat messages; keep splats as primary feedback
- **Where**: `[src/core/game_manager.py](src/core/game_manager.py)` in melee branch, projectile hit branch, ranged/magic “out of ammo/runes” branches.
- **Change**:
  - Remove per-tick “Hit/Missed …” messages (or gate them behind a cooldown like once per 2–3 seconds per target).
  - Keep **hit splats** (already great OSRS feedback) and only message on important events:
    - “Out of arrows!” (once per X seconds)
    - “Not enough runes!” (once per X seconds)
    - Kill message (already in `_on_enemy_defeated_xp`)
- **Why**: OSRS doesn’t spam chat every swing; splats + occasional important messages feels closer and is more readable.

### 4) Expand resource context-menu verb mapping to cover all node types you spawn
- **Where**: `[src/core/game_manager.py](src/core/game_manager.py)` inside `show_world_context_menu()`.
- **Change**: extend mapping:
  - `coal_rock`, `essence_rock` → “Mine”
  - `wheat_field` → “Pick”
  - `chicken`, `cow` → “Collect”/“Milk”/“Take” (your call)
- **Why**: preserves the RS feel you’re aiming for.

### 5) (Optional, small) Remove repeated imports inside `show_world_context_menu()`
- **Where**: `[src/core/game_manager.py](src/core/game_manager.py)` lines ~322–328.
- **Change**: delete the local imports and rely on top-level imports.
- **Why**: small cleanup; not critical.

## Test plan (manual)
- **Pathfinding**: click far destinations repeatedly; confirm no hitching and chase still works.
- **Combat**:
  - Let an enemy hit you: confirm displayed damage equals HP loss.
  - Confirm auto-retaliate still triggers when idle.
  - Ranged/magic: run out of arrows/runes and confirm message is not spammed every tick.
- **Context menus**: right-click each node type (tree/rock/iron/coal/essence/wheat/chicken/cow/fishing) and confirm verb feels right.

## Notes / non-goals for this pass
- No networking/multiplayer (aligned with your repo constraint).
- Not extracting a full ECS; keeping changes small/medium and local to existing systems.