'''
Game constants and configuration
'''
# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)
LIGHT_BROWN = (222, 184, 135)
DARK_BROWN = (139, 69, 19)
HIGHLIGHT = (255, 255, 0, 128)  # Yellow with transparency
# Game dimensions
SQUARE_SIZE = 80
ROWS = 8
COLS = 8
WIDTH = COLS * SQUARE_SIZE
HEIGHT = ROWS * SQUARE_SIZE + 100  # Extra space for UI
# Game settings
FPS = 60
CROWN = pygame.transform.scale(pygame.image.load('crown.png'), (44, 25))