'''
board.py
Board class managing the game board state and piece positions.
'''
from piece import Piece
import constants
class Board:
    """Manages the checkers board state and piece positions."""
    def __init__(self):
        """Initialize an empty board and set up initial pieces."""
        self.board = []
        self.create_board()
    def create_board(self):
        """Create the initial board setup with pieces in starting positions."""
        self.board = [[0 for _ in range(constants.BOARD_SIZE)] for _ in range(constants.BOARD_SIZE)]
        # Place player one pieces (top three rows)
        for row in range(3):
            for col in range(constants.BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, constants.PLAYER_ONE)
        # Place player two pieces (bottom three rows)
        for row in range(5, constants.BOARD_SIZE):
            for col in range(constants.BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, constants.PLAYER_TWO)
    def get_piece(self, row, col):
        """Get piece at specified position."""
        if 0 <= row < constants.BOARD_SIZE and 0 <= col < constants.BOARD_SIZE:
            return self.board[row][col]
        return None
    def move(self, piece, row, col):
        """Move a piece to a new position."""
        # Store the piece
        temp = self.board[piece.row][piece.col]
        # Clear old position
        self.board[piece.row][piece.col] = 0
        # Place piece in new position
        piece.move(row, col)
        self.board[row][col] = temp
    def remove(self, pieces):
        """Remove captured pieces from the board."""
        for piece in pieces:
            self.board[piece.row][piece.col] = 0
    def get_valid_moves(self, piece):
        """Get all valid moves for a given piece."""
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == constants.PLAYER_TWO or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == constants.PLAYER_ONE or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, constants.BOARD_SIZE), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, constants.BOARD_SIZE), 1, piece.color, right))
        return moves
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        """Traverse left diagonal for possible moves."""
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            current = self.board[r][left]
            if current == 0:
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
                        row = min(r + 3, constants.BOARD_SIZE)
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
        """Traverse right diagonal for possible moves."""
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= constants.BOARD_SIZE:
                break
            current = self.board[r][right]
            if current == 0:
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
                        row = min(r + 3, constants.BOARD_SIZE)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            right += 1
        return moves
    def get_all_valid_moves(self, color):
        """Get all valid moves for all pieces of a given color."""
        all_moves = {}
        for row in range(constants.BOARD_SIZE):
            for col in range(constants.BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0 and piece.color == color:
                    moves = self.get_valid_moves(piece)
                    if moves:
                        all_moves[(row, col)] = moves
        return all_moves
    def has_capture_moves(self, color):
        """Check if there are any capture moves available for the given color."""
        for row in range(constants.BOARD_SIZE):
            for col in range(constants.BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0 and piece.color == color:
                    moves = self.get_valid_moves(piece)
                    for move in moves.values():
                        if move:  # If there are captured pieces in the move
                            return True
        return False
    def winner(self):
        """Check if there's a winner."""
        red_pieces = 0
        blue_pieces = 0
        for row in self.board:
            for piece in row:
                if piece != 0:
                    if piece.color == constants.PLAYER_ONE:
                        red_pieces += 1
                    else:
                        blue_pieces += 1
        if red_pieces == 0:
            return constants.PLAYER_TWO
        elif blue_pieces == 0:
            return constants.PLAYER_ONE
        return None