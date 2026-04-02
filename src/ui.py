import pygame

class UIManager:
    def __init__(self, inventory):
        self.inventory = inventory
        pygame.font.init() # Ensure font module is initialized
        self.font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 32)
        
        self.message = ""
        self.message_timer = 0
        self.message_duration = 3000 # 3 seconds in ms

    def show_message(self, text):
        self.message = text
        self.message_timer = pygame.time.get_ticks()

    def update(self):
        if self.message and pygame.time.get_ticks() - self.message_timer > self.message_duration:
            self.message = ""

    def draw(self, surface):
        # Draw Inventory
        y_offset = 10
        title_surf = self.font.render("Inventory:", True, (255, 255, 255))
        surface.blit(title_surf, (10, y_offset))
        y_offset += 25
        
        for item, count in self.inventory.items.items():
            item_surf = self.font.render(f"{item.capitalize()}: {count}", True, (200, 200, 200))
            surface.blit(item_surf, (10, y_offset))
            y_offset += 25

        # Draw Message
        if self.message:
            msg_surf = self.large_font.render(self.message, True, (255, 255, 0))
            msg_rect = msg_surf.get_rect(center=(surface.get_width() // 2, 50))
            surface.blit(msg_surf, msg_rect)
