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
NUM_COAL_ROCKS = 8
NUM_ESSENCE_ROCKS = 15

# Combat settings
RANGED_ATTACK_RANGE = 250  # px; used when bow is equipped

# Equipment/tool wield requirements keyed by item id.
EQUIPMENT_REQUIREMENTS = {
    "iron_sword": ("attack", 5),
    "iron_armor": ("defense", 10),
    "iron_axe": ("attack", 5),
    "iron_pickaxe": ("attack", 5),
    "steel_sword": ("attack", 20),
    "steel_armor": ("defense", 20),
    "steel_axe": ("attack", 20),
    "steel_pickaxe": ("attack", 20),
    "staff_of_air": ("magic", 1),
}

# Enemy type definitions
# drops: list of (item_name, min_amount, max_amount, chance)
ENEMY_TYPE_STATS = {
    "goblin": {
        "name": "Goblin",
        "combat_level": 2,
        "hp": 5,
        "defense_level": 1,
        "max_hit": 1,
        "speed": 1.8,
        "aggro_range": 200,
        "color": (100, 140, 50),
        "drops": [("bones", 1, 1, 1.0), ("coins", 1, 3, 0.6)],
        "respawn_time": 25000,
        "xp_reward": 13,
    },
    "skeleton": {
        "name": "Skeleton",
        "combat_level": 13,
        "hp": 21,
        "defense_level": 6,
        "max_hit": 4,
        "speed": 2.2,
        "aggro_range": 280,
        "color": (215, 210, 190),
        "drops": [("bones", 1, 1, 1.0), ("coins", 3, 8, 0.4)],
        "respawn_time": 45000,
        "xp_reward": 50,
    },
    "guard": {
        "name": "Guard",
        "combat_level": 22,
        "hp": 35,
        "defense_level": 16,
        "max_hit": 6,
        "speed": 2.0,
        "aggro_range": 180,
        "color": (60, 70, 150),
        "drops": [("bones", 1, 1, 1.0), ("coins", 8, 20, 0.8), ("iron_bar", 1, 1, 0.1)],
        "respawn_time": 60000,
        "xp_reward": 88,
    },
}

NUM_GOBLINS   = 8
NUM_SKELETONS = 4
NUM_GUARDS    = 3
