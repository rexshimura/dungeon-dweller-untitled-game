import pygame
import math

class FogOfWar:
    def __init__(self, vision_radius=260, max_shadow_opacity=185):
        self.vision_radius = vision_radius
        self.max_shadow_opacity = max_shadow_opacity
        self.gradient_light = self._create_gradient_light(vision_radius)

    def _create_gradient_light(self, radius):
        size = radius * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        for r in range(radius, 0, -2):
            alpha = int(255 * (1.0 - (r / radius) ** 1.8))
            pygame.draw.circle(surf, (255, 255, 255, alpha), (radius, radius), r)
            
        return surf

    def _get_wall_edges(self, wall):
        return [
            ((wall.left, wall.top), (wall.right, wall.top)),
            ((wall.right, wall.top), (wall.right, wall.bottom)),
            ((wall.right, wall.bottom), (wall.left, wall.bottom)),
            ((wall.left, wall.bottom), (wall.left, wall.top))
        ]

    def _is_edge_facing_player(self, p1, p2, player_pos):
        edge_vec = pygame.Vector2(p2[0] - p1[0], p2[1] - p1[1])
        normal = pygame.Vector2(-edge_vec.y, edge_vec.x)
        midpoint = pygame.Vector2((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        to_player = player_pos - midpoint
        return normal.dot(to_player) > 0

    def draw(self, target_surface, player_rect, walls):
        px, py = player_rect.centerx, player_rect.centery
        player_pos = pygame.Vector2(px, py)
        width, height = target_surface.get_width(), target_surface.get_height()

        dark_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        dark_overlay.fill((10, 8, 14, self.max_shadow_opacity))

        light_mask = pygame.Surface((width, height), pygame.SRCALPHA)
        grad_x = px - self.vision_radius
        grad_y = py - self.vision_radius
        light_mask.blit(self.gradient_light, (grad_x, grad_y))

        nearby_walls = [
            w for w in walls 
            if abs(w.centerx - px) < self.vision_radius + 60 and abs(w.centery - py) < self.vision_radius + 60
        ]

        for wall in nearby_walls:
            edges = self._get_wall_edges(wall)
            for p1, p2 in edges:
                if not self._is_edge_facing_player(p1, p2, player_pos):
                    v1 = pygame.Vector2(p1[0] - px, p1[1] - py)
                    v2 = pygame.Vector2(p2[0] - px, p2[1] - py)

                    if v1.length() == 0 or v2.length() == 0:
                        continue

                    proj1 = pygame.Vector2(p1[0], p1[1]) + v1.normalize() * (self.vision_radius * 2)
                    proj2 = pygame.Vector2(p2[0], p2[1]) + v2.normalize() * (self.vision_radius * 2)

                    shadow_quad = [p1, p2, (proj2.x, proj2.y), (proj1.x, proj1.y)]
                    pygame.draw.polygon(light_mask, (0, 0, 0, 0), shadow_quad)

        dark_overlay.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        for wall in nearby_walls:
            wall_center = pygame.Vector2(wall.centerx, wall.centery)
            dist = player_pos.distance_to(wall_center)

            proximity_ratio = max(0.0, min(1.0, (dist - 20) / (self.vision_radius - 20)))
            
            if proximity_ratio > 0:
                wall_dim_alpha = int(self.max_shadow_opacity * (proximity_ratio ** 1.2))
                wall_shadow_surf = pygame.Surface((wall.width, wall.height), pygame.SRCALPHA)
                wall_shadow_surf.fill((10, 8, 14, wall_dim_alpha))
                dark_overlay.blit(wall_shadow_surf, (wall.x, wall.y))

        target_surface.blit(dark_overlay, (0, 0))