import pygame
import random
from src.player import Player
from src.resource_item import ResourceItem
from src.resource_node import ResourceNode
from src.ui import UIManager
from src.enemy import Enemy
from src.camera import Camera
from src.save_manager import SaveManager
from src.action_manager import ActionManager
from src.inventory import RECIPES

class GameManager:
    def __init__(self):
        pygame.init()
        
        # Display setup
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("My Pygame RPG")
        self.clock = pygame.time.Clock()
        
        # Game objects
        self.player = Player(400, 300)
        self.resources = []
        self._generate_resources()
        
        self.enemies = []
        self._generate_enemies()
        
        self.camera = Camera(800, 600, 2400, 2400)
        self.ui = UIManager(self.player)
        self.action_manager = ActionManager(self.ui)
        self.last_tick = pygame.time.get_ticks()
        
        self.running = True

    def _generate_resources(self):
        for _ in range(15):
            rx = random.randint(50, 2350)
            ry = random.randint(50, 2350)
            self.resources.append(ResourceNode(rx, ry, "tree", 20, "axe", "wood", hp=5, respawn_time=15000))
            
        for _ in range(10):
            rx = random.randint(50, 2350)
            ry = random.randint(50, 2350)
            self.resources.append(ResourceNode(rx, ry, "rock", 35, "pickaxe", "stone", hp=3, respawn_time=20000))

        for _ in range(8):
            rx = random.randint(50, 2350)
            ry = random.randint(50, 2350)
            self.resources.append(ResourceNode(rx, ry, "iron_rock", 50, "pickaxe", "iron_ore", hp=3, respawn_time=30000))
            
        for _ in range(5):
            rx = random.randint(50, 2350)
            ry = random.randint(50, 2350)
            self.resources.append(ResourceItem(rx, ry, "chest"))

    def _generate_enemies(self):
        for _ in range(15):
            ex = random.randint(50, 2350)
            ey = random.randint(50, 2350)
            self.enemies.append(Enemy(ex, ey))

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
                if event.key == pygame.K_e:
                    # Collect resource or start action
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
            self.ui.show_message("GAME OVER. Restart application.")
            
        self.camera.update(self.player)
        self.ui.update()

    def draw(self):
        self.screen.fill((0, 0, 0))
        # Draw Map background 
        pygame.draw.rect(self.screen, (20, 50, 20), self.camera.apply(pygame.Rect(0, 0, 2400, 2400))) 
        for item in self.resources:
            item.draw(self.screen, self.camera)
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera)
        self.player.draw(self.screen, self.camera)
        self.ui.draw(self.screen)
        pygame.display.update()
