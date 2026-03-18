'''
Game class managing game state, turns, and player interactions.
'''
import pygame
from board import Board
from constants import GREEN, GRAY, WIDTH, HEIGHT, SQUARE_SIZE
class Game:
    def __init__(self, screen):
        """
        Initialize the game.
        Args:
            screen: Pygame display surface
        """
        self.screen = screen
        self.reset()
    def reset(self):
        """Reset the game to starting state."""
        self.board = Board()
        self.turn = 'red'  # Red starts first
        self.selected = None
        self.valid_moves = {}
        self.must_capture = False
        self.winner = None
        self.move_history = []
    def update(self):
        """Update the game display."""
        self.board.draw(self.screen)
        self.draw_valid_moves()
        self.draw_turn_indicator()
        self.draw_move_notation()
        if self.winner:
            self.draw_winner()
    def select(self, row, col):
        """
        Handle piece selection and movement.
        Args:
            row: Selected row
            col: Selected column
        """
        if self.winner:
            return
        piece = self.board.get_piece(row, col)
        if self.selected:
            # Try to move the selected piece
            result = self._move(row, col)
            if not result:
                # If move failed, try selecting a different piece
                self.selected = None
                self.valid_moves = {}
                self.select(row, col)
        else:
            # Select a piece if it's the correct turn
            if piece is not None and piece.color == self.turn:
                self.selected = piece
                self.valid_moves = self.board.get_valid_moves(piece)
                # Check if captures are mandatory
                self.must_capture = any(len(captures) > 0 for captures in self.valid_moves.values())
                # If captures are mandatory, filter to only capture moves
                if self.must_capture:
                    self.valid_moves = {pos: caps for pos, caps in self.valid_moves.items() if len(caps) > 0}
                return True
        return False
    def _move(self, row, col):
        """
        Move selected piece to target position.
        Args:
            row: Target row
            col: Target column
        Returns:
            True if move successful, False otherwise
        """
        if self.selected and (row, col) in self.valid_moves:
            # Record move in notation
            from_pos = (self.selected.row, self.selected.col)
            to_pos = (row, col)
            move_notation = f"{self._pos_to_notation(from_pos)}-{self._pos_to_notation(to_pos)}"
            self.move_history.append((self.turn, move_notation))
            # Perform the move
            captured = self.board.move(self.selected, row, col)
            # Check if another capture is possible with the same piece
            if captured:
                self.selected = self.board.get_piece(row, col)
                self.valid_moves = self.board.get_valid_moves(self.selected)
                # Filter to only capture moves
                self.valid_moves = {pos: caps for pos, caps in self.valid_moves.items() if len(caps) > 0}
                if self.valid_moves:
                    # Multiple jump possible, don't switch turns yet
                    return True
            # Switch turns
            self.next_turn()
            return True
        return False
    def _pos_to_notation(self, pos):
        """
        Convert board position to algebraic notation.
        Args:
            pos: (row, col) tuple
        Returns:
            String in format like "a1", "b2", etc.
        """
        row, col = pos
        # Convert to standard checkers notation: columns a-h, rows 1-8 from bottom
        col_char = chr(ord('a') + col)
        row_num = 8 - row  # Row 0 is top (8 in notation), row 7 is bottom (1 in notation)
        return f"{col_char}{row_num}"
    def draw_valid_moves(self):
        """Highlight valid moves for selected piece."""
        if self.selected:
            for move in self.valid_moves:
                row, col = move
                x = col * SQUARE_SIZE + SQUARE_SIZE // 2
                y = row * SQUARE_SIZE + SQUARE_SIZE // 2
                # Draw a green circle for valid moves
                pygame.draw.circle(self.screen, GREEN, (x, y), 15)
                # Draw outline
                pygame.draw.circle(self.screen, (0, 100, 0), (x, y), 15, 2)
    def draw_turn_indicator(self):
        """Display whose turn it is."""
        font = pygame.font.SysFont('Arial', 24)
        if self.winner:
            text = f"Winner: {self.winner.capitalize()}"
            color = RED if self.winner == 'red' else WHITE
        else:
            text = f"Turn: {self.turn.capitalize()}"
            color = RED if self.turn == 'red' else WHITE
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, (10, 10))
        # Draw instructions
        instructions = [
            "Click on a piece to select it",
            "Click on highlighted square to move",
            "Press R to reset, ESC to quit"
        ]
        for i, instruction in enumerate(instructions):
            instr_surface = font.render(instruction, True, GRAY)
            self.screen.blit(instr_surface, (10, HEIGHT - 80 + i * 25))
    def draw_move_notation(self):
        """Display move notation for the current move."""
        if self.move_history and len(self.move_history) > 0:
            font = pygame.font.SysFont('Arial', 20)
            # Show last 5 moves
            recent_moves = self.move_history[-5:]
            for i, (player, notation) in enumerate(recent_moves):
                text = f"{player}: {notation}"
                color = RED if player == 'red' else WHITE
                text_surface = font.render(text, True, color)
                self.screen.blit(text_surface, (WIDTH - 150, 10 + i * 25))
    def draw_winner(self):
        """Display winner announcement."""
        font = pygame.font.SysFont('Arial', 48, bold=True)
        text = f"{self.winner.capitalize()} Wins!"
        color = RED if self.winner == 'red' else WHITE
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        # Draw background
        pygame.draw.rect(self.screen, (0, 0, 0, 128), 
                        text_rect.inflate(20, 20))
        self.screen.blit(text_surface, text_rect)
    def next_turn(self):
        """Switch to the other player's turn."""
        self.selected = None
        self.valid_moves = {}
        self.must_capture = False
        # Check for winner
        self.winner = self.board.winner()
        if not self.winner:
            # Switch turns
            self.turn = 'white' if self.turn == 'red' else 'red'
    def valid_move(self, piece, row, col):
        """
        Check if a move is valid.
        Args:
            piece: Piece to move
            row: Target row
            col: Target column
        Returns:
            True if move is valid, False otherwise
        """
        return (row, col) in piece.get_valid_moves(self.board)