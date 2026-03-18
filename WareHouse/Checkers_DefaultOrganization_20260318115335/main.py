'''
Checkers Game - Main Entry Point
Initializes Pygame and runs the main game loop
'''
import pygame
import sys
from game import Game
from constants import WIDTH, HEIGHT, SQUARE_SIZE, FPS, WHITE, BLACK, RED, BLUE
def get_row_col_from_mouse(pos):
    """Convert mouse position to board coordinates"""
    x, y = pos
    row = y // SQUARE_SIZE
    col = x // SQUARE_SIZE
    return row, col
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Checkers Game")
    clock = pygame.time.Clock()
    game = Game(screen)
    # Font for move notation display
    font = pygame.font.SysFont('Arial', 24)
    move_input = ""
    input_active = False
    input_rect = pygame.Rect(10, HEIGHT - 40, 200, 30)
    error_message = ""
    error_timer = 0
    while True:
        clock.tick(FPS)
        # Clear error message after 2 seconds
        if error_timer > 0:
            error_timer -= 1
            if error_timer == 0:
                error_message = ""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                row, col = get_row_col_from_mouse(pos)
                # Check if click is on board
                if row < 8 and col < 8:
                    game.select(row, col)
                else:
                    # Check if click is on input box
                    if input_rect.collidepoint(pos):
                        input_active = True
                    else:
                        input_active = False
            if event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        # Process move notation
                        if move_input:
                            try:
                                # Parse notation like "a3-b4" or "A3-B4"
                                parts = move_input.split('-')
                                if len(parts) == 2:
                                    from_pos = parts[0].strip().lower()
                                    to_pos = parts[1].strip().lower()
                                    # Validate input format
                                    if len(from_pos) != 2 or len(to_pos) != 2:
                                        raise ValueError("Invalid format")
                                    # Convert notation to coordinates
                                    # Format: letter (a-h) + number (1-8)
                                    if not ('a' <= from_pos[0] <= 'h' and '1' <= from_pos[1] <= '8'):
                                        raise ValueError("Invalid from position")
                                    if not ('a' <= to_pos[0] <= 'h' and '1' <= to_pos[1] <= '8'):
                                        raise ValueError("Invalid to position")
                                    col_from = ord(from_pos[0]) - ord('a')
                                    row_from = 8 - int(from_pos[1])
                                    col_to = ord(to_pos[0]) - ord('a')
                                    row_to = 8 - int(to_pos[1])
                                    # Validate board coordinates
                                    if not (0 <= row_from < 8 and 0 <= col_from < 8):
                                        raise ValueError("From position out of bounds")
                                    if not (0 <= row_to < 8 and 0 <= col_to < 8):
                                        raise ValueError("To position out of bounds")
                                    # Try to make the move
                                    if game.select(row_from, col_from):
                                        if game.select(row_to, col_to):
                                            error_message = ""
                                        else:
                                            error_message = "Invalid move"
                                            error_timer = 120  # 2 seconds at 60 FPS
                                    else:
                                        error_message = "Invalid piece selection"
                                        error_timer = 120
                                    move_input = ""
                                else:
                                    error_message = "Use format: a3-b4"
                                    error_timer = 120
                                    move_input = ""
                            except (ValueError, IndexError) as e:
                                error_message = f"Invalid notation: {str(e)}"
                                error_timer = 120
                                move_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        move_input = move_input[:-1]
                    else:
                        move_input += event.unicode
        # Draw everything
        screen.fill(WHITE)
        game.draw()
        # Draw input box for move notation
        pygame.draw.rect(screen, (200, 200, 200), input_rect, 2)
        text_surface = font.render("Move: " + move_input, True, BLACK)
        screen.blit(text_surface, (input_rect.x + 5, input_rect.y + 5))
        # Draw instructions
        instructions = [
            "Click pieces to select and move",
            "Or enter moves in notation (e.g., 'a3-b4')",
            f"Current player: {'RED' if game.turn == RED else 'BLUE'}"
        ]
        for i, text in enumerate(instructions):
            text_surface = font.render(text, True, BLACK)
            screen.blit(text_surface, (10, HEIGHT - 100 + i * 25))
        # Draw error message if any
        if error_message:
            error_surface = font.render(error_message, True, (255, 0, 0))
            screen.blit(error_surface, (WIDTH - 300, HEIGHT - 40))
        # Check for winner
        winner = game.check_winner()
        if winner:
            winner_text = f"{'RED' if winner == RED else 'BLUE'} WINS!"
            text_surface = font.render(winner_text, True, (0, 100, 0))
            screen.blit(text_surface, (WIDTH // 2 - 100, 10))
        pygame.display.flip()
if __name__ == "__main__":
    main()