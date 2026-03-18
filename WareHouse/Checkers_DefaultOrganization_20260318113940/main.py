'''
main.py
Entry point for the Checkers game application.
Initializes and runs the game with GUI.
'''
import pygame
from game import Game
from gui import GUI
def main():
    """Main function to initialize and run the Checkers game."""
    # Initialize Pygame
    pygame.init()
    # Create game instance
    game = Game()
    # Create GUI instance
    gui = GUI(game)
    # Run the game
    gui.run()
if __name__ == "__main__":
    main()