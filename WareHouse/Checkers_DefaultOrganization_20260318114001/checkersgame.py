'''
game_logic.py
Core game logic for Checkers including board state, move validation,
and game rules implementation.
'''
class Piece:
    """Represents a checkers piece on the board."""
    def __init__(self, color, row, col, is_king=False):
        """
        Initialize a checkers piece.
        Args:
            color (str): 'red' or 'black'
            row (int): Row position on board (0-7)
            col (int): Column position on board (0-7)
            is_king (bool): Whether the piece is a king
        """
        self.color = color
        self.row = row
        self.col = col
        self.is_king = is_king
    def __repr__(self):
        return f"Piece({self.color}, ({self.row},{self.col}), king={self.is_king})"
    def get_pos(self):
        """Get board position as tuple."""
        return (self.row, self.col)
    def move_to(self, row, col):
        """Move piece to new position."""
        self.row = row
        self.col = col
    def make_king(self):
        """Promote piece to king."""
        self.is_king = True
class Board:
    """Manages the checkers board state and piece positions."""
    def __init__(self):
        """Initialize an empty 8x8 board."""
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.initialize_pieces()
    def initialize_pieces(self):
        """Set up initial piece positions on the board."""
        # Place black pieces (top three rows)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('black', row, col)
        # Place red pieces (bottom three rows)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('red', row, col)
    def get_piece(self, row, col):
        """Get piece at specified position."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    def set_piece(self, row, col, piece):
        """Place piece at specified position."""
        if 0 <= row < 8 and 0 <= col < 8:
            self.board[row][col] = piece
            if piece:
                piece.row = row
                piece.col = col
    def remove_piece(self, row, col):
        """Remove piece from board."""
        self.board[row][col] = None
    def get_all_pieces(self, color=None):
        """Get all pieces, optionally filtered by color."""
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    if color is None or piece.color == color:
                        pieces.append(piece)
        return pieces
    def is_empty(self, row, col):
        """Check if a position is empty."""
        return self.get_piece(row, col) is None
    def is_within_bounds(self, row, col):
        """Check if position is within board bounds."""
        return 0 <= row < 8 and 0 <= col < 8
class CheckersGame:
    """Main game controller implementing checkers rules and logic."""
    def __init__(self):
        """Initialize a new checkers game."""
        self.board = Board()
        self.current_player = 'red'  # Red starts first
        self.selected_piece = None
        self.valid_moves = []
        self.must_capture = False
        self.game_over = False
        self.winner = None
    def switch_player(self):
        """Switch to the other player."""
        self.current_player = 'black' if self.current_player == 'red' else 'red'
        self.selected_piece = None
        self.valid_moves = []
        self.check_mandatory_captures()
    def check_mandatory_captures(self):
        """Check if current player has any mandatory capture moves."""
        self.must_capture = False
        pieces = self.board.get_all_pieces(self.current_player)
        for piece in pieces:
            capture_moves = self.get_valid_captures(piece)
            if capture_moves:
                self.must_capture = True
                break
    def get_valid_moves(self, piece):
        """
        Get all valid moves for a given piece.
        Args:
            piece (Piece): The piece to check moves for
        Returns:
            list: List of valid (row, col) destination positions
        """
        if not piece or piece.color != self.current_player:
            return []
        moves = []
        row, col = piece.row, piece.col
        # Regular pieces can only move forward, kings can move both directions
        directions = []
        if piece.is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif piece.color == 'red':
            directions = [(-1, -1), (-1, 1)]  # Red moves upward
        else:  # black
            directions = [(1, -1), (1, 1)]    # Black moves downward
        # Check regular moves
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if self.board.is_within_bounds(new_row, new_col) and self.board.is_empty(new_row, new_col):
                moves.append((new_row, new_col))
        # Check capture moves
        capture_moves = self.get_valid_captures(piece)
        moves.extend(capture_moves)
        return moves
    def get_valid_captures(self, piece):
        """
        Get all valid capture moves for a given piece.
        Args:
            piece (Piece): The piece to check captures for
        Returns:
            list: List of valid capture destination positions
        """
        captures = []
        row, col = piece.row, piece.col
        # Check all four diagonal directions
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            # Check if there's an opponent piece to jump over
            jump_row, jump_col = row + dr, col + dc
            land_row, land_col = row + 2*dr, col + 2*dc
            if (self.board.is_within_bounds(jump_row, jump_col) and 
                self.board.is_within_bounds(land_row, land_col)):
                jumped_piece = self.board.get_piece(jump_row, jump_col)
                if (jumped_piece and jumped_piece.color != piece.color and 
                    self.board.is_empty(land_row, land_col)):
                    # For regular pieces, ensure they're moving in the right direction
                    if not piece.is_king:
                        if piece.color == 'red' and dr > 0:  # Red moves upward
                            continue
                        if piece.color == 'black' and dr < 0:  # Black moves downward
                            continue
                    captures.append((land_row, land_col))
        return captures
    def select_piece(self, row, col):
        """
        Select a piece to move.
        Args:
            row (int): Row of selected piece
            col (int): Column of selected piece
        Returns:
            bool: True if piece was successfully selected
        """
        piece = self.board.get_piece(row, col)
        if not piece or piece.color != self.current_player:
            return False
        # If capture is mandatory, only select pieces that can capture
        if self.must_capture:
            capture_moves = self.get_valid_captures(piece)
            if not capture_moves:
                return False
        self.selected_piece = piece
        self.valid_moves = self.get_valid_moves(piece)
        # If capture is mandatory, filter to only capture moves
        if self.must_capture:
            self.valid_moves = [move for move in self.valid_moves 
                              if abs(move[0] - row) == 2]  # Capture moves are 2 squares away
        return True
    def make_move(self, to_row, to_col):
        """
        Move selected piece to destination.
        Args:
            to_row (int): Destination row
            to_col (int): Destination column
        Returns:
            bool: True if move was successful
        """
        if not self.selected_piece or (to_row, to_col) not in self.valid_moves:
            return False
        from_row, from_col = self.selected_piece.row, self.selected_piece.col
        # Move the piece
        self.board.set_piece(to_row, to_col, self.selected_piece)
        self.board.remove_piece(from_row, from_col)
        # Check if this was a capture move
        if abs(to_row - from_row) == 2:
            # Remove the captured piece (middle square)
            captured_row = (from_row + to_row) // 2
            captured_col = (from_col + to_col) // 2
            self.board.remove_piece(captured_row, captured_col)
            # Check for additional captures (multiple jumps)
            additional_captures = self.get_valid_captures(self.selected_piece)
            if additional_captures:
                # Player gets another turn for multiple jumps
                self.selected_piece = self.board.get_piece(to_row, to_col)
                self.valid_moves = additional_captures
                return True
        # Check for king promotion
        if not self.selected_piece.is_king:
            if (self.selected_piece.color == 'red' and to_row == 0) or \
               (self.selected_piece.color == 'black' and to_row == 7):
                self.selected_piece.make_king()
        # Switch to next player
        self.switch_player()
        # Check for game over
        self.check_game_over()
        return True
    def check_game_over(self):
        """Check if the game is over and determine winner."""
        red_pieces = self.board.get_all_pieces('red')
        black_pieces = self.board.get_all_pieces('black')
        # Check if a player has no pieces
        if not red_pieces:
            self.game_over = True
            self.winner = 'black'
        elif not black_pieces:
            self.game_over = True
            self.winner = 'red'
        # Check if current player has no valid moves
        if not self.game_over:
            current_pieces = self.board.get_all_pieces(self.current_player)
            has_valid_move = False
            for piece in current_pieces:
                if self.get_valid_moves(piece):
                    has_valid_move = True
                    break
            if not has_valid_move:
                self.game_over = True
                self.winner = 'black' if self.current_player == 'red' else 'red'
    def get_game_state(self):
        """Get current game state as string."""
        if self.game_over:
            return f"Game Over! Winner: {self.winner.capitalize()}"
        else:
            return f"Current Player: {self.current_player.capitalize()}"
    def get_move_notation(self, from_pos, to_pos):
        """
        Convert move positions to algebraic notation.
        Args:
            from_pos (tuple): (row, col) of starting position
            to_pos (tuple): (row, col) of destination position
        Returns:
            str: Move in notation format (e.g., "C3-D4")
        """
        def pos_to_notation(row, col):
            # Convert to algebraic notation: columns A-H, rows 1-8
            col_char = chr(ord('A') + col)
            row_num = 8 - row  # Board is drawn with row 0 at top
            return f"{col_char}{row_num}"
        from_notation = pos_to_notation(from_pos[0], from_pos[1])
        to_notation = pos_to_notation(to_pos[0], to_pos[1])
        return f"{from_notation}-{to_notation}"