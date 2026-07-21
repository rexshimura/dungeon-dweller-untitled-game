import os
import json
import copy
import math
import pygame

from assets.torch import TorchTile
from assets.sign import SignTile

pygame.init()

# Fixed Window Dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
SIDEBAR_WIDTH = 250

MIN_DIM = 10
MAX_DIM = 100
DEFAULT_COLS = 30
DEFAULT_ROWS = 20

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dungeon Map Builder")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 11, bold=True)
small_font = pygame.font.SysFont("Arial", 10)
title_font = pygame.font.SysFont("Arial", 18, bold=True)

# 5 Color Tiers for Doors and Keys
KEY_TIERS = [
    {"name": "Locked Door Gray",   "color": (160, 160, 170), "door": "L0", "key": "K0"},
    {"name": "Locked Door Green",  "color": (45, 205, 85),   "door": "L1", "key": "K1"},
    {"name": "Locked Door Blue",   "color": (40, 180, 255),  "door": "L2", "key": "K2"},
    {"name": "Locked Door Red",    "color": (230, 60, 60),   "door": "L3", "key": "K3"},
    {"name": "Locked Door Yellow", "color": (255, 215, 0),   "door": "L4", "key": "K4"},
]

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

    door_preview = pygame.Surface((20, 20))
    door_preview.fill((140, 85, 35))
    pygame.draw.rect(door_preview, (50, 30, 10), (0, 0, 20, 20), 1)

    return {
        '#': wall_preview,
        '.': floor_preview,
        'S': sign_preview,
        '1': torch_preview,
        'D': door_preview
    }

PREVIEWS = create_sidebar_previews()

# --- REORGANIZED TAB DEFINITIONS ---
OBJECT_ITEMS = [
    "-- Main",
    {'char': '#', 'name': 'Wall',        'symbol': '[#]', 'color': (42, 38, 54)},
    {'char': '.', 'name': 'Floor',       'symbol': '[.]', 'color': (20, 17, 26)},
    "-- Assets",
    {'char': 'D', 'name': 'Door (Open)', 'symbol': '[D]', 'color': (140, 85, 35)},
    {'char': 'S', 'name': 'Sign',        'symbol': '[S]', 'color': (180, 110, 40)},
    {'char': '1', 'name': 'Torch',       'symbol': '[1]', 'color': (255, 140, 20)},
    "-- Conditional Assets",
    {'char': 'L0', 'name': 'Locked Door Gray',   'symbol': '[L0]', 'color': (160, 160, 170), 'tier': 0},
    {'char': 'L1', 'name': 'Locked Door Green',  'symbol': '[L1]', 'color': (45, 205, 85),   'tier': 1},
    {'char': 'L2', 'name': 'Locked Door Blue',   'symbol': '[L2]', 'color': (40, 180, 255),  'tier': 2},
    {'char': 'L3', 'name': 'Locked Door Red',    'symbol': '[L3]', 'color': (230, 60, 60),   'tier': 3},
    {'char': 'L4', 'name': 'Locked Door Yellow', 'symbol': '[L4]', 'color': (255, 215, 0),   'tier': 4},
]

CONFIG_ITEMS = [
    {'char': 'P', 'name': 'Player Spawn', 'symbol': '[P]', 'color': (50, 230, 110)},
    {'char': 'X', 'name': 'Exit',         'symbol': '[X]', 'color': (240, 190, 40)},
]

# --- STATE VARIABLES ---
app_state = "START_MENU"
sidebar_tab = "OBJECTS"

grid_cols = DEFAULT_COLS
grid_rows = DEFAULT_ROWS
grid = [['.' for _ in range(grid_cols)] for _ in range(grid_rows)]
sign_texts = {}
map_filename = "map_01"
selected_tool = '#'
pen_size = 1

selected_door_coord = None
required_key_to_place = None
forced_key_tier = 0

text_input_val = "map_01"
editing_sign_coord = None
dropdown_open = False
save_error_msg = None

# Templates state
selected_template = None
active_template_name = None
is_creating_template = False
template_select_start = None
template_select_end = None
template_name_input = "room_01"

# Pan and Zoom State
zoom_level = 1.0
pan_offset_x = 0.0
pan_offset_y = 0.0
is_panning = False
pan_start_pos = (0, 0)

# --- UNDO / REDO HISTORY SYSTEM ---
undo_stack = []
redo_stack = []
MAX_HISTORY = 30


def save_state():
    global undo_stack, redo_stack
    state = {
        'grid': copy.deepcopy(grid),
        'signs': copy.deepcopy(sign_texts),
        'cols': grid_cols,
        'rows': grid_rows
    }
    undo_stack.append(state)
    if len(undo_stack) > MAX_HISTORY:
        undo_stack.pop(0)
    redo_stack.clear()


