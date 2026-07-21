import pygame

class CreditsScreen:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.active = False
        
        self.font_title = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_body = pygame.font.SysFont("Arial", 14)
        self.font_small = pygame.font.SysFont("Arial", 11)

    def show(self):
        self.active = True

    def hide(self):
        self.active = False

    def handle_event(self, event):
        if not self.active:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.hide()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.hide()
            return True
        return False

    def draw(self, surface):
        if not self.active:
            return

        # Semi-transparent overlay backdrop
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        # Modal Box
        box_w, box_h = 480, 280
        box_x = (self.width - box_w) // 2
        box_y = (self.height - box_h) // 2
        modal_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        pygame.draw.rect(surface, (18, 16, 24), modal_rect, border_radius=8)
        pygame.draw.rect(surface, (230, 175, 45), modal_rect, 2, border_radius=8)

        # Header
        title_surf = self.font_title.render("--- CREDITS ---", True, (240, 195, 60))
        surface.blit(title_surf, title_surf.get_rect(center=(self.width // 2, box_y + 30)))

        # Divider line
        pygame.draw.line(surface, (70, 55, 35), (box_x + 30, box_y + 55), (box_x + box_w - 30, box_y + 55), 1)

        # Developer Info
        credits_lines = [
            ("Lead Developer & Architect:", (200, 190, 210)),
            ("John Paul P. Mahilom (Yizaha / Rexshimura)", (255, 220, 100)),
            ("", (0,0,0)),
            ("Built with:", (200, 190, 210)),
            ("Python 3 & Pygame-CE", (180, 220, 255)),
            ("Procedural Dungeon & Lighting Engine", (180, 220, 255)),
        ]

        line_y = box_y + 75
        for text, color in credits_lines:
            if text:
                lbl = self.font_body.render(text, True, color)
                surface.blit(lbl, lbl.get_rect(center=(self.width // 2, line_y)))
            line_y += 22

        # Close Hint
        hint_surf = self.font_small.render("[Click anywhere or press ESC to close]", True, (140, 135, 155))
        surface.blit(hint_surf, hint_surf.get_rect(center=(self.width // 2, box_y + box_h - 25)))