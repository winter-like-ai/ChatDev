'''
Core game logic for Checkers.
Handles board state, move validation, and game rules.
'''
from piece import Piece
from constants import ROWS, COLS
class Game:
    def __init__(self):
        """Initialize the game with starting positions."""
        self.board = []
        self.turn = 'red'  # Red starts
        self.selected_piece = None
        self.create_board()
    def create_board(self):
        """Create the initial board setup."""
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        # Place red pieces (top rows)
        for row in range(3):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('red', row, col)
        # Place blue pieces (bottom rows)
        for row in range(5, ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('blue', row, col)
    def get_valid_moves(self, piece, pos):
        """
        Get all valid moves for a piece.
        Args:
            piece: The piece to check
            pos: (row, col) position of the piece
        Returns:
            List of valid (row, col) positions to move to
        """
        if not piece:
            return []
        row, col = pos
        moves = []
        captures = []
        # Determine move direction based on piece color and king status
        if piece.color == 'red' or piece.king:
            # Red moves down or kings can move both ways
            moves.extend(self._get_moves_in_direction(row, col, 1, piece))
            captures.extend(self._get_captures_in_direction(row, col, 1, piece))
        if piece.color == 'blue' or piece.king:
            # Blue moves up or kings can move both ways
            moves.extend(self._get_moves_in_direction(row, col, -1, piece))
            captures.extend(self._get_captures_in_direction(row, col, -1, piece))
        # If captures are available, only captures are valid moves
        if captures:
            return captures
        return moves
    def _get_moves_in_direction(self, row, col, direction, piece):
        """Get regular moves in a specific direction."""
        moves = []
        # Check diagonal moves
        new_row = row + direction
        for new_col in [col - 1, col + 1]:
            if 0 <= new_row < ROWS and 0 <= new_col < COLS:
                if self.board[new_row][new_col] is None:
                    moves.append((new_row, new_col))
        return moves
    def _get_captures_in_direction(self, row, col, direction, piece, captured=None):
        """Get capture moves in a specific direction."""
        if captured is None:
            captured = []
        captures = []
        # Check diagonal captures
        for col_offset in [-1, 1]:
            jump_row = row + direction
            jump_col = col + col_offset
            land_row = row + 2 * direction
            land_col = col + 2 * col_offset
            if (0 <= land_row < ROWS and 0 <= land_col < COLS and
                self.board[jump_row][jump_col] is not None and
                self.board[land_row][land_col] is None and
                self.board[jump_row][jump_col].color != piece.color and
                (jump_row, jump_col) not in captured):
                # Check for multiple jumps
                temp_captured = captured + [(jump_row, jump_col)]
                further_captures = self._get_captures_in_direction(
                    land_row, land_col, direction, piece, temp_captured
                )
                if further_captures:
                    captures.extend(further_captures)
                else:
                    captures.append((land_row, land_col))
        return captures
    def make_move(self, from_pos, to_pos):
        """
        Make a move on the board.
        Args:
            from_pos: (row, col) starting position
            to_pos: (row, col) ending position
        Returns:
            True if move was successful, False otherwise
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board[from_row][from_col]
        if not piece:
            return False
        # Check if move is valid
        valid_moves = self.get_valid_moves(piece, from_pos)
        if to_pos not in valid_moves:
            return False
        # Move the piece
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        piece.move(to_row, to_col)
        # Check for capture
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        if abs(row_diff) == 2:  # It's a capture
            captured_row = from_row + row_diff // 2
            captured_col = from_col + col_diff // 2
            self.board[captured_row][captured_col] = None
        # Check for king promotion
        if (piece.color == 'red' and to_row == ROWS - 1) or \
           (piece.color == 'blue' and to_row == 0):
            piece.make_king()
        # Switch turns
        self.turn = 'blue' if self.turn == 'red' else 'red'
        return True
    def check_winner(self):
        """
        Check if there's a winner.
        Returns:
            'red', 'blue', or None if no winner yet
        """
        red_pieces = 0
        blue_pieces = 0
        red_moves = 0
        blue_moves = 0
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece:
                    if piece.color == 'red':
                        red_pieces += 1
                        red_moves += len(self.get_valid_moves(piece, (row, col)))
                    else:
                        blue_pieces += 1
                        blue_moves += len(self.get_valid_moves(piece, (row, col)))
        if red_pieces == 0 or red_moves == 0:
            return 'blue'
        elif blue_pieces == 0 or blue_moves == 0:
            return 'red'
        return None
    def print_board(self):
        """Print the current board state to console."""
        for row in range(ROWS):
            row_str = ""
            for col in range(COLS):
                piece = self.board[row][col]
                if piece:
                    if piece.color == 'red':
                        row_str += "R" if not piece.king else "RK"
                    else:
                        row_str += "B" if not piece.king else "BK"
                else:
                    row_str += "."
                row_str += " "
            print(row_str)
        print()