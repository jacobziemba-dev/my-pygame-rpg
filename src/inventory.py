RECIPES = [
    {"name": "sword",        "label": "Sword",        "inputs": {"wood": 1, "stone": 1}, "outputs": {"sword": 1},        "min_level": 1, "xp": 10},
    {"name": "iron_bar",     "label": "Iron Bar",     "inputs": {"iron_ore": 2},          "outputs": {"iron_bar": 1},     "min_level": 3, "xp": 15},
    {"name": "iron_sword",   "label": "Iron Sword",   "inputs": {"iron_bar": 2},          "outputs": {"iron_sword": 1},   "min_level": 5, "xp": 25},
    {"name": "iron_axe",     "label": "Iron Axe",     "inputs": {"iron_bar": 2},          "outputs": {"iron_axe": 1},     "min_level": 5, "xp": 20},
    {"name": "iron_pickaxe", "label": "Iron Pickaxe", "inputs": {"iron_bar": 2},          "outputs": {"iron_pickaxe": 1}, "min_level": 5, "xp": 20},
]


class Inventory:
    def __init__(self):
        self.items = {
            "wood": 0,
            "stone": 0,
            "sword": 0
        }

    def add_item(self, item_type, amount=1):
        if item_type in self.items:
            self.items[item_type] += amount
        else:
            self.items[item_type] = amount

    def remove_item(self, item_type, amount=1):
        if item_type in self.items and self.items[item_type] >= amount:
            self.items[item_type] -= amount
            return True
        return False

    def craft(self, recipe_name, crafting_level=1):
        recipe = next((r for r in RECIPES if r["name"] == recipe_name), None)
        if not recipe:
            return False, "Unknown recipe."
        if crafting_level < recipe["min_level"]:
            return False, f"Requires Crafting Lv.{recipe['min_level']}."
        for item, amount in recipe["inputs"].items():
            if self.items.get(item, 0) < amount:
                return False, f"Need {amount} {item.replace('_', ' ')}."
        for item, amount in recipe["inputs"].items():
            self.remove_item(item, amount)
        for item, amount in recipe["outputs"].items():
            self.add_item(item, amount)
        return True, recipe["xp"]
