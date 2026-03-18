'''
Pygame GUI for Checkers game
'''
import pygame
from constants import *
from game import Game
class GUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Checkers Game")
        self.clock = pygame.time.Clock()
        self.game = Game()
        # Initialize font with fallback to avoid Windows font registry issues
        self.font = None
        # List of font names to try in order
        font_names = ['arial', 'freesansbold', 'dejavusans', None]
        for font_name in font_names:
            try:
                if font_name:
                    self.font = pygame.font.SysFont(font_name, 36)
                else:
                    self.font = pygame.font.Font(None, 36)
                break
            except Exception:
                continue
        # If all attempts fail, create a default font
        if self.font is None:
            self.font = pygame.font.Font(None, 36)
        self.running = True
    def draw_board(self):
        # Draw checkerboard
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(self.screen, color, 
                               (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                SQUARE_SIZE, SQUARE_SIZE))
        # Highlight selected piece
        selected = self.game.get_selected_piece()
        if selected:
            row, col = selected
            if (row + col) % 2 == 0:
                highlight_color = (255, 255, 0, 128)  # Semi-transparent yellow
            else:
                highlight_color = (255, 255, 100, 128)
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(highlight_color)
            self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        # Highlight valid moves
        for move in self.game.get_valid_moves():
            row, col = move
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((0, 255, 0, 64))  # Semi-transparent green
            self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        # Highlight valid captures
        for capture in self.game.get_valid_captures():
            row, col = capture[0], capture[1]
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill((255, 0, 0, 64))  # Semi-transparent red
            self.screen.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    def draw_pieces(self):
        board = self.game.get_board()
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = board[row][col]
                if piece != 0:
                    # Draw piece circle
                    color = RED if piece.color == 'red' else BLUE
                    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                    radius = SQUARE_SIZE // 2 - 10
                    pygame.draw.circle(self.screen, color, 
                                     (center_x, center_y), radius)
                    pygame.draw.circle(self.screen, BLACK,
                                     (center_x, center_y), radius, 2)
                    # Draw king crown
                    if piece.king:
                        crown_color = YELLOW if piece.color == 'red' else WHITE
                        crown_rect = pygame.Rect(
                            center_x - radius//2,
                            center_y - radius//2,
                            radius,
                            radius//2
                        )
                        pygame.draw.rect(self.screen, crown_color, crown_rect, border_radius=3)
                        pygame.draw.rect(self.screen, BLACK, crown_rect, 2, border_radius=3)
    def draw_status(self):
        # Draw current player
        current_player = self.game.get_current_player()
        player_text = f"Current Player: {current_player.capitalize()}"
        player_surface = self.font.render(player_text, True, WHITE)
        self.screen.blit(player_surface, (10, HEIGHT - 40))
        # Draw winner if game is over
        winner = self.game.get_winner()
        if winner:
            winner_text = f"Winner: {winner.capitalize()}!"
            winner_surface = self.font.render(winner_text, True, GREEN)
            text_rect = winner_surface.get_rect(center=(WIDTH//2, 30))
            self.screen.blit(winner_surface, text_rect)
        # Draw capture mandatory message
        if self.game.must_capture:
            capture_text = "Capture is mandatory!"
            capture_surface = self.font.render(capture_text, True, RED)
            self.screen.blit(capture_surface, (WIDTH - 200, HEIGHT - 40))
    def handle_click(self, pos):
        x, y = pos
        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            self.game.select_piece(row, col)
    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button
                        self.handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:  # Reset game with R key
                        self.game = Game()
                    elif event.key == pygame.K_ESCAPE:  # Quit with ESC
                        self.running = False
            # Draw everything
            self.screen.fill(BLACK)
            self.draw_board()
            self.draw_pieces()
            self.draw_status()
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()