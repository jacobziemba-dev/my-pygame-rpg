import math
import pygame
from src.core.settings import *
from src.entities.entity import Entity, resolve_collision_x, resolve_collision_y


class Enemy(Entity):
    _label_font = None

    def __init__(self, x, y, enemy_type="goblin"):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE)

        self.enemy_type = enemy_type
        stats = ENEMY_TYPE_STATS.get(enemy_type, ENEMY_TYPE_STATS["goblin"])

        self.name          = stats["name"]
        self.combat_level  = stats["combat_level"]
        self.hp            = stats["hp"]
        self.max_hp        = stats["hp"]
        self.defense_level = stats["defense_level"]
        self.max_hit       = stats["max_hit"]
        self.speed         = stats["speed"]
        self.aggro_range   = stats["aggro_range"]
        self.color         = stats["color"]
        self.drops         = stats["drops"]           # [(item, min, max, chance)]
        self.respawn_time  = stats["respawn_time"]    # ms
        self.xp_reward     = stats["xp_reward"]

        # Remember spawn position so respawn lands in the right zone
        self.spawn_x = x
        self.spawn_y = y

        self.image = None

        if Enemy._label_font is None:
            Enemy._label_font = pygame.font.SysFont(None, 16)

    def update(self, player, dt, obstacles=None):
        if obstacles is None:
            obstacles = []
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if 0 < dist < self.aggro_range:
            dx_norm = dx / dist
            dy_norm = dy / dist
            self.rect.x += dx_norm * self.speed * dt * 60
            resolve_collision_x(self.rect, obstacles)
            self.rect.y += dy_norm * self.speed * dt * 60
            resolve_collision_y(self.rect, obstacles)

    def draw(self, surface, camera=None):
        super().draw(surface, camera)
        draw_rect = camera.apply(self.rect) if camera else self.rect

        # Name + combat level label above sprite
        label = f"{self.name} (lvl {self.combat_level})"
        label_surf = self._label_font.render(label, True, (255, 120, 120))
        lx = draw_rect.centerx - label_surf.get_width() // 2
        ly = draw_rect.top - 24
        surface.blit(label_surf, (lx, ly))

        # HP bar — only visible once the enemy has taken damage
        if self.hp < self.max_hp:
            bar_w, bar_h = 32, 4
            fill = max(0, (self.hp / self.max_hp) * bar_w)
            bx = draw_rect.centerx - bar_w // 2
            by = draw_rect.top - 13
            # Dark border
            pygame.draw.rect(surface, (20, 0, 0), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
            # Red background
            pygame.draw.rect(surface, (180, 0, 0), (bx, by, bar_w, bar_h))
            # Green fill
            if fill > 0:
                pygame.draw.rect(surface, (0, 210, 0), (bx, by, int(fill), bar_h))
