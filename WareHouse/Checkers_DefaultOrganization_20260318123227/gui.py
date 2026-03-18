'''
Graphical user interface for the Checkers game using Pygame.
Handles visualization and user interaction.
'''
import pygame
import sys
class GameGUI:
    """Pygame-based GUI for the Checkers game."""
    def __init__(self, game):
        """
        Initialize the GUI.
        Args:
            game: CheckersGame instance
        """
        self.game = game
        self.WIDTH = 800
        self.HEIGHT = 800
        self.SQUARE_SIZE = self.WIDTH // 8
        # Colors
        self.BROWN = (139, 69, 19)
        self.BEIGE = (245, 222, 179)
        self.RED = (255, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GREEN = (0, 255, 0)
        self.GRAY = (128, 128, 128)
        # Initialize Pygame display
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Checkers Game")
        # Font for text with fallback to handle PyGame font initialization issues
        try:
            self.font = pygame.font.SysFont('Arial', 24)
            self.big_font = pygame.font.SysFont('Arial', 48)
        except Exception:
            # Fallback to default PyGame fonts if system font fails
            self.font = pygame.font.Font(None, 24)
            self.big_font = pygame.font.Font(None, 48)
    def draw_board(self):
        """Draw the checkers board."""
        for row in range(8):
            for col in range(8):
                # Alternate square colors
                color = self.BEIGE if (row + col) % 2 == 0 else self.BROWN
                pygame.draw.rect(self.screen, color, 
                               (col * self.SQUARE_SIZE, row * self.SQUARE_SIZE,
                                self.SQUARE_SIZE, self.SQUARE_SIZE))
    def draw_pieces(self):
        """Draw all pieces on the board."""
        board = self.game.get_board().board
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece:
                    # Draw piece circle
                    color = self.RED if piece.color == 'red' else self.WHITE
                    pygame.draw.circle(self.screen, color,
                                     (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                      row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                      self.SQUARE_SIZE // 2 - 10)
                    # Draw black outline
                    pygame.draw.circle(self.screen, self.BLACK,
                                     (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                      row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                      self.SQUARE_SIZE // 2 - 10, 2)
                    # Draw crown for kings
                    if piece.is_king:
                        pygame.draw.circle(self.screen, self.GRAY,
                                         (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                          row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                          self.SQUARE_SIZE // 4)
    def draw_selection(self):
        """Highlight selected piece and valid moves."""
        selected = self.game.get_selected()
        valid_moves = self.game.get_valid_moves()
        if selected:
            # Highlight selected piece
            pygame.draw.rect(self.screen, self.GREEN,
                           (selected.col * self.SQUARE_SIZE,
                            selected.row * self.SQUARE_SIZE,
                            self.SQUARE_SIZE, self.SQUARE_SIZE), 3)
            # Highlight valid moves
            for move in valid_moves:
                row, col = move
                pygame.draw.circle(self.screen, self.GREEN,
                                 (col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2,
                                  row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2),
                                  10)
    def draw_status(self):
        """Draw game status information."""
        # Current turn
        turn = self.game.get_turn()
        turn_text = f"Current Turn: {turn.capitalize()}"
        turn_surface = self.font.render(turn_text, True, self.BLACK)
        self.screen.blit(turn_surface, (10, 10))
        # Piece counts
        board = self.game.get_board()
        red_count = f"Red: {board.red_left} ({board.red_kings} kings)"
        white_count = f"White: {board.white_left} ({board.white_kings} kings)"
        red_surface = self.font.render(red_count, True, self.RED)
        white_surface = self.font.render(white_count, True, self.BLACK)
        self.screen.blit(red_surface, (10, 40))
        self.screen.blit(white_surface, (10, 70))
        # Game over message
        if self.game.is_game_over():
            winner = self.game.get_winner()
            game_over_text = f"Game Over! {winner} Wins!"
            game_over_surface = self.big_font.render(game_over_text, True, self.GREEN)
            # Center the text
            text_rect = game_over_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(game_over_surface, text_rect)
            # Restart instruction
            restart_text = "Press R to restart or ESC to quit"
            restart_surface = self.font.render(restart_text, True, self.BLACK)
            restart_rect = restart_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2 + 50))
            self.screen.blit(restart_surface, restart_rect)
    def draw_move_notation(self):
        """Draw move notation (row, col) on each square."""
        for row in range(8):
            for col in range(8):
                notation = f"{row},{col}"
                # Use a small font for notation
                try:
                    notation_font = pygame.font.SysFont('Arial', 12)
                except Exception:
                    notation_font = pygame.font.Font(None, 12)
                notation_surface = notation_font.render(notation, True, self.GRAY)
                self.screen.blit(notation_surface,
                               (col * self.SQUARE_SIZE + 5, row * self.SQUARE_SIZE + 5))
    def get_row_col_from_pos(self, pos):
        """Convert mouse position to board coordinates."""
        x, y = pos
        row = y // self.SQUARE_SIZE
        col = x // self.SQUARE_SIZE
        return row, col
    def show_move_prompt(self):
        """Show text input for move notation."""
        # This is a simplified version - in a full implementation,
        # you would use pygame's text input functionality
        prompt_text = "Enter move (e.g., '2,1 to 3,2'): Click pieces to move"
        prompt_surface = self.font.render(prompt_text, True, self.BLACK)
        self.screen.blit(prompt_surface, (10, self.HEIGHT - 30))
    def restart_game(self):
        """Restart the game."""
        # Use the existing game instance's reset method instead of importing
        self.game.reset()
    def run(self):
        """Main game loop."""
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and self.game.is_game_over():
                        self.restart_game()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.game.is_game_over():
                        pos = pygame.mouse.get_pos()
                        row, col = self.get_row_col_from_pos(pos)
                        if 0 <= row < 8 and 0 <= col < 8:
                            self.game.select(row, col)
            # Draw everything
            self.screen.fill((255, 255, 255))
            self.draw_board()
            self.draw_pieces()
            self.draw_selection()
            self.draw_status()
            self.draw_move_notation()
            self.show_move_prompt()
            pygame.display.flip()
        pygame.quit()
        sys.exit()