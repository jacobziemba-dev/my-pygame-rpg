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
        
    def craft(self, recipe_name):
        if recipe_name == "sword":
            if self.items.get("wood", 0) >= 1 and self.items.get("stone", 0) >= 1:
                self.remove_item("wood", 1)
                self.remove_item("stone", 1)
                self.add_item("sword", 1)
                return True
        return False
