import os
import json
import pygame

pygame.init()

# Fixed Window Dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SIDEBAR_WIDTH = 250

MIN_DIM = 15
MAX_DIM = 80
DEFAULT_COLS = 30
DEFAULT_ROWS = 20

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dungeon Map Builder")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 12, bold=True)
small_font = pygame.font.SysFont("Arial", 11)
title_font = pygame.font.SysFont("Arial", 18, bold=True)


# --- TEXTURE PREVIEWS ---
def create_sidebar_previews():
    wall_preview = pygame.Surface((20, 20))
    wall_preview.fill((42, 38, 54))
    pygame.draw.rect(wall_preview, (65, 60, 82), (0, 0, 20, 20), 1)

    floor_preview = pygame.Surface((20, 20))
    floor_preview.fill((20, 17, 26))
    pygame.draw.rect(floor_preview, (10, 8, 14), (0, 0, 20, 20), 1)

    sign_preview = pygame.Surface((20, 20))
    sign_preview.fill((20, 17, 26))
    board_rect = pygame.Rect(3, 4, 14, 10)
    pygame.draw.rect(sign_preview, (85, 48, 22), board_rect, border_radius=2)
    pygame.draw.rect(sign_preview, (45, 22, 10), board_rect, 1, border_radius=2)

    torch_preview = pygame.Surface((20, 20))
    torch_preview.fill((20, 17, 26))
    pygame.draw.circle(torch_preview, (255, 130, 20), (10, 10), 5)
    pygame.draw.circle(torch_preview, (255, 230, 100), (10, 10), 2)

    return {
        '#': wall_preview,
        '.': floor_preview,
        'S': sign_preview,
        '1': torch_preview
    }

PREVIEWS = create_sidebar_previews()

# --- TAB DEFINITIONS ---
OBJECT_ITEMS = [
    "-- Main",
    {'char': '#', 'name': 'Wall',   'symbol': '[#]', 'color': (42, 38, 54)},
    {'char': '.', 'name': 'Floor',  'symbol': '[.]', 'color': (20, 17, 26)},
    "-- Assets",
    {'char': 'S', 'name': 'Sign',   'symbol': '[S]', 'color': (180, 110, 40)},
    {'char': '1', 'name': 'Torch',  'symbol': '[1]', 'color': (255, 140, 20)},
]

CONFIG_ITEMS = [
    {'char': 'P', 'name': 'Player Spawn', 'symbol': '[P]', 'color': (50, 230, 110)},
    {'char': 'X', 'name': 'Exit',         'symbol': '[X]', 'color': (240, 190, 40)},
]

# --- STATE VARIABLES ---
app_state = "START_MENU"
sidebar_tab = "OBJECTS"  # "OBJECTS", "CONFIGS", "TOOLS"

grid_cols = DEFAULT_COLS
grid_rows = DEFAULT_ROWS
grid = [['.' for _ in range(grid_cols)] for _ in range(grid_rows)]
sign_texts = {}
map_filename = "map_01"
selected_tool = '#'
pen_size = 1  # Brush size: 1x1, 2x2, 3x3

text_input_val = "map_01"
editing_sign_coord = None
dropdown_open = False

# Pan and Zoom State
zoom_level = 1.0
pan_offset_x = 0.0
pan_offset_y = 0.0
is_panning = False
pan_start_pos = (0, 0)


def get_maps_list():
    if not os.path.exists("maps"):
        os.makedirs("maps")
    return [f for f in os.listdir("maps") if f.endswith(".txt")]


def reset_pan_zoom():
    global zoom_level, pan_offset_x, pan_offset_y
    avail_w = SCREEN_WIDTH - SIDEBAR_WIDTH
    avail_h = SCREEN_HEIGHT
    
    base_tile_size = min(avail_w / grid_cols, avail_h / grid_rows)
    zoom_level = 1.0
    
    canvas_w = base_tile_size * grid_cols
    canvas_h = base_tile_size * grid_rows
    
    pan_offset_x = (avail_w - canvas_w) / 2
    pan_offset_y = (avail_h - canvas_h) / 2


