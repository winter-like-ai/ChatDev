'''
Main game class handling game flow, turns, and user input.
'''
import pygame
from board import Board
from constants import *
class Game:
    def __init__(self, win):
        self.win = win
        self.board = Board()
        self.turn = PLAYER1_COLOR  # Red starts
        self.selected = None
        self.running = True
        self.winner = None
        self.font = pygame.font.SysFont('Arial', 24)
        self.move_history = []
        self.text_input = ""
        self.input_active = False
        self.input_rect = pygame.Rect(WINDOW_WIDTH - 200, BOARD_SIZE + 10, 180, 30)
        self.input_prompt = "Enter move (e.g., a3-b4):"
    def update(self):
        '''Update game display'''
        self.win.fill(BLACK)
        self.board.draw(self.win)
        self.draw_ui()
        pygame.display.update()
    def draw_ui(self):
        '''Draw user interface elements'''
        # Draw turn indicator
        turn_text = "Red's Turn" if self.turn == PLAYER1_COLOR else "Blue's Turn"
        turn_color = PLAYER1_COLOR if self.turn == PLAYER1_COLOR else PLAYER2_COLOR
        turn_surface = self.font.render(turn_text, True, turn_color)
        self.win.blit(turn_surface, (10, BOARD_SIZE + 10))
        # Draw move notation input area
        pygame.draw.rect(self.win, WHITE, self.input_rect, 2)
        prompt_surface = self.font.render(self.input_prompt, True, WHITE)
        self.win.blit(prompt_surface, (WINDOW_WIDTH - 200, BOARD_SIZE + 45))
        text_surface = self.font.render(self.text_input, True, WHITE)
        self.win.blit(text_surface, (self.input_rect.x + 5, self.input_rect.y + 5))
        # Draw move history
        if self.move_history:
            last_move = self.move_history[-1]
            move_text = f"Last move: {last_move}"
            move_surface = self.font.render(move_text, True, WHITE)
            self.win.blit(move_surface, (10, BOARD_SIZE + 40))
        # Draw winner
        if self.winner:
            winner_text = "Red Wins!" if self.winner == PLAYER1_COLOR else "Blue Wins!"
            winner_surface = self.font.render(winner_text, True, GREEN)
            self.win.blit(winner_surface, (WINDOW_WIDTH // 2 - 50, BOARD_SIZE + 70))
            # Draw restart instructions
            restart_text = "Press R to restart"
            restart_surface = self.font.render(restart_text, True, WHITE)
            self.win.blit(restart_surface, (WINDOW_WIDTH // 2 - 60, BOARD_SIZE + 100))
    def select(self, row, col):
        '''Handle piece selection'''
        if self.winner:
            return False
        if self.selected:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        else:
            piece = self.board.get_piece(row, col)
            if piece and piece.color == self.turn:
                self.selected = piece
                self.board.select(row, col)
                return True
        return False
    def _move(self, row, col):
        '''Execute a move'''
        piece = self.selected
        if piece and (row, col) in self.board.valid_moves:
            # Record move in notation
            from_pos = f"{chr(97 + piece.col)}{8 - piece.row}"
            to_pos = f"{chr(97 + col)}{8 - row}"
            self.move_history.append(f"{from_pos}-{to_pos}")
            # Move piece
            self.board.move(piece, row, col)
            # Handle captures
            skipped = self.board.valid_moves.get((row, col))
            if skipped:
                self.board.remove(skipped)
            # Switch turns
            self.change_turn()
            return True
        return False
    def change_turn(self):
        '''Switch to other player's turn'''
        self.board.valid_moves = {}
        self.board.selected_piece = None
        self.selected = None
        if self.turn == PLAYER1_COLOR:
            self.turn = PLAYER2_COLOR
        else:
            self.turn = PLAYER1_COLOR
        # Check for winner
        self.winner = self.board.winner()
    def reset(self):
        '''Reset game to initial state'''
        self.board = Board()
        self.turn = PLAYER1_COLOR
        self.selected = None
        self.winner = None
        self.move_history = []
        self.text_input = ""
        self.input_active = False
    def get_board(self):
        '''Get current board state'''
        return self.board
    def ai_move(self, board):
        '''Placeholder for AI move (not implemented in this version)'''
        pass
    def handle_text_input(self, event):
        '''Handle text input for move notation'''
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.text_input and not self.winner:
                self.process_move_notation(self.text_input)
                self.text_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.text_input = self.text_input[:-1]
            else:
                # Only allow alphanumeric and dash characters
                if event.unicode.isalnum() or event.unicode == '-':
                    self.text_input += event.unicode
    def process_move_notation(self, notation):
        '''Process move notation like "a3-b4"'''
        try:
            # Parse notation
            parts = notation.strip().lower().split('-')
            if len(parts) != 2:
                return False
            from_pos, to_pos = parts
            # Convert notation to board coordinates
            from_col = ord(from_pos[0]) - ord('a')
            from_row = 8 - int(from_pos[1])
            to_col = ord(to_pos[0]) - ord('a')
            to_row = 8 - int(to_pos[1])
            # Validate coordinates
            if not (0 <= from_row < ROWS and 0 <= from_col < COLS and
                    0 <= to_row < ROWS and 0 <= to_col < COLS):
                return False
            # Select piece if not already selected
            if not self.selected:
                piece = self.board.get_piece(from_row, from_col)
                if piece and piece.color == self.turn:
                    self.selected = piece
                    self.board.select(from_row, from_col)
            # Execute move
            if self.selected and (to_row, to_col) in self.board.valid_moves:
                return self._move(to_row, to_col)
            return False
        except (ValueError, IndexError):
            return False
    def handle_mouse_click(self, pos):
        '''Handle mouse click for piece selection'''
        if self.input_rect.collidepoint(pos):
            self.input_active = True
        else:
            self.input_active = False
        row = pos[1] // SQUARE_SIZE
        col = pos[0] // SQUARE_SIZE
        if row < ROWS and col < COLS:
            self.select(row, col)