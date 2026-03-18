'''
Checkers board class.
Manages board state, piece placement, and game rules.
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
        '''Initialize the board with pieces in starting positions'''
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        # Place pieces for player 1 (top rows)
        for row in range(3):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, PLAYER1)
        # Place pieces for player 2 (bottom rows)
        for row in range(5, ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, PLAYER2)
    def draw(self, win):
        '''Draw the board and all pieces'''
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
                if piece:
                    piece.draw(win)
    def get_piece(self, row, col):
        '''Get piece at specified position'''
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return None
    def remove_piece(self, row, col):
        '''Remove piece from board'''
        self.board[row][col] = None
    def move_piece(self, piece, row, col):
        '''Move piece to new position'''
        # Remove piece from old position
        self.board[piece.row][piece.col] = None
        # Place piece at new position
        self.board[row][col] = piece
        piece.move(row, col)
        # Check for king promotion
        if piece.player == PLAYER1 and row == ROWS - 1:
            piece.make_king()
        elif piece.player == PLAYER2 and row == 0:
            piece.make_king()
    def get_valid_moves(self, piece):
        '''Get all valid moves for a piece'''
        moves = {}
        row = piece.row
        col = piece.col
        # Directions based on player and piece type
        if piece.player == PLAYER1 or piece.is_king():
            moves.update(self._traverse_left(row-1, max(row-3, -1), -1, piece.player, col-1))
            moves.update(self._traverse_right(row-1, max(row-3, -1), -1, piece.player, col+1))
        if piece.player == PLAYER2 or piece.is_king():
            moves.update(self._traverse_left(row+1, min(row+3, ROWS), 1, piece.player, col-1))
            moves.update(self._traverse_right(row+1, min(row+3, ROWS), 1, piece.player, col+1))
        return moves
    def _traverse_left(self, start, stop, step, player, left, skipped=[]):
        '''Traverse left diagonal for valid moves'''
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
                        row = max(r-3, 0)
                    else:
                        row = min(r+3, ROWS)
                    moves.update(self._traverse_left(r+step, row, step, player, left-1, skipped=last))
                    moves.update(self._traverse_right(r+step, row, step, player, left+1, skipped=last))
                break
            elif current.player == player:
                break
            else:
                last = [current]
            left -= 1
        return moves
    def _traverse_right(self, start, stop, step, player, right, skipped=[]):
        '''Traverse right diagonal for valid moves'''
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
                        row = max(r-3, 0)
                    else:
                        row = min(r+3, ROWS)
                    moves.update(self._traverse_left(r+step, row, step, player, right-1, skipped=last))
                    moves.update(self._traverse_right(r+step, row, step, player, right+1, skipped=last))
                break
            elif current.player == player:
                break
            else:
                last = [current]
            right += 1
        return moves
    def get_all_pieces(self, player):
        '''Get all pieces for a specific player'''
        pieces = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece and piece.player == player:
                    pieces.append(piece)
        return pieces
    def get_all_valid_moves(self, player):
        '''Get all valid moves for a player, prioritizing captures'''
        all_moves = {}
        capture_moves = {}
        regular_moves = {}
        pieces = self.get_all_pieces(player)
        # First pass: collect all moves
        for piece in pieces:
            moves = self.get_valid_moves(piece)
            if moves:
                for move, skipped in moves.items():
                    if skipped:  # This is a capture move
                        if piece not in capture_moves:
                            capture_moves[piece] = {}
                        capture_moves[piece][move] = skipped
                    else:  # This is a regular move
                        if piece not in regular_moves:
                            regular_moves[piece] = {}
                        regular_moves[piece][move] = skipped
        # If there are capture moves, return only those (mandatory capture rule)
        if capture_moves:
            return capture_moves
        # Otherwise, return regular moves
        return regular_moves