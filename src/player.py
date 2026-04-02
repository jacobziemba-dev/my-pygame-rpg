import pygame
from src.inventory import Inventory

class Player: 
    def __init__(self, x, y): #* __init__ is the constructor for the Player class
        self.rect = pygame.Rect(x, y, 32, 32) 
        self.color = (0, 128, 255)
        self.speed = 4
        self.inventory = Inventory()

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
        pygame.draw.rect(surface, self.color, self.rect)













