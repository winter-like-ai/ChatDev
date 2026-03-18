'''
game.py - Core game logic for Checkers
Contains the CheckersGame class with all game rules and state management
'''
class CheckersGame:
    """Main game controller for Checkers"""
    def __init__(self):
        """Initialize a new Checkers game"""
        self.board = Board()
        self.current_player = 'red'  # Red starts first
        self.selected_piece = None
        self.valid_moves = []
        self.mandatory_captures = []
        self.game_over = False
        self.winner = None
    def initialize_game(self):
        """Set up the initial game state"""
        self.board.initialize_board()
        self.current_player = 'red'
        self.selected_piece = None
        self.valid_moves = []
        self.mandatory_captures = self.get_mandatory_captures()
        self.game_over = False
        self.winner = None
    def get_mandatory_captures(self):
        """Find all mandatory capture moves for current player"""
        captures = []
        for row in range(8):
            for col in range(8):
                piece = self.board.get_piece(row, col)
                if piece and piece.color == self.current_player:
                    piece_captures = self.get_capture_moves(row, col)
                    if piece_captures:
                        captures.extend([(row, col, move) for move in piece_captures])
        return captures
    def select_piece(self, row, col):
        """Select a piece at the given position"""
        piece = self.board.get_piece(row, col)
        if not piece or piece.color != self.current_player:
            return False
        # If there are mandatory captures, only allow selecting pieces that can capture
        if self.mandatory_captures:
            can_this_piece_capture = any(
                r == row and c == col for r, c, _ in self.mandatory_captures
            )
            if not can_this_piece_capture:
                return False
        self.selected_piece = (row, col)
        self.valid_moves = self.get_valid_moves(row, col)
        return True
    def get_valid_moves(self, row, col):
        """Get all valid moves for a piece at the given position"""
        piece = self.board.get_piece(row, col)
        if not piece:
            return []
        moves = []
        # If there are mandatory captures, only return capture moves
        if self.mandatory_captures:
            return self.get_capture_moves(row, col)
        # Regular moves (non-captures)
        directions = piece.get_move_directions()
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if self.board.is_valid_position(new_row, new_col):
                if self.board.is_empty(new_row, new_col):
                    moves.append((new_row, new_col, False))  # (row, col, is_capture)
        # Also include any capture moves
        capture_moves = self.get_capture_moves(row, col)
        for move in capture_moves:
            moves.append((move[0], move[1], True))
        return moves
    def get_capture_moves(self, row, col):
        """Get all capture moves for a piece at the given position"""
        piece = self.board.get_piece(row, col)
        if not piece:
            return []
        captures = []
        directions = piece.get_move_directions()
        for dr, dc in directions:
            # Check if there's an opponent piece to jump over
            jump_row, jump_col = row + dr, col + dc
            land_row, land_col = row + 2*dr, col + 2*dc
            if (self.board.is_valid_position(jump_row, jump_col) and 
                self.board.is_valid_position(land_row, land_col)):
                jumped_piece = self.board.get_piece(jump_row, jump_col)
                if (jumped_piece and jumped_piece.color != piece.color and 
                    self.board.is_empty(land_row, land_col)):
                    captures.append((land_row, land_col))
        return captures
    def make_move(self, to_row, to_col):
        """Make a move from selected piece to target position"""
        if not self.selected_piece or self.game_over:
            return False
        from_row, from_col = self.selected_piece
        # Check if this is a valid move
        is_valid = False
        is_capture = False
        for move in self.valid_moves:
            if len(move) == 3:
                r, c, capture = move
                if r == to_row and c == to_col:
                    is_valid = True
                    is_capture = capture
                    break
            else:
                r, c = move
                if r == to_row and c == to_col:
                    is_valid = True
                    is_capture = True
                    break
        if not is_valid:
            return False
        # Execute the move
        piece = self.board.get_piece(from_row, from_col)
        self.board.move_piece(from_row, from_col, to_row, to_col)
        # Handle capture
        if is_capture:
            # Remove the captured piece (middle position)
            mid_row = (from_row + to_row) // 2
            mid_col = (from_col + to_col) // 2
            self.board.remove_piece(mid_row, mid_col)
            # Check for additional captures (multiple jumps)
            additional_captures = self.get_capture_moves(to_row, to_col)
            if additional_captures:
                # Player gets another turn for multiple jumps
                self.selected_piece = (to_row, to_col)
                self.valid_moves = additional_captures
                return True
        # King the piece if it reached the opposite end
        if ((piece.color == 'red' and to_row == 7) or 
            (piece.color == 'black' and to_row == 0)):
            piece.king()
        # Switch players
        self.switch_player()
        # Check for game over
        self.check_game_over()
        return True
    def switch_player(self):
        """Switch to the other player's turn"""
        self.current_player = 'black' if self.current_player == 'red' else 'red'
        self.selected_piece = None
        self.valid_moves = []
        self.mandatory_captures = self.get_mandatory_captures()
    def check_game_over(self):
        """Check if the game is over"""
        red_pieces = self.board.get_pieces_by_color('red')
        black_pieces = self.board.get_pieces_by_color('black')
        if not red_pieces:
            self.game_over = True
            self.winner = 'black'
        elif not black_pieces:
            self.game_over = True
            self.winner = 'red'
        else:
            # Check if current player has any valid moves
            has_moves = False
            for row in range(8):
                for col in range(8):
                    piece = self.board.get_piece(row, col)
                    if piece and piece.color == self.current_player:
                        if self.get_valid_moves(row, col):
                            has_moves = True
                            break
                if has_moves:
                    break
            if not has_moves:
                self.game_over = True
                self.winner = 'black' if self.current_player == 'red' else 'red'
    def get_game_state_text(self):
        """Get text description of current game state"""
        if self.game_over:
            return f"Game Over! {self.winner.capitalize()} wins!"
        elif self.mandatory_captures:
            return f"{self.current_player.capitalize()}'s turn - Mandatory Capture!"
        else:
            return f"{self.current_player.capitalize()}'s turn"
    def reset_game(self):
        """Reset the game to initial state"""
        self.initialize_game()
