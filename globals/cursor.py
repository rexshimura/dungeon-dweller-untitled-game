import pygame

class CustomCursor:
    def __init__(self):
        # Hide default OS mouse cursor
        pygame.mouse.set_visible(False)
        self.color_inner = (255, 230, 100)
        self.color_outer = (255, 140, 20, 120)

    def draw(self, surface):
        mx, my = pygame.mouse.get_pos()
        
        # Outer soft glow circle
        glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, self.color_outer, (8, 8), 7)
        surface.blit(glow_surf, (mx - 8, my - 8))
        
        # Inner sharp dot
        pygame.draw.circle(surface, self.color_inner, (mx, my), 3)
        pygame.draw.circle(surface, (10, 8, 14), (mx, my), 3, 1)