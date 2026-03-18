'''
Piece class representing individual checkers pieces.
Handles piece properties and drawing.
'''
import pygame
from constants import *
class Piece:
    def __init__(self, row, col, color):
        """
        Initialize a checkers piece.
        Args:
            row: Row position on board (0-7)
            col: Column position on board (0-7)
            color: Piece color ('red' or 'blue')
        """
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate pixel position based on board coordinates."""
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2
    def make_king(self):
        """Promote piece to king."""
        self.king = True
    def draw(self, win):
        """
        Draw the piece on the screen.
        Args:
            win: Pygame window surface
        """
        # Draw piece circle
        radius = SQUARE_SIZE // 2 - 10
        pygame.draw.circle(win, RED if self.color == 'red' else BLUE, 
                          (self.x, self.y), radius)
        # Draw border
        pygame.draw.circle(win, WHITE, (self.x, self.y), radius, 2)
        # Draw crown if king
        if self.king:
            # Draw simple crown (yellow circle with points)
            crown_radius = radius // 2
            pygame.draw.circle(win, (255, 215, 0), (self.x, self.y), crown_radius)
            # Draw crown border
            pygame.draw.circle(win, (255, 255, 0), (self.x, self.y), crown_radius, 2)
            # Draw crown points (simplified)
            for i in range(5):
                angle = i * 72 * 3.14159 / 180
                x = self.x + crown_radius * 0.7 * pygame.math.Vector2(1, 0).rotate(i * 72).x
                y = self.y + crown_radius * 0.7 * pygame.math.Vector2(1, 0).rotate(i * 72).y
                pygame.draw.circle(win, (255, 255, 0), (int(x), int(y)), 4)
    def move(self, row, col):
        """
        Move piece to new position.
        Args:
            row: New row position
            col: New column position
        """
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        """String representation of piece."""
        return f"Piece({self.row}, {self.col}, {self.color}, king={self.king})"