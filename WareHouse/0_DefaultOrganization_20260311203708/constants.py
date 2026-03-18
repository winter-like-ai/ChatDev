'''
Constants and configuration for the Checkers game
'''
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT = (255, 255, 0, 128)  # Semi-transparent yellow
# Board settings
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
WIDTH = COLS * SQUARE_SIZE
HEIGHT = ROWS * SQUARE_SIZE
BOARD_SIZE = (WIDTH, HEIGHT)
# Game settings
FPS = 60
PLAYER_ONE = 'red'
PLAYER_TWO = 'blue'
EMPTY = 'empty'
# Piece settings
PIECE_RADIUS = 30
KING_OFFSET = 15