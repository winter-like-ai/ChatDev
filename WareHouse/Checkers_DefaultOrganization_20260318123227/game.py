'''
Core game logic for Checkers.
Manages game state, rules, and move validation.
'''
class Piece:
    """Represents a checkers piece."""
    def __init__(self, row, col, color):
        """
        Initialize a piece.
        Args:
            row: Row position on board
            col: Column position on board
            color: 'red' or 'white'
        """
        self.row = row
        self.col = col
        self.color = color
        self.is_king = False
        self.x = 0
        self.y = 0
        self.calc_pos()
    def calc_pos(self):
        """Calculate pixel position based on board coordinates."""
        self.x = self.col * 100 + 50
        self.y = self.row * 100 + 50
    def make_king(self):
        """Convert piece to a king."""
        self.is_king = True
    def move(self, row, col):
        """Move piece to new position."""
        self.row = row
        self.col = col
        self.calc_pos()
    def __repr__(self):
        return f"Piece({self.row}, {self.col}, {self.color}, king={self.is_king})"
class Board:
    """Manages the checkers board state."""
    def __init__(self):
        """Initialize an empty 8x8 board."""
        self.board = []
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self.create_board()
    def create_board(self):
        """Set up initial board with pieces in starting positions."""
        self.board = [[None for _ in range(8)] for _ in range(8)]
        # Place red pieces (top three rows)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, 'red')
        # Place white pieces (bottom three rows)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(row, col, 'white')
    def get_piece(self, row, col):
        """Get piece at specified position."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    def move_piece(self, piece, row, col):
        """Move a piece to new position."""
        # Remove piece from old position
        self.board[piece.row][piece.col] = None
        # Place piece at new position
        self.board[row][col] = piece
        piece.move(row, col)
        # Check for king promotion
        if not piece.is_king:
            if (piece.color == 'red' and row == 7) or (piece.color == 'white' and row == 0):
                piece.make_king()
                if piece.color == 'red':
                    self.red_kings += 1
                else:
                    self.white_kings += 1
    def remove_piece(self, row, col):
        """Remove a piece from the board."""
        piece = self.board[row][col]
        if piece:
            if piece.color == 'red':
                self.red_left -= 1
                if piece.is_king:
                    self.red_kings -= 1
            else:
                self.white_left -= 1
                if piece.is_king:
                    self.white_kings -= 1
        self.board[row][col] = None
    def get_valid_moves(self, piece):
        """Get all valid moves for a piece."""
        moves = {}
        left = piece.col - 1
        right = piece.col + 1
        row = piece.row
        if piece.color == 'red' or piece.is_king:
            moves.update(self._traverse_left(row - 1, max(row - 3, -1), -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, max(row - 3, -1), -1, piece.color, right))
        if piece.color == 'white' or piece.is_king:
            moves.update(self._traverse_left(row + 1, min(row + 3, 8), 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, min(row + 3, 8), 1, piece.color, right))
        # Enforce mandatory capture: if any capture moves exist, return only those
        capture_moves = {pos: skipped for pos, skipped in moves.items() if skipped}
        if capture_moves:
            return capture_moves
        return moves
    def _traverse_left(self, start, stop, step, color, left, skipped=[]):
        """Helper function to find moves to the left."""
        moves = {}
        last = []
        for r in range(start, stop, step):
            if left < 0:
                break
            current = self.board[r][left]
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
                        row = min(r + 3, 8)
                    moves.update(self._traverse_left(r + step, row, step, color, left - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, left + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            left -= 1
        return moves
    def _traverse_right(self, start, stop, step, color, right, skipped=[]):
        """Helper function to find moves to the right."""
        moves = {}
        last = []
        for r in range(start, stop, step):
            if right >= 8:
                break
            current = self.board[r][right]
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
                        row = min(r + 3, 8)
                    moves.update(self._traverse_left(r + step, row, step, color, right - 1, skipped=last))
                    moves.update(self._traverse_right(r + step, row, step, color, right + 1, skipped=last))
                break
            elif current.color == color:
                break
            else:
                last = [current]
            right += 1
        return moves
class CheckersGame:
    """Main game controller."""
    def __init__(self):
        """Initialize a new game."""
        self.board = Board()
        self.turn = 'red'  # Red starts
        self.selected = None
        self.valid_moves = {}
        self.game_over = False
        self.winner = None
        # State for mandatory multi-capture
        self.must_capture_again = False
        self.capturing_piece = None
    def reset(self):
        """Reset the game to initial state."""
        self.__init__()
    def select(self, row, col):
        """Select a piece or move to a position."""
        if self.game_over:
            return False
        piece = self.board.get_piece(row, col)
        # If a piece of current player's color is selected
        if piece and piece.color == self.turn:
            # If we are in a multi-capture sequence, only allow selecting the capturing piece
            if self.must_capture_again:
                if piece != self.capturing_piece:
                    return False
            self.selected = piece
            self.valid_moves = self.board.get_valid_moves(piece)
            return True
        # If a valid move position is selected
        elif self.selected and (row, col) in self.valid_moves:
            self.move(row, col)
            return True
        return False
    def move(self, row, col):
        """Move selected piece to specified position."""
        piece = self.selected
        move = self.valid_moves.get((row, col))
        if piece and move:
            # Move the piece
            self.board.move_piece(piece, row, col)
            # Remove captured pieces
            if move:
                for captured_piece in move:
                    self.board.remove_piece(captured_piece.row, captured_piece.col)
                # After a capture, check for further captures from the new position
                self.capturing_piece = piece
                further_moves = self.board.get_valid_moves(piece)
                # Filter further moves to only include captures
                capture_moves = {pos: skipped for pos, skipped in further_moves.items() if skipped}
                if capture_moves:
                    # More captures possible: stay on same turn
                    self.must_capture_again = True
                    self.valid_moves = capture_moves
                    return True
                else:
                    # No further captures: switch turns
                    self.change_turn()
            else:
                # Non-capturing move: switch turns
                self.change_turn()
            # Check for game over
            self.check_game_over()
        else:
            return False
        return True
    def change_turn(self):
        """Switch to the other player's turn."""
        self.selected = None
        self.valid_moves = {}
        self.turn = 'white' if self.turn == 'red' else 'red'
        # Reset multi-capture state
        self.must_capture_again = False
        self.capturing_piece = None
    def check_game_over(self):
        """Check if the game is over."""
        red_has_moves = self.player_has_moves('red')
        white_has_moves = self.player_has_moves('white')
        if not red_has_moves or self.board.red_left == 0:
            self.game_over = True
            self.winner = 'White'
        elif not white_has_moves or self.board.white_left == 0:
            self.game_over = True
            self.winner = 'Red'
    def player_has_moves(self, color):
        """Check if a player has any valid moves."""
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece and piece.color == color:
                    moves = self.board.get_valid_moves(piece)
                    if moves:
                        return True
        return False
    def get_board(self):
        """Get the current board state."""
        return self.board
    def get_turn(self):
        """Get current player's turn."""
        return self.turn
    def get_selected(self):
        """Get currently selected piece."""
        return self.selected
    def get_valid_moves(self):
        """Get valid moves for selected piece."""
        return self.valid_moves
    def is_game_over(self):
        """Check if game is over."""
        return self.game_over
    def get_winner(self):
        """Get the winner if game is over."""
        return self.winner
    def get_must_capture_again(self):
        """Check if current player must capture again."""
        return self.must_capture_again