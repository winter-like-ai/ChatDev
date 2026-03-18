'''
GUI class for rendering the Checkers game using Pygame.
Handles drawing and user input.
'''
import pygame
from constants import *
class GUI:
    def __init__(self, game):
        """
        Initialize GUI for Checkers game.
        Args:
            game: Game object containing game logic
        """
        self.game = game
        self.window_width = WIDTH + 300  # Extra space for info panel
        self.window_height = HEIGHT + 100
        pygame.init()
        self.win = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Checkers Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 36, bold=True)
        # Load images
        self.load_images()
    def load_images(self):
        """Load and scale game images."""
        # This would load images if we had them
        # For now, we'll create them programmatically in the Piece class
        pass
    def draw_board(self):
        """Draw the checkerboard."""
        self.win.fill(LIGHT_BROWN)
        # Draw squares
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    pygame.draw.rect(self.win, DARK_BROWN, 
                                    (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                     SQUARE_SIZE, SQUARE_SIZE))
        # Draw grid lines
        for i in range(ROWS + 1):
            pygame.draw.line(self.win, BLACK, (0, i * SQUARE_SIZE), 
                            (WIDTH, i * SQUARE_SIZE), 2)
            pygame.draw.line(self.win, BLACK, (i * SQUARE_SIZE, 0), 
                            (i * SQUARE_SIZE, HEIGHT), 2)
        # Draw coordinates
        for i in range(ROWS):
            # Row numbers (left side)
            text = self.font.render(str(i), True, BLACK)
            self.win.blit(text, (5, i * SQUARE_SIZE + SQUARE_SIZE // 2 - 10))
            # Row numbers (right side)
            self.win.blit(text, (WIDTH - 25, i * SQUARE_SIZE + SQUARE_SIZE // 2 - 10))
        for i in range(COLS):
            # Column letters (top)
            text = self.font.render(chr(65 + i), True, BLACK)
            self.win.blit(text, (i * SQUARE_SIZE + SQUARE_SIZE // 2 - 10, 5))
            # Column letters (bottom)
            self.win.blit(text, (i * SQUARE_SIZE + SQUARE_SIZE // 2 - 10, HEIGHT - 25))
    def draw_pieces(self):
        """Draw all pieces on the board."""
        board = self.game.get_board()
        for row in range(ROWS):
            for col in range(COLS):
                piece = board[row][col]
                if piece:
                    piece.draw(self.win)
    def draw_selection(self):
        """Draw highlight for selected piece and valid moves."""
        piece = self.game.get_selected_piece()
        if piece:
            # Highlight selected piece
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT)
            self.win.blit(s, (piece.col * SQUARE_SIZE, piece.row * SQUARE_SIZE))
            # Highlight valid moves
            valid_moves = self.game.get_valid_moves()
            for move in valid_moves:
                row, col = move
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                s.fill((0, 255, 0, 100))  # Green with transparency
                self.win.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    def draw_info_panel(self):
        """Draw game information panel on the right side."""
        panel_x = WIDTH + 20
        # Draw panel background
        pygame.draw.rect(self.win, GRAY, (panel_x - 10, 0, 280, self.window_height))
        # Game title
        title = self.big_font.render("CHECKERS", True, BLACK)
        self.win.blit(title, (panel_x + 50, 20))
        # Current turn
        turn = self.game.get_turn()
        turn_text = self.font.render(f"Current Turn:", True, BLACK)
        self.win.blit(turn_text, (panel_x, 80))
        turn_color = RED if turn == 'red' else BLUE
        pygame.draw.circle(self.win, turn_color, (panel_x + 150, 95), 20)
        pygame.draw.circle(self.win, WHITE, (panel_x + 150, 95), 20, 2)
        # Piece counts
        red_count = self.font.render(f"Red Pieces: {self.game.red_left}", True, RED)
        blue_count = self.font.render(f"Blue Pieces: {self.game.blue_left}", True, BLUE)
        self.win.blit(red_count, (panel_x, 130))
        self.win.blit(blue_count, (panel_x, 160))
        # King counts
        red_kings = self.font.render(f"Red Kings: {self.game.red_kings}", True, RED)
        blue_kings = self.font.render(f"Blue Kings: {self.game.blue_kings}", True, BLUE)
        self.win.blit(red_kings, (panel_x, 190))
        self.win.blit(blue_kings, (panel_x, 220))
        # Instructions
        instructions = [
            "INSTRUCTIONS:",
            "1. Click on a piece to select it",
            "2. Click on a highlighted square",
            "   to move",
            "3. Red moves first",
            "4. Pieces move diagonally",
            "5. Capture by jumping over",
            "   opponent's pieces",
            "6. Reach opposite end to",
            "   become a King",
            "7. Kings can move backwards"
        ]
        for i, line in enumerate(instructions):
            text = self.font.render(line, True, BLACK)
            self.win.blit(text, (panel_x, 270 + i * 30))
        # Move notation
        notation = self.font.render("Move Notation:", True, BLACK)
        self.win.blit(notation, (panel_x, 500))
        notation_ex = self.font.render("e.g., A3-B4", True, BLACK)
        self.win.blit(notation_ex, (panel_x, 530))
        # Current move display
        selected = self.game.get_selected_piece()
        if selected:
            move_from = f"{chr(65 + selected.col)}{selected.row}"
            move_text = self.font.render(f"From: {move_from}", True, BLACK)
            self.win.blit(move_text, (panel_x, 570))
    def draw_winner(self):
        """Draw winner announcement."""
        winner = self.game.winner()
        if winner:
            # Semi-transparent overlay
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))
            self.win.blit(s, (0, 0))
            # Winner text
            winner_text = self.big_font.render(f"{winner.upper()} WINS!", True, WHITE)
            text_rect = winner_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            self.win.blit(winner_text, text_rect)
            # Restart instruction
            restart_text = self.font.render("Press R to restart or ESC to quit", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            self.win.blit(restart_text, restart_rect)
    def get_row_col_from_pos(self, pos):
        """
        Convert mouse position to board coordinates.
        Args:
            pos: (x, y) mouse position
        Returns:
            (row, col) board coordinates or (None, None) if outside board
        """
        x, y = pos
        if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
            return None, None
        row = y // SQUARE_SIZE
        col = x // SQUARE_SIZE
        return row, col
    def run(self):
        """Main game loop."""
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r:
                        # Restart game
                        from game import Game
                        self.game = Game()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if not self.game.winner():  # Only process moves if game not ended
                        pos = pygame.mouse.get_pos()
                        row, col = self.get_row_col_from_pos(pos)
                        if row is not None and col is not None:
                            self.game.select(row, col)
            # Draw everything
            self.draw_board()
            self.draw_pieces()
            self.draw_selection()
            self.draw_info_panel()
            # Check for winner
            if self.game.winner():
                self.draw_winner()
            pygame.display.update()
        pygame.quit()