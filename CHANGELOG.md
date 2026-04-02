# Changelog

All notable changes to this project will be documented in this file.

## [v1.0] - Advanced Forging & Menus
- Implemented multi-step refinement chains (e.g., mining Ore -> smelting Bars -> forging Weapons).
- Created a dedicated pop-up Crafting Menu UI to replace the simple single-key press, allowing for dozens of dynamic recipes.
- Tied advanced recipes strictly to high Crafting skill thresholds.
- Added RECIPES list to src/inventory.py and refactored craft() to use it with Crafting skill level gating.
- Added iron_rock node type to the world and updated ResourceNode.draw() for its color.
- Built a pop-up Crafting Menu in UIManager — toggled with C, navigated with arrow keys, confirmed with Enter.
- Updated src/game_manager.py to route menu input, block movement while menu is open, and handle iron_sword equip.
- Updated Player.get_attack() to apply +10 bonus for iron_sword.

## [v0.9] - Modular Skill System
- Built a scalable SkillManager class breaking stats down into distinct disciplines: Woodcutting, Mining, Melee, and Crafting.
- Shifted XP gains from a global pool into specific skill pools based on the action performed (e.g. hitting a tree levels Woodcutting).
- Updated UIManager to render a new "Skill Page" overlay showing your breakdown.

## [v0.8] - Persistent Nodes & Tools
- Refactored ResourceItem system into persistent ResourceNodes (Trees, Rocks) that take multiple hits to deplete and then respawn over time.
- Introduced dedicated gathering tools (Axes for trees, Pickaxes for ore) required to harvest specific nodes.
- Overhauled inventory to distinguish between raw materials (Logs, Iron Ore), tools, and finished goods.

## [v0.7] - World & Map
- Added a scrolling camera for a world larger than the screen.
- Built a simple tile-based map (Opted for a solid 2400x2400 bounds matrix for MVP).
- Added interactive objects — doors, chests, switches.
- Added a basic save system: press F5 to save, F9 to load.
- Captured screenshot: scrolling world with interactive objects.

## [v0.6] - Player Progression
- Player has base stats: HP, attack, defense.
- Stats are shown in the UI.
- Defeating enemies awards XP.
- Reaching an XP threshold increases the player's level.
- Leveling up improves stats — example: +10 max HP, +1 attack.
- Crafted items like the sword can be equipped.
- Equipped items boost player stats.
- Captured screenshot: level and stats shown in UI, equipment visible.

## [v0.5] - Combat & Enemies
- Created an Enemy class in src/enemy.py.
- Enemies spawn at set positions on the map.
- Added basic AI — chase the player when in range, idle otherwise.
- Enemies have HP and can take damage.
- Player has HP — shown as a health bar on screen.
- Enemies deal damage on contact with the player.
- Player respawns or game ends at 0 HP.
- Press Space to attack nearby enemies.
- Hitting an enemy reduces their HP.
- Defeated enemies drop loot or XP.
- Captured screenshot: enemy on screen, health bars visible, combat happening.

## [v0.4] - Sprites & UI
- Loaded sprites from assets/sprites/ using pygame.image.load.
- Fall back to a colored rectangle if a sprite file is missing.
- Named sprite files clearly — example: player.png, wood.png.
- Made sure sprite bounds match collision rectangles.
- Created a UIManager class in src/ui.py.
- Showed inventory on screen with item icons and counts.
- Showed event notifications — example: "Collected wood", "Sword crafted".
- Flash or highlight the player when collecting or crafting.
- Captured screenshot: sprites and inventory UI visible in game.

## [v0.3] - Code Structure
- Created src/inventory.py and src/resource_item.py.
- Created a GameManager class for game state and the main loop.
- Kept all classes in separate files under src/.
- Captured screenshot: folder structure showing all modules.

## [v0.2] - Resources & Crafting
- Wood and stone spawn at random positions at game start.
- Press E to collect a resource when the player overlaps it.
- Removed the resource from the world after collecting.
- Stored collected items as a dictionary — example: { "wood": 2, "stone": 1 }.
- Showed inventory updates in the console.
- Press C to craft a sword (requires wood + stone).
- Showed a success message if crafting works.
- Showed a helpful error if resources are missing.
- Added ResourceItem and Inventory classes in src/.
- Captured screenshot: resources on the map, console showing inventory and crafting.

## [v0.1.5] - Player Movement
- Added speed to the Player class.
- Added update() to read keyboard input and move the player.
- Called player.update() in the main loop before drawing.
- Clamped position so the player cannot move off screen.
- Captured screenshot: player moving around the screen.

## [v0.1] - Project Setup
- Pygame window, game loop, and quit handling.
- Player class with rectangle rendering.
- src/ folder structure and module imports.
