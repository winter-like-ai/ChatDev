# Checkers Game - User Manual

## Overview

Welcome to the Checkers (Draughts) game! This is a fully-featured digital implementation of the classic board game, featuring an 8x8 board, two-player gameplay, standard capture and kinging rules, and multiple input methods. The game provides both mouse-based interaction and algebraic notation input for moves.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux with Python support
- **Python**: Version 3.8 or higher
- **RAM**: 4 GB minimum
- **Storage**: 50 MB available space
- **Display**: 1024x768 resolution minimum

### Recommended Requirements
- **Operating System**: Latest version of Windows, macOS, or Linux
- **Python**: Version 3.10 or higher
- **RAM**: 8 GB
- **Storage**: 100 MB available space
- **Display**: 1280x720 resolution or higher

## Installation Guide

### Step 1: Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Complete the installation

### Step 2: Install Required Dependencies
Open your terminal or command prompt and run:

```bash
pip install pygame pygame-textinput
```

### Step 3: Download Game Files
Create a project folder and download these files:
- `main.py` - Main game file
- `constants.py` - Game constants and configuration
- `piece.py` - Piece class definition
- `board.py` - Board class definition
- `game.py` - Game logic and rules

### Step 4: Verify Installation
Run this command to check if all dependencies are installed:
```bash
python -c "import pygame; import pygame_textinput; print('Installation successful!')"
```

## Game Features

### Core Gameplay
- **8x8 Checkers Board**: Standard international draughts board
- **Two Players**: Red (moves down) and White (moves up)
- **Alternating Turns**: Players take turns moving pieces
- **Standard Rules**: Follows international draughts rules
- **Capture Rules**: Mandatory captures, multiple jumps allowed
- **Kinging**: Pieces become kings when reaching opponent's back row
- **Win Conditions**: Capture all opponent pieces or block all moves

### User Interface Features
- **Visual Board**: Color-coded squares with clear piece representation
- **Move Highlighting**: Selected pieces and valid moves are highlighted
- **Dual Input Methods**: Mouse clicks and algebraic notation input
- **Game Status Display**: Current turn, last move, and winner announcement
- **Error Messages**: Clear feedback for invalid moves
- **Game Controls**: Reset and quit options

### Input Methods
1. **Mouse Control**: Click to select pieces and destination squares
2. **Algebraic Notation**: Type moves in format like "a3-b4"
3. **Keyboard Shortcuts**: Quick access to game functions

## How to Play

### Starting the Game
1. Navigate to your game folder in terminal/command prompt
2. Run the game:
```bash
python main.py
```

### Game Setup
- Red pieces start at the top three rows
- White pieces start at the bottom three rows
- Red player moves first
- Only dark squares are used for pieces

### Basic Rules
1. **Regular Moves**: Pieces move diagonally forward one square
2. **Capturing**: Jump over opponent's piece to capture it
3. **Multiple Jumps**: Continue capturing if possible
4. **King Promotion**: Reach opponent's back row to become king
5. **King Movement**: Kings can move diagonally in any direction
6. **Mandatory Capture**: If a capture is available, you must take it

### Using Mouse Controls
1. **Select a Piece**: Click on your piece (highlighted in green)
2. **View Valid Moves**: Valid destinations show as green circles
3. **Make a Move**: Click on a highlighted destination square
4. **Multiple Jumps**: After a capture, the same piece remains selected for additional jumps

### Using Algebraic Notation
1. **Activate Input**: Press Tab or click on the input box
2. **Enter Move**: Type in format "from-to" (e.g., "a3-b4")
3. **Submit**: Press Enter to execute the move
4. **Notation Guide**:
   - Columns: a-h (left to right)
   - Rows: 1-8 (bottom to top)
   - Example: "c2-d3" moves from column c, row 2 to column d, row 3

### Keyboard Shortcuts
- **Tab**: Toggle text input mode
- **Enter**: Submit move in text input
- **R**: Reset the game
- **Q**: Quit the game

## Game Interface Guide

### Main Game Window
```
┌─────────────────────────────────────────────────────────────┐
│                     CHECKERS GAME                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  8x8 Board Area               │  UI Panel                  │
│                               │                            │
│  □ ■ □ ■ □ ■ □ ■             │  Turn: Red                 │
│  ■ □ ■ □ ■ □ ■ □             │  Last move: a3-b4          │
│  □ ■ □ ■ □ ■ □ ■             │                            │
│  ■ □ ■ □ ■ □ ■ □             │  Enter move (e.g., a3-b4): │
│  □ ■ □ ■ □ ■ □ ■             │  [____________]            │
│  ■ □ ■ □ ■ □ ■ □             │                            │
│  □ ■ □ ■ □ ■ □ ■             │  Instructions:             │
│  ■ □ ■ □ ■ □ ■ □             │  1. Click on a piece...    │
│                               │  2. Click on highlighted.. │
│                               │  3. Or enter move...       │
│                               │  4. Tab: Toggle text input │
│                               │  5. R: Reset game          │
│                               │  6. Q: Quit game           │
└─────────────────────────────────────────────────────────────┘
```

