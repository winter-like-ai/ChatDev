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
    # Initialize Pygame
    pygame.init()
    # Create game instance
    game = CheckersGame()
    # Create GUI instance
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
        # Draw the game state
        gui.draw()
        # Update the display
        pygame.display.flip()
        # Cap the frame rate
        pygame.time.Clock().tick(60)
    # Quit Pygame
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()