# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Vision: A RuneScape-Inspired RPG

This game is a **top-down 2D RPG built with pygame-ce**, designed to feel and play like **Old School RuneScape (OSRS)**. Every design decision should be made with that reference in mind.

### What "RuneScape feel" means for this project

- **Click-to-move**: The player navigates by clicking on the world. WASD is a fallback but the primary input is mouse. Pathfinding (A*) is already implemented.
- **Skill grinding**: Players gain XP by doing repetitive actions (chop trees, mine rocks, fight enemies, cook food, smith bars). Levels gate higher-tier content. The grind *is* the game.
- **XP bars and level-up feedback**: Every skill shows a gold XP bar. Level-ups are celebrated with a message. The player always knows how far they are from the next level.
- **Inventory + bank**: 28-slot style inventory (currently uncapped but should feel limited). Bank stores items long-term. Players should regularly run to the bank.
- **Gathering → Processing → Equipping loop**: Chop logs → smith bars → craft gear → equip → fight harder enemies. This loop is the core progression.
- **Numbers and feedback**: Hit splats (red damage numbers) appear over enemies. XP gains are shown in messages. The player always has feedback on what they did.
- **Runescape aesthetics**: Dark background, gold UI text, tile-based world, HP bar in green/red, brown/tan inventory panels. Fonts are small and clean. No flashy effects — functional and nostalgic.

### What this game is NOT

- Not an action game (no real-time skill combos, no dodge-rolling)
- Not a story-driven RPG (no cutscenes, minimal dialogue)
- Not a platformer or shooter

---

## Running the Game

```bash
pip install -r requirements.txt
python main.py
```

Requires `pygame-ce>=2.5.0`. No test suite — all testing is manual by running the game.

---

## Key Controls

| Key               | Action                                        |
| ----------------- | --------------------------------------------- |
| Left-click ground | Move to point (primary input)                 |
| Left-click entity | Interact: gather, attack, bank, open station  |
| WASD / Arrow Keys | Move player (fallback)                        |
| E                 | Interact with nearby object                   |
| C                 | Open hand-crafting menu                       |
| I                 | Open inventory                                |
| K                 | Open skills panel                             |
| Space             | Attack nearest enemy                          |
| M                 | Toggle melee / ranged combat mode             |
| Tab               | Open / close combat style panel               |
| 1–9               | Activate hotbar slot                          |
| F5 / F9           | Save / Load                                   |
| F3                | Toggle FPS display                            |

---

## Architecture Overview

**Entry point**: `main.py` → creates `GameManager` → calls `.run()`.

**Game loop** (`src/core/game_manager.py`):

```text
while running:
  handle_events()   # input, UI state, mouse clicks
  update(dt)        # entities, actions, camera
  draw()            # world, entities, UI
```

### Core Systems (`src/core/`)

- **game_manager.py** — The central hub. Owns and orchestrates every entity and system. All cross-system logic lives here (combat, gathering ticks, station processing, enemy AI calls).
- **settings.py** — Global constants: screen 1280×720, map 2400×2400, 60 FPS, tile size 32. Tweak world/player constants here.
- **camera.py** — Follows player; constrains viewport to map bounds. All entities must draw in camera/screen space using `camera.apply(rect)`.
- **utils.py** — `import_folder()` loads animation frames from a directory sorted by filename; `get_path()` resolves asset paths cross-platform.

### Entity Hierarchy (`src/entities/`)

All drawable objects extend `Entity` (base class with sprite/animation support).

- **player.py** — Click-to-move with waypoint navigation, keyboard fallback, inventory, skills, HP, equipment, attack/defense. `combat_mode` ("melee"/"ranged") and `combat_style` drive XP routing. `set_combat_mode()`, `set_combat_style()`, `get_xp_skill_for_hit()` are the key methods. `has_bow()` remains a utility check.
- **enemy.py** — Chase AI within 250px aggro range, HP bar above sprite.
- **resource_node.py** — Gatherable world objects (trees, rocks, iron_rock, bushes, fishing_spots). Each has: HP (hits to deplete), tool requirement, drop yield, respawn timer, min skill level. Depleted nodes are passable.
- **resource_item.py** — Items dropped on the ground (from enemies or player drop). Auto-collected on click or nearby walk.
- **projectile.py** — Arrow projectiles spawned every 1000ms tick when `player.combat_mode == "ranged"` and a bow is equipped. Travels to target, applies damage + XP (routed via `get_xp_skill_for_hit()`) on collision.
- **bank.py** — Static 2×2 tile bank near spawn. Opening it shows the bank UI (deposit/withdraw).
- **station.py** — Furnace, Workbench, Stove. Each station processes recipes with a timer. Stores `pending_recipe` so XP is awarded when the player collects output.
- **crop.py** — Multi-stage farmable plants. Player tills, plants seeds, waits, harvests.

