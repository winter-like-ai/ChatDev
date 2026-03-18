'''
Main entry point for the Checkers game.
Initializes Pygame and starts the game loop.
'''
import pygame
from game import Game
from constants import WIDTH, HEIGHT, FPS
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Checkers (Draughts) Game")
    clock = pygame.time.Clock()
    game = Game(screen)
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    pos = pygame.mouse.get_pos()
                    game.handle_click(pos)
        game.update()
        game.draw()
        pygame.display.flip()
    pygame.quit()
if __name__ == "__main__":
    main()