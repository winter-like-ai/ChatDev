'''
GUI class for Checkers using Pygame.
Handles all graphical rendering and user input.
'''
import pygame
class GUI:
    """Graphical User Interface for Checkers game."""
    def __init__(self, game):
        """
        Initialize the GUI.
        Args:
            game: Game instance
        """
        self.game = game
        self.width = 800
        self.height = 800
        self.square_size = self.width // 8
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Checkers Game")
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.WHITE_PIECE = (200, 200, 200)
        self.RED_PIECE = (180, 0, 0)
        self.BEIGE = (245, 245, 220)
        self.BROWN = (139, 69, 19)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
    def draw(self):
        """Draw the entire game state."""
        self.window.fill(self.BLACK)
        self.draw_board()
        self.draw_pieces()
        self.draw_selection()
        self.draw_valid_moves()
        self.draw_turn_indicator()
    def draw_board(self):
        """Draw the 8x8 checkers board."""
        for row in range(8):
            for col in range(8):
                # Alternate colors
                if (row + col) % 2 == 0:
                    color = self.BEIGE
                else:
                    color = self.BROWN
                # Draw square
                pygame.draw.rect(self.window, color, 
                               (col * self.square_size, 
                                row * self.square_size,
                                self.square_size, 
                                self.square_size))
    def draw_pieces(self):
        """Draw all pieces on the board."""
        board = self.game.get_board().get_board_state()
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece:
                    # Draw piece
                    x = col * self.square_size + self.square_size // 2
                    y = row * self.square_size + self.square_size // 2
                    radius = self.square_size // 2 - 10
                    # Piece color
                    if piece.color == 'red':
                        color = self.RED_PIECE
                        outline = self.RED
                    else:
                        color = self.WHITE_PIECE
                        outline = self.WHITE
                    # Draw piece
                    pygame.draw.circle(self.window, outline, (x, y), radius + 2)
                    pygame.draw.circle(self.window, color, (x, y), radius)
                    # Draw king crown
                    if piece.king:
                        # Draw a smaller circle inside for king
                        pygame.draw.circle(self.window, self.YELLOW, (x, y), radius // 2)
                        # Draw K letter
                        font = pygame.font.SysFont('Arial', 20)
                        text = font.render('K', True, self.BLACK)
                        text_rect = text.get_rect(center=(x, y))
                        self.window.blit(text, text_rect)
    def draw_selection(self):
        """Highlight the selected piece."""
        selected_piece = self.game.get_selected_piece()
        if selected_piece:
            row, col = selected_piece.row, selected_piece.col
            x = col * self.square_size
            y = row * self.square_size
            # Draw selection rectangle
            pygame.draw.rect(self.window, self.GREEN, 
                           (x, y, self.square_size, self.square_size), 4)
    def draw_valid_moves(self):
        """Highlight valid moves for the selected piece."""
        valid_moves = self.game.get_valid_moves()
        for (row, col) in valid_moves.keys():
            x = col * self.square_size + self.square_size // 2
            y = row * self.square_size + self.square_size // 2
            radius = self.square_size // 8
            # Draw move indicator
            pygame.draw.circle(self.window, self.BLUE, (x, y), radius)
    def draw_turn_indicator(self):
        """Display whose turn it is."""
        turn = self.game.get_turn()
        font = pygame.font.SysFont('Arial', 24)
        if turn == 'red':
            text = font.render("Red's Turn", True, self.RED)
        else:
            text = font.render("White's Turn", True, self.WHITE)
        self.window.blit(text, (10, 10))
        # Draw piece counts
        board = self.game.get_board()
        red_text = font.render(f"Red: {board.red_left} ({board.red_kings}K)", True, self.RED)
        white_text = font.render(f"White: {board.white_left} ({board.white_kings}K)", True, self.WHITE)
        self.window.blit(red_text, (10, 40))
        self.window.blit(white_text, (10, 70))
    def display_winner(self):
        """Display the winner when game is over."""
        winner = self.game.winner
        font_large = pygame.font.SysFont('Arial', 48)
        font_small = pygame.font.SysFont('Arial', 24)
        if winner == 'red':
            text = font_large.render("Red Wins!", True, self.RED)
        else:
            text = font_large.render("White Wins!", True, self.WHITE)
        restart_text = font_small.render("Press R to Restart", True, self.YELLOW)
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.window.blit(overlay, (0, 0))
        # Draw winner text
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2 - 30))
        self.window.blit(text, text_rect)
        # Draw restart instruction
        restart_rect = restart_text.get_rect(center=(self.width // 2, self.height // 2 + 30))
        self.window.blit(restart_text, restart_rect)
    def handle_click(self, pos):
        """Handle mouse click events."""
        x, y = pos
        col = x // self.square_size
        row = y // self.square_size
        # Check if click is within board bounds
        if 0 <= row < 8 and 0 <= col < 8:
            # Check for restart if game is over
            if self.game.winner is not None:
                # Check for R key press (handled in main loop)
                return
            # Handle piece selection/move
            self.game.select(row, col)