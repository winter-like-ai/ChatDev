'''
Piece class representing a checkers piece.
Manages piece state, movement, and drawing.
'''
import pygame
from constants import *
class Piece:
    def __init__(self, row, col, player):
        self.row = row
        self.col = col
        self.player = player  # 1 or 2
        self.type = MAN  # Start as regular piece
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        '''Calculate pixel position based on row and column'''
        self.x = self.col * SQUARE_SIZE + SQUARE_SIZE // 2
        self.y = self.row * SQUARE_SIZE + SQUARE_SIZE // 2
    def make_king(self):
        '''Promote piece to king'''
        self.type = KING
    def is_king(self):
        '''Check if piece is a king'''
        return self.type == KING
    def draw(self, win):
        '''Draw the piece on the board'''
        radius = SQUARE_SIZE // 2 - 10
        # Draw outer circle
        color = RED if self.player == PLAYER1 else BLUE
        pygame.draw.circle(win, color, (self.x, self.y), radius)
        # Draw inner circle for contrast
        inner_color = (200, 0, 0) if self.player == PLAYER1 else (0, 0, 200)
        pygame.draw.circle(win, inner_color, (self.x, self.y), radius - 5)
        # Draw crown if king
        if self.is_king():
            crown_color = GOLD
            pygame.draw.circle(win, crown_color, (self.x, self.y), radius - 15)
    def move(self, row, col):
        '''Move piece to new position'''
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        return f"Piece(player={self.player}, type={self.type}, pos=({self.row}, {self.col}))"