'''
Game class managing game state, turns, and user interaction.
'''
import pygame
from board import Board
from constants import *
class Game:
    def __init__(self, screen):
        self.screen = screen
        self.board = Board()
        self.turn = RED  # Red starts
        self.selected = None
        self.valid_moves = {}
        self.game_over = False
        self.winner = None
    def update(self):
        '''Update game display.'''
        self.board.draw(self.screen)
        self.draw_valid_moves(self.valid_moves)
        if self.selected:
            self.draw_selected()
        if self.game_over:
            self.draw_game_over()
    def select(self, row, col):
        '''Handle piece selection and movement.'''
        if self.game_over:
            return
        if self.selected:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.turn:
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
        return False
    def _move(self, row, col):
        '''Execute a move.'''
        piece = self.selected
        if piece and (row, col) in self.valid_moves:
            # Move the piece
            self.board.move(piece, row, col)
            # Remove captured pieces
            skipped = self.valid_moves[(row, col)]
            if skipped:
                self.board.remove(skipped)
            # Check for multiple jumps
            if skipped:
                new_moves = self.board.get_valid_moves(piece)
                if any(skipped in move for move in new_moves.values()):
                    self.selected = piece
                    self.valid_moves = new_moves
                    return True
            self.change_turn()
            return True
        return False
    def draw_valid_moves(self, moves):
        '''Highlight valid moves on the board.'''
        for move in moves:
            row, col = move
            x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            y = row * SQUARE_SIZE + SQUARE_SIZE // 2
            pygame.draw.circle(self.screen, HIGHLIGHT, (x, y), 15)
    def draw_selected(self):
        '''Highlight selected piece.'''
        if self.selected:
            x = self.selected.col * SQUARE_SIZE + SQUARE_SIZE // 2
            y = self.selected.row * SQUARE_SIZE + SQUARE_SIZE // 2
            pygame.draw.circle(self.screen, BLUE, (x, y), PIECE_RADIUS + 3, 3)
    def change_turn(self):
        '''Switch to the other player's turn.'''
        self.valid_moves = {}
        self.selected = None
        # Check for winner
        winner = self.board.winner()
        if winner:
            self.game_over = True
            self.winner = winner
            return
        # Switch turn
        self.turn = WHITE if self.turn == RED else RED
        # Check if current player has any moves
        if not self._player_has_moves():
            self.game_over = True
            self.winner = WHITE if self.turn == RED else RED
    def _player_has_moves(self):
        '''Check if current player has any valid moves.'''
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.get_piece(row, col)
                if piece and piece.color == self.turn:
                    moves = self.board.get_valid_moves(piece)
                    if moves:
                        return True
        return False
    def draw_game_over(self):
        '''Display game over message.'''
        font = pygame.font.SysFont('Arial', 50)
        if self.winner == RED:
            text = font.render("Red Wins!", True, RED)
        else:
            text = font.render("White Wins!", True, WHITE)
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        # Draw text
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(text, text_rect)
        # Draw restart instruction
        font_small = pygame.font.SysFont('Arial', 30)
        restart_text = font_small.render("Close and restart to play again", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
        self.screen.blit(restart_text, restart_rect)
    def get_move_notation(self, from_pos, to_pos):
        '''Convert positions to algebraic notation.'''
        col_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        from_row = 8 - from_pos[0]
        from_col = col_letters[from_pos[1]]
        to_row = 8 - to_pos[0]
        to_col = col_letters[to_pos[1]]
        return f"{from_col}{from_row}-{to_col}{to_row}"