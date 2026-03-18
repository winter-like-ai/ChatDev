'''
Piece class for Checkers.
Represents individual checkers pieces.
'''
class Piece:
    """Represents a checkers piece."""
    def __init__(self, row, col, color):
        """
        Initialize a checkers piece.
        Args:
            row: Row position on board (0-7)
            col: Column position on board (0-7)
            color: 'red' or 'white'
        """
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        # Set direction based on color
        if self.color == 'red':
            self.direction = 1  # Moves downward
        else:
            self.direction = -1  # Moves upward
    def move(self, row, col):
        """Move piece to new position."""
        self.row = row
        self.col = col
    def make_king(self):
        """Promote piece to king."""
        self.king = True
    def __repr__(self):
        """String representation of the piece."""
        king_str = "K" if self.king else ""
        return f"{self.color[0].upper()}{king_str}({self.row},{self.col})"