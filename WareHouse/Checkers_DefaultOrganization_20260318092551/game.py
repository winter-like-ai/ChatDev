'''
Game class managing game state, turns, and logic.
'''
import pygame
from board import Board
from constants import ROWS, COLS, SQUARE_SIZE, RED, BLUE, GREEN, GRAY, HIGHLIGHT
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.board = Board()
        self.turn = "red"  # Red starts
        self.selected = None
        self.valid_moves = {}
        self.message = "Red's turn"
        self.game_over = False
    def update(self):
        '''Update game state'''
        if self.game_over:
            return
        winner = self.board.winner()
        if winner:
            self.game_over = True
            self.message = f"{winner.capitalize()} wins! Press R to restart"
    def draw(self):
        '''Draw the game'''
        self.board.draw(self.screen)
        self.draw_valid_moves()
        self.draw_message()
    def draw_valid_moves(self):
        '''Highlight valid moves for selected piece'''
        if self.selected:
            for move in self.valid_moves:
                row, col = move
                x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                pygame.draw.circle(self.screen, GREEN, (x, y), 15)
    def draw_message(self):
        '''Display game status message'''
        font = pygame.font.SysFont(None, 36)
        text = font.render(self.message, True, (255, 255, 255))
        pygame.draw.rect(self.screen, (50, 50, 50), (0, HEIGHT - 40, WIDTH, 40))
        self.screen.blit(text, (10, HEIGHT - 35))
        # Draw turn indicator
        turn_color = RED if self.turn == "red" else BLUE
        pygame.draw.circle(self.screen, turn_color, (WIDTH - 30, HEIGHT - 20), 15)
    def select(self, row, col):
        '''Select a piece or move to a position'''
        if self.game_over:
            return False
        piece = self.board.get_piece(row, col)
        if self.selected:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        elif piece is not None and piece.color == self.turn:
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
        return False
    def _move(self, row, col):
        '''Move selected piece to new position'''
        piece = self.selected
        if piece is None or (row, col) not in self.valid_moves:
            return False
        # Move the piece
        self.board.move(piece, row, col)
        # Remove captured pieces
        skipped = self.valid_moves.get((row, col))
        if skipped:
            self.board.remove(skipped)
        # Check for multiple jumps
        if skipped and self.board.get_valid_moves(piece):
            # Continue jumping with same piece
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            self.message = f"{self.turn.capitalize()}'s turn - Continue jumping!"
            return True
        # Switch turns
        self.change_turn()
        self.selected = None
        self.valid_moves = {}
        return True
    def change_turn(self):
        '''Switch to the other player's turn'''
        self.turn = "blue" if self.turn == "red" else "red"
        self.message = f"{self.turn.capitalize()}'s turn"
    def handle_click(self, pos):
        '''Handle mouse click events'''
        if self.game_over:
            return
        x, y = pos
        row = y // SQUARE_SIZE
        col = x // SQUARE_SIZE
        if 0 <= row < ROWS and 0 <= col < COLS:
            self.select(row, col)
    def reset(self):
        '''Reset the game to initial state'''
        self.board = Board()
        self.turn = "red"
        self.selected = None
        self.valid_moves = {}
        self.message = "Red's turn"
        self.game_over = False
    def get_board_state(self):
        '''Get current board state for notation display'''
        state = []
        for row in range(ROWS):
            row_state = []
            for col in range(COLS):
                piece = self.board.get_piece(row, col)
                if piece is None:
                    row_state.append('.')
                else:
                    if piece.color == "red":
                        row_state.append('R' if piece.king else 'r')
                    else:
                        row_state.append('B' if piece.king else 'b')
            state.append(''.join(row_state))
        return state