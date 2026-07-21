import os
import random
import pygame

# --- INCREASED TILE RESOLUTION ---
TILE_SIZE = 40  # Scaled up from 20 to 40 for crisp high-res rendering
WALL_COLOR = (40, 35, 55)
BORDER_COLOR = (70, 65, 95)

def load_random_map(maps_dir="maps"):
    """Picks a random .txt file from maps/ directory and parses the map data."""
    if not os.path.exists(maps_dir):
        os.makedirs(maps_dir)
        raise FileNotFoundError(f"Folder '{maps_dir}' was missing. Created it! Place map_01.txt inside.")

    map_files = [f for f in os.listdir(maps_dir) if f.endswith('.txt')]
    
    if not map_files:
        raise FileNotFoundError(f"No .txt map files found in '{maps_dir}/' folder!")

    chosen_file = random.choice(map_files)
    file_path = os.path.join(maps_dir, chosen_file)

    with open(file_path, "r") as f:
        content = f.read()

    map_scope = {}
    exec(content, map_scope)

    maze = map_scope.get("MAZE", [])
    player_start = map_scope.get("PLAYER_START", (1, 1))
    exit_start = map_scope.get("EXIT_START", (38, 28))

    walls = []
    for r_idx, row in enumerate(maze):
        for c_idx, cell in enumerate(row):
            if cell == 1:
                walls.append(pygame.Rect(c_idx * TILE_SIZE, r_idx * TILE_SIZE, TILE_SIZE, TILE_SIZE))

    return walls, player_start, exit_start, chosen_file

def draw_dungeon(target_surface, walls):
    """Draws all dungeon wall blocks onto the target surface with crisp borders."""
    for wall in walls:
        pygame.draw.rect(target_surface, WALL_COLOR, wall)
        pygame.draw.rect(target_surface, BORDER_COLOR, wall, 2)