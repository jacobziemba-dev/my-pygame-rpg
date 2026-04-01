import pygame  # Import the pygame module

pygame.init()  # Initialize all imported pygame modules

# Set up the display window with a size of 800x600 pixels
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My Pygame RPG")  # Set the window title
clock = pygame.time.Clock()  # Create a clock object to manage the game's frame rate

running = True  # Variable to control the game loop

# Main game loop
while running:
    # 1. Handle input/events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Check if the window close button was clicked
            running = False  # End the game loop

    # 2. Update game state
    # (Game logic and updates would go here)

    # 3. Draw everything
    screen.fill((0, 0, 0))  # Fill the screen with black (clear previous frame)

    pygame.display.flip()  # Update the display with everything drawn in this frame

    clock.tick(60)  # Limit the loop to 60 frames per second

pygame.quit()  # Quit pygame and clean up resources