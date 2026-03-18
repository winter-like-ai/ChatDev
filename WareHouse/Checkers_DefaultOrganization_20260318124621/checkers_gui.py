'''
Pygame-based graphical user interface for the Checkers game.
'''
import pygame
class CheckersGUI:
    def __init__(self, game):
        """
        Initialize the Checkers GUI.
        Args:
            game: Game instance
        """
        self.game = game
        self.WIDTH = 800
        self.HEIGHT = 800
        self.SQUARE_SIZE = self.WIDTH // 8
        self.PIECE_RADIUS = self.SQUARE_SIZE // 2 - 10
        self.CROWN_RADIUS = self.PIECE_RADIUS // 2
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.DARK_RED = (139, 0, 0)
        self.GRAY = (128, 128, 128)
        self.LIGHT_BROWN = (210, 180, 140)
        self.DARK_BROWN = (101, 67, 33)
        self.HIGHLIGHT = (255, 255, 0, 128)  # Semi-transparent yellow
        self.VALID_MOVE = (0, 255, 0, 128)   # Semi-transparent green
        # Initialize Pygame window
        self.window = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Checkers Game")
        # Font for text display
        self.font = pygame.font.SysFont('Arial', 24)
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
    def run(self):
        """Main game loop."""
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    row, col = self.get_row_col_from_mouse(pos)
                    self.handle_click(row, col)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game.reset()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            self.draw()
            pygame.display.update()
        pygame.quit()
    def get_row_col_from_mouse(self, pos):
        """
        Convert mouse position to board row and column.
        Args:
            pos: Mouse position (x, y)
        Returns:
            tuple: (row, column)
        """
        x, y = pos
        row = y // self.SQUARE_SIZE
        col = x // self.SQUARE_SIZE
        return row, col
    def handle_click(self, row, col):
        """
        Handle mouse click on the board.
        Args:
            row: Clicked row
            col: Clicked column
        """
        if self.game.is_game_over():
            return
        # Try to select a piece
        if not self.game.select_piece(row, col):
            # If piece is already selected, try to move it
            if self.game.selected_piece is not None:
                if self.game.move_piece(row, col):
                    # Move successful
                    pass
                else:
                    # Invalid move, try to select another piece
                    self.game.select_piece(row, col)
    def draw(self):
        """Draw the entire game state."""
        self.window.fill(self.WHITE)
        self.draw_board()
        self.draw_pieces()
        self.draw_highlights()
        self.draw_game_info()
        if self.game.is_game_over():
            self.draw_game_over()
    def draw_board(self):
        """Draw the checkers board."""
        for row in range(8):
            for col in range(8):
                # Alternate square colors
                if (row + col) % 2 == 0:
                    color = self.LIGHT_BROWN
                else:
                    color = self.DARK_BROWN
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
                if piece != 0:
                    # Calculate center position
                    x = col * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                    y = row * self.SQUARE_SIZE + self.SQUARE_SIZE // 2
                    # Draw piece
                    color = self.RED if piece.color == 'red' else self.GRAY
                    pygame.draw.circle(self.window, color, (x, y), self.PIECE_RADIUS)
                    # Draw outline
                    outline_color = self.DARK_RED if piece.color == 'red' else self.BLACK
                    pygame.draw.circle(self.window, outline_color, (x, y), self.PIECE_RADIUS, 2)
                    # Draw crown for kings
                    if piece.king:
                        pygame.draw.circle(self.window, (255, 215, 0), (x, y), self.CROWN_RADIUS)
                        pygame.draw.circle(self.window, outline_color, (x, y), self.CROWN_RADIUS, 2)
    def draw_highlights(self):
        """Highlight selected piece and valid moves."""
        if self.game.selected_piece is not None:
            # Highlight selected piece
            row, col = self.game.selected_piece.row, self.game.selected_piece.col
            self.highlight_square(row, col, self.HIGHLIGHT)
            # Highlight valid moves
            for (move_row, move_col) in self.game.valid_moves.keys():
                self.highlight_square(move_row, move_col, self.VALID_MOVE)
    def highlight_square(self, row, col, color):
        """
        Highlight a square on the board.
        Args:
            row: Row to highlight
            col: Column to highlight
            color: Highlight color (with alpha)
        """
        # Create a surface with per-pixel alpha
        s = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(color)
        self.window.blit(s, (col * self.SQUARE_SIZE, row * self.SQUARE_SIZE))
    def draw_game_info(self):
        """Draw game information (current player, scores, instructions)."""
        # Draw title
        title = self.title_font.render("CHECKERS", True, self.BLACK)
        self.window.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 10))
        # Draw current player
        player = self.game.get_current_player()
        player_text = f"Current Player: {player.capitalize()}"
        player_surface = self.font.render(player_text, True, 
                                         self.RED if player == 'red' else self.BLACK)
        self.window.blit(player_surface, (20, 760))
        # Draw piece counts
        board = self.game.get_board()
        red_count = f"Red: {board.red_left} ({board.red_kings} kings)"
        black_count = f"Black: {board.black_left} ({board.black_kings} kings)"
        red_surface = self.font.render(red_count, True, self.RED)
        black_surface = self.font.render(black_count, True, self.BLACK)
        self.window.blit(red_surface, (self.WIDTH - 200, 760))
        self.window.blit(black_surface, (self.WIDTH - 200, 730))
        # Draw instructions
        instructions = [
            "Instructions:",
            "1. Click on a piece to select it",
            "2. Click on a highlighted square to move",
            "3. Captures are mandatory",
            "4. Press R to reset, ESC to quit"
        ]
        for i, text in enumerate(instructions):
            surface = self.font.render(text, True, self.BLACK)
            self.window.blit(surface, (20, 50 + i * 30))
    def draw_game_over(self):
        """Draw game over screen."""
        # Create semi-transparent overlay
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        self.window.blit(overlay, (0, 0))
        # Draw game over text
        winner = self.game.get_winner()
        game_over_text = self.title_font.render("GAME OVER", True, self.WHITE)
        winner_text = self.font.render(f"{winner.capitalize()} wins!", True, self.WHITE)
        restart_text = self.font.render("Press R to restart or ESC to quit", True, self.WHITE)
        self.window.blit(game_over_text, 
                        (self.WIDTH // 2 - game_over_text.get_width() // 2, 
                         self.HEIGHT // 2 - 60))
        self.window.blit(winner_text, 
                        (self.WIDTH // 2 - winner_text.get_width() // 2, 
                         self.HEIGHT // 2))
        self.window.blit(restart_text, 
                        (self.WIDTH // 2 - restart_text.get_width() // 2, 
                         self.HEIGHT // 2 + 40))