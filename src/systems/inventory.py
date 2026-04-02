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

    def craft(self, recipe_name, crafting_level=1, recipe_manager=None):
        recipe = recipe_manager.get_by_name(recipe_name) if recipe_manager else None
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