'''
game.py
Game class managing game logic, turns, and rules.
'''
from board import Board
import constants
from notation import parse_notation
class Game:
    """Main game controller handling game logic and state."""
    def __init__(self):
        """Initialize a new game."""
        self.board = Board()
        self.turn = constants.PLAYER_ONE  # Player one starts
        self.selected = None
        self.valid_moves = {}
        self.game_over = False
        self.winner = None
        self.input_mode = "GUI"  # Can be "GUI" or "NOTATION"
    def reset(self):
        """Reset the game to initial state."""
        self.board = Board()
        self.turn = constants.PLAYER_ONE
        self.selected = None
        self.valid_moves = {}
        self.game_over = False
        self.winner = None
    def select(self, row, col):
        """Select a piece or a position to move to."""
        if self.game_over:
            return False
        piece = self.board.get_piece(row, col)
        # If a piece is already selected, try to move it
        if self.selected and (row, col) in self.valid_moves:
            result = self._move(row, col)
            if not result:
                self.selected = None
                self.select(row, col)
        else:
            # Select a new piece
            if piece != 0 and piece.color == self.turn:
                self.selected = piece
                self.valid_moves = self.board.get_valid_moves(piece)
                return True
        return False
    def move_by_notation(self, notation):
        """
        Execute a move using algebraic notation.
        Args:
            notation: Move in notation format (e.g., "c3-d4", "a5xb6")
        Returns:
            bool: True if move was successful, False otherwise
        """
        if self.game_over:
            return False
        # Parse notation to get from and to coordinates
        try:
            from_pos, to_pos, is_capture = parse_notation(notation)
        except ValueError as e:
            print(f"Invalid notation: {e}")
            return False
        # Check if there's a piece at the from position
        piece = self.board.get_piece(from_pos[0], from_pos[1])
        if not piece or piece.color != self.turn:
            print(f"No valid piece at {notation.split('-')[0]}")
            return False
        # Get valid moves for the piece
        self.selected = piece
        self.valid_moves = self.board.get_valid_moves(piece)
        # Check if the to position is a valid move
        if (to_pos[0], to_pos[1]) not in self.valid_moves:
            print(f"Invalid move: {notation}")
            self.selected = None
            self.valid_moves = {}
            return False
        # Check if it's a capture move when notation indicates capture
        move_data = self.valid_moves.get((to_pos[0], to_pos[1]))
        is_actual_capture = bool(move_data)
        if is_capture and not is_actual_capture:
            print(f"Not a capture move: {notation}")
            self.selected = None
            self.valid_moves = {}
            return False
        # Execute the move
        result = self._move(to_pos[0], to_pos[1])
        return result
    def _move(self, row, col):
        """Execute a move."""
        piece = self.selected
        destination = self.valid_moves.get((row, col))
        if not destination:
            return False
        # Move the piece
        self.board.move(piece, row, col)
        # Remove captured pieces
        if destination:
            self.board.remove(destination)
        # Check for king promotion
        self._check_king(piece)
        # Switch turns
        self.change_turn()
        # Clear selection
        self.selected = None
        self.valid_moves = {}
        # Check for winner
        self._check_winner()
        return True
    def _check_king(self, piece):
        """Promote piece to king if it reaches the opposite end."""
        if piece.color == constants.PLAYER_ONE and piece.row == constants.BOARD_SIZE - 1:
            piece.make_king()
        elif piece.color == constants.PLAYER_TWO and piece.row == 0:
            piece.make_king()
    def _check_winner(self):
        """Check if the game has a winner."""
        winner = self.board.winner()
        if winner:
            self.game_over = True
            self.winner = winner
    def change_turn(self):
        """Switch to the other player's turn."""
        self.turn = constants.PLAYER_TWO if self.turn == constants.PLAYER_ONE else constants.PLAYER_ONE
    def get_board(self):
        """Get the current board state."""
        return self.board
    def ai_move(self):
        """Simple AI move for single player mode (placeholder for future enhancement)."""
        # This is a placeholder - in a full implementation, this would contain AI logic
        pass
    def get_turn(self):
        """Get current player's turn."""
        return self.turn
    def is_game_over(self):
        """Check if game is over."""
        return self.game_over
    def get_winner(self):
        """Get the winner if game is over."""
        return self.winner
    def toggle_input_mode(self):
        """Toggle between GUI and notation input modes."""
        self.input_mode = "NOTATION" if self.input_mode == "GUI" else "GUI"
        return self.input_mode
    def get_input_mode(self):
        """Get current input mode."""
        return self.input_mode