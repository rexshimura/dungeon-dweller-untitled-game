import pygame

class DoorTile:
    def __init__(self, rect, is_locked=False, key_id="gold_key"):
        self.rect = rect
        self.is_locked = is_locked
        self.key_id = key_id
        self.is_open = False

    def try_open(self, player_keys):
        """Attempts to open the door. Returns True if successfully opened."""
        if self.is_open:
            return True
            
        if not self.is_locked:
            self.is_open = True
            return True
        elif self.key_id in player_keys:
            self.is_open = True
            player_keys.remove(self.key_id)  # Consume the key upon use
            return True
            
        return False

    def draw(self, surface):
        if self.is_open:
            # Draw open door frame / empty doorway
            pygame.draw.rect(surface, (12, 10, 16), self.rect)
            pygame.draw.rect(surface, (60, 40, 20), self.rect, 1)
        else:
            # Draw closed door
            door_color = (180, 120, 40) if self.is_locked else (130, 80, 30)
            pygame.draw.rect(surface, door_color, self.rect, border_radius=2)
            pygame.draw.rect(surface, (50, 30, 10), self.rect, 1, border_radius=2)
            
            # Keyhole icon on locked doors
            if self.is_locked:
                pygame.draw.circle(surface, (255, 215, 0), self.rect.center, 3)