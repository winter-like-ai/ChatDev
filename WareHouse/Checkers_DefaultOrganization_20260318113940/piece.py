'''
piece.py
Piece class representing individual checkers pieces.
'''
class Piece:
    """Represents a checkers piece on the board."""
    def __init__(self, row, col, color):
        """
        Initialize a piece.
        Args:
            row: Row position on the board (0-7)
            col: Column position on the board (0-7)
            color: Piece color (1 for player one, 2 for player two)
        """
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate pixel position based on board coordinates."""
        self.x = self.col * 80 + 40  # 80 is SQUARE_SIZE, 40 is half
        self.y = self.row * 80 + 40
    def make_king(self):
        """Promote the piece to a king."""
        self.king = True
    def move(self, row, col):
        """Move the piece to a new position."""
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        """String representation of the piece."""
        color_str = "Red" if self.color == 1 else "Blue"
        king_str = " (King)" if self.king else ""
        return f"{color_str} Piece at ({self.row}, {self.col}){king_str}"