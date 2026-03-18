'''
Board class for Checkers.
Manages the 8x8 board, piece positions, and board logic.
'''
from piece import Piece
class Board:
    """Represents the Checkers game board."""
    def __init__(self):
        """Initialize an 8x8 Checkers board with pieces in starting positions."""
        self.board = []
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self.create_board()
    def create_board(self):
        """Create the initial board setup with pieces."""
        self.board = [[None for _ in range(8)] for _ in range(8)]
        # Place red pieces (top three rows)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, 'red')
        # Place white pieces (bottom three rows)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, 'white')
    def get_piece(self, row, col):
        """Get piece at specified position."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    def move(self, piece, row, col, captures=None):
        """Move a piece to a new position."""
        # Remove piece from old position
        self.board[piece.row][piece.col] = None
        # Place piece at new position
        piece.move(row, col)
        self.board[row][col] = piece
        # Handle captures
        captured = False
        if captures:
            for capture_row, capture_col in captures:
                captured_piece = self.board[capture_row][capture_col]
                if captured_piece:
                    self.board[capture_row][capture_col] = None
                    if captured_piece.color == 'red':
                        self.red_left -= 1
                        if captured_piece.king:
                            self.red_kings -= 1
                    else:
                        self.white_left -= 1
                        if captured_piece.king:
                            self.white_kings -= 1
                    captured = True
        return captured
    def king_piece(self, piece):
        """Promote a piece to king if it reaches the opposite end."""
        if not piece.king:
            if piece.color == 'red' and piece.row == 7:
                piece.make_king()
                self.red_kings += 1
                return True
            elif piece.color == 'white' and piece.row == 0:
                piece.make_king()
                self.white_kings += 1
                return True
        return False
    def get_valid_moves(self, piece):
        """Get all valid moves for a piece."""
        moves = {}
        # Check for forced captures first
        captures = self.get_captures(piece)
        if captures:
            return captures
        # Regular moves
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == 'red' or piece.king:
            # Check upward moves
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == 'white' or piece.king:
            # Check downward moves
            moves.update(self._traverse_left(row + 1, min(row + 3, 8), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, 8), 1, piece.color, right))
        return moves
    def get_captures(self, piece):
        """Get all capture moves for a piece."""
        captures = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == 'red' or piece.king:
            # Check upward captures
            captures.update(self._traverse_left_capture(row - 1, max(row - 3, -1), -1, piece.color, left, []))
            captures.update(self._traverse_right_capture(row - 1, max(row - 3, -1), -1, piece.color, right, []))
        if piece.color == 'white' or piece.king:
            # Check downward captures
            captures.update(self._traverse_left_capture(row + 1, min(row + 3, 8), 1, piece.color, left, []))
            captures.update(self._traverse_right_capture(row + 1, min(row + 3, 8), 1, piece.color, right, []))
        return captures
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        """Traverse left for regular moves."""
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            current = self.board[r][left]
            if current is None:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = {'captures': last + skipped}
                else:
                    moves[(r, left)] = {'captures': last}
                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, 8)
                    moves.update(self._traverse_left(r + step, row, step, color, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, left + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [(r, left)]
            left -= 1
        return moves
    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        """Traverse right for regular moves."""
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= 8:
                break
            current = self.board[r][right]
            if current is None:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = {'captures': last + skipped}
                else:
                    moves[(r, right)] = {'captures': last}
                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, 8)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [(r, right)]
            right += 1
        return moves
    def _traverse_left_capture(self, start, stop, step, color, left, skipped):
        """Traverse left for capture moves."""
        moves = {}
        for r in range(start, stop, step):
            if left < 0:
                break
            current = self.board[r][left]
            if current is None:
                if skipped:
                    moves[(r, left)] = {'captures': skipped}
                    # Check for further captures
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, 8)
                    moves.update(self._traverse_left_capture(r + step, row, step, color, left - 1, skipped))
                    moves.update(self._traverse_right_capture(r + step, row, step, color, left + 1, skipped))
                break
            elif current.color == color:
                break
            else:
                skipped = [(r, left)]
            left -= 1
        return moves
    def _traverse_right_capture(self, start, stop, step, color, right, skipped):
        """Traverse right for capture moves."""
        moves = {}
        for r in range(start, stop, step):
            if right >= 8:
                break
            current = self.board[r][right]
            if current is None:
                if skipped:
                    moves[(r, right)] = {'captures': skipped}
                    # Check for further captures
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, 8)
                    moves.update(self._traverse_left_capture(r + step, row, step, color, right - 1, skipped))
                    moves.update(self._traverse_right_capture(r + step, row, step, color, right + 1, skipped))
                break
            elif current.color == color:
                break
            else:
                skipped = [(r, right)]
            right += 1
        return moves
    def has_valid_moves(self, color):
        """Check if a player has any valid moves."""
        for piece in self.get_pieces_by_color(color):
            if self.get_valid_moves(piece):
                return True
        return False
    def get_pieces_by_color(self, color):
        """Get all pieces of a specific color."""
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.color == color:
                    pieces.append(piece)
        return pieces
    def get_board_state(self):
        """Get the current board state as a 2D array."""
        return self.board