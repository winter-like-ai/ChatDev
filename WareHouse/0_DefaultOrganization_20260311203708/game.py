'''
Main game logic and state management
'''
import pygame
from board import Board
from constants import *
class Game:
    def __init__(self, win):
        self.win = win
        # Initialize font with fallback to default pygame font
        try:
            self.font = pygame.font.SysFont('Arial', 24)
        except Exception:
            self.font = pygame.font.Font(None, 24)  # Fallback to default font
        self.reset()
    def reset(self):
        '''Reset game to initial state'''
        self.selected = None
        self.board = Board()
        self.turn = PLAYER_ONE
        self.valid_moves = {}
        self.winner = None
        self.message = "Red's turn"
    def update(self):
        '''Update game display'''
        self.board.draw(self.win)
        self.draw_valid_moves(self.valid_moves)
        self.draw_message()
        pygame.display.update()
    def draw_message(self):
        '''Draw current game status message'''
        text = self.font.render(self.message, True, BLACK)
        self.win.blit(text, (10, HEIGHT - 30))
    def draw_valid_moves(self, moves):
        '''Highlight valid moves'''
        for move in moves:
            row, col = move
            pygame.draw.circle(self.win, HIGHLIGHT,
                             (col * SQUARE_SIZE + SQUARE_SIZE // 2,
                              row * SQUARE_SIZE + SQUARE_SIZE // 2),
                             15)
    def select(self, row, col):
        '''Select piece or move to selected position'''
        if self.winner:
            return False
        # Check if there are any forced captures
        forced_capture_pieces = self.get_forced_capture_pieces()
        piece = self.board.get_piece(row, col)
        if self.selected:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        elif piece != EMPTY and piece.color == self.turn:
            # If there are forced captures, only allow selecting pieces that can capture
            if forced_capture_pieces and piece not in forced_capture_pieces:
                self.message = "Must capture if possible!"
                return False
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
        return False
    def get_forced_capture_pieces(self):
        '''Get all pieces that have capture moves available'''
        capture_pieces = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board.get_piece(row, col)
                if piece != EMPTY and piece.color == self.turn:
                    moves = self.board.get_valid_moves(piece)
                    # Check if any move involves capturing
                    for skipped in moves.values():
                        if skipped:  # If there are skipped pieces, it's a capture
                            capture_pieces.append(piece)
                            break
        return capture_pieces
    def _move(self, row, col):
        '''Execute move if valid'''
        piece = self.selected
        move = (row, col)
        if move in self.valid_moves:
            # Move the piece
            self.board.move(piece, row, col)
            # Remove captured pieces
            skipped = self.valid_moves[move]
            if skipped:
                self.board.remove(skipped)
            # Check for multiple jumps
            if skipped:
                new_moves = self.board.get_valid_moves(piece)
                if any(skipped in move_skipped for move_skipped in new_moves.values()):
                    self.selected = piece
                    self.valid_moves = new_moves
                    return True
            self.change_turn()
            return True
        return False
    def change_turn(self):
        '''Switch to other player's turn'''
        self.valid_moves = {}
        self.selected = None
        if self.turn == PLAYER_ONE:
            self.turn = PLAYER_TWO
            self.message = "Blue's turn"
        else:
            self.turn = PLAYER_ONE
            self.message = "Red's turn"
        # Check for winner
        winner = self.board.winner()
        if winner:
            self.winner = winner
            self.message = f"{winner.capitalize()} wins!"
    def get_board(self):
        '''Get current board state'''
        return self.board
    def ai_move(self, board):
        '''Make AI move (for future AI implementation)'''
        self.board = board
        self.change_turn()
    def get_pos_from_mouse(self, pos):
        '''Convert mouse position to board coordinates'''
        x, y = pos
        row = y // SQUARE_SIZE
        col = x // SQUARE_SIZE
        return row, col