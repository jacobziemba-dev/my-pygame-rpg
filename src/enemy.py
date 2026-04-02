import math
import pygame

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.color = (255, 0, 0)
        self.hp = 30
        self.max_hp = 30
        self.speed = 2
        self.aggro_range = 250
        
        self.image = None

    def update(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        
        if 0 < dist < self.aggro_range:
            dx_norm = dx / dist
            dy_norm = dy / dist
            self.rect.x += dx_norm * self.speed
            self.rect.y += dy_norm * self.speed
            
    def draw(self, surface):
        if self.image:
             surface.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)
            
        if self.hp < self.max_hp:
            bar_width = 30
            bar_height = 5
            fill = (self.hp / self.max_hp) * bar_width
            
            x = self.rect.centerx - (bar_width // 2)
            y = self.rect.top - 10
            
            pygame.draw.rect(surface, (255, 0, 0), (x, y, bar_width, bar_height))
            pygame.draw.rect(surface, (0, 255, 0), (x, y, fill, bar_height))
