# Checkers Game - User Manual

## Overview
Checkers (also known as Draughts) is a classic two-player strategy board game. This implementation features a complete graphical interface with all standard rules, including mandatory captures and king promotion.

## Main Features
- **Complete Game Logic**: Implements all standard checkers rules
- **Graphical Interface**: Clean, intuitive PyGame-based interface
- **Visual Feedback**: Highlights selected pieces, valid moves, and mandatory captures
- **Mandatory Capture Enforcement**: Automatically enforces capture rules
- **King Promotion**: Pieces become kings when reaching the opposite end
- **Multiple Capture Support**: Allows consecutive captures with the same piece
- **Win Detection**: Automatically detects when a player wins
- **Game Controls**: Easy reset and quit functionality

## System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.7 or higher
- **RAM**: Minimum 512MB
- **Display**: 640x640 resolution or higher

## Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### Step 2: Install PyGame
Open your terminal or command prompt and run:

```bash
pip install pygame
```

### Step 3: Download the Game Files
Download all the game files to a folder on your computer:
- `constants.py`
- `piece.py`
- `game.py`
- `gui.py`
- `main.py`

## How to Play

### Starting the Game
1. Navigate to the folder containing the game files
2. Run the game by executing:
   ```bash
   python main.py
   ```

### Game Setup
- The game starts with Red pieces at the bottom and Blue pieces at the top
- Red player always goes first
- Pieces can only move on dark squares (brown squares)

### Basic Controls
- **Left Click**: Select a piece or make a move
- **R Key**: Reset the game to start over
- **ESC Key**: Quit the game
- **Close Window**: Click the X button to exit

### Game Rules

#### Movement
1. **Regular Pieces**:
   - Red pieces move diagonally downward (toward the top of the screen)
   - Blue pieces move diagonally upward (toward the bottom of the screen)
   - Can only move one square diagonally to an empty dark square

2. **Kings**:
   - Can move diagonally in any direction
   - Can move multiple squares (one at a time)
   - Created when a piece reaches the opposite end of the board

#### Capturing
1. **Mandatory Capture**: If a capture is available, you MUST take it
2. **Capture Move**: Jump over an opponent's piece diagonally
3. **Multiple Captures**: If after capturing, you can capture again with the same piece, you must continue
4. **Captured Pieces**: Are removed from the board immediately

#### Winning the Game
You win when:
- You capture all of your opponent's pieces
- Your opponent has no legal moves left

### Game Interface

#### Visual Elements
- **Light Brown Squares**: Light squares (cannot be used)
- **Dark Brown Squares**: Playable squares
- **Red Circles**: Red player's pieces
- **Blue Circles**: Blue player's pieces
- **Yellow Crown**: King piece
- **Green Highlight**: Valid regular moves
- **Red Highlight**: Valid capture moves
- **Yellow Highlight**: Selected piece

#### Status Display
- **Top Center**: Winner announcement (when game ends)
- **Bottom Left**: Current player's turn
- **Bottom Right**: "Capture is mandatory!" warning (when applicable)

### Game Flow Example
1. Game starts with Red's turn
2. Click on a Red piece to select it
3. Green squares show where you can move
4. If red squares appear, you MUST capture
5. Click on a highlighted square to move
6. If you capture a piece and can capture again, your piece remains selected
7. Continue capturing until no more captures are possible
8. Turn switches to the other player
9. Repeat until one player wins

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'pygame'"**
   - Solution: Run `pip install pygame` in your terminal

2. **Game window doesn't open**
   - Solution: Make sure all Python files are in the same folder
   - Solution: Check that you're running `python main.py` from the correct directory

3. **Font warning messages**
   - Solution: These are harmless - the game will use a default font if system fonts aren't available

4. **Game seems frozen**
   - Solution: Check if a capture is mandatory (red squares should be highlighted)
   - Solution: Press 'R' to reset the game

### Performance Tips
- Close other applications if the game runs slowly
- Reduce screen resolution if needed
- Ensure your graphics drivers are up to date

## Game Files Structure
```
checkers_game/
├── constants.py    # Game constants and colors
├── piece.py       # Piece class and movement logic
├── game.py        # Core game rules and state management
├── gui.py         # Graphical user interface
└── main.py        # Main entry point
```

## Advanced Features
- **Consecutive Capture Support**: The game properly handles multiple jumps in one turn
- **King Movement Logic**: Kings can move both forward and backward
- **Win Condition Detection**: Automatic detection of no-move situations
- **Visual Feedback**: Clear indication of all game states

## Tips for Beginners
1. Control the center of the board
2. Try to create kings whenever possible
3. Plan multiple moves ahead
4. Force your opponent into positions where they must make unfavorable captures
5. Protect your back row to prevent your pieces from becoming kings

## Support
For issues or questions:
1. Check the troubleshooting section above
2. Ensure you have the latest version of Python and PyGame
3. Verify all game files are present and in the same directory

Enjoy the game! Remember, checkers is a game of strategy - think ahead and plan your moves carefully.