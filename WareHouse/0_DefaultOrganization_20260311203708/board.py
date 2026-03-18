'''
Board class representing the checkers board
'''
import pygame
from piece import Piece
from constants import *
class Board:
    def __init__(self):
        self.board = []
        self.red_left = self.blue_left = 12
        self.red_kings = self.blue_kings = 0
        self.create_board()
    def create_board(self):
        '''Initialize board with pieces in starting positions'''
        self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        # Place pieces on black squares
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:  # Black squares
                    if row < 3:
                        self.board[row][col] = Piece(row, col, PLAYER_TWO)
                    elif row > 4:
                        self.board[row][col] = Piece(row, col, PLAYER_ONE)
    def draw(self, win):
        '''Draw board and pieces'''
        self.draw_squares(win)
        self.draw_pieces(win)
    def draw_squares(self, win):
        '''Draw the checkerboard pattern'''
        win.fill(LIGHT_BROWN)
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    pygame.draw.rect(win, DARK_BROWN, 
                                    (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                     SQUARE_SIZE, SQUARE_SIZE))
    def draw_pieces(self, win):
        '''Draw all pieces on the board'''
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != EMPTY:
                    # Draw piece
                    color = RED if piece.color == PLAYER_ONE else BLUE
                    pygame.draw.circle(win, color, (piece.x, piece.y), PIECE_RADIUS)
                    pygame.draw.circle(win, BLACK, (piece.x, piece.y), PIECE_RADIUS, 2)
                    # Draw crown for kings
                    if piece.king:
                        # Draw a crown symbol (letter K)
                        font = pygame.font.SysFont('Arial', 24)
                        text = font.render('K', True, YELLOW)
                        text_rect = text.get_rect(center=(piece.x, piece.y))
                        win.blit(text, text_rect)
    def get_piece(self, row, col):
        '''Get piece at specified position'''
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return None
    def move(self, piece, row, col):
        '''Move piece to new position'''
        # Swap positions
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)
        # Check for king promotion
        if not piece.king:
            if piece.color == PLAYER_ONE and row == 0:
                piece.make_king()
                self.red_kings += 1
            elif piece.color == PLAYER_TWO and row == ROWS - 1:
                piece.make_king()
                self.blue_kings += 1
    def remove(self, pieces):
        '''Remove captured pieces'''
        for piece in pieces:
            self.board[piece.row][piece.col] = EMPTY
            if piece.color == PLAYER_ONE:
                self.red_left -= 1
                if piece.king:
                    self.red_kings -= 1
            else:
                self.blue_left -= 1
                if piece.king:
                    self.blue_kings -= 1
    def get_valid_moves(self, piece):
        '''Get all valid moves for a piece'''
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == PLAYER_ONE or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == PLAYER_TWO or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))
        return moves
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        '''Traverse left diagonal for valid moves'''
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            current = self.board[r][left]
            if current == EMPTY:
                if skipped and not last:
                    break
                moves[(r, left)] = last + skipped
                if last:
                    moves.update(self._traverse_left(r + step, r + (3 * step), step, color, left - 1, skipped=last + skipped))
                    moves.update(self._traverse_right(r + step, r + (3 * step), step, color, left + 1, skipped=last + skipped))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            left -= 1
        return moves
    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        '''Traverse right diagonal for valid moves'''
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= COLS:
                break
            current = self.board[r][right]
            if current == EMPTY:
                if skipped and not last:
                    break
                moves[(r, right)] = last + skipped
                if last:
                    moves.update(self._traverse_left(r + step, r + (3 * step), step, color, right - 1, skipped=last + skipped))
                    moves.update(self._traverse_right(r + step, r + (3 * step), step, color, right + 1, skipped=last + skipped))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            right += 1
        return moves
    def winner(self):
        '''Check if there's a winner'''
        if self.red_left <= 0:
            return PLAYER_TWO
        elif self.blue_left <= 0:
            return PLAYER_ONE
        return None