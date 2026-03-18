'''
game.py
Core game logic including board management and move validation.
'''
from piece import Piece
from constants import ROWS, COLS, PLAYER_RED, PLAYER_BLUE, EMPTY
class Board:
    def __init__(self):
        """Initialize the checkers board with pieces in starting positions."""
        self.board = []
        self.create_board()
    def create_board(self):
        """Create the initial board setup."""
        self.board = [[EMPTY for _ in range(COLS)] for _ in range(ROWS)]
        # Place red pieces (top 3 rows)
        for row in range(3):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, PLAYER_RED)
        # Place blue pieces (bottom 3 rows)
        for row in range(5, 8):
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, PLAYER_BLUE)
    def get_piece(self, row, col):
        """Get the piece at the specified position."""
        if 0 <= row < ROWS and 0 <= col < COLS:
            piece = self.board[row][col]
            if piece != EMPTY:
                return piece
        return None
    def move_piece(self, piece, row, col):
        """Move a piece to a new position."""
        self.board[piece.row][piece.col] = EMPTY
        self.board[row][col] = piece
        piece.move(row, col)
    def remove_piece(self, row, col):
        """Remove a piece from the board."""
        self.board[row][col] = EMPTY
    def get_all_pieces(self, color):
        """Get all pieces of a specific color."""
        pieces = []
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.get_piece(row, col)
                if piece and piece.color == color:
                    pieces.append(piece)
        return pieces
    def __getitem__(self, index):
        """Allow board[row][col] access."""
        return self.board[index]
class Game:
    def __init__(self):
        """Initialize a new game."""
        self.board = Board()
        self.current_player = PLAYER_RED
        self.winner = None
        self.must_continue_jumping = False
    def switch_turn(self):
        """Switch to the other player's turn."""
        if self.current_player == PLAYER_RED:
            self.current_player = PLAYER_BLUE
        else:
            self.current_player = PLAYER_RED
        # Check for winner
        if self.check_winner():
            self.winner = self.current_player
    def check_winner(self):
        """Check if there's a winner."""
        red_pieces = self.board.get_all_pieces(PLAYER_RED)
        blue_pieces = self.board.get_all_pieces(PLAYER_BLUE)
        if not red_pieces:
            self.winner = PLAYER_BLUE
            return True
        if not blue_pieces:
            self.winner = PLAYER_RED
            return True
        # Check if current player has any valid moves
        for piece in (red_pieces if self.current_player == PLAYER_RED else blue_pieces):
            if self.get_valid_moves(piece.row, piece.col):
                return False
        # No valid moves for current player
        self.winner = PLAYER_BLUE if self.current_player == PLAYER_RED else PLAYER_RED
        return True
    def get_valid_moves(self, row, col):
        """Get all valid moves for a piece at the given position."""
        piece = self.board.get_piece(row, col)
        if not piece or piece.color != self.current_player:
            return []
        # Check for forced captures
        capture_moves = self.get_capture_moves(piece)
        if capture_moves:
            return capture_moves
        # Regular moves (non-capturing)
        moves = self.get_regular_moves(piece)
        return moves
    def get_regular_moves(self, piece):
        """Get regular (non-capturing) moves for a piece."""
        moves = []
        row, col = piece.row, piece.col
        # Determine move directions based on piece type
        if piece.color == PLAYER_RED or piece.king:
            # Red moves down or king moves both directions
            moves.extend(self.check_diagonal(row, col, 1, -1, piece))  # Down-left
            moves.extend(self.check_diagonal(row, col, 1, 1, piece))   # Down-right
        if piece.color == PLAYER_BLUE or piece.king:
            # Blue moves up or king moves both directions
            moves.extend(self.check_diagonal(row, col, -1, -1, piece))  # Up-left
            moves.extend(self.check_diagonal(row, col, -1, 1, piece))   # Up-right
        return moves
    def get_capture_moves(self, piece):
        """Get capturing moves for a piece."""
        moves = []
        row, col = piece.row, piece.col
        # Check all four diagonal directions for captures
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            # Check if there's an opponent piece to capture
            jump_row, jump_col = row + dr, col + dc
            land_row, land_col = row + 2*dr, col + 2*dc
            if (0 <= land_row < ROWS and 0 <= land_col < COLS and
                self.board.get_piece(land_row, land_col) is None):
                jumped_piece = self.board.get_piece(jump_row, jump_col)
                if (jumped_piece and jumped_piece.color != piece.color):
                    moves.append((land_row, land_col))
        return moves
    def check_diagonal(self, row, col, row_dir, col_dir, piece):
        """Check diagonal moves in a specific direction."""
        moves = []
        new_row, new_col = row + row_dir, col + col_dir
        if (0 <= new_row < ROWS and 0 <= new_col < COLS and
            self.board.get_piece(new_row, new_col) is None):
            moves.append((new_row, new_col))
        return moves
    def make_move(self, from_row, from_col, to_row, to_col):
        """Make a move from one position to another."""
        piece = self.board.get_piece(from_row, from_col)
        if not piece:
            return False
        # Move the piece
        self.board.move_piece(piece, to_row, to_col)
        # Check for capture
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        if abs(row_diff) == 2:  # It's a capture
            jumped_row = from_row + row_diff // 2
            jumped_col = from_col + col_diff // 2
            self.board.remove_piece(jumped_row, jumped_col)
            # Check for additional captures
            self.must_continue_jumping = bool(self.get_capture_moves(piece))
        else:
            self.must_continue_jumping = False
        # Check for kinging
        if not piece.king:
            if (piece.color == PLAYER_RED and to_row == 7) or \
               (piece.color == PLAYER_BLUE and to_row == 0):
                piece.make_king()
        return True