import pygame
import os
from src.systems.recipe_manager import RecipeManager
from src.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class UIManager:
    def __init__(self, player):
        self.player = player
        self.recipe_manager = RecipeManager()
        pygame.font.init() # Ensure font module is initialized
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 18)
        self.large_font = pygame.font.SysFont(None, 32)
        
        self.message = ""
        self.message_timer = 0
        self.message_duration = 3000 # 3 seconds in ms
        self.show_inventory = False
        self.show_skills = False
        self.show_crafting = False
        self.crafting_index = 0
        self.inventory_index = 0
        self.bank_index = 0
        self.active_bank = False
        self.active_station = None
        self.station_index = 0
        self.skills_scroll_y = 0
        
        self.item_images = {}
        self._load_item_sprites()

    def _load_item_sprites(self):
        # We'll try to load sprites for any item that might exist in inventory
        item_types = ["wood", "stone", "sword", "iron_ore", "iron_bar", "iron_sword", 
                      "iron_axe", "iron_pickaxe", "chest_item", "bread", "wheat", 
                      "iron_armor", "wheat_seeds", "bronze_axe", "bronze_pickaxe", "bronze_hoe"]
        
        for item in item_types:
            sprite_name = item
            if item == "chest_item": sprite_name = "chest"
            
            path = os.path.join("assets", "sprites", f"{sprite_name}.png")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    img = pygame.transform.scale(img, (32, 32))
                    self.item_images[item] = img
                except:
                    pass

    def show_message(self, text):
        self.message = text
        self.message_timer = pygame.time.get_ticks()

    def reset_skills_scroll(self):
        self.skills_scroll_y = 0

    def scroll_skills(self, wheel_y):
        """Mouse wheel: positive y scrolls content up."""
        self.skills_scroll_y = max(0, self.skills_scroll_y - wheel_y * 24)

    def _skills_panel_content_height(self):
        h = 0
        for _, _, skills in self.player.skills.skills_by_category():
            h += 22
            h += len(skills) * 20
        return h

    def update(self):
        if self.message and pygame.time.get_ticks() - self.message_timer > self.message_duration:
            self.message = ""

    def draw(self, surface):
        # Draw Player HP Bar
        hp_bar_width = 200
        hp_bar_height = 20
        hp_y = surface.get_height() - hp_bar_height - 20
        hp_x = 20
        fill = (self.player.hp / self.player.max_hp) * hp_bar_width
        
        # Draw Player Stats (combat skills + equipment)
        atk_s = self.player.skills.attack
        str_s = self.player.skills.strength
        con_s = self.player.skills.constitution
        stats_text = (
            f"ATK {atk_s.level} | STR {str_s.level} | CON {con_s.level} "
            f"| Hit: {self.player.get_attack()} | DEF: {self.player.get_defense()}"
        )
        stats_surf = self.font.render(stats_text, True, (255, 215, 0)) # Gold Text
        surface.blit(stats_surf, (hp_x, hp_y - 45))
        
        pygame.draw.rect(surface, (255, 0, 0), (hp_x, hp_y, hp_bar_width, hp_bar_height))
        if fill > 0:
            pygame.draw.rect(surface, (0, 255, 0), (hp_x, hp_y, fill, hp_bar_height))
            
        hp_text = self.font.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, (255, 255, 255))
        surface.blit(hp_text, (hp_x, hp_y - 20))

        # Draw control hints (bottom-right)
        hints = ["[I] Inventory", "[E] Interact", "[Space] Attack", "[C] Craft", "[Enter] Use/Equip", "[F] Farm", "[K] Skills", "[F5] Save", "[F9] Load"]
        hint_x = surface.get_width() - 140
        hint_y = surface.get_height() - len(hints) * 18 - 10
        for i, hint in enumerate(hints):
            hint_surf = self.font.render(hint, True, (110, 110, 110))
            surface.blit(hint_surf, (hint_x, hint_y + i * 18))

        # Draw overlays
        if self.show_inventory:
            self._draw_inventory_panel(surface)
        if self.show_skills:
            self._draw_skills_panel(surface)
        if self.show_crafting:
            self._draw_crafting_menu(surface)
        if self.active_bank:
            self._draw_bank_inventory(surface)
        if self.active_station:
            self._draw_station_menu(surface)

        # Draw Message
        if self.message:
            msg_surf = self.large_font.render(self.message, True, (255, 255, 0))
            msg_rect = msg_surf.get_rect(center=(surface.get_width() // 2, 50))
            surface.blit(msg_surf, msg_rect)

    def get_inventory_slot_rects(self):
        rects = []
        panel_w, panel_h = 320, 400
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        start_x = panel_x + 20
        start_y = panel_y + 70
        slots_per_row = 6
        slot_size = 40
        padding = 4
        
        active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0]
        
        for i in range(len(active_items)):
            row = i // slots_per_row
            col = i % slots_per_row
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            rects.append(pygame.Rect(x, y, slot_size, slot_size))
        return rects

    def get_bank_slot_rects(self, is_player_inv=False):
        rects = []
        panel_w, panel_h = 600, 450
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        start_x = panel_x + 20 if is_player_inv else panel_x + 320
        start_y = panel_y + 80
        slots_per_row = 6
        slot_size = 40
        padding = 4
        
        inventory = self.player.inventory if is_player_inv else self.player.bank_inventory
        active_items = [(item, count) for item, count in inventory.items.items() if count > 0]
        
        for i in range(len(active_items)):
            row = i // slots_per_row
            col = i % slots_per_row
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            rects.append(pygame.Rect(x, y, slot_size, slot_size))
        return rects

    def get_crafting_recipe_rects(self):
        rects = []
        panel_w, panel_h = 400, 300
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        list_top = panel_y + 54
        
        for i, recipe in enumerate(self.recipe_manager.get_all()):
            row_y = list_top + i * 22
            if row_y > panel_y + panel_h - 86:
                break
            rects.append(pygame.Rect(panel_x + 4, row_y - 2, panel_w - 8, 20))
        return rects

    def handle_mouse_event(self, event):
        if not (self.show_inventory or self.show_crafting or self.active_bank):
            return None, None

        if event.type == pygame.MOUSEMOTION:
            if self.active_bank:
                 p_rects = self.get_bank_slot_rects(is_player_inv=True)
                 for i, rect in enumerate(p_rects):
                     if rect.collidepoint(event.pos):
                         self.inventory_index = i
                         return None, None
                 b_rects = self.get_bank_slot_rects(is_player_inv=False)
                 for i, rect in enumerate(b_rects):
                     if rect.collidepoint(event.pos):
                         self.bank_index = i
                         return None, None
            elif self.show_inventory:
                rects = self.get_inventory_slot_rects()
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        self.inventory_index = i
                        break
            elif self.show_crafting:
                rects = self.get_crafting_recipe_rects()
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        self.crafting_index = i
                        break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if self.active_bank:
                     p_rects = self.get_bank_slot_rects(is_player_inv=True)
                     for i, rect in enumerate(p_rects):
                         if rect.collidepoint(event.pos):
                             return "deposit_item", i
                     b_rects = self.get_bank_slot_rects(is_player_inv=False)
                     for i, rect in enumerate(b_rects):
                         if rect.collidepoint(event.pos):
                             return "withdraw_item", i
                elif self.show_inventory:
                    rects = self.get_inventory_slot_rects()
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            self.inventory_index = i
                            return "use_item", i
                elif self.show_crafting:
                    rects = self.get_crafting_recipe_rects()
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            self.crafting_index = i
                            return "craft_item", i
            elif event.button == 3: # Right click
                if self.show_inventory:
                    rects = self.get_inventory_slot_rects()
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            self.inventory_index = i
                            return "drop_item", i
        return None, None

    def _draw_station_menu(self, surface):
        panel_w, panel_h = 400, 300
        panel_x = (surface.get_width() - panel_w) // 2
        panel_y = (surface.get_height() - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 220))
        surface.blit(panel, (panel_x, panel_y))

        # Header
        title = self.font.render(f"{self.active_station.name} Menu", True, (255, 215, 0))
        surface.blit(title, (panel_x + 10, panel_y + 8))
        controls = self.font.render("[ESC] Close  [↑↓] Select  [Enter] Process", True, (140, 140, 140))
        surface.blit(controls, (panel_x + 10, panel_y + 28))
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + 48), (panel_x + panel_w, panel_y + 48))

        recipes = self.recipe_manager.get_for_station(self.active_station.station_type)

        # Recipe list
        list_top = panel_y + 54
        for i, recipe in enumerate(recipes):
            row_y = list_top + i * 22
            if row_y > panel_y + panel_h - 86:
                break
            can_items = all(self.player.inventory.items.get(k, 0) >= v for k, v in recipe["inputs"].items())

            if i == self.station_index:
                pygame.draw.rect(surface, (60, 55, 15), (panel_x + 4, row_y - 2, panel_w - 8, 20))

            name_color = (220, 220, 220) if can_items else (90, 90, 90)
            status = "✓" if can_items else "✗ items"
            status_color = (80, 200, 80) if can_items else (200, 80, 80)

            label = f"{'>' if i == self.station_index else ' '} {recipe['label']}"
            surface.blit(self.font.render(label, True, name_color), (panel_x + 8, row_y))
            status_surf = self.font.render(status, True, status_color)
            surface.blit(status_surf, (panel_x + panel_w - status_surf.get_width() - 10, row_y))

        # Detail section
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + panel_h - 76), (panel_x + panel_w, panel_y + panel_h - 76))
        if 0 <= self.station_index < len(recipes):
            r = recipes[self.station_index]
            inputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["inputs"].items())
            outputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["outputs"].items())
            surface.blit(self.font.render(f"In:  {inputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 70))
            surface.blit(self.font.render(f"Out: {outputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 48))

    def _draw_crafting_menu(self, surface):
        panel_w, panel_h = 400, 300
        panel_x = (surface.get_width() - panel_w) // 2
        panel_y = (surface.get_height() - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((20, 20, 20, 220))
        surface.blit(panel, (panel_x, panel_y))

        # Header
        title = self.font.render("Hand Crafting", True, (255, 215, 0))
        surface.blit(title, (panel_x + 10, panel_y + 8))
        controls = self.font.render("[ESC] Close  [↑↓] Select  [Enter] Craft", True, (140, 140, 140))
        surface.blit(controls, (panel_x + 10, panel_y + 28))
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + 48), (panel_x + panel_w, panel_y + 48))

        crafting_level = self.player.skills.crafting.level

        # Filter out station recipes
        recipes = self.recipe_manager.get_handcrafted()

        # Recipe list
        list_top = panel_y + 54
        for i, recipe in enumerate(recipes):
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
        if 0 <= self.crafting_index < len(recipes):
            r = recipes[self.crafting_index]
            inputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["inputs"].items())
            outputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["outputs"].items())
            surface.blit(self.font.render(f"In:  {inputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 70))
            surface.blit(self.font.render(f"Out: {outputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 48))
            surface.blit(self.font.render(f"XP:  +{r['xp']} Crafting", True, (160, 210, 160)), (panel_x + 10, panel_y + panel_h - 26))

    def _draw_skills_panel(self, surface):
        panel_w = 320
        panel_h = min(440, surface.get_height() - 20)
        panel_x = surface.get_width() - panel_w - 10
        panel_y = 10

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 200))
        surface.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(surface, (80, 70, 40), (panel_x, panel_y, panel_w, panel_h), 2)

        title = self.font.render("Skills", True, (255, 215, 0))
        surface.blit(title, (panel_x + 8, panel_y + 6))
        hint = self.small_font.render("[Wheel] Scroll  [ESC] Close", True, (140, 140, 140))
        surface.blit(hint, (panel_x + panel_w - hint.get_width() - 8, panel_y + 10))

        content_top = panel_y + 36
        clip_h = panel_h - 44
        total_h = self._skills_panel_content_height()
        max_scroll = max(0, total_h - clip_h)
        self.skills_scroll_y = min(self.skills_scroll_y, max_scroll)

        y = content_top - self.skills_scroll_y
        for _, cat_label, skills in self.player.skills.skills_by_category():
            if y + 22 > content_top - 500 and y < content_top + clip_h + 500:
                cat_surf = self.small_font.render(cat_label, True, (200, 180, 100))
                surface.blit(cat_surf, (panel_x + 8, y))
            y += 22
            for skill in skills:
                label = f"  {skill.name}  Lv.{skill.level}  {skill.xp}/{skill.xp_threshold()} XP"
                if y + 20 > content_top and y < content_top + clip_h:
                    text_surf = self.small_font.render(label, True, (220, 220, 220))
                    surface.blit(text_surf, (panel_x + 10, y))
                y += 20

        if max_scroll > 0:
            sb_x = panel_x + panel_w - 8
            track_top = content_top
            track_h = clip_h
            pygame.draw.line(surface, (60, 60, 60), (sb_x, track_top), (sb_x, track_top + track_h), 2)
            thumb_h = max(20, int(track_h * (clip_h / total_h)))
            thumb_y = track_top + int((track_h - thumb_h) * (self.skills_scroll_y / max_scroll)) if max_scroll else track_top
            pygame.draw.rect(surface, (120, 120, 120), (sb_x - 3, thumb_y, 6, thumb_h))

    def _draw_bank_inventory(self, surface):
        panel_w, panel_h = 600, 450
        panel_x = (surface.get_width() - panel_w) // 2
        panel_y = (surface.get_height() - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 30, 20, 230))
        surface.blit(panel, (panel_x, panel_y))

        title = self.font.render("Bank of Runescape", True, (255, 215, 0))
        surface.blit(title, (panel_x + 20, panel_y + 15))
        
        # Player Inventory section (Left)
        player_title = self.font.render("Your Inventory", True, (200, 200, 200))
        surface.blit(player_title, (panel_x + 20, panel_y + 50))
        self._draw_inventory_slots(surface, self.player.inventory, panel_x + 20, panel_y + 80, slots_per_row=6, highlight_index=self.inventory_index)
        
        # Bank Inventory section (Right)
        bank_title = self.font.render("Bank Vault", True, (200, 200, 200))
        surface.blit(bank_title, (panel_x + 320, panel_y + 50))
        self._draw_inventory_slots(surface, self.player.bank_inventory, panel_x + 320, panel_y + 80, slots_per_row=6, highlight_index=self.bank_index)
        
        hint = self.font.render("[ESC] Close   [T] Deposit All  [LClick] Deposit/Withdraw 1", True, (150, 150, 150))
        surface.blit(hint, (panel_x + 20, panel_y + panel_h - 30))

    def _draw_inventory_panel(self, surface):
        panel_w, panel_h = 320, 400
        panel_x = (surface.get_width() - panel_w) // 2
        panel_y = (surface.get_height() - panel_h) // 2

        # Draw Background Panel
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((30, 30, 30, 240))
        surface.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(surface, (100, 100, 100), (panel_x, panel_y, panel_w, panel_h), 2)

        # Header
        title = self.large_font.render("Inventory", True, (255, 215, 0))
        surface.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 15))
        pygame.draw.line(surface, (70, 70, 70), (panel_x + 20, panel_y + 55), (panel_x + panel_w - 20, panel_y + 55), 2)

        # Inventory Section
        active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0]
        if self.inventory_index >= len(active_items) and len(active_items) > 0:
            self.inventory_index = len(active_items) - 1
            
        self._draw_inventory_slots(surface, self.player.inventory, panel_x + 20, panel_y + 70, slots_per_row=6, highlight_index=self.inventory_index)

        # Show selected item name (Detail section)
        if 0 <= self.inventory_index < len(active_items):
            item_id, count = active_items[self.inventory_index]
            display_name = item_id.replace('_', ' ').title()
            
            # Detail Box
            detail_y = panel_y + 200
            pygame.draw.rect(surface, (20, 20, 20), (panel_x + 20, detail_y, panel_w - 40, 40))
            pygame.draw.rect(surface, (50, 50, 50), (panel_x + 20, detail_y, panel_w - 40, 40), 1)
            
            name_surf = self.font.render(f"{display_name} (x{count})", True, (255, 255, 255))
            surface.blit(name_surf, (panel_x + panel_w // 2 - name_surf.get_width() // 2, detail_y + 10))

        # Gear Section
        gear_y = panel_y + 255
        pygame.draw.line(surface, (70, 70, 70), (panel_x + 20, gear_y), (panel_x + panel_w - 20, gear_y), 2)
        gear_title = self.font.render("Equipped Gear", True, (255, 215, 0))
        surface.blit(gear_title, (panel_x + 20, gear_y + 10))
        
        if self.player.equipped_items:
            self._draw_equipped_slots(surface, self.player.equipped_items, panel_x + 20, gear_y + 40, slots_per_row=6)
        else:
            none_surf = self.font.render("None", True, (100, 100, 100))
            surface.blit(none_surf, (panel_x + 30, gear_y + 40))

        # Footer hints
        hint = self.small_font.render("[I] Close  [Enter/LClick] Use Item  [RClick] Drop", True, (150, 150, 150))
        surface.blit(hint, (panel_x + panel_w // 2 - hint.get_width() // 2, panel_y + panel_h - 25))

    def _draw_inventory_slots(self, surface, inventory, start_x, start_y, slots_per_row=5, highlight_index=None):
        slot_size = 40
        padding = 4
        
        active_items = [(item, count) for item, count in inventory.items.items() if count > 0]
        
        max_y = start_y
        for i, (item, count) in enumerate(active_items):
            row = i // slots_per_row
            col = i % slots_per_row
            
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            max_y = max(max_y, y + slot_size)
            
            # Slot background
            pygame.draw.rect(surface, (40, 40, 40), (x, y, slot_size, slot_size))
            if i == highlight_index:
                pygame.draw.rect(surface, (255, 255, 0), (x, y, slot_size, slot_size), 2)
            else:
                pygame.draw.rect(surface, (80, 80, 80), (x, y, slot_size, slot_size), 1)
            
            # Item icon
            if item in self.item_images:
                img = self.item_images[item]
                rect = img.get_rect(center=(x + slot_size//2, y + slot_size//2))
                surface.blit(img, rect)
            else:
                # Fallback: display letters
                parts = item.split('_')
                if len(parts) > 1:
                    label = (parts[0][0] + parts[1][0]).upper()
                else:
                    label = item[:2].upper()
                text = self.small_font.render(label, True, (180, 180, 180))
                surface.blit(text, (x + 5, y + 5))
            
            # Count
            if count > 1:
                count_surf = self.small_font.render(str(count), True, (255, 255, 255))
                surface.blit(count_surf, (x + slot_size - count_surf.get_width() - 2, 
                                          y + slot_size - count_surf.get_height() - 2))
        return max_y

    def _draw_equipped_slots(self, surface, items, start_x, start_y, slots_per_row=5):
        slot_size = 40
        padding = 4
        
        for i, item in enumerate(items):
            row = i // slots_per_row
            col = i % slots_per_row
            
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            
            # Slot background (gold border for equipped)
            pygame.draw.rect(surface, (50, 45, 20), (x, y, slot_size, slot_size))
            pygame.draw.rect(surface, (218, 165, 32), (x, y, slot_size, slot_size), 1)
            
            # Item icon
            if item in self.item_images:
                img = self.item_images[item]
                rect = img.get_rect(center=(x + slot_size//2, y + slot_size//2))
                surface.blit(img, rect)
            else:
                # Fallback: display letters
                parts = item.split('_')
                if len(parts) > 1:
                    label = (parts[0][0] + parts[1][0]).upper()
                else:
                    label = item[:2].upper()
                text = self.small_font.render(label, True, (218, 165, 32))
                surface.blit(text, (x + 5, y + 5))