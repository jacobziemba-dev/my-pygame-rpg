import pygame

class UIManager:
    def __init__(self, player):
        self.player = player
        pygame.font.init() # Ensure font module is initialized
        self.font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 32)
        
        self.message = ""
        self.message_timer = 0
        self.message_duration = 3000 # 3 seconds in ms
        self.show_skills = False

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
        
        for item, count in self.player.inventory.items.items():
            item_surf = self.font.render(f"{item.capitalize()}: {count}", True, (200, 200, 200))
            surface.blit(item_surf, (10, y_offset))
            y_offset += 25

        # Draw Player HP Bar
        hp_bar_width = 200
        hp_bar_height = 20
        hp_y = surface.get_height() - hp_bar_height - 20
        hp_x = 20
        fill = (self.player.hp / self.player.max_hp) * hp_bar_width
        
        # Draw Player Stats
        melee = self.player.skills.melee
        stats_text = (f"Melee Lv.{melee.level} (XP: {melee.xp}/{melee.xp_threshold()}) "
                      f"| ATK: {self.player.get_attack()} | DEF: {self.player.get_defense()}")
        stats_surf = self.font.render(stats_text, True, (255, 215, 0)) # Gold Text
        surface.blit(stats_surf, (hp_x, hp_y - 45))
        
        pygame.draw.rect(surface, (255, 0, 0), (hp_x, hp_y, hp_bar_width, hp_bar_height))
        if fill > 0:
            pygame.draw.rect(surface, (0, 255, 0), (hp_x, hp_y, fill, hp_bar_height))
            
        hp_text = self.font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, (255, 255, 255))
        surface.blit(hp_text, (hp_x, hp_y - 20))

        # Draw Skills panel hint
        hint_surf = self.font.render("[K] Skills", True, (160, 160, 160))
        surface.blit(hint_surf, (surface.get_width() - 90, 10))

        # Draw Skills overlay
        if self.show_skills:
            self._draw_skills_panel(surface)

        # Draw Message
        if self.message:
            msg_surf = self.large_font.render(self.message, True, (255, 255, 0))
            msg_rect = msg_surf.get_rect(center=(surface.get_width() // 2, 50))
            surface.blit(msg_surf, msg_rect)

    def _draw_skills_panel(self, surface):
        panel_w, panel_h = 220, 140
        panel_x = surface.get_width() - panel_w - 10
        panel_y = 30

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        surface.blit(panel, (panel_x, panel_y))

        title = self.font.render("Skills", True, (255, 215, 0))
        surface.blit(title, (panel_x + 8, panel_y + 6))

        for i, skill in enumerate(self.player.skills.all_skills()):
            row_y = panel_y + 28 + i * 26
            label = f"{skill.name:<14} Lv.{skill.level:<3} XP: {skill.xp}/{skill.xp_threshold()}"
            text_surf = self.font.render(label, True, (220, 220, 220))
            surface.blit(text_surf, (panel_x + 8, row_y))
