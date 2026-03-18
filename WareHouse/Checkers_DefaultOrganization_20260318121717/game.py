'''
Game class managing game state, turns, and rules.
'''
from board import Board
class Game:
    def __init__(self):
        """Initialize a new game."""
        self.board = Board()
        self.turn = 'red'  # Red starts
        self.selected_piece = None
        self.valid_moves = []
        self.last_move = None
        self.winner = None
        self.must_capture = False
        self.capture_chain = False
    def change_turn(self):
        """Switch to the other player's turn."""
        self.turn = 'white' if self.turn == 'red' else 'red'
        self.selected_piece = None
        self.valid_moves = []
        self.must_capture = False
        self.capture_chain = False
    def select_piece(self, row, col):
        """
        Select a piece to move.
        Args:
            row (int): Row index
            col (int): Column index
        Returns:
            bool: True if piece was successfully selected
        """
        piece = self.board.get_piece(row, col)
        if piece and piece.color == self.turn:
            self.selected_piece = (row, col)
            self.valid_moves = self.get_valid_moves(row, col)
            return True
        return False
    def get_valid_moves(self, row, col):
        """
        Get all valid moves for a piece at given position.
        Args:
            row (int): Row index
            col (int): Column index
        Returns:
            list: List of valid (row, col) moves
        """
        piece = self.board.get_piece(row, col)
        if not piece or piece.color != self.turn:
            return []
        # Check if any captures are available for current player
        all_captures = self.get_all_captures_for_player(self.turn)
        if all_captures:
            # If captures are available, only allow capturing moves
            piece_captures = piece.get_possible_captures(self.board)
            return piece_captures if piece_captures else []
        else:
            # Otherwise, allow all moves
            return piece.get_possible_moves(self.board)
    def get_all_captures_for_player(self, color):
        """
        Get all possible captures for a player.
        Args:
            color (str): 'red' or 'white'
        Returns:
            list: List of all possible capture moves for the player
        """
        captures = []
        pieces = self.board.get_all_pieces(color)
        for piece in pieces:
            piece_captures = piece.get_possible_captures(self.board)
            if piece_captures:
                captures.extend([(piece.row, piece.col, move[0], move[1]) 
                               for move in piece_captures])
        return captures
    def make_move(self, from_pos, to_pos):
        """
        Execute a move from one position to another.
        Args:
            from_pos (tuple): (row, col) of piece to move
            to_pos (tuple): (row, col) of destination
        Returns:
            bool: True if move was successful
        """
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        piece = self.board.get_piece(from_row, from_col)
        if not piece or piece.color != self.turn:
            return False
        valid_moves = self.get_valid_moves(from_row, from_col)
        if (to_row, to_col) not in valid_moves:
            return False
        # Execute the move
        captured = self.board.move_piece(piece, to_row, to_col)
        self.last_move = (from_row, from_col, to_row, to_col)
        # Check for multiple jumps (capture chain)
        if captured and piece.get_possible_captures(self.board):
            # Piece can capture again
            self.capture_chain = True
            self.selected_piece = (to_row, to_col)
            self.valid_moves = piece.get_possible_captures(self.board)
        else:
            # End turn
            self.check_winner()
            if not self.winner:
                self.change_turn()
        return True
    def check_winner(self):
        """Check if the game has ended and determine winner."""
        red_pieces = self.board.get_all_pieces('red')
        white_pieces = self.board.get_all_pieces('white')
        # Check if a player has no pieces
        if not red_pieces:
            self.winner = 'white'
            return True
        if not white_pieces:
            self.winner = 'red'
            return True
        # Check if a player has no valid moves
        red_has_moves = False
        for piece in red_pieces:
            if self.get_valid_moves(piece.row, piece.col):
                red_has_moves = True
                break
        white_has_moves = False
        for piece in white_pieces:
            if self.get_valid_moves(piece.row, piece.col):
                white_has_moves = True
                break
        if not red_has_moves:
            self.winner = 'white'
            return True
        if not white_has_moves:
            self.winner = 'red'
            return True
        return False
    def get_notation_move(self, move):
        """
        Convert move to algebraic notation.
        Args:
            move (tuple): (from_row, from_col, to_row, to_col)
        Returns:
            str: Move in notation format (e.g., "a3-b4")
        """
        if not move:
            return ""
        from_row, from_col, to_row, to_col = move
        # Convert to algebraic notation (a-h, 1-8)
        col_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        from_notation = f"{col_letters[from_col]}{8 - from_row}"
        to_notation = f"{col_letters[to_col]}{8 - to_row}"
        return f"{from_notation}-{to_notation}"
    def reset(self):
        """Reset the game to initial state."""
        self.__init__()