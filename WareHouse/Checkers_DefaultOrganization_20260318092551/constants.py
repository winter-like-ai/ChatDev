'''
Game constants including colors, dimensions, and configuration.
'''
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT = (255, 255, 0, 128)  # Yellow with transparency
# Board dimensions
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
PIECE_RADIUS = 30
KING_RADIUS = 35
# Window dimensions
WIDTH = COLS * SQUARE_SIZE
HEIGHT = ROWS * SQUARE_SIZE
FPS = 60
# Game states
PLAYER_ONE = 1
PLAYER_TWO = 2
EMPTY = 0
# Directions
UP = -1
DOWN = 1
LEFT = -1
RIGHT = 1