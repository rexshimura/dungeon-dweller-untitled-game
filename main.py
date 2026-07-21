import pygame
import sys

from globals.config import SCREEN_WIDTH, SCREEN_HEIGHT
from game_engine import GameEngine


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Dungeon Crawler")

    engine = GameEngine(screen)

    running = True
    while running:
        running = engine.handle_events()
        engine.update()
        engine.draw()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()