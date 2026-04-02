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
        self.show_crafting = False
        self.crafting_index = 0

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
            if count == 0:
                continue
            label = item.replace('_', ' ').title()
            item_surf = self.font.render(f"{label}: {count}", True, (200, 200, 200))
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

        # Draw control hints (bottom-right)
        hints = ["[E] Gather", "[Space] Attack", "[C] Craft", "[K] Skills", "[F5] Save", "[F9] Load"]
        hint_x = surface.get_width() - 110
        hint_y = surface.get_height() - len(hints) * 18 - 10
        for i, hint in enumerate(hints):
            hint_surf = self.font.render(hint, True, (110, 110, 110))
            surface.blit(hint_surf, (hint_x, hint_y + i * 18))

        # Draw overlays
        if self.show_skills:
            self._draw_skills_panel(surface)
        if self.show_crafting:
            self._draw_crafting_menu(surface)

        # Draw Message
        if self.message:
            msg_surf = self.large_font.render(self.message, True, (255, 255, 0))
            msg_rect = msg_surf.get_rect(center=(surface.get_width() // 2, 50))
            surface.blit(msg_surf, msg_rect)

    def _draw_crafting_menu(self, surface):
        from src.inventory import RECIPES
        panel_w, panel_h = 400, 300
        panel_x = (surface.get_width() - panel_w) // 2
        panel_y = (surface.get_height() - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 220))
        surface.blit(panel, (panel_x, panel_y))

        # Header
        title = self.font.render("Crafting Menu", True, (255, 215, 0))
        surface.blit(title, (panel_x + 10, panel_y + 8))
        controls = self.font.render("[ESC] Close  [↑↓] Select  [Enter] Craft", True, (140, 140, 140))
        surface.blit(controls, (panel_x + 10, panel_y + 28))
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + 48), (panel_x + panel_w, panel_y + 48))

        crafting_level = self.player.skills.crafting.level

        # Recipe list
        list_top = panel_y + 54
        for i, recipe in enumerate(RECIPES):
            row_y = list_top + i * 22
            if row_y > panel_y + panel_h - 86:
                break
            can_level = crafting_level >= recipe["min_level"]
            can_items = all(self.player.inventory.items.get(k, 0) >= v for k, v in recipe["inputs"].items())

            if i == self.crafting_index:
                pygame.draw.rect(surface, (60, 55, 15), (panel_x + 4, row_y - 2, panel_w - 8, 20))

            name_color = (220, 220, 220) if can_level else (90, 90, 90)
            status = "✓" if (can_level and can_items) else ("✗ Lv." + str(recipe["min_level"]) if not can_level else "✗ items")
            status_color = (80, 200, 80) if (can_level and can_items) else (200, 80, 80)

            label = f"{'>' if i == self.crafting_index else ' '} {recipe['label']}"
            surface.blit(self.font.render(label, True, name_color), (panel_x + 8, row_y))
            status_surf = self.font.render(status, True, status_color)
            surface.blit(status_surf, (panel_x + panel_w - status_surf.get_width() - 10, row_y))

        # Detail section
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + panel_h - 76), (panel_x + panel_w, panel_y + panel_h - 76))
        if 0 <= self.crafting_index < len(RECIPES):
            r = RECIPES[self.crafting_index]
            inputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["inputs"].items())
            outputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["outputs"].items())
            surface.blit(self.font.render(f"In:  {inputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 70))
            surface.blit(self.font.render(f"Out: {outputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 48))
            surface.blit(self.font.render(f"XP:  +{r['xp']} Crafting", True, (160, 210, 160)), (panel_x + 10, panel_y + panel_h - 26))

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