### Systems (`src/systems/`)

- **inventory.py** — Item quantity tracking (dict of item_name → count). `add_item`, `remove_item`, `craft` (validates level + materials).
- **recipe_manager.py** — Loads `data/recipes.json`. Provides `get_handcrafted()`, `get_for_station(type)`, `get_all()`.
- **skill_manager.py** — 30+ skills in four categories: Combat, Gathering, Artisan, Support. XP threshold per level = `level² × 30` (quadratic — feels like a proper grind). `gain_xp(skill_name, amount)` returns True on level-up. Handles legacy key migration.
- **action_manager.py** — Processes the 1000ms gathering tick. Calculates success chance from tool power + skill level vs node difficulty. Awards **25 XP** per successful gather. Shows miss/fail messages.
- **save_manager.py** — Full world persistence to `data/save.json`: player state, inventory, bank, skills, resource nodes (with respawn timers), enemies, crops, station queues.
- **pathfinder.py** — A* on a 75×75 tile grid. Called on every left-click. Returns smoothed world-space waypoints. If destination is inside a solid tile, BFS finds nearest walkable neighbor. Bresenham line-of-sight used for path smoothing.

### UI (`src/ui/ui.py`)

Single `UIManager` class. Renders all HUD and menus. Key features:

- **HP bar** (green/red) bottom-left with HP text above it
- **Combat stats** line above HP bar (ATK, STR, CON levels + calculated hit/def values)
- **Skills panel** (K) — scrollable list, skills grouped by category, each showing level + XP/threshold text + **gold XP progress bar**
- **Inventory panel** (I) — 6-column grid of item slots with icons and stack counts; equipped gear section below
- **Crafting menu** (C) — hand-crafted recipes only; shows correct skill level requirement per recipe
- **Bank UI** — dual-pane (player inventory left, bank right); left-click to deposit/withdraw; T to deposit all
- **Station menu** — shown when interacting with furnace/workbench/stove; checks the recipe's actual skill level
- **Hit splats** — floating red damage numbers over enemies; fade and drift upward over 800ms
- **Message bar** — centered yellow text at top for action feedback (3-second duration)
- **Hotbar** — 9 slots bottom-center (48×48px each). Slots hold style shortcuts, `"toggle_combat"`, or item names. Activated by 1–9 keys. Slot 1=TGL, 2=ACC, 3=AGG, 4=DEF, 5=RAP, 6=LNG by default; slots 7–9 empty.
- **Combat tab** (`Tab`) — small overlay above hotbar showing current mode and style selector with XP hints per style. `[M]` toggles melee/ranged mode.
- **Control hints** — bottom-right corner key reminders

---

## Data Files

- **`data/recipes.json`** — All crafting recipes. Fields: `name`, `label`, `inputs` (dict), `outputs` (dict), `min_level`, `xp`, optional `skill` (defaults to `"crafting"`), optional `station` (`"furnace"/"workbench"/"stove"`), optional `duration` (ms). **Adding a recipe only requires editing this file.**
- **`data/save.json`** — Auto-generated. Safe to delete to reset the world.

### Current Recipes

|Recipe|Station|Skill|Min Level|
|------|-------|-----|---------|
|Sword|Hand|Crafting|1|
|Rope|Hand|Crafting|1|
|Fishing Rod|Hand|Crafting|1|
|Bread|Hand|Cooking|1|
|Arrow (×10)|Hand|Fletching|1|
|Shortbow|Hand|Fletching|1|
|Iron Bar|Furnace|Smithing|3|
|Iron Sword|Workbench|Smithing|5|
|Iron Axe|Workbench|Smithing|5|
|Iron Pickaxe|Workbench|Smithing|5|
|Iron Armor|Workbench|Smithing|7|
|Cooked Fish|Stove|Cooking|1|

---

## XP & Progression System

### XP Threshold Formula

`threshold = level² × 30`

