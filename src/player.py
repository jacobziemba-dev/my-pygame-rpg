import pygame
import os
from src.inventory import Inventory

class Player: 
    def __init__(self, x, y): #* __init__ is the constructor for the Player class
        self.rect = pygame.Rect(x, y, 32, 32) 
        self.color = (0, 128, 255)
        self.speed = 4
        self.inventory = Inventory()
        
        self.max_hp = 100
        self.hp = 100
        self.last_hit_time = 0
        
        self.xp = 0
        self.level = 1
        self.base_attack = 5
        self.base_defense = 0
        self.equipped_items = []
        
        self.image = None
        sprite_path = os.path.join("assets", "sprites", "player.png")
        if os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
            except pygame.error:
                pass

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.rect.y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            
        self.rect.clamp_ip(pygame.Rect(0, 0, 2400, 2400))

    def draw(self, surface, camera=None): #* draw function is used to draw the player character on the screen
        # Flash player transparent if they were hit recently
        current_time = pygame.time.get_ticks()
        if current_time - self.last_hit_time < 1000 and (current_time // 100) % 2 == 0:
            return

        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.image:
            surface.blit(self.image, draw_rect)
        else:
            pygame.draw.rect(surface, self.color, draw_rect)

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
        if "sword" in self.equipped_items:
            attack += 5
        return attack

    def get_defense(self):
        return self.base_defense

    def gain_xp(self, amount):
        self.xp += amount
        threshold = self.level * 50
        leveled_up = False
        while self.xp >= threshold:
            self.xp -= threshold
            self.level += 1
            self.max_hp += 10
            self.hp = self.max_hp
            self.base_attack += 2
            threshold = self.level * 50
            leveled_up = True
        return leveled_up

    def equip(self, item_name):
        if self.inventory.items.get(item_name, 0) > 0:
            if item_name not in self.equipped_items:
                self.inventory.remove_item(item_name, 1)
                self.equipped_items.append(item_name)
                return True
        return False













