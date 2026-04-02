# My Pygame RPG

---

## 📝 Overview

A 2D RPG built with **Python** and **Pygame**.

The player explores a world, collects resources, crafts items, fights enemies, and levels up.

### 🎮 Controls

| Key | Action |
| --- | --- |
| **WASD** / **Arrow keys** | Move |
| **E** | Collect resource |
| **C** | Craft item |
| **Q** | Drop item |
| **Space** | Attack |
| **S** | Save game |
| **L** | Load game |

### 🚀 How to Run

```bash
pip install pygame
python main.py
```

---

> **Currently working on:** v0.6 — 📈 Player Progression

---

## ⏳ Core Milestones

These milestones make up the MVP — a playable RPG with movement, combat, and progression.

---

### v0.1 — 🏗️ Project Setup ✅

- [x] Pygame window, game loop, and quit handling
- [x] `Player` class with rectangle rendering
- [x] `src/` folder structure and module imports

---

### v0.1.5 — 🕹️ Player Movement

- [x] Add `speed` to the `Player` class
- [x] Add `update()` to read keyboard input and move the player
- [x] Call `player.update()` in the main loop before drawing
- [x] Clamp position so the player cannot move off screen
- [x] 📸 Screenshot: player moving around the screen

---

### v0.2 — ⛏️ Resources & Crafting

**🌱 Resources:**

- [x] Wood and stone spawn at random positions at game start
- [x] Press **E** to collect a resource when the player overlaps it
- [x] Remove the resource from the world after collecting

**🎒 Inventory:**

- [x] Store collected items as a dictionary — example: `{ "wood": 2, "stone": 1 }`
- [x] Show inventory updates in the console

**⚒️ Crafting:**

- [x] Press **C** to craft a sword (requires wood + stone)
- [x] Show a success message if crafting works
- [x] Show a helpful error if resources are missing

**📁 Code:**

- [x] Add `ResourceItem` and `Inventory` classes in `src/`
- [x] 📸 Screenshot: resources on the map, console showing inventory and crafting

---

### v0.3 — 🗂️ Code Structure

- [x] Create `src/inventory.py` and `src/resource_item.py`
- [x] Create a `GameManager` class for game state and the main loop
- [x] Keep all classes in separate files under `src/`
- [x] 📸 Screenshot: folder structure showing all modules

---

### v0.4 — 🖼️ Sprites & UI

**🎨 Sprites:**

- [x] Load sprites from `assets/sprites/` using `pygame.image.load`
- [x] Fall back to a colored rectangle if a sprite file is missing
- [x] Name sprite files clearly — example: `player.png`, `wood.png`
- [x] Make sure sprite bounds match collision rectangles

**🖥️ UI:**

- [x] Create a `UIManager` class in `src/ui.py`
- [x] Show inventory on screen with item icons and counts
- [x] Show event notifications — example: "Collected wood", "Sword crafted"
- [x] Flash or highlight the player when collecting or crafting

- [x] 📸 Screenshot: sprites and inventory UI visible in game

---

### v0.5 — ⚔️ Combat & Enemies

**👾 Enemies:**

- [x] Create an `Enemy` class in `src/enemy.py`
- [x] Enemies spawn at set positions on the map
- [x] Add basic AI — chase the player when in range, idle otherwise
- [x] Enemies have HP and can take damage

**❤️ Health:**

- [x] Player has HP — shown as a health bar on screen
- [x] Enemies deal damage on contact with the player
- [x] Player respawns or game ends at 0 HP

**⚔️ Combat:**

- [x] Press **Space** to attack nearby enemies
- [x] Hitting an enemy reduces their HP
- [x] Defeated enemies drop loot or XP

- [x] 📸 Screenshot: enemy on screen, health bars visible, combat happening

---

### v0.6 — 📈 Player Progression

**📊 Stats:**

- [ ] Player has base stats: HP, attack, defense
- [ ] Stats are shown in the UI

**⭐ XP & Leveling:**

- [ ] Defeating enemies awards XP
- [ ] Reaching an XP threshold increases the player's level
- [ ] Leveling up improves stats — example: +10 max HP, +1 attack

**🗡️ Equipment:**

- [ ] Crafted items like the sword can be equipped
- [ ] Equipped items boost player stats

- [ ] 📸 Screenshot: level and stats shown in UI, equipment visible

---

### v0.7 — 🗺️ World & Map

- [ ] Add a scrolling camera for a world larger than the screen
- [ ] Build a simple tile-based map
- [ ] Add interactive objects — doors, chests, switches
- [ ] Add a basic save system: press **S** to save, **L** to load
- [ ] 📸 Screenshot: scrolling world with interactive objects

---

## 🔮 Post-MVP

Features to add after the core game is complete.

- [ ] 🔊 Sound effects and background music
- [ ] ✨ Visual effects for hits, pickups, and level-ups
- [ ] 💾 Multiple save slots and autosave
- [ ] 📜 Basic NPC dialogue
- [ ] 🌍 Expanded map with distinct regions
- [ ] 🔧 More crafting recipes and resource types
- [ ] 🎬 Player sprite animation (walk cycle, attack)
- [ ] ⚙️ In-game settings — volume, fullscreen, controls

---

## 📋 Tasks

Next steps for **v0.6 — 📈 Player Progression**:

- [ ] Add `xp`, `level`, `attack`, and `defense` stats to `Player`.
- [ ] Add `Enemy` logic to grant XP upon death.
- [ ] Implement `level_up` method checking XP thresholds to increase `Player` max default stats.
- [ ] Update `UIManager` to render Player Level and XP.
- [ ] Implement an equipment system enabling our crafted sword to buff player `attack`.

---

## 📝 Notes

- 🖥️ Screen size: **800x600** (may change)
- 🐍 Python 3.x + Pygame required
- 📁 All game classes live in `src/`
- 🎮 Sprites go in `assets/sprites/` (32x32 PNG)
