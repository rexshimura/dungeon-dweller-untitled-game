import pygame

KEY_COLORS = {
    "gray_key": (160, 160, 170),
    "green_key": (45, 205, 85),
    "blue_key": (40, 180, 255),
    "red_key": (230, 60, 60),
    "yellow_key": (255, 215, 0)
}

class DoorTile:
    def __init__(self, rect, is_locked=False, key_id="gray_key"):
        self.rect = rect
        self.is_locked = is_locked
        self.key_id = key_id
        self.is_open = False
        self.prompt_radius = 24
        
        self.closed_texture = self._generate_door_texture()

    def _generate_door_texture(self):
        w, h = self.rect.width, self.rect.height
        surf = pygame.Surface((w, h))
        
        base_wood = (140, 85, 35)
        surf.fill(base_wood)
        
        # Planks
        plank_w = w // 3
        for i in range(1, 3):
            pygame.draw.line(surf, (80, 45, 15), (i * plank_w, 0), (i * plank_w, h), 1)
            
        pygame.draw.rect(surf, (200, 140, 60), (0, 0, w, h), 1)
        pygame.draw.rect(surf, (50, 30, 10), (0, 0, w, h), 2)
        
        if self.is_locked:
            lock_color = KEY_COLORS.get(self.key_id, (160, 160, 170))
            # Colored Lock Plate
            pygame.draw.rect(surf, lock_color, (w // 2 - 4, h // 2 - 5, 8, 10), border_radius=2)
            pygame.draw.circle(surf, (20, 20, 20), (w // 2, h // 2 - 1), 2)
        else:
            pygame.draw.circle(surf, (60, 60, 70), (w - 6, h // 2), 2)
            
        return surf

    def check_proximity(self, player_pos):
        if self.is_open:
            return False
        door_vec = pygame.Vector2(self.rect.centerx, self.rect.centery)
        p_vec = pygame.Vector2(player_pos[0], player_pos[1])
        return door_vec.distance_to(p_vec) <= self.prompt_radius

    def try_open(self, player_keys):
        if self.is_open:
            return True
            
        if not self.is_locked:
            self.is_open = True
            return True
        elif self.key_id in player_keys:
            self.is_open = True
            player_keys.remove(self.key_id)
            return True
            
        return False

    def draw(self, surface):
        if self.is_open:
            pygame.draw.rect(surface, (12, 10, 16), self.rect)
            pygame.draw.rect(surface, (45, 30, 20), self.rect, 1)
        else:
            surface.blit(self.closed_texture, (self.rect.x, self.rect.y))

    def draw_prompt(self, surface, font, camera_offset, zoom):
        cam_x, cam_y = camera_offset
        screen_x = int((self.rect.centerx - cam_x) * zoom)
        screen_y = int((self.rect.y - 12 - cam_y) * zoom)

        color_name = self.key_id.replace("_key", "").capitalize() if self.is_locked else ""
        msg = f"[E] Needs {color_name} Key" if self.is_locked else "[E] Open Door"
        color = KEY_COLORS.get(self.key_id, (255, 255, 255)) if self.is_locked else (240, 240, 250)
        
        lbl = font.render(msg, True, color)
        bg_rect = lbl.get_rect(center=(screen_x, screen_y))
        bg_rect.inflate_ip(10, 6)

        pygame.draw.rect(surface, (15, 12, 22), bg_rect, border_radius=3)
        pygame.draw.rect(surface, (100, 80, 120), bg_rect, 1, border_radius=3)
        surface.blit(lbl, lbl.get_rect(center=(screen_x, screen_y)))