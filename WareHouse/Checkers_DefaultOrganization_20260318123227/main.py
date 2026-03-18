'''
Main entry point for the Checkers game application.
Initializes and runs the game with GUI.
'''
import pygame
from game import CheckersGame
from gui import GameGUI
def main():
    """Main function to initialize and run the Checkers game."""
    # Initialize Pygame
    pygame.init()
    # Create game instance
    game = CheckersGame()
    # Create GUI instance
    gui = GameGUI(game)
    # Run the game
    gui.run()
if __name__ == "__main__":
    main()