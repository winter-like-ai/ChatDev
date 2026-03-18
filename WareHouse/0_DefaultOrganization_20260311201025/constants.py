'''
Constants for the Checkers game.
Contains colors, board dimensions, and other game constants.
'''
# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT = (255, 255, 0, 128)  # Yellow with transparency
# Board dimensions
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
WIDTH = COLS * SQUARE_SIZE
HEIGHT = ROWS * SQUARE_SIZE
PADDING = 50
# Game settings
FPS = 60
CROWN_IMG = "crown.png"  # Will be created programmatically