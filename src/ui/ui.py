import pygame
import os
from src.systems.recipe_manager import RecipeManager
from src.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT

class UIManager:
    def __init__(self, game_manager):
        self.gm = game_manager
        self.player = game_manager.player
        self.shop = getattr(game_manager, 'shop', None)
        self.recipe_manager = RecipeManager()
        try:
            self.stone_texture = pygame.image.load(os.path.join("assets", "sprites", "ui", "stone_texture.png")).convert()
        except:
            self.stone_texture = None
            
        # Load custom tab icons
        self.tab_icons = {}
        for tab in ["inventory", "skills", "combat", "crafting"]:
            try:
                img = pygame.image.load(os.path.join("assets", "sprites", "ui", f"tab_{tab}.png")).convert_alpha()
                self.tab_icons[tab] = pygame.transform.scale(img, (28, 28))
            except:
                self.tab_icons[tab] = None
        pygame.font.init() # Ensure font module is initialized
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 18)
        self.large_font = pygame.font.SysFont(None, 32)
        
        self.messages = []
        self.active_tab = "inventory" # "inventory", "skills", "combat", "crafting", None
        self.sidebar_rect = pygame.Rect(SCREEN_WIDTH - 300, SCREEN_HEIGHT - 440, 300, 440)
        self.crafting_index = 0
        self.inventory_index = 0
        self.bank_index = 0
        self.active_bank = False
        self.active_shop = False
        self.shop_index = 0
        self.active_station = None
        self.station_index = 0
        self.skills_scroll_y = 0
        
        self.active_dialogue = None

        self.item_images = {}
        self._load_item_sprites()

        # Floating hit splats: list of [text, screen_x, screen_y, spawn_time_ms]
        self.hit_splats = []
        self._splat_duration = 800

        # Floating XP drops: list of [text, screen_x, screen_y, spawn_time_ms]
        self.xp_drops = []
        self._xp_drop_duration = 1000

        # Hotbar — 9 slots: None | item_name | style_name | "toggle_combat"
        self.hotbar_slots = [
            "toggle_combat",  # 1
            "accurate",       # 2
            "aggressive",     # 3
            "defensive",      # 4
            "rapid",          # 5
            "longrange",      # 6
            None, None, None, # 7-9 (assignable)
        ]

        # RS-style right-click context menu
        # {"pos": (x, y), "options": [{"label": str, "action": callable}]}
        self.context_menu = None

        # Death fade animation state
        self.is_fading = False
        self.fade_start_time = 0
        self.fade_duration = 600  # milliseconds


    def _draw_textured_rect(self, surface, rect, border_color=(50, 40, 20), border_width=3):
        if self.stone_texture:
            tw, th = self.stone_texture.get_size()
            for x in range(rect.x, rect.x + rect.w, tw):
                for y in range(rect.y, rect.y + rect.h, th):
                    w = min(tw, rect.x + rect.w - x)
                    h = min(th, rect.y + rect.h - y)
                    surface.blit(self.stone_texture, (x, y), (0, 0, w, h))
        else:
            pygame.draw.rect(surface, (50, 40, 30), rect)
            
        if border_color:
            pygame.draw.rect(surface, border_color, rect, border_width)
            pygame.draw.rect(surface, (20, 15, 10), rect, 1) 
            pygame.draw.rect(surface, (20, 15, 10), (rect.x - 1, rect.y - 1, rect.w + 2, rect.h + 2), 1)

    def _draw_minimap(self, surface):
        mm_radius = 80
        mm_x = surface.get_width() - mm_radius - 20
        mm_y = 20 + mm_radius
        
        mm_surf = pygame.Surface((mm_radius*2, mm_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(mm_surf, (30, 80, 30), (mm_radius, mm_radius), mm_radius) # base color
        
        TILE_PXL = 4
        px, py = self.player.rect.centerx, self.player.rect.centery
        
        def world_to_mm(wx, wy):
            dx = (wx - px) * (TILE_PXL / 32.0)
            dy = (wy - py) * (TILE_PXL / 32.0)
            return (int(mm_radius + dx), int(mm_radius + dy))
            
        for r in getattr(self.gm, 'resource_nodes', []):
            if not getattr(r, 'depleted', False):
                mx, my = world_to_mm(r.rect.centerx, r.rect.centery)
                if (mx-mm_radius)**2 + (my-mm_radius)**2 < mm_radius**2:
                    pygame.draw.circle(mm_surf, (0, 255, 255), (mx, my), 2)
                    
        for item in getattr(self.gm, 'ground_items', []):
           mx, my = world_to_mm(item.rect.centerx, item.rect.centery)
           if (mx-mm_radius)**2 + (my-mm_radius)**2 < mm_radius**2:
               pygame.draw.circle(mm_surf, (255, 50, 50), (mx, my), 1)

        for e in getattr(self.gm, 'enemies', []):
            mx, my = world_to_mm(e.rect.centerx, e.rect.centery)
            if (mx-mm_radius)**2 + (my-mm_radius)**2 < mm_radius**2:
                pygame.draw.circle(mm_surf, (255, 255, 0), (mx, my), 2)
                
        # Draw player
        pygame.draw.circle(mm_surf, (255, 255, 255), (mm_radius, mm_radius), 2)

        # Draw frame
        pygame.draw.circle(surface, (50, 40, 20), (mm_x, mm_y), mm_radius + 4)
        pygame.draw.circle(surface, (20, 15, 10), (mm_x, mm_y), mm_radius + 4, 1)
        pygame.draw.circle(surface, (20, 15, 10), (mm_x, mm_y), mm_radius + 5, 2)
        
        surface.blit(mm_surf, (mm_x - mm_radius, mm_y - mm_radius))
        pygame.draw.circle(surface, (0, 0, 0), (mm_x, mm_y), mm_radius, 1)

    def _draw_shop_inventory(self, surface):
        """Draw the shop UI with buy and sell sections."""
        panel_w, panel_h = 600, 450
        panel_x = (surface.get_width() - panel_w) // 2
        panel_y = (surface.get_height() - panel_h) // 2

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((40, 30, 20, 230))
        surface.blit(panel, (panel_x, panel_y))

        title = self.font.render("General Store", True, (255, 215, 0))
        surface.blit(title, (panel_x + 20, panel_y + 15))
        
        # BUY section (Left) - items shop is selling
        coins = self.player.inventory.get_item_count("coins")
        buy_title = self.font.render(f"Buy (You have {coins} coins)", True, (200, 200, 200))
        surface.blit(buy_title, (panel_x + 20, panel_y + 50))
        self._draw_shop_buy_slots(surface, panel_x + 20, panel_y + 80)
        
        # SELL section (Right) - items player can sell to shop  
        sell_title = self.font.render("Sell", True, (200, 200, 200))
        surface.blit(sell_title, (panel_x + 320, panel_y + 50))
        self._draw_inventory_slots(surface, self.player.inventory, panel_x + 320, panel_y + 80, slots_per_row=6, highlight_index=None)
        
        hint = self.font.render("[ESC] Close  [LClick] Buy/Sell 1", True, (150, 150, 150))
        surface.blit(hint, (panel_x + 20, panel_y + panel_h - 30))

    def _draw_shop_buy_slots(self, surface, start_x, start_y):
        """Draw the shop's items for sale with prices."""
        slot_size = 40
        padding = 4
        slots_per_row = 6
        
        if not self.shop:
            font_small = pygame.font.SysFont(None, 20)
            text = font_small.render("(Shop not available)", True, (150, 150, 150))
            surface.blit(text, (start_x, start_y))
            return
        
        # Draw shop's items for sale with prices
        shop_items = [(item, count) for item, count in self.shop.inventory.items.items() if count > 0]
        
        for i, (item_name, count) in enumerate(shop_items):
            row = i // slots_per_row
            col = i % slots_per_row
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            
            # Draw slot background
            pygame.draw.rect(surface, (60, 50, 40), (x, y, slot_size, slot_size))
            pygame.draw.rect(surface, (100, 80, 60), (x, y, slot_size, slot_size), 1)
            
            # Draw item icon
            if item_name in self.item_images:
                surface.blit(self.item_images[item_name], (x, y))
            else:
                # Fallback to 2-letter abbreviation
                abbrev = item_name[:2].upper()
                abbrev_surf = self.small_font.render(abbrev, True, (200, 200, 200))
                surface.blit(abbrev_surf, (x + 12, y + 12))
            
            # Draw count
            count_surf = self.small_font.render(str(count), True, (255, 215, 0))
            surface.blit(count_surf, (x + slot_size - 14, y + slot_size - 14))
            
            # Draw price label below item
            price = self.shop.get_buy_price(item_name)
            price_surf = self.small_font.render(f"{price}g", True, (255, 200, 100))
            surface.blit(price_surf, (x, y + slot_size + 2))

    def show_context_menu(self, pos, options):
        self.context_menu = {"pos": pos, "options": options}

    def handle_context_menu_click(self, pos):
        """Returns the action callable if an option was clicked, else None."""
        if not self.context_menu:
            return None
        x, y = self._clamped_menu_pos()
        for i, opt in enumerate(self.context_menu["options"]):
            row_rect = pygame.Rect(x, y + 20 + i * 22, 200, 22)
            if row_rect.collidepoint(pos):
                return opt["action"]
        return None

    def _clamped_menu_pos(self):
        if not self.context_menu:
            return (0, 0)
        x, y = self.context_menu["pos"]
        n = len(self.context_menu["options"])
        w, h = 200, 20 + n * 22
        if x + w > SCREEN_WIDTH:
            x = SCREEN_WIDTH - w
        if y + h > SCREEN_HEIGHT:
            y = SCREEN_HEIGHT - h
        return (x, y)

    def _draw_context_menu(self, surface):
        if not self.context_menu:
            return
        x, y = self._clamped_menu_pos()
        n = len(self.context_menu["options"])
        w, row_h = 200, 22
        h = 20 + n * row_h

        bg = pygame.Surface((w, h), pygame.SRCALPHA)
        bg.fill((20, 15, 10, 230))
        surface.blit(bg, (x, y))
        pygame.draw.rect(surface, (120, 90, 40), (x, y, w, h), 1)

        header = self.small_font.render("Choose option", True, (255, 255, 255))
        surface.blit(header, (x + 6, y + 3))

        mx, my = pygame.mouse.get_pos()
        for i, opt in enumerate(self.context_menu["options"]):
            ry = y + 20 + i * row_h
            row_rect = pygame.Rect(x, ry, w, row_h)
            if row_rect.collidepoint(mx, my):
                pygame.draw.rect(surface, (60, 50, 25), row_rect)

            label = opt["label"]
            parts = label.split(" ", 1)
            verb_surf = self.small_font.render(parts[0], True, (255, 215, 0))
            surface.blit(verb_surf, (x + 6, ry + 3))
            if len(parts) > 1:
                target_surf = self.small_font.render(parts[1], True, (210, 210, 190))
                surface.blit(target_surf, (x + 6 + verb_surf.get_width() + 4, ry + 3))

    def _load_item_sprites(self):
        # We'll try to load sprites for any item that might exist in inventory
        item_types = ["wood", "stone", "sword", "iron_ore", "iron_bar", "iron_sword", 
                      "iron_axe", "iron_pickaxe", "chest_item", "bread", "wheat", 
                      "iron_armor", "wheat_seeds", "bronze_axe", "bronze_pickaxe", "bronze_hoe",
                      "coins", "arrows", "raw_fish", "cooked_fish", "rope", "rod", "bronze_sword"]
        
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

    def add_hit_splat(self, damage, world_x, world_y, camera, is_miss=False):
        """Spawn a floating damage number above a hit position.
        is_miss=True shows a blue '0' (RS-style splash)."""
        screen_x = world_x - (camera.camera_rect.x if camera else 0)
        screen_y = world_y - (camera.camera_rect.y if camera else 0)
        color = (100, 160, 255) if is_miss else (255, 50, 50)
        self.hit_splats.append([str(damage), screen_x, screen_y, pygame.time.get_ticks(), color])

    def add_xp_drop(self, skill_name, amount, world_x, world_y, camera):
        """Spawn a floating XP gain label near the player (distinct from hit splats)."""
        screen_x = world_x - (camera.camera_rect.x if camera else 0)
        screen_y = world_y - (camera.camera_rect.y if camera else 0)
        text = f"+{int(amount)} {skill_name.capitalize()}"
        self.xp_drops.append([text, screen_x, screen_y, pygame.time.get_ticks(), (255, 220, 80)])

    def show_message(self, text, color=(255, 255, 0)):
        self.messages.append({"text": text, "time": pygame.time.get_ticks(), "color": color})
        if len(self.messages) > 6:
            self.messages.pop(0)

    def toggle_tab(self, tab_name):
        if self.active_tab == tab_name:
            self.active_tab = None
        else:
            self.active_tab = tab_name

    def reset_skills_scroll(self):
        self.skills_scroll_y = 0

    def scroll_skills(self, wheel_y):
        """Mouse wheel: positive y scrolls content up."""
        self.skills_scroll_y = max(0, self.skills_scroll_y - wheel_y * 24)

    def _skills_panel_content_height(self):
        h = 0
        for _, _, skills in self.player.skills.skills_by_category():
            h += 22
            h += len(skills) * 26
        return h

    def update(self):
        now = pygame.time.get_ticks()
        self.hit_splats = [s for s in self.hit_splats if now - s[3] < self._splat_duration]
        self.xp_drops = [d for d in self.xp_drops if now - d[3] < self._xp_drop_duration]

    def draw(self, surface):
        # Draw Player HP Bar
        hp_bar_width = 200
        hp_bar_height = 20
        hp_y = surface.get_height() - hp_bar_height - 76  # shifted up for hotbar
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
        hints = ["Left-click: Move/Interact", "Right-click: Options menu",
                 "[I] Inventory", "[C] Craft", "[K] Skills",
                 "[Space] Attack nearest", "[Tab] Combat tab",
                 "[M] Toggle mode", "[1-9] Hotbar",
                 "[F5] Save", "[F9] Load"]
        hint_x = surface.get_width() - 140
        hint_y = surface.get_height() - len(hints) * 18 - 64  # above hotbar
        for i, hint in enumerate(hints):
            hint_surf = self.font.render(hint, True, (110, 110, 110))
            surface.blit(hint_surf, (hint_x, hint_y + i * 18))

        # Draw floating hit splats
        now = pygame.time.get_ticks()
        for splat in self.hit_splats:
            text, sx, sy, spawn = splat[0], splat[1], splat[2], splat[3]
            color = splat[4] if len(splat) > 4 else (255, 50, 50)
            age = now - spawn
            progress = age / self._splat_duration
            offset_y = int(progress * 30)  # float upward 30px over lifetime
            alpha = max(0, int(255 * (1.0 - progress)))
            splat_surf = self.font.render(text, True, color)
            splat_surf.set_alpha(alpha)
            surface.blit(splat_surf, (int(sx) - splat_surf.get_width() // 2, int(sy) - 20 - offset_y))

        # Draw floating XP drops (gold, slower rise than hit splats)
        for drop in self.xp_drops:
            text, sx, sy, spawn, color = drop
            age = now - spawn
            progress = age / self._xp_drop_duration
            offset_y = int(progress * 22)
            alpha = max(0, int(255 * (1.0 - progress)))

            shadow = self.small_font.render(text, True, (20, 20, 20))
            shadow.set_alpha(alpha)
            x = int(sx) - shadow.get_width() // 2
            y = int(sy) - 32 - offset_y
            surface.blit(shadow, (x + 1, y + 1))

            drop_surf = self.small_font.render(text, True, color)
            drop_surf.set_alpha(alpha)
            surface.blit(drop_surf, (x, y))

        # Draw overlays
        if self.active_bank:
            self._draw_bank_inventory(surface)
        if self.active_shop:
            self._draw_shop_inventory(surface)
        if getattr(self, 'active_station', None):
            self._draw_station_menu(surface)
        if getattr(self, 'active_dialogue', None):
            self._draw_dialogue(surface)

        self._draw_hotbar(surface)

        # Draw Sidebar
        self._draw_sidebar(surface)

        # Context menu draws on top of everything
        self._draw_context_menu(surface)

        # Draw Chatbox Messages
        chat_x, chat_y = 10, surface.get_height() - 150
        self._draw_textured_rect(surface, pygame.Rect(chat_x, chat_y, 450, 140))
        
        # Minimap
        self._draw_minimap(surface)
        
        y_offset = chat_y + 10
        now = pygame.time.get_ticks()
        # Keep messages for 10 seconds in chatbox
        valid_msgs = [m for m in self.messages if now - m["time"] < 10000]
        for m in valid_msgs[-6:]:
            msg_surf = self.small_font.render(m["text"], True, m["color"])
            surface.blit(msg_surf, (chat_x + 10, y_offset))
            y_offset += 20


    def _draw_sidebar(self, surface):
        panel_w, panel_h = 300, 440
        panel_x = surface.get_width() - panel_w
        panel_y = surface.get_height() - panel_h

        # Background
        self._draw_textured_rect(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h))

        # Tabs (OSRS protruded style)
        tabs = [("combat", "Cbt"), ("skills", "Skl"), ("inventory", "Inv"), ("crafting", "Crf")]
        tab_w = 40
        tab_h = 34
        spacing = (panel_w - (len(tabs) * tab_w)) // (len(tabs) + 1)
        
        # We draw tabs sticking OUT of the top panel_y boundary, so panel_y is the top of the content.
        for i, (tab_id, label) in enumerate(tabs):
            tx = panel_x + spacing + i * (tab_w + spacing)
            ty = panel_y - tab_h + 2  # slight overlap
            
            # Draw tab protrusion (redder stone for unselected, brighter for selected)
            bg_color = (80, 60, 40) if self.active_tab == tab_id else (50, 35, 20)
            tab_rect = pygame.Rect(tx, ty, tab_w, tab_h)
            
            pygame.draw.rect(surface, bg_color, tab_rect, border_top_left_radius=6, border_top_right_radius=6)
            pygame.draw.rect(surface, (20, 15, 10), tab_rect, 2, border_top_left_radius=6, border_top_right_radius=6)
            
            if self.active_tab == tab_id:
                # remove bottom border line connecting to main panel
                pygame.draw.line(surface, bg_color, (tx+2, panel_y+1), (tx+tab_w-3, panel_y+1), 3)

            icon = getattr(self, 'tab_icons', {}).get(tab_id)
            if icon:
                ix = tx + (tab_w - icon.get_width()) // 2
                iy = ty + (tab_h - icon.get_height()) // 2
                surface.blit(icon, (ix, iy))
            else:
                text_color = (255, 215, 0) if self.active_tab == tab_id else (180, 180, 180)
                lbl_surf = self.small_font.render(label, True, text_color)
                surface.blit(lbl_surf, (tx + tab_w//2 - lbl_surf.get_width()//2, ty + 8))

        # Content rect
        crect = pygame.Rect(panel_x, panel_y + tab_h, panel_w, panel_h - tab_h)

        if self.active_tab == "inventory":
            self._draw_inventory_panel(surface, crect)
        elif self.active_tab == "skills":
            self._draw_skills_panel(surface, crect)
        elif self.active_tab == "crafting":
            self._draw_crafting_menu(surface, crect)
        elif self.active_tab == "combat":
            self._draw_combat_tab(surface, crect)

    def get_inventory_slot_rects(self):
        rects = []
        panel_w, panel_h = 300, 440
        panel_x = SCREEN_WIDTH - panel_w
        panel_y = SCREEN_HEIGHT - panel_h + 30
        start_x = panel_x + 10
        start_y = panel_y + 40
        slots_per_row = 6
        slot_size = 40
        padding = 4
        
        active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0 and item != "coins"]
        
        for i in range(len(active_items)):
            row = i // slots_per_row
            col = i % slots_per_row
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            rects.append(pygame.Rect(x, y, slot_size, slot_size))
        return rects

    def get_shop_buy_slot_rects(self):
        rects = []
        if not self.shop:
            return rects
        panel_w, panel_h = 600, 450
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        start_x = panel_x + 20
        start_y = panel_y + 80
        slots_per_row = 6
        slot_size = 40
        padding = 4

        shop_items = [(item, count) for item, count in self.shop.inventory.items.items() if count > 0]
        for i in range(len(shop_items)):
            row = i // slots_per_row
            col = i % slots_per_row
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            rects.append(pygame.Rect(x, y, slot_size, slot_size))
        return rects

    def get_shop_sell_slot_rects(self):
        rects = []
        panel_w, panel_h = 600, 450
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        start_x = panel_x + 320
        start_y = panel_y + 80
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

    def get_equipped_slot_rects(self):
        rects = []
        panel_w, panel_h = 300, 440
        panel_x = SCREEN_WIDTH - panel_w
        panel_y = SCREEN_HEIGHT - panel_h + 30
        gear_y = panel_y + 230
        start_x = panel_x + 10
        start_y = gear_y + 30
        slots_per_row = 6
        slot_size = 40
        padding = 4

        for i in range(len(self.player.equipped_items)):
            row = i // slots_per_row
            col = i % slots_per_row
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            rects.append(pygame.Rect(x, y, slot_size, slot_size))
        return rects

    def get_crafting_recipe_rects(self):
        rects = []
        panel_w, panel_h = 300, 440
        panel_x = SCREEN_WIDTH - panel_w
        panel_y = SCREEN_HEIGHT - panel_h + 30
        list_top = panel_y + 40
        
        for i, recipe in enumerate(self.recipe_manager.get_all()):
            row_y = list_top + i * 22
            if row_y > panel_y + panel_h - 86:
                break
            rects.append(pygame.Rect(panel_x + 4, row_y - 2, panel_w - 8, 20))
        return rects

    def handle_mouse_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            panel_w, panel_h = 300, 440
            panel_x = SCREEN_WIDTH - panel_w
            panel_y = SCREEN_HEIGHT - panel_h
            # Check protruded tabs
            tab_w = 40
            spacing = (panel_w - (4 * tab_w)) // 5
            for i, tab in enumerate(["combat", "skills", "inventory", "crafting"]):
                tx = panel_x + spacing + i * (tab_w + spacing)
                ty = panel_y - 34 + 2
                if tx <= event.pos[0] <= tx + tab_w and ty <= event.pos[1] <= ty + 34:
                    self.toggle_tab(tab)
                    return "tab_clicked", -1

        if getattr(self, 'active_dialogue', None):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return "next_dialogue", -1
            return None, None

        if not (self.active_tab or getattr(self, 'active_bank', False) or getattr(self, 'active_shop', False)):
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
            elif self.active_shop:
                buy_rects = self.get_shop_buy_slot_rects()
                for i, rect in enumerate(buy_rects):
                    if rect.collidepoint(event.pos):
                        self.shop_index = i
                        return None, None
                sell_rects = self.get_shop_sell_slot_rects()
                for i, rect in enumerate(sell_rects):
                    if rect.collidepoint(event.pos):
                        self.inventory_index = i
                        return None, None
            elif self.active_tab == 'inventory':
                rects = self.get_inventory_slot_rects()
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        self.inventory_index = i
                        break
            elif self.active_tab == 'crafting':
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
                elif self.active_shop:
                    buy_rects = self.get_shop_buy_slot_rects()
                    for i, rect in enumerate(buy_rects):
                        if rect.collidepoint(event.pos):
                            return "shop_buy_item", i
                    sell_rects = self.get_shop_sell_slot_rects()
                    for i, rect in enumerate(sell_rects):
                        if rect.collidepoint(event.pos):
                            return "shop_sell_item", i
                elif self.active_tab == 'inventory':
                    rects = self.get_inventory_slot_rects()
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            self.inventory_index = i
                            return "use_item", i
                elif self.active_tab == 'crafting':
                    rects = self.get_crafting_recipe_rects()
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            self.crafting_index = i
                            return "craft_item", i
            elif event.button == 3: # Right click — context menu handled in game_manager
                return "right_click_inventory", -1
        return None, None

    def _draw_station_menu(self, surface):
        panel_w, panel_h = 400, 300
        panel_x = (surface.get_width() - panel_w) // 2
        panel_y = (surface.get_height() - panel_h) // 2



        # Header
        title = self.font.render(f"{self.active_station.name} Menu", True, (255, 215, 0))
        surface.blit(title, (panel_x + 10, panel_y + 8))
        controls = self.font.render("[ESC] Close  [↑↓] Select  [Enter] Process", True, (140, 140, 140))
        surface.blit(controls, (panel_x + 10, panel_y + 28))
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + 48), (panel_x + panel_w, panel_y + 48))

        recipes = self.recipe_manager.get_for_station(self.active_station.station_type)

        # Recipe list
        list_top = panel_y + 40
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

    def _draw_crafting_menu(self, surface, crect=None):
        if crect:
            panel_x, panel_y, panel_w, panel_h = crect.x, crect.y, crect.w, crect.h
        else:
            panel_w, panel_h = 400, 300
            panel_x = (surface.get_width() - panel_w) // 2
            panel_y = (surface.get_height() - panel_h) // 2



        # Header
        title = self.font.render("Hand Crafting", True, (255, 215, 0))
        surface.blit(title, (panel_x + 10, panel_y + 8))
        controls = self.font.render("[ESC] Close  [↑↓] Select  [Enter] Craft", True, (140, 140, 140))
        surface.blit(controls, (panel_x + 10, panel_y + 28))
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + 48), (panel_x + panel_w, panel_y + 48))

        # Filter out station recipes
        recipes = self.recipe_manager.get_handcrafted()

        # Recipe list
        list_top = panel_y + 40
        for i, recipe in enumerate(recipes):
            row_y = list_top + i * 22
            if row_y > panel_y + panel_h - 86:
                break
            skill_name = recipe.get("skill", "crafting")
            skill_level = getattr(self.player.skills, skill_name, self.player.skills.crafting).level
            can_level = skill_level >= recipe["min_level"]
            can_items = all(self.player.inventory.items.get(k, 0) >= v for k, v in recipe["inputs"].items())

            if i == self.crafting_index:
                pygame.draw.rect(surface, (60, 55, 15), (panel_x + 4, row_y - 2, panel_w - 8, 20))

            name_color = (220, 220, 220) if can_level else (90, 90, 90)
            if not can_level:
                status = f"✗ {skill_name.capitalize()} Lv.{recipe['min_level']}"
            elif not can_items:
                status = "✗ items"
            else:
                status = "✓"
            status_color = (80, 200, 80) if (can_level and can_items) else (200, 80, 80)

            label = f"{'>' if i == self.crafting_index else ' '} {recipe['label']}"
            surface.blit(self.font.render(label, True, name_color), (panel_x + 8, row_y))
            status_surf = self.font.render(status, True, status_color)
            surface.blit(status_surf, (panel_x + panel_w - status_surf.get_width() - 10, row_y))

        # Detail section
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + panel_h - 76), (panel_x + panel_w, panel_y + panel_h - 76))
        if 0 <= self.crafting_index < len(recipes):
            r = recipes[self.crafting_index]
            r_skill = r.get("skill", "crafting").capitalize()
            inputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["inputs"].items())
            outputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["outputs"].items())
            surface.blit(self.font.render(f"In:  {inputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 70))
            surface.blit(self.font.render(f"Out: {outputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 48))
            surface.blit(self.font.render(f"XP:  +{r['xp']} {r_skill}", True, (160, 210, 160)), (panel_x + 10, panel_y + panel_h - 26))

    def _draw_skills_panel(self, surface, crect=None):
        if crect:
            panel_x, panel_y, panel_w, panel_h = crect.x, crect.y, crect.w, crect.h
        else:
            panel_w = 320
            panel_h = min(440, surface.get_height() - 20)
            panel_x = surface.get_width() - panel_w - 10
            panel_y = 10



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
                if y + 26 > content_top and y < content_top + clip_h:
                    text_surf = self.small_font.render(label, True, (220, 220, 220))
                    surface.blit(text_surf, (panel_x + 10, y))
                    # XP progress bar
                    bar_w = 100
                    thresh = skill.xp_threshold()
                    fill_w = int(bar_w * (skill.xp / thresh)) if thresh > 0 else 0
                    pygame.draw.rect(surface, (60, 50, 20), (panel_x + 10, y + 14, bar_w, 4))
                    if fill_w > 0:
                        pygame.draw.rect(surface, (200, 160, 40), (panel_x + 10, y + 14, fill_w, 4))
                y += 26

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

    def _draw_inventory_panel(self, surface, crect=None):
        if crect:
            panel_x, panel_y, panel_w, panel_h = crect.x, crect.y, crect.w, crect.h
        else:
            panel_w, panel_h = 320, 400
            panel_x = (surface.get_width() - panel_w) // 2
            panel_y = (surface.get_height() - panel_h) // 2



        # Header
        title = self.font.render("Inventory", True, (255, 215, 0))
        surface.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 15))
        pygame.draw.line(surface, (70, 70, 70), (panel_x + 10, panel_y + 30), (panel_x + panel_w - 10, panel_y + 30), 2)

        # Inventory Section
        active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0 and item != "coins"]
        if self.inventory_index >= len(active_items) and len(active_items) > 0:
            self.inventory_index = len(active_items) - 1
            
        self._draw_inventory_slots(surface, self.player.inventory, panel_x + 10, panel_y + 40, slots_per_row=5, highlight_index=self.inventory_index, hide_coins=True)

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
        gear_y = panel_y + 230
        pygame.draw.line(surface, (70, 70, 70), (panel_x + 20, gear_y), (panel_x + panel_w - 20, gear_y), 2)
        gear_title = self.font.render("Equipped Gear", True, (255, 215, 0))
        surface.blit(gear_title, (panel_x + 20, gear_y + 10))
        
        if self.player.equipped_items:
            self._draw_equipped_slots(surface, self.player.equipped_items, panel_x + 10, gear_y + 30, slots_per_row=5)
        else:
            none_surf = self.font.render("None", True, (100, 100, 100))
            surface.blit(none_surf, (panel_x + 30, gear_y + 40))

        # Coin Box
        coins = self.player.inventory.get_item_count("coins")
        coin_y = panel_y + panel_h - 45
        pygame.draw.line(surface, (70, 70, 70), (panel_x + 10, coin_y - 5), (panel_x + panel_w - 10, coin_y - 5), 2)
        coin_surf = self.font.render(f"Coins: {coins:,}", True, (255, 215, 0))
        surface.blit(coin_surf, (panel_x + panel_w // 2 - coin_surf.get_width() // 2, coin_y - 2))

        # Footer hints
        hint = self.small_font.render("[I] Close  [Enter/LClick] Use Item  [RClick] Drop/Remove", True, (150, 150, 150))
        surface.blit(hint, (panel_x + panel_w // 2 - hint.get_width() // 2, panel_y + panel_h - 20))

    def _draw_inventory_slots(self, surface, inventory, start_x, start_y, slots_per_row=5, highlight_index=None, hide_coins=False):
        slot_size = 40
        padding = 4
        
        active_items = [(item, count) for item, count in inventory.items.items() if count > 0]
        if hide_coins:
            active_items = [(item, count) for item, count in active_items if item != "coins"]
        
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

    def _draw_hotbar_icon(self, surface, slot_val, cx, cy, color):
        """Draw a small icon for a hotbar slot centered at (cx, cy)."""
        if slot_val == "toggle_combat":
            # Sword (melee) or bow (ranged) depending on current mode
            if self.player.combat_mode == "ranged":
                # Bow: arc left side + bowstring
                pygame.draw.arc(surface, color,
                                (cx - 10, cy - 12, 14, 24), -1.2, 1.2, 2)
                pygame.draw.line(surface, color, (cx + 2, cy - 11), (cx + 2, cy + 11), 1)
                # Arrow nocked
                pygame.draw.line(surface, (200, 200, 160), (cx - 6, cy), (cx + 10, cy), 1)
                pygame.draw.polygon(surface, (200, 200, 160),
                                    [(cx + 10, cy), (cx + 6, cy - 3), (cx + 6, cy + 3)])
            else:
                # Sword: blade + crossguard + grip
                pygame.draw.line(surface, color, (cx, cy + 13), (cx, cy - 13), 3)  # blade
                pygame.draw.line(surface, color, (cx - 7, cy + 2), (cx + 7, cy + 2), 2)  # guard
                pygame.draw.line(surface, (150, 120, 80), (cx, cy + 3), (cx, cy + 10), 3)  # grip

        elif slot_val == "accurate":
            # Crosshair / target
            pygame.draw.circle(surface, color, (cx, cy), 9, 2)
            pygame.draw.circle(surface, color, (cx, cy), 3, 1)
            pygame.draw.line(surface, color, (cx - 13, cy), (cx - 5, cy), 1)
            pygame.draw.line(surface, color, (cx + 5, cy), (cx + 13, cy), 1)
            pygame.draw.line(surface, color, (cx, cy - 13), (cx, cy - 5), 1)
            pygame.draw.line(surface, color, (cx, cy + 5), (cx, cy + 13), 1)

        elif slot_val == "aggressive":
            # Upward sword thrust (power strike feel)
            pygame.draw.line(surface, color, (cx, cy + 13), (cx, cy - 10), 3)   # blade
            pygame.draw.polygon(surface, color,
                                [(cx, cy - 14), (cx - 4, cy - 7), (cx + 4, cy - 7)])  # tip
            pygame.draw.line(surface, color, (cx - 7, cy + 3), (cx + 7, cy + 3), 2)  # guard
            pygame.draw.line(surface, (150, 120, 80), (cx, cy + 4), (cx, cy + 11), 3)  # grip

        elif slot_val == "defensive":
            # Shield shape
            pts = [
                (cx,      cy - 13),
                (cx + 10, cy - 8),
                (cx + 10, cy + 2),
                (cx,      cy + 13),
                (cx - 10, cy + 2),
                (cx - 10, cy - 8),
            ]
            pygame.draw.polygon(surface, color, pts, 2)
            # Boss (center circle)
            pygame.draw.circle(surface, color, (cx, cy), 4, 1)

        elif slot_val == "rapid":
            # Three arrows pointing right (fast volleys)
            for dy in (-5, 0, 5):
                sx, sy = cx - 10, cy + dy
                pygame.draw.line(surface, color, (sx, sy), (sx + 14, sy), 1)
                pygame.draw.polygon(surface, color,
                                    [(sx + 14, sy), (sx + 10, sy - 3), (sx + 10, sy + 3)])

        elif slot_val == "longrange":
            # Bow with long arrow
            pygame.draw.arc(surface, color,
                            (cx - 11, cy - 12, 14, 24), -1.2, 1.2, 2)
            pygame.draw.line(surface, color, (cx + 2, cy - 11), (cx + 2, cy + 11), 1)
            # Long arrow
            pygame.draw.line(surface, (200, 200, 160), (cx - 8, cy), (cx + 14, cy), 1)
            pygame.draw.polygon(surface, (200, 200, 160),
                                [(cx + 14, cy), (cx + 10, cy - 3), (cx + 10, cy + 3)])
            # Fletching
            pygame.draw.line(surface, (200, 180, 100), (cx - 6, cy), (cx - 9, cy - 3), 1)
            pygame.draw.line(surface, (200, 180, 100), (cx - 6, cy), (cx - 9, cy + 3), 1)

    def _draw_hotbar(self, surface):
        SLOT = 48
        PAD  = 4
        N    = 9
        total_w = N * SLOT + (N - 1) * PAD
        hx = (surface.get_width()  - total_w) // 2
        hy = surface.get_height() - SLOT - 8

        STYLE_COLORS = {
            "accurate":      (80,  180, 255),
            "aggressive":    (255, 100,  80),
            "defensive":     (80,  220, 120),
            "rapid":         (200, 160,  80),
            "longrange":     (160,  80, 220),
            "toggle_combat": (255, 215,   0),
        }

        for i in range(N):
            x = hx + i * (SLOT + PAD)
            slot_val = self.hotbar_slots[i]

            # Highlight currently-active style slot
            is_active = (slot_val == self.player.combat_style or slot_val == "toggle_combat")
            bg_color  = (55, 45, 20) if is_active else (30, 30, 30)
            pygame.draw.rect(surface, bg_color,    (x, hy, SLOT, SLOT))
            pygame.draw.rect(surface, (90, 80, 50), (x, hy, SLOT, SLOT), 1)

            # Slot number top-left
            num_surf = self.small_font.render(str(i + 1), True, (130, 130, 130))
            surface.blit(num_surf, (x + 2, hy + 2))

            if slot_val is None:
                continue

            cx = x + SLOT // 2
            cy = hy + SLOT // 2

            if slot_val in STYLE_COLORS:
                color = STYLE_COLORS[slot_val]
                self._draw_hotbar_icon(surface, slot_val, cx, cy, color)
            else:
                # Item slot — sprite or abbreviation fallback
                if slot_val in self.item_images:
                    img_scaled = pygame.transform.scale(self.item_images[slot_val], (32, 32))
                    surface.blit(img_scaled, (x + 8, hy + 8))
                    count = self.player.inventory.items.get(slot_val, 0)
                    if count > 0:
                        c_surf = self.small_font.render(str(count), True, (255, 255, 255))
                        surface.blit(c_surf, (x + SLOT - c_surf.get_width() - 2,
                                              hy + SLOT - c_surf.get_height() - 2))
                else:
                    parts = slot_val.split("_")
                    label = (parts[0][0] + parts[1][0]).upper() if len(parts) > 1 else slot_val[:2].upper()
                    text_surf = self.font.render(label, True, (200, 200, 200))
                    surface.blit(text_surf, (cx - text_surf.get_width() // 2,
                                             cy - text_surf.get_height() // 2))

    def _draw_combat_tab(self, surface, crect=None):
        """RS-style combat style selector panel shown above the hotbar."""
        if crect:
            panel_x, panel_y, panel_w, panel_h = crect.x, crect.y, crect.w, crect.h
        else:
            SLOT = 48
            N    = 9
            PAD  = 4
            total_w = N * SLOT + (N - 1) * PAD
            panel_w = 240
            panel_h = 140
            panel_x = (surface.get_width() - panel_w) // 2
            panel_y = surface.get_height() - SLOT - 8 - panel_h - 4


        pygame.draw.rect(surface, (80, 70, 40), (panel_x, panel_y, panel_w, panel_h), 1)

        mode = self.player.combat_mode
        title = self.font.render(f"Combat: {mode.capitalize()}  [Tab]", True, (255, 215, 0))
        surface.blit(title, (panel_x + 8, panel_y + 6))

        toggle_surf = self.small_font.render("[M] Switch Mode", True, (150, 150, 150))
        surface.blit(toggle_surf, (panel_x + 8, panel_y + 26))

        melee_styles  = [("accurate",   "Accurate   (+ATK xp)"),
                         ("aggressive", "Aggressive (+STR xp)"),
                         ("defensive",  "Defensive  (+DEF xp)")]
        ranged_styles = [("accurate",   "Accurate   (+RNG xp)"),
                         ("rapid",      "Rapid      (+RNG xp)"),
                         ("longrange",  "Longrange  (+RNG+DEF)")]

        styles  = melee_styles if mode == "melee" else ranged_styles
        current = self.player.combat_style

        for i, (sid, label) in enumerate(styles):
            btn_y     = panel_y + 48 + i * 26
            is_active = (sid == current)
            bg        = (60, 55, 15) if is_active else (35, 35, 35)
            pygame.draw.rect(surface, bg, (panel_x + 8, btn_y, panel_w - 16, 22))
            color     = (255, 220, 80) if is_active else (180, 180, 180)
            prefix    = "* " if is_active else "  "
            btn_surf  = self.small_font.render(prefix + label, True, color)
            surface.blit(btn_surf, (panel_x + 12, btn_y + 3))

    def show_dialogue(self, npc_name, lines):
        self.active_dialogue = {"npc": npc_name, "lines": lines, "line_index": 0}

    def close_dialogue(self):
        self.active_dialogue = None

    def _draw_dialogue(self, surface):
        width = 400
        height = 120
        x = (surface.get_width() - width) // 2
        y = surface.get_height() - height - 100
        rect = pygame.Rect(x, y, width, height)
        self._draw_textured_rect(surface, rect)
        
        npc = self.active_dialogue["npc"]
        line = self.active_dialogue["lines"][self.active_dialogue["line_index"]]
        
        npc_surf = self.font.render(npc, True, (255, 215, 0))
        surface.blit(npc_surf, (x + width // 2 - npc_surf.get_width() // 2, y + 15))
        
        line_surf = self.font.render(line, True, (220, 220, 220))
        surface.blit(line_surf, (x + 20, y + 50))
        
        cont_surf = self.small_font.render("Click or press Space to continue", True, (150, 150, 150))
        surface.blit(cont_surf, (x + width // 2 - cont_surf.get_width() // 2, y + height - 25))