import pygame
import math
import random

class SlimeParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-3.5, 1.0)
        self.size = random.uniform(2, 4)
        self.color = random.choice([(50, 210, 90), (120, 240, 150), (30, 170, 70)])
        self.lifetime = random.randint(15, 28)
        self.alpha = 255

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.lifetime -= 1
        if self.lifetime < 10:
            self.alpha = max(0, int((self.lifetime / 10) * 255))

    def draw(self, surface):
        if self.lifetime <= 0:
            return
        p_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (*self.color, self.alpha), (int(self.size), int(self.size)), int(self.size))
        surface.blit(p_surf, (self.x - self.size, self.y - self.size))


class SmallSlime:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 14)
        self.name = "Small Slime"
        
        # Health Stats
        self.max_hp = 12
        self.hp = 12
        self.damage = 1
        self.is_dead = False

        # AI States: "IDLE", "CHASE", "CHARGE", "LUNGE", "STUNNED"
        self.state = "IDLE"
        self.detect_radius = 180
        self.attack_range = 75
        self.speed = 0.85

        self.charge_timer = 0
        self.charge_duration = 35
        self.lunge_timer = 0
        self.lunge_duration = 18
        self.stun_timer = 0
        self.attack_cooldown = 0
        
        self.move_vec = pygame.Vector2(0, 0)
        self.lunge_dir = pygame.Vector2(0, 0)

        self.flash_timer = 0
        self.knockback_vec = pygame.Vector2(0, 0)
        self.particles = []

        # Crisp High-Res UI Fonts for 1:1 Screen Surface
        self.ui_name_font = pygame.font.SysFont("Trebuchet MS", 11, bold=True)
        self.ui_hp_font = pygame.font.SysFont("Arial", 10, bold=True)

    @property
    def hitbox(self):
        return self.rect.inflate(4, 4)

    def take_damage(self, amount, knockback_source_pos=None):
        if self.is_dead:
            return

        self.hp -= amount
        self.flash_timer = 10

        # Taking damage instantly alerts the slime!
        if self.state == "IDLE":
            self.state = "CHASE"

        if knockback_source_pos:
            s_vec = pygame.Vector2(self.rect.centerx, self.rect.centery)
            p_vec = pygame.Vector2(knockback_source_pos[0], knockback_source_pos[1])
            diff = s_vec - p_vec
            if diff.length() > 0:
                self.knockback_vec = diff.normalize() * 4.5

        if self.hp <= 0:
            self.hp = 0
            self.is_dead = True
            for _ in range(16):
                self.particles.append(SlimeParticle(self.rect.centerx, self.rect.centery))

    def trigger_parry_stun(self, player_pos):
        self.state = "STUNNED"
        self.stun_timer = 50
        self.flash_timer = 15
        
        s_vec = pygame.Vector2(self.rect.centerx, self.rect.centery)
        p_vec = pygame.Vector2(player_pos[0], player_pos[1])
        diff = s_vec - p_vec
        if diff.length() > 0:
            self.knockback_vec = diff.normalize() * 6.0

    def _has_line_of_sight(self, player_center, obstacles):
        """Casts a ray to check if any wall/door blocks view of player."""
        start = (self.rect.centerx, self.rect.centery)
        end = (player_center.x, player_center.y)
        
        for obstacle in obstacles:
            if obstacle.clipline(start, end):
                return False
        return True

    def update(self, player_rect, obstacles):
        for p in self.particles[:]:
            p.update()
            if p.lifetime <= 0:
                self.particles.remove(p)

        if self.is_dead:
            return

        if self.flash_timer > 0:
            self.flash_timer -= 1

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        if self.knockback_vec.length() > 0.1:
            self._move_exact(self.knockback_vec.x, self.knockback_vec.y, obstacles)
            self.knockback_vec *= 0.80
        else:
            self.knockback_vec = pygame.Vector2(0, 0)

        slime_center = pygame.Vector2(self.rect.centerx, self.rect.centery)
        player_center = pygame.Vector2(player_rect.centerx, player_rect.centery)
        dist_to_player = slime_center.distance_to(player_center)

        has_los = self._has_line_of_sight(player_center, obstacles)

        if self.state == "STUNNED":
            self.stun_timer -= 1
            if self.stun_timer <= 0:
                self.state = "CHASE" if has_los else "IDLE"

        elif self.state == "CHARGE":
            self.charge_timer -= 1
            if not has_los:
                self.state = "IDLE"
            elif self.charge_timer <= 0:
                self.state = "LUNGE"
                self.lunge_timer = self.lunge_duration
                dir_vec = player_center - slime_center
                self.lunge_dir = dir_vec.normalize() if dir_vec.length() > 0 else pygame.Vector2(1, 0)

        elif self.state == "LUNGE":
            self.lunge_timer -= 1
            lunge_speed = 3.8
            self._move_exact(self.lunge_dir.x * lunge_speed, self.lunge_dir.y * lunge_speed, obstacles)
            
            if self.lunge_timer <= 0:
                self.state = "CHASE" if has_los else "IDLE"
                self.attack_cooldown = random.randint(60, 90)

        else:
            # ONLY DETECT AND CHASE IF IN RANGE AND HAS LINE OF SIGHT
            if dist_to_player <= self.detect_radius and has_los:
                self.state = "CHASE"
                dir_vec = player_center - slime_center
                
                if dist_to_player <= self.attack_range and self.attack_cooldown <= 0:
                    self.state = "CHARGE"
                    self.charge_timer = self.charge_duration
                elif dir_vec.length() > 0:
                    self.move_vec = dir_vec.normalize()
                    self._move_exact(self.move_vec.x * self.speed, self.move_vec.y * self.speed, obstacles)
            else:
                self.state = "IDLE"

    def _move_exact(self, dx, dy, obstacles):
        if dx != 0:
            self.rect.x += dx
            for obstacle in obstacles:
                if self.rect.colliderect(obstacle):
                    if dx > 0: self.rect.right = obstacle.left
                    elif dx < 0: self.rect.left = obstacle.right

        if dy != 0:
            self.rect.y += dy
            for obstacle in obstacles:
                if self.rect.colliderect(obstacle):
                    if dy > 0: self.rect.bottom = obstacle.top
                    elif dy < 0: self.rect.top = obstacle.bottom

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

        if self.is_dead:
            return

        draw_rect = self.rect.copy()
        offset_y = 0
        h_scale = 0

        if self.state == "CHARGE":
            offset_y = 3
            h_scale = -3
        elif self.state == "LUNGE":
            progress = self.lunge_timer / self.lunge_duration
            offset_y = int(math.sin(progress * math.pi) * -8)
            h_scale = 2

        draw_rect.y += offset_y
        draw_rect.height += h_scale

        if self.flash_timer > 0:
            body_color = (255, 255, 255)
            core_color = (240, 220, 220)
        elif self.state == "CHARGE":
            pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.02)) * 180) + 75
            body_color = (230, pulse, 40)
            core_color = (255, 120, 30)
        elif self.state == "STUNNED":
            body_color = (130, 160, 210)
            core_color = (180, 200, 240)
        else:
            body_color = (50, 210, 90)
            core_color = (120, 240, 150)

        pygame.draw.ellipse(surface, body_color, draw_rect)
        core_rect = draw_rect.inflate(-4, -4)
        if core_rect.width > 2 and core_rect.height > 2:
            pygame.draw.ellipse(surface, core_color, core_rect)

        if self.flash_timer == 0:
            eye_y = draw_rect.centery - 1
            eye_color = (220, 20, 20) if self.state == "CHARGE" else (20, 30, 20)
            pygame.draw.circle(surface, eye_color, (draw_rect.centerx - 3, eye_y), 1)
            pygame.draw.circle(surface, eye_color, (draw_rect.centerx + 3, eye_y), 1)

        # --- ONLY DRAW HP BAR IF SLIME HAS DETECTED PLAYER (NOT IDLE) ---
        if self.state != "IDLE":
            bar_w = 20
            bar_h = 2
            bar_x = draw_rect.centerx - bar_w // 2
            bar_y = draw_rect.bottom + 2

            hp_ratio = max(0, self.hp / self.max_hp)
            pygame.draw.rect(surface, (15, 12, 20), (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), border_radius=1)
            pygame.draw.rect(surface, (40, 25, 30), (bar_x, bar_y, bar_w, bar_h))
            fill_color = (50, 220, 100) if hp_ratio > 0.4 else (230, 60, 60)
            pygame.draw.rect(surface, fill_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    def draw_overhead_ui(self, screen, camera_offset=(0, 0), zoom=1.0, fog=None, player_rect=None):
        """Renders crisp text on screen ONLY if slime is not IDLE and visible in lit space."""
        # 1. HIDE IF DEAD OR IF SLIME HASN'T DETECTED PLAYER YET (STATE IS IDLE)
        if self.is_dead or self.state == "IDLE":
            return

        cam_x, cam_y = camera_offset
        screen_x = int((self.rect.centerx - cam_x) * zoom)
        screen_y_top = int((self.rect.top - cam_y) * zoom)
        screen_y_bottom = int((self.rect.bottom - cam_y) * zoom)

        # 2. SCREEN BOUNDS CHECK
        if screen_x < 0 or screen_x > screen.get_width() or screen_y_top < 0 or screen_y_bottom > screen.get_height():
            return

        # 3. STRICT FOG/LIGHTING CHECK
        if fog:
            if hasattr(fog, 'fog_surface') and fog.fog_surface:
                try:
                    fog_alpha = fog.fog_surface.get_at((screen_x, screen_y_top))[3]
                    if fog_alpha > 150:  
                        return
                except (IndexError, TypeError):
                    pass
            elif hasattr(fog, 'surface') and fog.surface:
                try:
                    fog_alpha = fog.surface.get_at((screen_x, screen_y_top))[3]
                    if fog_alpha > 150:  
                        return
                except (IndexError, TypeError):
                    pass
            
            if hasattr(fog, 'is_lit') and not fog.is_lit((self.rect.centerx, self.rect.centery)):
                return
            elif hasattr(fog, 'is_visible') and not fog.is_visible((self.rect.centerx, self.rect.centery)):
                return

        # 4. RENDER TEXT (Name Tag & HP Digits)
        name_txt = self.ui_name_font.render(self.name, True, (240, 245, 240))
        name_x = screen_x - (name_txt.get_width() // 2)
        name_y = screen_y_top - int(14 * zoom)
        screen.blit(name_txt, (name_x, name_y))

        hp_str = f"{int(self.hp)}/{self.max_hp}"
        hp_txt = self.ui_hp_font.render(hp_str, True, (220, 225, 230))
        hp_x = screen_x - (hp_txt.get_width() // 2)
        hp_y = screen_y_bottom + int(8 * zoom)
        screen.blit(hp_txt, (hp_x, hp_y))