def resize_grid(new_cols, new_rows):
    global grid_cols, grid_rows, grid

    new_cols = max(MIN_DIM, min(MAX_DIM, new_cols))
    new_rows = max(MIN_DIM, min(MAX_DIM, new_rows))

    new_grid = [['.' for _ in range(new_cols)] for _ in range(new_rows)]
    for r in range(min(grid_rows, new_rows)):
        for c in range(min(grid_cols, new_cols)):
            new_grid[r][c] = grid[r][c]

    grid_cols = new_cols
    grid_rows = new_rows
    grid = new_grid
    reset_pan_zoom()


def auto_add_border_walls():
    """Applies '#' walls around the perimeter of the current canvas."""
    for r in range(grid_rows):
        for c in range(grid_cols):
            if r == 0 or r == grid_rows - 1 or c == 0 or c == grid_cols - 1:
                grid[r][c] = '#'
                sign_texts.pop(f"{r},{c}", None)


def paint_brush(center_r, center_c, tool):
    """Paints tiles according to current pen_size."""
    half = pen_size // 2
    for dr in range(-half, half + 1 if pen_size % 2 != 0 else half):
        for dc in range(-half, half + 1 if pen_size % 2 != 0 else half):
            r, c = center_r + dr, center_c + dc
            if 0 <= r < grid_rows and 0 <= c < grid_cols:
                grid[r][c] = tool
                if tool == 'S':
                    global editing_sign_coord, text_input_val, app_state
                    editing_sign_coord = f"{r},{c}"
                    text_input_val = sign_texts.get(editing_sign_coord, "")
                    app_state = "SIGN_TEXT_MODAL"
                elif tool == '.':
                    sign_texts.pop(f"{r},{c}", None)


