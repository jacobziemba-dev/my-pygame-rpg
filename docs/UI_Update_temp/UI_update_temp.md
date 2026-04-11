## Inventory Update Plan

### 1. UI Changes

- **Visual Layout**
  - Redesign inventory panel
  - Add grid/tile-based item slots with support for item icons and stack counts.
  - Implement item tooltips showing descriptions, stats, and available left-click and right-click actions.



- **Inventory Capacity**
  - Clearly display current carrying capacity (slots) and alert player when full.

### 2. Controls / Interactions

- **Item Interaction**
  - **Left-click:** Performs the default action for the item (e.g., eat food, wield weapon, equip armor, open container). Default actions match classic RuneScape:
    - Consumables: use/eat/drink
    - Equipment: wield/equip
    - Misc: open/examine as appropriate
  - **Right-click:** Opens a classic-style context menu with options such as:
    - Use
    - Wield/Equip
    - Drop
    - Examine
    - Destroy (if applicable)
    - Split (for stackable items, if supported)
  - **Examine:** Always available as a right-click menu option. Shows flavor text and relevant stats.
  - **Drag and drop:** Rearranging items within inventory as in RuneScape.


- **Sorting and Filtering**
  - Add buttons/toggles to sort inventory (by type, by stack size)

### 3. Planned Features

- Drag-and-drop item rearrangement within inventory.



---