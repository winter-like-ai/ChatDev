'''
gui.py
GUI rendering functions for the Checkers game.
'''
import pygame
from constants import *
def draw_board(screen):
    """Draw the checkers board."""
    for row in range(ROWS):
        for col in range(COLS):
            # Alternate colors for checkered pattern
            if (row + col) % 2 == 0:
                color = LIGHT_BROWN
            else:
                color = DARK_BROWN
            pygame.draw.rect(screen, color, 
                           (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                            SQUARE_SIZE, SQUARE_SIZE))
def draw_pieces(screen, board):
    """Draw all pieces on the board."""
    for row in range(ROWS):
        for col in range(COLS):
            piece = board.get_piece(row, col)
            if piece:
                # Draw piece circle
                color = RED if piece.color == PLAYER_RED else BLUE
                pygame.draw.circle(screen, color, 
                                 (piece.x, piece.y), 30)
                # Draw king crown
                if piece.king:
                    pygame.draw.circle(screen, YELLOW, 
                                     (piece.x, piece.y), 15)
                    # Draw K for king
                    font = pygame.font.Font(None, 24)  # Fixed: Use Font() instead of SysFont()
                    text = font.render("K", True, BLACK)
                    text_rect = text.get_rect(center=(piece.x, piece.y))
                    screen.blit(text, text_rect)
def draw_game_info(screen, current_player, winner):
    """Draw game information (current player, winner, instructions)."""
    # Draw info panel at bottom
    info_rect = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)
    pygame.draw.rect(screen, (40, 40, 40), info_rect)
    # Fixed: Use Font() instead of SysFont() to avoid Windows font enumeration issues
    font = pygame.font.Font(None, 28)
    if winner:
        text = f"Winner: {winner}! Press R to restart"
        color = RED if winner == PLAYER_RED else BLUE
    else:
        text = f"Current Player: {current_player}"
        color = RED if current_player == PLAYER_RED else BLUE
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT - 25))
    screen.blit(text_surface, text_rect)
    # Draw instructions
    instructions = "Click to select piece, click destination to move"
    instr_surface = font.render(instructions, True, WHITE)
    instr_rect = instr_surface.get_rect(center=(WIDTH // 2, 15))
    screen.blit(instr_surface, instr_rect)
def draw_selection(screen, row, col):
    """Draw a highlight around the selected piece."""
    pygame.draw.rect(screen, (255, 255, 0),
                    (col * SQUARE_SIZE, row * SQUARE_SIZE,
                     SQUARE_SIZE, SQUARE_SIZE), 4)
def draw_valid_move(screen, row, col):
    """Draw a circle to indicate a valid move position."""
    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2
    pygame.draw.circle(screen, (0, 255, 0), (center_x, center_y), 15, 3)