import pygame
import os
from src.core.utils import import_folder

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, game_manager=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        self.game_manager = game_manager
        self.image = None
        self.animations = {}
        self.status = 'idle'
        self.frame_index = 0
        self.animation_speed = 0.15

    def load_animations(self, base_path, frame_size):
        for animation in self.animations.keys():
            full_path = os.path.join(base_path, animation)
            frames = import_folder(full_path)
            self.animations[animation] = [pygame.transform.scale(f, frame_size) for f in frames]

    def animate(self, dt):
        animation = self.animations.get(self.status, [])
        if not animation:
            return

        self.frame_index += self.animation_speed * dt * 60
        if self.frame_index >= len(animation):
            self.frame_index = 0

        self.image = animation[int(self.frame_index)]

    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        if self.image:
            surface.blit(self.image, draw_rect)
        elif hasattr(self, 'color'):
            pygame.draw.rect(surface, self.color, draw_rect)


def resolve_collision_x(rect, obstacles):
    for obs in obstacles:
        if rect.colliderect(obs):
            if rect.centerx < obs.centerx:
                rect.right = obs.left
            else:
                rect.left = obs.right


def resolve_collision_y(rect, obstacles):
    for obs in obstacles:
        if rect.colliderect(obs):
            if rect.centery < obs.centery:
                rect.bottom = obs.top
            else:
                rect.top = obs.bottom


def depenetrate_rect(rect, obstacles, max_passes=8):
    """
    Resolve remaining AABB overlap after axis sliding (corner / multi-tile wedging).
    Uses shallow overlap on X vs Y to pick separation axis each step.
    """
    for _ in range(max_passes):
        moved = False
        for obs in obstacles:
            if not rect.colliderect(obs):
                continue
            ox = min(rect.right, obs.right) - max(rect.left, obs.left)
            oy = min(rect.bottom, obs.bottom) - max(rect.top, obs.top)
            if ox <= 0 or oy <= 0:
                continue
            if ox < oy:
                if rect.centerx < obs.centerx:
                    rect.x -= ox
                else:
                    rect.x += ox
            else:
                if rect.centery < obs.centery:
                    rect.y -= oy
                else:
                    rect.y += oy
            moved = True
        if not moved:
            break
