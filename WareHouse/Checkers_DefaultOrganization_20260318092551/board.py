'''
Board class representing the checkers board and managing pieces.
'''
from piece import Piece
from constants import ROWS, COLS, RED, BLUE, SQUARE_SIZE
class Board:
    def __init__(self):
        self.board = []
        self.red_left = self.blue_left = 12
        self.red_kings = self.blue_kings = 0
        self.create_board()
    def create_board(self):
        '''Initialize the board with pieces in starting positions'''
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        # Place pieces on black squares
        for row in range(ROWS):
            for col in range(COLS):
                if (row + col) % 2 == 1:  # Black squares
                    if row < 3:
                        self.board[row][col] = Piece(row, col, "blue")
                    elif row > 4:
                        self.board[row][col] = Piece(row, col, "red")
    def draw(self, screen):
        '''Draw the board and pieces'''
        self.draw_squares(screen)
        self.draw_pieces(screen)
    def draw_squares(self, screen):
        '''Draw the checkerboard pattern'''
        from constants import LIGHT_BROWN, DARK_BROWN
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT_BROWN if (row + col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(screen, color, 
                               (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                                SQUARE_SIZE, SQUARE_SIZE))
    def draw_pieces(self, screen):
        '''Draw all pieces on the board'''
        from constants import RED, BLUE, WHITE, BLACK, PIECE_RADIUS, KING_RADIUS
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece is not None:
                    radius = KING_RADIUS if piece.king else PIECE_RADIUS
                    color = RED if piece.color == "red" else BLUE
                    # Draw piece
                    pygame.draw.circle(screen, color, (piece.x, piece.y), radius)
                    pygame.draw.circle(screen, BLACK, (piece.x, piece.y), radius, 2)
                    # Draw king crown
                    if piece.king:
                        pygame.draw.circle(screen, WHITE, (piece.x, piece.y), radius - 10)
                        pygame.draw.circle(screen, BLACK, (piece.x, piece.y), radius - 10, 2)
    def get_piece(self, row, col):
        '''Get piece at specified position'''
        if 0 <= row < ROWS and 0 <= col < COLS:
            return self.board[row][col]
        return None
    def move(self, piece, row, col):
        '''Move a piece to new position'''
        self.board[piece.row][piece.col], self.board[row][col] = self.board[row][col], self.board[piece.row][piece.col]
        piece.move(row, col)
        # Check for king promotion
        if (piece.color == "red" and row == 0) or (piece.color == "blue" and row == ROWS - 1):
            if not piece.king:
                piece.make_king()
                if piece.color == "red":
                    self.red_kings += 1
                else:
                    self.blue_kings += 1
    def remove(self, pieces):
        '''Remove captured pieces from the board'''
        for piece in pieces:
            self.board[piece.row][piece.col] = None
            if piece is not None:
                if piece.color == "red":
                    self.red_left -= 1
                    if piece.king:
                        self.red_kings -= 1
                else:
                    self.blue_left -= 1
                    if piece.king:
                        self.blue_kings -= 1
    def winner(self):
        '''Check if there's a winner'''
        if self.red_left <= 0:
            return "blue"
        elif self.blue_left <= 0:
            return "red"
        return None
    def get_valid_moves(self, piece):
        '''Get all valid moves for a piece'''
        return piece.get_valid_moves(self)
    def get_all_pieces(self, color):
        '''Get all pieces of a specific color'''
        pieces = []
        for row in self.board:
            for piece in row:
                if piece is not None and piece.color == color:
                    pieces.append(piece)
        return pieces