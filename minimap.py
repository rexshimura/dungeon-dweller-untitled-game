import pygame

COLOR_HUD_BG = (18, 18, 22)
COLOR_MINI_WALL = (180, 180, 195)
COLOR_MINI_PLAYER = (50, 230, 110)
COLOR_MINI_EXIT = (255, 80, 180)
COLOR_GRID_LINE = (35, 35, 45)
COLOR_INDICATOR = (50, 230, 110)

RADAR_DIAMETER = 110
RADAR_RADIUS = 360

badge_font = None

def get_badge_font():
    global badge_font
    if badge_font is None:
        badge_font = pygame.font.SysFont("Arial", 11)
    return badge_font

def draw_minimap(screen, walls, player_rect, chest_rect, alpha, font):
    if alpha <= 0:
        return

    base_alpha = int(alpha * 0.75)
    padding = 15
    small_font = get_badge_font()

    badge_text = small_font.render("[M] MAP", True, COLOR_INDICATOR)
    badge_surface = pygame.Surface((badge_text.get_width() + 6, badge_text.get_height() + 2), pygame.SRCALPHA)
    badge_surface.fill((12, 12, 16, int(base_alpha * 0.8)))
    pygame.draw.rect(badge_surface, COLOR_INDICATOR, badge_surface.get_rect(), 1, border_radius=2)
    badge_surface.blit(badge_text, (3, 1))
    
    badge_x = screen.get_width() - badge_surface.get_width() - padding
    badge_y = padding
    screen.blit(badge_surface, (badge_x, badge_y))

    radar_y = badge_y + badge_surface.get_height() + 6
    radar_x = screen.get_width() - RADAR_DIAMETER - padding

    raw_radar = pygame.Surface((RADAR_DIAMETER, RADAR_DIAMETER), pygame.SRCALPHA)
    raw_radar.fill((*COLOR_HUD_BG, base_alpha))

    scale = RADAR_DIAMETER / (RADAR_RADIUS * 2)
    center_offset = RADAR_DIAMETER / 2
    px, py = player_rect.centerx, player_rect.centery

    for offset in range(-RADAR_RADIUS, RADAR_RADIUS, 80):
        grid_pos = offset * scale + center_offset
        pygame.draw.line(raw_radar, (*COLOR_GRID_LINE, int(base_alpha * 0.4)), (grid_pos, 0), (grid_pos, RADAR_DIAMETER))
        pygame.draw.line(raw_radar, (*COLOR_GRID_LINE, int(base_alpha * 0.4)), (0, grid_pos), (RADAR_DIAMETER, grid_pos))

    for wall in walls:
        if abs(wall.centerx - px) < RADAR_RADIUS + 60 and abs(wall.centery - py) < RADAR_RADIUS + 60:
            rel_x = (wall.x - px) * scale + center_offset
            rel_y = (wall.y - py) * scale + center_offset
            rel_w = max(1, wall.width * scale)
            rel_h = max(1, wall.height * scale)
            
            pygame.draw.rect(raw_radar, (*COLOR_MINI_WALL, base_alpha), (rel_x, rel_y, rel_w, rel_h))

    ex_rel_x = (chest_rect.centerx - px) * scale + center_offset
    ex_rel_y = (chest_rect.centery - py) * scale + center_offset
    if 0 <= ex_rel_x <= RADAR_DIAMETER and 0 <= ex_rel_y <= RADAR_DIAMETER:
        pygame.draw.circle(raw_radar, (*COLOR_MINI_EXIT, base_alpha), (int(ex_rel_x), int(ex_rel_y)), 3)

    pygame.draw.circle(raw_radar, (*COLOR_MINI_PLAYER, base_alpha), (int(center_offset), int(center_offset)), 3)

    circle_mask = pygame.Surface((RADAR_DIAMETER, RADAR_DIAMETER), pygame.SRCALPHA)
    rad = RADAR_DIAMETER // 2
    for r in range(rad, 0, -1):
        circle_alpha = int(base_alpha * (1.0 - (r / rad) ** 6))
        pygame.draw.circle(circle_mask, (255, 255, 255, circle_alpha), (rad, rad), r)

    raw_radar.blit(circle_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(raw_radar, (radar_x, radar_y))