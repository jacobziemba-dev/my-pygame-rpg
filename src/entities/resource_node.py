import pygame
import os
from src.core.settings import *

class ResourceNode:
    def __init__(self, x, y, node_type, difficulty, tool_required, yields, hp, respawn_time, min_level=1):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.node_type = node_type
        self.difficulty = difficulty
        self.tool_required = tool_required
        self.yields = yields
        self.max_hp = hp
        self.hp = hp
        self.respawn_time = respawn_time
        self.min_level = min_level
        self.dead_timer = 0
        self.is_active = True
        
        self.image = None
        sprite_path = os.path.join("assets", "sprites", f"{self.node_type}.png")
        if os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
            except pygame.error:
                pass
                
        if node_type == "tree":
            self.active_color = (0, 200, 0)
        elif node_type == "iron_rock":
            self.active_color = (180, 80, 20)
        elif node_type == "bush":
            self.active_color = (34, 139, 34)
        elif node_type == "fishing_spot":
            self.active_color = (30, 144, 255)
        else:
            self.active_color = (150, 150, 150)
        self.dead_color = (100, 100, 100)

    def update(self):
        if not self.is_active:
            current_time = pygame.time.get_ticks()
            if current_time - self.dead_timer >= self.respawn_time:
                self.respawn()

    def take_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.is_active = False
            self.dead_timer = pygame.time.get_ticks()

    def respawn(self):
        self.is_active = True
        self.hp = self.max_hp

    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.is_active:
            if self.image:
                surface.blit(self.image, draw_rect)
            else:
                pygame.draw.rect(surface, self.active_color, draw_rect)
        else:
            pygame.draw.rect(surface, self.dead_color, draw_rect)
