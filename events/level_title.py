import pygame

class LevelTitleBanner:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.title_font = pygame.font.SysFont("Georgia", 28, bold=True)
        self.level_font = pygame.font.SysFont("Arial", 16, bold=True)

        self.active = False
        self.timer = 0
        self.duration = 180  # Display duration in frames (3 seconds at 60 FPS)
        self.alpha = 0.0

        self.area_name = "Grimstone Fortress"
        self.level_number = "Level 1"

    def trigger(self, area_name="Grimstone Fortress", level_name="level_01"):
        """Starts the banner animation with the given area and level names."""
        self.area_name = area_name
        
        # Clean up level string e.g. "level_01" -> "Level 1"
        clean_lvl = level_name.replace("_", " ").replace("level", "Level").strip()
        formatted_parts = [p.lstrip("0") if p.isdigit() else p for p in clean_lvl.split()]
        self.level_number = " ".join(formatted_parts)

        self.active = True
        self.timer = self.duration
        self.alpha = 0.0

    def update(self):
        if not self.active:
            return

        self.timer -= 1
        if self.timer <= 0:
            self.active = False
            return

        # Calculate Smooth Fade-In and Fade-Out Alpha
        elapsed = self.duration - self.timer
        fade_frames = 30  # 0.5 sec fade duration
        
        if elapsed < fade_frames:
            self.alpha = (elapsed / fade_frames) * 255.0  # Fade In
        elif self.timer < fade_frames:
            self.alpha = (self.timer / fade_frames) * 255.0  # Fade Out
        else:
            self.alpha = 255.0  # Full opacity

    def draw(self, surface):
        if not self.active or self.alpha <= 0:
            return

        # Render Text Surfaces
        area_surf = self.title_font.render(self.area_name.upper(), True, (240, 200, 80))
        level_surf = self.level_font.render(self.level_number.upper(), True, (200, 200, 210))

        line_w = max(area_surf.get_width(), level_surf.get_width()) + 40
        line_h = 2

        # Combine into a single transparent Surface
        total_w = line_w + 40
        total_h = area_surf.get_height() + level_surf.get_height() + 25

        banner_surf = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
        banner_surf.fill((0, 0, 0, 0))  # Transparent background

        center_x = total_w // 2
        
        # 1. Render Location Title
        a_rect = area_surf.get_rect(center=(center_x, area_surf.get_height() // 2))
        banner_surf.blit(area_surf, a_rect)

        # 2. Render Separator Line
        line_y = area_surf.get_height() + 6
        pygame.draw.line(banner_surf, (240, 190, 40, int(self.alpha)), (center_x - line_w // 2, line_y), (center_x + line_w // 2, line_y), line_h)

        # 3. Render Level Subtitle
        l_rect = level_surf.get_rect(center=(center_x, line_y + 14 + level_surf.get_height() // 2))
        banner_surf.blit(level_surf, l_rect)

        # Apply Master Alpha Fade to Banner
        banner_surf.set_alpha(int(self.alpha))

        # Position at Upper Center of Screen
        screen_pos = (self.screen_width // 2 - total_w // 2, 80)
        surface.blit(banner_surf, screen_pos)