import pygame
import os
from src.inventory import Inventory

class Player: 
    def __init__(self, x, y): #* __init__ is the constructor for the Player class
        self.rect = pygame.Rect(x, y, 32, 32) 
        self.color = (0, 128, 255)
        self.speed = 4
        self.inventory = Inventory()
        
        self.image = None
        sprite_path = os.path.join("assets", "sprites", "player.png")
        if os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
            except pygame.error:
                pass

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.rect.y += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            
        self.rect.clamp_ip(pygame.Rect(0, 0, 800, 600))

    def draw(self, surface): #* draw function is used to draw the player character on the screen
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.rect(surface, self.color, self.rect)













