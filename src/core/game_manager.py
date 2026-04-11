import pygame
import random
import time
from src.entities.player import Player
from src.entities.resource_item import ResourceItem
from src.entities.resource_node import ResourceNode
from src.entities.bank import Bank
from src.entities.station import Station
from src.ui.ui import UIManager
from src.entities.enemy import Enemy
from src.entities.crop import Crop
from src.core.camera import Camera
from src.systems.save_manager import SaveManager
from src.systems.action_manager import ActionManager
from src.systems.pathfinder import find_path
from src.systems.recipe_manager import RecipeManager
from src.entities.projectile import Projectile
from src.entities.shop import Shop
from src.entities.npc import NPC
from src.core.settings import *
from src.core.tilemap import TileMap

class GameManager:
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        # 1. World and Core systems
        self.tilemap = TileMap(self)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT)
        
        # 2. Player must exist before UI
        self.player = Player(PLAYER_START_X, PLAYER_START_Y, self)
        
        # 3. UI and Actions
        self.ui = UIManager(self)
        self.action_manager = ActionManager(self.ui, self.camera)
        self.last_tick = pygame.time.get_ticks()
        self._last_frame_ms = 0.0
        
        # 4. Other Game objects
        self.resources = []
        self.enemies = []
        self.npcs = []
        self.projectiles = []
        self.crops = []
        self.respawn_queue = []
        self.recipe_manager = RecipeManager()
        
        # 4. Fixed entities (Snapped to grid)
        _hub_bank_x = PLAYER_START_X + 64
        _hub_bank_y = PLAYER_START_Y - 64 
        self.bank = Bank(_hub_bank_x, _hub_bank_y)

        _station_x = _hub_bank_x + TILE_SIZE * 3
        _shop_x = _hub_bank_x - TILE_SIZE * 3
        _shop_y = _hub_bank_y + TILE_SIZE * 2
        self.shop = Shop(_shop_x, _shop_y)

        self.stations = []
        self.stations.append(Station(_station_x, _hub_bank_y, "furnace", "Furnace"))
        self.stations.append( Station(_station_x, _hub_bank_y + TILE_SIZE * 2, "workbench", "Workbench") )
        self.stations.append( Station(_station_x, _hub_bank_y + TILE_SIZE * 4, "stove", "Stove") )
        self.stations.append( Station(_hub_bank_x + 320, _hub_bank_y - 192, "air_altar", "Air Altar") )
        self.stations.append( Station(_hub_bank_x - 320, _hub_bank_y - 192, "mind_altar", "Mind Altar") )
        
        # 5. Populate world (land check enabled)
        self._generate_resources()
        self._generate_enemies()

        # Add quest-specific NPC near spawn (grid snapped)
        self.npcs.append(NPC(PLAYER_START_X, PLAYER_START_Y - 32, "Baker", (255, 200, 200)))
        
        self.show_fps_overlay = True
        self.running = True
        self.game_over = False

    def _get_random_walkable_tile(self, allow_water=False):
        """Find a random grid-aligned position. Ensuring land-only if allow_water is False."""
        for _ in range(100): # Limit attempts
            tx = random.randint(1, self.tilemap.width - 2)
            ty = random.randint(1, self.tilemap.height - 2)
            
            walkable = self.tilemap.world_map[tx][ty] != TILE_WATER
            if allow_water or walkable:
                # Return world coordinates (top-left of tile)
                return tx * TILE_SIZE, ty * TILE_SIZE
        return 0, 0 # Fallback

    def _generate_resources(self):
        # 1. Main resources (Land only)
        configs = [
            (NUM_TREES, "tree", 20, "axe", "wood", 5, 15000, 1),
            (NUM_ROCKS, "rock", 35, "pickaxe", "stone", 3, 20000, 1),
            (NUM_IRON_ROCKS, "iron_rock", 50, "pickaxe", "iron_ore", 3, 30000, 5),
            (NUM_BUSHES, "bush", 10, None, "fiber", 2, 10000, 1),
            (NUM_COAL_ROCKS, "coal_rock", 50, "pickaxe", "coal", 4, 40000, 15),
            (NUM_ESSENCE_ROCKS, "essence_rock", 40, "pickaxe", "rune_essence", 8, 10000, 1)
        ]
        
        for count, ntype, diff, tool, yields, hp, respawn, min_lvl in configs:
            for _ in range(count):
                rx, ry = self._get_random_walkable_tile(allow_water=False)
                self.resources.append(ResourceNode(rx, ry, ntype, diff, tool, yields, hp, respawn, min_lvl))

        # 2. Fishing Spots (Water only)
        for _ in range(NUM_FISHING_SPOTS):
            for _ in range(100):
                tx = random.randint(1, self.tilemap.width - 2)
                ty = random.randint(1, self.tilemap.height - 2)
                if self.tilemap.world_map[tx][ty] == TILE_WATER:
                    rx, ry = tx * TILE_SIZE, ty * TILE_SIZE
                    self.resources.append(ResourceNode(rx, ry, "fishing_spot", 25, "rod", "raw_fish", hp=3, respawn_time=20000, min_level=1))
                    break

        # 3. Quest components near spawn (Snap manually)
        cx, cy = PLAYER_START_X, PLAYER_START_Y
        self.resources.append(ResourceNode(cx + 64, cy + 64, "wheat_field", 5, None, "wheat", hp=1, respawn_time=5000, min_level=1))
        self.resources.append(ResourceNode(cx + 96, cy + 64, "chicken", 5, None, "egg", hp=1, respawn_time=5000, min_level=1))
        self.resources.append(ResourceNode(cx + 128, cy + 64, "cow", 5, None, "milk", hp=1, respawn_time=5000, min_level=1))

    def _generate_enemies(self):
        for etype, count in [("goblin", NUM_GOBLINS), ("skeleton", NUM_SKELETONS), ("guard", NUM_GUARDS)]:
            for _ in range(count):
                ex, ey = self._get_random_walkable_tile(allow_water=False)
                self.enemies.append(Enemy(ex, ey, etype))

    def _restart(self):
        self.game_over = False

    def _handle_player_death(self):
        """Initiate death fade animation and schedule respawn."""
        self.ui.show_message("You died!")
        self.ui.is_fading = True
        self.ui.fade_start_time = pygame.time.get_ticks()

    def _handle_player_respawn(self):
        """Respawn player at bank with full HP and clean combat state. Items and equipment are kept (safe death)."""
        # Teleport to bank spawn point
        self.player.rect.centerx = PLAYER_START_X
        self.player.rect.centery = PLAYER_START_Y
        
        # Reset player state (clears action/combat, restores full HP)
        self.player.reset_after_death()
        
        # Show respawn message
        self.ui.show_message("You have been recovered!")
        self.respawn_queue = []
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT)
        self.ui = UIManager(self.player)
        self.action_manager = ActionManager(self.ui, self.camera)
        self.last_tick = pygame.time.get_ticks()

    def _award_xp(self, skill_name, amount, world_x=None, world_y=None):
        """Award XP and spawn a floating XP drop near the provided world position."""
        if amount <= 0:
            return False
        leveled_up = self.player.skills.gain_xp(skill_name, amount)
        if world_x is None:
            world_x = self.player.rect.centerx
        if world_y is None:
            world_y = self.player.rect.top
        self.ui.add_xp_drop(skill_name, amount, world_x, world_y, self.camera)
        return leveled_up

    def run(self):
        while self.running:
            frame_ms = float(self.clock.tick(FPS))
            self._last_frame_ms = frame_ms
            dt = frame_ms / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            
        pygame.quit()

    def _find_entity_at_world(self, world_x, world_y):
        """Return the topmost entity at world coordinates, or None."""
        click_rect = pygame.Rect(world_x - 5, world_y - 5, 10, 10)
        for item in self.resources:
            if click_rect.colliderect(item.rect):
                return item
        for enemy in self.enemies:
            if click_rect.colliderect(enemy.rect):
                return enemy
        if click_rect.colliderect(self.shop.rect):
            return self.shop
        if click_rect.colliderect(self.bank.rect):
            return self.bank
        for npc in self.npcs:
            if click_rect.colliderect(npc.rect):
                return npc
        for station in self.stations:
            if click_rect.colliderect(station.rect):
                return station
        for crop in self.crops:
            if click_rect.colliderect(crop.rect):
                return crop
        return None

    def _pathfind_to_entity(self, world_x, world_y, entity=None, action_type="default"):
        obstacles = self._get_solid_obstacles()
        path = find_path(
            (self.player.rect.centerx, self.player.rect.centery),
            (world_x, world_y),
            obstacles,
            self.tilemap.world_map
        )
        self.player.set_target_destination(world_x, world_y, target_entity=entity, waypoints=path or None, action_type=action_type)

    def handle_world_click(self, pos, button):
        # Convert screen pos to world pos
        world_x = pos[0] + self.camera.camera_rect.x
        world_y = pos[1] + self.camera.camera_rect.y
        entity = self._find_entity_at_world(world_x, world_y)
        self._pathfind_to_entity(world_x, world_y, entity)

    def show_world_context_menu(self, screen_pos):
        """Build and display an RS-style right-click context menu for the world position."""
        world_x = screen_pos[0] + self.camera.camera_rect.x
        world_y = screen_pos[1] + self.camera.camera_rect.y
        entity = self._find_entity_at_world(world_x, world_y)

        options = []

        from src.entities.resource_item import ResourceItem
        from src.entities.resource_node import ResourceNode
        from src.entities.enemy import Enemy
        from src.entities.bank import Bank
        from src.entities.station import Station
        from src.entities.npc import NPC

        if entity is None:
            options.append({
                "label": "Walk here",
                "action": lambda: self._pathfind_to_entity(world_x, world_y)
            })
            options.append({
                "label": "Examine Ground",
                "action": lambda: self.ui.show_message("Just the ground.")
            })
        elif isinstance(entity, ResourceItem):
            name = entity.resource_type.replace("_", " ").title()
            _e = entity
            options.append({
                "label": f"Pick-up {name}",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e)
            })
            options.append({
                "label": f"Examine {name}",
                "action": lambda n=name: self.ui.show_message(f"A {n} on the ground.")
            })
        elif isinstance(entity, ResourceNode):
            name = entity.node_type.replace("_", " ").title()
            action_verb = {
                "tree": "Chop", "rock": "Mine", "iron_rock": "Mine",
                "bush": "Search", "fishing_spot": "Fish"
            }.get(entity.node_type, "Gather")
            _e = entity
            options.append({
                "label": f"{action_verb} {name}",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e)
            })
            options.append({
                "label": f"Examine {name}",
                "action": lambda n=name: self.ui.show_message(f"A {n} resource node.")
            })
        elif isinstance(entity, Enemy):
            _e = entity
            options.append({
                "label": f"Attack {entity.name}",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e)
            })
            options.append({
                "label": f"Examine {entity.name}",
                "action": lambda e=_e: self.ui.show_message(
                    f"A level {e.combat_level} {e.name}. Max hit: {e.max_hit}."
                )
            })
        elif isinstance(entity, Bank):
            _e = entity
            options.append({
                "label": "Talk-to Teller",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e, action_type="talk")
            })
            options.append({
                "label": "Use Bank",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e)
            })
        elif isinstance(entity, NPC):
            _e = entity
            options.append({
                "label": f"Talk-to {entity.name}",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e, action_type="talk")
            })
            options.append({
                "label": f"Examine {entity.name}",
                "action": lambda e=_e: self.ui.show_message(f"It's {e.name}.")
            })
            options.append({
                "label": "Examine Bank",
                "action": lambda: self.ui.show_message("The bank. Safely stores your items.")
            })
        elif isinstance(entity, Shop):
            _e = entity
            options.append({
                "label": "Talk-to Shopkeeper",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e, action_type="talk")
            })
            options.append({
                "label": "Trade Shop",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e)
            })
            options.append({
                "label": "Examine Shop",
                "action": lambda: self.ui.show_message("A general store. Trade items for coins.")
            })
        elif isinstance(entity, Station):
            name = entity.name
            _e = entity
            options.append({
                "label": f"Use {name}",
                "action": lambda e=_e: self._pathfind_to_entity(e.rect.centerx, e.rect.centery, e)
            })
            options.append({
                "label": f"Examine {name}",
                "action": lambda n=name: self.ui.show_message(f"A {n}. Used for crafting.")
            })

        self.ui.show_context_menu(screen_pos, options)

    def _show_inventory_context_menu(self, screen_pos, item_index):
        """RS-style right-click menu for an inventory item."""
        active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0 and item != "coins"]
        if not (0 <= item_index < len(active_items)):
            return
        item_name, _ = active_items[item_index]
        display_name = item_name.replace("_", " ").title()

        options = []
        
        # Special "Bury" option for bones
        if item_name == "bones":
            _n = item_name
            options.append({
                "label": "Bury Bone",
                "action": lambda n=_n: self._bury_bone()
            })
        
        # Use / Equip option
        _n = item_name
        options.append({
            "label": f"Use {display_name}",
            "action": lambda n=_n: self._inv_use_item(n)
        })
        # Drop option
        options.append({
            "label": f"Drop {display_name}",
            "action": lambda n=_n: self._inv_drop_item(n)
        })
        options.append({
            "label": f"Examine {display_name}",
            "action": lambda dn=display_name: self.ui.show_message(f"It's a {dn}.")
        })
        self.ui.show_context_menu(screen_pos, options)

    def _show_equipped_context_menu(self, screen_pos, item_index):
        """RS-style right-click menu for an equipped item."""
        if not (0 <= item_index < len(self.player.equipped_items)):
            return
        item_name = self.player.equipped_items[item_index]
        display_name = item_name.replace("_", " ").title()

        options = [
            {
                "label": f"Remove {display_name}",
                "action": lambda n=item_name: self._inv_remove_equipped(n)
            },
            {
                "label": f"Examine {display_name}",
                "action": lambda dn=display_name: self.ui.show_message(f"You're wearing {dn}.")
            }
        ]
        self.ui.show_context_menu(screen_pos, options)

    def _inv_use_item(self, item_name):
        success, msg = self.player.use_item(item_name)
        self.ui.show_message(msg)

    def _inv_drop_item(self, item_name):
        self.player.inventory.remove_item(item_name, 1)
        drop_x = self.player.rect.centerx + random.randint(-20, 20)
        drop_y = self.player.rect.centery + random.randint(-20, 20)
        self.resources.append(ResourceItem(drop_x, drop_y, item_name))
        self.ui.show_message(f"Dropped 1 {item_name.replace('_', ' ').title()}")

    def _inv_remove_equipped(self, item_name):
        success, msg = self.player.unequip_item(item_name)
        self.ui.show_message(msg)

    def _bury_bone(self):
        """Bury a bone and award Prayer XP."""
        if self.player.inventory.items.get("bones", 0) <= 0:
            self.ui.show_message("You don't have any bones to bury.")
            return
        
        self.player.inventory.remove_item("bones", 1)
        prayer_xp = 4
        self._award_xp("prayer", prayer_xp, self.player.rect.centerx, self.player.rect.top)
        self.ui.show_message("You buried a bone.")

            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEWHEEL:
                if self.ui.active_tab == "skills":
                    self.ui.scroll_skills(event.y)
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                # Context menu: any click dismisses it; left-click executes hovered option
                if event.type == pygame.MOUSEBUTTONDOWN and self.ui.context_menu:
                    if event.button == 1:
                        act = self.ui.handle_context_menu_click(event.pos)
                        self.ui.context_menu = None
                        if act:
                            act()
                    else:
                        self.ui.context_menu = None
                    continue

                action, index = self.ui.handle_mouse_event(event)
                if action == "next_dialogue":
                    if self.ui.active_dialogue.get("type", "linear") == "linear":
                        self.ui.active_dialogue["line_index"] += 1
                        if self.ui.active_dialogue["line_index"] >= len(self.ui.active_dialogue.get("lines", [])):
                            self.ui.close_dialogue()
                elif action == "dialogue_response":
                    node_id, response_idx = index
                    node = self.ui.dialogue_manager.get_node(node_id)
                    response = node["responses"][response_idx]
                    
                    condition = response.get("condition")
                    can_proceed = True
                    if condition:
                        if condition["type"] == "has_items":
                            for req_item, req_amt in condition.get("items", {}).items():
                                if self.player.inventory.items.get(req_item, 0) < req_amt:
                                    can_proceed = False
                                    break
                    
                    if not can_proceed:
                        self.ui.show_message("You don't meet the requirements.")
                    else:
                        r_action = response.get("action")
                        if r_action:
                            if r_action == "start_quest_bakers_assistant":
                                self.player.quest_manager.start_quest("bakers_assistant")
                            elif r_action == "complete_quest_bakers_assistant":
                                self.player.inventory.remove_item("egg", 1)
                                self.player.inventory.remove_item("milk", 1)
                                self.player.inventory.remove_item("wheat", 1)
                                self.player.quest_manager.complete_quest("bakers_assistant")
                                self._award_xp("cooking", 100, self.player.rect.centerx, self.player.rect.top)
                                self.ui.show_message("Quest Complete: The Baker's Assistant!")
                                baker_npc = next((n for n in self.npcs if n.name == "Baker"), None)
                                if baker_npc:
                                    from src.entities.station import Station
                                    self.stations.append(Station(baker_npc.rect.right + 20, baker_npc.rect.top, "high_tier_stove", "Iron Stove"))
                        
                        next_node = response.get("next")
                        if next_node == "END":
                            self.ui.close_dialogue()
                        else:
                            self.ui.show_dialogue_node(next_node)
                elif action == "use_item":
                    active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0 and item != "coins"]
                    if 0 <= index < len(active_items):
                        item_name, _ = active_items[index]
                        success, msg = self.player.use_item(item_name)
                        self.ui.show_message(msg)
                elif action == "deposit_item":
                    active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0]
                    if 0 <= index < len(active_items):
                        item_name, _ = active_items[index]
                        self.player.inventory.remove_item(item_name, 1)
                        self.player.bank_inventory.add_item(item_name, 1)
                elif action == "withdraw_item":
                    active_items = [(item, count) for item, count in self.player.bank_inventory.items.items() if count > 0]
                    if 0 <= index < len(active_items):
                        item_name, _ = active_items[index]
                        if self.player.inventory.add_item(item_name, 1):
                            self.player.bank_inventory.remove_item(item_name, 1)
                        else:
                            self.ui.show_message("Your inventory is full.")
                elif action == "shop_buy_item":
                    shop_items = [(item, count) for item, count in self.shop.inventory.items.items() if count > 0]
                    if 0 <= index < len(shop_items):
                        item_name, _ = shop_items[index]
                        price = self.shop.get_buy_price(item_name)
                        coins = self.player.inventory.get_item_count("coins")
                        if coins < price:
                            self.ui.show_message("Not enough coins.")
                        elif not self.player.inventory.add_item(item_name, 1):
                            self.ui.show_message("Your inventory is full.")
                        else:
                            self.player.inventory.remove_item("coins", price)
                            self.shop.inventory.remove_item(item_name, 1)
                            self.ui.show_message(f"Bought 1 {item_name.replace('_', ' ')} for {price} coins.")
                elif action == "shop_sell_item":
                    active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0]
                    if 0 <= index < len(active_items):
                        item_name, _ = active_items[index]
                        if item_name == "coins":
                            self.ui.show_message("You can't sell coins.")
                        elif not self.shop.can_sell_item(item_name):
                            self.ui.show_message("The shop won't buy that item.")
                        else:
                            price = self.shop.get_sell_price(item_name)
                            self.player.inventory.remove_item(item_name, 1)
                            self.player.inventory.add_item("coins", price)
                            self.shop.inventory.add_item(item_name, 1)
                            self.ui.show_message(f"Sold 1 {item_name.replace('_', ' ')} for {price} coins.")
                elif action == "right_click_inventory":
                    # Show RS-style context menu for hovered inventory slot
                    if event.type == pygame.MOUSEBUTTONDOWN and self.ui.active_tab == "inventory":
                        rects = self.ui.get_inventory_slot_rects()
                        for i, rect in enumerate(rects):
                            if rect.collidepoint(event.pos):
                                self._show_inventory_context_menu(event.pos, i)
                                break
                        else:
                            equipped_rects = self.ui.get_equipped_slot_rects()
                            for i, rect in enumerate(equipped_rects):
                                if rect.collidepoint(event.pos):
                                    self._show_equipped_context_menu(event.pos, i)
                                    break
                elif action == "craft_item":
                    recipes = self.recipe_manager.get_handcrafted()
                    if 0 <= index < len(recipes):
                        recipe = recipes[index]
                        skill_name = recipe.get("skill", "crafting")
                        skill_level = getattr(self.player.skills, skill_name, self.player.skills.crafting).level
                        success, result = self.player.inventory.craft(recipe["name"], skill_level, self.recipe_manager)
                        if success:
                            self._award_xp(skill_name, result)
                            self.ui.show_message(f"{recipe['label']} crafted! (+{result} {skill_name.capitalize()} XP)")
                        else:
                            self.ui.show_message(result)
                elif action is None and event.type == pygame.MOUSEBUTTONDOWN:
                    # Only block clicks that land ON a UI panel/element background
                    if not self.ui.is_pos_on_ui(event.pos):
                        if event.button == 1:
                            self.handle_world_click(event.pos, event.button)
                        elif event.button == 3:
                            self.show_world_context_menu(event.pos)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    self.show_fps_overlay = not self.show_fps_overlay
                    continue
                if event.key == pygame.K_g:
                    self.tilemap.toggle_grid()
                    continue
                if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_q:
                    self.running = False
                    continue
                if self.game_over:
                    if event.key == pygame.K_r: self._restart()
                    continue

                if event.key == pygame.K_ESCAPE and self.ui.context_menu:
                    self.ui.context_menu = None
                    continue

                if self.ui.active_tab == "skills" and event.key == pygame.K_ESCAPE:
                    self.ui.active_tab = None
                    continue
                
                if self.ui.active_tab == "inventory":
                    self._handle_inventory_input(event)
                elif self.ui.active_tab == "crafting":
                    self._handle_crafting_input(event)
                elif self.ui.active_bank:
                    self._handle_bank_input(event)
                elif self.ui.active_shop:
                    self._handle_shop_input(event)
                elif getattr(self.ui, 'active_station', None):
                    self._handle_station_input(event)
                else:
                    self._handle_main_input(event)

    def _handle_crafting_input(self, event):
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_c:
            self.ui.active_tab = None
        else:
            recipes = self.recipe_manager.get_handcrafted()
            if event.key == pygame.K_UP:
                self.ui.crafting_index = max(0, self.ui.crafting_index - 1)
            elif event.key == pygame.K_DOWN:
                self.ui.crafting_index = min(len(recipes) - 1, self.ui.crafting_index + 1)
            elif event.key == pygame.K_RETURN:
                if 0 <= self.ui.crafting_index < len(recipes):
                    recipe = recipes[self.ui.crafting_index]
                    skill_name = recipe.get("skill", "crafting")
                    skill_level = getattr(self.player.skills, skill_name, self.player.skills.crafting).level
                    success, result = self.player.inventory.craft(recipe["name"], skill_level, self.recipe_manager)
                    if success:
                        self._award_xp(skill_name, result)
                        self.ui.show_message(f"{recipe['label']} crafted! (+{result} {skill_name.capitalize()} XP)")
                    else:
                        self.ui.show_message(result)

    def _handle_inventory_input(self, event):
        active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0 and item != "coins"]
        
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
            self.ui.active_tab = None
        elif event.key == pygame.K_UP:
            self.ui.inventory_index = max(0, self.ui.inventory_index - 6)
        elif event.key == pygame.K_DOWN:
            self.ui.inventory_index = min(len(active_items) - 1, self.ui.inventory_index + 6)
        elif event.key == pygame.K_LEFT:
            self.ui.inventory_index = max(0, self.ui.inventory_index - 1)
        elif event.key == pygame.K_RIGHT:
            self.ui.inventory_index = min(len(active_items) - 1, self.ui.inventory_index + 1)
        elif event.key == pygame.K_RETURN:
            if 0 <= self.ui.inventory_index < len(active_items):
                item_name, _ = active_items[self.ui.inventory_index]
                success, msg = self.player.use_item(item_name)
                self.ui.show_message(msg)
            else:
                self.ui.show_message("No item selected.")

    def _handle_bank_input(self, event):
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_e:
            self.ui.active_bank = False
        elif event.key == pygame.K_t:
            for item, count in list(self.player.inventory.items.items()):
                if count > 0:
                    self.player.bank_inventory.add_item(item, count)
                    self.player.inventory.items[item] = 0
            self.ui.show_message("Deposited all items into bank.")

    def _handle_shop_input(self, event):
        """Handle shop interaction input (buy/sell items)."""
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_e:
            self.ui.active_shop = False

    def _handle_station_input(self, event):
        station = self.ui.active_station
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_e:
            self.ui.active_station = None
        elif event.key == pygame.K_UP:
            self.ui.station_index = max(0, self.ui.station_index - 1)
        elif event.key == pygame.K_DOWN:
            recipes = self.recipe_manager.get_for_station(station.station_type)
            self.ui.station_index = min(len(recipes) - 1, self.ui.station_index + 1)
        elif event.key == pygame.K_RETURN:
            recipes = self.recipe_manager.get_for_station(station.station_type)
            if 0 <= self.ui.station_index < len(recipes):
                recipe = recipes[self.ui.station_index]
                # Start processing if we have items
                can_craft = True
                for item, amount in recipe["inputs"].items():
                    if self.player.inventory.items.get(item, 0) < amount:
                        self.ui.show_message(f"Need {amount} {item}!")
                        can_craft = False
                        break
                
                # Check min level against the recipe's actual skill
                recipe_skill = recipe.get("skill", "crafting")
                recipe_skill_level = getattr(self.player.skills, recipe_skill, self.player.skills.crafting).level
                if recipe_skill_level < recipe["min_level"]:
                    self.ui.show_message(f"Requires {recipe_skill.capitalize()} Lv.{recipe['min_level']}.")
                    can_craft = False

                if can_craft:
                    for item, amount in recipe["inputs"].items():
                        self.player.inventory.remove_item(item, amount)

                    output_item = list(recipe["outputs"].keys())[0]
                    duration = recipe.get("duration", 2000)
                    station.pending_recipe = recipe
                    station.start_processing(list(recipe["inputs"].keys())[0], output_item, 1, duration)
                    self.ui.show_message(f"Started processing {output_item}...")
            
    def _handle_main_input(self, event):
        if getattr(self.ui, 'active_dialogue', None):
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                if self.ui.active_dialogue.get("type", "linear") == "linear":
                    self.ui.active_dialogue["line_index"] += 1
                    if self.ui.active_dialogue["line_index"] >= len(self.ui.active_dialogue.get("lines", [])):
                        self.ui.close_dialogue()
            return

        # Hotbar slots 1–9
        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                         pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
            self._activate_hotbar_slot(event.key - pygame.K_1)
            return
        if event.key == pygame.K_e:
            self._interact()
        elif event.key == pygame.K_f:
            self._farm()
        elif event.key == pygame.K_SPACE:
            self._attack()
        elif event.key == pygame.K_c:
            self.ui.toggle_tab("crafting")
            self.ui.crafting_index = 0
        elif event.key == pygame.K_k:
            self.ui.toggle_tab("skills")
        elif event.key == pygame.K_i:
            self.ui.toggle_tab("inventory")
        elif event.key == pygame.K_RETURN:
            # Use/Equip first viable item (simple priority)
            for item in ["bread", "iron_armor", "iron_sword", "sword"]:
                success, msg = self.player.use_item(item)
                if success:
                    self.ui.show_message(msg)
                    return
            self.ui.show_message("No usable item in inventory.")
        elif event.key == pygame.K_TAB:
            self.ui.toggle_tab("combat")
        elif event.key == pygame.K_m:
            new_mode = "ranged" if self.player.combat_mode == "melee" else "melee"
            self.player.set_combat_mode(new_mode)
            self.ui.show_message(f"Combat mode: {new_mode.capitalize()}")
        elif event.key == pygame.K_F5:
            SaveManager.save_game(self.player, self.resources, self.enemies)
            self.ui.show_message("Game Saved!")
        elif event.key == pygame.K_F9:
            if SaveManager.load_game(self.player, self.resources, self.enemies):
                self.ui.show_message("Game Loaded!")
            else:
                self.ui.show_message("No Save Found.")

    def _activate_hotbar_slot(self, index):
        """Activate hotbar slot at 0-based index."""
        slots = self.ui.hotbar_slots
        if index >= len(slots) or slots[index] is None:
            return
        action = slots[index]
        if action == "toggle_combat":
            new_mode = "ranged" if self.player.combat_mode == "melee" else "melee"
            self.player.set_combat_mode(new_mode)
            self.ui.show_message(f"Combat mode: {new_mode.capitalize()}")
        elif action in ("accurate", "aggressive", "defensive", "rapid", "longrange"):
            self.player.set_combat_style(action)
            self.ui.show_message(f"Style: {action.capitalize()}")
        else:
            success, msg = self.player.use_item(action)
            self.ui.show_message(msg)

    def _interact(self):
        # Check for bank
        if self.player.rect.inflate(10, 10).colliderect(self.bank.rect):
            self.ui.active_shop = False
            self.ui.active_bank = True
            self.ui.show_message("Opened bank vault.")
            return

        # Check for shop
        if self.player.rect.inflate(10, 10).colliderect(self.shop.rect):
            self.ui.active_bank = False
            self.ui.active_shop = True
            self.ui.show_message("Opened shop.")
            return

        # Check for stations
        for station in self.stations:
            if self.player.rect.inflate(10, 10).colliderect(station.rect):
                collected = station.collect(self.player)
                if collected > 0:
                    if station.pending_recipe:
                        recipe = station.pending_recipe
                        skill_name = recipe.get("skill", "crafting")
                        xp_total = recipe["xp"] * collected
                        leveled_up = self._award_xp(skill_name, xp_total, self.player.rect.centerx, self.player.rect.top)
                        msg = f"Collected {collected} items! (+{xp_total} {skill_name.capitalize()} XP)"
                        if leveled_up:
                            lvl = getattr(self.player.skills, skill_name).level
                            msg += f" — {skill_name.capitalize()} Lv.{lvl}!"
                        self.ui.show_message(msg)
                        station.pending_recipe = None
                    else:
                        self.ui.show_message(f"Collected {collected} items!")
                else:
                    self.ui.active_station = station
                    self.ui.station_index = 0
                    self.ui.show_message(f"Opened {station.name}.")
                return

        # Check for resources/items
        for item in self.resources[:]:
            if self.player.rect.inflate(10, 10).colliderect(item.rect):
                if isinstance(item, ResourceItem):
                    if self.player.inventory.add_item(item.resource_type, 1):
                        self.ui.show_message(f"Picked up 1 {item.resource_type}!")
                        self.resources.remove(item)
                    else:
                        self.ui.show_message("Your inventory is full.")
                elif isinstance(item, ResourceNode) and item.is_active:
                    self.player.current_action = "gathering"
                    self.player.action_target = item
                    self.ui.show_message(f"Started gathering {item.node_type}...")
                return

    def _farm(self):
        grid_x = (self.player.rect.centerx // TILE_SIZE) * TILE_SIZE
        grid_y = (self.player.rect.centery // TILE_SIZE) * TILE_SIZE
        target_crop = next((c for c in self.crops if c.rect.topleft == (grid_x, grid_y)), None)
        
        if target_crop:
            if target_crop.is_mature:
                if not self.player.inventory.add_item("wheat", 3):
                    self.ui.show_message("Your inventory is full.")
                    return
                self.crops.remove(target_crop)
                if self._award_xp("farming", 20, self.player.rect.centerx, self.player.rect.top):
                    self.ui.show_message("Farming Level UP!")
                self.ui.show_message(f"Harvested {target_crop.crop_type}!")
            else:
                self.ui.show_message(f"Growing... (Stage {target_crop.growth_stage}/{target_crop.max_growth})")
        elif self.player.inventory.items.get("bronze_hoe", 0) > 0:
            if self.player.inventory.items.get("wheat_seeds", 0) > 0:
                self.crops.append(Crop(grid_x, grid_y))
                self.player.inventory.remove_item("wheat_seeds", 1)
                self.ui.show_message("Tilled and planted wheat!")
            else:
                self.ui.show_message("Need seeds.")
        else:
            self.ui.show_message("Need a hoe.")

    def _roll_hit(self, base_damage, enemy):
        """RS-like accuracy roll. Returns (damage, is_hit).
        Hit chance = 50% + (attack_level - enemy_defense_level) * 2.5%, clamped 10–95%."""
        atk_level = (self.player.skills.ranged.level
                     if self.player.combat_mode == "ranged"
                     else self.player.skills.attack.level)
        def_level = getattr(enemy, 'defense_level', 1)
        hit_chance = max(0.10, min(0.95, 0.50 + (atk_level - def_level) * 0.025))
        if random.random() > hit_chance:
            return 0, False
        return base_damage, True

    def _on_enemy_drops(self, enemy):
        """Spawn drop items from enemy's drop table."""
        for item_name, min_amt, max_amt, chance in enemy.drops:
            if random.random() < chance:
                amount = random.randint(min_amt, max_amt)
                for _ in range(amount):
                    drop_x = enemy.rect.centerx + random.randint(-16, 16)
                    drop_y = enemy.rect.centery + random.randint(-16, 16)
                    self.resources.append(ResourceItem(drop_x, drop_y, item_name))

    def _kill_enemy(self, enemy):
        """Handle all consequences of an enemy death."""
        if enemy not in self.enemies:
            return
        self.enemies.remove(enemy)
        self._on_enemy_drops(enemy)
        self._on_enemy_defeated_xp(enemy)
        self.respawn_queue.append((
            pygame.time.get_ticks() + enemy.respawn_time,
            enemy.enemy_type, enemy.spawn_x, enemy.spawn_y
        ))
        if self.player.action_target is enemy:
            self.player.current_action = None
            self.player.action_target = None

    def _on_enemy_defeated_xp(self, enemy):
        """Award XP on kill, scaled to enemy difficulty."""
        notes = []
        con_xp = max(1, enemy.xp_reward // 3)
        combat_xp = enemy.xp_reward

        if self._award_xp("constitution", con_xp, enemy.rect.centerx, enemy.rect.top):
            self.player.max_hp += 10
            self.player.hp = min(self.player.hp + 10, self.player.max_hp)
            notes.append("Constitution level up! +10 HP")

        primary, secondary = self.player.get_xp_skill_for_hit()
        if self._award_xp(primary, combat_xp, enemy.rect.centerx, enemy.rect.top):
            if primary == "strength":
                self.player.base_attack += 2
                notes.append("Strength level up! +2 ATK")
            else:
                notes.append(f"{primary.capitalize()} level up!")
        if secondary and self._award_xp(secondary, combat_xp // 2, enemy.rect.centerx, enemy.rect.top):
            notes.append(f"{secondary.capitalize()} level up!")

        base_msg = f"{enemy.name} defeated! (+{combat_xp} XP)"
        self.ui.show_message(base_msg + (" " + " ".join(notes) if notes else ""))

    def _attack(self):
        """Space: instant-hit nearest enemy if adjacent, else pathfind to it."""
        if self.player.hp <= 0: return
        if not self.enemies:
            self.ui.show_message("No enemies nearby.")
            return
        import math
        nearest = min(self.enemies,
                      key=lambda e: math.hypot(e.rect.centerx - self.player.rect.centerx,
                                               e.rect.centery - self.player.rect.centery))
        attack_rect = self.player.rect.inflate(80, 80)
        if attack_rect.colliderect(nearest.rect):
            base_dmg = self.player.get_attack()
            dmg, is_hit = self._roll_hit(base_dmg, nearest)
            self.ui.add_hit_splat(dmg, nearest.rect.centerx, nearest.rect.top, self.camera, is_miss=not is_hit)
            if is_hit:
                nearest.hp -= dmg
                primary, secondary = self.player.get_xp_skill_for_hit()
                self._award_xp(primary, 5, self.player.rect.centerx, self.player.rect.top)
                if secondary:
                    self._award_xp(secondary, 2, self.player.rect.centerx, self.player.rect.top)
                self.ui.show_message(f"Hit {nearest.name} for {dmg}!")
                if nearest.hp <= 0:
                    self._kill_enemy(nearest)
                    return
            else:
                self.ui.show_message(f"Missed {nearest.name}!")
        # Set up auto-attack loop toward nearest enemy
        self.player.set_target_destination(
            nearest.rect.centerx, nearest.rect.centery, target_entity=nearest)

    def _get_solid_obstacles(self):
        obstacles = []
        # Add entity-based obstacles
        for item in self.resources:
            if isinstance(item, ResourceNode) and item.is_active and item.node_type != "fishing_spot":
                obstacles.append(item.rect)
        for station in self.stations:
            obstacles.append(station.rect)
        obstacles.append(self.shop.rect)
        obstacles.append(self.bank.rect)
        for npc in self.npcs:
            obstacles.append(npc.rect)
            
        # Add tile-based obstacles (Water)
        # Optimized: only add tiles that are somewhat near the player/camera
        cam_x, cam_y = self.camera.camera_rect.x, self.camera.camera_rect.y
        start_cx = max(0, (cam_x - 100) // TILE_SIZE)
        end_cx = min(self.tilemap.width, (cam_x + SCREEN_WIDTH + 100) // TILE_SIZE)
        start_cy = max(0, (cam_y - 100) // TILE_SIZE)
        end_cy = min(self.tilemap.height, (cam_y + SCREEN_HEIGHT + 100) // TILE_SIZE)
        
        for x in range(start_cx, end_cx):
            for y in range(start_cy, end_cy):
                if self.tilemap.world_map[x][y] == TILE_WATER:
                    obstacles.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                    
        return obstacles

    def update(self, dt):
        # Handle death fade and respawn transition
        if self.ui.is_fading:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.ui.fade_start_time
            if elapsed >= self.ui.fade_duration:
                # Fade complete: respawn
                self._handle_player_respawn()
                self.ui.is_fading = False
            # Continue updating during fade, but pause certain actions
            self.camera.update(self.player)
            self.ui.update()
            return
        
        if self.player.hp > 0:
            obstacles = self._get_solid_obstacles()
            if self.ui.active_tab != "crafting":
                self.player.update(dt, obstacles)
            
            for crop in self.crops:
                crop.update()
                
            for station in self.stations:
                station.update()
            
            # Action Manager Ticks (once per 600ms)
            current_time = pygame.time.get_ticks()
            if current_time - self.last_tick >= 600:
                self.last_tick = current_time
                if self.player.current_action == "gathering" and self.player.action_target:
                    self.action_manager.process_gathering_tick(self.player, self.player.action_target)
                elif self.player.current_action == "attacking" and self.player.action_target:
                    enemy = self.player.action_target
                    if enemy not in self.enemies:
                        self.player.current_action = None
                        self.player.action_target = None
                    elif self.player.combat_mode == "ranged" and self.player.has_bow():
                        import math
                        dx = enemy.rect.centerx - self.player.rect.centerx
                        dy = enemy.rect.centery - self.player.rect.centery
                        dist = math.hypot(dx, dy)
                        if dist <= RANGED_ATTACK_RANGE:
                            if self.player.inventory.items.get("arrow", 0) > 0:
                                self.player.inventory.remove_item("arrow", 1)
                                proj = Projectile(
                                    self.player.rect.centerx, self.player.rect.centery,
                                    enemy, self.player.get_ranged_attack()
                                )
                                self.projectiles.append(proj)
                            else:
                                self.ui.show_message("Out of arrows!")
                                self.player.current_action = None
                                self.player.action_target = None
                        else:
                            # Move closer — keep attack state so next tick re-evaluates
                            self.player.target_destination = (enemy.rect.centerx, enemy.rect.centery)
                            self.player.waypoints = []
                    elif self.player.combat_mode == "magic" and self.player.has_staff():
                        import math
                        dx = enemy.rect.centerx - self.player.rect.centerx
                        dy = enemy.rect.centery - self.player.rect.centery
                        dist = math.hypot(dx, dy)
                        if dist <= RANGED_ATTACK_RANGE:
                            spell_key = getattr(self.player, "active_spell", "wind_strike")
                            spell = getattr(self.player, "spells", {}).get(spell_key, None)
                            if not spell:
                                self.ui.show_message("No active spell!")
                                self.player.current_action = None
                                self.player.action_target = None
                            elif self.player.skills.magic.level < spell["req"]:
                                self.ui.show_message(f"Requires Magic Lv.{spell['req']}.")
                                self.player.current_action = None
                                self.player.action_target = None
                            else:
                                has_runes = True
                                for rune, amt in spell["cost"].items():
                                    if self.player.inventory.items.get(rune, 0) < amt:
                                        has_runes = False
                                        break
                                        
                                if has_runes:
                                    for rune, amt in spell["cost"].items():
                                        self.player.inventory.remove_item(rune, amt)
                                    magic_hit = spell["max_hit"] + (self.player.skills.magic.level // 4)
                                    proj = Projectile(
                                        self.player.rect.centerx, self.player.rect.centery,
                                        enemy, magic_hit
                                    )
                                    proj.color = (0, 200, 255)
                                    self.projectiles.append(proj)
                                else:
                                    self.ui.show_message("Not enough runes!")
                                    self.player.current_action = None
                                    self.player.action_target = None
                        else:
                            self.player.target_destination = (enemy.rect.centerx, enemy.rect.centery)
                            self.player.waypoints = []
                    else:
                        # Melee branch
                        attack_rect = self.player.rect.inflate(80, 80)
                        if attack_rect.colliderect(enemy.rect):
                            base_dmg = self.player.get_attack()
                            dmg, is_hit = self._roll_hit(base_dmg, enemy)
                            self.ui.add_hit_splat(dmg, enemy.rect.centerx, enemy.rect.top, self.camera, is_miss=not is_hit)
                            if is_hit:
                                enemy.hp -= dmg
                                primary, secondary = self.player.get_xp_skill_for_hit()
                                self._award_xp(primary, 5, self.player.rect.centerx, self.player.rect.top)
                                if secondary:
                                    self._award_xp(secondary, 2, self.player.rect.centerx, self.player.rect.top)
                                self.ui.show_message(f"Hit {enemy.name} for {dmg}!")
                                if enemy.hp <= 0:
                                    self._kill_enemy(enemy)
                            else:
                                self.ui.show_message(f"Missed {enemy.name}!")
                        else:
                            # Enemy moved — keep attack state and chase them
                            self.player.target_destination = (enemy.rect.centerx, enemy.rect.centery)
                            self.player.waypoints = []

            # Respawn queue — bring enemies back at their spawn locations
            now_ms = pygame.time.get_ticks()
            for entry in self.respawn_queue[:]:
                if now_ms >= entry[0]:
                    self.respawn_queue.remove(entry)
                    self.enemies.append(Enemy(entry[2], entry[3], entry[1]))

            # Nodes updates (respawn ticks)
            for item in self.resources:
                if isinstance(item, ResourceNode):
                    item.update()

            for enemy in self.enemies[:]:
                enemy.update(self.player, dt, obstacles + [self.player.rect])
                if enemy.rect.inflate(4, 4).colliderect(self.player.rect):
                    dmg = random.randint(1, enemy.max_hit)
                    if self.player.take_damage(dmg):
                        actual = max(1, dmg - self.player.get_defense())
                        self._award_xp("defense", 3, self.player.rect.centerx, self.player.rect.top)
                        self.ui.show_message(f"{enemy.name} hits you for {actual}!")
                        # Auto-retaliate when idle
                        if self.player.current_action is None and self.player.hp > 0:
                            self._pathfind_to_entity(enemy.rect.centerx, enemy.rect.centery, enemy)

            for proj in self.projectiles[:]:
                proj.update(dt)
                if proj.hit:
                    if proj.target in self.enemies:
                        base_dmg = proj.damage
                        dmg, is_hit = self._roll_hit(base_dmg, proj.target)
                        self.ui.add_hit_splat(dmg, proj.target.rect.centerx, proj.target.rect.top, self.camera, is_miss=not is_hit)
                        if is_hit:
                            proj.target.hp -= dmg
                            primary, secondary = self.player.get_xp_skill_for_hit()
                            leveled_up = self._award_xp(primary, 4, self.player.rect.centerx, self.player.rect.top)
                            if secondary:
                                self._award_xp(secondary, 2, self.player.rect.centerx, self.player.rect.top)
                            self.ui.show_message(f"Hit {proj.target.name} for {dmg}!")
                            if leveled_up:
                                lvl = getattr(self.player.skills, primary).level
                                self.ui.show_message(f"{primary.capitalize()} level up! Now level {lvl}")
                            if proj.target.hp <= 0:
                                self._kill_enemy(proj.target)
                        else:
                            self.ui.show_message(f"Missed {proj.target.name}!")
                    self.projectiles.remove(proj)
        else:
            # Player is dead: start fade and respawn sequence
            if not self.ui.is_fading:
                self._handle_player_death()
            
        self.camera.update(self.player)
        self.ui.update()

    def draw(self):
        self.screen.fill((0, 0, 0))
        # Draw Map background
        self.tilemap.draw(self.screen, self.camera)
        # Draw ground-level objects first (no Y-sort needed)
        for item in self.resources:
            item.draw(self.screen, self.camera)
        for crop in self.crops:
            crop.draw(self.screen, self.camera)
        for proj in self.projectiles:
            proj.draw(self.screen, self.camera)

        # Y-sort entities so lower ones draw on top (correct depth)
        y_sorted = sorted(
              self.stations + self.enemies + self.npcs + [self.bank, self.shop, self.player],
            key=lambda e: e.rect.bottom
        )
        for entity in y_sorted:
            entity.draw(self.screen, self.camera)
        self.ui.draw(self.screen)
        
        # Draw death fade overlay if fading
        if self.ui.is_fading:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.ui.fade_start_time
            fade_alpha = int((elapsed / self.ui.fade_duration) * 200)  # 0 to 200
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, fade_alpha))
            self.screen.blit(overlay, (0, 0))
        
        if self.game_over:
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            go_font = pygame.font.SysFont(None, 64)
            go_text = go_font.render("GAME OVER", True, (220, 50, 50))
            self.screen.blit(go_text, go_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 30)))
            sub_font = pygame.font.SysFont(None, 32)
            sub_text = sub_font.render("[R] Restart", True, (200, 200, 200))
            self.screen.blit(sub_text, sub_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 30)))
        if self.show_fps_overlay:
            hud = pygame.font.SysFont(None, 22)
            fps = self.clock.get_fps()
            line = f"FPS: {fps:.0f}  frame: {self._last_frame_ms:.1f} ms  (F3 hide)"
            self.screen.blit(hud.render(line, True, (180, 220, 180)), (8, 8))
        pygame.display.update()