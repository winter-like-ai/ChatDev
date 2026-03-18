'''
Constants and configuration for the Checkers game.
Defines colors, board dimensions, and game settings.
'''
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
GREEN = (0, 200, 0)
YELLOW = (255, 255, 0)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT = (255, 255, 0, 128)  # Semi-transparent yellow
# Board settings
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
BOARD_SIZE = SQUARE_SIZE * ROWS
PIECE_RADIUS = SQUARE_SIZE // 2 - 10
KING_RADIUS = PIECE_RADIUS - 5
# Game settings
FPS = 60
WINDOW_WIDTH = BOARD_SIZE
WINDOW_HEIGHT = BOARD_SIZE + 150  # Extra space for UI
# Player colors
PLAYER1_COLOR = RED
PLAYER2_COLOR = BLUE