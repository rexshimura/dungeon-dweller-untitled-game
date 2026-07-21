import os
import random
import pygame

TILE_SIZE = 28

# Clean Default Wall Colors
COLOR_WALL = (120, 125, 140)
COLOR_WALL_BORDER = (80, 85, 100)
COLOR_WOOD = (110, 65, 25)
COLOR_FLAME_OUTER = (255, 130, 20)
COLOR_FLAME_INNER = (255, 230, 100)

def create_floor_light_cookie(radius=100):
    """Generates a warm, subtle radial light cookie to color floor tiles."""
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    for r in range(radius, 0, -2):
        # Subtle warm glow on floor (max alpha ~90 for soft color tint)
        alpha = int(90 * (1.0 - (r / radius) ** 1.6))
        pygame.draw.circle(surf, (255, 160, 50, alpha), (radius, radius), r)
        
    return surf

# Pre-render floor glow surface
FLOOR_TORCH_GLOW = create_floor_light_cookie(110)

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

    return walls, torches, player_start, exit_start, chosen_file

def draw_dungeon(surface, walls, torches):
    # 1. Draw Floor Light Glow centered on each torch flame FIRST
    for torch in torches:
        glow_r = 110
        tx, ty = torch.flame_pos.x, torch.flame_pos.y
        surface.blit(FLOOR_TORCH_GLOW, (tx - glow_r, ty - glow_r))

    # 2. Draw Walls OVER top of floor light (keeps walls dark & crisp)
    for wall in walls:
        pygame.draw.rect(surface, COLOR_WALL, wall, border_radius=2)
        pygame.draw.rect(surface, COLOR_WALL_BORDER, wall, 1, border_radius=2)

    # 3. Draw Torch brackets, flames, and sparks
    for torch in torches:
        torch.draw(surface)