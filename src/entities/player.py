import pygame
import os
import math
from src.systems.inventory import Inventory
from src.systems.skill_manager import SkillManager
from src.core.settings import *
from src.entities.entity import Entity

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
        
        self.current_action = None
        self.action_target = None
        self.action_timer = 0

        self.target_destination = None
        self.interaction_target = None
        
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

    def set_target_destination(self, x, y, target_entity=None):
        self.target_destination = (x, y)
        self.interaction_target = target_entity
        self.current_action = None
        self.action_target = None

    def update(self, dt):
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
                self.rect.y += dy_norm * self.speed * dt * 60
                moved = True
            else:
                self.rect.centerx = tx
                self.rect.centery = ty
                self.target_destination = None
                
                # Arrived at target, initiate interaction if there is one
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
                    elif hasattr(self.interaction_target, 'inventory') and hasattr(self.interaction_target, 'rect') and hasattr(self.interaction_target, 'image'):
                         # It's the Bank
                         if hasattr(self.game_manager, 'ui'):
                             self.game_manager.ui.active_bank = True
                             self.game_manager.ui.show_message("Opened bank vault.")
                    elif hasattr(self.interaction_target, 'resource_type'):
                         # It's a dropped item
                         item = self.interaction_target
                         if item in self.game_manager.resources:
                             if item.resource_type == "chest":
                                 self.inventory.add_item("wood", 10)
                                 self.inventory.add_item("stone", 10)
                                 if hasattr(self.game_manager, 'ui'):
                                    self.game_manager.ui.show_message("Opened Chest! Huge Loot gained.")
                             else:
                                 self.inventory.add_item(item.resource_type, 1)
                                 if hasattr(self.game_manager, 'ui'):
                                    self.game_manager.ui.show_message(f"Picked up 1 {item.resource_type}!")
                             self.game_manager.resources.remove(item)
                    
                    self.interaction_target = None
                    

        # Keyboard fallback
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.direction.y = -1
            self.rect.y -= self.speed * dt * 60
            moved = True
            self.target_destination = None
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction.y = 1
            self.rect.y += self.speed * dt * 60
            moved = True
            self.target_destination = None
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.rect.x -= self.speed * dt * 60
            moved = True
            self.target_destination = None
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.rect.x += self.speed * dt * 60
            moved = True
            self.target_destination = None
            
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

        # Draw movement target indicator
        if self.target_destination:
            target_rect = pygame.Rect(self.target_destination[0] - 5, self.target_destination[1] - 5, 10, 10)
            if camera:
                target_rect = camera.apply(target_rect)
            pygame.draw.circle(surface, (200, 200, 200, 100), target_rect.center, 6, 2)


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
                if item_name not in self.equipped_items:
                    # Unequip similar type? (simple version: just add)
                    self.inventory.remove_item(item_name, 1)
                    self.equipped_items.append(item_name)
                    return True, f"Equipped {item_name.replace('_', ' ').title()}!"
        return False, "Cannot use this item."