import pygame
import sys
import os

pygame.init()

# Editor Settings
GRID_COLS, GRID_ROWS = 32, 24
TILE_SIZE = 28
PALETTE_HEIGHT = 80

SCREEN_WIDTH = GRID_COLS * TILE_SIZE
SCREEN_HEIGHT = (GRID_ROWS * TILE_SIZE) + PALETTE_HEIGHT

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dungeon Map Builder")
clock = pygame.time.Clock()

# Colors
COLOR_BG = (15, 12, 20)
COLOR_GRID = (35, 30, 45)
COLOR_PALETTE_BG = (22, 20, 30)
COLOR_TEXT = (240, 240, 255)
COLOR_HIGHLIGHT = (255, 215, 0)

# Tile Definitions & Colors
TILE_TYPES = {
    "0": {"name": "Floor", "color": (30, 25, 40), "symbol": "0"},
    "#": {"name": "Wall", "color": (120, 125, 140), "symbol": "#"},
    "1": {"name": "Torch", "color": (255, 160, 40), "symbol": "1"},
    "P": {"name": "Player Spawn", "color": (50, 230, 110), "symbol": "P"},
    "X": {"name": "Exit Chest", "color": (240, 190, 40), "symbol": "X"},
}

TILE_KEYS = ["0", "#", "1", "P", "X"]
selected_tile_index = 1  # Default to Wall '#'

