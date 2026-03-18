'''
gui.py
GUI class handling graphical interface using Pygame.
'''
import pygame
import sys
from constants import *
class GUI:
    """Graphical user interface for the Checkers game using Pygame."""
    def __init__(self, game):
        """
        Initialize the GUI.
        Args:
            game: Game instance to control
        """
        self.game = game
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Checkers Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
    def run(self):
        """Main game loop."""
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    row, col = self.get_row_col_from_mouse(pos)
                    self.game.select(row, col)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game.reset()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            self.draw()
            pygame.display.update()
        pygame.quit()
        sys.exit()
    def get_row_col_from_mouse(self, pos):
        """Convert mouse position to board coordinates."""
        x, y = pos
        row = y // SQUARE_SIZE
        col = x // SQUARE_SIZE
        return row, col
    def draw(self):
        """Draw the entire game interface."""
        self.window.fill(BLACK)
        self.draw_board()
        self.draw_pieces()
        self.draw_status()
        if self.game.game_over:
            self.draw_game_over()
    def draw_board(self):
        """Draw the checkers board."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                # Alternate square colors
                if (row + col) % 2 == 0:
                    color = LIGHT_BROWN
                else:
                    color = DARK_BROWN
                # Draw square
                pygame.draw.rect(self.window, color, 
                                (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                 SQUARE_SIZE, SQUARE_SIZE))
                # Highlight selected piece's valid moves
                if self.game.selected:
                    if (row, col) in self.game.valid_moves:
                        # Create a transparent surface for highlighting
                        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                        s.fill(HIGHLIGHT_COLOR)
                        self.window.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    def draw_pieces(self):
        """Draw all pieces on the board."""
        board = self.game.get_board().board
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board[row][col]
                if piece != 0:
                    # Draw piece
                    color = RED if piece.color == PLAYER_ONE else BLUE
                    pygame.draw.circle(self.window, color, 
                                      (piece.x, piece.y), PIECE_RADIUS)
                    # Draw king crown
                    if piece.king:
                        crown_color = WHITE if piece.color == PLAYER_ONE else YELLOW
                        pygame.draw.circle(self.window, crown_color, 
                                          (piece.x, piece.y), CROWN_RADIUS)
                        pygame.draw.circle(self.window, BLACK, 
                                          (piece.x, piece.y), CROWN_RADIUS, 2)
                    # Highlight selected piece
                    if piece == self.game.selected:
                        pygame.draw.circle(self.window, GREEN, 
                                          (piece.x, piece.y), PIECE_RADIUS + 3, 3)
    def draw_status(self):
        """Draw game status information."""
        # Draw turn indicator
        turn_text = "Red's Turn" if self.game.get_turn() == PLAYER_ONE else "Blue's Turn"
        turn_color = RED if self.game.get_turn() == PLAYER_ONE else BLUE
        turn_surface = self.font.render(turn_text, True, turn_color)
        self.window.blit(turn_surface, (10, WINDOW_HEIGHT - 90))
        # Draw instructions
        instructions = [
            "Instructions:",
            "Click on a piece to select it",
            "Click on a highlighted square to move",
            "Press R to reset the game",
            "Press ESC to quit"
        ]
        for i, line in enumerate(instructions):
            text_surface = self.small_font.render(line, True, WHITE)
            self.window.blit(text_surface, (10, WINDOW_HEIGHT - 70 + i * 20))
    def draw_game_over(self):
        """Draw game over screen."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with transparency
        self.window.blit(overlay, (0, 0))
        # Draw winner text
        winner_text = "Red Wins!" if self.game.get_winner() == PLAYER_ONE else "Blue Wins!"
        winner_color = RED if self.game.get_winner() == PLAYER_ONE else BLUE
        winner_surface = self.font.render(winner_text, True, winner_color)
        winner_rect = winner_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        self.window.blit(winner_surface, winner_rect)
        # Draw restart prompt
        restart_surface = self.small_font.render("Press R to restart or ESC to quit", True, WHITE)
        restart_rect = restart_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10))
        self.window.blit(restart_surface, restart_rect)