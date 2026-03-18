'''
Main entry point for the Checkers game.
Initializes Pygame and runs the game loop.
'''
import pygame
from game import Game
from constants import *
def main():
    '''Main game loop'''
    pygame.init()
    win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Checkers Game")
    clock = pygame.time.Clock()
    game = Game(win)
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    pos = pygame.mouse.get_pos()
                    game.handle_mouse_click(pos)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                # Handle text input for move notation
                game.handle_text_input(event)
        game.update()
    pygame.quit()
if __name__ == "__main__":
    main()