|Level|XP to next level|Total XP needed|
|-----|----------------|---------------|
|1|30|30|
|5|750|~2,000|
|10|3,000|~10,000|
|20|12,000|~80,000|
|50|75,000|~1.3M|

### XP Sources

|Action|XP Awarded|
|------|----------|
|Gather resource (tree, rock, ore, fish, bush)|+25 Woodcutting / Mining / Fishing / Hunter|
|Harvest crop|+20 Farming|
|Melee hit (auto or Space) — Accurate style|+5 Attack|
|Melee hit (auto or Space) — Aggressive style|+5 Strength|
|Melee hit (auto or Space) — Defensive style|+5 Defense|
|Enemy kill|+20 Constitution (always) + +20 to active style's primary skill|
|Strength level-up bonus|+2 base_attack|
|Constitution level-up bonus|+10 max_hp|
|Ranged hit (arrow) — Accurate/Rapid style|+4 Ranged|
|Ranged hit (arrow) — Longrange style|+4 Ranged, +2 Defense|
|Take damage from enemy|+3 Defense|
|Hand-craft recipe|XP per recipe (see table), goes to recipe's skill|
|Station collect|XP per recipe × items collected, goes to recipe's skill|

---

## Combat System

- **Melee**: 1000ms auto-attack tick when `player.current_action == "attacking"` and combat falls to the melee branch. Uses `player.rect.inflate(80, 80)` (~56px reach) to check contact. Damage = `player.get_attack()`. XP routed via `player.get_xp_skill_for_hit()`.
- **Ranged**: Fires when `player.combat_mode == "ranged"` **AND** `player.has_bow()`. Spawns a `Projectile` toward target every 1000ms within `RANGED_ATTACK_RANGE = 250px`. Requires arrows in inventory. XP routed via `get_xp_skill_for_hit()`.
- **Combat branching**: Ranged requires BOTH `combat_mode == "ranged"` and `has_bow()`. If either is false, combat falls through to melee. Equipping a shortbow auto-sets `combat_mode = "ranged"`. Loading a save with shortbow equipped auto-detects ranged mode for backwards compatibility.
- **Out-of-range chasing**: If enemy is out of melee or ranged reach during the tick, the player's `target_destination` is updated directly (without calling `set_target_destination`) so `current_action` stays `"attacking"` and the player chases the enemy without losing attack state.
- **Space bar**: Instant-hits nearest enemy if within `inflate(80,80)` range, then sets up the auto-attack loop via `set_target_destination`. If out of range, pathfinds to the enemy to begin the loop.
- **Combat styles**: `player.combat_style` controls XP routing. Melee: `accurate` (Attack XP), `aggressive` (Strength XP), `defensive` (Defense XP). Ranged: `accurate`/`rapid` (Ranged XP), `longrange` (Ranged + Defense XP).
- **Mode/style switching**: `M` key toggles mode; `Tab` opens style selector panel; hotbar slots 1–6 also switch styles. `player.set_combat_mode()` resets style to mode default.
- **Enemy AI**: Enemies chase player within 250px. Collide with player rect and deal 10 damage per collision (1-second cooldown on player side).
- **Hit splats**: Red floating numbers appear above enemies when hit. Fade and drift upward over 800ms.
- **Defense XP**: Player earns +3 Defense XP each time they successfully take damage.

---

## Asset Conventions

Sprites: `assets/sprites/{entity_type}/{animation_name}/0.png, 1.png, …` (32×32 px, sorted order).

Player animations expected: `idle`, `walk_up`, `walk_down`, `walk_left`, `walk_right`, `attack_up`, `attack_down`, `attack_left`, `attack_right`.

Item icons: `assets/sprites/{item_name}.png` (32×32). The UI falls back to a 2-letter abbreviation if no icon exists.

---

## Key Design Patterns

