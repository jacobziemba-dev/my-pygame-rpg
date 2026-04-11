import pygame
import os
import math
from src.systems.inventory import Inventory
from src.systems.skill_manager import SkillManager
from src.core.settings import *
from src.core.utils import load_frames_from_sheet
from src.entities.entity import Entity
from src.entities.bank import Bank
from src.entities.shop import Shop
from src.systems.quest_manager import QuestManager
from src.entities.npc import NPC
from src.entities.resource_node import ResourceNode

# 2D HD Character Knight — Spritesheets/With shadows/*.png (128×128 cells).
# Maps logical names to files; "sit_down" is not included in this pack.
KNIGHT_ANIMATION_SOURCES = {
    # Basics
    "crouch_idle": "CrouchIdle.png",
    "die": "Die.png",
    "idle": "Idle.png",
    "idle2": "Idle2.png",
    "take_damage": "TakeDamage.png",
    # Movement
    "crouch_run": "CrouchRun.png",
    "walk": "Walk.png",
    "run": "Run.png",
    "run_backwards": "RunBackwards.png",
    "slide_start": "SlideStart.png",
    "slide": "Slide.png",
    "slide_end": "SlideEnd.png",
    "strafe_left": "StrafeLeft.png",
    "strafe_right": "StrafeRight.png",
    "rolling": "Rolling.png",
    "front_flip": "FrontFlip.png",
    # Combat
    "special_1": "Special1.png",
    "special_2": "Special2.png",
    "turn_180": "180Turn.png",
    "attack_1": "Melee.png",
    "attack_2": "Melee2.png",
    "attack_3": "MeleeSpin.png",
    "attack_run": "MeleeRun.png",
    "kick": "Kick.png",
    "pummel": "Pummel.png",
    "block_mid": "ShieldBlockMid.png",
    "block_start": "ShieldBlockStart.png",
    "cast_spell": "CastSpell.png",
    # Others
    "unsheath": "UnSheathSword.png",
}


