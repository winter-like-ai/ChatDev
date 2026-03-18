'''
Board class representing the checkers board
'''
import pygame
from piece import Piece
from constants import ROWS, COLS, SQUARE_SIZE, RED, BLUE, LIGHT_BROWN, DARK_BROWN, WHITE
class Board:
    def __init__(self):
        self.board = []
        self.red_left = self.blue_left = 12
        self.red_kings = self.blue_kings = 0
        self.create_board()
    def create_board(self):
        """Initialize the board with pieces in starting positions"""
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        # Place pieces on dark squares
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:  # Dark squares
                    if row < 3:
                        self.board[row][col] = Piece(row, col, BLUE)
                    elif row > 4:
                        self.board[row][col] = Piece(row, col, RED)
    def draw(self, screen):
        """Draw the board and pieces"""
        self.draw_squares(screen)
        self.draw_pieces(screen)
    def draw_squares(self, screen):
        """Draw the checkerboard pattern"""
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(screen, color, 
                                (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                 SQUARE_SIZE, SQUARE_SIZE))
    def draw_pieces(self, screen):
        """Draw all pieces on the board"""
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece:
                    piece.draw(screen)
    def get_piece(self, row, col):
        """Get piece at specified position"""
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return None
    def move(self, piece, row, col):
        """Move a piece to new position"""
        # Swap positions
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)
        # Check for king promotion
        if not piece.is_king:
            if piece.color == RED and row == 0:
                piece.make_king()
                self.red_kings += 1
            elif piece.color == BLUE and row == ROWS - 1:
                piece.make_king()
                self.blue_kings += 1
    def remove(self, pieces):
        """Remove captured pieces from the board"""
        for piece in pieces:
            self.board[piece.row][piece.col] = None
            if piece.color == RED:
                self.red_left -= 1
                if piece.is_king:
                    self.red_kings -= 1
            else:
                self.blue_left -= 1
                if piece.is_king:
                    self.blue_kings -= 1
    def get_valid_moves(self, piece):
        """Get all valid moves for a piece"""
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == RED or piece.is_king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == BLUE or piece.is_king:
            moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))
        return moves
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        """Traverse left diagonal for valid moves"""
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
        """Traverse right diagonal for valid moves"""
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
    def winner(self):
        """Check if there's a winner"""
        if self.red_left <= 0:
            return BLUE
        elif self.blue_left <= 0:
            return RED
        return None