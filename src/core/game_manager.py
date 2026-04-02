import pygame
import random
from src.entities.player import Player
from src.entities.resource_item import ResourceItem
from src.entities.resource_node import ResourceNode
from src.ui.ui import UIManager
from src.entities.enemy import Enemy
from src.entities.chest import Chest
from src.entities.crop import Crop
from src.core.camera import Camera
from src.systems.save_manager import SaveManager
from src.systems.action_manager import ActionManager
from src.systems.inventory import RECIPES
from src.core.settings import *

class GameManager:
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.player = Player(PLAYER_START_X, PLAYER_START_Y)
        self.player.game_manager = self
        self.resources = []
        self._generate_resources()
        
        self.enemies = []
        self._generate_enemies()

        self.placed_chests = []
        self.crops = []
        
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT)
        self.ui = UIManager(self.player)
        self.action_manager = ActionManager(self.ui)
        self.last_tick = pygame.time.get_ticks()
        
        self.running = True
        self.game_over = False

    def _generate_resources(self):
        for _ in range(NUM_TREES):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceNode(rx, ry, "tree", 20, "axe", "wood", hp=5, respawn_time=15000))
            
        for _ in range(NUM_ROCKS):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceNode(rx, ry, "rock", 35, "pickaxe", "stone", hp=3, respawn_time=20000))

        for _ in range(NUM_IRON_ROCKS):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceNode(rx, ry, "iron_rock", 50, "pickaxe", "iron_ore", hp=3, respawn_time=30000))
            
        for _ in range(NUM_CHESTS):
            rx = random.randint(50, MAP_WIDTH - 50)
            ry = random.randint(50, MAP_HEIGHT - 50)
            self.resources.append(ResourceItem(rx, ry, "chest"))

    def _generate_enemies(self):
        for _ in range(NUM_ENEMIES):
            ex = random.randint(50, MAP_WIDTH - 50)
            ey = random.randint(50, MAP_HEIGHT - 50)
            self.enemies.append(Enemy(ex, ey))

    def _restart(self):
        self.game_over = False
        self.player = Player(PLAYER_START_X, PLAYER_START_Y)
        self.player.game_manager = self
        self.resources = []
        self._generate_resources()
        self.enemies = []
        self._generate_enemies()
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, MAP_WIDTH, MAP_HEIGHT)
        self.ui = UIManager(self.player)
        self.action_manager = ActionManager(self.ui)
        self.last_tick = pygame.time.get_ticks()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
            
        pygame.quit()
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # Game over screen — only listen for R to restart
                if self.game_over:
                    if event.key == pygame.K_r:
                        self._restart()
                    continue
                # Crafting menu consumes input when open
                if self.ui.show_crafting:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_c:
                        self.ui.show_crafting = False
                    elif event.key == pygame.K_UP:
                        self.ui.crafting_index = max(0, self.ui.crafting_index - 1)
                    elif event.key == pygame.K_DOWN:
                        self.ui.crafting_index = min(len(RECIPES) - 1, self.ui.crafting_index + 1)
                    elif event.key == pygame.K_RETURN:
                        recipe = RECIPES[self.ui.crafting_index]
                        success, result = self.player.inventory.craft(recipe["name"], self.player.skills.crafting.level)
                        if success:
                            self.player.skills.gain_xp("crafting", result)
                            self.ui.show_message(f"{recipe['label']} crafted! (+{result} Crafting XP)")
                        else:
                            self.ui.show_message(result)
                    continue
                # Chest menu consumes input when open
                if self.ui.active_chest:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_e:
                        self.ui.active_chest = False
                    elif event.key == pygame.K_t:
                        # Deposit everything from player inventory to chest
                        for item, count in list(self.player.inventory.items.items()):
                            if count > 0:
                                self.ui.active_chest.inventory.add_item(item, count)
                                self.player.inventory.items[item] = 0
                        self.ui.show_message("Deposited all items into chest.")
                    continue
                if event.key == pygame.K_e:
                    # Collect resource or start action
                    interaction_found = False
                    # Check for chests first
                    for chest in self.placed_chests:
                        if self.player.rect.inflate(10, 10).colliderect(chest.rect):
                            self.ui.active_chest = chest
                            self.ui.show_message("Opened chest storage.")
                            interaction_found = True
                            break
                    
                    if interaction_found:
                        continue

                    for item in self.resources[:]:
                        if self.player.rect.colliderect(item.rect):
                            if isinstance(item, ResourceItem) and item.resource_type == "chest":
                                self.resources.remove(item)
                                self.player.inventory.add_item("wood", 10)
                                self.player.inventory.add_item("stone", 10)
                                self.ui.show_message("Opened Chest! Huge Loot gained.")
                            elif isinstance(item, ResourceItem):
                                self.resources.remove(item)
                                self.player.inventory.add_item(item.resource_type, 1)
                                self.ui.show_message(f"Picked up 1 {item.resource_type}!")
                            elif isinstance(item, ResourceNode) and item.is_active:
                                self.player.current_action = "gathering"
                                self.player.action_target = item
                                self.ui.show_message(f"Started gathering {item.node_type}...")
                            break
                elif event.key == pygame.K_f:
                    # Farming interaction
                    grid_x = (self.player.rect.centerx // TILE_SIZE) * TILE_SIZE
                    grid_y = (self.player.rect.centery // TILE_SIZE) * TILE_SIZE
                    
                    target_crop = next((c for c in self.crops if c.rect.topleft == (grid_x, grid_y)), None)
                    
                    if target_crop:
                        if target_crop.is_mature:
                            self.crops.remove(target_crop)
                            self.player.inventory.add_item("wheat", 3)
                            leveled_up = self.player.skills.gain_xp("farming", 20)
                            self.ui.show_message(f"Harvested {target_crop.crop_type}! (+20 Farming XP)")
                            if leveled_up:
                                self.ui.show_message("Farming Level UP!")
                        else:
                            self.ui.show_message(f"Crop is still growing... (Stage {target_crop.growth_stage}/{target_crop.max_growth})")
                    else:
                        # No crop here, check for tilling or planting
                        if self.player.inventory.items.get("bronze_hoe", 0) > 0:
                            # Plant seed if player has them
                            if self.player.inventory.items.get("wheat_seeds", 0) > 0:
                                new_crop = Crop(grid_x, grid_y)
                                self.crops.append(new_crop)
                                self.player.inventory.remove_item("wheat_seeds", 1)
                                self.ui.show_message("Tilled and planted wheat seeds!")
                            else:
                                self.ui.show_message("Need seeds to plant here.")
                        else:
                            self.ui.show_message("Need a hoe to till this soil.")
                elif event.key == pygame.K_p:
                    # Place a chest if the player has one in inventory
                    if self.player.inventory.items.get("chest_item", 0) > 0:
                        # Find the current tile position (32x32 grid)
                        grid_x = (self.player.rect.centerx // TILE_SIZE) * TILE_SIZE
                        grid_y = (self.player.rect.centery // TILE_SIZE) * TILE_SIZE
                        
                        already_has_chest = any(c.rect.topleft == (grid_x, grid_y) for c in self.placed_chests)
                        if not already_has_chest:
                            new_chest = Chest(grid_x, grid_y)
                            self.placed_chests.append(new_chest)
                            self.player.inventory.remove_item("chest_item", 1)
                            self.ui.show_message(f"Chest placed at ({grid_x}, {grid_y})!")
                        else:
                            self.ui.show_message("Already a chest at this location!")
                    else:
                        self.ui.show_message("No chest in inventory.")
                elif event.key == pygame.K_F5:
                    SaveManager.save_game(self.player, self.resources, self.enemies)
                    self.ui.show_message("Game Saved Successfully!")
                elif event.key == pygame.K_F9:
                    if SaveManager.load_game(self.player, self.resources, self.enemies):
                        self.ui.show_message("Game Loaded Successfully!")
                    else:
                        self.ui.show_message("No Save File found.")
                elif event.key == pygame.K_c:
                    self.ui.show_crafting = True
                    self.ui.show_skills = False
                    self.ui.crafting_index = 0
                elif event.key == pygame.K_RETURN:
                    if self.player.equip("iron_sword"):
                        self.ui.show_message("Iron Sword equipped! Attack +10")
                    elif self.player.equip("sword"):
                        self.ui.show_message("Sword equipped! Attack +5")
                    else:
                        self.ui.show_message("No sword in inventory to equip.")
                elif event.key == pygame.K_k:
                    self.ui.show_skills = not self.ui.show_skills
                    if self.ui.show_skills:
                        self.ui.show_crafting = False
                elif event.key == pygame.K_SPACE:
                    if self.player.hp > 0:
                        attack_rect = self.player.rect.inflate(40, 40)
                        dmg = self.player.get_attack()
                        for enemy in self.enemies[:]:
                            if attack_rect.colliderect(enemy.rect):
                                enemy.hp -= dmg
                                self.ui.show_message(f"Hit enemy for {dmg} damage!")
                                if enemy.hp <= 0:
                                    self.enemies.remove(enemy)
                                    self.resources.append(ResourceItem(enemy.rect.x, enemy.rect.y, "wood"))
                                    leveled_up = self.player.skills.gain_xp("melee", 15)
                                    if leveled_up:
                                        self.player.max_hp += 10
                                        self.player.hp = min(self.player.hp + 10, self.player.max_hp)
                                        self.player.base_attack += 2
                                        self.ui.show_message("Melee level up! +10 HP, +2 ATK")
                                    else:
                                        self.ui.show_message("Enemy defeated! +15 Melee XP")
                                break

    def update(self):
        if self.player.hp > 0:
            if not self.ui.show_crafting:
                self.player.update()
            
            for crop in self.crops:
                crop.update()
            
            # Action Manager Ticks (once per 1000ms)
            current_time = pygame.time.get_ticks()
            if current_time - self.last_tick >= 1000:
                self.last_tick = current_time
                if self.player.current_action == "gathering" and self.player.action_target:
                    self.action_manager.process_gathering_tick(self.player, self.player.action_target)
            
            # Nodes updates (respawn ticks)
            for item in self.resources:
                if isinstance(item, ResourceNode):
                    item.update()
            
            for enemy in self.enemies:
                enemy.update(self.player)
                if enemy.rect.colliderect(self.player.rect):
                    if self.player.take_damage(10):
                        self.ui.show_message("-10 HP!")
        else:
            if not self.game_over:
                self.game_over = True
            
        self.camera.update(self.player)
        self.ui.update()

    def draw(self):
        self.screen.fill((0, 0, 0))
        # Draw Map background 
        pygame.draw.rect(self.screen, (20, 50, 20), self.camera.apply(pygame.Rect(0, 0, 2400, 2400))) 
        for item in self.resources:
            item.draw(self.screen, self.camera)
        for crop in self.crops:
            crop.draw(self.screen, self.camera)
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera)
        for chest in self.placed_chests:
            chest.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        self.ui.draw(self.screen)
        if self.game_over:
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            go_font = pygame.font.SysFont(None, 64)
            go_text = go_font.render("GAME OVER", True, (220, 50, 50))
            self.screen.blit(go_text, go_text.get_rect(center=(400, 270)))
            sub_font = pygame.font.SysFont(None, 32)
            sub_text = sub_font.render("[R] Restart", True, (200, 200, 200))
            self.screen.blit(sub_text, sub_text.get_rect(center=(400, 330)))
        pygame.display.update()
