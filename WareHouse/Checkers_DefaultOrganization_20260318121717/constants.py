'''
Game constants and configuration.
'''
# Board dimensions
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
WIDTH = COLS * SQUARE_SIZE + 300  # Extra space for UI
HEIGHT = ROWS * SQUARE_SIZE
# Colors
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_SQUARE = (181, 136, 99)
LIGHT_SQUARE = (240, 217, 181)
BACKGROUND = (50, 50, 50)
HIGHLIGHT = (0, 255, 0)
VALID_MOVE = (0, 200, 0)
TEXT_COLOR = (255, 255, 255)
WINNER_COLOR = (255, 215, 0)
YELLOW = (255, 255, 0)
# Game settings
FPS = 60
PIECE_RADIUS = SQUARE_SIZE // 2 - 10