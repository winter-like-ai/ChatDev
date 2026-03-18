# Checkers Game - User Manual

## Overview
Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a modern graphical interface. The game features an 8x8 board, two-player gameplay with alternating turns, standard capture rules, king promotion, and a complete graphical user interface built with Pygame.

## System Requirements
- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.7 or higher
- **RAM**: Minimum 4GB recommended
- **Display**: 800x800 resolution or higher

## Installation

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

### Step 2: Install Dependencies
Open your terminal or command prompt and run:

```bash
pip install pygame==2.5.2
```

### Step 3: Download Game Files
Create a folder for the game and download the following files:
- `main.py`
- `game.py`
- `board.py`
- `piece.py`
- `gui.py`
- `requirements.txt`

All files should be in the same directory.

## How to Play

### Starting the Game
1. Open your terminal or command prompt
2. Navigate to the game directory
3. Run the game:
```bash
python main.py
```

### Game Interface
The game window displays:
- **Game Board**: 8x8 checkered board with alternating light and dark squares
- **Pieces**: Red and white circular pieces
- **Turn Indicator**: Shows whose turn it is (top-left corner)
- **Piece Count**: Displays remaining pieces and kings for each player
- **Selection Highlight**: Green border around selected piece
- **Valid Moves**: Blue dots indicating possible move destinations

### Game Rules
1. **Starting Positions**: Red pieces start on the top three rows, white pieces on the bottom three rows
2. **Movement**: 
   - Regular pieces move diagonally forward one square
   - Kings can move diagonally forward or backward
3. **Capturing**: 
   - Jump over opponent's piece to capture it
   - Multiple captures in one turn are allowed (capture chains)
   - Captures are mandatory when available
4. **King Promotion**: 
   - Red pieces become kings when reaching row 7 (bottom)
   - White pieces become kings when reaching row 0 (top)
   - Kings are marked with a yellow crown and "K" symbol

### Controls
- **Mouse**: Click to select pieces and make moves
- **R Key**: Restart the game when it's over
- **Close Button**: Click the window's close button to exit

### Game Flow
1. Red player starts first
2. Click on your piece to select it
3. Valid moves will be shown as blue dots
4. Click on a blue dot to move your piece
5. If a capture is available, you must take it
6. After a capture, if another capture is possible with the same piece, you must continue capturing
7. The game alternates turns after each move (unless in a capture chain)
8. The game ends when one player has no pieces left or no valid moves

## Features

### Core Game Features
- **Complete Checkers Rules**: Implements all standard checkers rules including forced captures and king promotion
- **Visual Feedback**: Clear visual indicators for selected pieces, valid moves, and captures
- **Game State Tracking**: Tracks piece counts, kings, and turn order
- **Win Detection**: Automatically detects when the game is won
- **Restart Functionality**: Easy game reset with R key

### User Interface Features
- **Clean Visual Design**: Professional-looking board and pieces
- **Turn Indicators**: Clear display of whose turn it is
- **Piece Counters**: Real-time tracking of remaining pieces
- **Winner Display**: Prominent winner announcement with restart option
- **Responsive Controls**: Smooth mouse interaction

## Troubleshooting

### Common Issues

1. **Game won't start**:
   - Ensure all Python files are in the same directory
   - Check that Pygame is installed: `pip list | grep pygame`
   - Verify Python version: `python --version`

2. **Graphics issues**:
   - Update your graphics drivers
   - Try running in windowed mode if fullscreen has issues
   - Check display resolution compatibility

3. **Game crashes**:
   - Ensure you have the latest Pygame version
   - Check for sufficient system memory
   - Verify file permissions

### Error Messages
- **"ModuleNotFoundError: No module named 'pygame'"**: Install Pygame using `pip install pygame`
- **"File not found"**: Ensure all game files are in the same directory
- **"Display mode not set"**: Check your display settings and Pygame installation

## Game Tips
1. **Plan Ahead**: Try to set up multiple jumps when possible
2. **Protect Your Back Row**: Pieces in the back row are safe from immediate capture
3. **King Strategy**: Kings are powerful - try to promote your pieces
4. **Forced Captures**: Remember that captures are mandatory when available
5. **Position Control**: Control the center of the board for better mobility

## Development Notes
This game was developed using:
- **Python 3.x** for the core logic
- **Pygame 2.5.2** for the graphical interface
- **Object-Oriented Design** with separate classes for game logic, board, pieces, and GUI

## Support
For issues or questions:
1. Check the troubleshooting section above
2. Verify all installation steps were followed
3. Ensure your system meets the requirements
4. Contact support if problems persist

## License
This game is provided for educational and entertainment purposes. Feel free to modify and distribute with proper attribution.

---

Enjoy playing Checkers! May the best strategist win!