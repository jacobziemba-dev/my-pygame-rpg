class Inventory:
    MAX_SLOTS = 28

    def __init__(self):
        self.items = {
            "wood": 0,
            "stone": 0,
            "sword": 0
        }

    def add_item(self, item_type, amount=1):
        if amount <= 0:
            return False
        if not self.can_add_item(item_type):
            return False
        if item_type in self.items:
            self.items[item_type] += amount
        else:
            self.items[item_type] = amount
        return True

    def occupied_slots(self):
        return sum(1 for count in self.items.values() if count > 0)

    def can_add_item(self, item_type):
        # Existing stacks never consume additional slots.
        if self.items.get(item_type, 0) > 0:
            return True
        return self.occupied_slots() < self.MAX_SLOTS

    def _can_add_outputs_after_inputs(self, inputs, outputs):
        # Simulate consumed inputs first, then ensure all outputs can fit.
        projected = dict(self.items)
        for item, amount in inputs.items():
            projected[item] = projected.get(item, 0) - amount

        projected_slots = sum(1 for count in projected.values() if count > 0)
        for item, amount in outputs.items():
            if amount <= 0:
                continue
            if projected.get(item, 0) > 0:
                continue
            if projected_slots >= self.MAX_SLOTS:
                return False
            projected_slots += 1
        return True

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
        if not self._can_add_outputs_after_inputs(recipe["inputs"], recipe["outputs"]):
            return False, "Your inventory is full."
        for item, amount in recipe["inputs"].items():
            self.remove_item(item, amount)
        for item, amount in recipe["outputs"].items():
            self.add_item(item, amount)
        return True, recipe["xp"]






        