import pygame
import os
from src.systems.recipe_manager import RecipeManager
from src.systems.dialogue_manager import DialogueManager
from src.core.settings import SCREEN_WIDTH, SCREEN_HEIGHT, ITEM_TOOLTIPS

INV_COLS = 4
INV_ROWS = 7
INV_NUM_SLOTS = INV_COLS * INV_ROWS
INV_SLOT_SIZE = 32
INV_SLOT_PAD = 3

class UIManager:
    def __init__(self, game_manager):
        self.gm = game_manager
        self.player = game_manager.player
        self.shop = getattr(game_manager, 'shop', None)
        self.recipe_manager = RecipeManager()
        self.dialogue_manager = DialogueManager()
        try:
            self.stone_texture = pygame.image.load(os.path.join("assets", "sprites", "ui", "stone_texture.png")).convert()
        except:
            self.stone_texture = None
            
        try:
            self.hit_red = pygame.image.load(os.path.join("assets", "sprites", "ui", "hit_splat_red.png")).convert_alpha()
            self.hit_red = pygame.transform.scale(self.hit_red, (24, 24))
            self.hit_blue = pygame.image.load(os.path.join("assets", "sprites", "ui", "hit_splat_blue.png")).convert_alpha()
            self.hit_blue = pygame.transform.scale(self.hit_blue, (24, 24))
        except:
            self.hit_red = None
            self.hit_blue = None
            
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
        self.inventory_sort_mode = "name"
        self.inv_hover_slot = -1
        self.inv_drag_from = None
        self.inv_press_slot = None
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
                    
        for item in getattr(self.gm, 'resources', []):
            if hasattr(item, 'resource_type'):
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

        self._draw_textured_rect(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h))

        title = self.font.render("General Store", True, (255, 215, 0))
        surface.blit(title, (panel_x + 20, panel_y + 15))
        
        coins = self.player.inventory.get_item_count("coins")
        buy_title = self.font.render(f"Buy (You have {coins} coins)", True, (200, 200, 200))
        surface.blit(buy_title, (panel_x + 20, panel_y + 50))
        if self.shop:
            bx, by = panel_x + 30, panel_y + 80
            self._draw_osrs_slot_grid(
                surface, self.shop.inventory, bx, by,
                highlight_index=None, hide_coins=False, hover_index=-1, flash_full=False,
            )
            cell = self._inv_cell_step()
            for i in range(INV_NUM_SLOTS):
                pair = self.shop.inventory.get_slot(i)
                if not pair:
                    continue
                item_name, _ = pair
                row, col = i // INV_COLS, i % INV_COLS
                ix = bx + col * cell
                iy = by + row * cell
                price = self.shop.get_buy_price(item_name)
                ps = self.small_font.render(f"{price}g", True, (255, 200, 100))
                surface.blit(ps, (ix, min(iy + INV_SLOT_SIZE + 1, panel_y + panel_h - 40)))
        else:
            t = self.small_font.render("(Shop not available)", True, (150, 150, 150))
            surface.blit(t, (panel_x + 30, panel_y + 80))

        sell_title = self.font.render("Sell", True, (200, 200, 200))
        surface.blit(sell_title, (panel_x + 320, panel_y + 50))
        self._draw_osrs_slot_grid(
            surface,
            self.player.inventory,
            panel_x + 330,
            panel_y + 80,
            highlight_index=None,
            hide_coins=False,
            hover_index=-1,
            flash_full=False,
        )
        
        hint = self.font.render("[ESC] Close  [LClick] Buy/Sell 1", True, (150, 150, 150))
        surface.blit(hint, (panel_x + 20, panel_y + panel_h - 30))

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
        hints = ["Left-click: Move/Interact", "Right-click: Options menu",
                 "[I] Inventory", "[C] Craft", "[K] Skills",
                 "[Space] Attack nearest", "[Tab] Combat tab",
                 "[M] Toggle mode", "[1-9] Hotbar",
                 "[F5] Save", "[F9] Load"]
        hint_x = surface.get_width() - 140
        hint_y = surface.get_height() - len(hints) * 18 - 8
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
            
            # Hit splat background
            bg_splat = self.hit_blue if color == (100, 160, 255) else self.hit_red
            final_y = int(sy) - 20 - offset_y
            final_x = int(sx)
            if bg_splat:
                splat_img = bg_splat.copy()
                splat_img.set_alpha(alpha)
                surface.blit(splat_img, (final_x - splat_img.get_width()//2, final_y - splat_img.get_height()//2))

            splat_surf = self.font.render(text, True, (255, 255, 255) if bg_splat else color)
            splat_surf.set_alpha(alpha)
            
            if bg_splat:
                # Add shadow for the number
                shadow = self.font.render(text, True, (0, 0, 0))
                shadow.set_alpha(alpha)
                surface.blit(shadow, (final_x - shadow.get_width() // 2 + 1, final_y - splat_surf.get_height() // 2 + 1))
                
            surface.blit(splat_surf, (final_x - splat_surf.get_width() // 2, final_y - splat_surf.get_height() // 2))

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


        # Draw Sidebar
        self._draw_sidebar(surface)
        self._draw_inv_tooltip(surface)
        self._draw_inv_drag_ghost(surface)

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
            shadow = self.small_font.render(m["text"], True, (0, 0, 0))
            surface.blit(shadow, (chat_x + 11, y_offset + 1))
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
        tabs = [("combat", "Cbt"), ("skills", "Skl"), ("quests", "Qst"), ("inventory", "Inv"), ("crafting", "Crf")]
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
        elif self.active_tab == "quests":
            self._draw_quests_tab(surface, crect)
        elif self.active_tab == "crafting":
            self._draw_crafting_menu(surface, crect)
        elif self.active_tab == "combat":
            self._draw_combat_tab(surface, crect)

    def _inv_cell_step(self):
        return INV_SLOT_SIZE + INV_SLOT_PAD

    def _sidebar_inv_grid_origin(self):
        panel_w, outer_h = 300, 440
        panel_x = SCREEN_WIDTH - panel_w
        outer_y = SCREEN_HEIGHT - outer_h
        tab_h = 34
        panel_y = outer_y + tab_h
        grid_start_y = panel_y + 58
        cell = self._inv_cell_step()
        grid_w = INV_COLS * cell - INV_SLOT_PAD
        grid_start_x = panel_x + (panel_w - grid_w) // 2
        return grid_start_x, grid_start_y

    def _sidebar_gear_zone(self):
        grid_x, grid_y = self._sidebar_inv_grid_origin()
        cell = self._inv_cell_step()
        grid_h = INV_ROWS * cell - INV_SLOT_PAD
        gear_y = grid_y + grid_h + 10
        panel_w = 300
        panel_x = SCREEN_WIDTH - panel_w
        return panel_x, gear_y

    def get_inventory_sort_button_rects(self):
        panel_w, outer_h = 300, 440
        panel_x = SCREEN_WIDTH - panel_w
        outer_y = SCREEN_HEIGHT - outer_h
        tab_h = 34
        panel_y = outer_y + tab_h
        y = panel_y + 34
        modes = [("name", "Name"), ("type", "Type"), ("quantity", "Qty")]
        rects = []
        bx = panel_x + 8
        for mode, label in modes:
            rects.append((pygame.Rect(bx, y, 56, 18), mode))
            bx += 62
        return rects

    def _draw_osrs_slot_grid(
        self,
        surface,
        inventory,
        start_x,
        start_y,
        highlight_index=None,
        hide_coins=False,
        hover_index=-1,
        flash_full=False,
    ):
        cell = self._inv_cell_step()
        bottom = start_y
        for i in range(INV_NUM_SLOTS):
            row = i // INV_COLS
            col = i % INV_COLS
            x = start_x + col * cell
            y = start_y + row * cell
            bottom = y + INV_SLOT_SIZE
            pair = inventory.get_slot(i)
            item = pair[0] if pair else None
            count = pair[1] if pair else 0
            visual_empty = pair is None or (hide_coins and item == "coins")

            bg = (22, 22, 24) if visual_empty else (38, 38, 42)
            pygame.draw.rect(surface, bg, (x, y, INV_SLOT_SIZE, INV_SLOT_SIZE))
            border_c = (55, 55, 60)
            if flash_full and pair and not (hide_coins and item == "coins"):
                border_c = (180, 60, 60)
            elif i == highlight_index:
                border_c = (255, 220, 80)
            elif i == hover_index:
                border_c = (140, 130, 90)
            pygame.draw.rect(surface, border_c, (x, y, INV_SLOT_SIZE, INV_SLOT_SIZE), 2)

            if not visual_empty and item:
                if item in self.item_images:
                    img = self.item_images[item]
                    rect = img.get_rect(center=(x + INV_SLOT_SIZE // 2, y + INV_SLOT_SIZE // 2))
                    surface.blit(img, rect)
                else:
                    parts = item.split("_")
                    label = (parts[0][0] + parts[1][0]).upper() if len(parts) > 1 else item[:2].upper()
                    text = self.small_font.render(label, True, (180, 180, 180))
                    surface.blit(text, (x + 4, y + 4))
                if count > 1:
                    count_surf = self.small_font.render(str(count), True, (255, 255, 255))
                    surface.blit(
                        count_surf,
                        (x + INV_SLOT_SIZE - count_surf.get_width() - 2, y + INV_SLOT_SIZE - count_surf.get_height() - 2),
                    )
        return bottom

    def get_inventory_slot_rects(self):
        rects = []
        start_x, start_y = self._sidebar_inv_grid_origin()
        cell = self._inv_cell_step()
        for i in range(INV_NUM_SLOTS):
            row = i // INV_COLS
            col = i % INV_COLS
            x = start_x + col * cell
            y = start_y + row * cell
            rects.append(pygame.Rect(x, y, INV_SLOT_SIZE, INV_SLOT_SIZE))
        return rects

    def get_shop_buy_slot_rects(self):
        rects = []
        if not self.shop:
            return rects
        panel_w, panel_h = 600, 450
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        start_x = panel_x + 30
        start_y = panel_y + 80
        cell = self._inv_cell_step()
        for i in range(INV_NUM_SLOTS):
            row = i // INV_COLS
            col = i % INV_COLS
            x = start_x + col * cell
            y = start_y + row * cell
            rects.append(pygame.Rect(x, y, INV_SLOT_SIZE, INV_SLOT_SIZE))
        return rects

    def get_shop_sell_slot_rects(self):
        rects = []
        panel_w, panel_h = 600, 450
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        start_x = panel_x + 330
        start_y = panel_y + 80
        cell = self._inv_cell_step()
        for i in range(INV_NUM_SLOTS):
            row = i // INV_COLS
            col = i % INV_COLS
            x = start_x + col * cell
            y = start_y + row * cell
            rects.append(pygame.Rect(x, y, INV_SLOT_SIZE, INV_SLOT_SIZE))
        return rects

    def get_bank_slot_rects(self, is_player_inv=False):
        rects = []
        panel_w, panel_h = 600, 450
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = (SCREEN_HEIGHT - panel_h) // 2
        start_x = (panel_x + 25) if is_player_inv else (panel_x + 325)
        start_y = panel_y + 80
        cell = self._inv_cell_step()
        for i in range(INV_NUM_SLOTS):
            row = i // INV_COLS
            col = i % INV_COLS
            x = start_x + col * cell
            y = start_y + row * cell
            rects.append(pygame.Rect(x, y, INV_SLOT_SIZE, INV_SLOT_SIZE))
        return rects

    def get_equipped_slot_rects(self):
        rects = []
        panel_x, gear_y = self._sidebar_gear_zone()
        start_x = panel_x + 8
        start_y = gear_y + 22
        slots_per_row = 4
        slot_size = 32
        padding = 3

        for i in range(len(self.player.equipped_items)):
            row = i // slots_per_row
            col = i % slots_per_row
            x = start_x + col * (slot_size + padding)
            y = start_y + row * (slot_size + padding)
            rects.append(pygame.Rect(x, y, slot_size, slot_size))
        return rects

    def get_crafting_recipe_rects(self):
        rects = []
        panel_w, outer_h = 300, 440
        panel_x = SCREEN_WIDTH - panel_w
        outer_y = SCREEN_HEIGHT - outer_h
        tab_h = 34
        panel_y = outer_y + tab_h
        panel_h = outer_h - tab_h
        recipes = self.recipe_manager.get_handcrafted()
        list_top = panel_y + 68
        for i, recipe in enumerate(recipes):
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
            tabs_list = ["combat", "skills", "quests", "inventory", "crafting"]
            spacing = (panel_w - (len(tabs_list) * tab_w)) // (len(tabs_list) + 1)
            for i, tab in enumerate(tabs_list):
                tx = panel_x + spacing + i * (tab_w + spacing)
                ty = panel_y - 34 + 2
                if tx <= event.pos[0] <= tx + tab_w and ty <= event.pos[1] <= ty + 34:
                    self.toggle_tab(tab)
                    return "tab_clicked", -1

        if getattr(self, 'active_dialogue', None):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.active_dialogue.get("type") == "node":
                    node = self.dialogue_manager.get_node(self.active_dialogue["id"])
                    if node:
                        responses = node.get("responses", [])
                        width, height = 400, 160
                        x, y = (SCREEN_WIDTH - width) // 2, SCREEN_HEIGHT - height - 100
                        for i, r in enumerate(responses):
                            rect = pygame.Rect(x + 20, y + 75 + i * 20, width - 40, 20)
                            if rect.collidepoint(event.pos):
                                return "dialogue_response", (self.active_dialogue["id"], i)
                else:
                    return "next_dialogue", -1
            return None, None

        if not (self.active_tab or getattr(self, 'active_bank', False) or getattr(self, 'active_shop', False)):
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.inv_press_slot = None
                self.inv_drag_from = None
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
                self.inv_hover_slot = -1
                rects = self.get_inventory_slot_rects()
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        self.inventory_index = i
                        self.inv_hover_slot = i
                        break
                if self.inv_press_slot is not None and pygame.mouse.get_pressed()[0]:
                    pr = rects[self.inv_press_slot]
                    if not pr.collidepoint(event.pos):
                        self.inv_drag_from = self.inv_press_slot
            elif self.active_tab == 'crafting':
                rects = self.get_crafting_recipe_rects()
                for i, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        self.crafting_index = i
                        break
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.active_tab == 'inventory':
                if self.inv_drag_from is not None:
                    dst = -1
                    for i, r in enumerate(self.get_inventory_slot_rects()):
                        if r.collidepoint(event.pos):
                            dst = i
                            break
                    src = self.inv_drag_from
                    self.inv_drag_from = None
                    self.inv_press_slot = None
                    if dst >= 0:
                        return "inv_drag_drop", (src, dst)
                elif self.inv_press_slot is not None:
                    s = self.inv_press_slot
                    self.inv_press_slot = None
                    rects = self.get_inventory_slot_rects()
                    if 0 <= s < len(rects) and rects[s].collidepoint(event.pos):
                        pair = self.player.inventory.get_slot(s)
                        if pair and pair[0] != "coins":
                            return "use_item", s
            else:
                self.inv_press_slot = None
                self.inv_drag_from = None
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if self.active_tab == 'combat' and self.player.combat_mode == "magic":
                    panel_w, panel_h = 300, 440
                    panel_x = SCREEN_WIDTH - panel_w
                    panel_y = SCREEN_HEIGHT - panel_h + 30 
                    for i, (s_key, spell) in enumerate(self.player.spells.items()):
                        rect = pygame.Rect(panel_x + 8, panel_y + 48 + i * 21, panel_w - 16, 20)
                        if rect.collidepoint(event.pos):
                            self.player.active_spell = s_key
                            self.show_message(f"Auto-cast set to: {spell['name']}")
                            return "spell_selected", i
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
                    for r, mode in self.get_inventory_sort_button_rects():
                        if r.collidepoint(event.pos):
                            self.inventory_sort_mode = mode
                            self.player.inventory.sort_slots(mode)
                            return None, None
                    rects = self.get_inventory_slot_rects()
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            self.inventory_index = i
                            pair = self.player.inventory.get_slot(i)
                            if pair:
                                self.inv_press_slot = i
                            return None, None
                elif self.active_tab == 'crafting':
                    rects = self.get_crafting_recipe_rects()
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            self.crafting_index = i
                            return "craft_item", i
            elif event.button == 2:
                if self.active_tab == 'inventory':
                    for i, rect in enumerate(self.get_inventory_slot_rects()):
                        if rect.collidepoint(event.pos):
                            return "inv_split", i
            elif event.button == 3: # Right click
                if self.active_tab == 'inventory':
                    self.inv_press_slot = None
                    self.inv_drag_from = None
                    slot_rects = self.get_inventory_slot_rects()
                    for i, rect in enumerate(slot_rects):
                        if rect.collidepoint(event.pos):
                            return "right_click_inventory", i

                    equipped_rects = self.get_equipped_slot_rects()
                    for i, rect in enumerate(equipped_rects):
                        if rect.collidepoint(event.pos):
                            return "right_click_equipped", i
                elif self.active_tab == 'crafting':
                    rects = self.get_crafting_recipe_rects()
                    for i, rect in enumerate(rects):
                        if rect.collidepoint(event.pos):
                            self.crafting_index = i
                            return "crafting_context", i
                return None, None
        return None, None

    def _draw_station_menu(self, surface):
        panel_w, panel_h = 400, 300
        panel_x = (surface.get_width() - panel_w) // 2
        panel_y = (surface.get_height() - panel_h) // 2



        # Header
        title = self.font.render(f"{self.active_station.name}", True, (255, 215, 0))
        surface.blit(title, (panel_x + 10, panel_y + 8))
        controls = self.small_font.render(
            "[ESC] Close   [↑↓] Select   [Enter] Make 1   [A] Make All", True, (140, 140, 140)
        )
        surface.blit(controls, (panel_x + 10, panel_y + 28))
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + 48), (panel_x + panel_w, panel_y + 48))

        recipes = self.recipe_manager.get_for_station(self.active_station.station_type)

        # Recipe list
        list_top = panel_y + 40
        for i, recipe in enumerate(recipes):
            row_y = list_top + i * 22
            if row_y > panel_y + panel_h - 86:
                break
            sk = recipe.get("skill", "crafting")
            skill_level = getattr(self.player.skills, sk, self.player.skills.crafting).level
            can_level = skill_level >= recipe["min_level"]
            can_items = all(self.player.inventory.items.get(k, 0) >= v for k, v in recipe["inputs"].items())
            can_make = can_level and can_items

            if i == self.station_index:
                pygame.draw.rect(surface, (60, 55, 15), (panel_x + 4, row_y - 2, panel_w - 8, 20))

            name_color = (220, 220, 220) if can_level else (90, 90, 90)
            if not can_level:
                sk_obj = getattr(self.player.skills, sk, self.player.skills.crafting)
                disp = sk_obj.name if sk_obj else sk.capitalize()
                status = f"✗ {disp} {recipe['min_level']}"
            elif not can_items:
                status = "✗ items"
            else:
                status = "✓"
            status_color = (80, 200, 80) if can_make else (200, 80, 80)

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



        # Header (OSRS-style combined crafting / cooking / fletching list)
        title = self.font.render("Crafting", True, (255, 215, 0))
        surface.blit(title, (panel_x + 10, panel_y + 8))
        controls = self.small_font.render(
            "[ESC] Close   [↑↓] Select   [Enter/Space] Make 1   [Shift+Enter] 5   [Ctrl+Enter] 10   [A] All",
            True,
            (140, 140, 140),
        )
        surface.blit(controls, (panel_x + 10, panel_y + 26))
        hint2 = self.small_font.render(
            "[LClick] Make 1   [RClick] Make menu (1 / 5 / 10 / All)", True, (120, 120, 120)
        )
        surface.blit(hint2, (panel_x + 10, panel_y + 42))
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + 62), (panel_x + panel_w, panel_y + 62))

        # Filter out station recipes
        recipes = self.recipe_manager.get_handcrafted()

        # Recipe list
        list_top = panel_y + 68
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
                sk_disp = getattr(self.player.skills, skill_name, self.player.skills.crafting).name
                status = f"✗ {sk_disp} {recipe['min_level']}"
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
            _sk = r.get("skill", "crafting")
            r_skill = getattr(self.player.skills, _sk, self.player.skills.crafting).name
            inputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["inputs"].items())
            outputs_str = ",  ".join(f"{v}x {k.replace('_', ' ')}" for k, v in r["outputs"].items())
            surface.blit(self.font.render(f"In:  {inputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 70))
            surface.blit(self.font.render(f"Out: {outputs_str}", True, (200, 200, 200)), (panel_x + 10, panel_y + panel_h - 48))
            surface.blit(self.font.render(f"XP:  +{r['xp']} {r_skill}", True, (160, 210, 160)), (panel_x + 10, panel_y + panel_h - 26))

    def _draw_quests_tab(self, surface, crect=None):
        if crect:
            panel_x, panel_y, panel_w, panel_h = crect.x, crect.y, crect.w, crect.h
        else:
            panel_w = 320
            panel_h = min(440, surface.get_height() - 20)
            panel_x = surface.get_width() - panel_w - 10
            panel_y = 10

        title = self.font.render("Quest Journal", True, (255, 215, 0))
        surface.blit(title, (panel_x + 8, panel_y + 6))
        
        qp = getattr(self.player.quest_manager, 'quest_points', 0)
        qp_text = self.small_font.render(f"Quest Points: {qp}", True, (50, 150, 255))
        surface.blit(qp_text, (panel_x + panel_w - qp_text.get_width() - 8, panel_y + 10))
        
        pygame.draw.line(surface, (70, 70, 70), (panel_x, panel_y + 30), (panel_x + panel_w, panel_y + 30))

        y = panel_y + 40
        for qid, qdata in self.player.quest_manager.quests_db.items():
            status = self.player.quest_manager.get_status(qid)
            color = (255, 50, 50) # unstarted
            if status == "active":
                color = (255, 255, 50)
            elif status == "completed":
                color = (50, 255, 50)
            
            qname = qdata.get("name", qid)
            label_surf = self.small_font.render(qname, True, color)
            surface.blit(label_surf, (panel_x + 16, y))
            y += 24

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

        player_title = self.font.render("Your Inventory", True, (200, 200, 200))
        surface.blit(player_title, (panel_x + 20, panel_y + 48))
        gx = panel_x + 25
        gy = panel_y + 72
        self._draw_osrs_slot_grid(
            surface,
            self.player.inventory,
            gx,
            gy,
            highlight_index=self.inventory_index,
            hide_coins=True,
            hover_index=-1,
            flash_full=self.player.inventory.occupied_slots() >= self.player.inventory.MAX_SLOTS,
        )

        bank_title = self.font.render("Bank Vault", True, (200, 200, 200))
        surface.blit(bank_title, (panel_x + 320, panel_y + 48))
        self._draw_osrs_slot_grid(
            surface,
            self.player.bank_inventory,
            panel_x + 325,
            gy,
            highlight_index=self.bank_index,
            hide_coins=False,
            hover_index=-1,
            flash_full=False,
        )

        hint = self.font.render("[ESC] Close   [T] Deposit All  [LClick] Deposit/Withdraw 1", True, (150, 150, 150))
        surface.blit(hint, (panel_x + 20, panel_y + panel_h - 30))

    def _draw_inventory_panel(self, surface, crect=None):
        if crect:
            panel_x, panel_y, panel_w, panel_h = crect.x, crect.y, crect.w, crect.h
        else:
            panel_w, panel_h = 320, 400
            panel_x = (surface.get_width() - panel_w) // 2
            panel_y = (surface.get_height() - panel_h) // 2

        self.inventory_index = max(0, min(self.inventory_index, INV_NUM_SLOTS - 1))

        title = self.font.render("Inventory", True, (255, 215, 0))
        surface.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 4))

        occ = self.player.inventory.occupied_slots()
        cap_color = (255, 100, 80) if occ >= self.player.inventory.MAX_SLOTS else (200, 180, 120)
        cap_surf = self.small_font.render(f"{occ} / {self.player.inventory.MAX_SLOTS} slots", True, cap_color)
        surface.blit(cap_surf, (panel_x + panel_w // 2 - cap_surf.get_width() // 2, panel_y + 22))

        sort_lbl = {"name": "Name", "type": "Type", "quantity": "Qty"}
        for r, mode in self.get_inventory_sort_button_rects():
            active = mode == self.inventory_sort_mode
            bg = (70, 55, 30) if active else (45, 40, 35)
            pygame.draw.rect(surface, bg, r)
            pygame.draw.rect(surface, (120, 100, 60), r, 1)
            ts = self.small_font.render(
                sort_lbl.get(mode, mode), True, (255, 215, 0) if active else (160, 160, 160)
            )
            surface.blit(ts, (r.x + 6, r.y + 2))

        gx, gy = self._sidebar_inv_grid_origin()
        flash_full = occ >= self.player.inventory.MAX_SLOTS
        hi = self.inventory_index if self.inv_drag_from is None else None
        self._draw_osrs_slot_grid(
            surface,
            self.player.inventory,
            gx,
            gy,
            highlight_index=hi,
            hide_coins=True,
            hover_index=self.inv_hover_slot,
            flash_full=flash_full,
        )

        _, gear_y = self._sidebar_gear_zone()
        pygame.draw.line(surface, (70, 70, 70), (panel_x + 12, gear_y - 6), (panel_x + panel_w - 12, gear_y - 6), 1)
        gear_title = self.font.render("Worn", True, (255, 215, 0))
        surface.blit(gear_title, (panel_x + 12, gear_y - 2))

        if self.player.equipped_items:
            self._draw_equipped_slots(surface, self.player.equipped_items, panel_x + 8, gear_y + 18, slots_per_row=4)
        else:
            none_surf = self.small_font.render("Nothing equipped", True, (100, 100, 100))
            surface.blit(none_surf, (panel_x + 16, gear_y + 24))

        coins = self.player.inventory.get_item_count("coins")
        coin_y = panel_y + panel_h - 36
        pygame.draw.line(surface, (70, 70, 70), (panel_x + 10, coin_y - 6), (panel_x + panel_w - 10, coin_y - 6), 1)
        coin_surf = self.small_font.render(f"Coins: {coins:,}", True, (255, 215, 0))
        surface.blit(coin_surf, (panel_x + panel_w // 2 - coin_surf.get_width() // 2, coin_y))

        sel = self.player.inventory.get_slot(self.inventory_index)
        if sel and sel[0] != "coins":
            dn = sel[0].replace("_", " ").title()
            line = self.small_font.render(f"{dn} ×{sel[1]}", True, (220, 220, 220))
            surface.blit(line, (panel_x + panel_w // 2 - line.get_width() // 2, coin_y - 22))

        hint = self.small_font.render(
            "[I] Close  [Click] Use  [Drag] Move  [M3] Split  [RClick] Menu", True, (130, 130, 130)
        )
        surface.blit(hint, (panel_x + panel_w // 2 - hint.get_width() // 2, panel_y + panel_h - 16))

    def _draw_inv_tooltip(self, surface):
        if self.active_tab != "inventory" or self.inv_hover_slot < 0:
            return
        pair = self.player.inventory.get_slot(self.inv_hover_slot)
        if not pair:
            return
        item_id, count = pair
        if item_id == "coins":
            return
        lines = ITEM_TOOLTIPS.get(item_id)
        if not lines:
            dn = item_id.replace("_", " ").title()
            lines = [f"It's a {dn}.", f"You have {count}." if count > 1 else ""]

        mx, my = pygame.mouse.get_pos()
        pad = 6
        name = item_id.replace("_", " ").title()
        header = self.small_font.render(f"{name} ×{count}", True, (255, 215, 0))
        body_surfs = []
        for ln in lines:
            if ln:
                body_surfs.append(self.small_font.render(ln, True, (220, 220, 210)))
        tw = max([header.get_width()] + [b.get_width() for b in body_surfs], default=header.get_width()) + pad * 2
        th = header.get_height() + sum(b.get_height() + 2 for b in body_surfs) + pad * 2
        bx = min(mx + 14, SCREEN_WIDTH - tw - 8)
        by = min(my + 14, SCREEN_HEIGHT - th - 8)
        rect = pygame.Rect(bx, by, tw, th)
        pygame.draw.rect(surface, (25, 22, 18), rect)
        pygame.draw.rect(surface, (90, 75, 45), rect, 2)
        surface.blit(header, (bx + pad, by + pad))
        yy = by + pad + header.get_height() + 4
        for b in body_surfs:
            surface.blit(b, (bx + pad, yy))
            yy += b.get_height() + 2

    def _draw_inv_drag_ghost(self, surface):
        if self.active_tab != "inventory" or self.inv_drag_from is None:
            return
        pair = self.player.inventory.get_slot(self.inv_drag_from)
        if not pair:
            return
        item_id, _c = pair
        mx, my = pygame.mouse.get_pos()
        half = INV_SLOT_SIZE // 2
        if item_id in self.item_images:
            img = self.item_images[item_id]
            r = img.get_rect(center=(mx, my))
            surface.blit(img, r)
        else:
            pygame.draw.rect(surface, (50, 50, 55), (mx - half, my - half, INV_SLOT_SIZE, INV_SLOT_SIZE))
            ab = item_id[:2].upper()
            t = self.small_font.render(ab, True, (180, 180, 180))
            surface.blit(t, (mx - t.get_width() // 2, my - t.get_height() // 2))

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

    def _draw_equipped_slots(self, surface, items, start_x, start_y, slots_per_row=4, slot_size=32, padding=3):
        
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


    def _draw_combat_tab(self, surface, crect=None):
        """RS-style combat style selector panel shown above the hotbar."""
        if crect:
            panel_x, panel_y, panel_w, panel_h = crect.x, crect.y, crect.w, crect.h
        else:
            panel_y = surface.get_height() - panel_h - 10


        pygame.draw.rect(surface, (80, 70, 40), (panel_x, panel_y, panel_w, panel_h), 1)

        mode = self.player.combat_mode
        title = self.font.render(f"Combat: {mode.capitalize()}  [Tab]", True, (255, 215, 0))
        surface.blit(title, (panel_x + 8, panel_y + 6))

        toggle_surf = self.small_font.render("[M] Switch Mode", True, (150, 150, 150))
        surface.blit(toggle_surf, (panel_x + 8, panel_y + 26))

        if mode == "magic":
            for i, (s_key, spell) in enumerate(self.player.spells.items()):
                btn_y     = panel_y + 48 + i * 21
                is_active = (s_key == getattr(self.player, "active_spell", "none"))
                bg        = (60, 55, 15) if is_active else (35, 35, 35)
                # Ensure it fits
                rect = pygame.Rect(panel_x + 8, btn_y, panel_w - 16, 20)
                pygame.draw.rect(surface, bg, rect)
                
                req = spell["req"]
                can_cast = self.player.skills.magic.level >= req
                color     = (255, 220, 80) if is_active and can_cast else ((150,150,150) if can_cast else (180, 50, 50))
                prefix    = "* " if is_active else "  "
                btn_surf  = self.small_font.render(prefix + spell["name"] + f" (Lv.{req})", True, color)
                surface.blit(btn_surf, (panel_x + 12, btn_y + 2))
        else:
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
        self.active_dialogue = {"type": "linear", "npc": npc_name, "lines": lines, "line_index": 0}
        
    def show_dialogue_node(self, node_id):
        node = self.dialogue_manager.get_node(node_id)
        if node:
            self.active_dialogue = {"type": "node", "id": node_id}

    def close_dialogue(self):
        self.active_dialogue = None

    def _draw_dialogue(self, surface):
        if not getattr(self, 'active_dialogue', None): return
        width, height = 400, 160
        x, y = (surface.get_width() - width) // 2, surface.get_height() - height - 100
        self._draw_textured_rect(surface, pygame.Rect(x, y, width, height))
        
        if self.active_dialogue.get("type") == "node":
            node = self.dialogue_manager.get_node(self.active_dialogue["id"])
            if not node: return
            npc_name = node.get("npc", "NPC")
            line = node.get("text", "")
            responses = node.get("responses", [])
            
            npc_surf = self.font.render(npc_name, True, (255, 215, 0))
            surface.blit(npc_surf, (x + width // 2 - npc_surf.get_width() // 2, y + 15))
            line_surf = self.small_font.render(line, True, (220, 220, 220))
            surface.blit(line_surf, (x + 20, y + 45))
            
            for i, r in enumerate(responses):
                ms = pygame.mouse.get_pos()
                btn_color = (200, 200, 100) if pygame.Rect(x+20, y+75+i*20, width-40, 20).collidepoint(ms) else (150, 150, 255)
                rsurf = self.small_font.render(f"{i+1}. {r['text']}", True, btn_color)
                surface.blit(rsurf, (x + 20, y + 75 + i * 20))
        else:
            npc = self.active_dialogue.get("npc", "NPC")
            lines = self.active_dialogue.get("lines", [""])
            idx = self.active_dialogue.get("line_index", 0)
            line = lines[idx] if idx < len(lines) else ""
            npc_surf = self.font.render(npc, True, (255, 215, 0))
            surface.blit(npc_surf, (x + width // 2 - npc_surf.get_width() // 2, y + 15))
            line_surf = self.font.render(line, True, (220, 220, 220))
            surface.blit(line_surf, (x + 20, y + 50))
            cont_surf = self.small_font.render("Click or press Space to continue", True, (150, 150, 150))
            surface.blit(cont_surf, (x + width // 2 - cont_surf.get_width() // 2, y + height - 25))

    def is_pos_on_ui(self, pos):
        """Return True if the screen position overlaps any active UI panel or element."""
        # 1. Sidebar (active tab)
        if self.active_tab:
            # Check the protruded tabs specifically
            panel_w = 300
            panel_x = SCREEN_WIDTH - panel_w
            panel_y = SCREEN_HEIGHT - 440
            
            # Use the actual sidebar panel rect, not just a full vertical strip
            visible_panel_rect = pygame.Rect(panel_x, panel_y, panel_w, 440)
            if visible_panel_rect.collidepoint(pos):
                return True

            tab_w = 40
            tabs_list = ["combat", "skills", "quests", "inventory", "crafting"]
            spacing = (panel_w - (len(tabs_list) * tab_w)) // (len(tabs_list) + 1)
            for i in range(len(tabs_list)):
                tx = panel_x + spacing + i * (tab_w + spacing)
                ty = panel_y - 34 + 2
                if pygame.Rect(tx, ty, tab_w, 34).collidepoint(pos):
                    return True

        # 2. Bank / Shop panels
        if self.active_bank or self.active_shop:
            panel_w, panel_h = 600, 450
            panel_x = (SCREEN_WIDTH - panel_w) // 2
            panel_y = (SCREEN_HEIGHT - panel_h) // 2
            if pygame.Rect(panel_x, panel_y, panel_w, panel_h).collidepoint(pos):
                return True

        # 3. Station menu
        if getattr(self, 'active_station', None):
            panel_w, panel_h = 400, 300
            panel_x = (SCREEN_WIDTH - panel_w) // 2
            panel_y = (SCREEN_HEIGHT - panel_h) // 2
            if pygame.Rect(panel_x, panel_y, panel_w, panel_h).collidepoint(pos):
                return True

        # 4. Dialogue
        if getattr(self, 'active_dialogue', None):
            width, height = 400, 160
            x, y = (SCREEN_WIDTH - width) // 2, SCREEN_HEIGHT - height - 100
            if pygame.Rect(x, y, width, height).collidepoint(pos):
                return True

        # 5. Chatbox (Shrink hitbox to only the message area, not a 450px block)
        if pos[0] < 300 and pos[1] > SCREEN_HEIGHT - 60:
            return True
        
        # Or if the chat area has many lines (let's just use the bottom for now)
        # if pygame.Rect(10, SCREEN_HEIGHT - 150, 450, 140).collidepoint(pos):
        #    return True

        # 6. Minimap
        mm_radius = 80
        mm_x = SCREEN_WIDTH - mm_radius - 20
        mm_y = 20 + mm_radius
        dist_sq = (pos[0] - mm_x)**2 + (pos[1] - mm_y)**2
        if dist_sq <= (mm_radius + 4)**2:
            return True


        return False