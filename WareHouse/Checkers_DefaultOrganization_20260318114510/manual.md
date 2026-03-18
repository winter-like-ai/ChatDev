# Checkers Game - User Manual

## Overview

Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a modern graphical interface. The game follows standard checkers rules with an 8x8 board, alternating turns between two players, and includes capture and kinging mechanics.

## Main Features

- **Complete Checkers Gameplay**: Standard 8x8 board with all official rules
- **Graphical User Interface**: Clean, intuitive visual interface using Pygame
- **Two-Player Mode**: Play against another person on the same computer
- **Visual Feedback**: Clear piece selection and valid move indicators
- **King Piece Promotion**: Automatic promotion to king pieces when reaching the opposite end
- **Forced Capture Rules**: Mandatory capture moves when available
- **Chain Captures**: Support for multiple consecutive captures in a single turn
- **Game State Management**: Automatic win detection and game reset functionality
- **Move Validation**: Prevents illegal moves according to checkers rules

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Python**: Version 3.8 or higher
- **RAM**: 4 GB minimum
- **Storage**: 50 MB available space

### Recommended Requirements
- **Operating System**: Latest version of Windows, macOS, or Linux
- **Python**: Version 3.10 or higher
- **RAM**: 8 GB
- **Storage**: 100 MB available space

## Installation Guide

### Step 1: Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Complete the installation

### Step 2: Install Pygame
Open your terminal/command prompt and run:
```bash
pip install pygame
```

### Step 3: Download Game Files
Create a project folder and download these files:
- `main.py` - Main game executable
- `game.py` - Core game logic
- `piece.py` - Piece class definition
- `constants.py` - Game configuration
- `gui.py` - Graphical interface functions

### Step 4: Verify Installation
Run this command to check Pygame installation:
```bash
python -c "import pygame; print('Pygame installed successfully')"
```

## How to Play

### Starting the Game
1. Navigate to your project folder in terminal/command prompt
2. Run the game:
```bash
python main.py
```

### Game Interface
- **Game Board**: 8x8 checkered board with alternating light and dark squares
- **Pieces**: Red pieces (top) vs Blue pieces (bottom)
- **Information Panel**: Shows current player and game instructions
- **Selection Highlight**: Yellow border around selected piece
- **Valid Move Indicators**: Green circles showing possible destinations

### Game Controls
- **Mouse Click**: Select pieces and make moves
- **R Key**: Reset the game at any time
- **Close Button**: Exit the game

### Game Rules
1. **Starting Positions**: Red pieces start on top 3 rows, Blue pieces on bottom 3 rows
2. **Turn Order**: Red moves first, then alternating turns
3. **Regular Moves**: Pieces move diagonally forward one square
4. **Capturing**: Jump over opponent's piece diagonally (must capture if possible)
5. **King Pieces**: Reach the opposite end row to become a king
6. **King Movement**: Kings can move diagonally in any direction
7. **Chain Captures**: Multiple captures in one turn are mandatory
8. **Winning**: Capture all opponent pieces or block all their moves

### Playing the Game
1. **Select a Piece**: Click on your piece (highlighted with yellow border)
2. **View Valid Moves**: Green circles show where you can move
3. **Make a Move**: Click on a valid destination square
4. **Forced Captures**: If a capture is available, you must take it
5. **Chain Captures**: Continue capturing if additional jumps are available
6. **King Promotion**: Pieces reaching the opposite end become kings automatically

### Game Flow Example
1. Red player clicks on a red piece
2. Green circles appear showing possible moves
3. Red player clicks on a destination square
4. If it's a capture, the opponent's piece is removed
5. If additional captures are possible, continue jumping
6. Turn switches to Blue player
7. Repeat until one player wins

## Troubleshooting

### Common Issues

**Issue**: "ModuleNotFoundError: No module named 'pygame'"
**Solution**: Install Pygame using: `pip install pygame`

**Issue**: Game window doesn't open
**Solution**: 
1. Check Python installation: `python --version`
2. Ensure all game files are in the same folder
3. Run from correct directory

**Issue**: Game crashes or freezes
**Solution**:
1. Restart the game
2. Check for updated Pygame: `pip install --upgrade pygame`
3. Ensure sufficient system resources

**Issue**: Can't select pieces or make moves
**Solution**:
1. Ensure you're clicking on your own pieces
2. Check if forced capture is required
3. Verify it's your turn (check information panel)

### Performance Tips
1. Close unnecessary applications while playing
2. Update graphics drivers if experiencing visual issues
3. Run game in full-screen mode for better performance

## Game Files Structure

```
checkers_game/
├── main.py          # Main game loop and event handling
├── game.py          # Game logic and board management
├── piece.py         # Piece class definition
├── constants.py     # Game constants and configuration
└── gui.py           # Graphical interface rendering
```

## Advanced Features

### Customization Options
You can modify `constants.py` to customize:
- Board colors
- Piece colors
- Window size
- Game speed (FPS)

### Development Notes
- Built with object-oriented design principles
- Modular architecture for easy maintenance
- Comprehensive move validation
- Extensible for future enhancements

## Support

For additional help:
1. Check the in-game instructions
2. Review this manual
3. Contact support if issues persist

## License

This Checkers game is provided for educational and entertainment purposes. Feel free to modify and distribute with proper attribution.

---

**Enjoy your game of Checkers!** 🎮

*Note: This implementation follows international draughts rules. Some regional variations may differ.*