# Checkers Game - User Manual

## 🎮 Overview

Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a modern graphical interface. The game follows standard checkers rules with an 8x8 board, alternating turns between two players, mandatory capture rules, and king promotion.

## ✨ Key Features

- **Complete Checkers Implementation**: Full adherence to standard checkers rules
- **Graphical User Interface**: Clean, intuitive visual interface using Pygame
- **Mandatory Capture Rule**: Enforces capture when available
- **Capture Chains**: Supports multiple captures in a single turn
- **King Promotion**: Regular pieces become kings when reaching the opposite end
- **Move Notation**: Displays moves in algebraic notation (e.g., "C3 to D4")
- **Turn Indicators**: Clear visual indication of whose turn it is
- **Game State Tracking**: Tracks move history and game progress
- **Win Detection**: Automatically detects game end conditions

## 🛠️ System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Python**: Version 3.8 or higher
- **RAM**: 512 MB minimum
- **Storage**: 10 MB free space

### Recommended
- **Display**: 1024x768 resolution or higher
- **Python**: Version 3.10 or higher

## 📦 Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### Step 2: Install Pygame
Open your terminal or command prompt and run:

```bash
pip install pygame>=2.5.0
```

### Step 3: Download Game Files
Create a folder for the game and download the following files:
- `main.py`
- `constants.py`
- `piece.py`
- `board.py`
- `game.py`
- `requirements.txt`

All files should be in the same directory.

## 🚀 How to Start the Game

1. Open a terminal or command prompt
2. Navigate to the game directory:
   ```bash
   cd path/to/checkers/game
   ```
3. Run the game:
   ```bash
   python main.py
   ```

## 🎯 How to Play

### Game Setup
- **Red Pieces**: Start at the top three rows
- **Blue Pieces**: Start at the bottom three rows
- **Red Player**: Always moves first
- **Game Board**: 8x8 alternating dark and light squares

### Basic Rules
1. **Movement**:
   - Regular pieces move diagonally forward one square
   - Kings can move diagonally forward or backward
   - You can only move to empty dark squares

2. **Capturing**:
   - Jump over opponent's piece diagonally
   - Land on empty square immediately beyond
   - Captured pieces are removed from the board
   - **Capture is mandatory** when available

3. **King Promotion**:
   - Red pieces become kings when reaching row 8 (bottom)
   - Blue pieces become kings when reaching row 1 (top)
   - Kings are marked with a white circle and "K"

4. **Capture Chains**:
   - If you can make another capture after capturing, you must continue
   - The same piece continues capturing until no more captures are possible

### Game Controls
- **Mouse Click**: Select pieces and make moves
- **Close Window**: Click the X button to exit
- **Restart**: Close and restart the application to play again

### Playing a Turn
1. **Select a Piece**: Click on your piece (red or blue depending on turn)
   - Valid moves will be highlighted in yellow
   - If capture is mandatory, only capture moves will be shown

2. **Make a Move**: Click on a highlighted square
   - For regular moves: Click adjacent diagonal square
   - For captures: Click two squares away (over opponent's piece)

3. **Continue Chain** (if applicable):
   - If additional captures are possible, select the same piece again
   - Continue until no more captures are available

### Game Interface Elements
- **Top Section**: Game board with pieces
- **Bottom Panel**:
  - Turn indicator (Red's Turn / Blue's Turn)
  - Capture requirement warning (when applicable)
  - Move notation prompt
  - Last move display
  - Game over message (when game ends)

### Move Notation
The game uses algebraic notation similar to chess:
- **Columns**: A-H (left to right)
- **Rows**: 1-8 (bottom to top)
- **Example**: "C3 to D4" means moving from column C, row 3 to column D, row 4

## 🏆 Winning the Game

You win by:
1. **Capturing All Opponent Pieces**: Remove all opponent pieces from the board
2. **Blocking All Moves**: Opponent has no valid moves left

The game automatically detects and announces the winner.

## 🎨 Visual Elements

### Board Colors
- **Light Brown**: Light squares
- **Dark Brown**: Dark squares (playable squares)
- **Red**: Player 1 pieces
- **Blue**: Player 2 pieces
- **Yellow Highlight**: Valid move destinations
- **White Circle with K**: King pieces

### Status Indicators
- **Green Text**: "Capture is mandatory!" (when applicable)
- **Red/Blue Text**: Current player's turn
- **Gray Text**: Last move made
- **White Text on Black**: Game over message

## 🔧 Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'pygame'"**
   ```bash
   pip install pygame
   ```

2. **Game window doesn't open**
   - Ensure all game files are in the same directory
   - Check Python installation: `python --version`
   - Verify Pygame installation: `python -c "import pygame; print(pygame.version.ver)"`

3. **Game runs but pieces don't move**
   - Make sure you're clicking on your own pieces during your turn
   - Check if capture is mandatory (green warning text)
   - Verify you're clicking on highlighted squares

4. **Performance issues**
   - Close other applications to free up system resources
   - Reduce screen resolution if using high-resolution display

### Game Rules Clarifications
- **Mandatory Capture**: If you can capture, you must capture. Regular moves are not allowed.
- **Multiple Captures**: You must continue capturing if possible with the same piece.
- **King Movement**: Kings can move and capture both forward and backward.
- **Backward Movement**: Regular pieces cannot move backward, even to capture.

## 📝 Game Files Description

- `main.py`: Main entry point, initializes and runs the game loop
- `constants.py`: Game configuration, colors, and dimensions
- `piece.py`: Piece class with movement and capture logic
- `board.py`: Board management and rendering
- `game.py`: Game state management, rules, and user interface
- `requirements.txt`: Python dependencies

## 🔄 Restarting the Game

To play again after a game ends:
1. Close the game window
2. Run `python main.py` again

## 🤝 Two-Player Game

This is a local two-player game. Players take turns using the same computer:
1. Player 1 controls Red pieces
2. Player 2 controls Blue pieces
3. Players alternate turns after each valid move

## 📊 Game Statistics

The game tracks:
- Move history (last move displayed)
- Turn count (implied by turn switching)
- Piece count (visible on board)
- Game state (active/ended)

## 🎮 Tips for Beginners

1. **Control the Center**: Pieces in the center have more movement options
2. **Create Kings**: Get your pieces to the opposite end to promote them
3. **Force Captures**: Position pieces to force opponent into capture situations
4. **Protect Your Back Row**: Keep pieces in your back row to prevent king promotions
5. **Plan Ahead**: Think about where your pieces will end up after captures

## 🆘 Getting Help

If you encounter issues not covered in this manual:
1. Check that all game files are present and in the same directory
2. Verify Python and Pygame versions meet requirements
3. Ensure you have necessary permissions to run Python applications

## 📄 License

This Checkers game is provided for educational and entertainment purposes. The code follows standard checkers rules and implements a complete game experience.

---

Enjoy playing Checkers! May the best strategist win! 🏁