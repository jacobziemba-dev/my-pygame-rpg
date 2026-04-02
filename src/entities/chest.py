import pygame
import os
from src.core.settings import TILE_SIZE
from src.systems.inventory import Inventory

class Chest:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.inventory = Inventory()
        self.is_open = False
        
        self.image = None
        sprite_path = os.path.join("assets", "sprites", "chest.png")
        if os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
            except pygame.error:
                pass
        
        self.color = (139, 69, 19) # Brown
        
    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.image:
            surface.blit(self.image, draw_rect)
        else:
            pygame.draw.rect(surface, self.color, draw_rect)
            # Draw a small detail for the lock/handle
            lock_rect = pygame.Rect(draw_rect.centerx - 4, draw_rect.centery - 2, 8, 4)
            pygame.draw.rect(surface, (255, 215, 0), lock_rect)
