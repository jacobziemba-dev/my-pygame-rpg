import pygame
import random
from src.player import Player
from src.resource_item import ResourceItem
from src.ui import UIManager

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
        
        self.ui = UIManager(self.player.inventory)
        
        self.running = True

    def _generate_resources(self):
        for _ in range(10):
            rx = random.randint(50, 750)
            ry = random.randint(50, 550)
            self.resources.append(ResourceItem(rx, ry, "wood"))
            
        for _ in range(10):
            rx = random.randint(50, 750)
            ry = random.randint(50, 550)
            self.resources.append(ResourceItem(rx, ry, "stone"))

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
                if event.key == pygame.K_e:
                    # Collect resource
                    for item in self.resources[:]:
                        if self.player.rect.colliderect(item.rect):
                            self.resources.remove(item)
                            self.player.inventory.add_item(item.resource_type, 1)
                            self.ui.show_message(f"Collected {item.resource_type}!")
                elif event.key == pygame.K_c:
                    # Craft sword
                    if self.player.inventory.craft("sword"):
                        self.ui.show_message("Success! Sword crafted.")
                    else:
                        self.ui.show_message("Failed to craft sword. Need 1 wood and 1 stone.")

    def update(self):
        self.player.update()
        self.ui.update()

    def draw(self):
        self.screen.fill((0, 0, 0))
        for item in self.resources:
            item.draw(self.screen)
        self.player.draw(self.screen)
        self.ui.draw(self.screen)
        pygame.display.update()
