# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Recently Implemented

### Visual & Aesthetic Overhaul (Milestone 3 Complete)
- **Authentic Stone UI**: All game panels (inventory, shop, bank, dialogues) now render using seamlessly tiled stone textures (`stone_panel.png`) instead of flat rectangles.
- **Dynamic Circular Minimap**: Added a real-time minimap overlay tracking the player, NPCs, ground items, and resources. 
- **Procedural World Mapping**: Replaced the static flat grass with noise-based procedural world boundaries consisting of dirt paths and water edges. 
- **Typography & Interaction**: Ground drops feature text labels with drop shadows. Hitsplats use dynamic red/blue starburst sprites. Left-clicking to pathfind spawns an authentic flashing yellow crosshair.
- **The Steel Tier & Economy**: Added `coal_rock` natively scaling off Lv. 15 Mining. `coins` separated from base inventory into a tracking UI overlay (money pouch system). `Talk-to` context actions built for interactive RS dialogues.

---

## 🗺️ Milestone 4: Magic & The Offline Quest System

> **Development Constraint**: This game is strictly an OFFLINE, single-player RPG. Under no circumstances will online, multiplayer, or networking mechanics be introduced. All features must simulate the rich MMO experience natively without relying on external servers.

### Phase 1: Magic Combat & Runecrafting
- **The Runecrafting Loop**:
  - Add `rune_essence_rock` entities scaling off the Mining skill. Mining yields `rune_essence`.
  - Add Altar objects (e.g., Air Altar). Players interact with Altars to convert essence into specific elemental runes, awarding Runecrafting XP.
- **The Spellbook UI**:
  - Create a new UI Sidebar tab containing a grid of castable spells.
  - Each spell dictates a minimum Magic level and specific rune cost ratios (e.g., *Air Strike* requires 1 Mind Rune, 1 Air Rune).
- **Magic Combat Integration**:
  - Add magical weapons (staves/wands) that, when equipped, route attack logic to use the Magic skill.
  - Update the 600ms combat loop in `game_manager.py`: When attacking via magic, verify the inventory has the required runes for the active spell, deduct the runes, and calculate damage against the enemy's magical defense using quadratic XP scaling.

### Phase 2: The Single-Player Quest Engine
- **Stateful Dialogue Trees**:
  - Upgrade from linear flavor text to a robust dialogue payload system capable of multiple-choice branching paths, player responses, item requirement checks, and quest state flags.
- **Quest Journal UI**:
  - Add a dedicated Quest list in the sidebar showing Unlocked, Active, and Completed quests in classic red/yellow/green text formatting.
- **"The Baker's Assistant" Starter Quest**:
  - A multi-step introductory quest requiring the player to speak to a Baker NPC, agree to the quest, gather three specific processed materials (e.g., Wheat, Egg, Milk), and return them.
  - On completion, award the player highly visible Quest Points, a lump sum of Cooking XP, and access to a previously locked high-tier Stove.

## Vision: A RuneScape-Inspired RPG

This game is a **top-down 2D RPG built with pygame-ce**, designed to feel and play like **Old School RuneScape (OSRS)**. **Every design decision — controls, combat, UI, progression, economy — must be made with OSRS as the reference.** When in doubt, ask: "Does this feel like RuneScape?" If yes, do it. If not, rethink it.

### What "RuneScape feel" means for this project