### Piece Representation
- **Red Regular Piece**: Solid red circle
- **White Regular Piece**: Solid white circle
- **Red King**: Red circle with yellow center
- **White King**: White circle with yellow center

### Visual Indicators
- **Selected Piece**: Green border around the piece
- **Valid Moves**: Small green circles on destination squares
- **Active Input Box**: White border when text input is active
- **Error Messages**: Red text below input box
- **Winner Announcement**: Gold text in center of screen

## Troubleshooting

### Common Issues and Solutions

**Issue**: "ModuleNotFoundError: No module named 'pygame'"
**Solution**: Reinstall pygame: `pip install --upgrade pygame`

**Issue**: Game window doesn't open
**Solution**: 
1. Check Python installation: `python --version`
2. Ensure all files are in the same directory
3. Run from correct directory in terminal

**Issue**: Mouse clicks not registering
**Solution**:
1. Ensure you're clicking on dark squares for pieces
2. Check if it's your turn
3. Verify piece selection (green border should appear)

**Issue**: Invalid move notation error
**Solution**:
1. Use correct format: "letter-number-letter-number"
2. Columns must be a-h
3. Rows must be 1-8
4. Example: "b2-c3" not "B2-C3"

**Issue**: Game runs slowly
**Solution**:
1. Close other applications
2. Reduce screen resolution if needed
3. Update graphics drivers

### Performance Tips
1. Run game in full-screen mode for better performance
2. Close unnecessary background applications
3. Keep game files on SSD for faster loading
4. Update Python and pygame to latest versions

## Advanced Features

### Game State Management
- **Auto-save**: Last move is always displayed
- **Reset Function**: Complete game restart with R key
- **Move History**: Last move shown in algebraic notation

### Input Flexibility
- **Mixed Input**: Switch between mouse and keyboard anytime
- **Input Validation**: Real-time move validation
- **Error Recovery**: Clear error messages with suggestions

### Visual Customization
The game uses a classic color scheme, but you can modify colors in `constants.py`:
- Change board colors (DARK_SQUARE, LIGHT_SQUARE)
- Adjust piece colors (RED, WHITE)
- Modify highlight colors (HIGHLIGHT, VALID_MOVE)

## Rules Reference

### Movement Rules
1. **Regular Pieces**: Move diagonally forward only
2. **Kings**: Move diagonally in any direction
3. **Capture Direction**: Both forward and backward for kings
4. **Multiple Captures**: Must continue capturing if possible

### Special Situations
1. **Mandatory Capture**: If any capture is available, you must take it
2. **Capture Chain**: Continue jumping with the same piece
3. **King Promotion**: Automatic when reaching opponent's back row
4. **Stalemate**: Game ends when player has no legal moves

### Winning Conditions
1. **Capture All**: Remove all opponent pieces
2. **Block All**: Opponent has no legal moves
3. **Resignation**: Player quits the game

## Support and Feedback

### Getting Help
If you encounter issues:
1. Check the Troubleshooting section above
2. Verify all installation steps were followed
3. Ensure you have the latest version of all files

### Reporting Bugs
Please report any issues with:
1. Game version (file dates)
2. Operating system
3. Python version
4. Steps to reproduce the issue
5. Error messages (if any)

### Feature Requests
Suggestions for improvements are welcome! Consider:
1. New game modes
2. Additional customization options
3. Enhanced UI features
4. Network multiplayer support

## Credits

### Development Team
- **Game Design**: ChatDev Product Team
- **Programming**: Python/Pygame Implementation
- **Testing**: Quality Assurance Team

### Technologies Used
- **Python 3**: Core programming language
- **Pygame**: Graphics and input handling
- **Pygame-textinput**: Text input functionality

### License
This game is provided for educational and entertainment purposes. All code is open for modification and learning.

## Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Pygame and pygame-textinput installed
- [ ] All game files in same folder
- [ ] Run `python main.py` to start
- [ ] Red pieces at top, White at bottom
- [ ] Red moves first
- [ ] Use mouse or notation to play
- [ ] Press R to reset, Q to quit

Enjoy your game of Checkers!