'''
Core game logic for Checkers.
Manages board state, turns, moves, captures, and game rules.
'''
from board import Board
from piece import Piece
class Game:
    def __init__(self):
        """Initialize a new Checkers game."""
        self.board = Board()
        self.current_player = 'red'  # Red starts first
        self.selected_piece = None
        self.valid_moves = {}
        self.must_capture = False
        self.game_over = False
        self.winner = None
    def reset(self):
        """Reset the game to initial state."""
        self.__init__()
    def select_piece(self, row, col):
        """
        Select a piece at the given position.
        Args:
            row: Row index (0-7)
            col: Column index (0-7)
        Returns:
            bool: True if selection was successful
        """
        if self.game_over:
            return False
        piece = self.board.get_piece(row, col)
        # If clicking on a piece of current player
        if piece != 0 and piece.color == self.current_player:
            self.selected_piece = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
        return False
    def move_piece(self, row, col):
        """
        Move the selected piece to the given position.
        Args:
            row: Target row index
            col: Target column index
        Returns:
            bool: True if move was successful
        """
        if self.game_over or self.selected_piece is None:
            return False
        move = self.valid_moves.get((row, col))
        if move is None:
            return False
        # Check if this is a capture move
        is_capture = move.get('captured', [])
        # Perform the move
        self.board.move(self.selected_piece, row, col)
        # Remove captured pieces
        for captured_pos in is_capture:
            self.board.remove(*captured_pos)
        # Check for promotion to king
        if self.board.should_promote(self.selected_piece, row):
            self.board.promote_to_king(self.selected_piece)
        # Check for chain captures
        if is_capture:
            # Check if the same piece can capture again
            self.selected_piece = self.board.get_piece(row, col)
            self.valid_moves = self.board.get_valid_moves(self.selected_piece)
            # Filter only capture moves for chain captures
            chain_captures = {}
            for pos, move_info in self.valid_moves.items():
                if move_info.get('captured'):
                    chain_captures[pos] = move_info
            if chain_captures:
                self.valid_moves = chain_captures
                self.must_capture = True
                return True
        # Switch player if no chain capture
        self.switch_turn()
        return True
    def switch_turn(self):
        """Switch to the other player's turn."""
        self.selected_piece = None
        self.valid_moves = {}
        self.must_capture = False
        self.current_player = 'black' if self.current_player == 'red' else 'red'
        # Check if game is over
        if not self.board.has_valid_moves(self.current_player):
            self.game_over = True
            self.winner = 'black' if self.current_player == 'red' else 'red'
    def get_board(self):
        """Get the current board state."""
        return self.board
    def get_current_player(self):
        """Get the current player's color."""
        return self.current_player
    def is_game_over(self):
        """Check if the game is over."""
        return self.game_over
    def get_winner(self):
        """Get the winner of the game."""
        return self.winner