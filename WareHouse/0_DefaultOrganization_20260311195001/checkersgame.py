'''
checkersgame.py
Core game logic for Checkers including board state,
move validation, and game rules.
'''
class Piece:
    """Represents a checkers piece."""
    def __init__(self, color, row, col, is_king=False):
        """
        Initialize a checkers piece.
        Args:
            color (str): 'red' or 'white'
            row (int): Row position on board
            col (int): Column position on board
            is_king (bool): Whether the piece is a king
        """
        self.color = color
        self.row = row
        self.col = col
        self.is_king = is_king
    def __repr__(self):
        return f"Piece({self.color}, ({self.row},{self.col}), king={self.is_king})"
class Board:
    """Manages the checkers board state."""
    def __init__(self):
        """Initialize an empty 8x8 board."""
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.initialize_pieces()
    def initialize_pieces(self):
        """Set up initial piece positions on the board."""
        # Place red pieces (top three rows)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('red', row, col)
        # Place white pieces (bottom three rows)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('white', row, col)
    def get_piece(self, row, col):
        """Get piece at specified position."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    def move_piece(self, from_row, from_col, to_row, to_col):
        """
        Move a piece from one position to another.
        Returns:
            Piece: The piece that was moved, or None if no piece at source
        """
        piece = self.board[from_row][from_col]
        if piece:
            piece.row = to_row
            piece.col = to_col
            self.board[to_row][to_col] = piece
            self.board[from_row][from_col] = None
            return piece
        return None
    def remove_piece(self, row, col):
        """Remove a piece from the board."""
        self.board[row][col] = None
    def king_piece(self, row, col):
        """Convert a piece to a king."""
        piece = self.get_piece(row, col)
        if piece:
            piece.is_king = True
    def get_all_pieces(self, color=None):
        """Get all pieces on the board, optionally filtered by color."""
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    if color is None or piece.color == color:
                        pieces.append(piece)
        return pieces
class CheckersGame:
    """Main game controller implementing checkers rules."""
    def __init__(self):
        """Initialize a new checkers game."""
        self.board = Board()
        self.current_player = 'red'  # Red starts
        self.selected_piece = None
        self.valid_moves = []
        self.must_capture = False
        self.game_over = False
        self.winner = None
    def switch_player(self):
        """Switch to the other player."""
        self.current_player = 'white' if self.current_player == 'red' else 'red'
        self.selected_piece = None
        self.valid_moves = []
        self.check_mandatory_captures()
    def check_mandatory_captures(self):
        """Check if current player has any mandatory captures."""
        self.must_capture = False
        pieces = self.board.get_all_pieces(self.current_player)
        for piece in pieces:
            captures = self.get_valid_captures(piece)
            if captures:
                self.must_capture = True
                break
    def get_valid_moves(self, piece):
        """
        Get all valid moves for a given piece.
        Args:
            piece (Piece): The piece to check moves for
        Returns:
            list: List of valid (row, col) move positions
        """
        if not piece or piece.color != self.current_player:
            return []
        moves = []
        row, col = piece.row, piece.col
        # Determine move directions based on piece type and color
        if piece.is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif piece.color == 'red':
            directions = [(1, -1), (1, 1)]  # Red moves down
        else:  # white
            directions = [(-1, -1), (-1, 1)]  # White moves up
        # Check regular moves
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if self.board.get_piece(new_row, new_col) is None:
                    moves.append((new_row, new_col))
        # Check capture moves
        capture_moves = self.get_valid_captures(piece)
        moves.extend(capture_moves)
        # If captures are mandatory, only return capture moves
        if self.must_capture and capture_moves:
            return capture_moves
        return moves
    def get_valid_captures(self, piece):
        """
        Get all valid capture moves for a given piece.
        Args:
            piece (Piece): The piece to check captures for
        Returns:
            list: List of valid (row, col) capture positions
        """
        captures = []
        row, col = piece.row, piece.col
        # Determine capture directions
        if piece.is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif piece.color == 'red':
            directions = [(1, -1), (1, 1)]
        else:  # white
            directions = [(-1, -1), (-1, 1)]
        for dr, dc in directions:
            # Check if there's an opponent piece to jump over
            jump_row, jump_col = row + dr, col + dc
            land_row, land_col = row + 2*dr, col + 2*dc
            if (0 <= land_row < 8 and 0 <= land_col < 8 and
                self.board.get_piece(land_row, land_col) is None):
                jumped_piece = self.board.get_piece(jump_row, jump_col)
                if jumped_piece and jumped_piece.color != piece.color:
                    captures.append((land_row, land_col))
        return captures
    def select_piece(self, row, col):
        """
        Select a piece at the given position.
        Returns:
            bool: True if piece was selected, False otherwise
        """
        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.current_player:
            self.selected_piece = piece
            self.valid_moves = self.get_valid_moves(piece)
            return True
        return False
    def make_move(self, to_row, to_col):
        """
        Make a move to the specified position.
        Args:
            to_row (int): Destination row
            to_col (int): Destination column
        Returns:
            bool: True if move was successful, False otherwise
            list: List of captured pieces positions
        """
        if not self.selected_piece:
            return False, []
        # Check if move is valid
        if (to_row, to_col) not in self.valid_moves:
            return False, []
        from_row, from_col = self.selected_piece.row, self.selected_piece.col
        captured = []
        # Check if this is a capture move
        if abs(to_row - from_row) == 2:
            # Calculate captured piece position
            cap_row = (from_row + to_row) // 2
            cap_col = (from_col + to_col) // 2
            # Remove captured piece
            self.board.remove_piece(cap_row, cap_col)
            captured.append((cap_row, cap_col))
        # Move the piece
        self.board.move_piece(from_row, from_col, to_row, to_col)
        # Check for kinging
        if not self.selected_piece.is_king:
            if (self.selected_piece.color == 'red' and to_row == 7) or \
               (self.selected_piece.color == 'white' and to_row == 0):
                self.board.king_piece(to_row, to_col)
        # Check for additional captures
        if captured:
            # Check if same piece can capture again
            self.selected_piece = self.board.get_piece(to_row, to_col)
            additional_captures = self.get_valid_captures(self.selected_piece)
            if additional_captures:
                self.valid_moves = additional_captures
                return True, captured
        # Switch player if no more captures
        self.switch_player()
        # Check for game over
        self.check_game_over()
        return True, captured
    def check_game_over(self):
        """Check if the game is over and set winner."""
        red_pieces = self.board.get_all_pieces('red')
        white_pieces = self.board.get_all_pieces('white')
        if not red_pieces:
            self.game_over = True
            self.winner = 'white'
        elif not white_pieces:
            self.game_over = True
            self.winner = 'red'
        else:
            # Check if current player has any valid moves
            current_pieces = self.board.get_all_pieces(self.current_player)
            has_moves = False
            for piece in current_pieces:
                if self.get_valid_moves(piece):
                    has_moves = True
                    break
            if not has_moves:
                self.game_over = True
                self.winner = 'white' if self.current_player == 'red' else 'red'
    def get_game_state(self):
        """
        Get current game state as a string.
        Returns:
            str: Current game state description
        """
        if self.game_over:
            return f"Game Over! {self.winner.capitalize()} wins!"
        else:
            status = f"{self.current_player.capitalize()}'s turn"
            if self.must_capture:
                status += " (Must capture!)"
            return status
    def get_move_notation(self, from_row, from_col, to_row, to_col):
        """
        Convert move to algebraic notation.
        Args:
            from_row, from_col: Starting position
            to_row, to_col: Ending position
        Returns:
            str: Move in notation format (e.g., "a3-b4")
        """
        cols = 'abcdefgh'
        from_pos = f"{cols[from_col]}{8-from_row}"
        to_pos = f"{cols[to_col]}{8-to_row}"
        return f"{from_pos}-{to_pos}"