# Map Data Storage
grid = [["0" for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

font = pygame.font.SysFont("Arial", 14, bold=True)
small_font = pygame.font.SysFont("Arial", 12)

def detect_torch_attachment(grid, r, c):
    """
    Checks adjacent tiles and returns attachment orientation:
    'LEFT', 'RIGHT', 'TOP', 'BOTTOM', or 'NONE'
    Rule: [Wall A][None][Torch][Wall B] -> Torch attaches to Wall B's LEFT side.
    """
    # Check Wall B (Right)
    if c + 1 < GRID_COLS and grid[r][c + 1] == "#":
        return "LEFT"
    # Check Wall A (Left)
    if c - 1 >= 0 and grid[r][c - 1] == "#":
        return "RIGHT"
    # Check Wall Above
    if r - 1 >= 0 and grid[r - 1][c] == "#":
        return "BOTTOM"
    # Check Wall Below
    if r + 1 < GRID_ROWS and grid[r + 1][c] == "#":
        return "TOP"
    
    return "NONE"

def draw_torch(surface, rect, attachment):
    """Draws a pixel torch icon with flame attached to its wall side."""
    cx, cy = rect.centerx, rect.centery
    
    # Position torch base according to attachment side
    if attachment == "LEFT":
        wood_rect = pygame.Rect(rect.right - 8, cy - 2, 6, 4)
        flame_pos = (rect.right - 10, cy)
    elif attachment == "RIGHT":
        wood_rect = pygame.Rect(rect.left + 2, cy - 2, 6, 4)
        flame_pos = (rect.left + 10, cy)
    elif attachment == "BOTTOM":
        wood_rect = pygame.Rect(cx - 2, rect.top + 2, 4, 6)
        flame_pos = (cx, rect.top + 10)
    elif attachment == "TOP":
        wood_rect = pygame.Rect(cx - 2, rect.bottom - 8, 4, 6)
        flame_pos = (cx, rect.bottom - 10)
    else:  # Unattached (Center)
        wood_rect = pygame.Rect(cx - 2, cy - 2, 4, 6)
        flame_pos = (cx, cy - 4)

    # Draw Wooden Handle
    pygame.draw.rect(surface, (110, 65, 25), wood_rect)
    # Draw Outer Glow & Flame
    pygame.draw.circle(surface, (255, 120, 20, 180), flame_pos, 5)
    pygame.draw.circle(surface, (255, 220, 80), flame_pos, 3)

def save_map(filename="map_custom.txt"):
    os.makedirs("maps", exist_ok=True)
    filepath = os.path.join("maps", filename)
    with open(filepath, "w") as f:
        for row in grid:
            f.write("".join(row) + "\n")
    print(f"[MAP SAVED] -> {filepath}")

def load_map(filename="map_custom.txt"):
    global grid
    filepath = os.path.join("maps", filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            for r in range(min(GRID_ROWS, len(lines))):
                for c in range(min(GRID_COLS, len(lines[r]))):
                    grid[r][c] = lines[r][c]
        print(f"[MAP LOADED] -> {filepath}")
    else:
        print(f"[ERROR] File not found: {filepath}")

running = True
message_timer = 0
status_msg = "Left-Click: Place | Right-Click: Erase | [S] Save | [L] Load"

while running:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    grid_col = mouse_x // TILE_SIZE
    grid_row = mouse_y // TILE_SIZE

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1: selected_tile_index = 0
            elif event.key == pygame.K_2: selected_tile_index = 1
            elif event.key == pygame.K_3: selected_tile_index = 2
            elif event.key == pygame.K_4: selected_tile_index = 3
            elif event.key == pygame.K_5: selected_tile_index = 4
            elif event.key == pygame.K_s:
                save_map("map_01.txt")
                status_msg = "Map Saved to maps/map_01.txt!"
                message_timer = 120
            elif event.key == pygame.K_l:
                load_map("map_01.txt")
                status_msg = "Map Loaded from maps/map_01.txt!"
                message_timer = 120

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Click Palette
            if mouse_y >= GRID_ROWS * TILE_SIZE:
                for idx in range(len(TILE_KEYS)):
                    box_x = 20 + (idx * 85)
                    box_y = (GRID_ROWS * TILE_SIZE) + 15
                    rect = pygame.Rect(box_x, box_y, 75, 45)
                    if rect.collidepoint(mouse_x, mouse_y):
                        selected_tile_index = idx

    # Mouse Paint / Erase Dragging
    mouse_buttons = pygame.mouse.get_pressed()
    if 0 <= grid_row < GRID_ROWS and 0 <= grid_col < GRID_COLS:
        if mouse_buttons[0]:  # Left Click Paint
            sym = TILE_KEYS[selected_tile_index]
            # Ensure unique P and X
            if sym in ["P", "X"]:
                for r in range(GRID_ROWS):
                    for c in range(GRID_COLS):
                        if grid[r][c] == sym:
                            grid[r][c] = "0"
            grid[grid_row][grid_col] = sym

        elif mouse_buttons[2]:  # Right Click Erase (Set to Floor)
            grid[grid_row][grid_col] = "0"

    # --- RENDER ---
    screen.fill(COLOR_BG)

    # 1. Draw Map Grid
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            tile_sym = grid[r][c]
            rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            # Draw Floor Base
            pygame.draw.rect(screen, TILE_TYPES["0"]["color"], rect)

            # Draw Tile Type
            if tile_sym == "#":
                pygame.draw.rect(screen, TILE_TYPES["#"]["color"], rect, border_radius=2)
                pygame.draw.rect(screen, (80, 85, 100), rect, 1, border_radius=2)

            elif tile_sym == "1":  # Torch with Auto-Attachment
                attachment = detect_torch_attachment(grid, r, c)
                draw_torch(screen, rect, attachment)

            elif tile_sym in ["P", "X"]:
                t_color = TILE_TYPES[tile_sym]["color"]
                pygame.draw.rect(screen, t_color, rect, border_radius=4)
                txt = small_font.render(tile_sym, True, (10, 10, 15))
                screen.blit(txt, txt.get_rect(center=rect.center))

            pygame.draw.rect(screen, COLOR_GRID, rect, 1)

    # 2. Draw Hover Cursor
    if 0 <= grid_row < GRID_ROWS and 0 <= grid_col < GRID_COLS:
        hover_rect = pygame.Rect(grid_col * TILE_SIZE, grid_row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(screen, (255, 255, 255, 100), hover_rect, 2)

    # 3. Draw Bottom Palette UI
    palette_rect = pygame.Rect(0, GRID_ROWS * TILE_SIZE, SCREEN_WIDTH, PALETTE_HEIGHT)
    pygame.draw.rect(screen, COLOR_PALETTE_BG, palette_rect)
    pygame.draw.line(screen, (60, 55, 80), (0, GRID_ROWS * TILE_SIZE), (SCREEN_WIDTH, GRID_ROWS * TILE_SIZE), 2)

    for idx, key in enumerate(TILE_KEYS):
        box_x = 20 + (idx * 85)
        box_y = (GRID_ROWS * TILE_SIZE) + 15
        box_rect = pygame.Rect(box_x, box_y, 75, 45)

        is_selected = (idx == selected_tile_index)
        bg_col = (40, 35, 55) if not is_selected else (60, 55, 85)
        border_col = COLOR_HIGHLIGHT if is_selected else (80, 75, 100)

        pygame.draw.rect(screen, bg_col, box_rect, border_radius=4)
        pygame.draw.rect(screen, border_col, box_rect, 2 if is_selected else 1, border_radius=4)

        # Draw tile key preview
        t_info = TILE_TYPES[key]
        lbl = font.render(f"[{idx+1}] {t_info['name']}", True, COLOR_TEXT)
        screen.blit(lbl, (box_x + 6, box_y + 12))

    # Status Bar Message
    if message_timer > 0:
        message_timer -= 1
        msg_surface = font.render(status_msg, True, COLOR_HIGHLIGHT)
    else:
        msg_surface = font.render("Left-Click: Paint | Right-Click: Erase | [S] Save | [L] Load", True, (160, 160, 180))

    screen.blit(msg_surface, (SCREEN_WIDTH - msg_surface.get_width() - 20, (GRID_ROWS * TILE_SIZE) + 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()