def load_map_from_file(filename):
    global grid_cols, grid_rows, grid, sign_texts, map_filename, app_state
    filepath = os.path.join("maps", filename)
    map_filename = os.path.splitext(filename)[0]

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        loaded_rows = len(lines)
        loaded_cols = max(len(l) for l in lines) if loaded_rows > 0 else DEFAULT_COLS

        grid_rows = max(MIN_DIM, min(MAX_DIM, loaded_rows))
        grid_cols = max(MIN_DIM, min(MAX_DIM, loaded_cols))
        grid = [['.' for _ in range(grid_cols)] for _ in range(grid_rows)]

        for r in range(min(grid_rows, loaded_rows)):
            for c in range(min(grid_cols, len(lines[r]))):
                grid[r][c] = lines[r][c]

    json_path = os.path.join("maps", f"{map_filename}.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as jf:
                sign_texts = json.load(jf)
        except Exception:
            sign_texts = {}
    else:
        sign_texts = {}

    reset_pan_zoom()
    app_state = "EDITOR"


def save_map_to_file():
    if not os.path.exists("maps"):
        os.makedirs("maps")

    txt_path = os.path.join("maps", f"{map_filename}.txt")
    json_path = os.path.join("maps", f"{map_filename}.json")

    with open(txt_path, "w") as f:
        for row in grid:
            f.write("".join(row) + "\n")

    with open(json_path, "w") as jf:
        json.dump(sign_texts, jf, indent=2)

    print(f"Saved to: {txt_path} and {json_path}")


# --- MAIN LOOP ---
running = True
while running:
    mouse_x, mouse_y = pygame.mouse.get_pos()
    sidebar_x = SCREEN_WIDTH - SIDEBAR_WIDTH

    avail_w = SCREEN_WIDTH - SIDEBAR_WIDTH
    avail_h = SCREEN_HEIGHT
    base_tile_size = min(avail_w / grid_cols, avail_h / grid_rows)
    current_tile_size = base_tile_size * zoom_level

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # --- 1. START MENU STATE ---
        elif app_state == "START_MENU":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                btn_new = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 30, 240, 42)
                btn_load = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 25, 240, 42)

                if btn_new.collidepoint(mouse_x, mouse_y):
                    text_input_val = "map_01"
                    app_state = "NEW_MAP_NAME"
                elif btn_load.collidepoint(mouse_x, mouse_y):
                    app_state = "LOAD_MAP_SELECT"

        # --- 2. NEW MAP NAME INPUT STATE ---
        elif app_state == "NEW_MAP_NAME":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if text_input_val.strip():
                        map_filename = text_input_val.strip()
                        grid_cols, grid_rows = DEFAULT_COLS, DEFAULT_ROWS
                        grid = [['.' for _ in range(grid_cols)] for _ in range(grid_rows)]
                        sign_texts = {}
                        reset_pan_zoom()
                        app_state = "EDITOR"
                elif event.key == pygame.K_BACKSPACE:
                    text_input_val = text_input_val[:-1]
                elif event.key == pygame.K_ESCAPE:
                    app_state = "START_MENU"
                elif len(text_input_val) < 20 and event.unicode.isprintable():
                    text_input_val += event.unicode

        # --- 3. LOAD MAP SELECTION STATE ---
        elif app_state == "LOAD_MAP_SELECT":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                maps_list = get_maps_list()
                item_y = 180
                for f_name in maps_list:
                    item_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, item_y, 300, 32)
                    if item_rect.collidepoint(mouse_x, mouse_y):
                        load_map_from_file(f_name)
                        break
                    item_y += 38

                back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 60, 120, 32)
                if back_btn.collidepoint(mouse_x, mouse_y):
                    app_state = "START_MENU"

        # --- 4. SIGN TEXT MODAL STATE ---
        elif app_state == "SIGN_TEXT_MODAL":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if editing_sign_coord:
                        sign_texts[editing_sign_coord] = text_input_val
                    app_state = "EDITOR"
                elif event.key == pygame.K_BACKSPACE:
                    text_input_val = text_input_val[:-1]
                elif event.key == pygame.K_ESCAPE:
                    app_state = "EDITOR"
                elif len(text_input_val) < 80 and event.unicode.isprintable():
                    text_input_val += event.unicode

        # --- 5. EDITOR STATE ---
        elif app_state == "EDITOR":
            keys = pygame.key.get_pressed()

            # MOUSE WHEEL ZOOMING
            if event.type == pygame.MOUSEWHEEL and mouse_x < sidebar_x:
                zoom_factor = 1.15 if event.y > 0 else 0.85
                old_zoom = zoom_level
                zoom_level = max(0.5, min(6.0, zoom_level * zoom_factor))

                if old_zoom != zoom_level:
                    pan_offset_x = mouse_x - (mouse_x - pan_offset_x) * (zoom_level / old_zoom)
                    pan_offset_y = mouse_y - (mouse_y - pan_offset_y) * (zoom_level / old_zoom)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_pan_zoom()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2 or (event.button == 1 and keys[pygame.K_SPACE] and mouse_x < sidebar_x):
                    is_panning = True
                    pan_start_pos = (mouse_x, mouse_y)

                # SIDEBAR INTERACTION
                elif mouse_x >= sidebar_x:
                    if event.button == 1:
                        # Tab Switching Header
                        tab_w = 72
                        tab_objs_rect = pygame.Rect(sidebar_x + 12, 40, tab_w, 24)
                        tab_cfg_rect = pygame.Rect(sidebar_x + 88, 40, tab_w, 24)
                        tab_tls_rect = pygame.Rect(sidebar_x + 164, 40, tab_w, 24)

                        if tab_objs_rect.collidepoint(mouse_x, mouse_y):
                            sidebar_tab = "OBJECTS"
                        elif tab_cfg_rect.collidepoint(mouse_x, mouse_y):
                            sidebar_tab = "CONFIGS"
                        elif tab_tls_rect.collidepoint(mouse_x, mouse_y):
                            sidebar_tab = "TOOLS"

                        # TAB 1: OBJECTS
                        elif sidebar_tab == "OBJECTS":
                            btn_y = 80
                            for item in OBJECT_ITEMS:
                                if isinstance(item, str):
                                    btn_y += 20
                                    continue
                                btn_rect = pygame.Rect(sidebar_x + 12, btn_y, 225, 28)
                                if btn_rect.collidepoint(mouse_x, mouse_y):
                                    selected_tool = item['char']
                                btn_y += 32

                        # TAB 2: CONFIGS
                        elif sidebar_tab == "CONFIGS":
                            btn_y = 80
                            for item in CONFIG_ITEMS:
                                btn_rect = pygame.Rect(sidebar_x + 12, btn_y, 225, 28)
                                if btn_rect.collidepoint(mouse_x, mouse_y):
                                    selected_tool = item['char']
                                btn_y += 32

                            # Canvas Size Adjust
                            if pygame.Rect(sidebar_x + 120, 190, 24, 22).collidepoint(mouse_x, mouse_y):
                                resize_grid(grid_cols - 1, grid_rows)
                            elif pygame.Rect(sidebar_x + 185, 190, 24, 22).collidepoint(mouse_x, mouse_y):
                                resize_grid(grid_cols + 1, grid_rows)

                            if pygame.Rect(sidebar_x + 120, 218, 24, 22).collidepoint(mouse_x, mouse_y):
                                resize_grid(grid_cols, grid_rows - 1)
                            elif pygame.Rect(sidebar_x + 185, 218, 24, 22).collidepoint(mouse_x, mouse_y):
                                resize_grid(grid_cols, grid_rows + 1)

                            # Switch Map Dropdown
                            dropdown_rect = pygame.Rect(sidebar_x + 12, 280, 225, 26)
                            if dropdown_rect.collidepoint(mouse_x, mouse_y):
                                dropdown_open = not dropdown_open
                            elif dropdown_open:
                                item_y = 308
                                for f_name in get_maps_list():
                                    item_rect = pygame.Rect(sidebar_x + 12, item_y, 225, 22)
                                    if item_rect.collidepoint(mouse_x, mouse_y):
                                        load_map_from_file(f_name)
                                        dropdown_open = False
                                        break
                                    item_y += 24

                        # TAB 3: TOOLS
                        elif sidebar_tab == "TOOLS":
                            # Pen Size Buttons
                            p1_rect = pygame.Rect(sidebar_x + 12, 110, 68, 26)
                            p2_rect = pygame.Rect(sidebar_x + 88, 110, 68, 26)
                            p3_rect = pygame.Rect(sidebar_x + 164, 110, 68, 26)

                            if p1_rect.collidepoint(mouse_x, mouse_y): pen_size = 1
                            elif p2_rect.collidepoint(mouse_x, mouse_y): pen_size = 2
                            elif p3_rect.collidepoint(mouse_x, mouse_y): pen_size = 3

                            # Auto Border Wall Button
                            border_btn = pygame.Rect(sidebar_x + 12, 180, 225, 32)
                            if border_btn.collidepoint(mouse_x, mouse_y):
                                auto_add_border_walls()

                        # Universal Save Button
                        save_rect = pygame.Rect(sidebar_x + 12, SCREEN_HEIGHT - 45, 225, 32)
                        if save_rect.collidepoint(mouse_x, mouse_y):
                            save_map_to_file()

                # SCALED CANVAS PAINTING
                elif mouse_x < sidebar_x and not keys[pygame.K_SPACE]:
                    rel_x = mouse_x - pan_offset_x
                    rel_y = mouse_y - pan_offset_y
                    c = int(rel_x // current_tile_size)
                    r = int(rel_y // current_tile_size)

                    if 0 <= r < grid_rows and 0 <= c < grid_cols:
                        if event.button == 1:     # Left Click = Place
                            paint_brush(r, c, selected_tool)
                        elif event.button == 3:   # Right Click = Erase
                            paint_brush(r, c, '.')

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2 or event.button == 1:
                    is_panning = False

            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    dx = mouse_x - pan_start_pos[0]
                    dy = mouse_y - pan_start_pos[1]
                    pan_offset_x += dx
                    pan_offset_y += dy
                    pan_start_pos = (mouse_x, mouse_y)
                elif mouse_x < sidebar_x and not keys[pygame.K_SPACE]:
                    rel_x = mouse_x - pan_offset_x
                    rel_y = mouse_y - pan_offset_y
                    c = int(rel_x // current_tile_size)
                    r = int(rel_y // current_tile_size)

                    if 0 <= r < grid_rows and 0 <= c < grid_cols:
                        if event.buttons[0] and selected_tool != 'S':
                            paint_brush(r, c, selected_tool)
                        elif event.buttons[2]:
                            paint_brush(r, c, '.')

    # ==================== RENDERING ====================
    screen.fill((12, 10, 16))

    # 1. START MENU DISPLAY
    if app_state == "START_MENU":
        title_txt = title_font.render("DUNGEON MAP BUILDER", True, (240, 190, 40))
        screen.blit(title_txt, title_txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 80)))

        btn_new = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 - 30, 240, 42)
        btn_load = pygame.Rect(SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2 + 25, 240, 42)

        pygame.draw.rect(screen, (45, 180, 90), btn_new, border_radius=6)
        pygame.draw.rect(screen, (55, 50, 75), btn_load, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 240), btn_load, 1, border_radius=6)

        new_lbl = font.render("CREATE NEW MAP", True, (10, 20, 10))
        load_lbl = font.render("LOAD EXISTING MAP", True, (240, 240, 250))

        screen.blit(new_lbl, new_lbl.get_rect(center=btn_new.center))
        screen.blit(load_lbl, load_lbl.get_rect(center=btn_load.center))

    # 2. NEW MAP NAME DISPLAY
    elif app_state == "NEW_MAP_NAME":
        hdr = title_font.render("ENTER NEW MAP NAME", True, (240, 190, 40))
        screen.blit(hdr, hdr.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)))

        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 10, 280, 36)
        pygame.draw.rect(screen, (25, 22, 34), input_box, border_radius=4)
        pygame.draw.rect(screen, (240, 190, 40), input_box, 2, border_radius=4)

        txt_surf = font.render(text_input_val + "_", True, (255, 255, 255))
        screen.blit(txt_surf, (input_box.x + 12, input_box.y + 10))

        hint = small_font.render("Press [ENTER] to Confirm | [ESC] Cancel", True, (140, 140, 160))
        screen.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 42)))

    # 3. LOAD MAP SELECTION DISPLAY
    elif app_state == "LOAD_MAP_SELECT":
        hdr = title_font.render("SELECT MAP TO LOAD", True, (240, 190, 40))
        screen.blit(hdr, hdr.get_rect(center=(SCREEN_WIDTH // 2, 130)))

        maps_list = get_maps_list()
        item_y = 180
        if not maps_list:
            empty_txt = font.render("No maps found in /maps directory!", True, (200, 100, 100))
            screen.blit(empty_txt, empty_txt.get_rect(center=(SCREEN_WIDTH // 2, 220)))
        else:
            for f_name in maps_list:
                item_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, item_y, 300, 32)
                pygame.draw.rect(screen, (35, 30, 48), item_rect, border_radius=4)
                pygame.draw.rect(screen, (80, 70, 100), item_rect, 1, border_radius=4)

                f_txt = font.render(f_name, True, (240, 240, 250))
                screen.blit(f_txt, (item_rect.x + 14, item_rect.y + 8))
                item_y += 38

        back_btn = pygame.Rect(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 60, 120, 32)
        pygame.draw.rect(screen, (60, 50, 70), back_btn, border_radius=4)
        b_txt = font.render("BACK", True, (220, 220, 230))
        screen.blit(b_txt, b_txt.get_rect(center=back_btn.center))

    # 4. EDITOR & SIGN MODAL DISPLAY
    elif app_state in ["EDITOR", "SIGN_TEXT_MODAL"]:
        # Render Scaled Grid Tiles
        for r in range(grid_rows):
            for c in range(grid_cols):
                char = grid[r][c]
                rx = pan_offset_x + c * current_tile_size
                ry = pan_offset_y + r * current_tile_size

                if rx + current_tile_size < 0 or rx > sidebar_x or ry + current_tile_size < 0 or ry > SCREEN_HEIGHT:
                    continue

                rect = pygame.Rect(rx, ry, current_tile_size, current_tile_size)

                tile_color = (20, 17, 26)
                for item in OBJECT_ITEMS + CONFIG_ITEMS:
                    if isinstance(item, dict) and item['char'] == char:
                        tile_color = item['color']
                        break

                pygame.draw.rect(screen, tile_color, rect)
                pygame.draw.rect(screen, (30, 28, 38), rect, 1)

                if char in ['S', 'P', 'X', '1'] and current_tile_size >= 10:
                    txt = small_font.render(char, True, (255, 255, 255))
                    screen.blit(txt, txt.get_rect(center=rect.center))

        # --- CURSOR PEN SIZE PREVIEW INDICATOR ---
        if mouse_x < sidebar_x:
            rel_x = mouse_x - pan_offset_x
            rel_y = mouse_y - pan_offset_y
            cur_c = int(rel_x // current_tile_size)
            cur_r = int(rel_y // current_tile_size)

            half = pen_size // 2
            start_c = cur_c - half
            start_r = cur_r - half

            indicator_x = pan_offset_x + start_c * current_tile_size
            indicator_y = pan_offset_y + start_r * current_tile_size
            indicator_w = current_tile_size * pen_size
            indicator_h = current_tile_size * pen_size

            indicator_rect = pygame.Rect(indicator_x, indicator_y, indicator_w, indicator_h)
            pygame.draw.rect(screen, (255, 220, 80), indicator_rect, 2)

        # Render Sidebar
        sidebar_rect = pygame.Rect(sidebar_x, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, (22, 18, 28), sidebar_rect)
        pygame.draw.line(screen, (50, 45, 60), (sidebar_x, 0), (sidebar_x, SCREEN_HEIGHT), 2)

        # Header Title
        title_surf = font.render(f"MAP: {map_filename}", True, (240, 190, 40))
        screen.blit(title_surf, (sidebar_x + 12, 12))

        # TAB SELECTION HEADERS
        tab_w = 72
        tab_objs_rect = pygame.Rect(sidebar_x + 12, 40, tab_w, 24)
        tab_cfg_rect = pygame.Rect(sidebar_x + 88, 40, tab_w, 24)
        tab_tls_rect = pygame.Rect(sidebar_x + 164, 40, tab_w, 24)

        for rect, name, tab_key in [(tab_objs_rect, "Objects", "OBJECTS"), (tab_cfg_rect, "Configs", "CONFIGS"), (tab_tls_rect, "Tools", "TOOLS")]:
            is_active = (sidebar_tab == tab_key)
            pygame.draw.rect(screen, (55, 50, 75) if is_active else (35, 30, 45), rect, border_radius=3)
            pygame.draw.rect(screen, (255, 200, 50) if is_active else (60, 55, 75), rect, 1, border_radius=3)
            t_lbl = small_font.render(name, True, (255, 255, 255) if is_active else (160, 160, 180))
            screen.blit(t_lbl, t_lbl.get_rect(center=rect.center))

        # --- TAB CONTENT: OBJECTS ---
        if sidebar_tab == "OBJECTS":
            btn_y = 80
            for item in OBJECT_ITEMS:
                if isinstance(item, str):
                    cat_lbl = small_font.render(item, True, (240, 190, 40))
                    screen.blit(cat_lbl, (sidebar_x + 12, btn_y))
                    btn_y += 20
                    continue

                char = item['char']
                is_selected = (selected_tool == char)
                btn_rect = pygame.Rect(sidebar_x + 12, btn_y, 225, 28)

                pygame.draw.rect(screen, (35, 30, 45) if not is_selected else (55, 50, 75), btn_rect, border_radius=4)
                pygame.draw.rect(screen, (255, 200, 50) if is_selected else (60, 55, 75), btn_rect, 2 if is_selected else 1, border_radius=4)

                if char in PREVIEWS:
                    screen.blit(PREVIEWS[char], (btn_rect.x + 6, btn_rect.y + 4))

                name_txt = font.render(item['name'], True, (255, 255, 255) if is_selected else (190, 190, 200))
                screen.blit(name_txt, (btn_rect.x + 34, btn_rect.y + 5))

                sym_txt = font.render(item['symbol'], True, (255, 200, 50) if is_selected else (120, 120, 140))
                screen.blit(sym_txt, (btn_rect.right - sym_txt.get_width() - 8, btn_rect.y + 5))

                btn_y += 32

        # --- TAB CONTENT: CONFIGS ---
        elif sidebar_tab == "CONFIGS":
            btn_y = 80
            for item in CONFIG_ITEMS:
                char = item['char']
                is_selected = (selected_tool == char)
                btn_rect = pygame.Rect(sidebar_x + 12, btn_y, 225, 28)

                pygame.draw.rect(screen, (35, 30, 45) if not is_selected else (55, 50, 75), btn_rect, border_radius=4)
                pygame.draw.rect(screen, (255, 200, 50) if is_selected else (60, 55, 75), btn_rect, 2 if is_selected else 1, border_radius=4)

                spawn_box = pygame.Rect(btn_rect.x + 6, btn_rect.y + 4, 20, 20)
                pygame.draw.rect(screen, item['color'], spawn_box, border_radius=2)

                name_txt = font.render(item['name'], True, (255, 255, 255) if is_selected else (190, 190, 200))
                screen.blit(name_txt, (btn_rect.x + 34, btn_rect.y + 5))

                sym_txt = font.render(item['symbol'], True, (255, 200, 50) if is_selected else (120, 120, 140))
                screen.blit(sym_txt, (btn_rect.right - sym_txt.get_width() - 8, btn_rect.y + 5))

                btn_y += 32

            pygame.draw.line(screen, (60, 55, 75), (sidebar_x + 12, 160), (SCREEN_WIDTH - 12, 160), 1)

            # Canvas Resizer
            size_hdr = font.render(f"CANVAS SIZE: {grid_cols} x {grid_rows}", True, (240, 190, 40))
            screen.blit(size_hdr, (sidebar_x + 12, 170))

            w_lbl = small_font.render("Cols (W):", True, (180, 180, 200))
            screen.blit(w_lbl, (sidebar_x + 12, 194))
            
            btn_w_dec = pygame.Rect(sidebar_x + 120, 190, 24, 22)
            btn_w_inc = pygame.Rect(sidebar_x + 185, 190, 24, 22)
            pygame.draw.rect(screen, (45, 40, 60), btn_w_dec, border_radius=3)
            pygame.draw.rect(screen, (45, 40, 60), btn_w_inc, border_radius=3)
            screen.blit(font.render("-", True, (255, 255, 255)), (btn_w_dec.x + 8, btn_w_dec.y + 2))
            screen.blit(font.render("+", True, (255, 255, 255)), (btn_w_inc.x + 7, btn_w_inc.y + 2))
            screen.blit(font.render(str(grid_cols), True, (255, 220, 100)), (sidebar_x + 150, 192))

            h_lbl = small_font.render("Rows (H):", True, (180, 180, 200))
            screen.blit(h_lbl, (sidebar_x + 12, 222))

            btn_h_dec = pygame.Rect(sidebar_x + 120, 218, 24, 22)
            btn_h_inc = pygame.Rect(sidebar_x + 185, 218, 24, 22)
            pygame.draw.rect(screen, (45, 40, 60), btn_h_dec, border_radius=3)
            pygame.draw.rect(screen, (45, 40, 60), btn_h_inc, border_radius=3)
            screen.blit(font.render("-", True, (255, 255, 255)), (btn_h_dec.x + 8, btn_h_dec.y + 2))
            screen.blit(font.render("+", True, (255, 255, 255)), (btn_h_inc.x + 7, btn_h_inc.y + 2))
            screen.blit(font.render(str(grid_rows), True, (255, 220, 100)), (sidebar_x + 150, 220))

            pygame.draw.line(screen, (60, 55, 75), (sidebar_x + 12, 260), (SCREEN_WIDTH - 12, 260), 1)

            # Switch Map Dropdown
            dropdown_rect = pygame.Rect(sidebar_x + 12, 280, 225, 26)
            pygame.draw.rect(screen, (35, 30, 45), dropdown_rect, border_radius=3)
            pygame.draw.rect(screen, (100, 90, 120), dropdown_rect, 1, border_radius=3)
            
            dd_txt = small_font.render(f"Switch File: {map_filename}.txt v", True, (220, 220, 240))
            screen.blit(dd_txt, (dropdown_rect.x + 8, dropdown_rect.y + 6))

            if dropdown_open:
                item_y = 308
                for f_name in get_maps_list():
                    item_rect = pygame.Rect(sidebar_x + 12, item_y, 225, 22)
                    pygame.draw.rect(screen, (45, 40, 60), item_rect)
                    pygame.draw.rect(screen, (80, 70, 100), item_rect, 1)
                    
                    f_txt = small_font.render(f_name, True, (240, 240, 250))
                    screen.blit(f_txt, (item_rect.x + 8, item_rect.y + 3))
                    item_y += 24

        # --- TAB CONTENT: TOOLS ---
        elif sidebar_tab == "TOOLS":
            p_hdr = font.render("PEN BRUSH SIZE:", True, (240, 190, 40))
            screen.blit(p_hdr, (sidebar_x + 12, 80))

            p1_rect = pygame.Rect(sidebar_x + 12, 110, 68, 26)
            p2_rect = pygame.Rect(sidebar_x + 88, 110, 68, 26)
            p3_rect = pygame.Rect(sidebar_x + 164, 110, 68, 26)

            for rect, p_val in [(p1_rect, 1), (p2_rect, 2), (p3_rect, 3)]:
                is_p_sel = (pen_size == p_val)
                pygame.draw.rect(screen, (55, 50, 75) if is_p_sel else (35, 30, 45), rect, border_radius=4)
                pygame.draw.rect(screen, (255, 200, 50) if is_p_sel else (60, 55, 75), rect, 2 if is_p_sel else 1, border_radius=4)
                p_txt = small_font.render(f"{p_val}x{p_val}", True, (255, 255, 255) if is_p_sel else (160, 160, 180))
                screen.blit(p_txt, p_txt.get_rect(center=rect.center))

            pygame.draw.line(screen, (60, 55, 75), (sidebar_x + 12, 155), (SCREEN_WIDTH - 12, 155), 1)

            # Auto Border Wall Button
            border_btn = pygame.Rect(sidebar_x + 12, 180, 225, 32)
            pygame.draw.rect(screen, (65, 55, 85), border_btn, border_radius=4)
            pygame.draw.rect(screen, (140, 120, 170), border_btn, 1, border_radius=4)
            b_lbl = font.render("AUTO BORDER WALL", True, (240, 230, 255))
            screen.blit(b_lbl, b_lbl.get_rect(center=border_btn.center))

        # Save Button
        save_rect = pygame.Rect(sidebar_x + 12, SCREEN_HEIGHT - 45, 225, 32)
        pygame.draw.rect(screen, (45, 180, 90), save_rect, border_radius=4)
        save_txt = font.render("SAVE MAP", True, (10, 20, 10))
        screen.blit(save_txt, save_txt.get_rect(center=save_rect.center))

        # In-Game Sign Text Modal
        if app_state == "SIGN_TEXT_MODAL":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            box_w, box_h = 420, 130
            modal_box = pygame.Rect(SCREEN_WIDTH // 2 - box_w // 2, SCREEN_HEIGHT // 2 - box_h // 2, box_w, box_h)
            pygame.draw.rect(screen, (22, 18, 28), modal_box, border_radius=6)
            pygame.draw.rect(screen, (240, 190, 40), modal_box, 2, border_radius=6)

            m_title = font.render(f"EDIT SIGN MESSAGE ({editing_sign_coord}):", True, (240, 190, 40))
            screen.blit(m_title, (modal_box.x + 16, modal_box.y + 16))

            t_box = pygame.Rect(modal_box.x + 16, modal_box.y + 45, box_w - 32, 32)
            pygame.draw.rect(screen, (12, 10, 16), t_box, border_radius=3)
            pygame.draw.rect(screen, (100, 90, 120), t_box, 1, border_radius=3)

            in_txt = font.render(text_input_val + "_", True, (255, 255, 255))
            screen.blit(in_txt, (t_box.x + 8, t_box.y + 7))

            h_txt = small_font.render("Press [ENTER] to Save | [ESC] Cancel", True, (150, 145, 165))
            screen.blit(h_txt, (modal_box.x + 16, modal_box.y + 92))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()