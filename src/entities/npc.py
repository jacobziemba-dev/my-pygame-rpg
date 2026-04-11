import pygame
import os
from src.core.settings import TILE_SIZE

class NPC:
    def __init__(self, x, y, name, color=(150, 100, 200)):
        self.name = name
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.color = color
        
        self.image = None
        # Attempt to load sprite with given name
        sprite_path = os.path.join("assets", "sprites", "npc", f"{name.lower()}.png")
        if os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
            except pygame.error:
                pass

    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.image:
            surface.blit(self.image, draw_rect)
        else:
            pygame.draw.rect(surface, self.color, draw_rect)
            
    def get_interaction_node(self, player):
        """Determine which node of dialogue to return based on quest state."""
        if self.name == "Baker":
            status = player.quest_manager.get_status("bakers_assistant")
            if status == "unstarted":
                return "baker_start"
            elif status == "active":
                return "baker_progress"
            else:
                return "baker_finished"
        return None
