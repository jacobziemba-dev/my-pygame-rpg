import pygame
import os
import math
from src.systems.inventory import Inventory
from src.systems.skill_manager import SkillManager
from src.core.settings import *
from src.entities.entity import Entity, resolve_collision_x, resolve_collision_y
from src.entities.bank import Bank
from src.entities.shop import Shop

class Player(Entity): 
    def __init__(self, x, y, game_manager):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE, game_manager)
        self.color = COLOR_PLAYER
        self.speed = PLAYER_SPEED
        self.inventory = Inventory()
        self.bank_inventory = Inventory()
        
        self.max_hp = PLAYER_MAX_HP
        self.hp = PLAYER_MAX_HP
        self.last_hit_time = 0
        
        self.skills = SkillManager()
        self.base_attack = 5
        self.base_defense = 0
        self.equipped_items = []
        self.combat_mode  = "melee"       # "melee" | "ranged"
        self.combat_style = "aggressive"  # melee: accurate/aggressive/defensive | ranged: accurate/rapid/longrange
        
        self.current_action = None
        self.action_target = None
        self.action_timer = 0

        self.target_destination = None
        self.interaction_target = None
        self.interaction_type = "default"
        self.waypoints = []
        
        # Animations
        self.import_assets()
        self.status = 'idle'
        self.frame_index = 0
        self.animation_speed = 0.15
        self.direction = pygame.math.Vector2()
        
        # Grant starting tools
        self.inventory.add_item("bronze_axe", 1)
        self.inventory.add_item("bronze_pickaxe", 1)
        self.inventory.add_item("bronze_hoe", 1)
        self.inventory.add_item("fishing_rod", 1)
        self.inventory.add_item("wheat_seeds", 5)

        self.image = None

    def import_assets(self):
        self.animations = {
            'idle': [], 'walk_up': [], 'walk_down': [], 'walk_left': [], 'walk_right': [],
            'attack_up': [], 'attack_down': [], 'attack_left': [], 'attack_right': []
        }
        self.load_animations('assets/sprites/player', (TILE_SIZE, TILE_SIZE))

    def get_status(self):
        # Action status
        if self.current_action == "attacking":
            if 'attack' not in self.status:
                self.status = self.status.replace('walk', 'attack').replace('idle', 'attack')
                if 'attack' not in self.status:
                    self.status = 'attack_down'
        else:
            if self.direction.magnitude() == 0:
                self.status = 'idle'
            else:
                if abs(self.direction.x) > abs(self.direction.y):
                    if self.direction.x > 0: self.status = 'walk_right'
                    else: self.status = 'walk_left'
                else:
                    if self.direction.y > 0: self.status = 'walk_down'
                    else: self.status = 'walk_up'

    def animate(self, dt):
        animation = self.animations.get(self.status, self.animations['idle'])
        if not animation:
            return

        self.frame_index += self.animation_speed * dt * 60
        if self.frame_index >= len(animation):
            self.frame_index = 0

        self.image = animation[int(self.frame_index)]

    def set_target_destination(self, x, y, target_entity=None, waypoints=None, action_type="default"):
        if waypoints:
            self.waypoints = list(waypoints[1:])
            self.target_destination = waypoints[0]
        else:
            self.waypoints = []
            self.target_destination = (x, y)
        self.interaction_target = target_entity
        self.interaction_type = action_type
        self.current_action = None
        self.action_target = None

    def update(self, dt, obstacles=None):
        if obstacles is None:
            obstacles = []
        moved = False
        self.direction.xy = (0, 0)
        if self.target_destination:
            tx, ty = self.target_destination
            dx = tx - self.rect.centerx
            dy = ty - self.rect.centery
            dist = math.hypot(dx, dy)

            # Move towards target if not close enough
            if dist > self.speed:
                dx_norm = dx / dist
                dy_norm = dy / dist
                self.direction.x = dx_norm
                self.direction.y = dy_norm
                self.rect.x += dx_norm * self.speed * dt * 60
                resolve_collision_x(self.rect, obstacles)
                self.rect.y += dy_norm * self.speed * dt * 60
                resolve_collision_y(self.rect, obstacles)
                moved = True
            else:
                if self.waypoints:
                    # Intermediate waypoint reached — advance to next, no interaction yet
                    self.target_destination = self.waypoints.pop(0)
                else:
                    # Final destination reached — snap and trigger interaction
                    if not self.interaction_target:
                        test = self.rect.copy()
                        test.centerx = tx
                        test.centery = ty
                        if not any(test.colliderect(obs) for obs in obstacles):
                            self.rect.centerx = tx
                            self.rect.centery = ty
                    else:
                        self.rect.centerx = tx
                        self.rect.centery = ty
                    self.target_destination = None

                    if self.interaction_target:
                        if hasattr(self.interaction_target, 'is_active') and self.interaction_target.is_active:
                             # It's a resource node
                             self.current_action = "gathering"
                             self.action_target = self.interaction_target
                             if hasattr(self.game_manager, 'ui'):
                                 self.game_manager.ui.show_message(f"Started gathering {self.interaction_target.node_type}...")
                        elif hasattr(self.interaction_target, 'hp') and hasattr(self.interaction_target, 'max_hp'):
                             # It's an enemy
                             self.current_action = "attacking"
                             self.action_target = self.interaction_target
                        elif hasattr(self.interaction_target, 'station_type'):
                             # It's a station
                             station = self.interaction_target
                             collected = station.collect(self)
                             if hasattr(self.game_manager, 'ui'):
                                 if collected > 0:
                                     if station.pending_recipe:
                                         recipe = station.pending_recipe
                                         skill_name = recipe.get("skill", "crafting")
                                         xp_total = recipe["xp"] * collected
                                         if hasattr(self.game_manager, "_award_xp"):
                                             leveled_up = self.game_manager._award_xp(
                                                 skill_name, xp_total, self.rect.centerx, self.rect.top
                                             )
                                         else:
                                             leveled_up = self.skills.gain_xp(skill_name, xp_total)
                                         msg = f"Collected {collected} items! (+{xp_total} {skill_name.capitalize()} XP)"
                                         if leveled_up:
                                             lvl = getattr(self.skills, skill_name).level
                                             msg += f" — {skill_name.capitalize()} Lv.{lvl}!"
                                         self.game_manager.ui.show_message(msg)
                                         station.pending_recipe = None
                                     else:
                                         self.game_manager.ui.show_message(f"Collected {collected} items!")
                                 else:
                                     self.game_manager.ui.active_station = station
                                     self.game_manager.ui.station_index = 0
                                     self.game_manager.ui.show_message(f"Opened {station.name}.")
                        elif hasattr(self.interaction_target, 'inventory') and hasattr(self.interaction_target, 'rect') and not hasattr(self.interaction_target, 'image'):
                             # It's a chest
                             if hasattr(self.game_manager, 'ui'):
                                 self.game_manager.ui.active_chest = self.interaction_target
                                 self.game_manager.ui.show_message("Opened chest storage.")
                        elif isinstance(self.interaction_target, Bank):
                             # It's the Bank
                             if hasattr(self.game_manager, 'ui'):
                                 if getattr(self, "interaction_type", "default") == "talk":
                                     self.game_manager.ui.show_dialogue("Bank Teller", ["Good day! How can I help you?", "Please use my booth to access your items."])
                                 else:
                                     self.game_manager.ui.active_shop = False
                                     self.game_manager.ui.active_bank = True
                                     self.game_manager.ui.show_message("Opened bank vault.")
                        elif isinstance(self.interaction_target, Shop):
                             # It's the Shop
                             if hasattr(self.game_manager, 'ui'):
                                 if getattr(self, "interaction_type", "default") == "talk":
                                     self.game_manager.ui.show_dialogue("Shopkeeper", ["Welcome to my General Store!", "Trade with me to buy and sell supplies."])
                                 else:
                                     self.game_manager.ui.active_bank = False
                                     self.game_manager.ui.active_shop = True
                                     self.game_manager.ui.show_message("Opened shop.")
                        elif hasattr(self.interaction_target, 'resource_type'):
                             # It's a dropped item
                             item = self.interaction_target
                             if item in self.game_manager.resources:
                                 if item.resource_type == "chest":
                                     wood_ok = self.inventory.add_item("wood", 10)
                                     stone_ok = self.inventory.add_item("stone", 10)
                                     if hasattr(self.game_manager, 'ui'):
                                        if wood_ok or stone_ok:
                                            self.game_manager.ui.show_message("Opened Chest! Huge Loot gained.")
                                        else:
                                            self.game_manager.ui.show_message("Your inventory is full.")
                                 else:
                                     if self.inventory.add_item(item.resource_type, 1):
                                         if hasattr(self.game_manager, 'ui'):
                                            self.game_manager.ui.show_message(f"Picked up 1 {item.resource_type}!")
                                         self.game_manager.resources.remove(item)
                                     else:
                                         if hasattr(self.game_manager, 'ui'):
                                            self.game_manager.ui.show_message("Your inventory is full.")
                                         # Keep item on the ground when pickup fails.
                                         
                                 if item.resource_type == "chest" and (wood_ok or stone_ok):
                                     self.game_manager.resources.remove(item)

                        self.interaction_target = None
                    

        # Keyboard fallback removed (forced click-to-move for RS feel)
            
        if moved and self.current_action is not None and not self.target_destination:
            self.current_action = None
            self.action_target = None

        self.get_status()
        self.animate(dt)
            
        self.rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))

    def draw(self, surface, camera=None):
        # Flash player transparent if they were hit recently
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time < 1000 and (current_time // 100) % 2 == 0:
            return

        super().draw(surface, camera)

        # Draw movement target indicator (RS-style yellow X)
        if self.target_destination:
            tx = self.target_destination[0]
            ty = self.target_destination[1]
            if camera:
                tx -= camera.camera_rect.x
                ty -= camera.camera_rect.y
            
            now = pygame.time.get_ticks()
            if (now // 200) % 2 == 0:
                x_color = (255, 230, 0, 180)
                length = 8
                # Draw an X
                pygame.draw.line(surface, x_color, (tx - length, ty - length), (tx + length, ty + length), 3)
                pygame.draw.line(surface, x_color, (tx - length, ty + length), (tx + length, ty - length), 3)


    def take_damage(self, amount):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time > 1000:
            # apply defense
            actual_damage = max(1, amount - self.get_defense())
            self.hp -= actual_damage
            if self.hp < 0:
                self.hp = 0
            self.last_hit_time = current_time
            return True
        return False

    def get_attack(self):
        attack = self.base_attack
        if "iron_sword" in self.equipped_items:
            attack += 10
        elif "sword" in self.equipped_items:
            attack += 5
        return attack

    def get_defense(self):
        defense = self.base_defense
        if "iron_armor" in self.equipped_items:
            defense += 15
        return defense

    def get_ranged_attack(self):
        base = 5
        if "shortbow" in self.equipped_items:
            base += 8
        return base + (self.skills.ranged.level // 5)

    def has_bow(self):
        return "shortbow" in self.equipped_items

    def set_combat_mode(self, mode):
        if mode == "melee":
            self.combat_mode, self.combat_style = "melee", "aggressive"
        elif mode == "ranged":
            self.combat_mode, self.combat_style = "ranged", "rapid"

    def set_combat_style(self, style):
        melee_styles  = {"accurate", "aggressive", "defensive"}
        ranged_styles = {"accurate", "rapid", "longrange"}
        valid = melee_styles if self.combat_mode == "melee" else ranged_styles
        if style in valid:
            self.combat_style = style

    def get_xp_skill_for_hit(self):
        """Returns (primary_skill, secondary_skill_or_None) based on current mode+style."""
        if self.combat_mode == "melee":
            return {
                "accurate":   ("attack",   None),
                "aggressive": ("strength", None),
                "defensive":  ("defense",  None),
            }.get(self.combat_style, ("strength", None))
        else:
            return {
                "accurate":  ("ranged", None),
                "rapid":     ("ranged", None),
                "longrange": ("ranged", "defense"),
            }.get(self.combat_style, ("ranged", None))

    def _check_item_requirement(self, item_name):
        req = EQUIPMENT_REQUIREMENTS.get(item_name)
        if not req:
            return True, ""
        skill_name, level_required = req
        current = getattr(self.skills, skill_name).level
        if current < level_required:
            return False, f"You need {skill_name.capitalize()} Lv.{level_required} to wield this."
        return True, ""

    def use_item(self, item_name):
        if self.inventory.items.get(item_name, 0) > 0:
            if item_name == "bread":
                self.hp = min(self.max_hp, self.hp + 20)
                self.inventory.remove_item(item_name, 1)
                return True, "Healed 20 HP!"
            if item_name == "cooked_fish":
                self.hp = min(self.max_hp, self.hp + 15)
                self.inventory.remove_item(item_name, 1)
                return True, "Healed 15 HP with cooked fish!"
            # For gear, equip it
            if item_name in ["sword", "iron_sword", "iron_armor", "shortbow"]:
                meets_req, req_msg = self._check_item_requirement(item_name)
                if not meets_req:
                    return False, req_msg
                if item_name not in self.equipped_items:
                    self.inventory.remove_item(item_name, 1)
                    self.equipped_items.append(item_name)
                    if item_name == "shortbow":
                        self.combat_mode  = "ranged"
                        self.combat_style = "rapid"
                    return True, f"Equipped {item_name.replace('_', ' ').title()}!"
        return False, "Cannot use this item."

    def unequip_item(self, item_name):
        if item_name not in self.equipped_items:
            return False, "That item is not equipped."
        if not self.inventory.add_item(item_name, 1):
            return False, "Your inventory is full."

        self.equipped_items.remove(item_name)
        if item_name == "shortbow" and self.combat_mode == "ranged" and not self.has_bow():
            self.set_combat_mode("melee")
        return True, f"Removed {item_name.replace('_', ' ').title()}."

    def reset_after_death(self):
        """Reset player state after safe death/respawn."""
        # Clear all action/combat state
        self.current_action = None
        self.action_target = None
        self.action_timer = 0
        self.target_destination = None
        self.interaction_target = None
        self.waypoints = []
        
        # Restore HP and reset defensive state
        self.hp = self.max_hp
        self.last_hit_time = 0