- **Right-click context menus everywhere**: Right-clicking any entity in the world shows a RS-style dropdown with verb-colored options ("Attack Goblin", "Chop Tree", "Walk here"). This is already implemented and must be maintained for all new entities.
- **Click-to-move as the primary input**: The player navigates by clicking on the world. WASD movement has been removed to enforce this. Pathfinding (A*) is already implemented. New movement or interaction features should always default to mouse-driven.
- **Tick-based combat**: Attacks fire on a 600ms tick, not in real time. No button mashing. The player clicks an enemy and watches the numbers roll. This pacing is intentional and RS-authentic.
- **Miss/splash system**: Attacks can miss based on accuracy vs enemy defense. Low-level players vs high-level enemies should miss often. Blue "0" splats on miss, red numbers on hit — exactly like OSRS.
- **Auto-retaliate**: When an enemy hits the player and the player is idle, automatically fight back. This is the RS default and must always be on.
- **Skill grinding**: Players gain XP by doing repetitive actions (chop trees, mine rocks, fight enemies, cook food, smith bars). Levels gate higher-tier content. The grind *is* the game — do not short-circuit it.
- **XP bars and level-up feedback**: Every skill shows a gold XP bar. Level-ups are celebrated with a message. XP drops float near the player for immediate feedback.
- **Inventory + bank**: 28-slot inventory cap is enforced. Bank stores items long-term. Players should regularly run to the bank. The inventory being full and needing to bank is a core gameplay loop.
- **Gathering → Processing → Equipping loop**: Chop logs → smith bars → craft gear → equip → fight harder enemies. Every feature added should reinforce this loop.
- **Enemy variety and scaling**: Different enemies have different combat levels, HP, max hits, drops, and aggro behavior. Weaker enemies near spawn, stronger ones further away. Players should feel progression pressure.
- **Economy via drops and shops**: Enemies drop coins and items. A general store lets players buy supplies and sell loot. Gold is the universal currency. This gives purpose to grinding.
- **Numbers and feedback**: Hit splats (red/blue) over enemies, XP drops near player, level-up messages, action feedback in the message bar. The player should always know exactly what happened.
- **RS aesthetics**: Dark background, gold UI text, tile-based world, green/red HP bars, brown/tan inventory panels. Fonts small and clean. No particle explosions or screen shake — functional and nostalgic.

### Design rules for all future features

1. **If it exists in OSRS, model it after OSRS.** Don't invent a new system when RS already has a proven one.
2. **Mouse first.** Every new interaction should be right-clickable with a context menu and left-click default action.
3. **Skill gates everything.** New content should require skill levels to access. This creates natural progression.
4. **Drops matter.** Every enemy should have a meaningful drop table. Coins, bones, and at least one unique drop per enemy type.
5. **The grind is the point.** Don't make leveling too fast. The quadratic XP curve is intentional. Resist the urge to inflate XP rewards.
6. **Feedback is mandatory.** Every action must produce visible feedback: a message, a splat, a floating number, or an animation.

### What this game is NOT

- **Absolutely NOT a multiplayer or online game** (There is zero networking, zero connection handling, and zero multiplayer mechanics. It is exclusively an offline, single-player recreation).
- Not an action game (no real-time skill combos, no dodge-rolling, no stamina bars)
- Not a story-driven RPG (no cutscenes, minimal dialogue — RS has almost none)
- Not a platformer or shooter
- Not a game where you hold down keys to fight — it's click-to-interact, tick-to-resolve

---

## Running the Game

```bash
pip install -r requirements.txt
python main.py
```

Requires `pygame-ce>=2.5.0`. No test suite — all testing is manual by running the game.

---

## Key Controls

| Key / Input        | Action                                                      |
| ------------------ | ----------------------------------------------------------- |
| Left-click ground  | Move to point (primary input)                               |
| Left-click entity  | Default action: gather, attack, open bank/shop/station, pick up  |
| Right-click world  | RS-style context menu ("Chop Tree", "Attack Enemy", etc.)   |
| Right-click inv    | Context menu: Use/Equip, Drop, Examine, Remove (equipped)   |
| ESC                | Close context menu / close open panels                      |
| E                  | Interact with nearby object                                 |
| C                  | Open hand-crafting menu                                     |
| I                  | Open inventory                                              |
| K                  | Open skills panel                                           |
| Space              | Attack nearest enemy                                        |
| M                  | Toggle melee / ranged combat mode                           |
| Tab                | Open / close combat style panel                             |
| 1–9                | Activate hotbar slot                                        |
| F5 / F9            | Save / Load                                                 |
| F3                 | Toggle FPS display                                          |

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

