import pygame

class TabMenu:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.active = False

        self.font_title = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_button = pygame.font.SysFont("Arial", 16, bold=True)
        self.font_hint = pygame.font.SysFont("Arial", 11)

        box_w, box_h = 320, 240
        box_x = (screen_width - box_w) // 2
        box_y = (screen_height - box_h) // 2
        self.modal_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        btn_w, btn_h = 240, 38
        btn_x = (screen_width - btn_w) // 2
        self.btn_reset = pygame.Rect(btn_x, box_y + 75, btn_w, btn_h)
        self.btn_main_menu = pygame.Rect(btn_x, box_y + 125, btn_w, btn_h)
        self.btn_resume = pygame.Rect(btn_x, box_y + 175, btn_w, btn_h)

    def show(self):
        self.active = True

    def hide(self):
        self.active = False

    def handle_event(self, event):
        """Returns 'RESET', 'MAIN_MENU', or None."""
        if not self.active:
            return None

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_ESCAPE):
                self.hide()
                return None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            if self.btn_reset.collidepoint(mx, my):
                self.hide()
                return "RESET"
            elif self.btn_main_menu.collidepoint(mx, my):
                self.hide()
                return "MAIN_MENU"
            elif self.btn_resume.collidepoint(mx, my):
                self.hide()

        return None

    def draw(self, surface):
        if not self.active:
            return

        # Semi-transparent overlay backdrop
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # Main Panel
        pygame.draw.rect(surface, (18, 16, 24), self.modal_rect, border_radius=8)
        pygame.draw.rect(surface, (230, 175, 45), self.modal_rect, 2, border_radius=8)

        # Title
        title_surf = self.font_title.render("GAME PAUSED", True, (240, 195, 60))
        surface.blit(title_surf, title_surf.get_rect(center=(self.width // 2, self.modal_rect.y + 35)))

        mx, my = pygame.mouse.get_pos()

        # Render Buttons
        buttons = [
            (self.btn_reset, "RESET DUNGEON", (210, 130, 40)),
            (self.btn_main_menu, "RETURN TO MAIN MENU", (180, 60, 60)),
            (self.btn_resume, "RESUME GAME", (50, 45, 65))
        ]

        for rect, label, base_color in buttons:
            is_hover = rect.collidepoint(mx, my)
            color = tuple(min(255, c + 35) for c in base_color) if is_hover else base_color

            pygame.draw.rect(surface, color, rect, border_radius=5)
            pygame.draw.rect(
                surface, 
                (255, 220, 100) if is_hover else (70, 60, 85), 
                rect, 
                2 if is_hover else 1, 
                border_radius=5
            )

            lbl_surf = self.font_button.render(label, True, (255, 255, 255))
            surface.blit(lbl_surf, lbl_surf.get_rect(center=rect.center))