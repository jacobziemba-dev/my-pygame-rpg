import json
import os
import pygame
from src.entities.resource_item import ResourceItem
from src.entities.resource_node import ResourceNode
from src.entities.enemy import Enemy
from src.entities.crop import Crop
from src.systems.skill_manager import SkillManager
from src.core.settings import TILE_SIZE

SAVE_FILE = os.path.join("data", "save.json")

class SaveManager:
    @staticmethod
    def save_game(player, resources, enemies):
        data = {
            "player": {
                "centerx": player.rect.centerx,
                "centery": player.rect.centery,
                "hp": player.hp,
                "max_hp": player.max_hp,
                "base_attack": getattr(player, 'base_attack', 5),
                "base_defense": getattr(player, 'base_defense', 0),
                "equipped_items": getattr(player, 'equipped_items', []),
                "combat_mode":   getattr(player, 'combat_mode',  "melee"),
                "combat_style":  getattr(player, 'combat_style', "aggressive"),
                "inventory": player.inventory.to_save_dict(),
                "bank_inventory": player.bank_inventory.to_save_dict(),
                "skills": player.skills.to_dict()
            },
            "resources": [
                {
                    "class": "ResourceNode", "x": r.rect.x, "y": r.rect.y, "type": r.node_type,
                    "difficulty": r.difficulty, "tool_required": r.tool_required, "yields": r.yields,
                    "max_hp": r.max_hp, "hp": r.hp, "respawn_time": r.respawn_time, "min_level": getattr(r, 'min_level', 1),
                    "is_active": r.is_active,
                    "remaining_respawn_ms": max(0, r.respawn_time - (pygame.time.get_ticks() - r.dead_timer)) if not r.is_active else 0,
                } if isinstance(r, ResourceNode) 
                else { "class": "ResourceItem", "x": r.rect.x, "y": r.rect.y, "type": r.resource_type }
                for r in resources
            ],
            "enemies": [{"x": e.rect.x, "y": e.rect.y, "hp": e.hp,
                          "enemy_type": getattr(e, 'enemy_type', 'goblin'),
                          "spawn_x": getattr(e, 'spawn_x', e.rect.x),
                          "spawn_y": getattr(e, 'spawn_y', e.rect.y)} for e in enemies],
            "crops": [
                {
                    "x": c.rect.x, "y": c.rect.y, "type": c.crop_type,
                    "stage": c.growth_stage, "timer": c.growth_timer,
                    "is_mature": c.is_mature
                } for c in getattr(player, 'game_manager', None).crops if hasattr(player, 'game_manager')
            ] if hasattr(player, 'game_manager') else []
        }
        
        # Save stations data
        gm = getattr(player, 'game_manager', None)
        if gm and hasattr(gm, 'stations'):
            data["stations"] = [
                {
                    "x": s.rect.x,
                    "y": s.rect.y,
                    "station_type": s.station_type,
                    "name": s.name,
                    "is_processing": s.is_processing,
                    "process_start_time": pygame.time.get_ticks() - s.process_start_time if s.is_processing else 0,
                    "process_duration": s.process_duration,
                    "input_item": s.input_item,
                    "output_item": s.output_item,
                    "items_to_process": s.items_to_process,
                    "processed_items": s.processed_items
                } for s in gm.stations
            ]
        

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
        if "centerx" in p_data and "centery" in p_data:
            player.rect.centerx = p_data["centerx"]
            player.rect.centery = p_data["centery"]
        else:
            # Legacy: x,y were top-left of old 32×32 player rect
            player.rect.centerx = p_data["x"] + TILE_SIZE // 2
            player.rect.centery = p_data["y"] + TILE_SIZE // 2
        player.hp = p_data["hp"]
        player.max_hp = p_data["max_hp"]
        player.base_attack = p_data.get("base_attack", 5)
        player.base_defense = p_data.get("base_defense", 0)
        player.equipped_items = p_data.get("equipped_items", [])
        # Auto-detect ranged mode for old saves that didn't save combat_mode
        default_mode = "ranged" if "shortbow" in player.equipped_items else "melee"
        player.combat_mode  = p_data.get("combat_mode",  default_mode)
        default_style = "rapid" if player.combat_mode == "ranged" else "aggressive"
        player.combat_style = p_data.get("combat_style", default_style)
        player.inventory.load_from_save(p_data.get("inventory", {}))
        player.bank_inventory.load_from_save(p_data.get("bank_inventory", {}))
        player.skills = SkillManager.from_dict(p_data.get("skills", {}))
        
        # load resources
        resources.clear()
        for r_data in data["resources"]:
            if r_data.get("class") == "ResourceNode":
                node = ResourceNode(
                    r_data["x"], r_data["y"], r_data["type"], 
                    r_data["difficulty"], r_data["tool_required"], r_data["yields"], 
                    r_data["max_hp"], r_data["respawn_time"], r_data.get("min_level", 1)
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
            enemy_type = e_data.get("enemy_type", "goblin")
            enemy = Enemy(e_data["x"], e_data["y"], enemy_type)
            enemy.hp = e_data["hp"]
            enemy.spawn_x = e_data.get("spawn_x", e_data["x"])
            enemy.spawn_y = e_data.get("spawn_y", e_data["y"])
            enemies.append(enemy)

        # load crops
        gm = getattr(player, 'game_manager', None)
        if gm:
            gm.crops = []
            for cr_data in data.get("crops", []):
                crop = Crop(cr_data["x"], cr_data["y"], cr_data.get("type", "wheat"))
                crop.growth_stage = cr_data.get("stage", 0)
                crop.is_mature = cr_data.get("is_mature", False)
                # Adjust timer to keep progress
                crop.growth_timer = pygame.time.get_ticks() - (cr_data.get("timer", 0))
                gm.crops.append(crop)
                
            if "stations" in data and hasattr(gm, 'stations'):
                for i, s_data in enumerate(data["stations"]):
                    if i < len(gm.stations):
                        s = gm.stations[i]
                        s.is_processing = s_data.get("is_processing", False)
                        if s.is_processing:
                            s.process_start_time = pygame.time.get_ticks() - s_data.get("process_start_time", 0)
                        s.process_duration = s_data.get("process_duration", 0)
                        s.input_item = s_data.get("input_item")
                        s.output_item = s_data.get("output_item")
                        s.items_to_process = s_data.get("items_to_process", 0)
                        s.processed_items = s_data.get("processed_items", 0)


        return True






        