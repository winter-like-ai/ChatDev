'''
game.py
Core game logic for Checkers including board state, move validation,
and game rules implementation.
'''
class Piece:
    """Represents a checkers piece on the board."""
    def __init__(self, row, col, color):
        """
        Initialize a checkers piece.
        Args:
            row: Row position on the board (0-7)
            col: Column position on the board (0-7)
            color: 'red' or 'white' indicating player color
        """
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate pixel position based on board coordinates."""
        self.x = self.col * 100 + 50
        self.y = self.row * 100 + 50
    def make_king(self):
        """Convert piece to a king."""
        self.king = True
    def move(self, row, col):
        """Move piece to new position."""
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        return f"Piece({self.row}, {self.col}, {self.color}, king={self.king})"
class Board:
    """Manages the checkers board state and piece positions."""
    def __init__(self):
        """Initialize an empty 8x8 board."""
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
        """Move a piece to new position and handle king promotion."""
        # Swap positions
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)
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
        """Get all valid moves for a given piece."""
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
        """Helper function to find moves in left diagonal direction."""
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
        """Helper function to find moves in right diagonal direction."""
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
class Game:
    """Main game controller managing game state and turns."""
    def __init__(self):
        """Initialize a new game."""
        self.board = Board()
        self.turn = 'red'  # Red starts
        self.selected = None
        self.valid_moves = {}
        self.game_over = False
        self.winner = None
    def select(self, row, col):
        """Select a piece or destination square."""
        if self.game_over:
            return False
        piece = self.board.get_piece(row, col)
        # If a piece of current player's color is selected
        if piece and piece.color == self.turn:
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
        # If a destination square is selected
        elif self.selected and (row, col) in self.valid_moves:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        return False
    def _move(self, row, col):
        """Execute a move from selected piece to destination."""
        piece = self.selected
        destination = self.valid_moves.get((row, col))
        if not destination:
            return False
        # Move the piece
        self.board.move(piece, row, col)
        # Remove captured pieces
        if destination:
            self.board.remove(destination)
        # Check for multiple jumps
        if destination and self.board.get_valid_moves(piece):
            # Continue jumping with same piece
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
        else:
            # Switch turns
            self.change_turn()
            return True
    def change_turn(self):
        """Switch to the other player's turn."""
        self.valid_moves = {}
        self.selected = None
        if self.turn == 'red':
            self.turn = 'white'
        else:
            self.turn = 'red'
        # Check for winner
        self.winner = self.board.winner()
        if self.winner:
            self.game_over = True
    def get_board(self):
        """Return the current board state."""
        return self.board
    def ai_move(self):
        """Simple AI move for single player mode (placeholder)."""
        # This is a placeholder - in a full implementation, this would
        # contain AI logic for making moves
        pass