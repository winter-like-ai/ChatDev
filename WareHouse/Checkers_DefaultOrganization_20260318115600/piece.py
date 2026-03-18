'''
Piece class representing a checkers piece
'''
from constants import BOARD_SIZE
class Piece:
    def __init__(self, color, row, col):
        self.color = color  # 'red' or 'blue'
        self.row = row
        self.col = col
        self.king = False
        self.direction = 1 if color == 'red' else -1  # red moves down, blue moves up
    def make_king(self):
        self.king = True
    def get_possible_moves(self, board):
        moves = []
        captures = []
        # Regular moves (single step)
        if self.king or self.direction == 1:  # Can move down or is king
            moves.extend(self._get_moves_in_direction(board, 1))
        if self.king or self.direction == -1:  # Can move up or is king
            moves.extend(self._get_moves_in_direction(board, -1))
        # Capture moves
        if self.king or self.direction == 1:
            captures.extend(self._get_captures_in_direction(board, 1))
        if self.king or self.direction == -1:
            captures.extend(self._get_captures_in_direction(board, -1))
        return moves, captures
    def _get_moves_in_direction(self, board, row_direction):
        moves = []
        new_row = self.row + row_direction
        if 0 <= new_row < BOARD_SIZE:
            # Left diagonal
            new_col = self.col - 1
            if 0 <= new_col < BOARD_SIZE and board[new_row][new_col] == 0:
                moves.append((new_row, new_col))
            # Right diagonal
            new_col = self.col + 1
            if 0 <= new_col < BOARD_SIZE and board[new_row][new_col] == 0:
                moves.append((new_row, new_col))
        return moves
    def _get_captures_in_direction(self, board, row_direction):
        captures = []
        # Check left capture
        new_row = self.row + row_direction
        jump_row = self.row + 2 * row_direction
        if 0 <= new_row < BOARD_SIZE and 0 <= jump_row < BOARD_SIZE:
            # Left capture
            new_col = self.col - 1
            jump_col = self.col - 2
            if (0 <= new_col < BOARD_SIZE and 0 <= jump_col < BOARD_SIZE and 
                board[new_row][new_col] != 0 and 
                board[new_row][new_col].color != self.color and
                board[jump_row][jump_col] == 0):
                captures.append((jump_row, jump_col, new_row, new_col))
            # Right capture
            new_col = self.col + 1
            jump_col = self.col + 2
            if (0 <= new_col < BOARD_SIZE and 0 <= jump_col < BOARD_SIZE and 
                board[new_row][new_col] != 0 and 
                board[new_row][new_col].color != self.color and
                board[jump_row][jump_col] == 0):
                captures.append((jump_row, jump_col, new_row, new_col))
        return captures
    def move(self, row, col):
        self.row = row
        self.col = col
        # Check for king promotion
        if (self.color == 'red' and row == BOARD_SIZE - 1) or (self.color == 'blue' and row == 0):
            self.make_king()
    def __repr__(self):
        king_str = "K" if self.king else ""
        return f"{self.color[0].upper()}{king_str}({self.row},{self.col})"