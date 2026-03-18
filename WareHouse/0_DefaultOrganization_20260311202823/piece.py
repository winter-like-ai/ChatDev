'''
Piece class representing a checkers piece.
Handles piece movement logic, king promotion, and valid move calculations.
'''
class Piece:
    def __init__(self, row, col, color):
        """
        Initialize a checkers piece.
        Args:
            row: Row position on board
            col: Column position on board
            color: Piece color ('red' or 'white')
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
        self.x = self.col * 80 + 40
        self.y = self.row * 80 + 40
    def make_king(self):
        """Promote piece to king."""
        self.king = True
    def move(self, row, col):
        """Move piece to new position."""
        self.row = row
        self.col = col
        self.calc_pos()
    def get_valid_moves(self, board):
        """
        Get all valid moves for this piece.
        Args:
            board: Board object
        Returns:
            Dictionary of moves: {position: [captured pieces]}
        """
        moves = {}
        captures = self.get_captures(board)
        if captures:
            # If captures are available, only captures are allowed
            return captures
        # Regular moves (only for non-capture situations)
        directions = self.get_move_directions()
        for direction in directions:
            new_row = self.row + direction[0]
            new_col = self.col + direction[1]
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if board.get_piece(new_row, new_col) is None:
                    moves[(new_row, new_col)] = []
        return moves
    def get_captures(self, board):
        """
        Get all possible capture moves for this piece.
        Args:
            board: Board object
        Returns:
            Dictionary of capture moves: {position: [captured piece]}
        """
        captures = {}
        directions = self.get_move_directions()
        for direction in directions:
            # Check one square ahead
            row_ahead = self.row + direction[0]
            col_ahead = self.col + direction[1]
            # Check two squares ahead (landing position)
            row_land = self.row + direction[0] * 2
            col_land = self.col + direction[1] * 2
            if 0 <= row_ahead < 8 and 0 <= col_ahead < 8 and \
               0 <= row_land < 8 and 0 <= col_land < 8:
                piece_ahead = board.get_piece(row_ahead, col_ahead)
                if piece_ahead is not None and piece_ahead.color != self.color:
                    # Check if landing square is empty
                    if board.get_piece(row_land, col_land) is None:
                        captures[(row_land, col_land)] = [(row_ahead, col_ahead)]
                        # For kings, check for multiple jumps
                        if self.king:
                            # Temporarily remove the captured piece to check further jumps
                            temp_piece = board.board[row_ahead][col_ahead]
                            board.board[row_ahead][col_ahead] = None
                            # Check for additional captures from the new position
                            further_captures = self.get_further_captures(board, row_land, col_land, [(row_ahead, col_ahead)])
                            # Restore the captured piece
                            board.board[row_ahead][col_ahead] = temp_piece
                            # Add further captures to the result
                            for end_pos, captured_list in further_captures.items():
                                captures[end_pos] = captured_list
        return captures
    def get_further_captures(self, board, start_row, start_col, already_captured):
        """
        Recursively find additional captures from a position.
        Args:
            board: Board object
            start_row: Starting row
            start_col: Starting column
            already_captured: List of already captured positions
        Returns:
            Dictionary of further capture moves
        """
        further_captures = {}
        directions = self.get_move_directions()
        for direction in directions:
            row_ahead = start_row + direction[0]
            col_ahead = start_col + direction[1]
            row_land = start_row + direction[0] * 2
            col_land = start_col + direction[1] * 2
            if 0 <= row_ahead < 8 and 0 <= col_ahead < 8 and \
               0 <= row_land < 8 and 0 <= col_land < 8:
                piece_ahead = board.get_piece(row_ahead, col_ahead)
                if piece_ahead is not None and piece_ahead.color != self.color:
                    # Check if this piece hasn't been captured already
                    if (row_ahead, col_ahead) not in already_captured:
                        # Check if landing square is empty
                        if board.get_piece(row_land, col_land) is None:
                            new_captured = already_captured + [(row_ahead, col_ahead)]
                            further_captures[(row_land, col_land)] = new_captured
                            # Check for even further captures
                            temp_piece = board.board[row_ahead][col_ahead]
                            board.board[row_ahead][col_ahead] = None
                            deeper_captures = self.get_further_captures(board, row_land, col_land, new_captured)
                            board.board[row_ahead][col_ahead] = temp_piece
                            for end_pos, captured_list in deeper_captures.items():
                                further_captures[end_pos] = captured_list
        return further_captures
    def get_move_directions(self):
        """
        Get movement directions based on piece type and color.
        Returns:
            List of (row_delta, col_delta) tuples
        """
        if self.king:
            # Kings can move in all 4 diagonal directions
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif self.color == 'red':
            # Red pieces move upward (decreasing row)
            return [(-1, -1), (-1, 1)]
        else:
            # White pieces move downward (increasing row)
            return [(1, -1), (1, 1)]
    def __repr__(self):
        """String representation of piece."""
        king_str = "K" if self.king else ""
        return f"{self.color[0].upper()}{king_str}({self.row},{self.col})"