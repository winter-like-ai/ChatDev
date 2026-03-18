'''
main.py
Entry point for the Checkers game application.
Initializes Pygame and starts the game.
'''
import pygame
from game import Game
def main():
    """Main function to initialize and run the game."""
    pygame.init()
    game = Game()
    game.run()
    pygame.quit()
if __name__ == "__main__":
    main()