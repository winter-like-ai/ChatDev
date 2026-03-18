'''
Core game logic for Checkers.
Manages board state, turns, moves, and game rules.
'''
from board import Board
from piece import Piece
class Game:
    """Main game controller for Checkers."""
    def __init__(self):
        """Initialize a new Checkers game."""
        self.board = Board()
        self.turn = 'red'  # Red starts first
        self.selected_piece = None
        self.valid_moves = {}
        self.winner = None
        self.must_capture = False
        self.capture_chain = False
        self.capturing_piece = None
    def reset(self):
        """Reset the game to initial state."""
        self.board = Board()
        self.turn = 'red'
        self.selected_piece = None
        self.valid_moves = {}
        self.winner = None
        self.must_capture = False
        self.capture_chain = False
        self.capturing_piece = None
    def select(self, row, col):
        """Select a piece or make a move."""
        if self.winner is not None:
            return False
        # If we're in a capture chain, only allow moves for the capturing piece
        if self.capture_chain and self.capturing_piece:
            if (row, col) != (self.capturing_piece.row, self.capturing_piece.col):
                # Try to move the capturing piece
                return self._try_move(row, col)
            else:
                # Reselect the capturing piece
                self.selected_piece = self.capturing_piece
                self.valid_moves = self.board.get_valid_moves(self.selected_piece)
                return True
        # If a piece is already selected
        if self.selected_piece:
            result = self._try_move(row, col)
            if result:
                # Move was successful
                if not self.capture_chain:
                    self.change_turn()
                return True
            else:
                # Try to select a different piece
                piece = self.board.get_piece(row, col)
                if piece and piece.color == self.turn:
                    self.selected_piece = piece
                    self.valid_moves = self.board.get_valid_moves(piece)
                    return True
                else:
                    self.selected_piece = None
                    self.valid_moves = {}
                    return False
        else:
            # No piece selected yet
            piece = self.board.get_piece(row, col)
            if piece and piece.color == self.turn:
                self.selected_piece = piece
                self.valid_moves = self.board.get_valid_moves(piece)
                return True
        return False
    def _try_move(self, row, col):
        """Attempt to move the selected piece to the given position."""
        if self.selected_piece and (row, col) in self.valid_moves:
            move = self.valid_moves[(row, col)]
            # Make the move
            captured = self.board.move(self.selected_piece, row, col, move['captures'])
            # Check for king promotion
            if not self.selected_piece.king:
                if self.selected_piece.color == 'red' and row == 7:
                    self.selected_piece.make_king()
                elif self.selected_piece.color == 'white' and row == 0:
                    self.selected_piece.make_king()
            # Check for additional captures
            if captured:
                self.capturing_piece = self.selected_piece
                self.capture_chain = self.board.get_captures(self.selected_piece)
                if self.capture_chain:
                    # Still in capture chain, don't change turn
                    self.selected_piece = self.capturing_piece
                    self.valid_moves = self.capture_chain
                    return True
                else:
                    # Capture chain ended
                    self.capture_chain = False
                    self.capturing_piece = None
                    self.selected_piece = None
                    self.valid_moves = {}
                    # Check for win
                    if self.check_win():
                        return True
                    return True
            else:
                # No capture made
                self.capture_chain = False
                self.capturing_piece = None
                self.selected_piece = None
                self.valid_moves = {}
                # Check for win
                if self.check_win():
                    return True
                return True
        return False
    def change_turn(self):
        """Switch to the other player's turn."""
        self.turn = 'white' if self.turn == 'red' else 'red'
        self.selected_piece = None
        self.valid_moves = {}
        # Check if the current player has any moves
        if not self.board.has_valid_moves(self.turn):
            self.winner = 'white' if self.turn == 'red' else 'red'
    def check_win(self):
        """Check if the game has been won."""
        red_pieces = self.board.get_pieces_by_color('red')
        white_pieces = self.board.get_pieces_by_color('white')
        if len(red_pieces) == 0:
            self.winner = 'white'
            return True
        elif len(white_pieces) == 0:
            self.winner = 'red'
            return True
        # Check if current player has any valid moves
        if not self.board.has_valid_moves(self.turn):
            self.winner = 'white' if self.turn == 'red' else 'red'
            return True
        return False
    def get_board(self):
        """Get the current board state."""
        return self.board
    def get_turn(self):
        """Get the current player's turn."""
        return self.turn
    def get_selected_piece(self):
        """Get the currently selected piece."""
        return self.selected_piece
    def get_valid_moves(self):
        """Get valid moves for the selected piece."""
        return self.valid_moves