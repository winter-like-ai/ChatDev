'''
Piece class representing a checkers piece.
Handles piece movement, kinging, and capture logic.
'''
class Piece:
    def __init__(self, row, col, color):
        self.row = row
        self.col = col
        self.color = color
        self.king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        '''Calculate pixel position based on row and column'''
        self.x = self.col * 80 + 40
        self.y = self.row * 80 + 40
    def make_king(self):
        '''Promote piece to king'''
        self.king = True
    def move(self, row, col):
        '''Move piece to new position'''
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        return f"Piece({self.row}, {self.col}, {self.color}, king={self.king})"