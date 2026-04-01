import pygame


class Player: 
    def __init__(self, x, y): #* __init__ is the constructor for the Player class
        self.rect = pygame.Rect(x, y, 32, 32) 
        self.color = (0, 128, 255)

    def draw(self, surface): #* draw function is used to draw the player character on the screen
        pygame.draw.rect(surface, self.color, self.rect)

















#NOTES: ========================================================================================================================== 
# when creating a new Python file, you should name it with a descriptive, short, and lowercase name, using underscores if needed.
# for example:
#   player.py            # for a file containing the Player class
#   main.py              # for the main entry point (like this one)
#   game_logic.py        # for game logic code
# avoid spaces and special characters. Always end the filename with '.py'.   
#NOTES: ========================================================================================================================== 
