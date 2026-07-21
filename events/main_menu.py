import pygame
import sys
from events.credits import CreditsScreen

class MainMenu:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        
        self.title_font = pygame.font.SysFont("Arial", 42, bold=True)
        self.button_font = pygame.font.SysFont("Arial", 18, bold=True)
        self.sub_font = pygame.font.SysFont("Arial", 12)

        self.credits_screen = CreditsScreen(screen_width, screen_height)

        # Button Layout
        btn_w, btn_h = 220, 44
        center_x = (screen_width - btn_w) // 2
        
        self.btn_play = pygame.Rect(center_x, 340, btn_w, btn_h)
        self.btn_credits = pygame.Rect(center_x, 400, btn_w, btn_h)
        self.btn_quit = pygame.Rect(center_x, 460, btn_w, btn_h)

    def handle_event(self, event):
        """Returns 'PLAY', 'QUIT', or None."""
        if self.credits_screen.active:
            self.credits_screen.handle_event(event)
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()

            if self.btn_play.collidepoint(mx, my):
                return "PLAY"
            elif self.btn_credits.collidepoint(mx, my):
                self.credits_screen.show()
            elif self.btn_quit.collidepoint(mx, my):
                return "QUIT"

        return None

    def draw(self, surface):
        surface.fill((10, 8, 14))

        # Title Banner
        title_surf = self.title_font.render("INSCRIPTION", True, (240, 190, 40))
        surface.blit(title_surf, title_surf.get_rect(center=(self.width // 2, 200)))

        sub_surf = self.sub_font.render("A Procedural Fog of War Dungeon Crawler", True, (160, 150, 180))
        surface.blit(sub_surf, sub_surf.get_rect(center=(self.width // 2, 245)))

        mx, my = pygame.mouse.get_pos()

        # Render Buttons
        buttons = [
            (self.btn_play, "PLAY", (45, 180, 90)),
            (self.btn_credits, "CREDITS", (55, 50, 75)),
            (self.btn_quit, "QUIT", (180, 60, 60))
        ]

        for rect, label, base_color in buttons:
            is_hover = rect.collidepoint(mx, my)
            color = tuple(min(255, c + 35) for c in base_color) if is_hover else base_color

            pygame.draw.rect(surface, color, rect, border_radius=6)
            pygame.draw.rect(
                surface, 
                (255, 220, 100) if is_hover else (80, 70, 95), 
                rect, 
                2 if is_hover else 1, 
                border_radius=6
            )

            lbl_surf = self.button_font.render(label, True, (255, 255, 255))
            surface.blit(lbl_surf, lbl_surf.get_rect(center=rect.center))

        # Render Credits Modal on top if active
        self.credits_screen.draw(surface)