'''
Piece class representing a checkers piece.
Handles piece movement, capturing, and king promotion logic.
'''
from constants import SQUARE_SIZE
class Piece:
    def __init__(self, color, row, col):
        '''
        Initialize a checkers piece.
        Args:
            color (tuple): RGB color of the piece
            row (int): Row position on board
            col (int): Column position on board
        '''
        self.color = color
        self.row = row
        self.col = col
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        '''Calculate pixel position based on board position.'''
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2
    def make_king(self):
        '''Promote piece to king.'''
        self.king = True
    def move(self, row, col):
        '''Move piece to new position.'''
        self.row = row
        self.col = col
        self.calc_pos()
    def get_possible_moves(self, board):
        '''
        Get all possible regular moves for this piece.
        Args:
            board (Board): The game board
        Returns:
            list: List of (row, col) tuples representing valid moves
        '''
        moves = []
        direction = 1 if self.color == (255, 0, 0) else -1  # Red moves down, Blue moves up
        # Regular pieces can only move forward, kings can move both directions
        directions = [direction]
        if self.king:
            directions = [1, -1]
        for d in directions:
            # Check diagonal moves
            for dc in [-1, 1]:
                new_row = self.row + d
                new_col = self.col + dc
                if board.is_valid_position(new_row, new_col):
                    if board.get_piece(new_row, new_col) is None:
                        moves.append((new_row, new_col))
        return moves
    def get_possible_captures(self, board):
        '''
        Get all possible capture moves for this piece.
        Args:
            board (Board): The game board
        Returns:
            list: List of ((capture_row, capture_col), (land_row, land_col)) tuples
        '''
        captures = []
        direction = 1 if self.color == (255, 0, 0) else -1
        # Regular pieces can only capture forward, kings can capture both directions
        directions = [direction]
        if self.king:
            directions = [1, -1]
        for d in directions:
            for dc in [-1, 1]:
                # Position of piece to capture
                capture_row = self.row + d
                capture_col = self.col + dc
                # Landing position after capture
                land_row = self.row + (2 * d)
                land_col = self.col + (2 * dc)
                if (board.is_valid_position(capture_row, capture_col) and 
                    board.is_valid_position(land_row, land_col)):
                    captured_piece = board.get_piece(capture_row, capture_col)
                    landing_piece = board.get_piece(land_row, land_col)
                    if (captured_piece is not None and 
                        captured_piece.color != self.color and 
                        landing_piece is None):
                        captures.append(((capture_row, capture_col), (land_row, land_col)))
        return captures
    def __repr__(self):
        '''String representation of the piece.'''
        color_str = "Red" if self.color == (255, 0, 0) else "Blue"
        king_str = " King" if self.king else ""
        return f"{color_str}{king_str} at ({self.row}, {self.col})"