import json
import os
import pygame
from src.resource_item import ResourceItem
from src.resource_node import ResourceNode
from src.enemy import Enemy
from src.skill_manager import SkillManager

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
                "base_attack": getattr(player, 'base_attack', 5),
                "base_defense": getattr(player, 'base_defense', 0),
                "equipped_items": getattr(player, 'equipped_items', []),
                "inventory": player.inventory.items,
                "skills": player.skills.to_dict()
            },
            "resources": [
                {
                    "class": "ResourceNode", "x": r.rect.x, "y": r.rect.y, "type": r.node_type,
                    "difficulty": r.difficulty, "tool_required": r.tool_required, "yields": r.yields,
                    "max_hp": r.max_hp, "hp": r.hp, "respawn_time": r.respawn_time,
                    "is_active": r.is_active,
                    "remaining_respawn_ms": max(0, r.respawn_time - (pygame.time.get_ticks() - r.dead_timer)) if not r.is_active else 0,
                } if isinstance(r, ResourceNode) 
                else { "class": "ResourceItem", "x": r.rect.x, "y": r.rect.y, "type": r.resource_type }
                for r in resources
            ],
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
        player.base_attack = p_data.get("base_attack", 5)
        player.base_defense = p_data.get("base_defense", 0)
        player.equipped_items = p_data.get("equipped_items", [])
        player.inventory.items = p_data.get("inventory", {})
        player.skills = SkillManager.from_dict(p_data.get("skills", {}))
        
        # load resources
        resources.clear()
        for r_data in data["resources"]:
            if r_data.get("class") == "ResourceNode":
                node = ResourceNode(
                    r_data["x"], r_data["y"], r_data["type"], 
                    r_data["difficulty"], r_data["tool_required"], r_data["yields"], 
                    r_data["max_hp"], r_data["respawn_time"]
                )
                node.is_active = r_data.get("is_active", True)
                if not node.is_active:
                    remaining = r_data.get("remaining_respawn_ms", 0)
                    node.dead_timer = pygame.time.get_ticks() - (node.respawn_time - remaining)
                    node.hp = 0
                else:
                    node.hp = r_data.get("hp", node.max_hp)
                resources.append(node)
            else:
                resources.append(ResourceItem(r_data["x"], r_data["y"], r_data["type"]))
            
        # load enemies
        enemies.clear()
        for e_data in data["enemies"]:
            enemy = Enemy(e_data["x"], e_data["y"])
            enemy.hp = e_data["hp"]
            enemies.append(enemy)
            
        return True