- **player.py** — Click-to-move with waypoint navigation, inventory, skills, HP, equipment, attack/defense. `combat_mode` ("melee"/"ranged") and `combat_style` drive XP routing. `set_combat_mode()`, `set_combat_style()`, `get_xp_skill_for_hit()` are the key methods. `has_bow()` remains a utility check.
- **enemy.py** — Three typed enemies (goblin/skeleton/guard). Each has `name`, `combat_level`, `hp`, `defense_level`, `max_hit`, `speed`, `aggro_range`, `drops`, `respawn_time`, `xp_reward`, `spawn_x/y`. HP bar appears only after first hit. Name + "(lvl X)" label always visible above sprite.
- **resource_node.py** — Gatherable world objects (trees, rocks, iron_rock, bushes, fishing_spots). Each has: HP (hits to deplete), tool requirement, drop yield, respawn timer, min skill level. Depleted nodes are passable.
- **resource_item.py** — Items dropped on the ground (from enemies or player drop). Auto-collected on click or nearby walk.
- **projectile.py** — Arrow projectiles spawned every 600ms tick when `player.combat_mode == "ranged"` and a bow is equipped. Travels to target, applies damage + XP (routed via `get_xp_skill_for_hit()`) on collision.
- **bank.py** — Static 2×2 tile bank near spawn. Opening it shows the bank UI (deposit/withdraw).
- **shop.py** — Static 2×2 tile general store near spawn. Supports fixed-price buy/sell trading via the shop UI.
- **station.py** — Furnace, Workbench, Stove. Each station processes recipes with a timer. Stores `pending_recipe` so XP is awarded when the player collects output.
- **crop.py** — Multi-stage farmable plants. Player tills, plants seeds, waits, harvests.

### Systems (`src/systems/`)

- **inventory.py** — Item quantity tracking (dict of item_name → count). `add_item`, `remove_item`, `craft` (validates level + materials).
- **recipe_manager.py** — Loads `data/recipes.json`. Provides `get_handcrafted()`, `get_for_station(type)`, `get_all()`.
- **skill_manager.py** — 30+ skills in four categories: Combat, Gathering, Artisan, Support. XP threshold per level = `level² × 30` (quadratic — feels like a proper grind). `gain_xp(skill_name, amount)` returns True on level-up. Handles legacy key migration.
- **action_manager.py** — Processes the 600ms gathering tick. Calculates success chance from tool power + skill level vs node difficulty. Awards **25 XP** per successful gather. Shows miss/fail messages.
- **save_manager.py** — Full world persistence to `data/save.json`: player state, inventory, bank, skills, resource nodes (with respawn timers), enemies, crops, station queues.
- **pathfinder.py** — A* on a 75×75 tile grid. Called on every left-click. Returns smoothed world-space waypoints. If destination is inside a solid tile, BFS finds nearest walkable neighbor. Bresenham line-of-sight used for path smoothing.

### UI (`src/ui/ui.py`)

Single `UIManager` class. Renders all HUD and menus. Key features:

- **HP bar** (green/red) bottom-left with HP text above it
- **Combat stats** line above HP bar (ATK, STR, CON levels + calculated hit/def values)
- **Sidebar Panels** — persistently drawn in the bottom-right corner, driven by an `active_tab` state.
  - **Skills panel** (K) — scrollable list, skills grouped by category, each showing level + XP/threshold text + gold XP progress bar.
  - **Inventory panel** (I) — 5-column grid of item slots with icons and stack counts; equipped gear section below.
  - **Crafting menu** (C) — hand-crafted recipes only; shows correct skill level requirement per recipe.
  - **Combat tab** (Tab) — small panel showing current mode and style selector with XP hints per style. `[M]` toggles melee/ranged mode.
