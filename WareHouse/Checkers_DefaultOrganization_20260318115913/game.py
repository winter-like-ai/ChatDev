'''
Game controller class.
Manages game state, turns, and user interaction.
'''
import pygame
import sys
from checkers import Board
from constants import *
class Game:
    def __init__(self):
        # Initialize pygame window
        self.win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Checkers Game")
        # Initialize game components
        self.board = Board()
        self.turn = PLAYER1_TURN
        self.selected_piece = None
        self.valid_moves = {}
        self.game_over = False
        self.winner = None
        # Font for UI
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 24)
    def run(self):
        '''Main game loop'''
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    pos = pygame.mouse.get_pos()
                    row, col = self.get_row_col_from_mouse(pos)
                    self.handle_click(row, col)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
            # Draw everything
            self.draw()
            pygame.display.update()
    def get_row_col_from_mouse(self, pos):
        '''Convert mouse position to board coordinates'''
        x, y = pos
        row = y // SQUARE_SIZE
        col = x // SQUARE_SIZE
        return row, col
    def handle_click(self, row, col):
        '''Handle mouse click on the board'''
        if row >= ROWS or col >= COLS:
            return
        # If a piece is already selected
        if self.selected_piece:
            result = self._move(row, col)
            if not result:
                self.selected_piece = None
                self.valid_moves = {}
                self.handle_click(row, col)
        else:
            # Select a piece
            piece = self.board.get_piece(row, col)
            if piece:
                # Check if it's the correct player's turn
                if (self.turn == PLAYER1_TURN and piece.player == PLAYER1) or \
                   (self.turn == PLAYER2_TURN and piece.player == PLAYER2):
                    self.selected_piece = piece
                    self.valid_moves = self.board.get_valid_moves(piece)
    def _move(self, row, col):
        '''Move selected piece to target position'''
        piece = self.selected_piece
        # Check if move is valid
        if (row, col) in self.valid_moves:
            # Move the piece
            self.board.move_piece(piece, row, col)
            # Remove captured pieces
            skipped = self.valid_moves.get((row, col), [])
            if skipped:
                for skip_piece in skipped:
                    self.board.remove_piece(skip_piece.row, skip_piece.col)
            # Switch turns
            self.switch_turn()
            self.selected_piece = None
            self.valid_moves = {}
            # Check for game over
            self.check_game_over()
            return True
        return False
    def switch_turn(self):
        '''Switch to the other player's turn'''
        if self.turn == PLAYER1_TURN:
            self.turn = PLAYER2_TURN
        else:
            self.turn = PLAYER1_TURN
    def check_game_over(self):
        '''Check if the game is over'''
        player1_pieces = self.board.get_all_pieces(PLAYER1)
        player2_pieces = self.board.get_all_pieces(PLAYER2)
        if not player1_pieces:
            self.game_over = True
            self.winner = "Player 2 (Blue)"
        elif not player2_pieces:
            self.game_over = True
            self.winner = "Player 1 (Red)"
    def reset_game(self):
        '''Reset the game to initial state'''
        self.board = Board()
        self.turn = PLAYER1_TURN
        self.selected_piece = None
        self.valid_moves = {}
        self.game_over = False
        self.winner = None
    def draw(self):
        '''Draw the entire game state'''
        # Draw board and pieces
        self.board.draw(self.win)
        # Draw valid moves if piece is selected
        if self.selected_piece:
            self.draw_valid_moves(self.valid_moves)
        # Draw UI panel
        self.draw_ui()
        # Draw game over screen if needed
        if self.game_over:
            self.draw_game_over()
    def draw_valid_moves(self, moves):
        '''Highlight valid moves for selected piece'''
        for move in moves:
            row, col = move
            x = col * SQUARE_SIZE
            y = row * SQUARE_SIZE
            # Draw semi-transparent yellow square
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            s.fill(HIGHLIGHT)
            self.win.blit(s, (x, y))
    def draw_ui(self):
        '''Draw user interface elements'''
        # Draw turn indicator
        turn_text = "Red's Turn" if self.turn == PLAYER1_TURN else "Blue's Turn"
        turn_color = RED if self.turn == PLAYER1_TURN else BLUE
        turn_surface = self.font.render(turn_text, True, turn_color)
        self.win.blit(turn_surface, (10, BOARD_HEIGHT + 10))
        # Draw instructions
        instructions = [
            "Instructions:",
            "1. Click on your piece to select it",
            "2. Click on highlighted square to move",
            "3. Must capture if possible",
            "4. Press R to reset, Q to quit"
        ]
        for i, line in enumerate(instructions):
            text_surface = self.small_font.render(line, True, BLACK)
            self.win.blit(text_surface, (BOARD_WIDTH - 300, BOARD_HEIGHT + 10 + i * 25))
        # Draw piece count
        player1_count = len(self.board.get_all_pieces(PLAYER1))
        player2_count = len(self.board.get_all_pieces(PLAYER2))
        count_text = f"Red: {player1_count}  Blue: {player2_count}"
        count_surface = self.font.render(count_text, True, BLACK)
        self.win.blit(count_surface, (BOARD_WIDTH // 2 - 80, BOARD_HEIGHT + 10))
    def draw_game_over(self):
        '''Draw game over screen'''
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.win.blit(overlay, (0, 0))
        # Draw game over text
        game_over_text = self.font.render("GAME OVER", True, WHITE)
        winner_text = self.font.render(f"Winner: {self.winner}", True, GREEN)
        restart_text = self.small_font.render("Press R to restart or Q to quit", True, WHITE)
        self.win.blit(game_over_text, (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, 
                                      WINDOW_HEIGHT // 2 - 50))
        self.win.blit(winner_text, (WINDOW_WIDTH // 2 - winner_text.get_width() // 2, 
                                   WINDOW_HEIGHT // 2))
        self.win.blit(restart_text, (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, 
                                    WINDOW_HEIGHT // 2 + 50))