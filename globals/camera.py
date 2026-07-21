import pygame
from globals.config import SCREEN_WIDTH, SCREEN_HEIGHT, ZOOM, VOID_COLOR


class Camera:
    def __init__(self):
        self.view_w = SCREEN_WIDTH / ZOOM
        self.view_h = SCREEN_HEIGHT / ZOOM
        self.cam_x = 0.0
        self.cam_y = 0.0

    def update(self, player_rect):
        """Centers camera on player position."""
        self.cam_x = player_rect.centerx - (self.view_w / 2)
        self.cam_y = player_rect.centery - (self.view_h / 2)

    def get_mouse_world(self):
        """Translates screen mouse coordinates to world coordinates."""
        screen_mouse_x, screen_mouse_y = pygame.mouse.get_pos()
        return pygame.Vector2(
            self.cam_x + (screen_mouse_x / ZOOM),
            self.cam_y + (screen_mouse_y / ZOOM)
        )

    def render(self, target_screen, world_surface, map_w, map_h):
        """Clips and scales the world surface dynamically to fit the map bounds."""
        camera_view = pygame.Surface((self.view_w, self.view_h), pygame.SRCALPHA)
        camera_view.fill((*VOID_COLOR, 255))

        map_rect = pygame.Rect(0, 0, map_w, map_h)
        cam_rect = pygame.Rect(self.cam_x, self.cam_y, self.view_w, self.view_h)

        overlap_rect = cam_rect.clip(map_rect)
        if overlap_rect.width > 0 and overlap_rect.height > 0:
            sub_surface = world_surface.subsurface(overlap_rect)
            dest_x = overlap_rect.x - self.cam_x
            dest_y = overlap_rect.y - self.cam_y
            camera_view.blit(sub_surface, (dest_x, dest_y))

        scaled_surface = pygame.transform.smoothscale(camera_view, (SCREEN_WIDTH, SCREEN_HEIGHT))
        target_screen.blit(scaled_surface, (0, 0))