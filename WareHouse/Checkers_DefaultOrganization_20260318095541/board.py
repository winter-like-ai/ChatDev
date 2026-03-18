'''
Board class representing the checkers board.
Manages piece placement, movement, and board rendering.
'''
import pygame
from piece import Piece
from constants import ROWS, COLS, SQUARE_SIZE, LIGHT_BROWN, DARK_BROWN, BLACK, WHITE
class Board:
    def __init__(self):
        '''Initialize an 8x8 checkers board with starting positions.'''
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.selected_piece = None
        self.valid_moves = []
        self.setup_board()
    def setup_board(self):
        '''Set up initial board with pieces in starting positions.'''
        from constants import PLAYER1_COLOR, PLAYER2_COLOR
        # Place red pieces (top rows)
        for row in range(3):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(PLAYER1_COLOR, row, col)
        # Place blue pieces (bottom rows)
        for row in range(5, ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(PLAYER2_COLOR, row, col)
    def get_piece(self, row, col):
        '''
        Get piece at specified position.
        Args:
            row (int): Row index
            col (int): Column index
        Returns:
            Piece or None: Piece at position, or None if empty
        '''
        if self.is_valid_position(row, col):
            return self.board[row][col]
        return None
    def is_valid_position(self, row, col):
        '''
        Check if position is within board bounds.
        Args:
            row (int): Row index
            col (int): Column index
        Returns:
            bool: True if position is valid
        '''
        return 0 <= row < ROWS and 0 <= col < COLS
    def move_piece(self, piece, row, col):
        '''
        Move piece to new position.
        Args:
            piece (Piece): Piece to move
            row (int): Destination row
            col (int): Destination column
        Returns:
            bool: True if move was successful
        '''
        if not self.is_valid_position(row, col):
            return False
        # Remove piece from old position
        self.board[piece.row][piece.col] = None
        # Place piece at new position
        piece.move(row, col)
        self.board[row][col] = piece
        # Check for king promotion
        if not piece.king:
            if piece.color == (255, 0, 0) and row == ROWS - 1:  # Red reaches bottom
                piece.make_king()
            elif piece.color == (0, 120, 255) and row == 0:  # Blue reaches top
                piece.make_king()
        return True
    def remove_piece(self, row, col):
        '''
        Remove piece from board (for captures).
        Args:
            row (int): Row of piece to remove
            col (int): Column of piece to remove
        '''
        if self.is_valid_position(row, col):
            self.board[row][col] = None
    def draw(self, screen):
        '''
        Draw the board and all pieces.
        Args:
            screen (pygame.Surface): Pygame surface to draw on
        '''
        # Draw board squares
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(screen, color, 
                                (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                 SQUARE_SIZE, SQUARE_SIZE))
        # Draw pieces
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece is not None:
                    # Draw piece circle
                    pygame.draw.circle(screen, piece.color, 
                                      (piece.x, piece.y), 
                                      SQUARE_SIZE // 2 - 10)
                    # Draw king crown
                    if piece.king:
                        # Draw a more visible crown with a border
                        pygame.draw.circle(screen, WHITE, 
                                          (piece.x, piece.y), 
                                          SQUARE_SIZE // 4)
                        pygame.draw.circle(screen, BLACK, 
                                          (piece.x, piece.y), 
                                          SQUARE_SIZE // 4, 2)  # Border
                        # Draw K for king
                        font = pygame.font.Font(None, 24)
                        text = font.render("K", True, BLACK)
                        text_rect = text.get_rect(center=(piece.x, piece.y))
                        screen.blit(text, text_rect)
        # Draw valid move highlights
        for move in self.valid_moves:
            row, col = move
            if isinstance(move, tuple) and len(move) == 2:
                # Create a semi-transparent surface for highlight
                highlight_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(highlight_surface, (255, 255, 0, 128), 
                                (0, 0, SQUARE_SIZE, SQUARE_SIZE))
                screen.blit(highlight_surface, (col * SQUARE_SIZE, row * SQUARE_SIZE))
    def get_all_pieces(self, color):
        '''
        Get all pieces of a specific color.
        Args:
            color (tuple): RGB color of pieces to find
        Returns:
            list: List of Piece objects
        '''
        pieces = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece is not None and piece.color == color:
                    pieces.append(piece)
        return pieces
    def clear_selection(self):
        '''Clear current piece selection and valid moves.'''
        self.selected_piece = None
        self.valid_moves = []