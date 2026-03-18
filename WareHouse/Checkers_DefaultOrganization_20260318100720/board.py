'''
Board class representing the checkers board.
Manages piece placement, movement validation, and captures.
'''
import pygame
from piece import Piece
from constants import *
class Board:
    def __init__(self):
        self.board = []
        self.selected_piece = None
        self.valid_moves = {}
        self.create_board()
    def create_board(self):
        '''Initialize board with pieces in starting positions'''
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        # Place pieces for player 1 (top rows)
        for row in range(3):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, PLAYER1_COLOR)
        # Place pieces for player 2 (bottom rows)
        for row in range(5, ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, PLAYER2_COLOR)
    def get_piece(self, row, col):
        '''Get piece at specified position'''
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return None
    def draw(self, win):
        '''Draw board and pieces'''
        # Draw board squares
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(win, color, 
                               (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                SQUARE_SIZE, SQUARE_SIZE))
        # Draw pieces
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece:
                    # Draw piece circle
                    pygame.draw.circle(win, piece.color, 
                                     (piece.x, piece.y), PIECE_RADIUS)
                    # Draw king crown
                    if piece.king:
                        pygame.draw.circle(win, GREEN, 
                                         (piece.x, piece.y), KING_RADIUS)
                        # Draw small crown symbol
                        pygame.draw.circle(win, YELLOW, 
                                         (piece.x, piece.y), KING_RADIUS - 10)
        # Highlight selected piece
        if self.selected_piece:
            row, col = self.selected_piece.row, self.selected_piece.col
            pygame.draw.rect(win, HIGHLIGHT, 
                           (col * SQUARE_SIZE, row * SQUARE_SIZE,
                            SQUARE_SIZE, SQUARE_SIZE), 4)
            # Highlight valid moves
            for move in self.valid_moves:
                pygame.draw.circle(win, GREEN, 
                                 (move[1] * SQUARE_SIZE + SQUARE_SIZE//2,
                                  move[0] * SQUARE_SIZE + SQUARE_SIZE//2), 15)
    def remove(self, pieces):
        '''Remove captured pieces from board'''
        for piece in pieces:
            self.board[piece.row][piece.col] = None
    def winner(self):
        '''Check if there's a winner'''
        red_pieces = 0
        blue_pieces = 0
        for row in self.board:
            for piece in row:
                if piece:
                    if piece.color == PLAYER1_COLOR:
                        red_pieces += 1
                    else:
                        blue_pieces += 1
        if red_pieces == 0:
            return PLAYER2_COLOR
        elif blue_pieces == 0:
            return PLAYER1_COLOR
        return None
    def get_valid_moves(self, piece):
        '''Get all valid moves for a piece'''
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == PLAYER2_COLOR or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == PLAYER1_COLOR or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, ROWS), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, ROWS), 1, piece.color, right))
        return moves
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        '''Helper for left diagonal moves'''
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
        '''Helper for right diagonal moves'''
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
    def select(self, row, col):
        '''Select a piece'''
        piece = self.get_piece(row, col)
        if piece:
            self.selected_piece = piece
            self.valid_moves = self.get_valid_moves(piece)
            return True
        return False
    def move(self, piece, row, col):
        '''Move a piece to new position'''
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)
        # King promotion
        if row == 0 and piece.color == PLAYER2_COLOR:
            piece.make_king()
        elif row == ROWS - 1 and piece.color == PLAYER1_COLOR:
            piece.make_king()