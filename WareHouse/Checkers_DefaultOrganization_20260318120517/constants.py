'''
Game constants and configuration settings.
'''
# Window dimensions
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS
# Colors
RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT = (0, 255, 0, 100)  # Semi-transparent green
# Game settings
FPS = 60
PIECE_RADIUS = SQUARE_SIZE // 2 - 10
KING_CROWN_RADIUS = 15