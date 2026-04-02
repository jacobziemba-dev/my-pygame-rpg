import pygame
import os
from src.systems.inventory import Inventory
from src.core.settings import TILE_SIZE

class Bank:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, TILE_SIZE * 2, TILE_SIZE * 2) # Making bank a 2x2 tile object
        self.inventory = Inventory()
        
        self.image = None
        sprite_path = os.path.join("assets", "sprites", "bank.png")
        if os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
            except pygame.error:
                pass
                
    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.image:
            surface.blit(self.image, draw_rect)
        else:
            pygame.draw.rect(surface, (150, 100, 50), draw_rect) # Brownish block
            # Add some details
            pygame.draw.rect(surface, (100, 50, 0), draw_rect, 4)
            # $ Sign
            font = pygame.font.SysFont(None, 40)
            text = font.render("$", True, (255, 215, 0))
            text_rect = text.get_rect(center=draw_rect.center)
            surface.blit(text, text_rect)
