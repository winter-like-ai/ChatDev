'''
main.py
Entry point for the Checkers game application.
Initializes Pygame and runs the main game loop.
'''
import pygame
from game import Game
from constants import WIDTH, HEIGHT, FPS, SQUARE_SIZE, ROWS, COLS
from gui import draw_board, draw_pieces, draw_game_info, draw_selection, draw_valid_move
def main():
    """Main function to run the Checkers game."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Checkers Game")
    clock = pygame.time.Clock()
    game = Game()
    running = True
    selected_piece = None
    valid_moves = []
    chain_capture_path = []
    while running:
        clock.tick(FPS)
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    pos = pygame.mouse.get_pos()
                    row, col = get_board_position(pos)
                    if chain_capture_path:
                        # If in a chain capture, only allow the next move in the sequence
                        if (row, col) == chain_capture_path[0]:
                            # Execute the next capture in the chain
                            from_row, from_col = selected_piece
                            game.make_move(from_row, from_col, row, col)
                            chain_capture_path.pop(0)
                            if chain_capture_path:
                                # More captures in the chain
                                selected_piece = (row, col)
                                valid_moves = [chain_capture_path[0]]
                            else:
                                # Chain capture complete
                                selected_piece = None
                                valid_moves = []
                                game.switch_turn()
                        else:
                            # Invalid move during chain capture
                            continue
                    else:
                        # Normal move selection
                        if selected_piece is None:
                            # Select a piece
                            piece = game.board.get_piece(row, col)
                            if piece and piece.color == game.current_player:
                                selected_piece = (row, col)
                                valid_moves = game.get_valid_moves(row, col)
                                # Check for chain captures
                                if valid_moves and len(valid_moves[0]) > 2:
                                    # First move in a chain capture
                                    chain_capture_path = list(valid_moves[0][1:])
                                    valid_moves = [(valid_moves[0][0],)]
                        else:
                            # Try to move the selected piece
                            from_row, from_col = selected_piece
                            move_made = False
                            for move in valid_moves:
                                if (row, col) in move:
                                    # Execute the move
                                    game.make_move(from_row, from_col, row, col)
                                    move_made = True
                                    # Check for chain captures
                                    if len(move) > 1 and (row, col) != move[-1]:
                                        # This is part of a chain capture
                                        chain_capture_path = list(move[1:])
                                        selected_piece = (row, col)
                                        valid_moves = [(chain_capture_path[0],)]
                                    else:
                                        # Move complete
                                        selected_piece = None
                                        valid_moves = []
                                        chain_capture_path = []
                                        game.switch_turn()
                                    break
                            if not move_made:
                                # Select a different piece or deselect
                                piece = game.board.get_piece(row, col)
                                if piece and piece.color == game.current_player:
                                    selected_piece = (row, col)
                                    valid_moves = game.get_valid_moves(row, col)
                                    chain_capture_path = []
                                    if valid_moves and len(valid_moves[0]) > 2:
                                        chain_capture_path = list(valid_moves[0][1:])
                                        valid_moves = [(valid_moves[0][0],)]
                                else:
                                    selected_piece = None
                                    valid_moves = []
                                    chain_capture_path = []
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset game
                    game = Game()
                    selected_piece = None
                    valid_moves = []
                    chain_capture_path = []
        # Draw everything
        screen.fill((50, 50, 50))
        draw_board(screen)
        draw_pieces(screen, game.board)
        # Highlight selected piece and valid moves
        if selected_piece:
            row, col = selected_piece
            draw_selection(screen, row, col)
            for move_sequence in valid_moves:
                for move_pos in move_sequence:
                    if isinstance(move_pos, tuple):
                        draw_valid_move(screen, move_pos[0], move_pos[1])
        draw_game_info(screen, game.current_player, game.winner)
        pygame.display.flip()
    pygame.quit()
def get_board_position(pos):
    """Convert screen coordinates to board row and column."""
    x, y = pos
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    # Ensure coordinates are within board bounds
    row = max(0, min(row, ROWS - 1))
    col = max(0, min(col, COLS - 1))
    return row, col
if __name__ == "__main__":
    main()