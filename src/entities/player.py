import pygame
import os
import math
from src.systems.inventory import Inventory
from src.systems.skill_manager import SkillManager
from src.core.settings import *

class Player: 
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE) 
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
        
        # Grant starting tools
        self.inventory.add_item("bronze_axe", 1)
        self.inventory.add_item("bronze_pickaxe", 1)
        self.inventory.add_item("bronze_hoe", 1)
        self.inventory.add_item("wheat_seeds", 5)

        self.image = None
        sprite_path = os.path.join("assets", "sprites", "player.png")
        if os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
            except pygame.error:
                pass

    def set_target_destination(self, x, y, target_entity=None):
        self.target_destination = (x, y)
        self.interaction_target = target_entity
        self.current_action = None
        self.action_target = None

    def update(self):
        moved = False
        if self.target_destination:
            tx, ty = self.target_destination
            dx = tx - self.rect.centerx
            dy = ty - self.rect.centery
            dist = math.hypot(dx, dy)

            # Move towards target if not close enough
            if dist > self.speed:
                dx_norm = dx / dist
                dy_norm = dy / dist
                self.rect.x += dx_norm * self.speed
                self.rect.y += dy_norm * self.speed
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
            self.rect.y -= self.speed
            moved = True
            self.target_destination = None
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.rect.y += self.speed
            moved = True
            self.target_destination = None
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
            moved = True
            self.target_destination = None
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            moved = True
            self.target_destination = None
            
        if moved and self.current_action is not None and not self.target_destination:
            self.current_action = None
            self.action_target = None
            
        self.rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))

    def draw(self, surface, camera=None):
        # Flash player transparent if they were hit recently
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time < 1000 and (current_time // 100) % 2 == 0:
            return

        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.image:
            surface.blit(self.image, draw_rect)
        else:
            pygame.draw.rect(surface, self.color, draw_rect)

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

    def use_item(self, item_name):
        if self.inventory.items.get(item_name, 0) > 0:
            if item_name == "bread":
                self.hp = min(self.max_hp, self.hp + 20)
                self.inventory.remove_item(item_name, 1)
                return True, "Healed 20 HP!"
            # For gear, equip it
            if item_name in ["sword", "iron_sword", "iron_armor"]:
                if item_name not in self.equipped_items:
                    # Unequip similar type? (simple version: just add)
                    self.inventory.remove_item(item_name, 1)
                    self.equipped_items.append(item_name)
                    return True, f"Equipped {item_name.replace('_', ' ').title()}!"
        return False, "Cannot use this item."