class Board:
    """Represents the checkers board and piece positions"""
    def __init__(self):
        """Initialize an empty board"""
        self.grid = [[None for _ in range(8)] for _ in range(8)]
    def initialize_board(self):
        """Set up initial piece positions"""
        self.grid = [[None for _ in range(8)] for _ in range(8)]
        # Place red pieces (top three rows)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = Piece('red')
        # Place black pieces (bottom three rows)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.grid[row][col] = Piece('black')
    def get_piece(self, row, col):
        """Get piece at specified position"""
        if self.is_valid_position(row, col):
            return self.grid[row][col]
        return None
    def is_empty(self, row, col):
        """Check if position is empty"""
        return self.get_piece(row, col) is None
    def is_valid_position(self, row, col):
        """Check if position is within board bounds"""
        return 0 <= row < 8 and 0 <= col < 8
    def move_piece(self, from_row, from_col, to_row, to_col):
        """Move a piece from one position to another"""
        piece = self.grid[from_row][from_col]
        self.grid[from_row][from_col] = None
        self.grid[to_row][to_col] = piece
    def remove_piece(self, row, col):
        """Remove a piece from the board"""
        self.grid[row][col] = None
    def get_pieces_by_color(self, color):
        """Get all pieces of a specific color"""
        pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.get_piece(row, col)
                if piece and piece.color == color:
                    pieces.append((row, col, piece))
        return pieces
class Piece:
    """Represents a checkers piece"""
    def __init__(self, color):
        """Initialize a piece with given color"""
        self.color = color  # 'red' or 'black'
        self.is_king = False
    def king(self):
        """Make this piece a king"""
        self.is_king = True
    def get_move_directions(self):
        """Get possible move directions based on piece type and color"""
        if self.is_king:
            # Kings can move in all four diagonal directions
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif self.color == 'red':
            # Red moves downward (increasing row)
            return [(1, -1), (1, 1)]
        else:  # black
            # Black moves upward (decreasing row)
            return [(-1, -1), (-1, 1)]
    def __repr__(self):
        """String representation of the piece"""
        king_symbol = 'K' if self.is_king else ''
        return f"{self.color[0].upper()}{king_symbol}"