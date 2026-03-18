'''
Board class representing the checkers board and piece management.
'''
from piece import Piece
class Board:
    def __init__(self):
        """Initialize an 8x8 checkers board with starting positions."""
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.setup_board()
    def setup_board(self):
        """Set up the initial board configuration."""
        # Place red pieces (top three rows)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('red', row, col)
        # Place white pieces (bottom three rows)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('white', row, col)
    def get_piece(self, row, col):
        """
        Get piece at specified position.
        Args:
            row (int): Row index
            col (int): Column index
        Returns:
            Piece or None: Piece at position or None if empty
        """
        if self.is_valid_position(row, col):
            return self.board[row][col]
        return None
    def move_piece(self, piece, new_row, new_col):
        """
        Move a piece to a new position.
        Args:
            piece (Piece): Piece to move
            new_row (int): New row position
            new_col (int): New column position
        Returns:
            list: List of captured pieces positions
        """
        old_row, old_col = piece.row, piece.col
        # Move piece
        self.board[old_row][old_col] = None
        self.board[new_row][new_col] = piece
        piece.row = new_row
        piece.col = new_col
        # Check for captures
        captured = []
        row_diff = new_row - old_row
        col_diff = new_col - old_col
        # If move is a capture (jump of 2 squares)
        if abs(row_diff) == 2:
            captured_row = old_row + row_diff // 2
            captured_col = old_col + col_diff // 2
            captured_piece = self.get_piece(captured_row, captured_col)
            if captured_piece:
                self.remove_piece(captured_row, captured_col)
                captured.append((captured_row, captured_col))
        # Check for king promotion
        if not piece.king:
            if (piece.color == 'red' and new_row == 7) or \
               (piece.color == 'white' and new_row == 0):
                piece.make_king()
        return captured
    def remove_piece(self, row, col):
        """
        Remove piece from board.
        Args:
            row (int): Row index
            col (int): Column index
        """
        if self.is_valid_position(row, col):
            self.board[row][col] = None
    def is_valid_position(self, row, col):
        """
        Check if position is within board bounds.
        Args:
            row (int): Row index
            col (int): Column index
        Returns:
            bool: True if position is valid
        """
        return 0 <= row < 8 and 0 <= col < 8
    def get_all_pieces(self, color=None):
        """
        Get all pieces on the board, optionally filtered by color.
        Args:
            color (str, optional): 'red' or 'white' to filter by color
        Returns:
            list: List of Piece objects
        """
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    if color is None or piece.color == color:
                        pieces.append(piece)
        return pieces
    def __str__(self):
        """String representation of the board."""
        result = "  0 1 2 3 4 5 6 7\n"
        for row in range(8):
            result += f"{row} "
            for col in range(8):
                piece = self.board[row][col]
                if piece is None:
                    result += ". "
                else:
                    if piece.color == 'red':
                        result += 'r' if not piece.king else 'R'
                    else:
                        result += 'w' if not piece.king else 'W'
                    result += " "
            result += "\n"
        return result