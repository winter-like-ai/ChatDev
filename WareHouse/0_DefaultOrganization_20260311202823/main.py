'''
Main entry point for the Checkers game.
Handles Pygame initialization, main game loop, and event processing.
'''
import pygame
from game import Game
from constants import WIDTH, HEIGHT, SQUARE_SIZE, FPS, WHITE, BLACK
def get_row_col_from_mouse(pos):
    """Convert mouse position to board row and column."""
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col
def main():
    """Main game loop."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Checkers (Draughts)")
    clock = pygame.time.Clock()
    game = Game(screen)
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                game.select(row, col)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_ESCAPE:
                    running = False
        game.update()
        pygame.display.flip()
    pygame.quit()
if __name__ == "__main__":
    main()