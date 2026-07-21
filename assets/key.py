import pygame

KEY_COLORS = {
    "gray_key": (160, 160, 170),
    "green_key": (45, 205, 85),
    "blue_key": (40, 180, 255),
    "red_key": (230, 60, 60),
    "yellow_key": (255, 215, 0)
}

class KeyTile:
    def __init__(self, rect, key_id="gray_key"):
        self.rect = rect
        self.key_id = key_id
        self.collected = False

    def draw(self, surface):
        if not self.collected:
            center_x, center_y = self.rect.centerx, self.rect.centery
            color = KEY_COLORS.get(self.key_id, (160, 160, 170))
            
            # Colored key rendering
            pygame.draw.circle(surface, color, (center_x - 3, center_y), 3, 1)
            pygame.draw.rect(surface, color, (center_x - 1, center_y - 1, 6, 2))
            pygame.draw.rect(surface, color, (center_x + 3, center_y, 2, 2))