import pygame

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
            
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
