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

        tool_power = 0
        has_tool = False
        
        TOOL_DB = {
            "bronze_axe": {"type": "axe", "power": 15},
            "iron_axe": {"type": "axe", "power": 30},
            "bronze_pickaxe": {"type": "pickaxe", "power": 15},
            "iron_pickaxe": {"type": "pickaxe", "power": 30}
        }
        
        for item_name, count in player.inventory.items.items():
            if count > 0 and item_name in TOOL_DB:
                tool_data = TOOL_DB[item_name]
                if tool_data["type"] == node.tool_required:
                    has_tool = True
                    if tool_data["power"] > tool_power:
                        tool_power = tool_data["power"]
                        
        if not has_tool:
            self.ui.show_message(f"Need a {node.tool_required} to harvest this.")
            player.current_action = None
            player.action_target = None
            return
            
        skill_name = "woodcutting" if node.node_type == "tree" else "mining"
        skill_level = getattr(player.skills, skill_name).level
        success_chance = ((tool_power + skill_level) / node.difficulty) * 100
        success_chance = max(5, min(95, success_chance))

        roll = random.uniform(0, 100)

        if roll <= success_chance:
            node.take_hit()
            player.inventory.add_item(node.yields, 1)
            leveled_up = player.skills.gain_xp(skill_name, 5)
            self.ui.show_message(f"Gained 1 {node.yields}! (+5 {skill_name.capitalize()} XP)")
            if leveled_up:
                new_level = getattr(player.skills, skill_name).level
                self.ui.show_message(f"{skill_name.capitalize()} level up! Now level {new_level}")
        else:
            if success_chance < 50:
                self.ui.show_message(f"Miss! ({int(success_chance)}% chance)")
