'''
Piece class representing individual checkers pieces.
Handles piece properties and drawing.
'''
import pygame
from constants import SQUARE_SIZE, PIECE_RADIUS, KING_OFFSET, RED, BLUE, WHITE, BLACK
class Piece:
    def __init__(self, color, row, col):
        """
        Initialize a checkers piece.
        Args:
            color: 'red' or 'blue'
            row: Row position on board (0-7)
            col: Column position on board (0-7)
        """
        self.color = color
        self.row = row
        self.col = col
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate pixel position based on board position."""
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
        # Draw main piece
        color = RED if self.color == 'red' else BLUE
        pygame.draw.circle(win, color, (self.x, self.y), PIECE_RADIUS)
        # Draw outline
        pygame.draw.circle(win, BLACK, (self.x, self.y), PIECE_RADIUS, 2)
        # Draw king crown if king
        if self.king:
            # Draw a smaller circle inside for king
            pygame.draw.circle(win, WHITE, (self.x, self.y), PIECE_RADIUS - 10)
            pygame.draw.circle(win, BLACK, (self.x, self.y), PIECE_RADIUS - 10, 2)
            # Draw K letter for king
            font = pygame.font.SysFont('arial', 20)
            text = font.render('K', True, BLACK)
            text_rect = text.get_rect(center=(self.x, self.y))
            win.blit(text, text_rect)
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
        return f"Piece({self.color}, {self.row}, {self.col}, king={self.king})"