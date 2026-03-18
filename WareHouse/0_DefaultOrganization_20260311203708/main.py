'''
Main entry point for the Checkers game
'''
import pygame
import sys
from game import Game
from constants import *
def main():
    '''Main game loop'''
    pygame.init()
    win = pygame.display.set_mode(BOARD_SIZE)
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
                pos = pygame.mouse.get_pos()
                row, col = game.get_pos_from_mouse(pos)
                game.select(row, col)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_ESCAPE:
                    running = False
        game.update()
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()