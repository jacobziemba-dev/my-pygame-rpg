import pygame
import random
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
from src.core.settings import *

class GameManager:
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.player = Player(PLAYER_START_X, PLAYER_START_Y, self)
        self.resources = []
        self._generate_resources()
        
        self.enemies = []
        self._generate_enemies()
        self.projectiles = []

        # Bank is 2×2 tiles; keep stations to the right with tile gaps so rects do not overlap.
        _hub_bank_x = PLAYER_START_X + 96
        _hub_bank_y = PLAYER_START_Y - 48
        self.bank = Bank(_hub_bank_x, _hub_bank_y)

        _station_x = _hub_bank_x + TILE_SIZE * 2 + TILE_SIZE  # one tile gap past bank
        self.stations = []
        self.stations.append(Station(_station_x, _hub_bank_y, "furnace", "Furnace"))
        self.stations.append(
            Station(_station_x, _hub_bank_y + TILE_SIZE * 2, "workbench", "Workbench")
        )
        self.stations.append(
            Station(_station_x, _hub_bank_y + TILE_SIZE * 4, "stove", "Stove")
        )

        self.crops = []
        self.recipe_manager = RecipeManager()

        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT)
        self.ui = UIManager(self.player)
        self.action_manager = ActionManager(self.ui)
        self.last_tick = pygame.time.get_ticks()
        self._last_frame_ms = 0.0
        self.show_fps_overlay = True  # F3 toggles; issue #10 dev diagnostics

        self.running = True
        self.game_over = False

    def _generate_resources(self):
        for _ in range(NUM_TREES):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceNode(rx, ry, "tree", 20, "axe", "wood", hp=5, respawn_time=15000, min_level=1))
            
        for _ in range(NUM_ROCKS):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceNode(rx, ry, "rock", 35, "pickaxe", "stone", hp=3, respawn_time=20000, min_level=1))

        for _ in range(NUM_IRON_ROCKS):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceNode(rx, ry, "iron_rock", 50, "pickaxe", "iron_ore", hp=3, respawn_time=30000, min_level=5))

        for _ in range(NUM_BUSHES):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceNode(rx, ry, "bush", 10, None, "fiber", hp=2, respawn_time=10000, min_level=1))

        for _ in range(NUM_FISHING_SPOTS):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceNode(rx, ry, "fishing_spot", 25, "rod", "raw_fish", hp=3, respawn_time=20000, min_level=1))

    def _generate_enemies(self):
        for _ in range(NUM_ENEMIES):
            ex = random.randint(50, MAP_WIDTH - 50)
            ey = random.randint(50, MAP_HEIGHT - 50)
            self.enemies.append(Enemy(ex, ey))

    def _restart(self):
        self.game_over = False
        self.player = Player(PLAYER_START_X, PLAYER_START_Y, self)
        self.resources = []
        self._generate_resources()
        self.enemies = []
        self._generate_enemies()
        self.projectiles = []
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT)
        self.ui = UIManager(self.player)
        self.action_manager = ActionManager(self.ui)
        self.last_tick = pygame.time.get_ticks()

    def run(self):
        while self.running:
            frame_ms = float(self.clock.tick(FPS))
            self._last_frame_ms = frame_ms
            dt = frame_ms / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            
        pygame.quit()

    def handle_world_click(self, pos, button):
        # Convert screen pos to world pos
        world_x = pos[0] + self.camera.camera_rect.x
        world_y = pos[1] + self.camera.camera_rect.y
        
        click_rect = pygame.Rect(world_x - 5, world_y - 5, 10, 10)
        clicked_entity = None
        
        # Check if an entity was clicked
        # Resources / Items
        for item in self.resources:
            if click_rect.colliderect(item.rect):
                clicked_entity = item
                break
                
        # Enemies
        if not clicked_entity:
            for enemy in self.enemies:
                if click_rect.colliderect(enemy.rect):
                    clicked_entity = enemy
                    break
                    
        # Bank
        if not clicked_entity:
            if click_rect.colliderect(self.bank.rect):
                clicked_entity = self.bank
                
        # Stations
        if not clicked_entity:
            for station in self.stations:
                if click_rect.colliderect(station.rect):
                    clicked_entity = station
                    break
                    
        # Crops
        if not clicked_entity:
             for crop in self.crops:
                 if click_rect.colliderect(crop.rect):
                     clicked_entity = crop
                     break

        obstacles = self._get_solid_obstacles()
        path = find_path(
            (self.player.rect.centerx, self.player.rect.centery),
            (world_x, world_y),
            obstacles
        )
        self.player.set_target_destination(world_x, world_y, target_entity=clicked_entity, waypoints=path or None)

            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEWHEEL:
                if self.ui.show_skills:
                    self.ui.scroll_skills(event.y)
            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                action, index = self.ui.handle_mouse_event(event)
                if action == "use_item":
                    active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0]
                    if 0 <= index < len(active_items):
                        item_name, _ = active_items[index]
                        success, msg = self.player.use_item(item_name)
                        if success:
                            self.ui.show_message(msg)
                        else:
                            self.ui.show_message("Cannot use this item.")
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
                        self.player.bank_inventory.remove_item(item_name, 1)
                        self.player.inventory.add_item(item_name, 1)
                elif action == "drop_item":
                    active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0]
                    if 0 <= index < len(active_items):
                        item_name, _ = active_items[index]
                        self.player.inventory.remove_item(item_name, 1)
                        drop_x = self.player.rect.centerx + random.randint(-20, 20)
                        drop_y = self.player.rect.centery + random.randint(-20, 20)
                        self.resources.append(ResourceItem(drop_x, drop_y, item_name))
                        self.ui.show_message(f"Dropped 1 {item_name.replace('_', ' ').title()}")
                elif action == "craft_item":
                    # For normal crafting menu
                    recipes = self.recipe_manager.get_handcrafted()
                    if 0 <= index < len(recipes):
                        recipe = recipes[index]
                        skill_name = recipe.get("skill", "crafting")
                        skill_level = getattr(self.player.skills, skill_name, self.player.skills.crafting).level
                        success, result = self.player.inventory.craft(recipe["name"], skill_level, self.recipe_manager)
                        if success:
                            self.player.skills.gain_xp(skill_name, result)
                            self.ui.show_message(f"{recipe['label']} crafted! (+{result} {skill_name.capitalize()} XP)")
                        else:
                            self.ui.show_message(result)
                elif action is None and event.type == pygame.MOUSEBUTTONDOWN:
                     if not (self.ui.show_inventory or self.ui.show_crafting or self.ui.active_bank or self.ui.show_skills or getattr(self.ui, 'active_station', None)):
                         if event.button == 1: # Left click moves
                             self.handle_world_click(event.pos, event.button)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F3:
                    self.show_fps_overlay = not self.show_fps_overlay
                    continue
                if event.mod & pygame.KMOD_CTRL and event.key == pygame.K_q:
                    self.running = False
                    continue
                if self.game_over:
                    if event.key == pygame.K_r: self._restart()
                    continue

                if self.ui.show_skills and event.key == pygame.K_ESCAPE:
                    self.ui.show_skills = False
                    continue
                
                if self.ui.show_inventory:
                    self._handle_inventory_input(event)
                elif self.ui.show_crafting:
                    self._handle_crafting_input(event)
                elif self.ui.active_bank:
                    self._handle_bank_input(event)
                elif getattr(self.ui, 'active_station', None):
                    self._handle_station_input(event)
                else:
                    self._handle_main_input(event)

    def _handle_crafting_input(self, event):
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_c:
            self.ui.show_crafting = False
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
                        self.player.skills.gain_xp(skill_name, result)
                        self.ui.show_message(f"{recipe['label']} crafted! (+{result} {skill_name.capitalize()} XP)")
                    else:
                        self.ui.show_message(result)

    def _handle_inventory_input(self, event):
        active_items = [(item, count) for item, count in self.player.inventory.items.items() if count > 0]
        
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
            self.ui.show_inventory = False
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
                if success:
                    self.ui.show_message(msg)
                else:
                    self.ui.show_message("Cannot use this item.")
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
            self.ui.show_crafting = True
            self.ui.show_skills = False
            self.ui.show_inventory = False
            self.ui.crafting_index = 0
        elif event.key == pygame.K_k:
            self.ui.show_skills = not self.ui.show_skills
            if self.ui.show_skills:
                self.ui.reset_skills_scroll()
                self.ui.show_crafting = False
                self.ui.show_inventory = False
        elif event.key == pygame.K_i:
            self.ui.show_inventory = not self.ui.show_inventory
            if self.ui.show_inventory:
                self.ui.show_crafting = False
                self.ui.show_skills = False
        elif event.key == pygame.K_RETURN:
            # Use/Equip first viable item (simple priority)
            for item in ["bread", "iron_armor", "iron_sword", "sword"]:
                success, msg = self.player.use_item(item)
                if success:
                    self.ui.show_message(msg)
                    return
            self.ui.show_message("No usable item in inventory.")
        elif event.key == pygame.K_TAB:
            self.ui.show_combat_tab = not self.ui.show_combat_tab
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
            self.ui.active_bank = True
            self.ui.show_message("Opened bank vault.")
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
                        leveled_up = self.player.skills.gain_xp(skill_name, xp_total)
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
                    self.player.inventory.add_item(item.resource_type, 1)
                    self.ui.show_message(f"Picked up 1 {item.resource_type}!")
                    self.resources.remove(item)
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
                self.crops.remove(target_crop)
                self.player.inventory.add_item("wheat", 3)
                if self.player.skills.gain_xp("farming", 20):
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

    def _on_enemy_defeated_xp(self):
        """+20 Constitution always; +20 to combat style's primary/secondary skill per kill."""
        notes = []
        # Constitution always
        if self.player.skills.gain_xp("constitution", 20):
            self.player.max_hp += 10
            self.player.hp = min(self.player.hp + 10, self.player.max_hp)
            notes.append("Constitution level up! +10 HP")
        # Style-routed kill bonus
        primary, secondary = self.player.get_xp_skill_for_hit()
        if self.player.skills.gain_xp(primary, 20):
            if primary == "strength":
                self.player.base_attack += 2
                notes.append("Strength level up! +2 ATK")
            else:
                notes.append(f"{primary.capitalize()} level up!")
        if secondary and self.player.skills.gain_xp(secondary, 10):
            notes.append(f"{secondary.capitalize()} level up!")
        if notes:
            self.ui.show_message("Enemy defeated! " + " ".join(notes))
        else:
            self.ui.show_message("Enemy defeated!")

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
            # Immediate hit
            dmg = self.player.get_attack()
            nearest.hp -= dmg
            primary, secondary = self.player.get_xp_skill_for_hit()
            self.player.skills.gain_xp(primary, 5)
            if secondary:
                self.player.skills.gain_xp(secondary, 2)
            self.ui.add_hit_splat(dmg, nearest.rect.centerx, nearest.rect.top, self.camera)
            self.ui.show_message(f"Hit enemy for {dmg}!")
            if nearest.hp <= 0:
                self.enemies.remove(nearest)
                self.resources.append(ResourceItem(nearest.rect.x, nearest.rect.y, "wood"))
                self._on_enemy_defeated_xp()
                return
        # Set up auto-attack loop toward nearest enemy
        self.player.set_target_destination(
            nearest.rect.centerx, nearest.rect.centery, target_entity=nearest)

    def _get_solid_obstacles(self):
        obstacles = []
        for item in self.resources:
            if isinstance(item, ResourceNode) and item.is_active and item.node_type != "fishing_spot":
                obstacles.append(item.rect)
        for station in self.stations:
            obstacles.append(station.rect)
        obstacles.append(self.bank.rect)
        return obstacles

    def update(self, dt):
        if self.player.hp > 0:
            obstacles = self._get_solid_obstacles()
            if not self.ui.show_crafting:
                self.player.update(dt, obstacles)
            
            for crop in self.crops:
                crop.update()
                
            for station in self.stations:
                station.update()
            
            # Action Manager Ticks (once per 1000ms)
            current_time = pygame.time.get_ticks()
            if current_time - self.last_tick >= 1000:
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
                    else:
                        # Melee branch
                        attack_rect = self.player.rect.inflate(80, 80)
                        if attack_rect.colliderect(enemy.rect):
                            dmg = self.player.get_attack()
                            enemy.hp -= dmg
                            primary, secondary = self.player.get_xp_skill_for_hit()
                            self.player.skills.gain_xp(primary, 5)
                            if secondary:
                                self.player.skills.gain_xp(secondary, 2)
                            self.ui.add_hit_splat(dmg, enemy.rect.centerx, enemy.rect.top, self.camera)
                            self.ui.show_message(f"Hit enemy for {dmg}!")
                            if enemy.hp <= 0:
                                self.enemies.remove(enemy)
                                self.resources.append(ResourceItem(enemy.rect.x, enemy.rect.y, "wood"))
                                self._on_enemy_defeated_xp()
                                self.player.current_action = None
                                self.player.action_target = None
                        else:
                            # Enemy moved — keep attack state and chase them
                            self.player.target_destination = (enemy.rect.centerx, enemy.rect.centery)
                            self.player.waypoints = []

            # Nodes updates (respawn ticks)
            for item in self.resources:
                if isinstance(item, ResourceNode):
                    item.update()
            
            for enemy in self.enemies:
                enemy.update(self.player, dt, obstacles + [self.player.rect])
                if enemy.rect.inflate(4, 4).colliderect(self.player.rect):
                    if self.player.take_damage(10):
                        self.player.skills.gain_xp("defense", 3)
                        self.ui.show_message("-10 HP!")

            for proj in self.projectiles[:]:
                proj.update(dt)
                if proj.hit:
                    if proj.target in self.enemies:
                        proj.target.hp -= proj.damage
                        primary, secondary = self.player.get_xp_skill_for_hit()
                        leveled_up = self.player.skills.gain_xp(primary, 4)
                        if secondary:
                            self.player.skills.gain_xp(secondary, 2)
                        self.ui.add_hit_splat(proj.damage, proj.target.rect.centerx, proj.target.rect.top, self.camera)
                        self.ui.show_message(f"Ranged hit for {proj.damage}!")
                        if leveled_up:
                            lvl = getattr(self.player.skills, primary).level
                            self.ui.show_message(f"{primary.capitalize()} level up! Now level {lvl}")
                        if proj.target.hp <= 0:
                            self.enemies.remove(proj.target)
                            self.resources.append(ResourceItem(proj.target.rect.x, proj.target.rect.y, "wood"))
                            self._on_enemy_defeated_xp()
                            self.player.current_action = None
                            self.player.action_target = None
                    self.projectiles.remove(proj)
        else:
            if not self.game_over:
                self.game_over = True
            
        self.camera.update(self.player)
        self.ui.update()

    def draw(self):
        self.screen.fill((0, 0, 0))
        # Draw Map background 
        pygame.draw.rect(self.screen, (20, 50, 20), self.camera.apply(pygame.Rect(0, 0, 2400, 2400))) 
        # Draw ground-level objects first (no Y-sort needed)
        for item in self.resources:
            item.draw(self.screen, self.camera)
        for crop in self.crops:
            crop.draw(self.screen, self.camera)
        for proj in self.projectiles:
            proj.draw(self.screen, self.camera)

        # Y-sort entities so lower ones draw on top (correct depth)
        y_sorted = sorted(
            self.stations + self.enemies + [self.bank, self.player],
            key=lambda e: e.rect.bottom
        )
        for entity in y_sorted:
            entity.draw(self.screen, self.camera)
        self.ui.draw(self.screen)
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