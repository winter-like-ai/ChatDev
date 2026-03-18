'''
Game class containing core game logic.
Manages board state, move validation, and game rules.
'''
from piece import Piece
from constants import ROWS, COLS
class Game:
    def __init__(self):
        """Initialize game with starting board state."""
        self.board = []
        self.red_left = self.blue_left = 12
        self.red_kings = self.blue_kings = 0
        self.turn = 'red'  # Red starts first
        self.selected_piece = None
        self.valid_moves = {}
        self.create_board()
    def create_board(self):
        """Create initial board with pieces in starting positions."""
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        # Place red pieces (top 3 rows)
        for row in range(3):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, 'red')
        # Place blue pieces (bottom 3 rows)
        for row in range(5, ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, 'blue')
    def get_board(self):
        """Return current board state."""
        return self.board
    def get_piece(self, row, col):
        """
        Get piece at specified position.
        Args:
            row: Row position
            col: Column position
        Returns:
            Piece object or None
        """
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return None
    def select(self, row, col):
        """
        Select a piece or move to a position.
        Args:
            row: Row position
            col: Column position
        Returns:
            True if selection was successful, False otherwise
        """
        if self.selected_piece:
            result = self._move(row, col)
            if not result:
                self.selected_piece = None
                self.select(row, col)
        piece = self.get_piece(row, col)
        if piece and piece.color == self.turn:
            self.selected_piece = piece
            self.valid_moves = self._get_valid_moves(piece)
            return True
        return False
    def _move(self, row, col):
        """
        Move selected piece to new position.
        Args:
            row: Destination row
            col: Destination column
        Returns:
            True if move was successful, False otherwise
        """
        piece = self.selected_piece
        if piece and (row, col) in self.valid_moves:
            # Move the piece
            self.board[piece.row][piece.col] = None
            self.board[row][col] = piece
            piece.move(row, col)
            # Handle captures
            if self.valid_moves[(row, col)]:
                self._remove(self.valid_moves[(row, col)])
            # King promotion
            if not piece.king:
                if piece.color == 'red' and row == ROWS - 1:
                    piece.make_king()
                    self.red_kings += 1
                elif piece.color == 'blue' and row == 0:
                    piece.make_king()
                    self.blue_kings += 1
            # Switch turns
            self.change_turn()
            self.selected_piece = None
            self.valid_moves = {}
            return True
        return False
    def _remove(self, pieces):
        """
        Remove captured pieces from board.
        Args:
            pieces: List of pieces to remove
        """
        for piece in pieces:
            self.board[piece.row][piece.col] = None
            if piece.color == 'red':
                self.red_left -= 1
                if piece.king:
                    self.red_kings -= 1
            else:
                self.blue_left -= 1
                if piece.king:
                    self.blue_kings -= 1
    def _get_valid_moves(self, piece):
        """
        Get all valid moves for a piece.
        Args:
            piece: Piece to check moves for
        Returns:
            Dictionary of valid moves with capture information
        """
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == 'red' or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == 'blue' or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))
        return moves
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        """
        Traverse board to left to find valid moves.
        Args:
            start: Starting row
            stop: Stopping row
            step: Direction (1 for down, -1 for up)
            color: Piece color
            left: Left column boundary
            skipped: List of skipped pieces
        Returns:
            Dictionary of valid moves
        """
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
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last
                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, left + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            left -= 1
        return moves
    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        """
        Traverse board to right to find valid moves.
        Args:
            start: Starting row
            stop: Stopping row
            step: Direction (1 for down, -1 for up)
            color: Piece color
            right: Right column boundary
            skipped: List of skipped pieces
        Returns:
            Dictionary of valid moves
        """
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break
            current = self.board[r][right]
            if current is None:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last
                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, ROWS)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            right += 1
        return moves
    def change_turn(self):
        """Switch turns between players."""
        self.turn = 'blue' if self.turn == 'red' else 'red'
    def winner(self):
        """
        Check if there's a winner.
        Returns:
            'red', 'blue', or None if no winner yet
        """
        if self.red_left <= 0:
            return 'blue'
        elif self.blue_left <= 0:
            return 'red'
        return None
    def get_turn(self):
        """Get current player's turn."""
        return self.turn
    def get_selected_piece(self):
        """Get currently selected piece."""
        return self.selected_piece
    def get_valid_moves(self):
        """Get valid moves for selected piece."""
        return self.valid_moves