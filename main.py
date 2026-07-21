import pygame
import sys
from map_loader import load_random_map, draw_dungeon, TILE_SIZE
from minimap import draw_minimap
from player import PlayerStats
from weapons.sword.sword import Sword
from fog import FogOfWar

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dungeon Crawler")
clock = pygame.time.Clock()

ZOOM = 2.8
MAP_WIDTH, MAP_HEIGHT = 1600, 1200
world_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))

FLOOR_COLOR = (15, 12, 20)
VOID_COLOR = (8, 6, 10)  # Dark void color for area outside level borders
PLAYER_COLOR = (50, 230, 110)
CHEST_COLOR = (240, 190, 40)
TEXT_COLOR = (255, 255, 255)

pos_x = 0.0
pos_y = 0.0

def reset_game():
    global pos_x, pos_y
    walls, torches, player_start, exit_start, file_name = load_random_map("maps")

    player_size = 12
    offset = (TILE_SIZE - player_size) // 2
    
    start_x = player_start[0] * TILE_SIZE + offset
    start_y = player_start[1] * TILE_SIZE + offset
    
    player_rect = pygame.Rect(start_x, start_y, player_size, player_size)

    pos_x = float(start_x)
    pos_y = float(start_y)

    exit_x = exit_start[0] * TILE_SIZE + 6
    exit_y = exit_start[1] * TILE_SIZE + 6
    chest_rect = pygame.Rect(exit_x, exit_y, 28, 28)

    return walls, torches, player_rect, chest_rect, file_name

walls, torches, player_rect, chest_rect, map_name = reset_game()
sword = Sword()
player_stats = PlayerStats()
fog = FogOfWar(vision_radius=260)

font = pygame.font.SysFont("Arial", 20)
small_font = pygame.font.SysFont("Arial", 14)
game_won = False

show_minimap = True
minimap_alpha = 220.0
TARGET_ALPHA = 220.0

def move_player_exact(rect, dx, dy, walls):
    global pos_x, pos_y

    pos_x += dx
    rect.x = round(pos_x)
    for wall in walls:
        if rect.colliderect(wall):
            if dx > 0: rect.right = wall.left
            if dx < 0: rect.left = wall.right
            pos_x = float(rect.x)

    pos_y += dy
    rect.y = round(pos_y)
    for wall in walls:
        if rect.colliderect(wall):
            if dy > 0: rect.bottom = wall.top
            if dy < 0: rect.top = wall.bottom
            pos_y = float(rect.y)

running = True
while running:
    view_w = SCREEN_WIDTH / ZOOM
    view_h = SCREEN_HEIGHT / ZOOM

    # 1. ALWAYS KEEP PLAYER DEAD-CENTER (Unclamped Camera)
    cam_x = player_rect.centerx - (view_w / 2)
    cam_y = player_rect.centery - (view_h / 2)

    screen_mouse_x, screen_mouse_y = pygame.mouse.get_pos()
    mouse_world = pygame.Vector2(
        cam_x + (screen_mouse_x / ZOOM),
        cam_y + (screen_mouse_y / ZOOM)
    )

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                sword.start_press()
            elif event.button == 3:
                player_vec = pygame.Vector2(player_rect.centerx, player_rect.centery)
                sword.trigger_parry(player_vec, mouse_world)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                player_vec = pygame.Vector2(player_rect.centerx, player_rect.centery)
                sword.release_attack(player_vec, mouse_world, player_stats)
            elif event.button == 3:
                sword.release_parry()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                walls, torches, player_rect, chest_rect, map_name = reset_game()
                sword = Sword()
                player_stats = PlayerStats()
                game_won = False
            elif event.key == pygame.K_m:
                show_minimap = not show_minimap
                TARGET_ALPHA = 220.0 if show_minimap else 0.0

    minimap_alpha += (TARGET_ALPHA - minimap_alpha) * 0.15

    player_stats.update()

    if not game_won:
        if not sword.is_dashing:
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071

            move_player_exact(player_rect, dx * player_stats.move_speed, dy * player_stats.move_speed, walls)

        sword.update(player_rect, mouse_world, move_player_exact, walls)

        if player_rect.colliderect(chest_rect):
            game_won = True

    # 2. RENDER WORLD & TORCHES TO LEVEL SURFACE
    world_surface.fill(FLOOR_COLOR)
    draw_dungeon(world_surface, walls, torches)
    pygame.draw.rect(world_surface, CHEST_COLOR, chest_rect, border_radius=4)
    pygame.draw.rect(world_surface, PLAYER_COLOR, player_rect, border_radius=2)
    
    sword.draw(world_surface, player_rect, mouse_world)
    fog.draw(world_surface, player_rect, walls, torches)

    # 3. CAMERA VIEW SURFACE (Render off-map void gracefully)
    camera_view = pygame.Surface((view_w, view_h), pygame.SRCALPHA)
    camera_view.fill((*VOID_COLOR, 255))

    map_rect = pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT)
    cam_rect = pygame.Rect(cam_x, cam_y, view_w, view_h)
    
    overlap_rect = cam_rect.clip(map_rect)
    
    if overlap_rect.width > 0 and overlap_rect.height > 0:
        sub_surface = world_surface.subsurface(overlap_rect)
        dest_x = overlap_rect.x - cam_x
        dest_y = overlap_rect.y - cam_y
        camera_view.blit(sub_surface, (dest_x, dest_y))

    scaled_surface = pygame.transform.smoothscale(camera_view, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_surface, (0, 0))

    # 4. HUD OVERLAY
    info_text = font.render(f"Map: {map_name} | Left-Click: Swing/Thrust | Right-Click: Parry", True, TEXT_COLOR)
    screen.blit(info_text, (20, 15))

    player_stats.draw_hud(screen, font)
    draw_minimap(screen, walls, player_rect, chest_rect, minimap_alpha, font)

    current_fps = int(clock.get_fps())
    fps_text = small_font.render(f"FPS: {current_fps}", True, (150, 255, 150))
    fps_x = SCREEN_WIDTH - fps_text.get_width() - 15
    fps_y = SCREEN_HEIGHT - fps_text.get_height() - 10
    screen.blit(fps_text, (fps_x, fps_y))

    if game_won:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        win_text = font.render("TREASURE LOCATED! Press 'R' for Next Map", True, CHEST_COLOR)
        screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()