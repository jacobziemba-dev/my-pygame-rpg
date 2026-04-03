import pygame
import math


class Projectile:
    def __init__(self, x, y, target_enemy, damage):
        self.rect = pygame.Rect(x, y, 6, 6)
        self.target = target_enemy
        self.damage = damage
        self.speed = 8
        self.hit = False

    def update(self, dt):
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.rect.x += int((dx / dist) * self.speed * dt * 60)
            self.rect.y += int((dy / dist) * self.speed * dt * 60)
        if self.rect.colliderect(self.target.rect):
            self.hit = True

    def draw(self, surface, camera=None):
        draw_rect = camera.apply(self.rect) if camera else self.rect
        pygame.draw.rect(surface, (255, 200, 50), draw_rect)
