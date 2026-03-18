'''
Main entry point for the Checkers game.
Initializes Pygame and runs the game loop.
Handles both mouse and keyboard input for move notation.
'''
import pygame
from game import Game
from constants import WIDTH, HEIGHT, FPS, SQUARE_SIZE
def main():
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
                row, col = get_row_col_from_mouse(pos)
                game.select(row, col)
            elif event.type == pygame.KEYDOWN:
                game.handle_event(event)  # Handle keyboard input for move notation
        game.update()
        pygame.display.flip()
    pygame.quit()
def get_row_col_from_mouse(pos):
    '''Convert mouse position to board coordinates.'''
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col
if __name__ == "__main__":
    main()