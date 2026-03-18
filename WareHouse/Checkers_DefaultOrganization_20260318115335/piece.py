'''
Piece class representing a checkers piece
'''
import pygame
from constants import SQUARE_SIZE, RED, BLUE, WHITE, CROWN
class Piece:
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.is_king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate pixel position based on board coordinates"""
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2
    def make_king(self):
        """Promote piece to king"""
        self.is_king = True
    def draw(self, screen):
        """Draw the piece on the screen"""
        radius = SQUARE_SIZE // 2 - 10
        # Draw piece body
        pygame.draw.circle(screen, self.color, (self.x, self.y), radius)
        # Draw outline
        outline_color = WHITE if self.color == RED or self.color == BLUE else BLACK
        pygame.draw.circle(screen, outline_color, (self.x, self.y), radius, 2)
        # Draw crown if king
        if self.is_king:
            screen.blit(CROWN, (self.x - CROWN.get_width() // 2, 
                               self.y - CROWN.get_height() // 2))
    def move(self, row, col):
        """Move piece to new position"""
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        return f"Piece({self.row}, {self.col}, {self.color}, king={self.is_king})"