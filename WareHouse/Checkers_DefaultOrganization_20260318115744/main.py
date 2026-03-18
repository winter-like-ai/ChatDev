'''
Main entry point for the Checkers game.
Initializes and runs the game with GUI.
'''
import pygame
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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.winner is not None:
                    game.reset()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    pos = pygame.mouse.get_pos()
                    gui.handle_click(pos)
        # Draw everything
        gui.draw()
        # Check for game over
        if game.winner is not None:
            gui.display_winner()
        pygame.display.flip()
        pygame.time.Clock().tick(60)
    pygame.quit()
if __name__ == "__main__":
    main()