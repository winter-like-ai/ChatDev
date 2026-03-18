'''
Game constants including colors, board dimensions, and game settings.
'''
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
LIGHT_BROWN = (210, 180, 140)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT_COLOR = (255, 255, 0, 128)  # Yellow with transparency
# Board settings
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
PIECE_RADIUS = 30
KING_OFFSET = 15
# Window settings
WIDTH = COLS * SQUARE_SIZE
HEIGHT = ROWS * SQUARE_SIZE
FPS = 60
# Game settings
PLAYER_COLORS = ['red', 'blue']