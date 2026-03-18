'''
Constants and configuration for the Checkers game.
Defines colors, board dimensions, and game settings.
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
HIGHLIGHT = (255, 255, 0, 128)  # Semi-transparent yellow
# Board dimensions
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
WIDTH = COLS * SQUARE_SIZE
HEIGHT = ROWS * SQUARE_SIZE + 100  # Extra space for UI
# Game settings
FPS = 60
PLAYER1_COLOR = RED
PLAYER2_COLOR = BLUE