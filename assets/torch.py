import random
import pygame

COLOR_WOOD = (110, 65, 25)
COLOR_FLAME_OUTER = (255, 130, 20)
COLOR_FLAME_INNER = (255, 230, 100)

def create_floor_light_cookie(radius=85):
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        alpha = int(45 * (1.0 - (r / radius) ** 1.5))
        pygame.draw.circle(surf, (220, 120, 20, alpha), (radius, radius), r)
    return surf

FLOOR_TORCH_GLOW_COOKIE = create_floor_light_cookie(85)


class TorchParticle:
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x + random.uniform(-2, 2), y)
        self.vel = pygame.Vector2(random.uniform(-0.3, 0.3), random.uniform(-0.8, -0.3))
        self.life = random.randint(10, 20)
        self.max_life = self.life

    def update(self):
        self.pos += self.vel
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            alpha = int((self.life / self.max_life) * 200)
            color = (255, 200, 80, alpha)
            p_surf = pygame.Surface((2, 2), pygame.SRCALPHA)
            p_surf.fill(color)
            surface.blit(p_surf, (int(self.pos.x), int(self.pos.y)))


class TorchTile:
    def __init__(self, rect, attachment):
        self.rect = rect
        self.attachment = attachment
        self.pos = pygame.Vector2(rect.centerx, rect.centery)
        self.is_visible = False

        if attachment == "LEFT":
            self.wood_rect = pygame.Rect(rect.right - 8, rect.centery - 2, 6, 4)
            self.flame_pos = pygame.Vector2(rect.right - 10, rect.centery)
        elif attachment == "RIGHT":
            self.wood_rect = pygame.Rect(rect.left + 2, rect.centery - 2, 6, 4)
            self.flame_pos = pygame.Vector2(rect.left + 10, rect.centery)
        elif attachment == "BOTTOM":
            self.wood_rect = pygame.Rect(rect.centerx - 2, rect.top + 2, 4, 6)
            self.flame_pos = pygame.Vector2(rect.centerx, rect.top + 10)
        elif attachment == "TOP":
            self.wood_rect = pygame.Rect(rect.centerx - 2, rect.bottom - 8, 4, 6)
            self.flame_pos = pygame.Vector2(rect.centerx, rect.bottom - 10)
        else:
            self.wood_rect = pygame.Rect(rect.centerx - 2, rect.centery - 2, 4, 6)
            self.flame_pos = pygame.Vector2(rect.centerx, rect.centery - 4)

        self.sparks = []

    def check_visibility(self, player_pos, vision_radius, walls):
        p_vec = pygame.Vector2(player_pos)
        t_vec = pygame.Vector2(self.flame_pos)

        dist = p_vec.distance_to(t_vec)
        if dist > vision_radius + 40:
            self.is_visible = False
            return False

        for wall in walls:
            if wall.clipline((p_vec.x, p_vec.y), (t_vec.x, t_vec.y)):
                self.is_visible = False
                return False

        self.is_visible = True
        return True

    def get_raycasted_light_mask(self, base_light_surface, radius, walls):
        size = radius * 2
        torch_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        torch_surf.blit(base_light_surface, (0, 0))

        tx, ty = self.flame_pos.x, self.flame_pos.y
        torch_pos = self.flame_pos
        offset_x, offset_y = tx - radius, ty - radius

        nearby_walls = [
            w for w in walls 
            if abs(w.centerx - tx) < radius + 60 and abs(w.centery - ty) < radius + 60
        ]

        for wall in nearby_walls:
            edges = [
                ((wall.left, wall.top), (wall.right, wall.top)),
                ((wall.right, wall.top), (wall.right, wall.bottom)),
                ((wall.right, wall.bottom), (wall.left, wall.bottom)),
                ((wall.left, wall.bottom), (wall.left, wall.top))
            ]
            
            for p1, p2 in edges:
                edge_vec = pygame.Vector2(p2[0] - p1[0], p2[1] - p1[1])
                normal = pygame.Vector2(-edge_vec.y, edge_vec.x)
                midpoint = pygame.Vector2((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                
                if normal.dot(torch_pos - midpoint) <= 0:
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

        return torch_surf, (offset_x, offset_y)

    def update(self):
        if self.is_visible and random.random() < 0.4:
            self.sparks.append(TorchParticle(self.flame_pos.x, self.flame_pos.y))

        for p in self.sparks[:]:
            p.update()
            if p.life <= 0:
                self.sparks.remove(p)

    def draw_floor_glow(self, surface):
        if self.is_visible:
            radius = 85
            tx, ty = self.flame_pos.x, self.flame_pos.y
            surface.blit(FLOOR_TORCH_GLOW_COOKIE, (tx - radius, ty - radius))

    def draw(self, surface):
        if not self.is_visible:
            return

        self.update()
        for p in self.sparks:
            p.draw(surface)

        pygame.draw.rect(surface, COLOR_WOOD, self.wood_rect)
        pygame.draw.circle(surface, COLOR_FLAME_OUTER, (int(self.flame_pos.x), int(self.flame_pos.y)), 5)
        pygame.draw.circle(surface, COLOR_FLAME_INNER, (int(self.flame_pos.x), int(self.flame_pos.y)), 2)