'''
main.py
Entry point for the Checkers game application.
Initializes and runs the game with GUI.
'''
import pygame
import sys
from checkersgame import CheckersGame
from gamegui import GameGUI
def main():
    """Main function to initialize and run the Checkers game."""
    pygame.init()
    # Initialize game components
    game = CheckersGame()
    gui = GameGUI(game)
    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    gui.handle_click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Restart game when 'R' key is pressed
                    game = CheckersGame()
                    gui = GameGUI(game)
        gui.draw()
        pygame.display.flip()
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()