- **Bank UI** — Center screen UI, dual-pane (player inventory left, bank right); left-click to deposit/withdraw; T to deposit all
- **Shop UI** — Center screen UI, dual-pane (shop stock left, player inventory right); left-click to buy/sell one item with coin checks and stock updates
- **Station menu** — Center screen UI, shown when interacting with furnace/workbench/stove; checks the recipe's actual skill level
- **Hit splats** — floating damage numbers over enemies; red for hits, blue "0" for misses (RS splash); fade and drift upward over 800ms.
- **Chatbox Messages** — localized log at the bottom-left of the screen for action feedback. Stores recent messages and fades them after 10 seconds.
- **Hotbar** — 9 slots bottom-center (48×48px each). Slots hold style shortcuts, `"toggle_combat"`, or item names. Activated by 1–9 keys.
- **Control hints** — bottom-right corner key reminders
- **Right-click context menu** — RS-style popup on right-click anywhere in the world. Shows verb-colored options (gold verb + white target, e.g. "Chop Tree", "Attack Enemy", "Walk here"). Left-click an option to execute; click elsewhere or press ESC to dismiss. Also shown on right-click of inventory items ("Use", "Drop", "Examine"). Rendered by `UIManager`: `show_context_menu(pos, options)`, `handle_context_menu_click(pos)`, `_draw_context_menu(surface)`.

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
|Enemy kill — combat skill|+`enemy.xp_reward` to active style's primary skill (13 goblin → 88 guard)|
|Enemy kill — Constitution|+`enemy.xp_reward // 3` (always; goblin=4, skeleton=16, guard=29)|
|Strength level-up bonus|+2 base_attack|
|Constitution level-up bonus|+10 max_hp|
|Ranged hit (arrow) — Accurate/Rapid style|+4 Ranged|
|Ranged hit (arrow) — Longrange style|+4 Ranged, +2 Defense|
|Take damage from enemy|+3 Defense|
|Hand-craft recipe|XP per recipe (see table), goes to recipe's skill|
|Station collect|XP per recipe × items collected, goes to recipe's skill|

---

## Combat System

- **Melee**: 600ms auto-attack tick when `player.current_action == "attacking"` and combat falls to the melee branch. Uses `player.rect.inflate(80, 80)` (~56px reach) to check contact. Damage = `player.get_attack()`. All hits go through `_roll_hit()` for miss chance. XP routed via `player.get_xp_skill_for_hit()`.
- **Ranged**: Fires when `player.combat_mode == "ranged"` **AND** `player.has_bow()`. Spawns a `Projectile` toward target every 600ms within `RANGED_ATTACK_RANGE = 250px`. Requires arrows in inventory. Miss checked on projectile impact via `_roll_hit()`.
- **Miss mechanic**: `GameManager._roll_hit(base_damage, enemy)` → `(damage, is_hit)`. Hit chance = `clamp(0.50 + (attack_level − enemy.defense_level) × 0.025, 0.10, 0.95)`. Misses show a blue "0" hit splat (`add_hit_splat(..., is_miss=True)`).
- **Combat branching**: Ranged requires BOTH `combat_mode == "ranged"` and `has_bow()`. If either is false, combat falls through to melee. Equipping a shortbow auto-sets `combat_mode = "ranged"`. Loading a save with shortbow equipped auto-detects ranged mode for backwards compatibility.
- **Out-of-range chasing**: If enemy is out of melee or ranged reach during the tick, the player's `target_destination` is updated directly (without calling `set_target_destination`) so `current_action` stays `"attacking"` and the player chases the enemy without losing attack state.
- **Space bar**: Instant-hits nearest enemy if within `inflate(80,80)` range with miss roll, then sets up the auto-attack loop. If out of range, pathfinds to the enemy.
- **Auto-retaliate**: When an enemy lands a hit on the player and `player.current_action is None`, the player automatically pathfinds to and attacks that enemy (classic RS default).
- **Enemy AI**: Enemies chase player within their `aggro_range`. Collision damage = `random.randint(1, enemy.max_hit)` reduced by player defense (1s cooldown). Each enemy type has its own aggro range and speed.
- **Enemy death**: `_kill_enemy(enemy)` removes the enemy, calls `_on_enemy_drops()` (type-specific drop table), `_on_enemy_defeated_xp()` (scales with `enemy.xp_reward`), and adds to `respawn_queue`.
- **Enemy respawn**: `respawn_queue = [(respawn_at_ms, enemy_type, spawn_x, spawn_y)]`. Each tick in `update()`, expired entries spawn a new Enemy at the original spawn location.
- **Enemy drops**: Defined per type in `ENEMY_TYPE_STATS["drops"]` as `[(item, min, max, chance)]`. All enemies drop bones (100%). Guards also drop coins (80%) and rarely iron_bar (10%).
- **Kill XP**: `_on_enemy_defeated_xp(enemy)` awards `enemy.xp_reward` to the active combat skill and `xp_reward // 3` to Constitution. Scales from 13 XP (goblin) to 88 XP (guard).
- **Combat styles**: `player.combat_style` controls XP routing. Melee: `accurate` (Attack XP), `aggressive` (Strength XP), `defensive` (Defense XP). Ranged: `accurate`/`rapid` (Ranged XP), `longrange` (Ranged + Defense XP).
- **Mode/style switching**: `M` key toggles mode; `Tab` opens style selector panel; hotbar slots 1–6 also switch styles. `player.set_combat_mode()` resets style to mode default.
- **Hit splats**: `add_hit_splat(damage, wx, wy, camera, is_miss=False)` — red for hits, blue for misses. Fade and drift upward over 800ms.
- **Defense XP**: Player earns +3 Defense XP each time they successfully take damage.

