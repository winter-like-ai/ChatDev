'''
gui.py
Pygame-based graphical user interface for the Checkers game.
Handles visualization and user interaction.
'''
import pygame
import pygame.math  # Added import for Vector2
class GameGUI:
    """Handles the graphical interface for the Checkers game."""
    def __init__(self, game):
        """
        Initialize the GUI.
        Args:
            game (CheckersGame): The game logic controller
        """
        self.game = game
        self.square_size = 80
        self.board_size = self.square_size * 8
        self.piece_radius = self.square_size // 2 - 10
        # Initialize Pygame window
        self.screen = pygame.display.set_mode((self.board_size, self.board_size + 50))
        pygame.display.set_caption("Checkers Game")
        # Colors
        self.colors = {
            'light': (240, 217, 181),
            'dark': (181, 136, 99),
            'red': (220, 20, 60),
            'black': (40, 40, 40),
            'highlight': (50, 205, 50),
            'selected': (255, 215, 0),
            'king_highlight': (255, 255, 0),
            'text': (255, 255, 255),
            'status_bg': (50, 50, 50)
        }
        # Fonts - Use Font(None, size) for cross-platform compatibility
        try:
            # Try to use system font first
            self.font = pygame.font.SysFont('Arial', 24)
            self.small_font = pygame.font.SysFont('Arial', 18)
        except (TypeError, Exception):
            # Fallback to default font if system font fails
            self.font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
    def draw(self):
        """Draw the entire game interface."""
        self.screen.fill((50, 50, 50))
        self.draw_board()
        self.draw_pieces()
        self.draw_status()
        if self.game.game_over:
            self.draw_game_over()
    def draw_board(self):
        """Draw the checkers board."""
        for row in range(8):
            for col in range(8):
                # Determine square color
                if (row + col) % 2 == 0:
                    color = self.colors['light']
                else:
                    color = self.colors['dark']
                # Highlight selected piece
                if (self.game.selected_piece and 
                    self.game.selected_piece.row == row and 
                    self.game.selected_piece.col == col):
                    color = self.colors['selected']
                # Draw square
                rect = pygame.Rect(
                    col * self.square_size,
                    row * self.square_size,
                    self.square_size,
                    self.square_size
                )
                pygame.draw.rect(self.screen, color, rect)
                # Draw valid move highlights
                if self.game.selected_piece:
                    for move_row, move_col in self.game.valid_moves:
                        if move_row == row and move_col == col:
                            highlight_rect = pygame.Rect(
                                col * self.square_size + 5,
                                row * self.square_size + 5,
                                self.square_size - 10,
                                self.square_size - 10
                            )
                            pygame.draw.rect(self.screen, self.colors['highlight'], highlight_rect, 3)
    def draw_pieces(self):
        """Draw all pieces on the board."""
        for row in range(8):
            for col in range(8):
                piece = self.game.board.get_piece(row, col)
                if piece:
                    self.draw_piece(piece)
    def draw_piece(self, piece):
        """Draw a single piece."""
        x = piece.col * self.square_size + self.square_size // 2
        y = piece.row * self.square_size + self.square_size // 2
        # Draw piece base
        color = self.colors[piece.color]
        pygame.draw.circle(self.screen, color, (x, y), self.piece_radius)
        # Draw piece border
        pygame.draw.circle(self.screen, (255, 255, 255), (x, y), self.piece_radius, 2)
        # Draw king crown
        if piece.is_king:
            crown_color = self.colors['king_highlight']
            # Draw crown symbol (simplified as a smaller circle inside)
            pygame.draw.circle(self.screen, crown_color, (x, y), self.piece_radius // 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (x, y), self.piece_radius // 2, 2)
            # Draw crown points
            for i in range(4):
                angle = i * 90
                px = x + int((self.piece_radius // 2) * 0.7 * pygame.math.Vector2(1, 0).rotate(angle).x)
                py = y + int((self.piece_radius // 2) * 0.7 * pygame.math.Vector2(1, 0).rotate(angle).y)
                pygame.draw.circle(self.screen, crown_color, (px, py), 5)
    def draw_status(self):
        """Draw game status information."""
        # Status bar background
        status_rect = pygame.Rect(0, self.board_size, self.board_size, 50)
        pygame.draw.rect(self.screen, self.colors['status_bg'], status_rect)
        # Current player
        player_text = self.game.get_game_state()
        player_surface = self.font.render(player_text, True, self.colors['text'])
        self.screen.blit(player_surface, (10, self.board_size + 10))
        # Instructions
        instructions = "Click piece to select, then click destination. Red starts."
        instr_surface = self.small_font.render(instructions, True, self.colors['text'])
        self.screen.blit(instr_surface, (10, self.board_size + 35))
        # Move notation (if a move was made)
        if hasattr(self, 'last_move_notation'):
            move_text = f"Last move: {self.last_move_notation}"
            move_surface = self.small_font.render(move_text, True, self.colors['text'])
            move_rect = move_surface.get_rect(right=self.board_size - 10, centery=self.board_size + 25)
            self.screen.blit(move_surface, move_rect)
    def draw_game_over(self):
        """Draw game over overlay."""
        overlay = pygame.Surface((self.board_size, self.board_size), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))
        # Game over text
        game_over_text = self.font.render("GAME OVER", True, (255, 255, 255))
        winner_text = self.font.render(f"Winner: {self.game.winner.capitalize()}", True, (255, 255, 255))
        restart_text = self.small_font.render("Close and restart to play again", True, (255, 255, 255))
        # Center text
        game_over_rect = game_over_text.get_rect(center=(self.board_size // 2, self.board_size // 2 - 40))
        winner_rect = winner_text.get_rect(center=(self.board_size // 2, self.board_size // 2))
        restart_rect = restart_text.get_rect(center=(self.board_size // 2, self.board_size // 2 + 40))
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(winner_text, winner_rect)
        self.screen.blit(restart_text, restart_rect)
    def handle_click(self, pos):
        """
        Handle mouse click events.
        Args:
            pos (tuple): (x, y) mouse position
        """
        if self.game.game_over:
            return
        x, y = pos
        # Check if click is on status bar
        if y >= self.board_size:
            return
        # Convert pixel coordinates to board coordinates
        row = y // self.square_size
        col = x // self.square_size
        if not self.game.selected_piece:
            # Try to select a piece
            if self.game.select_piece(row, col):
                print(f"Selected piece at ({row}, {col})")
        else:
            # Try to move selected piece
            from_pos = (self.game.selected_piece.row, self.game.selected_piece.col)
            if self.game.make_move(row, col):
                # Store move notation for display
                self.last_move_notation = self.game.get_move_notation(from_pos, (row, col))
                print(f"Move: {self.last_move_notation}")
            else:
                # If move failed, try to select a different piece
                self.game.select_piece(row, col)