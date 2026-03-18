'''
Main entry point for the Checkers game.
Initializes and runs the Checkers game with GUI.
'''
import pygame
from game import Game
from checkers_gui import CheckersGUI
def main():
    """Main function to initialize and run the Checkers game."""
    # Initialize Pygame
    pygame.init()
    # Create game instance
    game = Game()
    # Create GUI instance
    gui = CheckersGUI(game)
    # Run the game
    gui.run()
if __name__ == "__main__":
    main()