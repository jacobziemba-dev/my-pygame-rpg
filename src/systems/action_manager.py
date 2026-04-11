import random
import pygame
from src.core.settings import GATHERING_REACH_INFLATE


def player_in_gathering_range(player_rect, node_rect):
    """True if the player is close enough to interact with a resource node (edge-adjacent or overlapping)."""
    reach = node_rect.inflate(GATHERING_REACH_INFLATE, GATHERING_REACH_INFLATE)
    return reach.colliderect(player_rect)


class ActionManager:
    def __init__(self, ui_manager, camera):
        self.ui = ui_manager
        self.camera = camera

    TOOL_DB = {
        "bronze_axe": {"type": "axe", "power": 15, "min_level": 1},
        "iron_axe": {"type": "axe", "power": 30, "min_level": 5, "required_attack": 5},
        "steel_axe": {"type": "axe", "power": 45, "min_level": 20, "required_attack": 20},
        "bronze_pickaxe": {"type": "pickaxe", "power": 15, "min_level": 1},
        "iron_pickaxe": {"type": "pickaxe", "power": 30, "min_level": 5, "required_attack": 5},
        "steel_pickaxe": {"type": "pickaxe", "power": 45, "min_level": 20, "required_attack": 20},
        "fishing_rod": {"type": "rod", "power": 20, "min_level": 1},
        "iron_fishing_rod": {"type": "rod", "power": 35, "min_level": 5},
    }

    def check_gathering_prerequisites(self, player, node):
        """Return (ok, message). message is user-facing when ok is False."""
        if not node.is_active:
            return False, f"The {node.node_type} is depleted."

        skill_name = (
            "woodcutting"
            if node.node_type == "tree"
            else "hunter"
            if node.node_type == "bush"
            else "fishing"
            if node.node_type == "fishing_spot"
            else "mining"
        )
        skill_level = getattr(player.skills, skill_name).level

        if skill_level < getattr(node, "min_level", 1):
            return False, f"Need {skill_name.capitalize()} Lv.{node.min_level} to harvest this."

        tool_power = 0
        has_tool = False

        if node.tool_required is None:
            has_tool = True
            tool_power = 10
        else:
            blocked_by_attack = False
            attack_level = player.skills.attack.level

            for item_name, count in player.inventory.items.items():
                if count > 0 and item_name in self.TOOL_DB:
                    tool_data = self.TOOL_DB[item_name]
                    if tool_data["type"] == node.tool_required:
                        req_attack = tool_data.get("required_attack", 1)
                        if attack_level < req_attack:
                            blocked_by_attack = True
                            continue
                        if skill_level >= tool_data["min_level"]:
                            has_tool = True
                            if tool_data["power"] > tool_power:
                                tool_power = tool_data["power"]

            if not has_tool:
                if blocked_by_attack:
                    return False, "You need Attack Lv.5 to wield this."
                return (
                    False,
                    f"Need a {node.tool_required} to harvest this (or higher skill level).",
                )

        return True, None

    def try_begin_gathering(self, player, node):
        """Attempt to start gathering. Returns 'started' | 'out_of_range' | 'invalid'."""
        if not player_in_gathering_range(player.rect, node.rect):
            return "out_of_range"
        ok, msg = self.check_gathering_prerequisites(player, node)
        if not ok:
            if msg:
                self.ui.show_message(msg)
            return "invalid"
        player.current_action = "gathering"
        player.action_target = node
        self.ui.show_message(f"Started gathering {node.node_type}...")
        return "started"

    def process_gathering_tick(self, player, node):
        if not player_in_gathering_range(player.rect, node.rect):
            player.current_action = None
            player.action_target = None
            self.ui.show_message("You are too far away.")
            return

        if not node.is_active:
            player.current_action = None
            player.action_target = None
            self.ui.show_message(f"The {node.node_type} is depleted.")
            return

        ok, msg = self.check_gathering_prerequisites(player, node)
        if not ok:
            if msg:
                self.ui.show_message(msg)
            player.current_action = None
            player.action_target = None
            return

        skill_name = (
            "woodcutting"
            if node.node_type == "tree"
            else "hunter"
            if node.node_type == "bush"
            else "fishing"
            if node.node_type == "fishing_spot"
            else "mining"
        )
        skill_level = getattr(player.skills, skill_name).level

        tool_power = 0
        has_tool = False
        if node.tool_required is None:
            has_tool = True
            tool_power = 10
        else:
            attack_level = player.skills.attack.level
            for item_name, count in player.inventory.items.items():
                if count > 0 and item_name in self.TOOL_DB:
                    tool_data = self.TOOL_DB[item_name]
                    if tool_data["type"] == node.tool_required:
                        req_attack = tool_data.get("required_attack", 1)
                        if attack_level < req_attack:
                            continue
                        if skill_level >= tool_data["min_level"]:
                            has_tool = True
                            if tool_data["power"] > tool_power:
                                tool_power = tool_data["power"]

        success_chance = ((tool_power + skill_level) / node.difficulty) * 100
        success_chance = max(5, min(95, success_chance))

        roll = random.uniform(0, 100)

        if roll <= success_chance:
            if not player.inventory.add_item(node.yields, 1):
                self.ui.show_message("Your inventory is full.")
                player.current_action = None
                player.action_target = None
                return
            node.take_hit()

            if node.node_type == "tree" and random.uniform(0, 100) < 15:
                if player.inventory.add_item("wheat_seeds", 1):
                    self.ui.show_message("Found some wheat seeds!")

            leveled_up = player.skills.gain_xp(skill_name, 25)
            self.ui.add_xp_drop(skill_name, 25, player.rect.centerx, player.sprite_top_y, self.camera)
            self.ui.show_message(f"Gained 1 {node.yields}! (+25 {skill_name.capitalize()} XP)")
            if leveled_up:
                new_level = getattr(player.skills, skill_name).level
                self.ui.show_message(f"{skill_name.capitalize()} level up! Now level {new_level}")
        else:
            if success_chance < 50:
                self.ui.show_message(f"Miss! ({int(success_chance)}% chance)")
