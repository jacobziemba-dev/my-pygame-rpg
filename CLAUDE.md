# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
pip install -r requirements.txt
python main.py
```

Requires `pygame-ce>=2.5.0`. No test suite exists — all testing is manual by running the game.

## Key Controls

| Key | Action |
|-----|--------|
| WASD / Arrow Keys | Move player |
| Left-click ground | Move to point |
| Left-click entity | Interact (gather, attack, bank, craft) |
| E | Interact with nearby object |
| C | Open crafting menu |
| I | Open inventory |
| K | Open skills panel |
| Space | Attack |
| F5 / F9 | Save / Load |
| F3 | Toggle FPS display |

## Architecture Overview

**Entry point**: `main.py` creates a `GameManager` and calls `.run()`.

**Game loop** (`src/core/game_manager.py`):
```
while running:
  handle_events()   # input, UI state, mouse clicks
  update(dt)        # entities, actions, camera
  draw()            # world, entities, UI
```

### Core Systems (`src/core/`)

- **game_manager.py** — Owns and orchestrates every game entity and system. The central hub.
- **settings.py** — Global constants: screen 1280×720, map 2400×2400, 60 FPS, tile size 32. Change these here.
- **camera.py** — Follows player; constrains viewport to map bounds. All entities draw in camera/screen space.
- **utils.py** — `import_folder()` loads animation frames from a directory; `get_path()` resolves asset paths cross-platform.

### Entity Hierarchy (`src/entities/`)

All drawable objects extend `Entity` (base class with sprite/animation support).

- **player.py** — Movement (keyboard + point-and-click), inventory, skills, HP, equipment, attack/defense.
- **enemy.py** — Simple chase AI within 250px aggro range, HP bar.
- **resource_node.py** — Gatherable nodes (trees, rocks, iron, bushes) with HP, tool requirements, difficulty, skill level requirements, and respawn timers.
- **resource_item.py** — Dropped items on the ground; picked up by clicking or walking nearby.
- **bank.py** — Static storage vault near spawn.
- **station.py** — Furnace / Workbench; queued, timed processing of station recipes.
- **crop.py** — Multi-stage farmable plants (till → plant → harvest).

### Systems (`src/systems/`)

- **inventory.py** — Item quantity tracking; add/remove/craft validation.
- **recipe_manager.py** — Loads `data/recipes.json`; filters by hand-crafting, station type, or name.
- **skill_manager.py** — 30+ skills across Combat, Gathering, Artisan, and Support categories. XP threshold per level = `level × 50`. Handles legacy save key migration (melee→strength, foraging→hunter).
- **action_manager.py** — Processes gathering and combat actions on a 1000ms tick. Calculates success chance from tool power, skill level, and node difficulty. Awards XP and status messages.
- **save_manager.py** — Full world persistence to `data/save.json`: player state, inventory, bank, skills, resource nodes (with respawn timers), enemies, crops, and station queues.

### UI (`src/ui/ui.py`)

Single `UIManager` class renders all HUD and overlay menus (inventory, crafting, skills, bank, station). Menu navigation uses arrow keys + Enter; Esc closes.

## Data Files

- **`data/recipes.json`** — All crafting recipes. Each recipe defines: inputs, outputs, min skill level, XP reward, optional station type (`furnace`/`workbench`), and optional duration. Modify here to add crafting without touching code.
- **`data/save.json`** — Auto-generated save state. Safe to delete to reset the world.

## Asset Conventions

Sprites live in `assets/sprites/{entity_type}/{animation_name}/` as numbered PNGs (`0.png`, `1.png`, …). Expected size is 32×32. The `import_folder()` utility loads them in sorted order.

## Key Design Patterns

- **Manager pattern**: `GameManager` creates and holds references to all systems; systems do not hold references to each other directly — they receive what they need via method arguments.
- **Action ticking**: Long-running actions (gathering, attacking) are processed once per 1000ms tick by `ActionManager`, independent of the 60 FPS render loop.
- **Data-driven crafting**: Adding a recipe requires only a `recipes.json` edit, not code changes.
- **Point-and-click interaction**: Clicking an entity sets the player's movement target and desired action; the action fires once the player is in range.
