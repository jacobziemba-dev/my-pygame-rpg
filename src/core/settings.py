import pygame

# Display settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "My Pygame RPG"

# World settings
MAP_WIDTH = 2400
MAP_HEIGHT = 2400
TILE_SIZE = 32

# Player settings
PLAYER_START_X = 400
PLAYER_START_Y = 300
PLAYER_SPEED = 4
PLAYER_MAX_HP = 100

# Entity colors
COLOR_PLAYER = (0, 128, 255)
COLOR_ENEMY = (255, 0, 0)

# Resource settings
NUM_TREES = 15
NUM_ROCKS = 10
NUM_IRON_ROCKS = 8
NUM_BUSHES = 10
NUM_FISHING_SPOTS = 6
NUM_CHESTS = 5

# Combat settings
RANGED_ATTACK_RANGE = 250  # px; used when bow is equipped
NUM_ENEMIES = 15