def undo():
    global grid, sign_texts, grid_cols, grid_rows, undo_stack, redo_stack
    if not undo_stack:
        return
    current_state = {
        'grid': copy.deepcopy(grid),
        'signs': copy.deepcopy(sign_texts),
        'cols': grid_cols,
        'rows': grid_rows
    }
    redo_stack.append(current_state)

    last_state = undo_stack.pop()
    grid = last_state['grid']
    sign_texts = last_state['signs']
    grid_cols = last_state['cols']
    grid_rows = last_state['rows']


def redo():
    global grid, sign_texts, grid_cols, grid_rows, undo_stack, redo_stack
    if not redo_stack:
        return
    current_state = {
        'grid': copy.deepcopy(grid),
        'signs': copy.deepcopy(sign_texts),
        'cols': grid_cols,
        'rows': grid_rows
    }
    undo_stack.append(current_state)

    next_state = redo_stack.pop()
    grid = next_state['grid']
    sign_texts = next_state['signs']
    grid_cols = last_state['cols']
    grid_rows = next_state['rows']


def get_maps_list():
    if not os.path.exists("maps"):
        os.makedirs("maps")
    return [f for f in os.listdir("maps") if f.endswith(".txt")]


def get_templates_list():
    folder = os.path.join("maps", "templates")
    if not os.path.exists(folder):
        os.makedirs(folder)
    return [f for f in os.listdir(folder) if f.endswith(".json")]


