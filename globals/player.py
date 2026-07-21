import pygame

KEY_COLORS = {
    "gray_key": (160, 160, 170),
    "green_key": (45, 205, 85),
    "blue_key": (40, 180, 255),
    "red_key": (230, 60, 60),
    "yellow_key": (255, 215, 0)
}

class PlayerStats:
    def __init__(self):
        # Stats
        self.max_hp = 10
        self.current_hp = 10
        
        self.max_mp = 5
        self.current_mp = 5.0
        self.mp_regen_rate = 0.003  # Slower MP regeneration rate
        
        self.base_damage = 3       # Regular Swing = 3 DMG (Thrust deals 2x = 6 DMG)
        self.move_speed = 1.3
        self.parry_speed = 0.9

        # Invincibility frames when taking damage
        self.i_frames = 0

        # Key Inventory System (Set of key IDs e.g., {"gray_key", "blue_key"})
        self.keys = set()

    def add_key(self, key_id):
        self.keys.add(key_id)

    def has_key(self, key_id):
        return key_id in self.keys

    def get_speed(self, is_parrying=False):
        return self.parry_speed if is_parrying else self.move_speed

    def update(self):
        # Countdown invincibility timer
        if self.i_frames > 0:
            self.i_frames -= 1

        # Passive MP Regeneration
        if self.current_mp < self.max_mp:
            self.current_mp = min(self.max_mp, self.current_mp + self.mp_regen_rate)

    def can_use_mp(self, cost=1):
        return int(self.current_mp) >= cost

    def consume_mp(self, cost=1):
        if self.can_use_mp(cost):
            self.current_mp -= cost
            return True
        return False

    def draw_hud(self, surface, font):
        """Renders compact HP/MP bars and key icons in the bottom-left corner."""
        screen_h = surface.get_height()
        bar_w, bar_h = 120, 10
        
        start_x = 15
        hp_y = screen_h - 38
        mp_y = screen_h - 22

        # 1. DRAW HP BAR
        hp_ratio = max(0.0, self.current_hp / self.max_hp)
        pygame.draw.rect(surface, (35, 20, 25), (start_x, hp_y, bar_w, bar_h), border_radius=2)
        pygame.draw.rect(surface, (230, 60, 60), (start_x, hp_y, int(bar_w * hp_ratio), bar_h), border_radius=2)
        pygame.draw.rect(surface, (180, 100, 100), (start_x, hp_y, bar_w, bar_h), 1, border_radius=2)
        
        hp_text = font.render(f"HP {int(self.current_hp)}/{self.max_hp}", True, (255, 220, 220))
        surface.blit(hp_text, (start_x + bar_w + 8, hp_y - 2))

        # 2. DRAW MP PIP BLOCKS
        pip_w = (bar_w - 8) // self.max_mp
        for i in range(self.max_mp):
            pip_x = start_x + i * (pip_w + 2)
            pygame.draw.rect(surface, (15, 25, 35), (pip_x, mp_y, pip_w, bar_h - 2), border_radius=2)
            
            if i < int(self.current_mp):
                pygame.draw.rect(surface, (40, 180, 255), (pip_x, mp_y, pip_w, bar_h - 2), border_radius=2)
            elif i == int(self.current_mp):
                partial = self.current_mp - int(self.current_mp)
                pygame.draw.rect(surface, (20, 100, 160), (pip_x, mp_y, int(pip_w * partial), bar_h - 2), border_radius=2)
                
            pygame.draw.rect(surface, (90, 150, 200), (pip_x, mp_y, pip_w, bar_h - 2), 1, border_radius=2)

        mp_text = font.render(f"MP {int(self.current_mp)}/{self.max_mp}", True, (100, 210, 255))
        surface.blit(mp_text, (start_x + bar_w + 8, mp_y - 2))

        # 3. DRAW COLLECTED KEY ICONS
        key_x = start_x + bar_w + 110
        key_y = mp_y + 2
        
        for key_id in sorted(self.keys):
            color = KEY_COLORS.get(key_id, (255, 215, 0))
            pygame.draw.circle(surface, color, (key_x, key_y), 3, 1)
            pygame.draw.rect(surface, color, (key_x + 2, key_y - 1, 5, 2))
            pygame.draw.rect(surface, color, (key_x + 5, key_y, 2, 2))
            key_x += 14