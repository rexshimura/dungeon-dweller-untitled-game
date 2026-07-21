import os
import pygame

class LevelSelectMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.area_font = pygame.font.SysFont("Georgia", 32, bold=True)
        self.sub_font = pygame.font.SysFont("Arial", 16, bold=True)
        self.font = pygame.font.SysFont("Arial", 20, bold=True)

        self.buttons = []

    def refresh_maps(self, maps_folder="maps"):
        """Scans the maps directory for .txt map files and sorts them alphabetically."""
        self.buttons.clear()
        if not os.path.exists(maps_folder):
            os.makedirs(maps_folder)

        map_files = sorted([f for f in os.listdir(maps_folder) if f.endswith(".txt")])

        btn_w, btn_h = 300, 44
        start_y = 230  # Positioned below the area title banner

        for idx, file_name in enumerate(map_files):
            clean_name = os.path.splitext(file_name)[0]
            
            # Format display label (e.g., "level_01" -> "LEVEL 1")
            clean_lvl = clean_name.replace("_", " ").replace("level", "Level").strip()
            formatted_parts = [p.lstrip("0") if p.isdigit() else p for p in clean_lvl.split()]
            display_title = " ".join(formatted_parts).upper()

            center_x = self.screen_width // 2 - btn_w // 2
            y = start_y + idx * (btn_h + 12)

            rect = pygame.Rect(center_x, y, btn_w, btn_h)
            self.buttons.append({"rect": rect, "file": file_name, "title": display_title})

        # Back Button
        back_rect = pygame.Rect(self.screen_width // 2 - 60, self.screen_height - 70, 120, 36)
        self.buttons.append({"rect": back_rect, "file": None, "title": "BACK"})

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.buttons:
                if btn["rect"].collidepoint(mouse_pos):
                    if btn["title"] == "BACK":
                        return "MAIN_MENU"
                    else:
                        return btn["file"]  # Returns map filename e.g., "level_01.txt"
        return None

    def draw(self, surface):
        # Dark Background
        surface.fill((12, 10, 16))

        center_x = self.screen_width // 2

        # 1. Main Area Title Header
        area_title = self.area_font.render("GRIMSTONE FORTRESS", True, (240, 200, 80))
        surface.blit(area_title, area_title.get_rect(center=(center_x, 90)))

        # 2. Gold Separator Line
        line_w = area_title.get_width() + 40
        pygame.draw.line(surface, (240, 190, 40), (center_x - line_w // 2, 120), (center_x + line_w // 2, 120), 2)

        # 3. Subtitle Header
        sub_title = self.sub_font.render("SELECT LEVEL", True, (180, 180, 195))
        surface.blit(sub_title, sub_title.get_rect(center=(center_x, 145)))

        mouse_pos = pygame.mouse.get_pos()

        # 4. Render Level Buttons
        for btn in self.buttons:
            rect = btn["rect"]
            is_hovered = rect.collidepoint(mouse_pos)
            is_back = btn["title"] == "BACK"

            if is_back:
                bg_color = (70, 50, 60) if is_hovered else (45, 35, 45)
                border_color = (180, 80, 80) if is_hovered else (80, 60, 70)
                text_color = (255, 255, 255)
            else:
                bg_color = (55, 50, 75) if is_hovered else (35, 30, 45)
                border_color = (255, 200, 50) if is_hovered else (60, 55, 75)
                text_color = (255, 255, 255) if is_hovered else (200, 200, 220)

            pygame.draw.rect(surface, bg_color, rect, border_radius=6)
            pygame.draw.rect(surface, border_color, rect, 2 if is_hovered else 1, border_radius=6)

            lbl = self.font.render(btn["title"], True, text_color)
            surface.blit(lbl, lbl.get_rect(center=rect.center))