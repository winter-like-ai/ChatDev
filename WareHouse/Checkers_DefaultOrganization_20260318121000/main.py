'''
Main entry point for the Checkers game.
Initializes the game and runs the main game loop.
'''
import pygame
from game import Game
from gui import GUI
from constants import WIDTH, HEIGHT, FPS
def main():
    # Initialize Pygame
    pygame.init()
    # Create game and GUI instances
    game = Game()
    gui = GUI()
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    selected_piece = None
    valid_moves = []
    while running:
        clock.tick(FPS)
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = gui.get_board_position(pos)
                if selected_piece:
                    # Try to make a move
                    if (row, col) in valid_moves:
                        game.make_move(selected_piece, (row, col))
                        selected_piece = None
                        valid_moves = []
                        # Check for winner
                        winner = game.check_winner()
                        if winner:
                            print(f"Game Over! {winner} wins!")
                            running = False
                    else:
                        # Select a different piece
                        piece = game.board[row][col]
                        if piece and piece.color == game.turn:
                            selected_piece = (row, col)
                            valid_moves = game.get_valid_moves(piece, (row, col))
                        else:
                            selected_piece = None
                            valid_moves = []
                else:
                    # Select a piece
                    piece = game.board[row][col]
                    if piece and piece.color == game.turn:
                        selected_piece = (row, col)
                        valid_moves = game.get_valid_moves(piece, (row, col))
        # Draw everything
        gui.draw_board(game.board)
        if selected_piece:
            gui.highlight_selected(selected_piece)
            gui.highlight_moves(valid_moves)
        gui.draw_pieces(game.board)
        # Update display
        pygame.display.flip()
    pygame.quit()
if __name__ == "__main__":
    main()