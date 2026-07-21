import os
import random
import pygame

TILE_SIZE = 28

COLOR_WALL = (120, 125, 140)
COLOR_WALL_BORDER = (80, 85, 100)
COLOR_WOOD = (110, 65, 25)
COLOR_FLAME_OUTER = (255, 130, 20)
COLOR_FLAME_INNER = (255, 230, 100)

# Cached surface for pre-baked floor glows
BAKED_FLOOR_GLOW_SURFACE = None

def create_floor_light_cookie(radius=85):
    """Generates a very soft, dim radial light cookie for floor tiles."""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Very dim warm glow (Max alpha reduced to 45)
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

    def update(self):
        if random.random() < 0.4:
            self.sparks.append(TorchParticle(self.flame_pos.x, self.flame_pos.y))
        
        for p in self.sparks[:]:
            p.update()
            if p.life <= 0:
                self.sparks.remove(p)

    def draw(self, surface):
        self.update()
        for p in self.sparks:
            p.draw(surface)

        pygame.draw.rect(surface, COLOR_WOOD, self.wood_rect)
        pygame.draw.circle(surface, COLOR_FLAME_OUTER, (int(self.flame_pos.x), int(self.flame_pos.y)), 5)
        pygame.draw.circle(surface, COLOR_FLAME_INNER, (int(self.flame_pos.x), int(self.flame_pos.y)), 2)

def detect_attachment(lines, r, c):
    rows = len(lines)
    cols = len(lines[0])

    if c + 1 < cols and lines[r][c + 1] == '#':
        return 'LEFT'
    if c - 1 >= 0 and lines[r][c - 1] == '#':
        return 'RIGHT'
    if r - 1 >= 0 and lines[r - 1][c] == '#':
        return 'BOTTOM'
    if r + 1 < rows and lines[r + 1][c] == '#':
        return 'TOP'
    
    return 'NONE'

def _bake_static_floor_glows(walls, torches, map_cols, map_rows):
    """Bakes steady, dim torch floor glows and casts wall shadows ONCE on load."""
    global BAKED_FLOOR_GLOW_SURFACE
    w, h = map_cols * TILE_SIZE, map_rows * TILE_SIZE
    BAKED_FLOOR_GLOW_SURFACE = pygame.Surface((w, h), pygame.SRCALPHA)

    radius = 85
    for torch in torches:
        tx, ty = torch.flame_pos.x, torch.flame_pos.y
        torch_pos = torch.flame_pos

        cookie_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        cookie_surf.blit(FLOOR_TORCH_GLOW_COOKIE, (0, 0))

        offset_x, offset_y = tx - radius, ty - radius
        nearby_walls = [
            w_rect for w_rect in walls 
            if abs(w_rect.centerx - tx) < radius + 60 and abs(w_rect.centery - ty) < radius + 60
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
                        pygame.draw.polygon(cookie_surf, (0, 0, 0, 0), quad)

            wall_local = pygame.Rect(wall.x - offset_x, wall.y - offset_y, wall.width, wall.height)
            pygame.draw.rect(cookie_surf, (0, 0, 0, 0), wall_local)

        BAKED_FLOOR_GLOW_SURFACE.blit(cookie_surf, (offset_x, offset_y))

def load_random_map(maps_folder="maps"):
    map_files = [f for f in os.listdir(maps_folder) if f.endswith(".txt")]
    if not map_files:
        raise FileNotFoundError(f"No map files found in '{maps_folder}'.")

    chosen_file = random.choice(map_files)
    filepath = os.path.join(maps_folder, chosen_file)

    walls = []
    torches = []
    player_start = (1, 1)
    exit_start = (2, 2)

    with open(filepath, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    rows = len(lines)
    cols = max(len(line) for line in lines)

    for r, line in enumerate(lines):
        for c, char in enumerate(line):
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            if char == '#':
                walls.append(rect)
            elif char == '1':
                attachment = detect_attachment(lines, r, c)
                torches.append(TorchTile(rect, attachment))
            elif char == 'P':
                player_start = (c, r)
            elif char == 'X':
                exit_start = (c, r)

    _bake_static_floor_glows(walls, torches, cols, rows)

    return walls, torches, player_start, exit_start, chosen_file

def draw_dungeon(surface, walls, torches):
    if BAKED_FLOOR_GLOW_SURFACE:
        surface.blit(BAKED_FLOOR_GLOW_SURFACE, (0, 0))

    for wall in walls:
        pygame.draw.rect(surface, COLOR_WALL, wall, border_radius=2)
        pygame.draw.rect(surface, COLOR_WALL_BORDER, wall, 1, border_radius=2)

    for torch in torches:
        torch.draw(surface)