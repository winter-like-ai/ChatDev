# Checkers (Draughts) Game - User Manual

## Overview
Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a graphical user interface built using Pygame. The game features an 8x8 board, two-player gameplay, standard capture rules, king promotion, and multiple jump capabilities.

## Main Features
- **Complete Checkers Gameplay**: Standard rules with 8x8 board
- **Graphical Interface**: Visual board with piece highlighting
- **Two-Player Mode**: Alternate turns between Red (Player 1) and Blue (Player 2)
- **King Pieces**: Regular pieces can be promoted to kings when reaching the opposite end
- **Capture Rules**: Mandatory captures and multiple jumps
- **Move Notation**: Real-time board state display in algebraic notation
- **Game Controls**: Reset and quit functionality
- **Visual Highlights**: 
  - Yellow: Selected piece
  - Green: Valid regular moves
  - Red: Valid capture moves

## System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.7 or higher
- **Pygame**: Version 2.0 or higher

## Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### Step 2: Install Pygame
Open your terminal or command prompt and run:
```bash
pip install pygame
```

### Step 3: Download Game Files
Create a folder for the game and download the following files:
- `main.py`
- `game.py`
- `board.py`
- `piece.py`
- `constants.py`

All files should be in the same directory.

## How to Play

### Starting the Game
1. Navigate to the game directory in your terminal
2. Run the game:
```bash
python main.py
```

### Game Interface
The game window consists of two main sections:
1. **Game Board (Left)**: 8x8 checkerboard with pieces
2. **Information Panel (Right)**: Game status, instructions, and board notation

### Game Rules
1. **Starting Position**:
   - Red pieces (Player 1) start on the top three rows
   - Blue pieces (Player 2) start on the bottom three rows
   - Pieces only occupy dark squares

2. **Movement**:
   - Regular pieces move diagonally forward one square
   - Kings can move diagonally in any direction
   - Pieces cannot move onto occupied squares

3. **Capturing**:
   - Jump over opponent's piece diagonally
   - Multiple jumps are allowed in the same turn
   - Captures are mandatory when available

4. **King Promotion**:
   - Regular pieces become kings when reaching the opposite end of the board
   - Kings can move and capture in any diagonal direction

### Controls
- **Mouse**: Click to select pieces and make moves
- **R Key**: Reset the game
- **Q Key**: Quit the game

### Playing a Turn
1. **Select Your Piece**: Click on one of your pieces (Red if it's Player 1's turn, Blue if it's Player 2's turn)
2. **View Valid Moves**:
   - Green squares show regular moves
   - Red squares show capture moves
3. **Make Your Move**:
   - Click on a green square for a regular move
   - Click on a red square to capture an opponent's piece
4. **Multiple Jumps**: If you capture a piece and have another capture available, you must continue jumping

### Move Notation
The right panel displays the board state in algebraic notation:
- **Lowercase letters**: Columns (a-h)
- **Numbers**: Rows (1-8 from bottom to top)
- **Piece symbols**:
  - `.`: Empty square
  - `r`: Red regular piece
  - `R`: Red king
  - `b`: Blue regular piece
  - `B`: Blue king

Example move: Moving from e3 to d4 would be shown as moving from square e3 to d4.

### Game End
The game ends when:
- One player captures all opponent pieces
- A player has no legal moves

The winner is announced with an overlay screen.

## Troubleshooting

### Common Issues
1. **Game won't start**:
   - Ensure all Python files are in the same directory
   - Verify Pygame is installed: `pip show pygame`
   - Check Python version: `python --version`

2. **No graphics appear**:
   - Make sure your system supports Pygame
   - Update graphics drivers if needed

3. **Game crashes**:
   - Restart the game with `R` key
   - Ensure no other programs are interfering with graphics

### Getting Help
If you encounter issues:
1. Check that all dependencies are properly installed
2. Verify file permissions
3. Ensure your system meets the requirements

## Tips for Better Gameplay
1. **Plan Ahead**: Try to set up multiple jumps
2. **Protect Your Back Row**: Pieces near promotion are valuable
3. **Control the Center**: Central pieces have more movement options
4. **Force Captures**: Position pieces to force opponent into disadvantageous captures

## Development Notes
This game was developed using:
- **Python 3.x** for the programming language
- **Pygame** for graphics and user interface
- **Object-Oriented Design** with separate classes for game logic, board, and pieces

The code follows clean architecture principles with:
- Separation of concerns
- Modular design
- Clear documentation
- Error handling

## License
This game is provided for educational and entertainment purposes. Feel free to modify and distribute with proper attribution.

Enjoy playing Checkers!