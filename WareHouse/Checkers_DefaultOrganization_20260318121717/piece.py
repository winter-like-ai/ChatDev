'''
Piece class representing a checkers piece.
'''
class Piece:
    def __init__(self, color, row, col):
        """
        Initialize a checkers piece.
        Args:
            color (str): 'red' or 'white'
            row (int): Row position on board
            col (int): Column position on board
        """
        self.color = color
        self.row = row
        self.col = col
        self.king = False
        self.direction = 1 if color == 'red' else -1  # Red moves down, white moves up
    def make_king(self):
        """Promote piece to king."""
        self.king = True
    def get_possible_moves(self, board):
        """
        Get all possible moves for this piece.
        Args:
            board (Board): The game board
        Returns:
            list: List of (row, col) tuples for possible moves
        """
        moves = []
        # Regular pieces can only move forward, kings can move both directions
        directions = [self.direction]
        if self.king:
            directions = [1, -1]
        for direction in directions:
            # Regular moves (non-capturing)
            new_row = self.row + direction
            for col_offset in [-1, 1]:
                new_col = self.col + col_offset
                if board.is_valid_position(new_row, new_col):
                    if board.get_piece(new_row, new_col) is None:
                        moves.append((new_row, new_col))
            # Capture moves
            for col_offset in [-1, 1]:
                jump_row = self.row + direction
                jump_col = self.col + col_offset
                land_row = self.row + (2 * direction)
                land_col = self.col + (2 * col_offset)
                if (board.is_valid_position(jump_row, jump_col) and 
                    board.is_valid_position(land_row, land_col)):
                    jumped_piece = board.get_piece(jump_row, jump_col)
                    landing_piece = board.get_piece(land_row, land_col)
                    if (jumped_piece and jumped_piece.color != self.color and 
                        landing_piece is None):
                        moves.append((land_row, land_col))
        return moves
    def get_possible_captures(self, board):
        """
        Get all possible capture moves for this piece.
        Args:
            board (Board): The game board
        Returns:
            list: List of (row, col) tuples for capture moves
        """
        captures = []
        directions = [self.direction]
        if self.king:
            directions = [1, -1]
        for direction in directions:
            for col_offset in [-1, 1]:
                jump_row = self.row + direction
                jump_col = self.col + col_offset
                land_row = self.row + (2 * direction)
                land_col = self.col + (2 * col_offset)
                if (board.is_valid_position(jump_row, jump_col) and 
                    board.is_valid_position(land_row, land_col)):
                    jumped_piece = board.get_piece(jump_row, jump_col)
                    landing_piece = board.get_piece(land_row, land_col)
                    if (jumped_piece and jumped_piece.color != self.color and 
                        landing_piece is None):
                        captures.append((land_row, land_col))
        return captures
    def __repr__(self):
        """String representation of the piece."""
        king_str = "K" if self.king else ""
        return f"{self.color[0].upper()}{king_str}({self.row},{self.col})"