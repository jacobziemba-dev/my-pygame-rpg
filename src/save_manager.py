import json
import os
from src.resource_item import ResourceItem
from src.enemy import Enemy

SAVE_FILE = "save.json"

class SaveManager:
    @staticmethod
    def save_game(player, resources, enemies):
        data = {
            "player": {
                "x": player.rect.x,
                "y": player.rect.y,
                "hp": player.hp,
                "max_hp": player.max_hp,
                "xp": getattr(player, 'xp', 0),
                "level": getattr(player, 'level', 1),
                "base_attack": getattr(player, 'base_attack', 5),
                "base_defense": getattr(player, 'base_defense', 0),
                "equipped_items": getattr(player, 'equipped_items', []),
                "inventory": player.inventory.items
            },
            "resources": [{"x": r.rect.x, "y": r.rect.y, "type": r.resource_type} for r in resources],
            "enemies": [{"x": e.rect.x, "y": e.rect.y, "hp": e.hp} for e in enemies]
        }
        
        with open(SAVE_FILE, "w") as f:
            json.dump(data, f)
            
    @staticmethod
    def load_game(player, resources, enemies):
        if not os.path.exists(SAVE_FILE):
            return False
            
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            
        # load player
        p_data = data["player"]
        player.rect.x = p_data["x"]
        player.rect.y = p_data["y"]
        player.hp = p_data["hp"]
        player.max_hp = p_data["max_hp"]
        player.xp = p_data.get("xp", 0)
        player.level = p_data.get("level", 1)
        player.base_attack = p_data.get("base_attack", 5)
        player.base_defense = p_data.get("base_defense", 0)
        player.equipped_items = p_data.get("equipped_items", [])
        player.inventory.items = p_data.get("inventory", {})
        
        # load resources
        resources.clear()
        for r_data in data["resources"]:
            resources.append(ResourceItem(r_data["x"], r_data["y"], r_data["type"]))
            
        # load enemies
        enemies.clear()
        for e_data in data["enemies"]:
            enemy = Enemy(e_data["x"], e_data["y"])
            enemy.hp = e_data["hp"]
            enemies.append(enemy)
            
        return True
