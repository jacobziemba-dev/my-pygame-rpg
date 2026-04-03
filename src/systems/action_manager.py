import random
import pygame

class ActionManager:
    def __init__(self, ui_manager):
        self.ui = ui_manager

    def process_gathering_tick(self, player, node):
        if not node.is_active:
            player.current_action = None
            player.action_target = None
            self.ui.show_message(f"The {node.node_type} is depleted.")
            return

        skill_name = ("woodcutting" if node.node_type == "tree"
                      else "hunter" if node.node_type == "bush"
                      else "fishing" if node.node_type == "fishing_spot"
                      else "mining")
        skill_level = getattr(player.skills, skill_name).level
        
        if skill_level < getattr(node, 'min_level', 1):
            self.ui.show_message(f"Need {skill_name.capitalize()} Lv.{node.min_level} to harvest this.")
            player.current_action = None
            player.action_target = None
            return

        tool_power = 0
        has_tool = False

        if node.tool_required is None:
            has_tool = True
            tool_power = 10
        else:
            TOOL_DB = {
                "bronze_axe": {"type": "axe", "power": 15, "min_level": 1},
                "iron_axe": {"type": "axe", "power": 30, "min_level": 5},
                "bronze_pickaxe": {"type": "pickaxe", "power": 15, "min_level": 1},
                "iron_pickaxe": {"type": "pickaxe", "power": 30, "min_level": 5},
                "fishing_rod": {"type": "rod", "power": 20, "min_level": 1},
                "iron_fishing_rod": {"type": "rod", "power": 35, "min_level": 5}
            }

            for item_name, count in player.inventory.items.items():
                if count > 0 and item_name in TOOL_DB:
                    tool_data = TOOL_DB[item_name]
                    if tool_data["type"] == node.tool_required:
                        if skill_level >= tool_data["min_level"]:
                            has_tool = True
                            if tool_data["power"] > tool_power:
                                tool_power = tool_data["power"]

            if not has_tool:
                self.ui.show_message(f"Need a {node.tool_required} to harvest this (or higher skill level).")
                player.current_action = None
                player.action_target = None
                return
            
        success_chance = ((tool_power + skill_level) / node.difficulty) * 100
        success_chance = max(5, min(95, success_chance))

        roll = random.uniform(0, 100)

        if roll <= success_chance:
            node.take_hit()
            player.inventory.add_item(node.yields, 1)
            
            # Chance for seeds if woodcutting
            if node.node_type == "tree" and random.uniform(0, 100) < 15: # 15% chance
                player.inventory.add_item("wheat_seeds", 1)
                self.ui.show_message("Found some wheat seeds!")

            leveled_up = player.skills.gain_xp(skill_name, 5)
            self.ui.show_message(f"Gained 1 {node.yields}! (+5 {skill_name.capitalize()} XP)")
            if leveled_up:
                new_level = getattr(player.skills, skill_name).level
                self.ui.show_message(f"{skill_name.capitalize()} level up! Now level {new_level}")
        else:
            if success_chance < 50:
                self.ui.show_message(f"Miss! ({int(success_chance)}% chance)")
