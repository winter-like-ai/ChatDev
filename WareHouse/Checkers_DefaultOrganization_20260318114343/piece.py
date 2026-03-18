'''
piece.py
Piece class representing a checkers piece with movement logic.
'''
from constants import REGULAR, KING, PLAYER_ONE, PLAYER_TWO, SQUARE_SIZE
class Piece:
    def __init__(self, row, col, player):
        """
        Initialize a checkers piece.
        Args:
            row: Row position on the board
            col: Column position on the board
            player: Player number (PLAYER_ONE or PLAYER_TWO)
        """
        self.row = row
        self.col = col
        self.player = player
        self.type = REGULAR
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate pixel position based on board coordinates."""
        self.x = self.col * SQUARE_SIZE + SQUARE_SIZE // 2
        self.y = self.row * SQUARE_SIZE + SQUARE_SIZE // 2
    def make_king(self):
        """Promote the piece to a king."""
        self.type = KING
    def is_king(self):
        """Check if the piece is a king."""
        return self.type == KING
    def get_valid_moves(self, board):
        """
        Get all valid moves for this piece.
        Args:
            board: The game board
        Returns:
            Dictionary of valid moves and captures
        """
        moves = {}
        captures = {}
        # Determine movement direction based on player and piece type
        if self.player == PLAYER_ONE or self.is_king():
            moves.update(self._get_moves_in_direction(board, -1))  # Up
            captures.update(self._get_captures_in_direction(board, -1))
        if self.player == PLAYER_TWO or self.is_king():
            moves.update(self._get_moves_in_direction(board, 1))   # Down
            captures.update(self._get_captures_in_direction(board, 1))
        return moves, captures
    def _get_moves_in_direction(self, board, row_dir):
        """Get regular moves in a specific direction."""
        moves = {}
        # Left diagonal
        new_row = self.row + row_dir
        new_col = self.col - 1
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board.get_piece(new_row, new_col) == 0:
                moves[(new_row, new_col)] = []
        # Right diagonal
        new_col = self.col + 1
        if 0 <= new_row < 8 and 0 <= new_col < 8:
            if board.get_piece(new_row, new_col) == 0:
                moves[(new_row, new_col)] = []
        return moves
    def _get_captures_in_direction(self, board, row_dir):
        """Get capture moves in a specific direction."""
        captures = {}
        # Check both diagonals for captures
        for col_dir in [-1, 1]:
            jump_row = self.row + row_dir
            jump_col = self.col + col_dir
            land_row = self.row + (2 * row_dir)
            land_col = self.col + (2 * col_dir)
            if (0 <= land_row < 8 and 0 <= land_col < 8 and
                0 <= jump_row < 8 and 0 <= jump_col < 8):
                jumped_piece = board.get_piece(jump_row, jump_col)
                if (jumped_piece != 0 and jumped_piece.player != self.player and
                    board.get_piece(land_row, land_col) == 0):
                    captures[(land_row, land_col)] = [(jump_row, jump_col)]
                    # Check for multiple jumps
                    temp_piece = Piece(land_row, land_col, self.player)
                    temp_piece.type = self.type
                    # For kings, check all possible directions for further captures
                    if self.is_king():
                        for next_dir in [-1, 1]:
                            further_captures = temp_piece._get_captures_in_direction(board, next_dir)
                            for key, value in further_captures.items():
                                captures[key] = [(jump_row, jump_col)] + value
                    else:
                        further_captures = temp_piece._get_captures_in_direction(board, row_dir)
                        for key, value in further_captures.items():
                            captures[key] = [(jump_row, jump_col)] + value
        return captures
    def move(self, row, col):
        """Move the piece to a new position."""
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        return f"Piece(player={self.player}, type={'KING' if self.is_king() else 'REGULAR'}, pos=({self.row}, {self.col}))"