'''
Constants for the Checkers game.
Defines colors, board dimensions, and other game constants.
'''
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (128, 128, 128)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT = (255, 255, 0, 128)  # Yellow with transparency
GOLD = (255, 215, 0)
# Board dimensions
ROWS = 8
COLS = 8
SQUARE_SIZE = 80
BOARD_WIDTH = COLS * SQUARE_SIZE
BOARD_HEIGHT = ROWS * SQUARE_SIZE
WINDOW_WIDTH = BOARD_WIDTH
WINDOW_HEIGHT = BOARD_HEIGHT + 100  # Extra space for UI
# Game states
PLAYER1_TURN = 1
PLAYER2_TURN = 2
GAME_OVER = 3
# Piece types
MAN = "man"
KING = "king"
# Players
PLAYER1 = 1
PLAYER2 = 2