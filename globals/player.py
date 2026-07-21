import pygame

class PlayerStats:
    def __init__(self):
        # Stats
        self.max_hp = 100
        self.current_hp = 100
        
        self.max_mp = 5
        self.current_mp = 5.0  # Float for smooth regeneration
        self.mp_regen_rate = 0.015  # Recovers 1 MP roughly every 1.1 seconds
        
        self.base_damage = 10
        self.move_speed = 1.2  # Reduced walk speed for closer camera view

    def update(self):
        """Regenerate MP over time up to max_mp."""
        if self.current_mp < self.max_mp:
            self.current_mp = min(self.max_mp, self.current_mp + self.mp_regen_rate)

    def can_use_mp(self, cost=1):
        """Checks if the player has enough integer MP for an action."""
        return int(self.current_mp) >= cost

    def consume_mp(self, cost=1):
        """Deducts MP if available."""
        if self.can_use_mp(cost):
            self.current_mp -= cost
            return True
        return False

    def draw_hud(self, surface, font):
        """Renders compact HP/MP bars in the bottom-left corner."""
        screen_h = surface.get_height()
        
        # Sized down for a sleeker look
        bar_w, bar_h = 120, 10
        
        # Placed in the bottom left corner
        start_x = 15
        hp_y = screen_h - 38
        mp_y = screen_h - 22

        # 1. DRAW HP BAR (Vibrant Green)
        hp_ratio = self.current_hp / self.max_hp
        pygame.draw.rect(surface, (20, 35, 25), (start_x, hp_y, bar_w, bar_h), border_radius=2)
        pygame.draw.rect(surface, (45, 205, 85), (start_x, hp_y, int(bar_w * hp_ratio), bar_h), border_radius=2)
        pygame.draw.rect(surface, (120, 180, 140), (start_x, hp_y, bar_w, bar_h), 1, border_radius=2)
        
        hp_text = font.render(f"HP {int(self.current_hp)}/{self.max_hp}", True, (220, 255, 230))
        surface.blit(hp_text, (start_x + bar_w + 8, hp_y - 2))

        # 2. DRAW MP PIP BLOCKS (Cyan / Blue)
        pip_w = (bar_w - 8) // self.max_mp
        
        for i in range(self.max_mp):
            pip_x = start_x + i * (pip_w + 2)
            # Background slot
            pygame.draw.rect(surface, (15, 25, 35), (pip_x, mp_y, pip_w, bar_h - 2), border_radius=2)
            
            # Filled Pip check
            if i < int(self.current_mp):
                pygame.draw.rect(surface, (40, 180, 255), (pip_x, mp_y, pip_w, bar_h - 2), border_radius=2)
            elif i == int(self.current_mp):
                # Partial charge progress
                partial = self.current_mp - int(self.current_mp)
                pygame.draw.rect(surface, (20, 100, 160), (pip_x, mp_y, int(pip_w * partial), bar_h - 2), border_radius=2)
                
            pygame.draw.rect(surface, (90, 150, 200), (pip_x, mp_y, pip_w, bar_h - 2), 1, border_radius=2)

        mp_text = font.render(f"MP {int(self.current_mp)}/{self.max_mp}", True, (100, 210, 255))
        surface.blit(mp_text, (start_x + bar_w + 8, mp_y - 2))