- **Manager pattern**: `GameManager` creates and holds all systems. Systems receive what they need as arguments — they do not reference each other directly.
- **Action ticking**: Gathering and combat actions process once per 1000ms tick inside `GameManager.update()`. This is independent of the 60 FPS render loop.
- **Combat branching**: The 1000ms tick checks `combat_mode == "ranged" and has_bow()` for ranged (spawns Projectile), else melee (inflate(80,80) collision). XP always flows through `player.get_xp_skill_for_hit()`. Out-of-range: directly set `player.target_destination` (not `set_target_destination`) to chase without clearing `current_action`.
- **Data-driven crafting**: All recipes live in `recipes.json`. Add `"skill"` to route XP to the correct skill. Add `"station"` to require a workstation. No code changes needed for new recipes.
- **Skill-level checks**: Both the UI (display) and the game logic (crafting, gathering) check `recipe.get("skill", "crafting")` to get the right skill level. Do not hardcode `crafting.level` for smithing/cooking/fletching recipes.
- **Station XP**: When `_handle_station_input` starts processing, it sets `station.pending_recipe = recipe`. When the player collects output (`_interact` or click path in `player.py`), the game awards `recipe["xp"] × collected` to `recipe["skill"]` and clears `pending_recipe`.
- **Point-and-click interaction**: Clicking an entity pathfinds to the nearest walkable adjacent tile. Interaction triggers only on arrival at the final waypoint. Intermediate waypoints do not fire interactions.
- **Waypoint movement**: `player.set_target_destination()` accepts an optional `waypoints` list. Player walks waypoints in order; only the last waypoint triggers interaction and snapping.
- **Solid-object collision**: Axis-separated resolution via `resolve_collision_x` / `resolve_collision_y` (in `entity.py`). `GameManager._get_solid_obstacles()` returns active non-fishing ResourceNodes + stations + bank each frame.
- **Y-sorted rendering**: Stations, enemies, bank, and player are sorted by `rect.bottom` before drawing. Ground-level objects (nodes, crops, projectiles) draw first without sorting.
- **Hit splats**: `ui.add_hit_splat(damage, world_x, world_y, camera)` converts world coords to screen and appends to `ui.hit_splats`. Drawn each frame with fade-out alpha and upward drift. Removed in `update()` after `_splat_duration` (800ms).

---

## RuneScape Feature Checklist

Use this to guide future development. Checked items are implemented.

### Core Loop

- [x] Click-to-move with A* pathfinding
- [x] Skill XP / level system with quadratic curve
- [x] Gold XP progress bars per skill in skills panel
- [x] Gathering (woodcutting, mining, fishing, farming, hunter)
- [x] Crafting menu (hand-crafted recipes)
- [x] Station crafting (furnace, workbench, stove) with correct skill XP
- [x] Bank (deposit / withdraw / deposit-all)
- [x] Inventory system with item icons
- [x] Equipment system (sword, iron_sword, iron_armor, shortbow)
- [x] Melee and ranged combat with XP rewards
- [x] Hit splat damage numbers over enemies
- [x] Defense XP on taking damage
- [x] Save / Load world state
- [x] Combat style system (Accurate/Aggressive/Defensive melee; Accurate/Rapid/Longrange ranged)
- [x] Hotbar (9 slots, 1–9 keys, default-populated with style shortcuts)
- [x] Combat tab panel (Tab key) showing mode + style selector with XP hints

### Next Priority Features

- [ ] **More enemy types** — different sprites, HP, damage, drops, and XP rewards per enemy type (e.g. goblin, skeleton, guard)
- [ ] **Item tier progression** — Bronze → Iron → Steel → Mithril. Each tier requires higher smithing level and gives better stats
- [ ] **Unequip system** — clicking an equipped item should unequip it back to inventory
- [ ] **Level-gated equipment** — iron_armor requires Defense Lv.10; iron_sword requires Attack Lv.5
- [ ] **More recipes** — at least 5 recipes per crafting skill; currently very sparse
- [ ] **Minimap** — small world map in corner showing player position (classic RS feature)
- [ ] **XP drop messages** — RS-style "+25 Woodcutting" text that floats near the player (distinct from hit splats)
- [ ] **Inventory cap** — limit inventory to 28 slots (RS standard); force player to bank
- [ ] **Item weight / encumbrance** — optional RS3 mechanic
- [ ] **Respawn on death** — player dies → respawns at bank with items kept (or dropped, configurable)
- [ ] **NPC dialogue** — simple right-click interact → text box (e.g. bank teller, shop)
- [ ] **Shop / general store** — buy basic supplies, sell gathered resources for gold
- [ ] **Gold currency** — enemies and shops use gold; gives economy structure

### Visual / Polish

- [ ] Tile map with grass/dirt/water tiles instead of solid green background
- [ ] Player sprite with proper RS-style top-down perspective
- [ ] Animated resource nodes (tree sway, ore sparkle)
- [ ] Sound effects (hit sounds, level-up jingle, gather sound)
- [ ] Level-up visual effect (fireworks / glow flash)
- [ ] Item drop names visible on the ground (text label under ResourceItem)