class Player(Entity): 
    def __init__(self, x, y, game_manager):
        super().__init__(x, y, PLAYER_COLLISION_WIDTH, PLAYER_COLLISION_HEIGHT, game_manager)
        # Legacy spawn args were top-left of a TILE_SIZE cell; keep world position stable
        self.rect.center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
        self.quest_manager = QuestManager()
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
        self.combat_mode  = "melee"       # "melee" | "ranged" | "magic"
        self.combat_style = "aggressive"  # combat specific attack type
        
        self.spells = {
            "wind_strike": {"name": "Wind Strike", "req": 1, "cost": {"mind_rune": 1, "air_rune": 1}, "max_hit": 2, "xp": 5},
            "water_strike": {"name": "Water Strike", "req": 5, "cost": {"mind_rune": 1, "water_rune": 1, "air_rune": 1}, "max_hit": 4, "xp": 7},
            "earth_strike": {"name": "Earth Strike", "req": 9, "cost": {"mind_rune": 1, "earth_rune": 2, "air_rune": 1}, "max_hit": 6, "xp": 9},
            "fire_strike": {"name": "Fire Strike", "req": 13, "cost": {"mind_rune": 1, "fire_rune": 3, "air_rune": 2}, "max_hit": 8, "xp": 11}
        }
        self.active_spell = "wind_strike"
        
        self.current_action = None
        self.action_target = None
        self.action_timer = 0

        self.target_destination = None
        self.move_marker_pos = None
        self.move_marker_time = 0
        self.interaction_target = None
        self.interaction_type = "default"
        self.waypoints = []
        
        # Animations — cardinal suffix _up/_down/_left/_right (side-view art: E/W flip, N/S ±90°)
        self.facing = "_down"
        self.import_assets()
        self.status = "idle_down"
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
        self.hurt_until = 0

    @staticmethod
    def _flip_frames_h(frames):
        return [pygame.transform.flip(f, True, False) for f in frames]

    def _rot_frames(self, frames, angle_deg):
        sz = (PLAYER_SPRITE_SIZE, PLAYER_SPRITE_SIZE)
        out = []
        for f in frames:
            r = pygame.transform.rotate(f, angle_deg)
            out.append(pygame.transform.smoothscale(r, sz))
        return out

    def _cardinal_from_side_view(self, frames):
        """Strip faces right (+x). Left = mirror; up/down = ±90° then scale to sprite size."""
        if not frames:
            return {"_right": [], "_left": [], "_up": [], "_down": []}
        return {
            "_right": frames,
            "_left": self._flip_frames_h(frames),
            "_up": self._rot_frames(frames, 90),
            "_down": self._rot_frames(frames, -90),
        }

    def _cardinal_suffix_from_vector(self, vx, vy):
        if vx == 0 and vy == 0:
            return self.facing
        # Diagonal movement: dominant-axis pick maps equal |vx|==|vy| to vertical (walk_down),
        # but side-view sprites rotated for _down read as facing the wrong horizontal way.
        # Prefer left/right whenever both axes matter so e.g. down-left uses walk_left.
        if vx != 0 and vy != 0:
            return "_right" if vx > 0 else "_left"
        if abs(vx) > abs(vy):
            return "_right" if vx > 0 else "_left"
        return "_down" if vy > 0 else "_up"

    def import_assets(self):
        base = "assets/sprites/2D HD Character Knight/Spritesheets/With shadows"
        sz = (PLAYER_SPRITE_SIZE, PLAYER_SPRITE_SIZE)
        fw = PLAYER_SHEET_FRAME_WIDTH
        fh = PLAYER_SPRITE_SIZE

        def sheet(filename):
            return load_frames_from_sheet(f"{base}/{filename}", fw, sz, frame_height=fh)

        self.animations = {}
        for key, filename in KNIGHT_ANIMATION_SOURCES.items():
            self.animations[key] = sheet(filename)

        # Not in this pack (sit / social emote)
        self.animations["sit_down"] = []

        def add_cardinal(prefix, base_key):
            v = self._cardinal_from_side_view(self.animations.get(base_key) or [])
            for suf, fr in v.items():
                self.animations[prefix + suf] = fr

        add_cardinal("idle", "idle")
        add_cardinal("walk", "walk")
        add_cardinal("attack", "attack_1")
        add_cardinal("hurt", "take_damage")
        add_cardinal("death", "die")
        add_cardinal("cast_spell", "cast_spell")

    def get_status(self):
        now = pygame.time.get_ticks()
        was_hurt = self.status.startswith("hurt")
        was_attacking = self.status.startswith("attack_")
        if self.hp > 0 and now < self.hurt_until:
            self.status = "hurt" + self.facing
            return

        prev = self.status
        if self.current_action == "attacking":
            suf = self.facing
            t = self.action_target
            if t is not None and hasattr(t, "rect"):
                dx = t.rect.centerx - self.rect.centerx
                dy = t.rect.centery - self.rect.centery
                if dx != 0 or dy != 0:
                    suf = self._cardinal_suffix_from_vector(dx, dy)
            self.facing = suf
            self.status = "attack" + suf
        elif self.current_action == "gathering" and self.action_target is not None and hasattr(
            self.action_target, "rect"
        ):
            suf = self.facing
            t = self.action_target
            dx = t.rect.centerx - self.rect.centerx
            dy = t.rect.centery - self.rect.centery
            if dx != 0 or dy != 0:
                suf = self._cardinal_suffix_from_vector(dx, dy)
            self.facing = suf
            self.status = "attack" + suf
        elif self.direction.magnitude() > 0:
            self.facing = self._cardinal_suffix_from_vector(self.direction.x, self.direction.y)
            self.status = "walk" + self.facing
        else:
            self.status = "idle" + self.facing

        if was_hurt and not self.status.startswith("hurt"):
            self.frame_index = 0
        if was_attacking and not self.status.startswith("attack_"):
            self.frame_index = 0
        if prev != self.status and self.status.startswith("attack_"):
            self.frame_index = 0

    def animate(self, dt):
        status = self.status
        animation = None
        if (
            status.startswith("attack_")
            and self.current_action != "gathering"
            and self.combat_mode == "magic"
            and self.has_staff()
        ):
            suf = status[len("attack") :]  # e.g. "_right"
            animation = self.animations.get("cast_spell" + suf) or []
        if not animation:
            animation = (
                self.animations.get(status)
                or self.animations.get("idle" + self.facing)
                or []
            )
        if not animation:
            return

        loop = (
            not status.startswith("hurt")
            and not status.startswith("death")
            and (
                not status.startswith("attack_")
                or self.current_action == "gathering"
            )
        )

        self.frame_index += self.animation_speed * dt * 60
        if loop:
            if self.frame_index >= len(animation):
                self.frame_index = 0
        else:
            if self.frame_index >= len(animation):
                self.frame_index = len(animation) - 1

        self.image = animation[int(self.frame_index)]

    def begin_death_animation(self):
        self.hurt_until = 0
        self.status = "death" + self.facing
        self.frame_index = 0
        death = self.animations.get(self.status) or []
        if death:
            self.image = death[0]

    def update_death_animation(self, dt):
        self.status = "death" + self.facing
        self.animate(dt)

    def set_target_destination(self, x, y, target_entity=None, waypoints=None, action_type="default"):
        # Snap marker to tile center for RuneScape feel
        snap_x = (x // TILE_SIZE) * TILE_SIZE + TILE_SIZE // 2
        snap_y = (y // TILE_SIZE) * TILE_SIZE + TILE_SIZE // 2
        self.move_marker_pos = (snap_x, snap_y)
        self.move_marker_time = pygame.time.get_ticks()

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

    def update(self, dt):
        self.direction.xy = (0, 0)
        if self.target_destination:
            tx, ty = self.target_destination
            dx = tx - self.rect.centerx
            dy = ty - self.rect.centery
            dist = math.hypot(dx, dy)

            # Move towards target if not close enough
            if dist > ARRIVE_THRESHOLD:
                dx_norm = dx / dist
                dy_norm = dy / dist
                self.direction.x = dx_norm
                self.direction.y = dy_norm
                self.rect.x += dx_norm * self.speed * dt * 60
                self.rect.y += dy_norm * self.speed * dt * 60
            else:
                if self.waypoints:
                    # Intermediate waypoint reached — advance to next, no interaction yet
                    self.target_destination = self.waypoints.pop(0)
                else:
                    # Final destination reached — snap and trigger interaction
                    self.rect.centerx = tx
                    self.rect.centery = ty
                    self.target_destination = None
                    self.move_marker_pos = None  # Reached destination, clear marker

                    if self.interaction_target:
                        if isinstance(self.interaction_target, ResourceNode):
                            self.game_manager._try_begin_gathering(self.interaction_target)
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
                        elif isinstance(self.interaction_target, NPC):
                             if hasattr(self.game_manager, 'ui'):
                                 node_id = self.interaction_target.get_interaction_node(self)
                                 if node_id:
                                     self.game_manager.ui.show_dialogue_node(node_id)
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
                                     if wood_ok or stone_ok:
                                         self.game_manager.resources.remove(item)
                                 else:
                                     if self.inventory.add_item(item.resource_type, 1):
                                         if hasattr(self.game_manager, 'ui'):
                                            self.game_manager.ui.show_message(f"Picked up 1 {item.resource_type}!")
                                         self.game_manager.resources.remove(item)
                                     else:
                                         if hasattr(self.game_manager, 'ui'):
                                            self.game_manager.ui.show_message("Your inventory is full.")
                                         # Keep item on the ground when pickup fails.

                        self.interaction_target = None
                    

        # Keyboard fallback removed (forced click-to-move for RS feel)

        self.get_status()
        self.animate(dt)
            
        self.rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))

    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.image:
            # Feet on collision footprint; sprite extends upward (fixes overlap vs 32×32 center blit)
            img_rect = self.image.get_rect(midbottom=draw_rect.midbottom)
            surface.blit(self.image, img_rect)

        # Draw movement target indicator (RS-style yellow X)
        if self.move_marker_pos:
            current_time = pygame.time.get_ticks()
            # Only draw for 2 seconds
            if current_time - self.move_marker_time < 2000:
                tx = self.move_marker_pos[0]
                ty = self.move_marker_pos[1]
                if camera:
                    tx -= camera.camera_rect.x
                    ty -= camera.camera_rect.y
                
                if (current_time // 200) % 2 == 0:
                    x_color = (255, 230, 0, 180)
                    length = 8
                    # Draw an X
                    pygame.draw.line(surface, x_color, (tx - length, ty - length), (tx + length, ty + length), 3)
                    pygame.draw.line(surface, x_color, (tx - length, ty + length), (tx + length, ty - length), 3)
            else:
                self.move_marker_pos = None

    @property
    def sprite_top_y(self):
        """World Y of the top edge of the drawn sprite (feet aligned to rect.bottom)."""
        return self.rect.bottom - PLAYER_SPRITE_SIZE

    def take_damage(self, amount):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time > 1000:
            # apply defense
            actual_damage = max(1, amount - self.get_defense())
            self.hp -= actual_damage
            if self.hp < 0:
                self.hp = 0
            self.last_hit_time = current_time
            if self.hp <= 0:
                self.hurt_until = 0
            else:
                self.hurt_until = current_time + 450
                self.frame_index = 0
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

    def has_staff(self):
        return any("staff" in item for item in self.equipped_items)

    def set_combat_mode(self, mode):
        if mode == "melee":
            self.combat_mode, self.combat_style = "melee", "aggressive"
        elif mode == "ranged":
            self.combat_mode, self.combat_style = "ranged", "rapid"
        elif mode == "magic":
            self.combat_mode, self.combat_style = "magic", "magic"

    def set_combat_style(self, style):
        melee_styles  = {"accurate", "aggressive", "defensive"}
        ranged_styles = {"accurate", "rapid", "longrange"}
        magic_styles = {"magic"}
        if self.combat_mode == "melee" and style in melee_styles:
            self.combat_style = style
        elif self.combat_mode == "ranged" and style in ranged_styles:
            self.combat_style = style
        elif self.combat_mode == "magic" and style in magic_styles:
            self.combat_style = style

    def get_xp_skill_for_hit(self):
        """Returns (primary_skill, secondary_skill_or_None) based on current mode+style."""
        if self.combat_mode == "melee":
            return {
                "accurate":   ("attack",   None),
                "aggressive": ("strength", None),
                "defensive":  ("defense",  None),
            }.get(self.combat_style, ("strength", None))
        elif self.combat_mode == "ranged":
            return {
                "accurate":  ("ranged", None),
                "rapid":     ("ranged", None),
                "longrange": ("ranged", "defense"),
            }.get(self.combat_style, ("ranged", None))
        else:
            return ("magic", None)

    def _check_item_requirement(self, item_name):
        req = EQUIPMENT_REQUIREMENTS.get(item_name)
        if not req:
            return True, ""
        skill_name, level_required = req
        current = getattr(self.skills, skill_name).level
        if current < level_required:
            return False, f"You need {skill_name.capitalize()} Lv.{level_required} to wield this."
        return True, ""

    def use_item_at_slot(self, slot_index):
        pair = self.inventory.get_slot(slot_index)
        if not pair:
            return False, "Nothing there."
        item_name, _count = pair
        if item_name == "bread":
            self.hp = min(self.max_hp, self.hp + 20)
            self.inventory.remove_from_slot(slot_index, 1)
            return True, "Healed 20 HP!"
        if item_name == "cooked_fish":
            self.hp = min(self.max_hp, self.hp + 15)
            self.inventory.remove_from_slot(slot_index, 1)
            return True, "Healed 15 HP with cooked fish!"
        equippable = [
            "sword", "iron_sword", "iron_armor", "iron_axe", "iron_pickaxe",
            "steel_sword", "steel_armor", "steel_axe", "steel_pickaxe", "shortbow", "staff_of_air",
        ]
        if item_name in equippable:
            meets_req, req_msg = self._check_item_requirement(item_name)
            if not meets_req:
                return False, req_msg
            if item_name not in self.equipped_items:
                self.inventory.remove_from_slot(slot_index, 1)
                self.equipped_items.append(item_name)
                if "bow" in item_name:
                    self.set_combat_mode("ranged")
                elif "staff" in item_name:
                    self.set_combat_mode("magic")
                return True, f"Equipped {item_name.replace('_', ' ').title()}!"
        return False, "Cannot use this item."

    def use_item(self, item_name):
        if self.inventory.get_item_count(item_name) <= 0:
            return False, "Cannot use this item."
        for i in range(self.inventory.MAX_SLOTS):
            p = self.inventory.get_slot(i)
            if p and p[0] == item_name:
                return self.use_item_at_slot(i)
        return False, "Cannot use this item."

    def unequip_item(self, item_name):
        if item_name not in self.equipped_items:
            return False, "That item is not equipped."
        if not self.inventory.add_item(item_name, 1):
            return False, "Your inventory is full."

        self.equipped_items.remove(item_name)
        if "bow" in item_name and self.combat_mode == "ranged" and not self.has_bow():
            self.set_combat_mode("melee")
        if "staff" in item_name and self.combat_mode == "magic" and not self.has_staff():
            self.set_combat_mode("melee")
        return True, f"Removed {item_name.replace('_', ' ').title()}."

    def reset_after_death(self):
        """Reset player state after safe death/respawn."""
        # Clear all action/combat state
        self.current_action = None
        self.action_target = None
        self.action_timer = 0
        self.target_destination = None
        self.move_marker_pos = None
        self.interaction_target = None
        self.waypoints = []
        
        # Restore HP and reset defensive state
        self.hp = self.max_hp
        self.last_hit_time = 0
        self.hurt_until = 0
        self.status = "idle" + self.facing
        self.frame_index = 0