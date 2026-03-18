# Checkers Game - User Manual

## Overview
Checkers (also known as Draughts) is a classic two-player strategy board game. This implementation features a complete graphical interface with all standard rules, including piece movement, capturing, king promotion, and forced jumps.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux with X11
- **Python**: Version 3.8 or higher
- **RAM**: 512 MB minimum
- **Storage**: 10 MB free space
- **Display**: 800x800 resolution minimum

### Recommended Requirements
- **Operating System**: Latest version of Windows, macOS, or Linux
- **Python**: Version 3.10 or higher
- **RAM**: 1 GB or more
- **Display**: 1024x768 or higher resolution

## Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### Step 2: Install Pygame
Open your terminal or command prompt and run:
```bash
pip install pygame
```

### Step 3: Download the Game Files
Download the following files to the same directory:
- `main.py`
- `game.py`
- `gui.py`

## How to Play

### Starting the Game
1. Open a terminal or command prompt
2. Navigate to the directory containing the game files
3. Run the command:
```bash
python main.py
```

### Game Interface
The game window consists of:
- **Game Board**: 8x8 alternating brown and beige squares
- **Turn Indicator**: Top-left shows current player's turn
- **Piece Count**: Top-right shows remaining pieces for each player
- **Selected Piece**: Highlighted with green border
- **Valid Moves**: Green circles indicate possible destinations

### Game Rules

#### Starting Position
- Red pieces start on the top three rows
- White pieces start on the bottom three rows
- Pieces only occupy dark squares (brown)

#### Basic Movement
- **Regular Pieces**:
  - Red pieces move downward only
  - White pieces move upward only
  - Move one square diagonally forward to an empty dark square

- **Kings** (crowned pieces):
  - Can move both forward and backward
  - Move one square diagonally in any direction

#### Capturing (Jumping)
- Must capture opponent's piece if possible
- Jump over opponent's piece diagonally to an empty square
- Multiple jumps allowed in the same turn
- Captured pieces are removed from the board

#### King Promotion
- Regular piece reaches the opponent's back row (row 0 for white, row 7 for red)
- Automatically becomes a king
- Kings are marked with a gray circle in the center

### Controls

#### Mouse Controls
- **Left Click**: Select a piece or destination square
- **Click on your piece**: Select it to see valid moves
- **Click on valid move**: Move selected piece to that square

#### Keyboard Controls (Game Over Screen)
- **R Key**: Restart the game
- **ESC Key**: Quit the game

### Game Flow
1. Red player starts first
2. Players alternate turns
3. Select your piece (highlighted in green)
4. Valid moves appear as green circles
5. Click on destination to move
6. If a capture is possible, you must take it
7. Continue jumping if multiple captures are available
8. Game ends when one player has no pieces left

## Features

### Core Features
- **Complete Checkers Rules**: Implements all standard international draughts rules
- **Graphical Interface**: Clean, intuitive Pygame-based UI
- **Visual Feedback**: Clear highlighting of selected pieces and valid moves
- **Turn Management**: Automatic turn switching and validation
- **Game State Tracking**: Real-time piece count and turn display
- **Forced Capture**: Enforces mandatory jump rule
- **Multiple Jumps**: Supports consecutive jumps in a single turn
- **King Promotion**: Automatic crowning at opponent's back row

### Visual Elements
- **Color Coding**: Red vs White pieces with clear differentiation
- **King Indicator**: Gray center circle for crowned pieces
- **Selection Highlight**: Green border around selected piece
- **Move Indicators**: Green circles for valid destinations
- **Game Over Screen**: Victory message with restart options

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'pygame'"
```bash
pip install pygame
```

#### Game window doesn't open
- Ensure all three files are in the same directory
- Check Python installation: `python --version`
- Verify Pygame installation: `python -c "import pygame; print(pygame.version.ver)"`

#### Game runs but mouse clicks don't work
- Make sure you're clicking on valid squares (dark brown squares)
- Check if it's your turn (see turn indicator)
- Ensure piece selection is valid (your color only)

#### Performance issues
- Close other applications to free up system resources
- Reduce screen resolution if using integrated graphics

### Game Rules Clarifications

#### Mandatory Capture
If you have a capture available, you must take it. The game will not allow you to make a non-capturing move when a capture is possible.

#### Multiple Jumps
If after capturing a piece, you have another capture available with the same piece, you must continue jumping. The turn only ends when no more captures are possible.

#### King Movement
Kings can move both forward and backward, but still only one square at a time (unless capturing).

## Game Strategies

### Beginner Tips
1. **Control the Center**: Pieces in the center have more movement options
2. **Create Kings**: Get your pieces to the opponent's back row
3. **Force Captures**: Position pieces to create forced capture situations
4. **Protect Your Back Row**: Prevent opponent from getting kings
5. **Trade Wisely**: Sometimes sacrificing a piece can lead to better position

### Advanced Tactics
- **The Fork**: Position to threaten multiple opponent pieces
- **The Pin**: Trap opponent pieces against the board edge
- **The Sacrifice**: Give up a piece to gain positional advantage
- **King Dominance**: Use kings to control key diagonals

## Technical Details

### File Structure
```
checkers_game/
├── main.py      # Entry point and main game loop
├── game.py      # Core game logic and rules
└── gui.py       # Graphical interface and rendering
```

### Dependencies
- **Pygame**: 2.5.0 or higher (handles graphics and input)
- **Python Standard Library**: No additional dependencies required

### Code Architecture
- **Object-Oriented Design**: Separate classes for pieces, board, game, and GUI
- **Modular Structure**: Easy to extend or modify specific components
- **Event-Driven**: Responsive to user input through Pygame events

## Support

### Getting Help
If you encounter issues not covered in this manual:
1. Check the troubleshooting section above
2. Ensure you have the latest version of all files
3. Verify Python and Pygame installations

### Reporting Bugs
Please report any bugs or issues with:
- Python version
- Operating system
- Steps to reproduce the issue
- Screenshots if applicable

## License
This Checkers game implementation is provided for educational and entertainment purposes. The code is open for personal use and modification.

## Credits
Game developed using:
- **Python**: Programming language
- **Pygame**: Graphics and input library
- **Standard Checkers Rules**: International draughts ruleset

Enjoy the game! May the best strategist win!