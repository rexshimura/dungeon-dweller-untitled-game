import pygame
import sys

pygame.init()

# Setup Grid Configuration (40 cols x 30 rows @ 20px = 800x600 window)
COLS, ROWS = 40, 30
TILE_SIZE = 20
WIDTH, HEIGHT = COLS * TILE_SIZE, ROWS * TILE_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Map Builder | 1: Wall | 2: Floor | P: Player Spawn | E: Exit/Treasure | S: Export")
clock = pygame.time.Clock()

# Colors
COLOR_BG = (15, 12, 20)
COLOR_WALL = (40, 35, 55)
COLOR_GRID = (30, 25, 40)
COLOR_TEXT = (255, 255, 255)
COLOR_OUTLINE = (70, 65, 90)
COLOR_PLAYER = (60, 180, 240)    # Blue for Player
COLOR_EXIT = (240, 190, 40)      # Gold for Exit

# 0 = Floor, 1 = Wall, 2 = Player, 3 = Exit
grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]

# Add outer boundary default walls
for r in range(ROWS):
    for c in range(COLS):
        if r == 0 or r == ROWS - 1 or c == 0 or c == COLS - 1:
            grid[r][c] = 1

# Default positions
player_pos = (1, 1)
exit_pos = (COLS - 2, ROWS - 2)
grid[player_pos[1]][player_pos[0]] = 2
grid[exit_pos[1]][exit_pos[0]] = 3

# Selected Mode: "WALL", "ERASE", "PLAYER", "EXIT"
mode = "WALL"

def clear_value_from_grid(val):
    """Ensures there is only ever ONE player and ONE exit on the map."""
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] == val:
                grid[r][c] = 0

def export_map():
    global player_pos, exit_pos
    
    # Locate player & exit positions
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] == 2:
                player_pos = (c, r)
            elif grid[r][c] == 3:
                exit_pos = (c, r)

    print("\n" + "="*50)
    print("--- COPY THIS DATA INTO YOUR MAP.PY FILE ---")
    print("="*50)
    
    formatted_rows = []
    for row in grid:
        # Convert player (2) and exit (3) back to floor (0) in the printed maze array
        # so the collision map stays clean (0 = floor, 1 = wall)
        clean_row = [0 if cell in (2, 3) else cell for cell in row]
        formatted_rows.append("    [" + ",".join(str(cell) for cell in clean_row) + "]")
    
    output = f"""PLAYER_START = ({player_pos[0]}, {player_pos[1]})  # (col, row)
EXIT_START = ({exit_pos[0]}, {exit_pos[1]})      # (col, row)

MAZE = [
""" + ",\n".join(formatted_rows) + "\n]"

    print(output)
    print("="*50)
    
    with open("map_data.txt", "w") as f:
        f.write(output)
    print(" Saved successfully to 'map_data.txt'!\n")

font = pygame.font.SysFont("Arial", 16)
saved_notice_timer = 0

# Main Editor Loop
drawing = True
while drawing:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            drawing = False
            
        elif event.type == pygame.KEYDOWN:
            # Mode selection shortcuts
            if event.key == pygame.K_1:
                mode = "WALL"
            elif event.key == pygame.K_2:
                mode = "ERASE"
            elif event.key == pygame.K_p:
                mode = "PLAYER"
            elif event.key == pygame.K_e:
                mode = "EXIT"
            # Export / Save
            elif event.key == pygame.K_s or event.key == pygame.K_RETURN:
                export_map()
                saved_notice_timer = 120
            # Clear canvas
            elif event.key == pygame.K_c:
                grid = [[1 if (r == 0 or r == ROWS - 1 or c == 0 or c == COLS - 1) else 0 for c in range(COLS)] for r in range(ROWS)]
                grid[1][1] = 2
                grid[ROWS - 2][COLS - 2] = 3

    # Mouse placement logic
    mouse_buttons = pygame.mouse.get_pressed()
    if mouse_buttons[0] or mouse_buttons[2]:
        mx, my = pygame.mouse.get_pos()
        col = mx // TILE_SIZE
        row = my // TILE_SIZE
        
        # Don't overwrite outer boundary walls
        if 0 < row < ROWS - 1 and 0 < col < COLS - 1:
            if mouse_buttons[2]:  # Right click always erases
                grid[row][col] = 0
            elif mouse_buttons[0]:  # Left click places active tool
                if mode == "WALL":
                    grid[row][col] = 1
                elif mode == "ERASE":
                    grid[row][col] = 0
                elif mode == "PLAYER":
                    clear_value_from_grid(2)
                    grid[row][col] = 2
                elif mode == "EXIT":
                    clear_value_from_grid(3)
                    grid[row][col] = 3

    # Rendering
    screen.fill(COLOR_BG)
    
    for r in range(ROWS):
        for c in range(COLS):
            x = c * TILE_SIZE
            y = r * TILE_SIZE
            val = grid[r][c]
            
            if val == 1:
                pygame.draw.rect(screen, COLOR_WALL, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(screen, COLOR_OUTLINE, (x, y, TILE_SIZE, TILE_SIZE), 1)
            elif val == 2:
                pygame.draw.rect(screen, COLOR_PLAYER, (x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6), border_radius=3)
            elif val == 3:
                pygame.draw.rect(screen, COLOR_EXIT, (x + 3, y + 3, TILE_SIZE - 6, TILE_SIZE - 6), border_radius=2)
            else:
                pygame.draw.rect(screen, COLOR_GRID, (x, y, TILE_SIZE, TILE_SIZE), 1)

    # UI Overlay
    mode_text = font.render(f"ACTIVE TOOL: [{mode}]  |  [1] Wall  [2] Erase  [P] Player Spawn  [E] Exit  |  Press 'S' to Save", True, COLOR_TEXT)
    screen.blit(mode_text, (10, 5))

    if saved_notice_timer > 0:
        saved_text = font.render("EXPORTED TO TERMINAL & map_data.txt!", True, (100, 255, 100))
        screen.blit(saved_text, (WIDTH - saved_text.get_width() - 10, 5))
        saved_notice_timer -= 1

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()