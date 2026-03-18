# Checkers (Draughts) Game - User Manual

## Overview
Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a graphical interface. The game supports two players (Red and Blue) taking turns on an 8x8 board with standard checkers rules including piece movement, capturing, and king promotion.

## Main Features
- **Graphical Interface**: Clean, visually appealing board with colored pieces
- **Dual Input Methods**: 
  - Click-based piece selection and movement
  - Text-based move notation input (e.g., "a3-b4")
- **Complete Game Rules**:
  - Standard 8x8 board setup
  - Alternate turns between players
  - Mandatory capture rules
  - King promotion when reaching opponent's back row
  - Multiple captures in a single turn
- **Visual Feedback**:
  - Highlighted valid moves
  - Clear turn indication
  - Error messages for invalid moves
  - Winner announcement
- **Programmatically Generated Graphics**: No external image files required

## System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Python Version**: Python 3.7 or higher
- **Memory**: Minimum 512MB RAM
- **Display**: 800x600 resolution or higher

## Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### Step 2: Install Dependencies
Open a terminal or command prompt and run:

```bash
pip install pygame==2.5.2
```

### Step 3: Download Game Files
Create a folder for the game and download the following files:
- `main.py` - Main game entry point
- `constants.py` - Game constants and configuration
- `piece.py` - Piece class definition
- `board.py` - Board class definition
- `game.py` - Game logic and state management

All files should be in the same directory.

## How to Play

### Starting the Game
Run the game by executing:
```bash
python main.py
```

### Game Interface
The game window consists of:
1. **Game Board**: 8x8 checkerboard with pieces
2. **Current Player Indicator**: Shows whose turn it is (RED or BLUE)
3. **Move Input Box**: For entering moves in notation format
4. **Instructions**: Basic gameplay instructions
5. **Error Messages**: Displayed in red when moves are invalid

### Game Setup
- Red pieces start at the bottom three rows
- Blue pieces start at the top three rows
- Red moves first
- Pieces can only move on dark squares

### Movement Rules
1. **Regular Pieces**:
   - Move diagonally forward one square
   - Can only move to empty squares
   - Cannot move backward

2. **Kings**:
   - Move diagonally forward or backward
   - Can move multiple squares in one direction

3. **Capturing**:
   - Jump over opponent's piece to capture it
   - Must capture if possible (mandatory capture rule)
   - Multiple captures allowed in one turn
   - Captured pieces are removed from the board

4. **King Promotion**:
   - Regular pieces become kings when reaching the opponent's back row
   - Red pieces become kings when reaching row 0 (top)
   - Blue pieces become kings when reaching row 7 (bottom)

### Input Methods

#### Method 1: Mouse Controls
1. **Select a Piece**: Click on your piece (it must be your turn)
2. **View Valid Moves**: Selected piece's valid moves will be highlighted in green
3. **Make a Move**: Click on a highlighted square to move
4. **Multiple Captures**: If additional captures are possible, the piece remains selected

#### Method 2: Text Notation
1. **Activate Input Box**: Click on the text input box at the bottom of the screen
2. **Enter Move**: Type move in "from-to" notation (e.g., "a3-b4")
   - Letters a-h represent columns (left to right)
   - Numbers 1-8 represent rows (bottom to top)
   - Example: "a3-b4" moves from column a, row 3 to column b, row 4
3. **Submit Move**: Press Enter to execute the move
4. **Clear Input**: Use Backspace to correct mistakes

### Notation Examples
- `a3-b4`: Move from a3 to b4
- `c2-d3`: Move from c2 to d3
- `b4-a5`: Move from b4 to a5 (capture move)
- `g7-h8`: Move from g7 to h8 (king promotion for Red)

### Game End Conditions
The game ends when:
1. **No Pieces Left**: One player loses all pieces
2. **No Valid Moves**: A player cannot make any legal moves
3. **Resignation**: Close the game window

The winner is announced at the top of the screen when the game ends.

## Troubleshooting

### Common Issues

1. **Game won't start**:
   - Ensure all Python files are in the same directory
   - Verify pygame is installed: `pip show pygame`
   - Check Python version: `python --version`

2. **No valid moves highlighted**:
   - Make sure it's your turn
   - Check if you have mandatory captures
   - Verify you selected your own piece

3. **Text input not working**:
   - Click on the input box to activate it
   - Ensure the cursor is blinking in the box
   - Check for error messages in red

4. **Pieces not moving**:
   - Verify you're moving to a dark square
   - Check if the move follows checkers rules
   - Look for mandatory capture requirements

### Error Messages
- **"Invalid piece selection"**: You selected an opponent's piece or empty square
- **"Invalid move"**: The move is not allowed by checkers rules
- **"Invalid notation"**: Text input format is incorrect
- **"From position out of bounds"**: Starting position doesn't exist on board
- **"To position out of bounds"**: Target position doesn't exist on board

## Tips for Better Gameplay
1. **Plan Ahead**: Try to set up multiple captures
2. **Protect Your Back Row**: Prevent opponent pieces from becoming kings
3. **Use Kings Wisely**: Kings can move backward - use this to your advantage
4. **Force Captures**: Position pieces to force opponent into disadvantageous captures
5. **Control the Center**: Center squares offer more movement options

## Game Controls Summary
- **Mouse**: Select and move pieces
- **Keyboard**: Enter move notation in input box
- **Enter**: Submit text move
- **Backspace**: Delete text in input box
- **Window Close Button**: Exit game

## Support
For issues or questions:
1. Check the troubleshooting section above
2. Verify all files are correctly installed
3. Ensure you have the latest version of pygame

Enjoy your game of Checkers!