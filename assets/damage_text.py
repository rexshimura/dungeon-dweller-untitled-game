import pygame

class DamageText:
    def __init__(self, x, y, amount, color=(255, 70, 70), is_player=False):
        self.world_x = x
        self.world_y = y
        self.amount = amount
        self.color = color
        
        self.lifetime = 45  # Slightly longer duration to enjoy the bigger text!
        self.max_lifetime = 45
        self.float_offset_y = 0.0
        self.is_player = is_player

        # Increased font size (from 18 -> 25)
        self.font = pygame.font.SysFont("Trebuchet MS", 25, bold=True)

    def update(self):
        self.lifetime -= 1
        self.float_offset_y -= 0.7  # Smooth upward float

    def draw(self, screen, camera_offset=(0, 0), zoom=1.0):
        if self.lifetime <= 0:
            return

        cam_x, cam_y = camera_offset
        screen_x = int((self.world_x - cam_x) * zoom)
        screen_y = int((self.world_y + self.float_offset_y - cam_y) * zoom)

        # Smooth Alpha Fade Out
        alpha_ratio = max(0.0, min(1.0, self.lifetime / self.max_lifetime))
        alpha_val = int(255 * alpha_ratio)

        txt_str = f"-{self.amount}"
        txt_surf = self.font.render(txt_str, True, self.color)
        
        # Transparent surface pass for vector alpha blending
        alpha_surf = pygame.Surface((txt_surf.get_width(), txt_surf.get_height()), pygame.SRCALPHA)
        alpha_surf.blit(txt_surf, (0, 0))
        alpha_surf.set_alpha(alpha_val)

        # Center the larger text right over the entity
        screen.blit(alpha_surf, (screen_x - (txt_surf.get_width() // 2), screen_y))


class DamageTextManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DamageTextManager, cls).__new__(cls)
            cls._instance.texts = []
        return cls._instance

    def add_text(self, x, y, amount, color=(200, 205, 210), is_player=False):
        self.texts.append(DamageText(x, y, amount, color, is_player))

    def update(self):
        for t in self.texts[:]:
            t.update()
            if t.lifetime <= 0:
                self.texts.remove(t)

    def draw(self, screen, camera_offset=(0, 0), zoom=1.0):
        for t in self.texts:
            t.draw(screen, camera_offset, zoom)

    def clear(self):
        self.texts.clear()