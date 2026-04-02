import pygame


class Player: 
    def __init__(self, x, y): #* __init__ is the constructor for the Player class
        self.rect = pygame.Rect(x, y, 32, 32) 
        self.color = (0, 128, 255)

    def draw(self, surface): #* draw function is used to draw the player character on the screen
        pygame.draw.rect(surface, self.color, self.rect)













