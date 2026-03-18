'''
Piece class representing a checkers piece.
Handles movement, king status, and drawing.
'''
import pygame
from constants import *
class Piece:
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        '''Calculate pixel position based on board coordinates.'''
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2
    def make_king(self):
        '''Promote piece to king.'''
        self.king = True
    def draw(self, screen):
        '''Draw the piece on the screen.'''
        radius = PIECE_RADIUS
        pygame.draw.circle(screen, GRAY, (self.x, self.y), radius + 2)
        pygame.draw.circle(screen, self.color, (self.x, self.y), radius)
        if self.king:
            # Draw crown for king pieces
            pygame.draw.circle(screen, (255, 215, 0), (self.x, self.y), KING_CROWN_RADIUS)
            pygame.draw.circle(screen, (255, 255, 0), (self.x, self.y), KING_CROWN_RADIUS - 3)
    def move(self, row, col):
        '''Move piece to new position.'''
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        return f"Piece({self.row}, {self.col}, {self.color}, king={self.king})"