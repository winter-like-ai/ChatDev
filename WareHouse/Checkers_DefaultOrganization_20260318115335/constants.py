'''
Game constants and configuration
'''
import pygame
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
# Create crown graphic programmatically
def create_crown_surface():
    """Create a crown graphic using Pygame drawing functions"""
    crown_surface = pygame.Surface((44, 25), pygame.SRCALPHA)
    # Draw crown base
    pygame.draw.rect(crown_surface, (255, 215, 0), (0, 15, 44, 10))  # Gold color
    # Draw crown points
    points = [(4, 15), (8, 5), (12, 15), (16, 5), (20, 15), (24, 5), (28, 15), (32, 5), (36, 15), (40, 5)]
    for i in range(0, len(points)-1, 2):
        pygame.draw.polygon(crown_surface, (255, 215, 0), 
                           [points[i], points[i+1], (points[i][0]+4, 15)])
    # Add jewel in the middle
    pygame.draw.circle(crown_surface, (255, 0, 0), (22, 10), 4)
    return crown_surface
CROWN = create_crown_surface()