def save_template_to_disk(name, temp_grid, temp_signs):
    folder = os.path.join("maps", "templates")
    if not os.path.exists(folder):
        os.makedirs(folder)
    path = os.path.join(folder, f"{name}.json")
    
    data = {
        "grid": temp_grid,
        "signs": temp_signs
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_template_from_disk(filename):
    path = os.path.join("maps", "templates", filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


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
    save_state()

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
    save_state()
    for r in range(grid_rows):
        for c in range(grid_cols):
            if r == 0 or r == grid_rows - 1 or c == 0 or c == grid_cols - 1:
                grid[r][c] = '#'
                sign_texts.pop(f"{r},{c}", None)


def clear_canvas():
    global grid, sign_texts
    save_state()
    grid = [['.' for _ in range(grid_cols)] for _ in range(grid_rows)]
    sign_texts.clear()


def enforce_single_unique_tile(tool):
    if tool in ['P', 'X'] or tool.startswith('L') or tool.startswith('K'):
        for r in range(grid_rows):
            for c in range(grid_cols):
                if grid[r][c] == tool:
                    grid[r][c] = '.'


def tile_exists_on_map(token):
    for row in grid:
        if token in row:
            return True
    return False


def paint_brush(center_r, center_c, tool):
    global required_key_to_place, forced_key_tier, app_state
    global editing_sign_coord, text_input_val

    enforce_single_unique_tile(tool)

    half = pen_size // 2
    for dr in range(-half, half + 1 if pen_size % 2 != 0 else half):
        for dc in range(-half, half + 1 if pen_size % 2 != 0 else half):
            r, c = center_r + dr, center_c + dc
            if 0 <= r < grid_rows and 0 <= c < grid_cols:
                grid[r][c] = tool
                if tool == 'S':
                    editing_sign_coord = f"{r},{c}"
                    text_input_val = sign_texts.get(editing_sign_coord, "")
                    app_state = "SIGN_TEXT_MODAL"
                elif tool == '.':
                    sign_texts.pop(f"{r},{c}", None)

    if tool.startswith('L'):
        tier_idx = int(tool[1:])
        required_key_to_place = KEY_TIERS[tier_idx]["key"]
        forced_key_tier = tier_idx
        enforce_single_unique_tile(required_key_to_place)
        app_state = "PLACE_KEY_REQUIRED"


def stamp_template(start_r, start_c, template):
    save_state()
    temp_grid = template["grid"]
    temp_signs = template["signs"]
    t_rows = len(temp_grid)
    t_cols = len(temp_grid[0]) if t_rows > 0 else 0

    for r in range(t_rows):
        for c in range(t_cols):
            target_r = start_r + r
            target_c = start_c + c
            if 0 <= target_r < grid_rows and 0 <= target_c < grid_cols:
                char = temp_grid[r][c]
                enforce_single_unique_tile(char)
                grid[target_r][target_c] = char
                
                coord_key = f"{r},{c}"
                if coord_key in temp_signs:
                    sign_texts[f"{target_r},{target_c}"] = temp_signs[coord_key]


def load_map_from_file(filename):
    global grid_cols, grid_rows, grid, sign_texts, map_filename, app_state
    global undo_stack, redo_stack
    filepath = os.path.join("maps", filename)
    map_filename = os.path.splitext(filename)[0]

    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            lines = [line.strip().split() if ' ' in line.strip() else list(line.strip()) for line in f.readlines() if line.strip()]

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

    undo_stack.clear()
    redo_stack.clear()
    reset_pan_zoom()
    app_state = "EDITOR"


def save_map_to_file():
    global save_error_msg, app_state

    has_player = any('P' in cell for row in grid for cell in row)
    has_exit = any('X' in cell for row in grid for cell in row)

    if not has_player or not has_exit:
        missing = []
        if not has_player: missing.append("Player Spawn [P]")
        if not has_exit: missing.append("Exit [X]")
        save_error_msg = f"Cannot Save! Missing: {', '.join(missing)}"
        app_state = "SAVE_ERROR_MODAL"
        return

    if not os.path.exists("maps"):
        os.makedirs("maps")

    txt_path = os.path.join("maps", f"{map_filename}.txt")
    json_path = os.path.join("maps", f"{map_filename}.json")

    with open(txt_path, "w") as f:
        for row in grid:
            f.write(" ".join(row) + "\n")

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

    show_cursor = (pygame.time.get_ticks() // 500) % 2 == 0

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
            btn_confirm = pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 35, 100, 32)
            btn_cancel = pygame.Rect(SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT // 2 + 35, 100, 32)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_confirm.collidepoint(mouse_x, mouse_y):
                    if text_input_val.strip():
                        map_filename = text_input_val.strip()
                        grid_cols, grid_rows = DEFAULT_COLS, DEFAULT_ROWS
                        grid = [['.' for _ in range(grid_cols)] for _ in range(grid_rows)]
                        sign_texts = {}
                        undo_stack.clear()
                        redo_stack.clear()
                        reset_pan_zoom()
                        app_state = "EDITOR"
                elif btn_cancel.collidepoint(mouse_x, mouse_y):
                    app_state = "START_MENU"

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if text_input_val.strip():
                        map_filename = text_input_val.strip()
                        grid_cols, grid_rows = DEFAULT_COLS, DEFAULT_ROWS
                        grid = [['.' for _ in range(grid_cols)] for _ in range(grid_rows)]
                        sign_texts = {}
                        undo_stack.clear()
                        redo_stack.clear()
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

        # --- 5. FORCED KEY PLACEMENT STATE ---
        elif app_state == "PLACE_KEY_REQUIRED":
            keys = pygame.key.get_pressed()

            if event.type == pygame.MOUSEWHEEL and mouse_x < sidebar_x:
                zoom_factor = 1.15 if event.y > 0 else 0.85
                old_zoom = zoom_level
                zoom_level = max(0.5, min(6.0, zoom_level * zoom_factor))
                if old_zoom != zoom_level:
                    pan_offset_x = mouse_x - (mouse_x - pan_offset_x) * (zoom_level / old_zoom)
                    pan_offset_y = mouse_y - (mouse_y - pan_offset_y) * (zoom_level / old_zoom)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2 or (event.button == 1 and keys[pygame.K_SPACE] and mouse_x < sidebar_x):
                    is_panning = True
                    pan_start_pos = (mouse_x, mouse_y)
                elif event.button == 1 and mouse_x < sidebar_x and not keys[pygame.K_SPACE]:
                    rel_x = mouse_x - pan_offset_x
                    rel_y = mouse_y - pan_offset_y
                    c = int(rel_x // current_tile_size)
                    r = int(rel_y // current_tile_size)

                    if 0 <= r < grid_rows and 0 <= c < grid_cols:
                        save_state()
                        grid[r][c] = required_key_to_place
                        required_key_to_place = None
                        app_state = "EDITOR"

            elif event.type == pygame.MOUSEBUTTONUP and (event.button == 2 or event.button == 1):
                is_panning = False

            elif event.type == pygame.MOUSEMOTION and is_panning:
                dx = mouse_x - pan_start_pos[0]
                dy = mouse_y - pan_start_pos[1]
                pan_offset_x += dx
                pan_offset_y += dy
                pan_start_pos = (mouse_x, mouse_y)

        # --- 6. SAVE ERROR MODAL STATE ---
        elif app_state == "SAVE_ERROR_MODAL":
            box_w, box_h = 420, 130
            modal_box = pygame.Rect(SCREEN_WIDTH // 2 - box_w // 2, SCREEN_HEIGHT // 2 - box_h // 2, box_w, box_h)
            btn_ok = pygame.Rect(modal_box.centerx - 50, modal_box.y + 80, 100, 30)

            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and btn_ok.collidepoint(mouse_x, mouse_y)) or \
               (event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_ESCAPE]):
                app_state = "EDITOR"

        # --- 7. CLEAR CANVAS CONFIRMATION MODAL STATE ---
        elif app_state == "CLEAR_CANVAS_CONFIRM":
            box_w, box_h = 360, 130
            modal_box = pygame.Rect(SCREEN_WIDTH // 2 - box_w // 2, SCREEN_HEIGHT // 2 - box_h // 2, box_w, box_h)
            btn_yes = pygame.Rect(modal_box.x + 40, modal_box.y + 75, 120, 32)
            btn_no = pygame.Rect(modal_box.x + 200, modal_box.y + 75, 120, 32)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_yes.collidepoint(mouse_x, mouse_y):
                    clear_canvas()
                    app_state = "EDITOR"
                elif btn_no.collidepoint(mouse_x, mouse_y):
                    app_state = "EDITOR"
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                app_state = "EDITOR"

        # --- 8. EDITOR STATE ---
        elif app_state == "EDITOR":
            keys = pygame.key.get_pressed()

            if event.type == pygame.MOUSEWHEEL and mouse_x < sidebar_x:
                zoom_factor = 1.15 if event.y > 0 else 0.85
                old_zoom = zoom_level
                zoom_level = max(0.5, min(6.0, zoom_level * zoom_factor))

                if old_zoom != zoom_level:
                    pan_offset_x = mouse_x - (mouse_x - pan_offset_x) * (zoom_level / old_zoom)
                    pan_offset_y = mouse_y - (mouse_y - pan_offset_y) * (zoom_level / old_zoom)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                        redo()
                    else:
                        undo()
                elif event.key == pygame.K_y and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
                    redo()
                elif event.key == pygame.K_r:
                    reset_pan_zoom()
                elif event.key == pygame.K_ESCAPE:
                    selected_template = None
                    is_creating_template = False
                    selected_door_coord = None

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 2 or (event.button == 1 and keys[pygame.K_SPACE] and mouse_x < sidebar_x):
                    is_panning = True
                    pan_start_pos = (mouse_x, mouse_y)

                elif mouse_x >= sidebar_x:
                    if event.button == 1:
                        tab_w = 54
                        t1 = pygame.Rect(sidebar_x + 8, 40, tab_w, 24)
                        t2 = pygame.Rect(sidebar_x + 66, 40, tab_w, 24)
                        t3 = pygame.Rect(sidebar_x + 124, 40, tab_w, 24)
                        t4 = pygame.Rect(sidebar_x + 182, 40, tab_w, 24)

                        if t1.collidepoint(mouse_x, mouse_y): sidebar_tab = "OBJECTS"
                        elif t2.collidepoint(mouse_x, mouse_y): sidebar_tab = "CONFIGS"
                        elif t3.collidepoint(mouse_x, mouse_y): sidebar_tab = "TOOLS"
                        elif t4.collidepoint(mouse_x, mouse_y): sidebar_tab = "TEMPLATES"

                        elif sidebar_tab == "OBJECTS":
                            btn_y = 80
                            for item in OBJECT_ITEMS:
                                if isinstance(item, str):
                                    btn_y += 20
                                    continue
                                
                                char = item['char']
                                btn_rect = pygame.Rect(sidebar_x + 12, btn_y, 225, 28)
                                
                                if btn_rect.collidepoint(mouse_x, mouse_y):
                                    if not (char.startswith('L') and tile_exists_on_map(char)):
                                        selected_tool = char
                                        selected_template = None
                                
                                btn_y += 32

                        elif sidebar_tab == "CONFIGS":
                            btn_y = 80
                            for item in CONFIG_ITEMS:
                                btn_rect = pygame.Rect(sidebar_x + 12, btn_y, 225, 28)
                                if btn_rect.collidepoint(mouse_x, mouse_y):
                                    selected_tool = item['char']
                                    selected_template = None
                                btn_y += 32

                            if pygame.Rect(sidebar_x + 120, 190, 24, 22).collidepoint(mouse_x, mouse_y):
                                resize_grid(grid_cols - 1, grid_rows)
                            elif pygame.Rect(sidebar_x + 185, 190, 24, 22).collidepoint(mouse_x, mouse_y):
                                resize_grid(grid_cols + 1, grid_rows)

                            if pygame.Rect(sidebar_x + 120, 218, 24, 22).collidepoint(mouse_x, mouse_y):
                                resize_grid(grid_cols, grid_rows - 1)
                            elif pygame.Rect(sidebar_x + 185, 218, 24, 22).collidepoint(mouse_x, mouse_y):
                                resize_grid(grid_cols, grid_rows + 1)

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

                        elif sidebar_tab == "TOOLS":
                            p1_rect = pygame.Rect(sidebar_x + 12, 110, 68, 26)
                            p2_rect = pygame.Rect(sidebar_x + 88, 110, 68, 26)
                            p3_rect = pygame.Rect(sidebar_x + 164, 110, 68, 26)

                            if p1_rect.collidepoint(mouse_x, mouse_y): pen_size = 1
                            elif p2_rect.collidepoint(mouse_x, mouse_y): pen_size = 2
                            elif p3_rect.collidepoint(mouse_x, mouse_y): pen_size = 3

                            border_btn = pygame.Rect(sidebar_x + 12, 175, 225, 32)
                            if border_btn.collidepoint(mouse_x, mouse_y):
                                auto_add_border_walls()

                            clear_btn = pygame.Rect(sidebar_x + 12, 220, 225, 32)
                            if clear_btn.collidepoint(mouse_x, mouse_y):
                                app_state = "CLEAR_CANVAS_CONFIRM"

                        elif sidebar_tab == "TEMPLATES":
                            create_btn = pygame.Rect(sidebar_x + 12, 80, 225, 30)
                            if create_btn.collidepoint(mouse_x, mouse_y):
                                is_creating_template = True
                                selected_template = None
                                template_select_start = None
                                template_select_end = None

                            t_y = 140
                            for temp_file in get_templates_list():
                                item_rect = pygame.Rect(sidebar_x + 12, t_y, 225, 26)
                                if item_rect.collidepoint(mouse_x, mouse_y):
                                    selected_template = load_template_from_disk(temp_file)
                                    active_template_name = os.path.splitext(temp_file)[0]
                                    is_creating_template = False
                                t_y += 30

                        save_rect = pygame.Rect(sidebar_x + 12, SCREEN_HEIGHT - 45, 225, 32)
                        if save_rect.collidepoint(mouse_x, mouse_y):
                            save_map_to_file()

                elif mouse_x < sidebar_x and not keys[pygame.K_SPACE]:
                    rel_x = mouse_x - pan_offset_x
                    rel_y = mouse_y - pan_offset_y
                    c = int(rel_x // current_tile_size)
                    r = int(rel_y // current_tile_size)

                    if 0 <= r < grid_rows and 0 <= c < grid_cols:
                        clicked_tile = grid[r][c]
                        
                        # Click on an existing Sign 'S' on canvas to edit its text
                        if event.button == 1 and clicked_tile == 'S' and selected_tool != 'S':
                            editing_sign_coord = f"{r},{c}"
                            text_input_val = sign_texts.get(editing_sign_coord, "")
                            app_state = "SIGN_TEXT_MODAL"
                        elif event.button == 1 and clicked_tile.startswith('L') and not selected_template and not is_creating_template:
                            selected_door_coord = (r, c)
                        else:
                            selected_door_coord = None
                            if is_creating_template:
                                if event.button == 1:
                                    template_select_start = (r, c)
                                    template_select_end = (r, c)
                            elif selected_template:
                                if event.button == 1:
                                    stamp_template(r, c, selected_template)
                                elif event.button == 3:
                                    selected_template = None
                            else:
                                if event.button in [1, 3]:
                                    save_state()
                                    paint_brush(r, c, selected_tool if event.button == 1 else '.')

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2 or event.button == 1:
                    is_panning = False
                    if is_creating_template and template_select_start and mouse_x < sidebar_x:
                        rel_x = mouse_x - pan_offset_x
                        rel_y = mouse_y - pan_offset_y
                        c = int(rel_x // current_tile_size)
                        r = int(rel_y // current_tile_size)
                        template_select_end = (max(0, min(grid_rows - 1, r)), max(0, min(grid_cols - 1, c)))
                        
                        template_name_input = "room_01"
                        app_state = "SAVE_TEMPLATE_NAME_MODAL"

            elif event.type == pygame.MOUSEMOTION:
                if is_panning:
                    dx = mouse_x - pan_start_pos[0]
                    dy = mouse_y - pan_start_pos[1]
                    pan_offset_x += dx
                    pan_offset_y += dy
                    pan_start_pos = (mouse_x, mouse_y)
                elif is_creating_template and pygame.mouse.get_pressed()[0] and template_select_start and mouse_x < sidebar_x:
                    rel_x = mouse_x - pan_offset_x
                    rel_y = mouse_y - pan_offset_y
                    c = int(rel_x // current_tile_size)
                    r = int(rel_y // current_tile_size)
                    template_select_end = (max(0, min(grid_rows - 1, r)), max(0, min(grid_cols - 1, c)))
                elif mouse_x < sidebar_x and not keys[pygame.K_SPACE] and not selected_template and not is_creating_template:
                    rel_x = mouse_x - pan_offset_x
                    rel_y = mouse_y - pan_offset_y
                    c = int(rel_x // current_tile_size)
                    r = int(rel_y // current_tile_size)

                    if 0 <= r < grid_rows and 0 <= c < grid_cols:
                        if event.buttons[0] and not selected_tool.startswith('L') and selected_tool != 'S':
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
        screen.blit(hdr, hdr.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)))

        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 140, SCREEN_HEIGHT // 2 - 15, 280, 36)
        pygame.draw.rect(screen, (25, 22, 34), input_box, border_radius=4)
        pygame.draw.rect(screen, (240, 190, 40), input_box, 2, border_radius=4)

        txt_surf = font.render(text_input_val, True, (255, 255, 255))
        screen.blit(txt_surf, (input_box.x + 12, input_box.y + 11))

        if show_cursor:
            cursor_x = input_box.x + 12 + txt_surf.get_width() + 2
            pygame.draw.line(screen, (240, 190, 40), (cursor_x, input_box.y + 8), (cursor_x, input_box.y + 26), 2)

        btn_confirm = pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 35, 100, 32)
        btn_cancel = pygame.Rect(SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT // 2 + 35, 100, 32)

        pygame.draw.rect(screen, (45, 180, 90), btn_confirm, border_radius=4)
        pygame.draw.rect(screen, (180, 60, 60), btn_cancel, border_radius=4)

        c_txt = font.render("CONFIRM", True, (10, 20, 10))
        can_txt = font.render("CANCEL", True, (255, 255, 255))

        screen.blit(c_txt, c_txt.get_rect(center=btn_confirm.center))
        screen.blit(can_txt, can_txt.get_rect(center=btn_cancel.center))

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

    # 4. EDITOR DISPLAY
    elif app_state in ["EDITOR", "SIGN_TEXT_MODAL", "SAVE_TEMPLATE_NAME_MODAL", "CLEAR_CANVAS_CONFIRM", "SAVE_ERROR_MODAL", "PLACE_KEY_REQUIRED"]:
        for r in range(grid_rows):
            for c in range(grid_cols):
                token = grid[r][c]
                rx = pan_offset_x + c * current_tile_size
                ry = pan_offset_y + r * current_tile_size

                if rx + current_tile_size < 0 or rx > sidebar_x or ry + current_tile_size < 0 or ry > SCREEN_HEIGHT:
                    continue

                rect = pygame.Rect(rx, ry, current_tile_size, current_tile_size)

                tile_color = (20, 17, 26)
                if token == '#': tile_color = (42, 38, 54)
                elif token == 'D': tile_color = (140, 85, 35)
                elif token.startswith('L'):
                    idx = int(token[1:]) if len(token) > 1 and token[1:].isdigit() else 0
                    tile_color = KEY_TIERS[min(idx, 4)]["color"]
                elif token.startswith('K'):
                    idx = int(token[1:]) if len(token) > 1 and token[1:].isdigit() else 0
                    tile_color = KEY_TIERS[min(idx, 4)]["color"]
                else:
                    for item in OBJECT_ITEMS + CONFIG_ITEMS:
                        if isinstance(item, dict) and item['char'] == token:
                            tile_color = item['color']
                            break

                pygame.draw.rect(screen, tile_color, rect)
                pygame.draw.rect(screen, (30, 28, 38), rect, 1)

                if current_tile_size >= 10:
                    lbl_str = token
                    if token.startswith('L'): lbl_str = "L"
                    elif token.startswith('K'): lbl_str = "K"
                    
                    if lbl_str in ['S', 'P', 'X', '1', 'D', 'L', 'K']:
                        txt = small_font.render(lbl_str, True, (255, 255, 255))
                        screen.blit(txt, txt.get_rect(center=rect.center))

        if selected_door_coord:
            dr, dc = selected_door_coord
            door_token = grid[dr][dc]
            if door_token.startswith('L'):
                tier_idx = int(door_token[1:])
                target_key_token = f"K{tier_idx}"
                
                key_coord = None
                for kr in range(grid_rows):
                    for kc in range(grid_cols):
                        if grid[kr][kc] == target_key_token:
                            key_coord = (kr, kc)
                            break
                    if key_coord: break

                door_px = (pan_offset_x + (dc + 0.5) * current_tile_size, pan_offset_y + (dr + 0.5) * current_tile_size)
                
                d_rect = pygame.Rect(pan_offset_x + dc * current_tile_size, pan_offset_y + dr * current_tile_size, current_tile_size, current_tile_size)
                pygame.draw.rect(screen, (255, 255, 255), d_rect, 2)

                if key_coord:
                    kr, kc = key_coord
                    key_px = (pan_offset_x + (kc + 0.5) * current_tile_size, pan_offset_y + (kr + 0.5) * current_tile_size)
                    
                    pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 100) + 155
                    k_rect = pygame.Rect(pan_offset_x + kc * current_tile_size, pan_offset_y + kr * current_tile_size, current_tile_size, current_tile_size)
                    pygame.draw.rect(screen, (255, 215, pulse), k_rect, 3)

                    pygame.draw.line(screen, (255, 215, 0), door_px, key_px, 2)

        if mouse_x < sidebar_x and app_state == "EDITOR" and not is_creating_template:
            rel_x = mouse_x - pan_offset_x
            rel_y = mouse_y - pan_offset_y
            cur_c = int(rel_x // current_tile_size)
            cur_r = int(rel_y // current_tile_size)

            half = pen_size // 2
            start_c = cur_c - half
            start_r = cur_r - half

            indicator_rect = pygame.Rect(
                pan_offset_x + start_c * current_tile_size,
                pan_offset_y + start_r * current_tile_size,
                current_tile_size * pen_size,
                current_tile_size * pen_size
            )
            pygame.draw.rect(screen, (255, 220, 80), indicator_rect, 2)

        # Render Sidebar
        sidebar_rect = pygame.Rect(sidebar_x, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(screen, (22, 18, 28), sidebar_rect)
        pygame.draw.line(screen, (50, 45, 60), (sidebar_x, 0), (sidebar_x, SCREEN_HEIGHT), 2)

        title_surf = font.render(f"MAP: {map_filename}", True, (240, 190, 40))
        screen.blit(title_surf, (sidebar_x + 12, 12))

        tab_w = 54
        t1 = pygame.Rect(sidebar_x + 8, 40, tab_w, 24)
        t2 = pygame.Rect(sidebar_x + 66, 40, tab_w, 24)
        t3 = pygame.Rect(sidebar_x + 124, 40, tab_w, 24)
        t4 = pygame.Rect(sidebar_x + 182, 40, tab_w, 24)

        for rect, name, tab_key in [(t1, "Objs", "OBJECTS"), (t2, "Cfg", "CONFIGS"), (t3, "Tools", "TOOLS"), (t4, "Tmplt", "TEMPLATES")]:
            is_active = (sidebar_tab == tab_key)
            pygame.draw.rect(screen, (55, 50, 75) if is_active else (35, 30, 45), rect, border_radius=3)
            pygame.draw.rect(screen, (255, 200, 50) if is_active else (60, 55, 75), rect, 1, border_radius=3)
            t_lbl = small_font.render(name, True, (255, 255, 255) if is_active else (160, 160, 180))
            screen.blit(t_lbl, t_lbl.get_rect(center=rect.center))

        if sidebar_tab == "OBJECTS":
            btn_y = 80
            for item in OBJECT_ITEMS:
                if isinstance(item, str):
                    cat_lbl = small_font.render(item, True, (240, 190, 40))
                    screen.blit(cat_lbl, (sidebar_x + 12, btn_y))
                    btn_y += 20
                    continue

                char = item['char']
                is_selected = (selected_tool == char and not selected_template)
                already_on_map = char.startswith('L') and tile_exists_on_map(char)
                
                btn_rect = pygame.Rect(sidebar_x + 12, btn_y, 225, 28)

                bg_color = (25, 20, 30) if already_on_map else ((55, 50, 75) if is_selected else (35, 30, 45))
                border_color = (50, 45, 60) if already_on_map else ((255, 200, 50) if is_selected else (60, 55, 75))

                pygame.draw.rect(screen, bg_color, btn_rect, border_radius=4)
                pygame.draw.rect(screen, border_color, btn_rect, 2 if is_selected else 1, border_radius=4)

                if char in PREVIEWS:
                    screen.blit(PREVIEWS[char], (btn_rect.x + 6, btn_rect.y + 4))
                elif char.startswith('L'):
                    tier_idx = item['tier']
                    icon_box = pygame.Rect(btn_rect.x + 6, btn_rect.y + 4, 20, 20)
                    pygame.draw.rect(screen, KEY_TIERS[tier_idx]["color"], icon_box, border_radius=2)

                text_color = (100, 100, 110) if already_on_map else ((255, 255, 255) if is_selected else (190, 190, 200))
                name_txt = font.render(item['name'], True, text_color)
                screen.blit(name_txt, (btn_rect.x + 34, btn_rect.y + 5))

                sym_txt = font.render(item['symbol'], True, (120, 120, 140) if not already_on_map else (80, 80, 90))
                screen.blit(sym_txt, (btn_rect.right - sym_txt.get_width() - 8, btn_rect.y + 5))

                if already_on_map:
                    check_lbl = small_font.render("✓ ON MAP", True, (120, 180, 120))
                    screen.blit(check_lbl, (btn_rect.right - check_lbl.get_width() - 8, btn_rect.y + 6))

                btn_y += 32

        elif sidebar_tab == "CONFIGS":
            btn_y = 80
            for item in CONFIG_ITEMS:
                char = item['char']
                is_selected = (selected_tool == char and not selected_template)
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

            border_btn = pygame.Rect(sidebar_x + 12, 175, 225, 32)
            pygame.draw.rect(screen, (65, 55, 85), border_btn, border_radius=4)
            pygame.draw.rect(screen, (140, 120, 170), border_btn, 1, border_radius=4)
            b_lbl = font.render("AUTO BORDER WALL", True, (240, 230, 255))
            screen.blit(b_lbl, b_lbl.get_rect(center=border_btn.center))

            clear_btn = pygame.Rect(sidebar_x + 12, 220, 225, 32)
            pygame.draw.rect(screen, (180, 50, 50), clear_btn, border_radius=4)
            pygame.draw.rect(screen, (220, 80, 80), clear_btn, 1, border_radius=4)
            c_lbl = font.render("CLEAR CANVAS", True, (255, 255, 255))
            screen.blit(c_lbl, c_lbl.get_rect(center=clear_btn.center))

            legend_txt = small_font.render("[Ctrl+Z] Undo  |  [Ctrl+Y] Redo", True, (140, 140, 160))
            screen.blit(legend_txt, (sidebar_x + 12, 270))

        save_rect = pygame.Rect(sidebar_x + 12, SCREEN_HEIGHT - 45, 225, 32)
        pygame.draw.rect(screen, (45, 180, 90), save_rect, border_radius=4)
        save_txt = font.render("SAVE MAP", True, (10, 20, 10))
        screen.blit(save_txt, save_txt.get_rect(center=save_rect.center))

        # --- SIGN TEXT EDIT MODAL ---
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

            in_txt = font.render(text_input_val, True, (255, 255, 255))
            screen.blit(in_txt, (t_box.x + 8, t_box.y + 8))

            if show_cursor:
                cursor_x = t_box.x + 8 + in_txt.get_width() + 2
                pygame.draw.line(screen, (240, 190, 40), (cursor_x, t_box.y + 6), (cursor_x, t_box.y + 24), 2)

            h_txt = small_font.render("Press [ENTER] to Save | [ESC] Cancel", True, (150, 145, 165))
            screen.blit(h_txt, (modal_box.x + 16, modal_box.y + 92))

        # Forced Key Placement Prompt Banner
        elif app_state == "PLACE_KEY_REQUIRED":
            color_name = KEY_TIERS[forced_key_tier]["name"].replace("Locked Door ", "")
            tier_color = KEY_TIERS[forced_key_tier]["color"]

            prompt_box = pygame.Rect(SCREEN_WIDTH // 2 - 220, 15, 440, 42)
            pygame.draw.rect(screen, (22, 18, 28), prompt_box, border_radius=6)
            pygame.draw.rect(screen, tier_color, prompt_box, 2, border_radius=6)

            p_txt = font.render(f"CLICK CANVAS TO PLACE MATCHING {color_name.upper()} KEY!", True, tier_color)
            screen.blit(p_txt, p_txt.get_rect(center=prompt_box.center))

        # Save Error Modal
        elif app_state == "SAVE_ERROR_MODAL":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            box_w, box_h = 420, 130
            modal_box = pygame.Rect(SCREEN_WIDTH // 2 - box_w // 2, SCREEN_HEIGHT // 2 - box_h // 2, box_w, box_h)
            pygame.draw.rect(screen, (22, 18, 28), modal_box, border_radius=6)
            pygame.draw.rect(screen, (220, 80, 80), modal_box, 2, border_radius=6)

            err_txt = font.render(save_error_msg or "Cannot Save Map!", True, (255, 120, 120))
            screen.blit(err_txt, err_txt.get_rect(center=(modal_box.centerx, modal_box.y + 40)))

            btn_ok = pygame.Rect(modal_box.centerx - 50, modal_box.y + 80, 100, 30)
            pygame.draw.rect(screen, (60, 55, 75), btn_ok, border_radius=4)
            ok_txt = font.render("OK", True, (255, 255, 255))
            screen.blit(ok_txt, ok_txt.get_rect(center=btn_ok.center))

        # Clear Canvas Confirmation Modal
        elif app_state == "CLEAR_CANVAS_CONFIRM":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            box_w, box_h = 360, 130
            modal_box = pygame.Rect(SCREEN_WIDTH // 2 - box_w // 2, SCREEN_HEIGHT // 2 - box_h // 2, box_w, box_h)
            pygame.draw.rect(screen, (22, 18, 28), modal_box, border_radius=6)
            pygame.draw.rect(screen, (220, 80, 80), modal_box, 2, border_radius=6)

            q_txt = font.render("Clear the entire canvas?", True, (240, 230, 250))
            screen.blit(q_txt, q_txt.get_rect(center=(modal_box.centerx, modal_box.y + 35)))

            btn_yes = pygame.Rect(modal_box.x + 40, modal_box.y + 75, 120, 32)
            btn_no = pygame.Rect(modal_box.x + 200, modal_box.y + 75, 120, 32)

            pygame.draw.rect(screen, (180, 50, 50), btn_yes, border_radius=4)
            pygame.draw.rect(screen, (60, 55, 75), btn_no, border_radius=4)

            y_txt = font.render("YES", True, (255, 255, 255))
            n_txt = font.render("NO", True, (220, 220, 230))

            screen.blit(y_txt, y_txt.get_rect(center=btn_yes.center))
            screen.blit(n_txt, n_txt.get_rect(center=btn_no.center))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()