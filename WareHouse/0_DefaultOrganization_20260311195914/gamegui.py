'''
gui.py - Pygame GUI for the Checkers game
Handles visualization and user interaction
'''
import pygame
import sys
class GameGUI:
    """Pygame-based GUI for the Checkers game"""
    def __init__(self, game):
        """Initialize the GUI"""
        self.game = game
        self.square_size = 80
        self.board_size = self.square_size * 8
        self.window_size = self.board_size + 300  # Extra space for sidebar
        # Initialize Pygame window
        self.screen = pygame.display.set_mode((self.window_size, self.board_size))
        pygame.display.set_caption("Checkers Game")
        # Colors
        self.colors = {
            'light': (240, 217, 181),
            'dark': (181, 136, 99),
            'red': (220, 20, 60),
            'black': (50, 50, 50),
            'red_king': (255, 100, 100),
            'black_king': (100, 100, 100),
            'highlight': (255, 255, 0),
            'valid_move': (144, 238, 144),
            'sidebar': (245, 245, 220),
            'text': (50, 50, 50),
            'button': (100, 149, 237),
            'button_hover': (65, 105, 225)
        }
        # Fonts
        self.font = pygame.font.SysFont('Arial', 24)
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        # Initialize game
        self.game.initialize_game()
        # Button for reset
        self.reset_button = pygame.Rect(self.board_size + 50, 400, 200, 50)
    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.handle_click(event.pos)
            self.draw()
            pygame.display.flip()
            clock.tick(60)
    def handle_click(self, pos):
        """Handle mouse click events"""
        x, y = pos
        # Check if reset button was clicked
        if self.reset_button.collidepoint(x, y):
            self.game.reset_game()
            return
        # Convert screen coordinates to board coordinates
        if x < self.board_size and y < self.board_size:
            col = x // self.square_size
            row = y // self.square_size
            # If a piece is already selected, try to move it
            if self.game.selected_piece:
                if self.game.make_move(row, col):
                    # Move was successful
                    pass
                else:
                    # Try to select a different piece
                    self.game.select_piece(row, col)
            else:
                # Try to select a piece
                self.game.select_piece(row, col)
    def draw(self):
        """Draw the entire game interface"""
        # Draw sidebar background
        self.screen.fill(self.colors['sidebar'], 
                        (self.board_size, 0, 
                         self.window_size - self.board_size, self.board_size))
        # Draw the checkers board
        self.draw_board()
        # Draw pieces
        self.draw_pieces()
        # Draw highlights for selected piece and valid moves
        self.draw_highlights()
        # Draw sidebar content
        self.draw_sidebar()
    def draw_board(self):
        """Draw the 8x8 checkers board"""
        for row in range(8):
            for col in range(8):
                color = self.colors['light'] if (row + col) % 2 == 0 else self.colors['dark']
                rect = pygame.Rect(
                    col * self.square_size,
                    row * self.square_size,
                    self.square_size,
                    self.square_size
                )
                pygame.draw.rect(self.screen, color, rect)
                # Draw coordinates (for debugging/move notation)
                if col == 0:
                    coord_text = self.font.render(str(8 - row), True, self.colors['text'])
                    self.screen.blit(coord_text, (5, row * self.square_size + 5))
                if row == 7:
                    coord_text = self.font.render(chr(65 + col), True, self.colors['text'])
                    self.screen.blit(coord_text, (col * self.square_size + self.square_size - 20, 
                                                 row * self.square_size + self.square_size - 25))
    def draw_pieces(self):
        """Draw all pieces on the board"""
        for row in range(8):
            for col in range(8):
                piece = self.game.board.get_piece(row, col)
                if piece:
                    self.draw_piece(row, col, piece)
    def draw_piece(self, row, col, piece):
        """Draw a single piece"""
        center_x = col * self.square_size + self.square_size // 2
        center_y = row * self.square_size + self.square_size // 2
        radius = self.square_size // 2 - 10
        # Determine piece color
        if piece.is_king:
            piece_color = self.colors[f'{piece.color}_king']
        else:
            piece_color = self.colors[piece.color]
        # Draw piece
        pygame.draw.circle(self.screen, piece_color, (center_x, center_y), radius)
        pygame.draw.circle(self.screen, (0, 0, 0), (center_x, center_y), radius, 2)
        # Draw king crown symbol
        if piece.is_king:
            crown_color = (255, 215, 0)  # Gold color for crown
            # Draw a simple crown symbol (star)
            points = []
            for i in range(5):
                angle = 2 * 3.14159 * i / 5 - 3.14159 / 2
                outer_x = center_x + 0.7 * radius * 0.5 * (1 if i % 2 == 0 else 0.5) * pygame.math.Vector2(1, 0).rotate(angle * 180 / 3.14159).x
                outer_y = center_y + 0.7 * radius * 0.5 * (1 if i % 2 == 0 else 0.5) * pygame.math.Vector2(1, 0).rotate(angle * 180 / 3.14159).y
                points.append((outer_x, outer_y))
            if len(points) >= 3:
                pygame.draw.polygon(self.screen, crown_color, points)
    def draw_highlights(self):
        """Draw highlights for selected piece and valid moves"""
        # Highlight selected piece
        if self.game.selected_piece:
            row, col = self.game.selected_piece
            rect = pygame.Rect(
                col * self.square_size,
                row * self.square_size,
                self.square_size,
                self.square_size
            )
            pygame.draw.rect(self.screen, self.colors['highlight'], rect, 4)
        # Highlight valid moves
        for move in self.game.valid_moves:
            if len(move) == 3:
                row, col, _ = move
            else:
                row, col = move
            center_x = col * self.square_size + self.square_size // 2
            center_y = row * self.square_size + self.square_size // 2
            radius = self.square_size // 4
            # Draw a circle to indicate valid move
            pygame.draw.circle(self.screen, self.colors['valid_move'], 
                             (center_x, center_y), radius)
            pygame.draw.circle(self.screen, (0, 100, 0), 
                             (center_x, center_y), radius, 2)
    def draw_sidebar(self):
        """Draw the sidebar with game information and controls"""
        sidebar_x = self.board_size + 20
        # Draw title
        title = self.title_font.render("CHECKERS", True, self.colors['text'])
        self.screen.blit(title, (sidebar_x, 30))
        # Draw current game state
        state_text = self.game.get_game_state_text()
        state_surface = self.font.render(state_text, True, self.colors['text'])
        self.screen.blit(state_surface, (sidebar_x, 100))
        # Draw player indicators
        red_indicator = self.font.render("Red Player", True, self.colors['red'])
        black_indicator = self.font.render("Black Player", True, self.colors['black'])
        self.screen.blit(red_indicator, (sidebar_x, 150))
        self.screen.blit(black_indicator, (sidebar_x, 180))
        # Draw piece counts
        red_pieces = len(self.game.board.get_pieces_by_color('red'))
        black_pieces = len(self.game.board.get_pieces_by_color('black'))
        red_count = self.font.render(f"Pieces: {red_pieces}", True, self.colors['text'])
        black_count = self.font.render(f"Pieces: {black_pieces}", True, self.colors['text'])
        self.screen.blit(red_count, (sidebar_x + 120, 150))
        self.screen.blit(black_count, (sidebar_x + 120, 180))
        # Draw instructions
        instructions = [
            "How to Play:",
            "1. Click on your piece to select it",
            "2. Click on highlighted square to move",
            "3. Captures are mandatory when available",
            "4. Pieces become kings at opposite end",
            "5. Kings can move both forward and backward"
        ]
        for i, line in enumerate(instructions):
            text_surface = self.font.render(line, True, self.colors['text'])
            self.screen.blit(text_surface, (sidebar_x, 230 + i * 30))
        # Draw reset button
        mouse_pos = pygame.mouse.get_pos()
        button_color = self.colors['button_hover'] if self.reset_button.collidepoint(mouse_pos) else self.colors['button']
        pygame.draw.rect(self.screen, button_color, self.reset_button, border_radius=10)
        pygame.draw.rect(self.screen, (0, 0, 0), self.reset_button, 2, border_radius=10)
        reset_text = self.font.render("Reset Game", True, (255, 255, 255))
        text_rect = reset_text.get_rect(center=self.reset_button.center)
        self.screen.blit(reset_text, text_rect)
        # Draw move notation example
        notation_text = self.font.render("Move Notation:", True, self.colors['text'])
        self.screen.blit(notation_text, (sidebar_x, 500))
        example_text = self.font.render("e.g., A3-B4", True, self.colors['text'])
        self.screen.blit(example_text, (sidebar_x, 530))
        # Draw current move in notation if piece is selected
        if self.game.selected_piece:
            from_row, from_col = self.game.selected_piece
            from_notation = f"{chr(65 + from_col)}{8 - from_row}"
            notation = self.font.render(f"From: {from_notation}", True, self.colors['text'])
            self.screen.blit(notation, (sidebar_x, 560))