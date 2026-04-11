class Inventory:
    MAX_SLOTS = 28

    def __init__(self):
        self.slots = [None] * self.MAX_SLOTS
        self.items = {}

    def _rebuild_items(self):
        self.items.clear()
        for cell in self.slots:
            if cell:
                it, c = cell["item"], cell["count"]
                self.items[it] = self.items.get(it, 0) + c

    def _first_empty_slot(self):
        for i, cell in enumerate(self.slots):
            if cell is None:
                return i
        return None

    def _find_merge_slot(self, item_type):
        """First slot already holding this item (for stacking pickups)."""
        for i, cell in enumerate(self.slots):
            if cell and cell["item"] == item_type:
                return i
        return None

    def get_item_count(self, item_type):
        return self.items.get(item_type, 0)

    def occupied_slots(self):
        return sum(1 for c in self.slots if c is not None)

    def can_add_item(self, item_type):
        if self.get_item_count(item_type) > 0:
            return True
        return self.occupied_slots() < self.MAX_SLOTS

    def add_item(self, item_type, amount=1):
        if amount <= 0:
            return False
        if not self.can_add_item(item_type):
            return False
        merge_i = self._find_merge_slot(item_type)
        if merge_i is not None:
            self.slots[merge_i]["count"] += amount
        else:
            empty = self._first_empty_slot()
            if empty is None:
                return False
            self.slots[empty] = {"item": item_type, "count": amount}
        self._rebuild_items()
        return True

    def remove_item(self, item_type, amount=1):
        if self.get_item_count(item_type) < amount:
            return False
        remaining = amount
        for i, cell in enumerate(self.slots):
            if not cell or cell["item"] != item_type:
                continue
            take = min(remaining, cell["count"])
            cell["count"] -= take
            remaining -= take
            if cell["count"] <= 0:
                self.slots[i] = None
            if remaining <= 0:
                break
        self._rebuild_items()
        return True

    def get_slot(self, index):
        """Return (item_id, count) or None."""
        if not (0 <= index < self.MAX_SLOTS):
            return None
        cell = self.slots[index]
        if not cell:
            return None
        return (cell["item"], cell["count"])

    def remove_from_slot(self, slot_index, amount=1):
        """Remove amount from a specific slot. Returns True if anything removed."""
        if not (0 <= slot_index < self.MAX_SLOTS):
            return False
        cell = self.slots[slot_index]
        if not cell or cell["count"] < amount:
            return False
        cell["count"] -= amount
        if cell["count"] <= 0:
            self.slots[slot_index] = None
        self._rebuild_items()
        return True

    def swap_slots(self, a, b):
        if not (0 <= a < self.MAX_SLOTS and 0 <= b < self.MAX_SLOTS):
            return
        self.slots[a], self.slots[b] = self.slots[b], self.slots[a]
        self._rebuild_items()

    def merge_or_swap(self, src, dst):
        """
        OSRS-like: dst empty -> move src; same item -> merge; else swap.
        Returns True if src became empty (moved/merged).
        """
        if not (0 <= src < self.MAX_SLOTS and 0 <= dst < self.MAX_SLOTS):
            return False
        if src == dst:
            return False
        s_cell = self.slots[src]
        d_cell = self.slots[dst]
        if s_cell is None:
            return False
        if d_cell is None:
            self.slots[dst] = s_cell
            self.slots[src] = None
            self._rebuild_items()
            return True
        if d_cell["item"] == s_cell["item"]:
            d_cell["count"] += s_cell["count"]
            self.slots[src] = None
            self._rebuild_items()
            return True
        self.slots[src], self.slots[dst] = d_cell, s_cell
        self._rebuild_items()
        return True

    def split_slot(self, slot_index, take_amount):
        """
        Move take_amount from slot_index into first empty slot.
        Returns True on success.
        """
        if not (0 <= slot_index < self.MAX_SLOTS):
            return False
        cell = self.slots[slot_index]
        if not cell or cell["count"] <= 1 or take_amount < 1:
            return False
        if take_amount >= cell["count"]:
            return False
        empty = self._first_empty_slot()
        if empty is None:
            return False
        cell["count"] -= take_amount
        self.slots[empty] = {"item": cell["item"], "count": take_amount}
        self._rebuild_items()
        return True

    def sort_slots(self, mode="name"):
        """
        Compact non-empty slots to the front, ordered by mode:
        'name', 'type' (prefix heuristic), 'quantity' (count desc, then name).
        """
        stacks = [c for c in self.slots if c is not None]
        if mode == "quantity":
            stacks.sort(key=lambda c: (-c["count"], c["item"]))
        elif mode == "type":
            def type_key(c):
                it = c["item"]
                for prefix in (
                    "rune_", "ore_", "bar_", "raw_", "cooked_", "iron_", "steel_", "bronze_",
                ):
                    if it.startswith(prefix):
                        return (prefix, it)
                return ("zzz", it)

            stacks.sort(key=type_key)
        else:
            stacks.sort(key=lambda c: c["item"])
        self.slots = stacks + [None] * (self.MAX_SLOTS - len(stacks))
        self._rebuild_items()

    def load_from_save(self, data):
        """Accept legacy flat dict or {'slots': [...]} format."""
        if isinstance(data, dict) and "slots" in data:
            raw = data["slots"]
            self.slots = [None] * self.MAX_SLOTS
            for i, cell in enumerate(raw):
                if i >= self.MAX_SLOTS:
                    break
                if cell is None:
                    self.slots[i] = None
                elif isinstance(cell, dict) and "item" in cell and "count" in cell:
                    c = int(cell["count"])
                    if c > 0:
                        self.slots[i] = {"item": str(cell["item"]), "count": c}
            self._rebuild_items()
            return
        self.slots = [None] * self.MAX_SLOTS
        if isinstance(data, dict):
            for item_type, count in data.items():
                n = int(count)
                if n > 0:
                    self.add_item(str(item_type), n)
        self._rebuild_items()

    def to_save_dict(self):
        return {"slots": [dict(c) if c else None for c in self.slots]}

    def _can_add_outputs_after_inputs(self, inputs, outputs, projected=None):
        if projected is None:
            projected = dict(self.items)
        else:
            projected = dict(projected)
        for item, amount in inputs.items():
            projected[item] = projected.get(item, 0) - amount

        projected_slots = self._occupied_slots_for_dict(projected)
        for item, amount in outputs.items():
            if amount <= 0:
                continue
            if projected.get(item, 0) > 0:
                continue
            if projected_slots >= self.MAX_SLOTS:
                return False
            projected_slots += 1
        return True

    @staticmethod
    def _occupied_slots_for_dict(d):
        return sum(1 for count in d.values() if count > 0)

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
