import pygame
import os
from src.core.settings import *
from src.core.utils import load_frames_from_sheet, get_path


class ResourceNode:
    def __init__(self, x, y, node_type, difficulty, tool_required, yields, hp, respawn_time, min_level=1):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        self.node_type = node_type
        self.difficulty = difficulty
        self.tool_required = tool_required
        self.yields = yields
        self.max_hp = hp
        self.hp = hp
        self.respawn_time = respawn_time
        self.min_level = min_level
        self.dead_timer = 0
        self.is_active = True

        self.image = None
        self._tree_frames = []
        self._tree_phase = 0.0
        self._tree_anim_speed = 0.055

        sprite_path = os.path.join("assets", "sprites", f"{self.node_type}.png")

        if node_type == "tree":
            tree_path = get_path("assets/sprites/tree.png")
            if os.path.exists(tree_path):
                try:
                    sheet = pygame.image.load(tree_path).convert_alpha()
                    w, h = sheet.get_width(), sheet.get_height()
                    # One row of square cells: frame size = row height (width // frame_size = frame count).
                    if h > 0 and w >= h:
                        frame_sz = h
                        frames = load_frames_from_sheet(
                            "assets/sprites/tree.png",
                            frame_sz,
                            scale_to=(TILE_SIZE, TILE_SIZE),
                            frame_height=frame_sz,
                        )
                        if frames:
                            self._tree_frames = frames
                            self.image = frames[0]
                except pygame.error:
                    pass
        elif os.path.exists(sprite_path):
            try:
                self.image = pygame.image.load(sprite_path).convert_alpha()
                self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
            except pygame.error:
                pass

        if node_type == "tree":
            self.active_color = (0, 200, 0)
        elif node_type == "iron_rock":
            self.active_color = (180, 80, 20)
        elif node_type == "bush":
            self.active_color = (34, 139, 34)
        elif node_type == "fishing_spot":
            self.active_color = (30, 144, 255)
        else:
            self.active_color = (150, 150, 150)
        self.dead_color = (100, 100, 100)

    def update(self, dt=0):
        if not self.is_active:
            current_time = pygame.time.get_ticks()
            if current_time - self.dead_timer >= self.respawn_time:
                self.respawn()
            return

        if self._tree_frames:
            n = len(self._tree_frames)
            self._tree_phase += self._tree_anim_speed * dt * 60
            self._tree_phase %= n
            self.image = self._tree_frames[int(self._tree_phase)]

    def take_hit(self):
        self.hp -= 1
        if self.hp <= 0:
            self.is_active = False
            self.dead_timer = pygame.time.get_ticks()

    def respawn(self):
        self.is_active = True
        self.hp = self.max_hp

    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.is_active:
            if self.image:
                surface.blit(self.image, draw_rect)
            else:
                pygame.draw.rect(surface, self.active_color, draw_rect)
        else:
            pygame.draw.rect(surface, self.dead_color, draw_rect)
