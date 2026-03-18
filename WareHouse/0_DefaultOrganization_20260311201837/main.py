'''
main.py
Entry point for the Checkers game application.
Initializes and runs the game with GUI.
'''
import pygame
import sys
from game import Game
from gui import GUI
def main():
    """Main function to initialize and run the Checkers game."""
    pygame.init()
    # Initialize game and GUI
    game = Game()
    gui = GUI(game)
    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    pos = pygame.mouse.get_pos()
                    gui.handle_click(pos)
        # Draw the game state
        gui.draw()
        # Check for game over
        if game.game_over:
            gui.display_game_over()
        pygame.display.flip()
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()