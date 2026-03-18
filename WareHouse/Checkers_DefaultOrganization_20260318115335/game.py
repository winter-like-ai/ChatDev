'''
Game class managing game state and logic
'''
import pygame
from board import Board
from constants import RED, BLUE, SQUARE_SIZE, WHITE
class Game:
    def __init__(self, screen):
        self.screen = screen
        self._init()
    def _init(self):
        """Initialize game state"""
        self.selected = None
        self.board = Board()
        self.turn = RED
        self.valid_moves = {}
    def draw(self):
        """Draw the game board and highlight valid moves"""
        self.board.draw(self.screen)
        self.draw_valid_moves()
    def draw_valid_moves(self):
        """Highlight squares that are valid moves for selected piece"""
        if self.selected:
            piece = self.selected
            for move in self.valid_moves:
                row, col = move
                pygame.draw.rect(self.screen, (0, 255, 0, 100),
                                (col * SQUARE_SIZE, row * SQUARE_SIZE,
                                 SQUARE_SIZE, SQUARE_SIZE), 4)
    def select(self, row, col):
        """Select a piece or make a move"""
        if self.selected:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.turn:
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
        return False
    def _move(self, row, col):
        """Move selected piece to target position"""
        piece = self.selected
        if piece and (row, col) in self.valid_moves:
            # Move the piece
            self.board.move(piece, row, col)
            # Remove captured pieces
            skipped = self.valid_moves[(row, col)]
            if skipped:
                self.board.remove(skipped)
            self.change_turn()
            return True
        return False
    def change_turn(self):
        """Switch to the other player's turn"""
        self.valid_moves = {}
        self.selected = None
        self.turn = BLUE if self.turn == RED else RED
    def check_winner(self):
        """Check if there's a winner"""
        return self.board.winner()
    def get_board(self):
        """Get current board state"""
        return self.board
    def reset(self):
        """Reset the game"""
        self._init()