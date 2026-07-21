import pygame

class FogOfWar:
    def __init__(self, vision_radius=180, max_shadow_opacity=255):
        self.vision_radius = vision_radius
        # Full pitch black fog
        self.max_shadow_opacity = 255
        
        self.player_light = self._create_gradient_light(vision_radius, max_alpha=255)
        self.player_surf = pygame.Surface((vision_radius * 2, vision_radius * 2), pygame.SRCALPHA)
        
        self.torch_light_radius = 70
        self.torch_light_base = self._create_gradient_light(self.torch_light_radius, max_alpha=255)

        self.dark_overlay = None
        self.light_mask = None

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

    def draw(self, target_surface, player_rect, walls, torches=[]):
        px, py = player_rect.centerx, player_rect.centery
        player_pos = pygame.Vector2(px, py)
        width, height = target_surface.get_width(), target_surface.get_height()

        if self.dark_overlay is None or self.dark_overlay.get_size() != (width, height):
            self.dark_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            self.light_mask = pygame.Surface((width, height), pygame.SRCALPHA)

        # 1. CHECK TORCH VISIBILITY
        for torch in torches:
            torch.check_visibility(player_pos, self.vision_radius, walls)

        # Base overlay is pure pitch black (0, 0, 0, 255)
        self.dark_overlay.fill((0, 0, 0, 255))
        self.light_mask.fill((0, 0, 0, 0))

        # 2. DRAW PLAYER LIGHT & CAST SHADOW QUADS
        self.player_surf.fill((0, 0, 0, 0))
        self.player_surf.blit(self.player_light, (0, 0))

        p_offset_x = px - self.vision_radius
        p_offset_y = py - self.vision_radius

        nearby_walls = [
            w for w in walls 
            if abs(w.centerx - px) < self.vision_radius + 40 and abs(w.centery - py) < self.vision_radius + 40
        ]

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
                        # Erase light from mask in blocked sightlines
                        pygame.draw.polygon(self.player_surf, (0, 0, 0, 0), quad)

        self.light_mask.blit(self.player_surf, (p_offset_x, p_offset_y), special_flags=pygame.BLEND_RGBA_MAX)

        # 3. BLIT RAYCASTED TORCH LIGHT MASKS
        for torch in torches:
            if torch.is_visible:
                torch_mask, offset = torch.get_raycasted_light_mask(
                    self.torch_light_base, 
                    self.torch_light_radius, 
                    walls
                )
                self.light_mask.blit(torch_mask, offset, special_flags=pygame.BLEND_RGBA_MAX)

        # 4. SUBTRACT LIGHT MASK FROM PITCH BLACK OVERLAY
        self.dark_overlay.blit(self.light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # 5. WALL SHADING (Pitch Black for hidden/farther walls)
        max_dim_dist = 140.0
        for wall in nearby_walls:
            dist = player_pos.distance_to(pygame.Vector2(wall.centerx, wall.centery))
            distance_ratio = max(0.0, min(1.0, (dist - 10.0) / (max_dim_dist - 10.0)))
            
            wall_dim_alpha = int(255 * (distance_ratio ** 1.8))
            if wall_dim_alpha > 0:
                pygame.draw.rect(self.dark_overlay, (0, 0, 0, wall_dim_alpha), wall)

        target_surface.blit(self.dark_overlay, (0, 0))