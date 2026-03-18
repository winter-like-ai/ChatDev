'''
main.py - Entry point for the Checkers game application
Launches the Pygame GUI and starts the game
'''
import pygame
from game import CheckersGame
from gui import GameGUI
def main():
    """Main function to initialize and run the Checkers game"""
    pygame.init()
    # Create game instance
    game = CheckersGame()
    # Create GUI instance
    gui = GameGUI(game)
    # Run the game
    gui.run()
if __name__ == "__main__":
    main()