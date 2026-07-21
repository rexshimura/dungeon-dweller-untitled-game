import pygame

class PlayerController:
    def __init__(self, start_x, start_y):
        self.pos_x = float(start_x)
        self.pos_y = float(start_y)

    def set_position(self, x, y):
        self.pos_x = float(x)
        self.pos_y = float(y)

    def move_player_exact(self, rect, dx, dy, walls):
        self.pos_x += dx
        rect.x = round(self.pos_x)
        for wall in walls:
            if rect.colliderect(wall):
                if dx > 0: rect.right = wall.left
                if dx < 0: rect.left = wall.right
                self.pos_x = float(rect.x)

        self.pos_y += dy
        rect.y = round(self.pos_y)
        for wall in walls:
            if rect.colliderect(wall):
                if dy > 0: rect.bottom = wall.top
                if dy < 0: rect.top = wall.bottom
                self.pos_y = float(rect.y)