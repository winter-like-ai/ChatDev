'''
piece.py
Piece class representing a checkers piece.
'''
class Piece:
    def __init__(self, row, col, color):
        """
        Initialize a checkers piece.
        Args:
            row: Row position on the board (0-7)
            col: Column position on the board (0-7)
            color: Color of the piece (RED or BLUE)
        """
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate the pixel position of the piece."""
        from constants import SQUARE_SIZE
        self.x = self.col * SQUARE_SIZE + SQUARE_SIZE // 2
        self.y = self.row * SQUARE_SIZE + SQUARE_SIZE // 2
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
        color_str = "R" if self.color == "RED" else "B"
        king_str = "K" if self.king else ""
        return f"{color_str}{king_str}"