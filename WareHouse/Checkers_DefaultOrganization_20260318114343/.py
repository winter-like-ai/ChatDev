'''
constants.py
Game constants including colors, dimensions, and configuration.
'''
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT_COLOR = (255, 255, 0, 128)  # Semi-transparent yellow
# Board dimensions
BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_WIDTH = BOARD_SIZE * SQUARE_SIZE
BOARD_HEIGHT = BOARD_SIZE * SQUARE_SIZE
WINDOW_WIDTH = BOARD_WIDTH + 300  # Extra space for UI
WINDOW_HEIGHT = BOARD_HEIGHT
# Game states
PLAYER_ONE = 1
PLAYER_TWO = 2
EMPTY = 0
# Piece types
REGULAR = 1
KING = 2
# Directions
UP = -1
DOWN = 1
LEFT = -1
RIGHT = 1