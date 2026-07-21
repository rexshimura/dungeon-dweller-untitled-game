import pygame

# Darker, weathered wood colors
COLOR_SIGN_POST = (55, 30, 15)
COLOR_SIGN_WOOD = (85, 48, 22)
COLOR_SIGN_BORDER = (45, 22, 10)
COLOR_SIGN_TEXT_LINES = (50, 28, 12)  # Scribble lines on wooden board


class SignTile:
    def __init__(self, rect, text="A mysterious sign..."):
        self.rect = rect
        self.pos = pygame.Vector2(rect.centerx, rect.centery)
        self.text = text
        self.is_near = False

    def check_proximity(self, player_pos, interact_radius=32.0):
        """Checks if player is close enough to interact."""
        dist = pygame.Vector2(player_pos).distance_to(self.pos)
        self.is_near = dist <= interact_radius
        return self.is_near

    def draw(self, surface):
        """Renders a darker, detailed signpost with written text lines."""
        # Wooden post
        pygame.draw.rect(surface, COLOR_SIGN_POST, (self.rect.centerx - 2, self.rect.bottom - 8, 4, 8))
        
        # Wooden sign board
        board_rect = pygame.Rect(self.rect.x + 4, self.rect.y + 4, 20, 14)
        pygame.draw.rect(surface, COLOR_SIGN_WOOD, board_rect, border_radius=2)
        pygame.draw.rect(surface, COLOR_SIGN_BORDER, board_rect, 1, border_radius=2)

        # Weathered text scribbles on the sign board
        pygame.draw.line(surface, COLOR_SIGN_TEXT_LINES, (board_rect.x + 4, board_rect.y + 4), (board_rect.x + 16, board_rect.y + 4), 1)
        pygame.draw.line(surface, COLOR_SIGN_TEXT_LINES, (board_rect.x + 4, board_rect.y + 7), (board_rect.x + 13, board_rect.y + 7), 1)
        pygame.draw.line(surface, COLOR_SIGN_TEXT_LINES, (board_rect.x + 4, board_rect.y + 10), (board_rect.x + 15, board_rect.y + 10), 1)

    def draw_prompt(self, surface, font, camera_offset=(0, 0), zoom=2.8):
        """Draws floating '[E] Read' prompt above sign if player is near."""
        if not self.is_near:
            return

        screen_x = (self.rect.centerx - camera_offset[0]) * zoom
        screen_y = (self.rect.top - 12 - camera_offset[1]) * zoom

        prompt_surf = font.render("[E] Read", True, (255, 220, 100))
        bg_rect = prompt_surf.get_rect(center=(screen_x, screen_y))
        
        padding_rect = bg_rect.inflate(10, 6)
        pygame.draw.rect(surface, (12, 10, 16), padding_rect, border_radius=4)
        pygame.draw.rect(surface, (240, 180, 50), padding_rect, 1, border_radius=4)
        surface.blit(prompt_surf, bg_rect)


class DialogModal:
    def __init__(self):
        self.active = False
        self.text = ""
        self.small_close_font = pygame.font.SysFont("Arial", 11)

    def show(self, text):
        self.text = text
        self.active = True

    def hide(self):
        self.active = False

    def draw(self, surface, font):
        """Renders an RPG dialog modal box elevated above the HUD bars."""
        if not self.active:
            return

        screen_w, screen_h = surface.get_size()
        modal_w, modal_h = screen_w - 120, 115
        modal_x = (screen_w - modal_w) // 2
        modal_y = screen_h - modal_h - 75

        modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        # 1. Drop Shadow
        shadow_rect = modal_rect.move(4, 4)
        pygame.draw.rect(surface, (0, 0, 0, 160), shadow_rect, border_radius=8)

        # 2. Main Background Panel
        pygame.draw.rect(surface, (18, 16, 24), modal_rect, border_radius=8)

        # 3. Double Retro Border
        pygame.draw.rect(surface, (230, 175, 45), modal_rect, 2, border_radius=8)
        inner_border = modal_rect.inflate(-6, -6)
        pygame.draw.rect(surface, (120, 80, 25), inner_border, 1, border_radius=6)

        # 4. Header Icon & Title
        icon_rect = pygame.Rect(modal_x + 16, modal_y + 14, 16, 12)
        pygame.draw.rect(surface, (110, 60, 20), icon_rect, border_radius=2)
        pygame.draw.rect(surface, (240, 180, 50), icon_rect, 1, border_radius=2)

        title_surf = font.render("???", True, (240, 195, 60))
        surface.blit(title_surf, (modal_x + 40, modal_y + 10))

        # Divider Line
        pygame.draw.line(
            surface, 
            (70, 55, 35), 
            (modal_x + 16, modal_y + 32), 
            (modal_x + modal_w - 16, modal_y + 32), 
            1
        )

        # 5. Body Text Word Wrap
        words = self.text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.size(test_line)[0] < modal_w - 40:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        for i, line in enumerate(lines[:3]):
            line_surf = font.render(line, True, (225, 225, 235))
            surface.blit(line_surf, (modal_x + 20, modal_y + 42 + i * 20))

        # 6. Close Prompt Hint (Smaller font & shifted up)
        close_surf = self.small_close_font.render("[E] Close", True, (160, 155, 175))
        surface.blit(close_surf, (modal_x + modal_w - close_surf.get_width() - 20, modal_y + modal_h - 28))