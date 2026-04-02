import pygame

class Camera:
    def __init__(self, width, height, map_width, map_height):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height
        
    def update(self, target):
        x = target.rect.centerx - int(self.width / 2)
        y = target.rect.centery - int(self.height / 2)
        
        x = max(0, min(x, self.map_width - self.width))
        y = max(0, min(y, self.map_height - self.height))
        
        self.camera_rect = pygame.Rect(x, y, self.width, self.height)
        
    def apply(self, entity_rect):
        return entity_rect.move(-self.camera_rect.x, -self.camera_rect.y)
