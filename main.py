
import pygame
import sys
from screens.menu import MenuScreen
from screens.game import GameScreen
from utils.constants import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, TITLE


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # Screen manager
    current_screen = "menu"
    menu = MenuScreen(screen)
    game = None

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if current_screen == "menu":
            result = menu.update(events)
            menu.draw()
            if result:
                action = result.get("action")
                if action == "start_game":
                    game = GameScreen(screen, result)
                    current_screen = "game"
                elif action == "load_game":
                    game = GameScreen(screen, result)
                    current_screen = "game"
                
                # --- NEW: Catch the quit action from the exit button ---
                elif action == "quit":
                    pygame.quit()
                    sys.exit()

        elif current_screen == "game":
            result = game.update(events)
            game.draw()
            if result:
                action = result.get("action")
                if action == "menu":
                    menu = MenuScreen(screen)
                    current_screen = "menu"
                    game = None

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()