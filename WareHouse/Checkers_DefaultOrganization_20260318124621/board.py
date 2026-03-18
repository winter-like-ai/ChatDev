'''
Board class representing the Checkers game board.
Manages piece positions, moves, and board state.
'''
class Board:
    def __init__(self):
        """Initialize an 8x8 Checkers board with starting positions."""
        self.board = []
        self.red_left = self.black_left = 12
        self.red_kings = self.black_kings = 0
        self.create_board()
    def create_board(self):
        """Create the initial board setup with pieces in starting positions."""
        self.board = [[0 for _ in range(8)] for _ in range(8)]
        # Place red pieces (top three rows)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, 'red')
        # Place black pieces (bottom three rows)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, 'black')
    def get_piece(self, row, col):
        """
        Get the piece at the specified position.
        Args:
            row: Row index
            col: Column index
        Returns:
            Piece object or 0 if empty
        """
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return 0
    def move(self, piece, row, col):
        """
        Move a piece to a new position.
        Args:
            piece: Piece to move
            row: Target row
            col: Target column
        """
        # Clear old position
        self.board[piece.row][piece.col] = 0
        # Update piece position
        piece.move(row, col)
        # Set new position
        self.board[row][col] = piece
    def remove(self, row, col):
        """
        Remove a piece from the board.
        Args:
            row: Row of piece to remove
            col: Column of piece to remove
        """
        piece = self.get_piece(row, col)
        if piece != 0:
            if piece.color == 'red':
                self.red_left -= 1
                if piece.king:
                    self.red_kings -= 1
            else:
                self.black_left -= 1
                if piece.king:
                    self.black_kings -= 1
            self.board[row][col] = 0
    def promote_to_king(self, piece):
        """
        Promote a piece to king.
        Args:
            piece: Piece to promote
        """
        piece.make_king()
        if piece.color == 'red':
            self.red_kings += 1
        else:
            self.black_kings += 1
    def should_promote(self, piece, row):
        """
        Check if a piece should be promoted to king.
        Args:
            piece: Piece to check
            row: Current row position
        Returns:
            bool: True if should be promoted
        """
        if piece.color == 'red' and row == 7:
            return True
        if piece.color == 'black' and row == 0:
            return True
        return False
    def get_valid_moves(self, piece):
        """
        Get all valid moves for a piece.
        Args:
            piece: Piece to get moves for
        Returns:
            dict: Dictionary of valid moves with move information
        """
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == 'black' or piece.king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == 'red' or piece.king:
            moves.update(self._traverse_left(row + 1, min(row + 3, 8), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, 8), 1, piece.color, right))
        return moves
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        """
        Traverse left diagonally to find valid moves.
        Args:
            start: Starting row
            stop: Stopping row
            step: Direction step
            color: Piece color
            left: Left column boundary
            skipped: List of captured pieces
        Returns:
            dict: Valid moves in left direction
        """
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, left)] = {'captured': last + skipped}
                else:
                    moves[(r, left)] = {'captured': last}
                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, 8)
                    moves.update(self._traverse_left(r + step, row, step, color, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, left + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [(r, left)]
            left -= 1
        return moves
    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        """
        Traverse right diagonally to find valid moves.
        Args:
            start: Starting row
            stop: Stopping row
            step: Direction step
            color: Piece color
            right: Right column boundary
            skipped: List of captured pieces
        Returns:
            dict: Valid moves in right direction
        """
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= 8:
                break
            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                elif skipped:
                    moves[(r, right)] = {'captured': last + skipped}
                else:
                    moves[(r, right)] = {'captured': last}
                if last:
                    if step == -1:
                        row = max(r - 3, 0)
                    else:
                        row = min(r + 3, 8)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [(r, right)]
            right += 1
        return moves
    def has_valid_moves(self, color):
        """
        Check if a player has any valid moves.
        Args:
            color: Player color to check
        Returns:
            bool: True if player has valid moves
        """
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece != 0 and piece.color == color:
                    if self.get_valid_moves(piece):
                        return True
        return False
    def get_all_pieces(self, color):
        """
        Get all pieces of a specific color.
        Args:
            color: Color of pieces to get
        Returns:
            list: List of pieces
        """
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece != 0 and piece.color == color:
                    pieces.append(piece)
        return pieces