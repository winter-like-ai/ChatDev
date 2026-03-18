# Checkers Game - User Manual

## Overview
Welcome to the Checkers (Draughts) game! This is a classic two-player board game implemented in Python with a graphical user interface using PyGame. The game features an 8x8 board, alternating turns between red and blue players, and implements standard capture and kinging rules.

## Main Features
- **Complete Checkers Gameplay**: Full implementation of standard checkers rules
- **Graphical Interface**: Clean, visually appealing board with intuitive controls
- **Forced Capture Enforcement**: The game automatically enforces mandatory capture rules
- **King Promotion**: Pieces are promoted to kings when reaching the opposite end of the board
- **Multiple Jumps**: Support for consecutive captures in a single turn
- **Win Detection**: Automatic detection of game winners
- **Game Reset**: Easy restart functionality

## System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.7 or higher
- **Memory**: Minimum 512MB RAM
- **Display**: 640x640 pixels minimum resolution

## Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### Step 2: Install PyGame
Open your terminal or command prompt and install PyGame using pip:

```bash
pip install pygame
```

### Step 3: Download Game Files
Download all the game files to a folder on your computer:
- `constants.py`
- `piece.py`
- `board.py`
- `game.py`
- `main.py`

## How to Play

### Starting the Game
1. Navigate to the folder containing the game files in your terminal/command prompt
2. Run the game by executing:
   ```bash
   python main.py
   ```

### Game Controls
- **Mouse**: Click to select pieces and make moves
- **R Key**: Reset the game at any time
- **ESC Key**: Exit the game
- **Close Window**: Click the X button to quit

### Game Rules
1. **Starting Position**: Red pieces start at the bottom three rows, blue pieces at the top three rows
2. **Turn Order**: Red moves first, then players alternate turns
3. **Movement**:
   - Regular pieces move diagonally forward one square
   - Kings can move diagonally forward or backward
4. **Capturing**:
   - Jump over opponent's pieces diagonally
   - Multiple jumps in one turn are allowed
   - Captures are mandatory when available
5. **King Promotion**:
   - Red pieces become kings when reaching row 0 (top)
   - Blue pieces become kings when reaching row 7 (bottom)
   - Kings are marked with a yellow "K"

### Game Interface
- **Board**: 8x8 alternating light and dark brown squares
- **Pieces**: Red circles (player one) and blue circles (player two)
- **Kings**: Display a yellow "K" in the center
- **Valid Moves**: Highlighted with yellow circles
- **Status Message**: Displayed at the bottom showing whose turn it is or game results

### Playing a Turn
1. **Select a Piece**: Click on one of your pieces
   - Valid moves will be highlighted with yellow circles
   - If captures are available, you must select a piece that can capture
2. **Make a Move**: Click on a highlighted square to move
   - If you capture a piece, check if additional jumps are available
   - The turn automatically ends when no more moves are possible
3. **Continue Playing**: The game alternates turns until one player wins

### Winning the Game
- The game ends when one player captures all of the opponent's pieces
- A victory message will display at the bottom of the screen
- Press 'R' to reset and play again

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'pygame'"**
   - Solution: Run `pip install pygame` in your terminal

2. **Game window doesn't open**
   - Solution: Ensure you're running `python main.py` from the correct directory
   - Check that all game files are in the same folder

3. **Game runs but pieces don't move**
   - Solution: Make sure you're clicking on valid squares
   - Check if captures are mandatory - the game will prevent invalid moves

4. **Graphics appear distorted**
   - Solution: Ensure your display resolution supports at least 640x640 pixels

### Game Reset
If the game becomes unresponsive or you want to start over:
- Press the 'R' key at any time
- Or close and restart the game

## Game Files Structure
- `main.py` - Main game loop and window management
- `game.py` - Game logic and state management
- `board.py` - Board representation and drawing
- `piece.py` - Piece class and movement logic
- `constants.py` - Game constants and configuration

## Tips for Better Gameplay
1. **Plan Ahead**: Try to set up multiple jumps
2. **Protect Your Back Row**: Pieces in the back row are safe from immediate capture
3. **King Strategy**: Get your pieces to the opposite end to create kings
4. **Forced Captures**: Remember that captures are mandatory when available

## Support
For issues or questions about the game:
1. Check that you have the latest version of Python and PyGame
2. Ensure all game files are in the same directory
3. Review the troubleshooting section above

Enjoy playing Checkers!