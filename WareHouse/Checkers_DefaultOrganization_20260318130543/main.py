'''
Main entry point for the Checkers game.
Initializes the game and runs the main loop.
'''
import pygame
from game import CheckersGame
from gui import GameGUI
def main():
    """Main game loop."""
    # Initialize Pygame
    pygame.init()
    # Create game instance
    game = CheckersGame()
    # Create GUI instance
    gui = GameGUI(game)
    # Main game loop
    running = True
    while running:
        gui.clock.tick(60)  # Limit to 60 FPS
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    gui.handle_click(event.pos)
        # Draw everything
        gui.draw()
        # Display game over screen if game ended
        if game.is_game_over():
            gui.display_game_over()
        # Update display
        pygame.display.flip()
    # Quit Pygame
    pygame.quit()
if __name__ == "__main__":
    main()