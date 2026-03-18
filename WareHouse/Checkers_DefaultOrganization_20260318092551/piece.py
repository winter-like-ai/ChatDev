'''
Piece class representing a checkers piece with position, color, and king status.
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
        '''Calculate pixel position based on board coordinates'''
        from constants import SQUARE_SIZE
        self.x = SQUARE_SIZE * self.col + SQUARE_SIZE // 2
        self.y = SQUARE_SIZE * self.row + SQUARE_SIZE // 2
    def make_king(self):
        '''Promote piece to king'''
        self.king = True
    def move(self, row, col):
        '''Move piece to new position'''
        self.row = row
        self.col = col
        self.calc_pos()
    def get_valid_moves(self, board):
        '''Get all valid moves for this piece'''
        moves = {}
        left = self.col - 1
        right = self.col + 1
        row = self.row
        if self.color == "red" or self.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, board, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, board, right))
        if self.color == "blue" or self.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, 8), 1, board, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, 8), 1, board, right))
        return moves
    def _traverse_left(self, start, stop, step, board, left, skipped=[]):
        '''Traverse diagonally left to find valid moves'''
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            current = board.get_piece(r, left)
            if current is None:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = last + skipped
                else:
                    moves[(r, left)] = last
                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, 7)
                    moves.update(self._traverse_left(r + step, row, step, board, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, board, left + 1, skipped=last))
                break
            elif current.color == self.color:
                break
            else:
                last = [current]
            left -= 1
        return moves
    def _traverse_right(self, start, stop, step, board, right, skipped=[]):
        '''Traverse diagonally right to find valid moves'''
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= 8:
                break
            current = board.get_piece(r, right)
            if current is None:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = last + skipped
                else:
                    moves[(r, right)] = last
                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, 7)
                    moves.update(self._traverse_left(r + step, row, step, board, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, board, right + 1, skipped=last))
                break
            elif current.color == self.color:
                break
            else:
                last = [current]
            right += 1
        return moves
    def __repr__(self):
        return f"Piece({self.row}, {self.col}, {self.color}, king={self.king})"