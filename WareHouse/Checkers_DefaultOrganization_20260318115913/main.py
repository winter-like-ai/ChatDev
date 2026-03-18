'''
Main entry point for the Checkers game.
Initializes Pygame and starts the game.
'''
import pygame
from game import Game
def main():
    # Initialize pygame
    pygame.init()
    # Create and run the game
    game = Game()
    game.run()
if __name__ == "__main__":
    main()