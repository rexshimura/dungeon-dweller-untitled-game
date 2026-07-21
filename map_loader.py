import os
import json
import random
import pygame
from torch import TorchTile
from sign import SignTile

TILE_SIZE = 28

# Base Floor Palette
FLOOR_BASE_COLORS = [
    (18, 15, 24),
    (20, 17, 26),
    (16, 14, 22),
    (22, 19, 28)
]
FLOOR_GRID_LINE = (10, 8, 14)

# Wall Color Palette (Slate stone matching floor hue)
WALL_BASE_COLOR = (42, 38, 54)
WALL_BORDER_LIGHT = (65, 60, 82)
WALL_BORDER_DARK = (24, 20, 32)
WALL_BRICK_LINE = (30, 26, 40)


def _generate_floor_textures():
    """Generates procedural stone floor tiles with noise specks and grid borders."""
    textures = []
    for color in FLOOR_BASE_COLORS:
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill(color)
        
        for _ in range(8):
            noise_x = random.randint(1, TILE_SIZE - 2)
            noise_y = random.randint(1, TILE_SIZE - 2)
            shade = random.choice([color[0] + 6, max(0, color[0] - 6)])
            surf.set_at((noise_x, noise_y), (shade, shade, shade))

        pygame.draw.rect(surf, FLOOR_GRID_LINE, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        textures.append(surf)
        
    return textures


def _generate_wall_texture():
    """Generates a procedural stone brick wall texture."""
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(WALL_BASE_COLOR)
    
    half_h = TILE_SIZE // 2
    
    # Brick mortar layout
    pygame.draw.line(surf, WALL_BRICK_LINE, (0, half_h), (TILE_SIZE, half_h), 1)
    pygame.draw.line(surf, WALL_BRICK_LINE, (TILE_SIZE // 2, 0), (TILE_SIZE // 2, half_h), 1)
    pygame.draw.line(surf, WALL_BRICK_LINE, (TILE_SIZE // 4, half_h), (TILE_SIZE // 4, TILE_SIZE), 1)
    pygame.draw.line(surf, WALL_BRICK_LINE, (3 * TILE_SIZE // 4, half_h), (3 * TILE_SIZE // 4, TILE_SIZE), 1)

    # Stone specks
    for _ in range(12):
        noise_x = random.randint(1, TILE_SIZE - 2)
        noise_y = random.randint(1, TILE_SIZE - 2)
        shade = random.choice([WALL_BASE_COLOR[0] + 8, max(0, WALL_BASE_COLOR[0] - 8)])
        surf.set_at((noise_x, noise_y), (shade, max(0, shade - 2), shade + 2))

    # Outer tile bevel highlights
    pygame.draw.line(surf, WALL_BORDER_LIGHT, (0, 0), (TILE_SIZE - 1, 0), 1)
    pygame.draw.line(surf, WALL_BORDER_LIGHT, (0, 0), (0, TILE_SIZE - 1), 1)
    pygame.draw.line(surf, WALL_BORDER_DARK, (0, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
    pygame.draw.line(surf, WALL_BORDER_DARK, (TILE_SIZE - 1, 0), (TILE_SIZE - 1, TILE_SIZE - 1), 1)

    return surf


FLOOR_TEXTURES = _generate_floor_textures()
WALL_TEXTURE = _generate_wall_texture()


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
    if not os.path.exists(maps_folder):
        os.makedirs(maps_folder)

    map_files = [f for f in os.listdir(maps_folder) if f.endswith(".txt")]
    if not map_files:
        raise FileNotFoundError(f"No map files found in '{maps_folder}'. Please create one in mapbuilder.py!")

    chosen_file = random.choice(map_files)
    filepath = os.path.join(maps_folder, chosen_file)

    # Load associated JSON metadata for sign text
    json_path = os.path.splitext(filepath)[0] + ".json"
    sign_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as jf:
                sign_data = json.load(jf)
        except Exception:
            sign_data = {}

    walls = []
    torches = []
    signs = []
    floor_tiles = []
    player_start = (1, 1)
    exit_start = (2, 2)

    with open(filepath, "r") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    random.seed(filepath)

    for r, line in enumerate(lines):
        for c, char in enumerate(line):
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            if char == '#':
                walls.append(rect)
            else:
                tex = random.choice(FLOOR_TEXTURES)
                floor_tiles.append((rect, tex))

                if char == '1':
                    attachment = detect_attachment(lines, r, c)
                    torches.append(TorchTile(rect, attachment))
                elif char == 'S':
                    coord_key = f"{r},{c}"
                    text = sign_data.get(coord_key, "A mysterious sign weathered by time...")
                    signs.append(SignTile(rect, text))
                elif char == 'P':
                    player_start = (c, r)
                elif char == 'X':
                    exit_start = (c, r)

    random.seed()

    return walls, torches, signs, floor_tiles, player_start, exit_start, chosen_file


def draw_dungeon(surface, walls, torches, signs=[], floor_tiles=[]):
    # 1. Floor Tiles
    for rect, tex in floor_tiles:
        surface.blit(tex, (rect.x, rect.y))

    # 2. Torch Floor Glow
    for torch in torches:
        torch.draw_floor_glow(surface)

    # 3. Textured Walls
    for wall in walls:
        surface.blit(WALL_TEXTURE, (wall.x, wall.y))

    # 4. Signs
    for sign in signs:
        sign.draw(surface)

    # 5. Torches & Flames
    for torch in torches:
        torch.draw(surface)