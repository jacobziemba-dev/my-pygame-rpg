import pygame
import os

class ResourceItem:
    def __init__(self, x, y, resource_type):
        self.resource_type = resource_type
        
        # Determine color and size based on type
        if self.resource_type == "wood":
            self.color = (139, 69, 19) # Brown
            self.rect = pygame.Rect(x, y, 20, 20)
        elif self.resource_type == "stone":
            self.color = (169, 169, 169) # Gray
            self.rect = pygame.Rect(x, y, 16, 16)
        else:
            self.color = (255, 255, 255)
            self.rect = pygame.Rect(x, y, 20, 20)
            
        self.image = None
        sprite_path = os.path.join("assets", "sprites", f"{self.resource_type}.png")
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
            pygame.draw.rect(surface, self.color, draw_rect)
