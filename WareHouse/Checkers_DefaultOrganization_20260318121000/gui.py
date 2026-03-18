'''
GUI rendering and input handling using Pygame.
'''
import pygame
from constants import (
    WIDTH, HEIGHT, SQUARE_SIZE, ROWS, COLS,
    LIGHT_BROWN, DARK_BROWN, HIGHLIGHT_COLOR,
    RED, BLUE
)
class GUI:
    def __init__(self):
        """Initialize the Pygame window."""
        self.win = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Checkers Game")
    def draw_board(self, board):
        """
        Draw the checkerboard.
        Args:
            board: The game board
        """
        self.win.fill(LIGHT_BROWN)
        # Draw dark squares
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    pygame.draw.rect(
                        self.win,
                        DARK_BROWN,
                        (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                    )
        # Draw grid lines
        for i in range(ROWS + 1):
            pygame.draw.line(
                self.win,
                BLACK,
                (0, i * SQUARE_SIZE),
                (WIDTH, i * SQUARE_SIZE),
                2
            )
            pygame.draw.line(
                self.win,
                BLACK,
                (i * SQUARE_SIZE, 0),
                (i * SQUARE_SIZE, HEIGHT),
                2
            )
    def draw_pieces(self, board):
        """
        Draw all pieces on the board.
        Args:
            board: The game board
        """
        for row in range(ROWS):
            for col in range(COLS):
                piece = board[row][col]
                if piece:
                    piece.draw(self.win)
    def get_board_position(self, pos):
        """
        Convert screen coordinates to board position.
        Args:
            pos: (x, y) screen coordinates
        Returns:
            (row, col) board position
        """
        x, y = pos
        row = y // SQUARE_SIZE
        col = x // SQUARE_SIZE
        return row, col
    def highlight_selected(self, pos):
        """
        Highlight the selected piece.
        Args:
            pos: (row, col) position to highlight
        """
        row, col = pos
        # Create a transparent surface for highlighting
        highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        highlight_surface.fill(HIGHLIGHT_COLOR)
        self.win.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    def highlight_moves(self, moves):
        """
        Highlight valid moves.
        Args:
            moves: List of (row, col) positions to highlight
        """
        for row, col in moves:
            # Draw a circle at the center of the square
            center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
            # Draw a green circle for valid moves
            pygame.draw.circle(self.win, GREEN, (center_x, center_y), 15)
            pygame.draw.circle(self.win, BLACK, (center_x, center_y), 15, 2)
    def show_message(self, message):
        """
        Display a message on the screen.
        Args:
            message: Text to display
        """
        # Create a semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.win.blit(overlay, (0, 0))
        # Render the message
        font = pygame.font.SysFont('arial', 48)
        text = font.render(message, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.win.blit(text, text_rect)
        pygame.display.flip()
        pygame.time.wait(3000)