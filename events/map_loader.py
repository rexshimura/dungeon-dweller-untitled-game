import os
import json
import random
import pygame

from assets.torch import TorchTile
from assets.sign import SignTile
from assets.door import DoorTile
from assets.key import KeyTile
from enemies.slime.small_slime import SmallSlime

TILE_SIZE = 28

# Color ID mapping: 0=Gray, 1=Green, 2=Blue, 3=Red, 4=Yellow
COLOR_KEYS = ["gray_key", "green_key", "blue_key", "red_key", "yellow_key"]

# Base Floor Palette
FLOOR_BASE_COLORS = [
    (18, 15, 24),
    (20, 17, 26),
    (16, 14, 22),
    (22, 19, 28)
]
FLOOR_GRID_LINE = (10, 8, 14)

# Wall Color Palette
WALL_BASE_COLOR = (42, 38, 54)
WALL_BORDER_LIGHT = (65, 60, 82)
WALL_BORDER_DARK = (24, 20, 32)
WALL_BRICK_LINE = (30, 26, 40)


def _generate_floor_textures():
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
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    surf.fill(WALL_BASE_COLOR)
    
    half_h = TILE_SIZE // 2
    
    pygame.draw.line(surf, WALL_BRICK_LINE, (0, half_h), (TILE_SIZE, half_h), 1)
    pygame.draw.line(surf, WALL_BRICK_LINE, (TILE_SIZE // 2, 0), (TILE_SIZE // 2, half_h), 1)
    pygame.draw.line(surf, WALL_BRICK_LINE, (TILE_SIZE // 4, half_h), (TILE_SIZE // 4, TILE_SIZE), 1)
    pygame.draw.line(surf, WALL_BRICK_LINE, (3 * TILE_SIZE // 4, half_h), (3 * TILE_SIZE // 4, TILE_SIZE), 1)

    for _ in range(12):
        noise_x = random.randint(1, TILE_SIZE - 2)
        noise_y = random.randint(1, TILE_SIZE - 2)
        shade = random.choice([WALL_BASE_COLOR[0] + 8, max(0, WALL_BASE_COLOR[0] - 8)])
        surf.set_at((noise_x, noise_y), (shade, max(0, shade - 2), shade + 2))

    pygame.draw.line(surf, WALL_BORDER_LIGHT, (0, 0), (TILE_SIZE - 1, 0), 1)
    pygame.draw.line(surf, WALL_BORDER_LIGHT, (0, 0), (0, TILE_SIZE - 1), 1)
    pygame.draw.line(surf, WALL_BORDER_DARK, (0, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 1)
    pygame.draw.line(surf, WALL_BORDER_DARK, (TILE_SIZE - 1, 0), (TILE_SIZE - 1, TILE_SIZE - 1), 1)

    return surf


FLOOR_TEXTURES = _generate_floor_textures()
WALL_TEXTURE = _generate_wall_texture()


def detect_attachment(lines, r, c):
    rows = len(lines)
    cols = len(lines[0]) if rows > 0 else 0

    if c + 1 < cols and lines[r][c + 1] == '#':
        return 'LEFT'
    if c - 1 >= 0 and lines[r][c - 1] == '#':
        return 'RIGHT'
    if r - 1 >= 0 and lines[r - 1][c] == '#':
        return 'BOTTOM'
    if r + 1 < rows and lines[r + 1][c] == '#':
        return 'TOP'
    
    return 'NONE'


def load_map(maps_folder="maps", target_file=None):
    if not os.path.exists(maps_folder):
        os.makedirs(maps_folder)

    if target_file:
        chosen_file = target_file
        filepath = os.path.join(maps_folder, chosen_file)
    else:
        map_files = [f for f in os.listdir(maps_folder) if f.endswith(".txt")]
        if not map_files:
            raise FileNotFoundError(f"No map files found in '{maps_folder}'. Please create one in map_builder.py!")
        chosen_file = random.choice(map_files)
        filepath = os.path.join(maps_folder, chosen_file)

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
    doors = []
    keys = []
    slimes = []
    floor_tiles = []
    player_start = (1, 1)
    exit_start = (2, 2)

    with open(filepath, "r") as f:
        raw_lines = [line.strip().split() if ' ' in line.strip() else list(line.strip()) for line in f.readlines() if line.strip()]

    rows = len(raw_lines)
    cols = max(len(line) for line in raw_lines) if rows > 0 else 0

    random.seed(filepath)

    for r, line in enumerate(raw_lines):
        for c, token in enumerate(line):
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            if token == '#':
                walls.append(rect)
            else:
                tex = random.choice(FLOOR_TEXTURES)
                floor_tiles.append((rect, tex))

                if token == '1':
                    attachment = detect_attachment(raw_lines, r, c)
                    torches.append(TorchTile(rect, attachment))
                elif token == 'S':
                    coord_key = f"{r},{c}"
                    text = sign_data.get(coord_key, "A mysterious sign weathered by time...")
                    signs.append(SignTile(rect, text))
                elif token == 'D':
                    doors.append(DoorTile(rect, is_locked=False))
                elif token.startswith('L'):
                    idx = int(token[1:]) if len(token) > 1 and token[1:].isdigit() else 0
                    key_id = COLOR_KEYS[min(idx, 4)]
                    doors.append(DoorTile(rect, is_locked=True, key_id=key_id))
                elif token.startswith('K'):
                    idx = int(token[1:]) if len(token) > 1 and token[1:].isdigit() else 0
                    key_id = COLOR_KEYS[min(idx, 4)]
                    keys.append(KeyTile(rect, key_id=key_id))
                elif token == 'e':
                    # Offsets centered relative to TILE_SIZE (28px)
                    slimes.append(SmallSlime(c * TILE_SIZE + 7, r * TILE_SIZE + 8))
                elif token == 'P':
                    player_start = (c, r)
                elif token == 'X':
                    exit_start = (c, r)

    random.seed()

    clean_name = os.path.splitext(chosen_file)[0]
    map_width_px = cols * TILE_SIZE
    map_height_px = rows * TILE_SIZE

    return (
        walls, 
        torches, 
        signs, 
        doors,
        keys,
        slimes,
        floor_tiles, 
        player_start, 
        exit_start, 
        clean_name, 
        map_width_px, 
        map_height_px
    )


def draw_dungeon(surface, walls, torches, signs=[], doors=[], keys=[], floor_tiles=[]):
    # 1. Floor Tiles
    for rect, tex in floor_tiles:
        surface.blit(tex, (rect.x, rect.y))

    # 2. Torch Floor Glow
    for torch in torches:
        torch.draw_floor_glow(surface)

    # 3. Textured Walls
    for wall in walls:
        surface.blit(WALL_TEXTURE, (wall.x, wall.y))

    # 4. Doors & Keys
    for key in keys:
        key.draw(surface)

    for door in doors:
        door.draw(surface)

    # 5. Signs
    for sign in signs:
        sign.draw(surface)

    # 6. Torches & Flames
    for torch in torches:
        torch.draw(surface)