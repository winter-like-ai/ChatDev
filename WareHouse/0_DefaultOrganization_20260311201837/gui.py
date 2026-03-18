'''
gui.py
Pygame-based graphical user interface for the Checkers game.
Handles rendering and user input.
'''
import pygame
import sys
class GUI:
    """Graphical user interface for the Checkers game."""
    def __init__(self, game):
        """
        Initialize the GUI.
        Args:
            game: Game instance to display and control
        """
        self.game = game
        self.WIDTH = 800
        self.HEIGHT = 800
        self.SQUARE_SIZE = self.WIDTH // 8
        # Initialize Pygame window
        self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Checkers Game")
        # Colors
        self.BROWN = (139, 69, 19)
        self.BEIGE = (245, 222, 179)
        self.RED = (255, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.GRAY = (128, 128, 128)
        # Font - using default font to avoid Windows system font enumeration issue
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 48)
    def draw(self):
        """Draw the entire game state."""
        self.window.fill(self.BLACK)
        self.draw_board()
        self.draw_pieces()
        self.draw_turn_indicator()
        self.draw_selected()
        self.draw_valid_moves()
    def draw_board(self):
        """Draw the checkers board."""
        for row in range(8):
            for col in range(8):
                color = self.BEIGE if (row + col) % 2 == 0 else self.BROWN
                pygame.draw.rect(self.window, color, 
                                (col * self.SQUARE_SIZE, 
                                 row * self.SQUARE_SIZE, 
                                 self.SQUARE_SIZE, 
                                 self.SQUARE_SIZE))
    def draw_pieces(self):
        """Draw all pieces on the board."""
        board = self.game.get_board()
        for row in range(8):
            for col in range(8):
                piece = board.get_piece(row, col)
                if piece:
                    # Draw piece circle
                    color = self.RED if piece.color == 'red' else self.WHITE
                    pygame.draw.circle(self.window, color, 
                                      (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                       row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                      self.SQUARE_SIZE // 2 - 10)
                    # Draw black outline
                    pygame.draw.circle(self.window, self.BLACK,
                                      (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                       row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                      self.SQUARE_SIZE // 2 - 10, 2)
                    # Draw crown for kings
                    if piece.king:
                        pygame.draw.circle(self.window, self.GRAY,
                                          (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                           row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                          self.SQUARE_SIZE // 4)
    def draw_selected(self):
        """Highlight the selected piece."""
        if self.game.selected:
            piece = self.game.selected
            pygame.draw.rect(self.window, self.GREEN,
                            (piece.col * self.SQUARE_SIZE,
                             piece.row * self.SQUARE_SIZE,
                             self.SQUARE_SIZE, self.SQUARE_SIZE), 4)
    def draw_valid_moves(self):
        """Highlight valid move destinations."""
        for move in self.game.valid_moves:
            row, col = move
            pygame.draw.circle(self.window, self.GREEN,
                              (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                               row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                              15)
    def draw_turn_indicator(self):
        """Display whose turn it is."""
        turn_text = f"Turn: {self.game.turn.capitalize()}"
        text_surface = self.font.render(turn_text, True, self.WHITE)
        self.window.blit(text_surface, (10, 10))
        # Display piece counts
        board = self.game.get_board()
        red_count = f"Red: {board.red_left}"
        white_count = f"White: {board.white_left}"
        red_surface = self.font.render(red_count, True, self.RED)
        white_surface = self.font.render(white_count, True, self.WHITE)
        self.window.blit(red_surface, (self.WIDTH - 150, 10))
        self.window.blit(white_surface, (self.WIDTH - 150, 40))
    def display_game_over(self):
        """Display game over message."""
        if self.game.winner:
            message = f"{self.game.winner.capitalize()} Wins!"
            text_surface = self.big_font.render(message, True, self.GREEN)
            text_rect = text_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            # Semi-transparent overlay
            overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.window.blit(overlay, (0, 0))
            self.window.blit(text_surface, text_rect)
            # Restart instruction
            restart_text = "Press R to restart or ESC to quit"
            restart_surface = self.font.render(restart_text, True, self.WHITE)
            restart_rect = restart_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 60))
            self.window.blit(restart_surface, restart_rect)
    def handle_click(self, pos):
        """Handle mouse click events."""
        if self.game.game_over:
            # Check for restart
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            return
        x, y = pos
        row = y // self.SQUARE_SIZE
        col = x // self.SQUARE_SIZE
        if 0 <= row < 8 and 0 <= col < 8:
            self.game.select(row, col)
    def restart_game(self):
        """Restart the game."""
        self.game.__init__()