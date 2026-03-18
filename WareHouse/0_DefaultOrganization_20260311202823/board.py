'''
Board class representing the checkers board.
Handles board state, piece placement, movement, and drawing.
'''
import pygame
from piece import Piece
from constants import ROWS, COLS, SQUARE_SIZE, WHITE, BLACK, RED, BLUE, LIGHT_BROWN, DARK_BROWN, CROWN_SIZE
class Board:
    def __init__(self):
        """Initialize the checkers board with starting positions."""
        self.board = []
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self.create_board()
    def create_board(self):
        """Create the initial board setup with pieces."""
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        # Place pieces in starting positions
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:  # Only dark squares
                    if row < 3:
                        self.board[row][col] = Piece(row, col, 'white')
                    elif row > 4:
                        self.board[row][col] = Piece(row, col, 'red')
    def draw(self, screen):
        """Draw the board and all pieces."""
        self.draw_squares(screen)
        self.draw_pieces(screen)
    def draw_squares(self, screen):
        """Draw the checkerboard pattern."""
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(screen, color, 
                                (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                 SQUARE_SIZE, SQUARE_SIZE))
    def draw_pieces(self, screen):
        """Draw all pieces on the board."""
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece is not None:
                    piece.calc_pos()
                    # Draw piece circle
                    color = RED if piece.color == 'red' else WHITE
                    pygame.draw.circle(screen, color, 
                                      (piece.x, piece.y), 
                                      SQUARE_SIZE // 2 - 10)
                    # Draw outline
                    outline_color = BLACK
                    pygame.draw.circle(screen, outline_color, 
                                      (piece.x, piece.y), 
                                      SQUARE_SIZE // 2 - 10, 2)
                    # Draw crown for kings
                    if piece.king:
                        crown_color = YELLOW if piece.color == 'red' else BLUE
                        pygame.draw.circle(screen, crown_color,
                                          (piece.x, piece.y),
                                          CROWN_SIZE // 2)
                        pygame.draw.circle(screen, BLACK,
                                          (piece.x, piece.y),
                                          CROWN_SIZE // 2, 2)
    def move(self, piece, row, col):
        """
        Move a piece to a new position.
        Args:
            piece: Piece to move
            row: Destination row
            col: Destination column
        Returns:
            List of captured piece positions
        """
        # Get valid moves for the piece
        valid_moves = piece.get_valid_moves(self)
        if (row, col) in valid_moves:
            # Move the piece
            self.board[piece.row][piece.col] = None
            self.board[row][col] = piece
            piece.move(row, col)
            # Handle captures
            captured_positions = valid_moves[(row, col)]
            for capture_pos in captured_positions:
                self.remove(capture_pos[0], capture_pos[1])
            # Check for king promotion
            if not piece.king:
                if piece.color == 'red' and row == 0:
                    piece.make_king()
                    self.red_kings += 1
                elif piece.color == 'white' and row == ROWS - 1:
                    piece.make_king()
                    self.white_kings += 1
            return captured_positions
        return []
    def get_piece(self, row, col):
        """
        Get piece at specified position.
        Args:
            row: Row position
            col: Column position
        Returns:
            Piece object or None
        """
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return None
    def remove(self, row, col):
        """
        Remove piece from board.
        Args:
            row: Row position
            col: Column position
        """
        piece = self.board[row][col]
        if piece is not None:
            self.board[row][col] = None
            if piece.color == 'red':
                self.red_left -= 1
                if piece.king:
                    self.red_kings -= 1
            else:
                self.white_left -= 1
                if piece.king:
                    self.white_kings -= 1
    def get_valid_moves(self, piece):
        """
        Get all valid moves for a piece.
        Args:
            piece: Piece object
        Returns:
            Dictionary of valid moves
        """
        return piece.get_valid_moves(self)
    def winner(self):
        """
        Check if there's a winner.
        Returns:
            'red', 'white', or None
        """
        if self.red_left <= 0:
            return 'white'
        elif self.white_left <= 0:
            return 'red'
        # Check if any player has no valid moves
        red_has_moves = False
        white_has_moves = False
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece is not None:
                    moves = piece.get_valid_moves(self)
                    if moves:
                        if piece.color == 'red':
                            red_has_moves = True
                        else:
                            white_has_moves = True
        if not red_has_moves:
            return 'white'
        elif not white_has_moves:
            return 'red'
        return None
    def reset(self):
        """Reset the board to starting position."""
        self.__init__()