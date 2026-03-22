'''
Graphical User Interface for the Checkers game using Pygame.
Handles visualization and user interaction.
'''
import pygame
class GameGUI:
    """Manages the graphical interface for the Checkers game."""
    def __init__(self, game):
        """
        Initialize the GUI.
        Args:
            game: CheckersGame instance
        """
        self.game = game
        self.board = game.board
        # Pygame setup
        self.WIDTH, self.HEIGHT = 800, 800
        self.ROWS, self.COLS = 8, 8
        self.SQUARE_SIZE = self.WIDTH // self.COLS
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.LIGHT_RED = (255, 100, 100)
        self.BEIGE = (245, 245, 220)
        self.BROWN = (139, 69, 19)
        self.LIGHT_BROWN = (222, 184, 135)
        self.GREEN = (0, 255, 0)
        self.GRAY = (128, 128, 128)
        self.YELLOW = (255, 255, 0)
        # Initialize Pygame window
        self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Checkers Game")
        self.clock = pygame.time.Clock()
        # Font for text - use default font to avoid system font issues
        try:
            self.font = pygame.font.SysFont('Arial', 24)
            self.big_font = pygame.font.SysFont('Arial', 48)
        except Exception:
            # Fallback to default font if system font fails
            self.font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 48)
    def draw(self):
        """Draw the entire game state."""
        self.window.fill(self.BLACK)
        self.draw_board()
        self.draw_pieces()
        self.draw_ui()
    def draw_board(self):
        """Draw the checkers board."""
        for row in range(self.ROWS):
            for col in range(self.COLS):
                # Alternate square colors
                if (row + col) % 2 == 0:
                    color = self.LIGHT_BROWN
                else:
                    color = self.BROWN
                # Highlight selected piece
                if self.game.selected:
                    if (row, col) == (self.game.selected.row, self.game.selected.col):
                        color = self.GREEN
                # Highlight valid moves
                if (row, col) in self.game.valid_moves:
                    color = self.YELLOW
                pygame.draw.rect(self.window, color, 
                               (col * self.SQUARE_SIZE, 
                                row * self.SQUARE_SIZE, 
                                self.SQUARE_SIZE, 
                                self.SQUARE_SIZE))
    def draw_pieces(self):
        """Draw all pieces on the board."""
        for row in range(self.ROWS):
            for col in range(self.COLS):
                piece = self.board.get_piece(row, col)
                if piece is not None:
                    # Draw piece circle
                    color = self.LIGHT_RED if piece.color == 'red' else self.WHITE
                    pygame.draw.circle(self.window, color, 
                                     (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                      row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                      self.SQUARE_SIZE // 2 - 10)
                    # Draw piece border
                    border_color = self.RED if piece.color == 'red' else self.GRAY
                    pygame.draw.circle(self.window, border_color,
                                     (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                      row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                      self.SQUARE_SIZE // 2 - 10, 3)
                    # Draw king crown
                    if piece.king:
                        crown_color = self.YELLOW
                        pygame.draw.circle(self.window, crown_color,
                                         (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                          row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                          self.SQUARE_SIZE // 4)
    def draw_ui(self):
        """Draw user interface elements."""
        # Draw turn indicator
        turn_text = f"Turn: {'Red' if self.game.turn == 'red' else 'White'}"
        turn_surface = self.font.render(turn_text, True, self.WHITE)
        self.window.blit(turn_surface, (10, 10))
        # Draw piece counts
        red_text = f"Red: {self.board.red_left} ({self.board.red_kings} kings)"
        white_text = f"White: {self.board.white_left} ({self.board.white_kings} kings)"
        red_surface = self.font.render(red_text, True, self.LIGHT_RED)
        white_surface = self.font.render(white_text, True, self.WHITE)
        self.window.blit(red_surface, (10, 40))
        self.window.blit(white_surface, (10, 70))
        # Draw capture warning if applicable
        if self.game.must_capture:
            warning_text = "MUST CAPTURE! Select a capture move."
            warning_surface = self.font.render(warning_text, True, self.YELLOW)
            self.window.blit(warning_surface, (10, 100))
        # Draw move notation
        if self.game.selected:
            notation = f"Selected: ({self.game.selected.row},{self.game.selected.col})"
            notation_surface = self.font.render(notation, True, self.GREEN)
            self.window.blit(notation_surface, (10, 130))
    def display_game_over(self):
        """Display game over screen."""
        if self.game.winner:
            # Semi-transparent overlay
            overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.window.blit(overlay, (0, 0))
            # Game over text
            winner_text = f"{self.game.winner.capitalize()} Wins!"
            game_over_text = "Game Over!"
            restart_text = "Click to restart"
            winner_surface = self.big_font.render(winner_text, True, self.YELLOW)
            game_over_surface = self.big_font.render(game_over_text, True, self.WHITE)
            restart_surface = self.font.render(restart_text, True, self.GREEN)
            # Center text
            self.window.blit(winner_surface, 
                           (self.WIDTH // 2 - winner_surface.get_width() // 2, 
                            self.HEIGHT // 2 - 100))
            self.window.blit(game_over_surface,
                           (self.WIDTH // 2 - game_over_surface.get_width() // 2,
                            self.HEIGHT // 2 - 40))
            self.window.blit(restart_surface,
                           (self.WIDTH // 2 - restart_surface.get_width() // 2,
                            self.HEIGHT // 2 + 40))
    def handle_click(self, pos):
        """Handle mouse click events."""
        if self.game.game_over:
            # Restart game on click when game is over
            self.game = CheckersGame()
            self.board = self.game.board
            return
        x, y = pos
        row = y // self.SQUARE_SIZE
        col = x // self.SQUARE_SIZE
        if 0 <= row < 8 and 0 <= col < 8:
            # Try to select or move
            if not self.game.select(row, col):
                # If selection failed, try to move
                if self.game.selected:
                    self.game.move(row, col)
    def get_row_col_from_pos(self, pos):
        """Convert pixel position to board coordinates."""
        x, y = pos
        row = y // self.SQUARE_SIZE
        col = x // self.SQUARE_SIZE
        return row, col