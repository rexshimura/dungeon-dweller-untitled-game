import pygame
import math
import random

COLOR_SWORD = (220, 225, 240)
COLOR_GUARD = (180, 185, 200)
COLOR_HILT = (120, 75, 30)
COLOR_CHARGE_EMPTY = (30, 40, 60)
COLOR_CHARGE_FILL = (40, 180, 255)
COLOR_CHARGE_READY = (255, 215, 0)
COLOR_PARTICLE = (100, 220, 255)
COLOR_SWING_PARTICLE = (240, 245, 255)
COLOR_SLICE_PARTICLE = (255, 255, 255)
COLOR_PARRY_SHIELD = (180, 220, 255)

# Micro Shield Icon Color Palette
COLOR_SHIELD_BG = (15, 22, 35)
COLOR_SHIELD_BORDER = (220, 235, 255)
COLOR_SHIELD_CORE = (40, 150, 240)
COLOR_SHIELD_EMBLEM = (255, 255, 255)

class Particle:
    def __init__(self, x, y, mode="GATHER", target_pos=None, angle=0):
        self.pos = pygame.Vector2(x, y)
        self.mode = mode
        self.life = random.randint(8, 16)
        self.max_life = self.life
        self.size = random.randint(2, 4)

        if mode == "GATHER" and target_pos:
            spawn_offset = pygame.Vector2(random.uniform(-30, 30), random.uniform(-30, 30))
            self.pos = target_pos + spawn_offset
            self.vel = (target_pos - self.pos) * 0.12
            self.color = COLOR_PARTICLE[:3]

        elif mode == "SWING":
            # Subtle, low-opacity swing trail
            speed = random.uniform(0.8, 2.0)
            spread = angle + random.uniform(-0.1, 0.1)
            self.vel = pygame.Vector2(math.cos(spread), math.sin(spread)) * speed
            self.color = COLOR_SWING_PARTICLE[:3]
            self.life = random.randint(5, 10)
            self.size = random.randint(1, 2)

        elif mode == "SLICE":
            # Fast, low-opacity sharp slice streaks
            speed = random.uniform(3.5, 6.0)
            spread = angle + random.uniform(-0.05, 0.05)
            self.vel = pygame.Vector2(math.cos(spread), math.sin(spread)) * speed
            self.color = COLOR_SLICE_PARTICLE[:3]
            self.life = random.randint(4, 7)
            self.size = 1

        elif mode == "PARRY":
            speed = random.uniform(1.5, 3.5)
            spread = angle + random.uniform(-0.4, 0.4)
            self.vel = pygame.Vector2(math.cos(spread), math.sin(spread)) * speed
            self.color = COLOR_PARRY_SHIELD[:3]
            self.life = random.randint(6, 10)
            self.size = random.randint(1, 2)

        else:  # THRUST burst particles
            speed = random.uniform(2.5, 6.5)
            spread = angle + random.uniform(-0.35, 0.35)
            self.vel = pygame.Vector2(math.cos(spread), math.sin(spread)) * speed
            selected_color = COLOR_PARTICLE if random.random() < 0.6 else COLOR_CHARGE_READY
            self.color = selected_color[:3]

    def update(self):
        self.pos += self.vel
        self.life -= 1

    def draw(self, surface):
        if self.life > 0:
            ratio = max(0.0, min(1.0, self.life / self.max_life))
            
            # Lowered alpha max for SWING (80) and SLICE (60) for subtle translucency
            if self.mode == "SWING":
                alpha = int(ratio * 80)
            elif self.mode == "SLICE":
                alpha = int(ratio * 60)
            else:
                alpha = int(ratio * 255)

            color = (int(self.color[0]), int(self.color[1]), int(self.color[2]), alpha)
            
            if self.mode == "SLICE":
                tail_pos = self.pos - (self.vel * 1.5)
                pygame.draw.line(surface, color, (self.pos.x, self.pos.y), (tail_pos.x, tail_pos.y), 1)
            else:
                p_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, color, (self.size, self.size), self.size)
                surface.blit(p_surf, (self.pos.x - self.size, self.pos.y - self.size))

