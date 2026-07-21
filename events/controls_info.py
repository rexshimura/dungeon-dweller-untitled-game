import pygame

class ControlsInfoOverlay:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.small_font = pygame.font.SysFont("Arial", 12)

        self.visible = False  # Hidden by default
        self.anim_progress = 0.0  # 0.0 = Collapsed/Indicator, 1.0 = Fully Expanded

        self.lines = [
            "LMB - Slash",
            "Hold LMB - Thrust",
            "Hold RMB - Parry / Block",
            "[I] Hide Controls"
        ]

    def toggle(self):
        """Toggles the controls overlay visibility."""
        self.visible = not self.visible

    def update(self):
        """Smoothly interpolates the animation progress toward target state."""
        target = 1.0 if self.visible else 0.0
        self.anim_progress += (target - self.anim_progress) * 0.15

    def draw(self, surface):
        padding = 8
        line_spacing = 4

        # Pre-render text lines
        text_surfs = [self.small_font.render(line, True, (220, 220, 230)) for line in self.lines]
        box_w = max(surf.get_width() for surf in text_surfs) + (padding * 2)
        box_h = sum(surf.get_height() for surf in text_surfs) + (line_spacing * (len(self.lines) - 1)) + (padding * 2)

        # Positioned lower middle-left
        overlay_y = (self.screen_height // 2 + 50)

        # 1. Render Expanding Animated Panel
        if self.anim_progress > 0.01:
            anim_x = int(-box_w + (15 + box_w) * self.anim_progress)
            alpha_val = int(140 * self.anim_progress)

            overlay_box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            overlay_box.fill((15, 12, 22, alpha_val))
            pygame.draw.rect(overlay_box, (80, 70, 100, int(180 * self.anim_progress)), (0, 0, box_w, box_h), 1, border_radius=4)

            y_off = padding
            for surf in text_surfs:
                s_copy = surf.copy()
                s_copy.set_alpha(int(255 * self.anim_progress))
                overlay_box.blit(s_copy, (padding, y_off))
                y_off += surf.get_height() + line_spacing

            surface.blit(overlay_box, (anim_x, overlay_y))

        # 2. Render Small Collapsed Indicator
        if self.anim_progress < 0.99:
            ind_alpha = int(255 * (1.0 - self.anim_progress))
            ind_surf = self.small_font.render("[I] Controls Info", True, (160, 160, 180))
            ind_box = pygame.Rect(15, overlay_y + (box_h // 2) - 12, ind_surf.get_width() + 12, 24)

            bg_ind = pygame.Surface((ind_box.width, ind_box.height), pygame.SRCALPHA)
            bg_ind.fill((15, 12, 22, int(120 * (1.0 - self.anim_progress))))
            pygame.draw.rect(bg_ind, (60, 55, 75, int(160 * (1.0 - self.anim_progress))), (0, 0, ind_box.width, ind_box.height), 1, border_radius=3)

            ind_text_copy = ind_surf.copy()
            ind_text_copy.set_alpha(ind_alpha)

            surface.blit(bg_ind, (ind_box.x, ind_box.y))
            surface.blit(ind_text_copy, (ind_box.x + 6, ind_box.y + 4))