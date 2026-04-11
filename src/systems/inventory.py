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

    def _can_add_outputs_after_inputs(self, inputs, outputs, projected=None):
        """If projected is None, start from current inventory; else mutate a copy of projected."""
        if projected is None:
            projected = dict(self.items)
        else:
            projected = dict(projected)
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

    @staticmethod
    def _skill_label(recipe):
        sid = recipe.get("skill", "crafting")
        labels = {
            "smithing": "Smithing",
            "crafting": "Crafting",
            "cooking": "Cooking",
            "fletching": "Fletching",
            "runecrafting": "Runecrafting",
        }
        return labels.get(sid, sid.replace("_", " ").title())

    def max_craftable_batches(self, recipe, skill_level, ignore_output_space=False):
        """How many times this recipe can be completed. If ignore_output_space, only materials are checked
        (for workstation queues where products are held until collection)."""
        if not recipe or skill_level < recipe["min_level"]:
            return 0
        sim = dict(self.items)
        count = 0
        while True:
            for item, amount in recipe["inputs"].items():
                if sim.get(item, 0) < amount:
                    return count
            if not ignore_output_space and not self._can_add_outputs_after_inputs(
                recipe["inputs"], recipe["outputs"], sim
            ):
                return count
            for item, amount in recipe["inputs"].items():
                sim[item] = sim.get(item, 0) - amount
            if not ignore_output_space:
                for item, amount in recipe["outputs"].items():
                    sim[item] = sim.get(item, 0) + amount
            count += 1
            if count > 10000:
                return count

    def craft(self, recipe_name, crafting_level=1, recipe_manager=None, quantity=1):
        recipe = recipe_manager.get_by_name(recipe_name) if recipe_manager else None
        if not recipe:
            return False, "Unknown recipe."
        skill_label = self._skill_label(recipe)
        if crafting_level < recipe["min_level"]:
            return False, f"You need {skill_label} level {recipe['min_level']} to make that."
        total_xp = 0
        crafted = 0
        last_fail = None
        q = max(1, int(quantity))
        for _ in range(q):
            recipe = recipe_manager.get_by_name(recipe_name)
            if crafting_level < recipe["min_level"]:
                last_fail = f"You need {skill_label} level {recipe['min_level']} to make that."
                break
            shortage = False
            for item, amount in recipe["inputs"].items():
                if self.items.get(item, 0) < amount:
                    last_fail = f"You don't have enough {item.replace('_', ' ')}."
                    shortage = True
                    break
            if shortage:
                break
            if not self._can_add_outputs_after_inputs(recipe["inputs"], recipe["outputs"]):
                last_fail = "Your inventory is too full to hold that."
                break
            for item, amount in recipe["inputs"].items():
                self.remove_item(item, amount)
            for item, amount in recipe["outputs"].items():
                self.add_item(item, amount)
            total_xp += recipe["xp"]
            crafted += 1
        if crafted == 0:
            return False, last_fail or "You can't make that."
        return True, total_xp, crafted






        