class Sword:
    def __init__(self):
        self.length = 22
        self.width = 4
        self.guard_width = 10
        self.right_hand_offset = 6
        
        # Hold Mouse Threshold Configuration
        self.is_holding = False
        self.hold_timer = 0
        self.charge_threshold = 12
        
        # Charge State
        self.is_charging = False
        self.charge_timer = 0
        self.max_charge = 30
        self.bar_offset_x = 8.0
        
        # Arc swing configuration
        self.is_swinging = False
        self.swing_progress = 0.0
        self.swing_speed = 0.12
        self.arc_angle = 170
        
        # Thrust Dash configuration
        self.is_dashing = False
        self.dash_dir = pygame.Vector2(0, 0)
        self.dash_speed = 0
        self.dash_timer = 0

        # Parry Configuration
        self.is_parrying = False
        self.is_holding_parry = False
        self.parry_cooldown = 0
        self.max_parry_cooldown = 20
        self.parry_progress = 0.0
        self.shield_float_timer = 0.0
        
        self.shield_offset_x = -12.0

        self.particles = []

    def start_press(self):
        if not self.is_swinging and not self.is_dashing and not self.is_parrying:
            self.is_holding = True
            self.hold_timer = 0
            self.is_charging = False
            self.charge_timer = 0

    def trigger_parry(self, player_pos, mouse_world_pos):
        if not self.is_swinging and not self.is_dashing and self.parry_cooldown <= 0:
            self.is_parrying = True
            self.is_holding_parry = True
            self.parry_cooldown = self.max_parry_cooldown

            self.is_holding = False
            self.is_charging = False

            direction = mouse_world_pos - player_pos
            facing_angle = math.atan2(direction.y, direction.x) if direction.length() > 0 else 0
            
            for _ in range(4):
                self.particles.append(Particle(player_pos.x, player_pos.y, mode="PARRY", angle=facing_angle))

    def release_parry(self):
        self.is_holding_parry = False
        self.is_parrying = False

    def release_attack(self, player_pos, mouse_world_pos, player_stats):
        if not self.is_holding or self.is_parrying:
            return

        direction = mouse_world_pos - player_pos
        if direction.length() > 0:
            direction = direction.normalize()
        else:
            direction = pygame.Vector2(1, 0)

        if self.is_charging and self.charge_timer >= 10 and player_stats.can_use_mp(1):
            player_stats.consume_mp(1)
            self.is_dashing = True
            self.dash_dir = direction

            charge_ratio = min(1.0, self.charge_timer / self.max_charge)
            self.dash_speed = 4.0 + (charge_ratio * 4.5)
            self.dash_timer = int(5 + (charge_ratio * 7))

            facing_angle = math.atan2(direction.y, direction.x)
            particle_count = int(10 + (charge_ratio * 15))
            for _ in range(particle_count):
                self.particles.append(Particle(player_pos.x, player_pos.y, mode="THRUST", angle=facing_angle))
        else:
            self.is_swinging = True
            self.swing_progress = 0.0

        self.is_holding = False
        self.is_charging = False
        self.hold_timer = 0
        self.charge_timer = 0

    def _draw_tiny_shield_icon(self, surface, center_pos, alpha):
        w, h = 10, 12
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        outer_points = [(1, 0), (8, 0), (9, 3), (8, 7), (5, 11), (1, 7), (0, 3)]
        inner_points = [(2, 1), (7, 1), (8, 3), (7, 6), (5, 9), (2, 6), (1, 3)]

        pygame.draw.polygon(surf, (*COLOR_SHIELD_BG, alpha), outer_points)
        pygame.draw.polygon(surf, (*COLOR_SHIELD_BORDER, alpha), outer_points, width=1)
        pygame.draw.polygon(surf, (*COLOR_SHIELD_CORE, int(alpha * 0.95)), inner_points)

        pygame.draw.line(surf, (*COLOR_SHIELD_EMBLEM, alpha), (5, 2), (5, 8), 1)
        pygame.draw.line(surf, (*COLOR_SHIELD_EMBLEM, alpha), (3, 4), (7, 4), 1)

        surface.blit(surf, (center_pos.x - (w / 2), center_pos.y - (h / 2)))

    def update(self, player_rect, mouse_world_pos, move_player_func, walls):
        player_center = pygame.Vector2(player_rect.centerx, player_rect.centery)

        if self.parry_cooldown > 0:
            self.parry_cooldown -= 1

        keys_mouse = pygame.mouse.get_pressed()
        if not keys_mouse[2]:
            self.is_holding_parry = False
            self.is_parrying = False

        target_parry_progress = 1.0 if (self.is_parrying or self.is_holding_parry) else 0.0
        self.parry_progress += (target_parry_progress - self.parry_progress) * 0.35

        if self.parry_progress > 0.05:
            self.shield_float_timer += 0.12

        if self.is_holding and not self.is_parrying:
            self.hold_timer += 1
            if self.hold_timer >= self.charge_threshold:
                self.is_charging = True

        if self.is_charging:
            if self.charge_timer < self.max_charge:
                self.charge_timer += 1
            if random.random() < 0.6:
                self.particles.append(Particle(0, 0, mode="GATHER", target_pos=player_center))

        if self.is_swinging:
            dir_to_mouse = mouse_world_pos - player_center
            facing_angle = math.atan2(dir_to_mouse.y, dir_to_mouse.x)
            angle_offset = math.radians(-self.arc_angle / 2 + (self.arc_angle * self.swing_progress))
            current_sword_angle = facing_angle + angle_offset

            perp_angle = facing_angle + math.pi / 2
            hand_pos = player_center + pygame.Vector2(math.cos(perp_angle), math.sin(perp_angle)) * self.right_hand_offset
            
            tip_pos = hand_pos + pygame.Vector2(math.cos(current_sword_angle), math.sin(current_sword_angle)) * self.length
            
            self.particles.append(Particle(tip_pos.x, tip_pos.y, mode="SWING", angle=current_sword_angle))
            self.particles.append(Particle(tip_pos.x, tip_pos.y, mode="SLICE", angle=current_sword_angle + (math.pi / 2)))

            self.swing_progress += self.swing_speed
            if self.swing_progress >= 1.0:
                self.is_swinging = False
                self.swing_progress = 0.0

        if self.is_dashing:
            dx = self.dash_dir.x * self.dash_speed
            dy = self.dash_dir.y * self.dash_speed
            move_player_func(player_rect, dx, dy, walls)
            
            facing_angle = math.atan2(self.dash_dir.y, self.dash_dir.x)
            self.particles.append(Particle(player_center.x, player_center.y, mode="THRUST", angle=facing_angle + math.pi))

            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = False

        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

    def draw(self, surface, player_rect, mouse_world_pos):
        player_center = pygame.Vector2(player_rect.centerx, player_rect.centery)
        
        dir_to_mouse = mouse_world_pos - player_center
        facing_angle = math.atan2(dir_to_mouse.y, dir_to_mouse.x)

        for p in self.particles:
            p.draw(surface)

        # Direction Pointer
        pointer_start = player_center + pygame.Vector2(math.cos(facing_angle), math.sin(facing_angle)) * 8
        pointer_end = player_center + pygame.Vector2(math.cos(facing_angle), math.sin(facing_angle)) * 20
        pygame.draw.line(surface, (50, 230, 110, 160), pointer_start, pointer_end, 2)

        perp_angle = facing_angle + math.pi / 2
        default_hand_pos = player_center + pygame.Vector2(math.cos(perp_angle), math.sin(perp_angle)) * self.right_hand_offset

        if self.parry_progress > 0.01:
            block_angle = facing_angle - (math.pi / 2)
            
            forward_pos = player_center + pygame.Vector2(math.cos(facing_angle), math.sin(facing_angle)) * 6
            parry_hand_pos = forward_pos - pygame.Vector2(math.cos(block_angle), math.sin(block_angle)) * (self.length * 0.45)
            
            hand_pos = default_hand_pos.lerp(parry_hand_pos, self.parry_progress)
            
            angle_diff = (block_angle - facing_angle + math.pi) % (2 * math.pi) - math.pi
            current_sword_angle = facing_angle + (angle_diff * self.parry_progress)

            target_shield_x = -12.0 if dir_to_mouse.x >= 0 else 12.0
            self.shield_offset_x += (target_shield_x - self.shield_offset_x) * 0.25

            shield_bob = math.sin(self.shield_float_timer) * 1.5
            icon_center = pygame.Vector2(player_center.x + self.shield_offset_x, player_center.y - 12 + shield_bob)
            icon_alpha = int(255 * self.parry_progress)

            self._draw_tiny_shield_icon(surface, icon_center, icon_alpha)

        elif self.is_swinging:
            hand_pos = default_hand_pos
            angle_offset = math.radians(-self.arc_angle / 2 + (self.arc_angle * self.swing_progress))
            current_sword_angle = facing_angle + angle_offset
        else:
            hand_pos = default_hand_pos
            current_sword_angle = facing_angle

        # Charge Progress Bar
        if self.is_charging:
            target_offset_x = -12.0 if dir_to_mouse.x >= 0 else 12.0
            self.bar_offset_x += (target_offset_x - self.bar_offset_x) * 0.2

            bar_w = 4
            bar_h = 18
            bar_x = player_center.x + self.bar_offset_x - (bar_w // 2)
            bar_y = player_center.y - (bar_h // 2)

            charge_ratio = min(1.0, self.charge_timer / self.max_charge)
            fill_h = int(bar_h * charge_ratio)

            pygame.draw.rect(surface, COLOR_CHARGE_EMPTY, (bar_x, bar_y, bar_w, bar_h), border_radius=1)
            fill_color = COLOR_CHARGE_READY if charge_ratio >= 1.0 else COLOR_CHARGE_FILL
            if fill_h > 0:
                pygame.draw.rect(surface, fill_color, (bar_x, bar_y + (bar_h - fill_h), bar_w, fill_h), border_radius=1)
            pygame.draw.rect(surface, (180, 200, 220), (bar_x, bar_y, bar_w, bar_h), 1, border_radius=1)

        # Draw Greatsword
        blade_len = self.length + (6 if self.is_dashing else 0)
        guard_pos = hand_pos + pygame.Vector2(math.cos(current_sword_angle), math.sin(current_sword_angle)) * 4
        tip_pos = hand_pos + pygame.Vector2(math.cos(current_sword_angle), math.sin(current_sword_angle)) * blade_len

        sword_perp = current_sword_angle + math.pi / 2
        guard_p1 = guard_pos + pygame.Vector2(math.cos(sword_perp), math.sin(sword_perp)) * (self.guard_width / 2)
        guard_p2 = guard_pos - pygame.Vector2(math.cos(sword_perp), math.sin(sword_perp)) * (self.guard_width / 2)

        pygame.draw.line(surface, COLOR_HILT, hand_pos, guard_pos, 4)
        pygame.draw.line(surface, COLOR_GUARD, guard_p1, guard_p2, 3)
        pygame.draw.line(surface, COLOR_SWORD, guard_pos, tip_pos, self.width)