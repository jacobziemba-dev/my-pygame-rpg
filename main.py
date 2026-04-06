from src.core.game_manager import GameManager
import pygame

if __name__ == "__main__":
    game = GameManager()
    try:
        game.run()
    except KeyboardInterrupt:
        # Allow clean terminal exits without traceback spam.
        pygame.quit()



# main function to run the game this calls the game manager and runs the game
