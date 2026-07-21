import pygame
import math

class FogOfWar:
    def __init__(self, vision_radius=260, max_shadow_opacity=185):
        self.vision_radius = vision_radius
        self.max_shadow_opacity = max_shadow_opacity
        
        # Pre-render Player Light Surface
        self.player_light = self._create_gradient_light(vision_radius, max_alpha=255)
        self.player_surf = pygame.Surface((vision_radius * 2, vision_radius * 2), pygame.SRCALPHA)
        
        # Pre-render Torch Base Cookie
        self.torch_light_radius = 85
        self.torch_light_base = self._create_gradient_light(self.torch_light_radius, max_alpha=120)

        # Reusable Fullscreen Surfaces (Allocated ONCE)
        self.dark_overlay = None
        self.light_mask = None
        self.baked_torch_mask = None
        self.cached_torches_id = None

    def _create_gradient_light(self, radius, max_alpha=255):
        size = radius * 2
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(radius, 0, -2):
            alpha = int(max_alpha * (1.0 - (r / radius) ** 1.8))
            pygame.draw.circle(surf, (255, 255, 255, alpha), (radius, radius), r)
        return surf

    def _get_wall_edges(self, wall):
        return [
            ((wall.left, wall.top), (wall.right, wall.top)),
            ((wall.right, wall.top), (wall.right, wall.bottom)),
            ((wall.right, wall.bottom), (wall.left, wall.bottom)),
            ((wall.left, wall.bottom), (wall.left, wall.top))
        ]

    def _is_edge_facing_origin(self, p1, p2, origin_pos):
        edge_vec = pygame.Vector2(p2[0] - p1[0], p2[1] - p1[1])
        normal = pygame.Vector2(-edge_vec.y, edge_vec.x)
        midpoint = pygame.Vector2((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        return normal.dot(origin_pos - midpoint) > 0

    def _bake_torch_fog_mask(self, width, height, walls, torches):
        self.baked_torch_mask = pygame.Surface((width, height), pygame.SRCALPHA)
        radius = self.torch_light_radius

        for torch in torches:
            tx, ty = torch.flame_pos.x, torch.flame_pos.y
            torch_pos = torch.flame_pos

            torch_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            torch_surf.blit(self.torch_light_base, (0, 0))

            offset_x, offset_y = tx - radius, ty - radius

            nearby_walls = [
                w for w in walls 
                if abs(w.centerx - tx) < radius + 60 and abs(w.centery - ty) < radius + 60
            ]

            for wall in nearby_walls:
                edges = self._get_wall_edges(wall)
                for p1, p2 in edges:
                    if not self._is_edge_facing_origin(p1, p2, torch_pos):
                        v1 = pygame.Vector2(p1[0] - tx, p1[1] - ty)
                        v2 = pygame.Vector2(p2[0] - tx, p2[1] - ty)

                        if v1.length() > 0 and v2.length() > 0:
                            proj1 = pygame.Vector2(p1[0], p1[1]) + v1.normalize() * (radius * 2)
                            proj2 = pygame.Vector2(p2[0], p2[1]) + v2.normalize() * (radius * 2)

                            quad = [
                                (p1[0] - offset_x, p1[1] - offset_y),
                                (p2[0] - offset_x, p2[1] - offset_y),
                                (proj2.x - offset_x, proj2.y - offset_y),
                                (proj1.x - offset_x, proj1.y - offset_y)
                            ]
                            pygame.draw.polygon(torch_surf, (0, 0, 0, 0), quad)

                wall_local = pygame.Rect(wall.x - offset_x, wall.y - offset_y, wall.width, wall.height)
                pygame.draw.rect(torch_surf, (0, 0, 0, 0), wall_local)

            self.baked_torch_mask.blit(torch_surf, (offset_x, offset_y), special_flags=pygame.BLEND_RGBA_MAX)

        self.cached_torches_id = id(torches)

    def draw(self, target_surface, player_rect, walls, torches=[]):
        px, py = player_rect.centerx, player_rect.centery
        player_pos = pygame.Vector2(px, py)
        width, height = target_surface.get_width(), target_surface.get_height()

        # Allocate screen-sized surfaces once
        if self.dark_overlay is None or self.dark_overlay.get_size() != (width, height):
            self.dark_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            self.light_mask = pygame.Surface((width, height), pygame.SRCALPHA)

        # Bake static torch mask ONCE per map
        if self.baked_torch_mask is None or self.cached_torches_id != id(torches):
            self._bake_torch_fog_mask(width, height, walls, torches)

        # Clear reusable overlays
        self.dark_overlay.fill((10, 8, 14, self.max_shadow_opacity))
        self.light_mask.fill((0, 0, 0, 0))

        # 1. BLIT PRE-BAKED TORCH MASK
        if self.baked_torch_mask:
            self.light_mask.blit(self.baked_torch_mask, (0, 0))

        # 2. RENDER PLAYER LIGHT USING PRE-ALLOCATED PLAYER_SURF
        self.player_surf.fill((0, 0, 0, 0))
        self.player_surf.blit(self.player_light, (0, 0))

        p_offset_x = px - self.vision_radius
        p_offset_y = py - self.vision_radius

        nearby_walls = [
            w for w in walls 
            if abs(w.centerx - px) < self.vision_radius + 60 and abs(w.centery - py) < self.vision_radius + 60
        ]

        # Calculate player raycasted shadow quads
        for wall in nearby_walls:
            edges = self._get_wall_edges(wall)
            for p1, p2 in edges:
                if not self._is_edge_facing_origin(p1, p2, player_pos):
                    v1 = pygame.Vector2(p1[0] - px, p1[1] - py)
                    v2 = pygame.Vector2(p2[0] - px, p2[1] - py)

                    if v1.length() > 0 and v2.length() > 0:
                        proj1 = pygame.Vector2(p1[0], p1[1]) + v1.normalize() * (self.vision_radius * 2)
                        proj2 = pygame.Vector2(p2[0], p2[1]) + v2.normalize() * (self.vision_radius * 2)

                        quad = [
                            (p1[0] - p_offset_x, p1[1] - p_offset_y),
                            (p2[0] - p_offset_x, p2[1] - p_offset_y),
                            (proj2.x - p_offset_x, proj2.y - p_offset_y),
                            (proj1.x - p_offset_x, proj1.y - p_offset_y)
                        ]
                        pygame.draw.polygon(self.player_surf, (0, 0, 0, 0), quad)

        self.light_mask.blit(self.player_surf, (p_offset_x, p_offset_y), special_flags=pygame.BLEND_RGBA_MAX)

        # 3. SUBTRACT LIGHT FROM FOG
        self.dark_overlay.blit(self.light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # 4. OPTIMIZED WALL OPACITY SHADING (Direct rect drawing instead of Surface instantiation)
        for wall in nearby_walls:
            dist = player_pos.distance_to(pygame.Vector2(wall.centerx, wall.centery))
            proximity_ratio = max(0.0, min(1.0, (dist - 20) / (self.vision_radius - 20)))
            
            if proximity_ratio > 0:
                wall_dim_alpha = int(self.max_shadow_opacity * (proximity_ratio ** 1.2))
                # Draw dark rect directly on dark_overlay without making a new Surface
                pygame.draw.rect(self.dark_overlay, (10, 8, 14, wall_dim_alpha), wall)

        target_surface.blit(self.dark_overlay, (0, 0))