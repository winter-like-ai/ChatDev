'''
Main entry point for the Checkers game application.
Initializes Pygame and runs the main game loop.
'''
import pygame
from game import Game
from constants import WIDTH, HEIGHT, FPS
def main():
    '''Initialize and run the Checkers game.'''
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Checkers Game")
    clock = pygame.time.Clock()
    game = Game(screen)
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                game.handle_click(pos)
        game.update()
        pygame.display.flip()
    pygame.quit()
if __name__ == "__main__":
    main()