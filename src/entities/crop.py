import pygame
import os
from src.core.settings import TILE_SIZE

class Crop:
    def __init__(self, x, y, crop_type="wheat"):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.crop_type = crop_type
        self.growth_stage = 0
        self.max_growth = 3
        self.growth_timer = pygame.time.get_ticks()
        self.growth_delay = 5000 # 5 seconds per stage
        self.is_mature = False
        
        self.colors = {
            0: (100, 80, 20),  # Tilled Soil
            1: (50, 150, 50),  # Sprout
            2: (100, 200, 50), # Growing
            3: (200, 200, 20)  # Mature (Harvestable)
        }
        
    def update(self):
        if not self.is_mature:
            current_time = pygame.time.get_ticks()
            if current_time - self.growth_timer >= self.growth_delay:
                self.growth_timer = current_time
                self.growth_stage += 1
                if self.growth_stage >= self.max_growth:
                    self.growth_stage = self.max_growth
                    self.is_mature = True
                    
    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        color = self.colors.get(self.growth_stage, (100, 80, 20))
        
        # Draw soil background
        pygame.draw.rect(surface, (100, 80, 20), draw_rect)
        
        # Draw crop visually depending on stage
        if self.growth_stage == 1:
            pygame.draw.circle(surface, color, draw_rect.center, 4)
        elif self.growth_stage == 2:
            pygame.draw.circle(surface, color, draw_rect.center, 8)
        elif self.growth_stage == 3:
            pygame.draw.rect(surface, color, draw_rect.inflate(-4, -4))
