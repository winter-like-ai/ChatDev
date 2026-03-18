'''
game.py
Main game controller class handling game loop and logic.
'''
import pygame
import sys
from board import Board
from constants import *
class Game:
    def __init__(self):
        """Initialize the game."""
        self.win = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Checkers Game")
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.turn = PLAYER_ONE
        self.game_over = False
        # Fixed: Use pygame.font.Font with None for default font instead of SysFont(None, ...)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.move_history = []
    def run(self):
        """Main game loop."""
        while True:
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and not self.game_over:
                    pos = pygame.mouse.get_pos()
                    row = pos[1] // SQUARE_SIZE
                    col = pos[0] // SQUARE_SIZE
                    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
                        piece = self.board.get_piece(row, col)
                        # Check if player is clicking their own piece
                        if piece != 0 and piece.player == self.turn:
                            turn_ended = self.board.select(row, col)
                            if turn_ended:
                                self.end_turn()
                        elif self.board.selected_piece:
                            turn_ended = self.board.select(row, col)
                            if turn_ended:
                                self.end_turn()
            self.draw()
            self.check_game_over()
    def end_turn(self):
        """Switch turns and clear selection."""
        self.turn = PLAYER_TWO if self.turn == PLAYER_ONE else PLAYER_ONE
        self.board.selected_piece = None
        self.board.valid_moves = {}
        self.board.valid_captures = {}
    def check_game_over(self):
        """Check if the game is over."""
        player_one_pieces = 0
        player_two_pieces = 0
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board.get_piece(row, col)
                if piece != 0:
                    if piece.player == PLAYER_ONE:
                        player_one_pieces += 1
                    else:
                        player_two_pieces += 1
        if player_one_pieces == 0:
            self.game_over = True
            self.winner = PLAYER_TWO
        elif player_two_pieces == 0:
            self.game_over = True
            self.winner = PLAYER_ONE
    def reset_game(self):
        """Reset the game to initial state."""
        self.board = Board()
        self.turn = PLAYER_ONE
        self.game_over = False
        self.move_history = []
    def draw(self):
        """Draw everything on the screen."""
        self.win.fill(BLACK)
        self.board.draw(self.win)
        self.draw_ui()
        pygame.display.update()
    def draw_ui(self):
        """Draw the user interface elements."""
        # Draw turn indicator
        turn_text = f"Turn: {'Red (Player 1)' if self.turn == PLAYER_ONE else 'Blue (Player 2)'}"
        turn_color = RED if self.turn == PLAYER_ONE else BLUE
        turn_surface = self.font.render(turn_text, True, turn_color)
        self.win.blit(turn_surface, (BOARD_WIDTH + 20, 50))
        # Draw instructions
        instructions = [
            "Instructions:",
            "1. Click on your piece to select",
            "2. Click on highlighted square",
            "   to move",
            "3. Green = regular move",
            "4. Red = capture move",
            "5. Kings can move both directions",
            "",
            "Controls:",
            "R - Reset game",
            "Q - Quit game"
        ]
        y_pos = 120
        for line in instructions:
            text_surface = self.small_font.render(line, True, WHITE)
            self.win.blit(text_surface, (BOARD_WIDTH + 20, y_pos))
            y_pos += 30
        # Draw move notation
        notation_text = "Move Notation:"
        notation_surface = self.small_font.render(notation_text, True, WHITE)
        self.win.blit(notation_surface, (BOARD_WIDTH + 20, 400))
        # Draw current board state
        board_text = self.board.get_board_state_text()
        lines = board_text.split('\n')
        y_pos = 430
        for line in lines:
            text_surface = self.small_font.render(line, True, WHITE)
            self.win.blit(text_surface, (BOARD_WIDTH + 20, y_pos))
            y_pos += 20
        # Draw game over message
        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.win.blit(overlay, (0, 0))
            winner_text = f"{'Red' if self.winner == PLAYER_ONE else 'Blue'} Player Wins!"
            winner_surface = pygame.font.SysFont(None, 72).render(winner_text, True, WHITE)
            self.win.blit(winner_surface, 
                         (WINDOW_WIDTH // 2 - winner_surface.get_width() // 2,
                          WINDOW_HEIGHT // 2 - winner_surface.get_height() // 2))
            restart_text = "Press R to restart or Q to quit"
            restart_surface = self.font.render(restart_text, True, WHITE)
            self.win.blit(restart_surface,
                         (WINDOW_WIDTH // 2 - restart_surface.get_width() // 2,
                          WINDOW_HEIGHT // 2 + 50))