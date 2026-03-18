'''
board.py
Board class representing the checkers board and piece management.
'''
import pygame
from piece import Piece
from constants import *
class Board:
    def __init__(self):
        """Initialize the checkers board with pieces in starting positions."""
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.selected_piece = None
        self.valid_moves = {}
        self.valid_captures = {}
        self.create_pieces()
    def create_pieces(self):
        """Create initial pieces on the board."""
        # Player 1 pieces (top rows)
        for row in range(3):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, PLAYER_ONE)
        # Player 2 pieces (bottom rows)
        for row in range(5, BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, PLAYER_TWO)
    def draw(self, win):
        """Draw the board and pieces on the window."""
        self.draw_squares(win)
        self.draw_pieces(win)
        self.draw_highlights(win)
    def draw_squares(self, win):
        """Draw the checkerboard squares."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(win, color, 
                                (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                 SQUARE_SIZE, SQUARE_SIZE))
    def draw_pieces(self, win):
        """Draw all pieces on the board."""
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0:
                    self.draw_piece(win, piece)
    def draw_piece(self, win, piece):
        """Draw a single piece."""
        # Draw piece circle
        color = RED if piece.player == PLAYER_ONE else BLUE
        pygame.draw.circle(win, color, (piece.x, piece.y), SQUARE_SIZE // 2 - 10)
        # Draw king crown
        if piece.is_king():
            pygame.draw.circle(win, GREEN, (piece.x, piece.y), SQUARE_SIZE // 2 - 20)
            # Draw K letter for king
            font = pygame.font.SysFont(None, 30)
            text = font.render('K', True, WHITE)
            win.blit(text, (piece.x - 8, piece.y - 10))
    def draw_highlights(self, win):
        """Highlight selected piece and valid moves."""
        if self.selected_piece:
            # Highlight selected piece
            row, col = self.selected_piece.row, self.selected_piece.col
            self.highlight_square(win, row, col)
            # Highlight valid moves
            for (move_row, move_col) in self.valid_moves.keys():
                self.highlight_square(win, move_row, move_col, color=(0, 255, 0, 100))
            # Highlight valid captures
            for (capture_row, capture_col) in self.valid_captures.keys():
                self.highlight_square(win, capture_row, capture_col, color=(255, 0, 0, 100))
    def highlight_square(self, win, row, col, color=HIGHLIGHT_COLOR):
        """Highlight a square on the board."""
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
        s.fill(color)
        win.blit(s, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    def get_piece(self, row, col):
        """Get piece at specified position."""
        if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
            return self.board[row][col]
        return None
    def select(self, row, col):
        """
        Select a piece or move to a position.
        Returns:
            True if a move was made, False otherwise
        """
        piece = self.get_piece(row, col)
        # If clicking on a piece
        if piece != 0 and piece != self.selected_piece:
            self.selected_piece = piece
            self.valid_moves, self.valid_captures = piece.get_valid_moves(self)
            return False
        # If clicking on a valid move
        elif self.selected_piece and (row, col) in self.valid_moves:
            self.move(self.selected_piece, row, col)
            return True
        # If clicking on a valid capture
        elif self.selected_piece and (row, col) in self.valid_captures:
            captured_positions = self.valid_captures[(row, col)]
            self.move(self.selected_piece, row, col)
            # Remove captured pieces
            for cap_row, cap_col in captured_positions:
                self.board[cap_row][cap_col] = 0
            # Check for additional captures
            self.selected_piece = self.get_piece(row, col)
            _, new_captures = self.selected_piece.get_valid_moves(self)
            # Filter only capture moves
            new_captures = {k: v for k, v in new_captures.items() if v}
            if new_captures:
                self.valid_moves = {}
                self.valid_captures = new_captures
                return False  # Continue turn for multiple jumps
            else:
                self.selected_piece = None
                self.valid_moves = {}
                self.valid_captures = {}
                return True
        # Deselect
        else:
            self.selected_piece = None
            self.valid_moves = {}
            self.valid_captures = {}
            return False
    def move(self, piece, row, col):
        """Move a piece to a new position."""
        # Clear old position
        self.board[piece.row][piece.col] = 0
        # Move piece
        piece.move(row, col)
        self.board[row][col] = piece
        # Check for king promotion
        if not piece.is_king():
            if (piece.player == PLAYER_ONE and row == BOARD_SIZE - 1) or \
               (piece.player == PLAYER_TWO and row == 0):
                piece.make_king()
    def get_board_state_text(self):
        """Get text representation of board state."""
        text = "  a b c d e f g h\n"
        for row in range(BOARD_SIZE):
            text += f"{8-row} "
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece == 0:
                    text += ". "
                elif piece.player == PLAYER_ONE:
                    text += "r " if piece.type == REGULAR else "R "
                else:
                    text += "b " if piece.type == REGULAR else "B "
            text += f"{8-row}\n"
        text += "  a b c d e f g h"
        return text