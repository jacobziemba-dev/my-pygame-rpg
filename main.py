
#TODO: - player class 
    #TODO: - Add a way to move the player character
    #TODO: - Add a way to jump the player character

#TODO: - Add a way to win the game
#TODO: - Add a way to lose the game
#TODO: - Add a way to restart the game
#TODO: - Add a way to quit the game

import pygame 
from src import Player # import the Player class 



pygame.init() #* initialize pygame

# Display setup
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My Pygame RPG")
clock = pygame.time.Clock() # limit frame rate




player = Player(400, 300) # create a player character at the center of the screen

running = True # controls main loop




# Main loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: # handle quit
            running = False

    screen.fill((0, 0, 0)) # clear screen

    player.draw(screen) #* draw the player character on the screen
    

    pygame.display.update() # update display

    clock.tick(60) # 60 fps

pygame.quit()
