'''
constants.py
Game constants and configuration settings.
'''
# Board dimensions
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
WIDTH = COLS * SQUARE_SIZE
HEIGHT = ROWS * SQUARE_SIZE + 50  # Extra space for info panel
FPS = 60
# Players
PLAYER_RED = "RED"
PLAYER_BLUE = "BLUE"
EMPTY = None
# Colors (RGB)
LIGHT_BROWN = (210, 180, 140)
DARK_BROWN = (139, 69, 19)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)