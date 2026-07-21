import pygame

class LoadingScreen:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        self.progress = 0.0          
        self.load_speed = 0.015      
        self.mode = "GENERATE"        # "GENERATE" or "REGENERATE"
        self.is_finished = False
        
        self.fade_alpha = 0          
        self.is_fading = False
        self.fade_speed = 14         
        
        self.font_title = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 12)

    def start(self, mode="GENERATE"):
        """Resets progress and starts loading sequence with selected mode."""
        self.mode = mode
        self.progress = 0.0
        self.is_finished = False
        self.fade_alpha = 0
        self.is_fading = False
        # Reset loading speed slightly faster for regenerations
        self.load_speed = 0.025 if mode == "REGENERATE" else 0.015

    def update(self):
        """Updates progress bar fill and handles transition fading."""
        if not self.is_finished:
            if self.progress < 1.0:
                self.progress = min(1.0, self.progress + self.load_speed)
            else:
                self.is_fading = True

            if self.is_fading:
                self.fade_alpha += self.fade_speed
                if self.fade_alpha >= 255:
                    self.fade_alpha = 255
                    self.is_finished = True

    def draw(self, surface):
        """Renders progress bar, mode text, and transition fade overlay."""
        surface.fill((10, 8, 14))

        # Title / Status Text based on mode
        if self.mode == "REGENERATE":
            status_text = "REBUILDING DUNGEON LAYOUT..." if self.progress < 1.0 else "READY!"
            color_theme = (240, 140, 40)
        else:
            status_text = "GENERATING DUNGEON..." if self.progress < 1.0 else "ENTERING..."
            color_theme = (45, 180, 90)

        txt_surf = self.font_title.render(status_text, True, color_theme)
        surface.blit(txt_surf, txt_surf.get_rect(center=(self.width // 2, self.height // 2 - 40)))

        # Progress Bar Dimensions
        bar_w, bar_h = 320, 18
        bar_x = (self.width - bar_w) // 2
        bar_y = self.height // 2 + 10

        # Background Track
        track_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        pygame.draw.rect(surface, (20, 16, 26), track_rect, border_radius=4)
        pygame.draw.rect(surface, (60, 50, 75), track_rect, 1, border_radius=4)

        # Fill Progress
        fill_w = int((bar_w - 4) * self.progress)
        if fill_w > 0:
            fill_rect = pygame.Rect(bar_x + 2, bar_y + 2, fill_w, bar_h - 4)
            pygame.draw.rect(surface, color_theme, fill_rect, border_radius=3)

        # Percentage Text
        pct_text = f"{int(self.progress * 100)}%"
        pct_surf = self.font_small.render(pct_text, True, (220, 220, 240))
        surface.blit(pct_surf, pct_surf.get_rect(center=(self.width // 2, bar_y + bar_h + 18)))

        # Fade Transition Overlay
        if self.is_fading:
            fade_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, self.fade_alpha))
            surface.blit(fade_surf, (0, 0))