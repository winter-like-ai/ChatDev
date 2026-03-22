'''
Core game logic for Checkers.
Manages game state, rules, and move validation.
'''
class Piece:
    """Represents a checkers piece."""
    def __init__(self, row, col, color):
        """
        Initialize a piece.
        Args:
            row: Row position on board (0-7)
            col: Column position on board (0-7)
            color: 'red' or 'white'
        """
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate pixel position based on board position."""
        self.x = self.col * 100 + 50
        self.y = self.row * 100 + 50
    def make_king(self):
        """Convert piece to a king."""
        self.king = True
    def __repr__(self):
        return f"Piece({self.row}, {self.col}, {self.color}, king={self.king})"
class Board:
    """Manages the checkers board state."""
    def __init__(self):
        """Initialize an empty board."""
        self.board = []
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self.create_board()
    def create_board(self):
        """Set up initial board with pieces in starting positions."""
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
    def move(self, piece, row, col):
        """Move a piece to a new position."""
        # Swap positions
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        # Update piece position
        piece.row = row
        piece.col = col
        piece.calc_pos()
        # Check for king promotion
        if (piece.color == 'red' and row == 7) or (piece.color == 'white' and row == 0):
            if not piece.king:
                piece.make_king()
                if piece.color == 'red':
                    self.red_kings += 1
                else:
                    self.white_kings += 1
    def remove(self, pieces):
        """Remove captured pieces from the board."""
        for piece in pieces:
            if piece is not None:  # Check if piece exists
                self.board[piece.row][piece.col] = None
                if piece.color == 'red':
                    self.red_left -= 1
                else:
                    self.white_left -= 1
    def winner(self):
        """Determine if there's a winner."""
        if self.red_left <= 0:
            return 'white'
        elif self.white_left <= 0:
            return 'red'
        return None
    def get_valid_moves(self, piece):
        """Get all valid moves for a piece."""
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == 'red' or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == 'white' or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, 8), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, 8), 1, piece.color, right))
        return moves
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        """Traverse diagonally left to find valid moves."""
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
                        row = min(r + 3, 8)
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
        """Traverse diagonally right to find valid moves."""
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
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last
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
                last = [current]
            right += 1
        return moves
class CheckersGame:
    """Main game controller managing game state and rules."""
    def __init__(self):
        """Initialize a new game."""
        self.board = Board()
        self.turn = 'red'  # Red starts
        self.selected = None
        self.valid_moves = {}
        self.must_capture = False
        self.game_over = False
        self.winner = None
    def select(self, row, col):
        """Select a piece or position on the board."""
        if self.game_over:
            return False
        piece = self.board.get_piece(row, col)
        # If a piece of current player's color is selected
        if piece is not None and piece.color == self.turn:
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            # Check if there are mandatory captures
            capture_moves = {k: v for k, v in self.valid_moves.items() if v}
            if capture_moves:
                self.valid_moves = capture_moves
                self.must_capture = True
            else:
                self.must_capture = False
            return True
        # If a valid move position is selected
        elif self.selected and (row, col) in self.valid_moves:
            self.move(row, col)
            return True
        return False
    def move(self, row, col):
        """Execute a move to the specified position."""
        piece = self.selected
        skipped = self.valid_moves.get((row, col))
        # Move the piece
        self.board.move(piece, row, col)
        # Remove captured pieces
        if skipped:
            self.board.remove(skipped)
        # Check for additional captures
        if skipped:
            self.valid_moves = self.board.get_valid_moves(piece)
            capture_moves = {k: v for k, v in self.valid_moves.items() if v}
            if capture_moves:
                self.valid_moves = capture_moves
                self.must_capture = True
                return  # Stay on same turn for multiple jumps
        # Switch turns
        self.change_turn()
    def change_turn(self):
        """Switch to the other player's turn."""
        self.selected = None
        self.valid_moves = {}
        self.must_capture = False
        self.turn = 'white' if self.turn == 'red' else 'red'
        # Check if game is over
        self.check_game_over()
    def check_game_over(self):
        """Check if the game has ended."""
        self.winner = self.board.winner()
        if self.winner:
            self.game_over = True
    def is_game_over(self):
        """Return whether the game is over."""
        return self.game_over
    def get_game_state(self):
        """Return current game state information."""
        return {
            'turn': self.turn,
            'selected': self.selected,
            'valid_moves': self.valid_moves,
            'must_capture': self.must_capture,
            'game_over': self.game_over,
            'winner': self.winner,
            'red_left': self.board.red_left,
            'white_left': self.board.white_left,
            'red_kings': self.board.red_kings,
            'white_kings': self.board.white_kings
        }
    def get_board(self):
        """Return the current board state."""
        return self.board