---

## Asset Conventions

Sprites: `assets/sprites/{entity_type}/{animation_name}/0.png, 1.png, …` (32×32 px, sorted order).

Player animations expected: `idle`, `walk_up`, `walk_down`, `walk_left`, `walk_right`, `attack_up`, `attack_down`, `attack_left`, `attack_right`.

Item icons: `assets/sprites/{item_name}.png` (32×32). The UI falls back to a 2-letter abbreviation if no icon exists.

---

## Key Design Patterns

- **Manager pattern**: `GameManager` creates and holds all systems. Systems receive what they need as arguments — they do not reference each other directly.
- **Action ticking**: Gathering and combat actions process once per 600ms tick inside `GameManager.update()`. This is independent of the 60 FPS render loop.
- **Combat branching**: The 600ms tick checks `combat_mode == "ranged" and has_bow()` for ranged (spawns Projectile), else melee (inflate(80,80) collision). XP always flows through `player.get_xp_skill_for_hit()`. Out-of-range: directly set `player.target_destination` (not `set_target_destination`) to chase without clearing `current_action`.
- **Data-driven crafting**: All recipes live in `recipes.json`. Add `"skill"` to route XP to the correct skill. Add `"station"` to require a workstation. No code changes needed for new recipes.
- **Skill-level checks**: Both the UI (display) and the game logic (crafting, gathering) check `recipe.get("skill", "crafting")` to get the right skill level. Do not hardcode `crafting.level` for smithing/cooking/fletching recipes.
- **Equipment/tool requirements**: Wield requirements are centralized in `EQUIPMENT_REQUIREMENTS` in `settings.py` (currently iron_sword/iron_axe/iron_pickaxe Attack 5, iron_armor Defense 10). Enforce these gates through item use/equip flows.
- **Station XP**: When `_handle_station_input` starts processing, it sets `station.pending_recipe = recipe`. When the player collects output (`_interact` or click path in `player.py`), the game awards `recipe["xp"] × collected` to `recipe["skill"]` and clears `pending_recipe`.
- **Right-click context menu**: `GameManager.show_world_context_menu(screen_pos)` detects the entity under the cursor via `_find_entity_at_world()`, builds a list of `{"label": str, "action": callable}` options, and passes them to `ui.show_context_menu()`. Left-clicking an option calls `ui.handle_context_menu_click()` which returns the stored callable. Any other click or ESC dismisses it. Inventory right-click goes through `_show_inventory_context_menu()`. Entity pathfinding is extracted to `_pathfind_to_entity(world_x, world_y, entity)`.
- **Point-and-click interaction**: Clicking an entity pathfinds to the nearest walkable adjacent tile. Interaction triggers only on arrival at the final waypoint. Intermediate waypoints do not fire interactions.
- **Waypoint movement**: `player.set_target_destination()` accepts an optional `waypoints` list. Player walks waypoints in order; only the last waypoint triggers interaction and snapping.
- **Solid-object collision**: Axis-separated resolution via `resolve_collision_x` / `resolve_collision_y` (in `entity.py`). `GameManager._get_solid_obstacles()` returns active non-fishing ResourceNodes + stations + shop + bank each frame.
- **Y-sorted rendering**: Stations, enemies, shop, bank, and player are sorted by `rect.bottom` before drawing. Ground-level objects (nodes, crops, projectiles) draw first without sorting.
- **Hit splats**: `ui.add_hit_splat(damage, world_x, world_y, camera, is_miss=False)` converts world coords to screen. Red for hits, blue for misses. Drawn each frame with fade-out alpha and upward drift. Removed in `update()` after `_splat_duration` (800ms).
- **Enemy types**: Defined entirely in `ENEMY_TYPE_STATS` in `settings.py`. Adding a new enemy type requires only a new dict entry there — no changes to `enemy.py` or `game_manager.py`. Then add it to `_generate_enemies()` with a count constant.

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
- [x] Right-click context menu (RS-style: verb-colored options for all world entities + inventory items)
- [x] Multiple enemy types — Goblin (lvl 2), Skeleton (lvl 13), Guard (lvl 22) with individual stats, drops, aggro ranges
- [x] Enemy respawn — each type respawns at spawn location after type-specific delay (25–60s)
- [x] Miss / splash mechanic — attacks can miss based on attack level vs enemy defense; blue "0" splat
- [x] Auto-retaliate — player automatically attacks back when hit while idle
- [x] Type-specific enemy drops — bones always, coins scaled to difficulty, guards can drop iron bars

