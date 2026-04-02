import pygame 
import random
from src import Player, ResourceItem # import the Player class 



pygame.init() #* initialize pygame

# Display setup
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My Pygame RPG")
clock = pygame.time.Clock() # limit frame rate




player = Player(400, 300) # create a player character at the center of the screen

# Generate resources
resources = []
for _ in range(10):
    rx = random.randint(50, 750)
    ry = random.randint(50, 550)
    resources.append(ResourceItem(rx, ry, "wood"))
    
for _ in range(10):
    rx = random.randint(50, 750)
    ry = random.randint(50, 550)
    resources.append(ResourceItem(rx, ry, "stone"))

running = True # controls main loop




# Main loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: # handle quit
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                for item in resources[:]:
                    if player.rect.colliderect(item.rect):
                        resources.remove(item)
                        player.inventory.add_item(item.resource_type, 1)
                        print(f"Collected {item.resource_type}! Inventory: {player.inventory.items}")
            elif event.key == pygame.K_c:
                if player.inventory.craft("sword"):
                    print(f"Success! Sword crafted. Inventory: {player.inventory.items}")
                else:
                    print("Failed to craft sword. Need 1 wood and 1 stone.")

    screen.fill((0, 0, 0)) # clear screen

    player.update()
    
    for item in resources:
        item.draw(screen)
        
    player.draw(screen) #* draw the player character on the screen
    

    pygame.display.update() # update display

    clock.tick(60) # 60 fps

pygame.quit()
