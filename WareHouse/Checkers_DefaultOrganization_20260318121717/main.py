'''
Main entry point for the Checkers game.
Handles Pygame initialization, game loop, rendering, and text input for move notation.
'''
import pygame
import sys
from game import Game
from constants import *
import pygame_textinput
def main():
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Checkers Game")
    clock = pygame.time.Clock()
    # Initialize game
    game = Game()
    # Initialize text input for move notation
    textinput = pygame_textinput.TextInputVisualizer()
    textinput.font_color = TEXT_COLOR
    textinput.cursor_color = TEXT_COLOR
    input_active = False
    error_message = ""
    error_timer = 0
    # Game loop
    running = True
    selected_piece = None
    valid_moves = []
    while running:
        # Feed textinput with events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    pos = pygame.mouse.get_pos()
                    row = pos[1] // SQUARE_SIZE
                    col = pos[0] // SQUARE_SIZE
                    # Check if clicking on text input area
                    input_rect = pygame.Rect(WIDTH - 200, 100, 180, 30)
                    if input_rect.collidepoint(pos):
                        input_active = True
                        textinput.value = ""
                    else:
                        input_active = False
                    if selected_piece:
                        # Try to move the selected piece
                        if (row, col) in valid_moves:
                            game.make_move(selected_piece, (row, col))
                            selected_piece = None
                            valid_moves = []
                            error_message = ""
                        else:
                            # Select a different piece
                            piece = game.board.get_piece(row, col)
                            if piece and piece.color == game.turn:
                                selected_piece = (row, col)
                                valid_moves = game.get_valid_moves(row, col)
                                error_message = ""
                            else:
                                selected_piece = None
                                valid_moves = []
                    else:
                        # Select a piece
                        piece = game.board.get_piece(row, col)
                        if piece and piece.color == game.turn:
                            selected_piece = (row, col)
                            valid_moves = game.get_valid_moves(row, col)
                            error_message = ""
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset game
                    game = Game()
                    selected_piece = None
                    valid_moves = []
                    error_message = ""
                    input_active = False
                    textinput.value = ""
                elif event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_RETURN and input_active and textinput.value.strip():
                    # Process move notation
                    move_text = textinput.value.strip()
                    success = game.process_notation_move(move_text)
                    if success:
                        selected_piece = None
                        valid_moves = []
                        textinput.value = ""
                        error_message = ""
                    else:
                        error_message = "Invalid move notation"
                        error_timer = 60  # Show error for 1 second at 60 FPS
                elif event.key == pygame.K_TAB:
                    # Toggle input active with Tab key
                    input_active = not input_active
                    if input_active:
                        textinput.value = ""
        # Update text input
        if input_active:
            textinput.update(events)
        # Update error timer
        if error_timer > 0:
            error_timer -= 1
            if error_timer == 0:
                error_message = ""
        # Draw everything
        screen.fill(BACKGROUND)
        draw_board(screen)
        draw_pieces(screen, game.board)
        draw_ui(screen, game, textinput, input_active, error_message)
        # Highlight selected piece and valid moves
        if selected_piece:
            row, col = selected_piece
            pygame.draw.rect(screen, HIGHLIGHT, 
                           (col * SQUARE_SIZE, row * SQUARE_SIZE, 
                            SQUARE_SIZE, SQUARE_SIZE), 3)
            for move_row, move_col in valid_moves:
                pygame.draw.circle(screen, VALID_MOVE, 
                                 (move_col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                  move_row * SQUARE_SIZE + SQUARE_SIZE // 2),
                                 SQUARE_SIZE // 6)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
    sys.exit()
def draw_board(screen):
    """Draw the checkers board."""
    for row in range(ROWS):
        for col in range(COLS):
            color = DARK_SQUARE if (row + col) % 2 == 0 else LIGHT_SQUARE
            pygame.draw.rect(screen, color,
                           (col * SQUARE_SIZE, row * SQUARE_SIZE,
                            SQUARE_SIZE, SQUARE_SIZE))
def draw_pieces(screen, board):
    """Draw all pieces on the board."""
    for row in range(ROWS):
        for col in range(COLS):
            piece = board.get_piece(row, col)
            if piece:
                # Draw piece
                color = RED if piece.color == 'red' else WHITE
                pygame.draw.circle(screen, color,
                                 (col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                  row * SQUARE_SIZE + SQUARE_SIZE // 2),
                                 PIECE_RADIUS)
                # Draw king crown
                if piece.king:
                    pygame.draw.circle(screen, YELLOW,
                                     (col * SQUARE_SIZE + SQUARE_SIZE // 2,
                                      row * SQUARE_SIZE + SQUARE_SIZE // 2),
                                     PIECE_RADIUS // 2)
def draw_ui(screen, game, textinput, input_active, error_message):
    """Draw game status, instructions, and text input."""
    # Draw current turn
    font = pygame.font.SysFont(None, 36)
    turn_text = f"Turn: {'Red' if game.turn == 'red' else 'White'}"
    turn_surface = font.render(turn_text, True, TEXT_COLOR)
    screen.blit(turn_surface, (WIDTH - 200, 20))
    # Draw move notation
    if game.last_move:
        notation = game.get_notation_move(game.last_move)
        move_surface = font.render(f"Last move: {notation}", True, TEXT_COLOR)
        screen.blit(move_surface, (WIDTH - 200, 60))
    # Draw text input for move notation
    input_label = font.render("Enter move (e.g., a3-b4):", True, TEXT_COLOR)
    screen.blit(input_label, (WIDTH - 200, 100))
    # Draw text input box
    input_rect = pygame.Rect(WIDTH - 200, 130, 180, 30)
    pygame.draw.rect(screen, WHITE if input_active else (100, 100, 100), input_rect, 2)
    screen.blit(textinput.surface, (WIDTH - 195, 135))
    # Draw error message
    if error_message:
        error_font = pygame.font.SysFont(None, 24)
        error_surface = error_font.render(error_message, True, (255, 50, 50))
        screen.blit(error_surface, (WIDTH - 200, 170))
    # Draw instructions
    font_small = pygame.font.SysFont(None, 24)
    instructions = [
        "Instructions:",
        "1. Click on a piece to select it",
        "2. Click on highlighted square to move",
        "3. Or enter move in notation (a3-b4)",
        "4. Tab: Toggle text input",
        "5. R: Reset game",
        "6. Q: Quit game"
    ]
    for i, line in enumerate(instructions):
        text_surface = font_small.render(line, True, TEXT_COLOR)
        screen.blit(text_surface, (10, HEIGHT - 180 + i * 25))
    # Draw winner if game ended
    if game.winner:
        winner_text = f"Winner: {'Red' if game.winner == 'red' else 'White'}!"
        winner_surface = font.render(winner_text, True, WINNER_COLOR)
        screen.blit(winner_surface, (WIDTH // 2 - 100, HEIGHT // 2 - 50))
if __name__ == "__main__":
    main()