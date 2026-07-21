import pygame

class PlayerController:
    def __init__(self, start_x, start_y):
        self.x = float(start_x)
        self.y = float(start_y)
        self.knockback_vel = pygame.Vector2(0, 0)

    def apply_knockback(self, force_vector):
        """Receives the hit force from SlimeCombatHandler and adds it to velocity."""
        self.knockback_vel += force_vector

    def move_player_exact(self, player_rect, dx, dy, obstacles):
        # 1. Combine player input delta with active knockback velocity
        total_dx = dx
        total_dy = dy

        if self.knockback_vel.length() > 0.05:
            total_dx += self.knockback_vel.x
            total_dy += self.knockback_vel.y
            # Smooth friction decay so knockback slows down naturally
            self.knockback_vel *= 0.75  

        # Sync internal floats with rect position before moving
        self.x = float(player_rect.x)
        self.y = float(player_rect.y)

        # 2. X-Axis Movement & Collision
        if total_dx != 0:
            self.x += total_dx
            player_rect.x = int(round(self.x))
            for obstacle in obstacles:
                if player_rect.colliderect(obstacle):
                    if total_dx > 0:
                        player_rect.right = obstacle.left
                        self.knockback_vel.x = 0  # Cancel horizontal knockback on wall hit
                    elif total_dx < 0:
                        player_rect.left = obstacle.right
                        self.knockback_vel.x = 0
                    self.x = float(player_rect.x)

        # 3. Y-Axis Movement & Collision
        if total_dy != 0:
            self.y += total_dy
            player_rect.y = int(round(self.y))
            for obstacle in obstacles:
                if player_rect.colliderect(obstacle):
                    if total_dy > 0:
                        player_rect.bottom = obstacle.top
                        self.knockback_vel.y = 0  # Cancel vertical knockback on wall hit
                    elif total_dy < 0:
                        player_rect.top = obstacle.bottom
                        self.knockback_vel.y = 0
                    self.y = float(player_rect.y)

        # Clear negligible micro-velocities to save performance
        if self.knockback_vel.length() < 0.05:
            self.knockback_vel.update(0, 0)