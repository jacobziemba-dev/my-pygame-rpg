import math
import pygame
from src.core.settings import *
from src.entities.entity import Entity

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE)
        self.color = COLOR_ENEMY
        self.hp = 30
        self.max_hp = 30
        self.speed = 2
        self.aggro_range = 250
        
        self.image = None

    def update(self, player, dt):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        
        if 0 < dist < self.aggro_range:
            dx_norm = dx / dist
            dy_norm = dy / dist
            self.rect.x += dx_norm * self.speed * dt * 60
            self.rect.y += dy_norm * self.speed * dt * 60
            
    def draw(self, surface, camera=None):
        super().draw(surface, camera)
        draw_rect = camera.apply(self.rect) if camera else self.rect
            
        if self.hp < self.max_hp:
            bar_width = 30
            bar_height = 5
            fill = (self.hp / self.max_hp) * bar_width
            
            x = draw_rect.centerx - (bar_width // 2)
            y = draw_rect.top - 10
            
            pygame.draw.rect(surface, (255, 0, 0), (x, y, bar_width, bar_height))
            pygame.draw.rect(surface, (0, 255, 0), (x, y, fill, bar_height))
