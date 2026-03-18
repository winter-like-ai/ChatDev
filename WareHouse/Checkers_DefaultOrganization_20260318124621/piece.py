'''
Piece class representing individual checkers pieces.
'''
class Piece:
    def __init__(self, row, col, color):
        """
        Initialize a checkers piece.
        Args:
            row: Starting row position
            col: Starting column position
            color: Piece color ('red' or 'black')
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
        """
        Move piece to new position.
        Args:
            row: New row position
            col: New column position
        """
        self.row = row
        self.col = col
    def make_king(self):
        """Promote piece to king."""
        self.king = True
    def __repr__(self):
        """String representation of the piece."""
        return f"{self.color}{'K' if self.king else ''}"