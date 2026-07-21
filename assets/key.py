import pygame

class KeyTile:
    def __init__(self, rect, key_id="gold_key"):
        self.rect = rect
        self.key_id = key_id
        self.collected = False

    def draw(self, surface):
        if not self.collected:
            # Gold key visual
            pygame.draw.circle(surface, (255, 215, 0), (self.rect.centerx - 2, self.rect.centery), 3)
            pygame.draw.rect(surface, (255, 215, 0), (self.rect.centerx - 1, self.rect.centery, 6, 2))