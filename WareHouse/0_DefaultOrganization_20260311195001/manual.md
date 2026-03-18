# Checkers Game - User Manual

## Overview

Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a modern graphical interface. The game follows standard checkers rules with an 8x8 board, alternating turns between two players, and includes capture and kinging mechanics.

## Main Features

### 🎮 Core Gameplay
- **Two-player gameplay** - Red vs White pieces
- **Standard checkers rules** - Including mandatory captures
- **King pieces** - Pieces that reach the opposite end become kings with enhanced movement
- **Visual feedback** - Clear highlighting of selected pieces and valid moves
- **Move notation** - Automatic notation display for each move

### 🖥️ User Interface
- **Clean, intuitive board** - Traditional checkers color scheme
- **Visual indicators**:
  - Green highlight for selected pieces
  - Light blue highlight for valid moves
  - Gold crown for king pieces
- **Status display** - Shows current player and game state
- **Move prompt** - Clear instructions for gameplay

### ⚙️ Technical Features
- **Complete game logic** - Validates all moves according to checkers rules
- **Mandatory capture enforcement** - Automatically detects when captures are required
- **Game state management** - Tracks pieces, turns, and win conditions
- **Error handling** - Prevents illegal moves

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10, macOS 10.15+, or Linux
- **Python**: Version 3.7 or higher
- **RAM**: 512 MB minimum
- **Storage**: 10 MB free space

### Recommended Requirements
- **Operating System**: Latest version of Windows, macOS, or Linux
- **Python**: Version 3.9 or higher
- **RAM**: 1 GB or more
- **Storage**: 50 MB free space

## Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

Verify installation by opening a terminal/command prompt and typing:
```bash
python --version
```

### Step 2: Install Pygame
The game requires Pygame for the graphical interface. Install it using pip:

```bash
pip install pygame
```

### Step 3: Download Game Files
Create a new folder for the game and download these three files:
1. `main.py` - Main game launcher
2. `checkersgame.py` - Core game logic
3. `gamegui.py` - Graphical interface

All three files must be in the same directory.

## How to Play

### Starting the Game
1. Navigate to the game directory in your terminal/command prompt
2. Run the game:
   ```bash
   python main.py
   ```

### Game Controls
- **Mouse**: Click to select pieces and make moves
- **Close Window**: Click the X button or press Alt+F4 to exit

### Game Rules

#### Basic Movement
- **Red pieces** start at the top (rows 0-2) and move downward
- **White pieces** start at the bottom (rows 5-7) and move upward
- Regular pieces move diagonally forward one square
- Kings can move diagonally in any direction

#### Capturing
- Jump over opponent's pieces to capture them
- Captures are mandatory when available
- Multiple captures in one turn are allowed
- Captured pieces are removed from the board

#### Kinging
- A piece becomes a king when it reaches the opposite end of the board
- Red pieces king on row 7
- White pieces king on row 0
- Kings are marked with a gold crown and can move backward

### Game Flow

1. **Starting the Game**
   - Red player goes first
   - Click on any red piece to select it

2. **Making a Move**
   - Click on a piece of your color
   - Valid moves will be highlighted in light blue
   - Click on a highlighted square to move there
   - If captures are available, only capture moves will be shown

3. **Special Situations**
   - **Mandatory Capture**: If you can capture, you must capture
   - **Multiple Jumps**: If you capture and can capture again with the same piece, you must continue
   - **King Promotion**: Automatic when reaching the opposite end

4. **Winning the Game**
   - Capture all opponent pieces, OR
   - Block all opponent pieces from moving

### Move Notation
The game uses algebraic notation similar to chess:
- Columns: a-h (left to right)
- Rows: 1-8 (bottom to top)
- Example: "a3-b4" means moving from column a, row 3 to column b, row 4

Moves are printed in the console for reference.

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'pygame'"
Solution: Install Pygame using `pip install pygame`

#### Game window doesn't open
Solution: Ensure all three Python files are in the same directory

#### Pieces won't move
Solution: Check if you're clicking valid squares (only dark squares are playable)

#### Game seems frozen
Solution: Check the status display - you may need to capture an opponent's piece

### Performance Issues
- If the game runs slowly, try closing other applications
- Reduce screen resolution if using an older computer

## Game Files Structure

```
checkers_game/
├── main.py          # Game launcher and main loop
├── checkersgame.py  # Game logic and rules
└── gamegui.py       # Graphical interface
```

## Advanced Features

### For Developers
The code is modular and well-documented:
- `CheckersGame` class handles all game logic
- `Board` class manages piece positions
- `GameGUI` class handles display and user input

### Extending the Game
You can modify:
- Board colors in `gamegui.py`
- Piece colors and sizes
- Game rules in `checkersgame.py`
- Add features like undo/redo, AI opponent, or network play

## Support

### Getting Help
If you encounter issues:
1. Check the console for error messages
2. Verify Pygame is installed correctly
3. Ensure Python version is 3.7 or higher

### Reporting Bugs
Please report any issues with:
- Steps to reproduce
- Error messages
- Your system configuration

## Credits

This Checkers game was developed as a demonstration project featuring:
- Complete checkers rule implementation
- Clean graphical interface using Pygame
- Modular, maintainable code structure

Enjoy your game of Checkers!