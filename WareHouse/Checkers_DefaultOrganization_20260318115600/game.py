'''
Core game logic for Checkers
'''
from piece import Piece
from constants import BOARD_SIZE
class Game:
    def __init__(self):
        self.board = [[0 for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_player = 'red'
        self.selected_piece = None
        self.valid_moves = []
        self.valid_captures = []
        self.must_capture = False
        self.winner = None
        self._initialize_board()
    def _initialize_board(self):
        # Place red pieces (bottom three rows)
        for row in range(BOARD_SIZE - 3, BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('red', row, col)
        # Place blue pieces (top three rows)
        for row in range(3):
            for col in range(BOARD_SIZE):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece('blue', row, col)
    def get_board(self):
        return self.board
    def select_piece(self, row, col):
        if self.winner:
            return False
        piece = self.board[row][col]
        # If clicking on empty square with no piece selected
        if piece == 0 and self.selected_piece is None:
            return False
        # If clicking on opponent's piece
        if piece != 0 and piece.color != self.current_player:
            return False
        # If clicking on empty square with piece selected - try to move
        if piece == 0 and self.selected_piece is not None:
            return self._try_move(row, col)
        # Select a piece
        self.selected_piece = (row, col)
        piece = self.board[row][col]
        # Get all possible moves and captures for this piece
        moves, captures = piece.get_possible_moves(self.board)
        # Check if any captures are mandatory
        all_captures = self._get_all_captures_for_player()
        if all_captures:
            # Filter captures for this specific piece
            self.valid_captures = [cap for cap in captures if (cap[0], cap[1]) in [(c[0], c[1]) for c in all_captures]]
            self.valid_moves = []
            self.must_capture = True if self.valid_captures else False
        else:
            self.valid_moves = moves
            self.valid_captures = []
            self.must_capture = False
        return True
    def _try_move(self, row, col):
        if self.selected_piece is None:
            return False
        from_row, from_col = self.selected_piece
        piece = self.board[from_row][from_col]
        # Check if it's a capture move first (captures are mandatory when available)
        for capture in self.valid_captures:
            if row == capture[0] and col == capture[1]:
                # Make the capture move
                self.board[row][col] = piece
                self.board[from_row][from_col] = 0
                self.board[capture[2]][capture[3]] = 0  # Remove captured piece
                piece.move(row, col)
                # Check for additional captures with the same piece
                moves, captures = piece.get_possible_moves(self.board)
                if captures:
                    # Same piece can capture again - keep it selected
                    self.selected_piece = (row, col)
                    self.valid_captures = captures
                    self.must_capture = True
                    return True
                else:
                    self._switch_turn()
                    return True
        # Only allow regular moves if no captures are mandatory
        if not self.must_capture and (row, col) in self.valid_moves:
            # Make the regular move
            self.board[row][col] = piece
            self.board[from_row][from_col] = 0
            piece.move(row, col)
            self._switch_turn()
            return True
        return False
    def _get_all_captures_for_player(self):
        all_captures = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0 and piece.color == self.current_player:
                    _, captures = piece.get_possible_moves(self.board)
                    for capture in captures:
                        all_captures.append(capture)
        return all_captures
    def _switch_turn(self):
        self.current_player = 'blue' if self.current_player == 'red' else 'red'
        self.selected_piece = None
        self.valid_moves = []
        self.valid_captures = []
        self.must_capture = False
        # Check for winner
        self._check_winner()
    def _check_winner(self):
        red_pieces = 0
        blue_pieces = 0
        red_moves = 0
        blue_moves = 0
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                piece = self.board[row][col]
                if piece != 0:
                    if piece.color == 'red':
                        red_pieces += 1
                        moves, captures = piece.get_possible_moves(self.board)
                        red_moves += len(moves) + len(captures)
                    else:
                        blue_pieces += 1
                        moves, captures = piece.get_possible_moves(self.board)
                        blue_moves += len(moves) + len(captures)
        if red_pieces == 0 or (self.current_player == 'red' and red_moves == 0):
            self.winner = 'blue'
        elif blue_pieces == 0 or (self.current_player == 'blue' and blue_moves == 0):
            self.winner = 'red'
    def get_winner(self):
        return self.winner
    def get_current_player(self):
        return self.current_player
    def get_selected_piece(self):
        return self.selected_piece
    def get_valid_moves(self):
        return self.valid_moves
    def get_valid_captures(self):
        return self.valid_captures