### Next Priority Features

Ordered by RS-authenticity impact. Do these in order when possible.

#### Combat & Progression

- [x] **XP drop messages** — RS-style "+25 Woodcutting" yellow text floating upward near the player on every XP gain (distinct from hit splats; use same fade/drift system)
- [x] **Level-gated equipment** — iron_sword requires Attack Lv.5; iron_armor requires Defense Lv.10; iron_axe/pickaxe require Attack Lv.5. Show "You need Attack Lv.X to wield this." message
- [x] **Unequip system** — right-clicking an equipped item in the inventory shows "Remove" option; unequips back to inventory
- [x] **Respawn on death** — player dies → fades to black → respawns at bank spawn point with all items kept (RS "safe death" mode). Reset HP to full.
- [ ] **Item tier progression** — add Steel tier (requires Smithing Lv.20+) above Iron. Steel sword, steel armor, steel axe/pickaxe. Each tier is a meaningful power step.

#### Economy

- [ ] **Gold currency** — coins stack in inventory; displayed separately in HUD. Enemies already drop coins — wire them up as a real currency value.
- [x] **Shop / general store** — NPC near spawn. Right-click → "Trade". Sells: bronze/iron tools, arrows, bread, seeds. Buys: gathered resources for coins. Uses the context menu system.
- [x] **Bones → Prayer XP** — right-click bones in inventory → "Bury" → +4 Prayer XP. Adds Prayer as a real skill.

#### UI / Inventory

- [x] **Inventory cap** — hard limit of 28 slots. When full, show "Your inventory is full." and prevent picking up. Forces bank runs — core RS loop.
- [ ] **Minimap** — small square map in top-right corner. Shows player dot (white), enemies (red dots), bank (yellow dot), resource nodes (green dots). Updates each frame.
- [ ] **Item drop names** — text label under each ResourceItem on the ground showing the item name (RS style). Small font, white text with black shadow.

#### World

- [ ] **Tile map** — replace solid green background with proper grass/dirt/path tiles. Water tiles as impassable borders. Makes the world feel like RS.
- [ ] **Zones by enemy difficulty** — goblins near spawn (safe area), skeletons mid-distance, guards further out. Player naturally progresses outward as they level up.
- [ ] **NPC dialogue** — right-click NPC → "Talk-to" → simple text box overlay. Bank teller, shopkeeper. No branching trees needed — just flavor text + one action.

### Visual / Polish

- [ ] Player sprite with RS-style top-down perspective (current placeholder is fine but RS aesthetic is small, top-down, slightly isometric-feeling)
- [ ] Animated resource nodes (tree sway on chop hit, ore sparkle when mining)
- [ ] Sound effects (hit sound on attack, level-up jingle, coin pickup clink, gather thud)
- [ ] Level-up visual effect — gold flash + "Congratulations, you've reached level X!" overlay panel (classic RS style)
- [ ] Item drop names visible on the ground (text label under ResourceItem)
