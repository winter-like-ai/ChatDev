'''
Game class managing the overall game state, turns, and rules.
Coordinates between the board, pieces, and user interface.
'''
import pygame
from board import Board
from constants import WIDTH, HEIGHT, SQUARE_SIZE, RED, BLUE, GREEN, GRAY, WHITE, BLACK
class Game:
    def __init__(self, screen):
        '''
        Initialize the game.
        Args:
            screen (pygame.Surface): Pygame surface for drawing
        '''
        self.screen = screen
        self.board = Board()
        self.turn = RED  # Red starts
        self.selected_piece = None
        self.must_capture = False
        self.game_over = False
        self.winner = None
        self.move_history = []
        self.capture_chain = False
        self.chain_piece = None
    def handle_click(self, pos):
        '''
        Handle mouse click events.
        Args:
            pos (tuple): (x, y) mouse position
        '''
        if self.game_over:
            return
        x, y = pos
        # Check if click is on the board
        if y < ROWS * SQUARE_SIZE:
            row = y // SQUARE_SIZE
            col = x // SQUARE_SIZE
            if self.capture_chain and self.chain_piece:
                # Continue capture chain
                self.handle_capture_chain(row, col)
            else:
                # Normal move selection
                self.select_piece_or_move(row, col)
    def select_piece_or_move(self, row, col):
        '''
        Select a piece or execute a move.
        Args:
            row (int): Row clicked
            col (int): Column clicked
        '''
        piece = self.board.get_piece(row, col)
        if self.selected_piece is None:
            # Select a piece
            if piece is not None and piece.color == self.turn:
                self.selected_piece = piece
                self.update_valid_moves(piece)
        else:
            # Try to move the selected piece
            if (row, col) in self.board.valid_moves:
                self.make_move(self.selected_piece, row, col)
            else:
                # Select a different piece
                if piece is not None and piece.color == self.turn:
                    self.selected_piece = piece
                    self.update_valid_moves(piece)
                else:
                    self.clear_selection()
    def handle_capture_chain(self, row, col):
        '''
        Handle additional captures in a chain.
        Args:
            row (int): Row clicked
            col (int): Column clicked
        '''
        if (row, col) in self.board.valid_moves:
            self.make_move(self.chain_piece, row, col, is_chain=True)
        else:
            # Invalid move in chain, cancel chain
            self.capture_chain = False
            self.chain_piece = None
            self.switch_turn()
            self.clear_selection()
    def update_valid_moves(self, piece):
        '''
        Update valid moves for the selected piece.
        Args:
            piece (Piece): Selected piece
        '''
        self.board.selected_piece = piece
        self.board.valid_moves = []
        # Check for captures first (mandatory capture rule)
        captures = piece.get_possible_captures(self.board)
        if captures:
            self.must_capture = True
            # Add landing positions to valid moves
            for capture_pos, land_pos in captures:
                self.board.valid_moves.append(land_pos)
        else:
            self.must_capture = False
            # Add regular moves
            self.board.valid_moves = piece.get_possible_moves(self.board)
    def make_move(self, piece, row, col, is_chain=False):
        '''
        Execute a move.
        Args:
            piece (Piece): Piece to move
            row (int): Destination row
            col (int): Destination column
            is_chain (bool): Whether this is part of a capture chain
        Returns:
            bool: True if move was successful
        '''
        # Check if this is a capture move
        is_capture = abs(piece.row - row) == 2
        # Store move notation
        from_pos = (piece.row, piece.col)
        to_pos = (row, col)
        move_notation = self.get_move_notation(from_pos, to_pos)
        self.move_history.append(move_notation)
        if is_capture:
            # Calculate captured piece position
            capture_row = (piece.row + row) // 2
            capture_col = (piece.col + col) // 2
            # Remove captured piece
            self.board.remove_piece(capture_row, capture_col)
            # Move the piece
            self.board.move_piece(piece, row, col)
            # Check for additional captures
            piece_captures = piece.get_possible_captures(self.board)
            if piece_captures:
                # Continue capture chain
                self.capture_chain = True
                self.chain_piece = piece
                self.update_valid_moves(piece)
                return True
            else:
                # End capture chain
                self.capture_chain = False
                self.chain_piece = None
        else:
            # Regular move
            self.board.move_piece(piece, row, col)
        # Clear selection and switch turn if not in chain
        if not self.capture_chain:
            self.clear_selection()
            self.switch_turn()
        # Check for winner
        self.check_winner()
        return True
    def clear_selection(self):
        '''Clear current selection.'''
        self.selected_piece = None
        self.board.clear_selection()
    def switch_turn(self):
        '''Switch to the other player's turn.'''
        self.turn = BLUE if self.turn == RED else RED
        self.must_capture = False
        # Check if current player has any valid moves
        if not self.has_valid_moves():
            self.game_over = True
            self.winner = BLUE if self.turn == RED else RED
    def has_valid_moves(self):
        '''
        Check if current player has any valid moves.
        Returns:
            bool: True if player has valid moves
        '''
        pieces = self.board.get_all_pieces(self.turn)
        # Check for any captures first
        for piece in pieces:
            captures = piece.get_possible_captures(self.board)
            if captures:
                return True
        # Check for any regular moves
        for piece in pieces:
            moves = piece.get_possible_moves(self.board)
            if moves:
                return True
        return False
    def check_winner(self):
        '''Check if the game has ended and determine winner.'''
        red_pieces = self.board.get_all_pieces(RED)
        blue_pieces = self.board.get_all_pieces(BLUE)
        if not red_pieces:
            self.game_over = True
            self.winner = BLUE
        elif not blue_pieces:
            self.game_over = True
            self.winner = RED
        elif not self.has_valid_moves():
            self.game_over = True
            self.winner = BLUE if self.turn == RED else RED
    def get_move_notation(self, from_pos, to_pos):
        '''
        Convert positions to algebraic notation.
        Args:
            from_pos (tuple): (row, col) starting position
            to_pos (tuple): (row, col) ending position
        Returns:
            str: Move in notation (e.g., "C3 to D4")
        '''
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        # Convert to algebraic notation (A-H, 1-8)
        col_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        from_str = f"{col_letters[from_col]}{8 - from_row}"
        to_str = f"{col_letters[to_col]}{8 - to_row}"
        return f"{from_str} to {to_str}"
    def update(self):
        '''Update game state and draw everything.'''
        # Clear screen
        self.screen.fill(WHITE)
        # Draw board
        self.board.draw(self.screen)
        # Draw UI panel
        self.draw_ui()
        # Draw game over message
        if self.game_over:
            self.draw_game_over()
    def draw_ui(self):
        '''Draw user interface elements.'''
        # Draw turn indicator
        turn_text = "Red's Turn" if self.turn == RED else "Blue's Turn"
        turn_color = RED if self.turn == RED else BLUE
        font = pygame.font.Font(None, 36)
        text = font.render(turn_text, True, turn_color)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - 70))
        self.screen.blit(text, text_rect)
        # Draw move notation prompt
        prompt_font = pygame.font.Font(None, 24)
        prompt = "Click piece then destination (e.g., C3 to D4)"
        prompt_text = prompt_font.render(prompt, True, BLACK)
        prompt_rect = prompt_text.get_rect(center=(WIDTH // 2, HEIGHT - 40))
        self.screen.blit(prompt_text, prompt_rect)
        # Draw last move
        if self.move_history:
            last_move = f"Last move: {self.move_history[-1]}"
            move_text = prompt_font.render(last_move, True, GRAY)
            move_rect = move_text.get_rect(center=(WIDTH // 2, HEIGHT - 20))
            self.screen.blit(move_text, move_rect)
        # Draw capture requirement
        if self.must_capture:
            capture_text = prompt_font.render("Capture is mandatory!", True, GREEN)
            capture_rect = capture_text.get_rect(center=(WIDTH // 2, HEIGHT - 90))
            self.screen.blit(capture_text, capture_rect)
    def draw_game_over(self):
        '''Draw game over message.'''
        # Create semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        # Draw winner message
        winner_text = "Red Wins!" if self.winner == RED else "Blue Wins!"
        font = pygame.font.Font(None, 72)
        text = font.render(winner_text, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(text, text_rect)
        # Draw restart instruction
        restart_font = pygame.font.Font(None, 36)
        restart_text = restart_font.render("Close and restart to play again", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
        self.screen.blit(restart_text, restart_rect)