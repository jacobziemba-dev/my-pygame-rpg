import pygame
import os
import math
from src.core.settings import *

class TileMap:
    def __init__(self, game_manager):
        self.gm = game_manager
        self.width = MAP_WIDTH // TILE_SIZE
        self.height = MAP_HEIGHT // TILE_SIZE
        self.world_map = [[TILE_GRASS for _ in range(self.height)] for _ in range(self.width)]
        
        self.show_grid = False
        
        self.textures = {}
        self._load_textures()
        self.generate_map()

    def _load_textures(self):
        try:
            self.textures[TILE_GRASS] = pygame.image.load(os.path.join("assets", "sprites", "world", "grass.png")).convert()
            self.textures[TILE_DIRT] = pygame.image.load(os.path.join("assets", "sprites", "world", "dirt.png")).convert()
            self.textures[TILE_WATER] = pygame.image.load(os.path.join("assets", "sprites", "world", "water.png")).convert()
            
            # Ensure they are TILE_SIZE
            for k in self.textures:
                if self.textures[k].get_size() != (TILE_SIZE, TILE_SIZE):
                    self.textures[k] = pygame.transform.scale(self.textures[k], (TILE_SIZE, TILE_SIZE))
        except:
            print("Warning: Could not load some tile textures.")
            # Fallbacks are handled in draw()

    def generate_map(self):
        """Procedural generation of the world map."""
        for x in range(self.width):
            for y in range(self.height):
                # Circular island logic: Water at edges
                dist_center = math.hypot(x - self.width/2, y - self.height/2)
                if dist_center > min(self.width, self.height) * 0.45:
                    self.world_map[x][y] = TILE_WATER
                else:
                    # Simple noise for dirt patches
                    noise = math.sin(x * 0.2) + math.cos(y * 0.2) + math.sin((x+y)*0.1)
                    if noise > 1.2:
                        self.world_map[x][y] = TILE_DIRT
                    else:
                        self.world_map[x][y] = TILE_GRASS
        # Map changed, refresh cached collision geometry
        self._rebuild_collision_cache()

    def _rebuild_collision_cache(self):
        """Precompute collision rects for water tiles.

        GameManager/pathfinding queries these frequently; caching avoids allocating
        thousands of Rects repeatedly.
        """
        self.water_rects = []
        self.water_rect_rows = [[] for _ in range(self.height)]
        for x in range(self.width):
            for y in range(self.height):
                if self.world_map[x][y] == TILE_WATER:
                    r = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    self.water_rects.append(r)
                    self.water_rect_rows[y].append(r)

    def get_water_rects_in_world_rect(self, world_rect, padding_px=0):
        """Return cached water rects intersecting a region (plus padding)."""
        if padding_px:
            region = pygame.Rect(
                world_rect.x - padding_px,
                world_rect.y - padding_px,
                world_rect.w + padding_px * 2,
                world_rect.h + padding_px * 2,
            )
        else:
            region = world_rect

        y0 = max(0, region.top // TILE_SIZE)
        y1 = min(self.height - 1, (region.bottom - 1) // TILE_SIZE)
        out = []
        for y in range(y0, y1 + 1):
            for r in self.water_rect_rows[y]:
                if r.colliderect(region):
                    out.append(r)
        return out

    def is_walkable(self, world_x, world_y):
        """Check if a world coordinate is walkable (not water)."""
        grid_x = int(world_x // TILE_SIZE)
        grid_y = int(world_y // TILE_SIZE)
        
        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            return self.world_map[grid_x][grid_y] != TILE_WATER
        return False

    def get_tile_rects_by_type(self, tile_type):
        """Return a list of rects for all tiles of a specific type.
        Useful for building the obstacles list."""
        rects = []
        for x in range(self.width):
            for y in range(self.height):
                if self.world_map[x][y] == tile_type:
                    rects.append(pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return rects

    def draw(self, surface, camera):
        cam_x = camera.camera_rect.x
        cam_y = camera.camera_rect.y
        
        # Calculate visible tiles
        start_cx = max(0, cam_x // TILE_SIZE)
        end_cx = min(self.width, (cam_x + surface.get_width()) // TILE_SIZE + 1)
        start_cy = max(0, cam_y // TILE_SIZE)
        end_cy = min(self.height, (cam_y + surface.get_height()) // TILE_SIZE + 1)
        
        for x in range(start_cx, end_cx):
            for y in range(start_cy, end_cy):
                tile_type = self.world_map[x][y]
                tex = self.textures.get(tile_type)
                
                screen_x = x * TILE_SIZE - cam_x
                screen_y = y * TILE_SIZE - cam_y
                
                if tex:
                    surface.blit(tex, (screen_x, screen_y))
                else:
                    # Fallback colors
                    color = (34, 139, 34) if tile_type == TILE_GRASS else (101, 67, 33)
                    if tile_type == TILE_WATER: color = (0, 105, 148)
                    pygame.draw.rect(surface, color, (screen_x, screen_y, TILE_SIZE, TILE_SIZE))
                
                # Draw grid if enabled
                if self.show_grid:
                    pygame.draw.rect(surface, (255, 255, 255, 50), (screen_x, screen_y, TILE_SIZE, TILE_SIZE), 1)

    def toggle_grid(self):
        self.show_grid = not self.show_grid
