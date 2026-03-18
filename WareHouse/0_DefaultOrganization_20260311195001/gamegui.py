'''
gamegui.py
Pygame-based graphical user interface for the Checkers game.
'''
import pygame
class GameGUI:
    """Handles the graphical user interface for Checkers."""
    def __init__(self, game):
        """
        Initialize the GUI.
        Args:
            game (CheckersGame): The game instance to visualize
        """
        self.game = game
        # Initialize Pygame display
        self.screen_width = 800
        self.screen_height = 700  # Extra space for status display
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Checkers Game")
        # Colors
        self.BOARD_COLOR1 = (240, 217, 181)  # Light squares
        self.BOARD_COLOR2 = (181, 136, 99)   # Dark squares
        self.RED_PIECE = (220, 20, 60)       # Red pieces
        self.WHITE_PIECE = (255, 250, 250)   # White pieces
        self.SELECTED_COLOR = (50, 205, 50)  # Green for selected
        self.VALID_MOVE_COLOR = (173, 216, 230)  # Light blue for valid moves
        self.TEXT_COLOR = (50, 50, 50)
        self.BACKGROUND = (245, 245, 245)
        # Calculate board dimensions
        self.board_size = 600
        self.square_size = self.board_size // 8
        self.board_offset_x = (self.screen_width - self.board_size) // 2
        self.board_offset_y = 50
        # Fonts - using pygame's default font to avoid system font loading issues
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
    def draw(self):
        """Draw the entire game state."""
        # Clear screen
        self.screen.fill(self.BACKGROUND)
        # Draw title
        self.draw_title()
        # Draw board
        self.draw_board()
        # Draw pieces
        self.draw_pieces()
        # Draw selected piece and valid moves
        if self.game.selected_piece:
            self.draw_selected_piece()
            self.draw_valid_moves()
        # Draw game status
        self.draw_status()
        # Draw move notation prompt
        self.draw_move_prompt()
    def draw_title(self):
        """Draw the game title."""
        title = self.title_font.render("CHECKERS", True, self.TEXT_COLOR)
        title_rect = title.get_rect(center=(self.screen_width // 2, 20))
        self.screen.blit(title, title_rect)
    def draw_board(self):
        """Draw the checkers board."""
        for row in range(8):
            for col in range(8):
                # Calculate position
                x = self.board_offset_x + col * self.square_size
                y = self.board_offset_y + row * self.square_size
                # Alternate colors
                color = self.BOARD_COLOR1 if (row + col) % 2 == 0 else self.BOARD_COLOR2
                # Draw square
                pygame.draw.rect(self.screen, color, 
                               (x, y, self.square_size, self.square_size))
    def draw_pieces(self):
        """Draw all pieces on the board."""
        for row in range(8):
            for col in range(8):
                piece = self.game.board.get_piece(row, col)
                if piece:
                    self.draw_piece(piece)
    def draw_piece(self, piece):
        """Draw a single piece."""
        # Calculate position (center of square)
        x = self.board_offset_x + piece.col * self.square_size + self.square_size // 2
        y = self.board_offset_y + piece.row * self.square_size + self.square_size // 2
        # Draw piece circle
        color = self.RED_PIECE if piece.color == 'red' else self.WHITE_PIECE
        radius = self.square_size // 2 - 10
        pygame.draw.circle(self.screen, color, (x, y), radius)
        # Draw outline
        pygame.draw.circle(self.screen, (0, 0, 0), (x, y), radius, 2)
        # Draw king crown if piece is a king
        if piece.is_king:
            king_color = (255, 215, 0)  # Gold color for king
            crown_radius = radius // 2
            pygame.draw.circle(self.screen, king_color, (x, y), crown_radius)
            pygame.draw.circle(self.screen, (0, 0, 0), (x, y), crown_radius, 1)
    def draw_selected_piece(self):
        """Highlight the selected piece."""
        piece = self.game.selected_piece
        if piece:
            # Draw highlight around selected piece
            x = self.board_offset_x + piece.col * self.square_size
            y = self.board_offset_y + piece.row * self.square_size
            pygame.draw.rect(self.screen, self.SELECTED_COLOR,
                           (x, y, self.square_size, self.square_size), 4)
    def draw_valid_moves(self):
        """Highlight valid move positions."""
        for move in self.game.valid_moves:
            row, col = move
            x = self.board_offset_x + col * self.square_size
            y = self.board_offset_y + row * self.square_size
            # Draw semi-transparent overlay
            s = pygame.Surface((self.square_size, self.square_size), pygame.SRCALPHA)
            s.fill((*self.VALID_MOVE_COLOR, 128))  # RGBA with alpha
            self.screen.blit(s, (x, y))
            # Draw outline
            pygame.draw.rect(self.screen, self.VALID_MOVE_COLOR,
                           (x, y, self.square_size, self.square_size), 2)
    def draw_status(self):
        """Draw current game status."""
        status = self.game.get_game_state()
        status_text = self.font.render(status, True, self.TEXT_COLOR)
        status_rect = status_text.get_rect(center=(self.screen_width // 2, 670))
        self.screen.blit(status_text, status_rect)
    def draw_move_prompt(self):
        """Draw move notation prompt."""
        prompt = "Click on a piece, then click on a highlighted square to move"
        prompt_text = self.font.render(prompt, True, (100, 100, 100))
        prompt_rect = prompt_text.get_rect(center=(self.screen_width // 2, 650))
        self.screen.blit(prompt_text, prompt_rect)
    def handle_click(self, pos):
        """Handle mouse click events."""
        if self.game.game_over:
            return
        # Convert screen coordinates to board coordinates
        x, y = pos
        col = (x - self.board_offset_x) // self.square_size
        row = (y - self.board_offset_y) // self.square_size
        # Check if click is within board bounds
        if 0 <= row < 8 and 0 <= col < 8:
            if self.game.selected_piece:
                # Try to make a move
                success, captured = self.game.make_move(row, col)
                if success:
                    # Print move notation
                    piece = self.game.selected_piece
                    if piece:  # Piece might have been deselected after move
                        notation = self.game.get_move_notation(
                            piece.row, piece.col, row, col
                        )
                        print(f"Move: {notation}")
                        if captured:
                            print(f"Captured piece at {captured}")
            else:
                # Try to select a piece
                self.game.select_piece(row, col)