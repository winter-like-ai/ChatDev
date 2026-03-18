'''
Main entry point for the Checkers game.
Initializes and runs the game with GUI.
'''
import pygame
from game import Game
from gui import GUI
def main():
    """Main function to run the Checkers game."""
    # Initialize game logic
    game = Game()
    # Initialize GUI
    gui = GUI(game)
    # Run the game
    gui.run()
if __name__ == "__main__":
    main()