# My Pygame RPG

**[Readme](README.md)** | **[Changelog](CHANGELOG.md)**

---

## Overview

A 2D RPG built with **Python** and **pygame-ce**. Explore a scrolling world, gather resources with tools, craft items, use furnace and workbench stations, bank your loot, farm crops, fight enemies, and level skills.

- **World**: Camera follows the player across a map larger than the screen (see `MAP_*` in settings).
- **Gathering**: Trees, rocks, iron nodes, and bushes require the right tool where applicable; nodes can respawn after depletion.
- **Crafting & stations**: Hand crafting from the menu; smelting and advanced recipes at placed **Furnace** and **Workbench** stations.
- **Bank**: A central **Bank** near the start stores items in a separate vault (deposit / withdraw in the bank UI).
- **Combat & skills**: Melee combat; skill XP and overlays for progression (e.g. gathering, crafting, combat stats).
- **Farming**: Till, plant, and harvest crops on a grid (hoe and seeds required).
- **Save / load**: Persist progress with the keys below.
- **Input**: Keyboard plus **point-and-click** movement and context actions (walk to nodes, enemies, pickups).

### Controls — main world

| Key | Action |
| --- | --- |
| **WASD** / **Arrow keys** | Move |
| **E** | Interact: open **bank** or **station**, collect station output, start **gathering** on a resource node, pick up **dropped items** on the ground |
| **C** | Open **crafting** menu |
| **I** | Toggle **inventory** |
| **K** | Toggle **skills** overlay |
| **F** | **Farming** (till / plant / harvest on the tile near you; needs hoe and seeds where applicable) |
| **Space** | **Attack** (melee) |
| **Enter** | Quick **use / equip** (tries common gear and consumables in priority order) |
| **F5** / **F9** | **Save** / **Load** game |
| **F3** | Toggle **FPS** overlay |
| **Ctrl+Q** | **Quit** |
| **R** | **Restart** (when game over) |

### Mouse

- **Left-click** empty ground: move to that location (with a destination marker).
- **Left-click** a resource node, enemy, or dropped item: walk there and **gather**, **attack**, or **pick up** as appropriate.
- **Right-click** an item in the **inventory** overlay: **drop** one near the player.

### Overlays (when a menu is open)

**Crafting** — **Esc** or **C** to close; **Up** / **Down** to select a recipe; **Enter** to craft.

**Inventory** — **Esc** or **I** to close; **Up** / **Down** / **Left** / **Right** to move selection; **Enter** to use the selected item.

**Skills** — **Esc** to close (or **K** to toggle off).

**Bank** — **Esc** or **E** to close; **T** to **deposit all** from your inventory into the bank.

**Furnace / Workbench** — **Esc** or **E** to close; **Up** / **Down** to select a recipe; **Enter** to start processing (inputs consumed per recipe).

### How to run

Requires **Python 3** and **pygame-ce** (see `requirements.txt`).

```bash
pip install -r requirements.txt
python main.py
```

---

- **Resolution**: **1280×720** (see `SCREEN_WIDTH` / `SCREEN_HEIGHT` in [`src/core/settings.py`](src/core/settings.py)).
- **Code layout**: Game logic lives under [`src/`](src/).
- **Art**: There is no bundled `assets/` tree yet; if you add 32×32 PNG sprites, a sensible convention is `assets/sprites/`.
