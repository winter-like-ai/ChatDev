# Checkers Game - User Manual

## Overview

Welcome to the Checkers (Draughts) game! This is a fully functional digital implementation of the classic board game, featuring an intuitive graphical interface, complete game rules, and smooth gameplay. The game supports two players on the same computer, with alternating turns and all standard checkers rules.

## Main Features

### 🎮 Core Gameplay
- **8x8 Standard Board**: Traditional checkers board layout
- **Two Players**: Red vs Black pieces
- **Alternating Turns**: Players take turns moving their pieces
- **Complete Rules**: Includes all standard checkers rules:
  - Mandatory captures
  - Multiple jumps (chain captures)
  - King promotion at opposite end
  - King movement (forward and backward)

### 🖥️ User Interface
- **Visual Board**: Color-coded board with clear piece representation
- **Interactive Controls**: Click-based piece selection and movement
- **Move Highlights**: Visual indicators for valid moves
- **Game Status Display**: Current player, mandatory captures, and game state
- **Piece Count**: Real-time tracking of remaining pieces
- **Reset Function**: Easy game restart

### 🎯 Game Mechanics
- **Mandatory Capture Enforcement**: System prevents illegal moves when captures are available
- **King Promotion**: Automatic promotion to king when reaching opposite end
- **Multiple Jumps**: Chain captures allowed in a single turn
- **Game Over Detection**: Automatic win detection when:
  - All opponent pieces are captured
  - Opponent has no valid moves

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.13+, or Linux
- **Python**: Version 3.7 or higher
- **RAM**: 4GB minimum
- **Storage**: 50MB free space

### Recommended Requirements
- **Operating System**: Latest version of Windows, macOS, or Linux
- **Python**: Version 3.9 or higher
- **RAM**: 8GB or more
- **Display**: 1280x720 resolution or higher

## Installation Guide

### Step 1: Install Python
If you don't have Python installed, download and install it from:
- **Windows/macOS/Linux**: [python.org/downloads](https://www.python.org/downloads/)

Verify installation by opening a terminal/command prompt and typing:
```bash
python --version
```

### Step 2: Install Pygame
The game requires Pygame for the graphical interface. Install it using pip:

```bash
pip install pygame
```

For macOS users, you might need to use:
```bash
pip3 install pygame
```

### Step 3: Download Game Files
Download the following files to the same directory:
- `main.py`
- `piece.py` (renamed from game.py in the provided code)
- `gamegui.py`

**Important**: Ensure all three files are in the same folder.

## How to Play

### Starting the Game
1. Open a terminal/command prompt
2. Navigate to the folder containing the game files
3. Run the game:
```bash
python main.py
```

### Game Interface Layout
The game window is divided into two main sections:

**Left Side - Game Board**
- 8x8 checkers board with alternating light and dark squares
- Red pieces start at the top (rows 1-3)
- Black pieces start at the bottom (rows 6-8)
- Coordinates displayed on the edges (A-H for columns, 1-8 for rows)

**Right Side - Control Panel**
- Game title and status
- Player indicators with piece counts
- Game instructions
- Reset button
- Move notation display

### Basic Gameplay

#### 1. Selecting a Piece
- **Click** on one of your pieces to select it
- Selected pieces are highlighted with a yellow border
- If mandatory captures are available, only pieces that can capture can be selected

#### 2. Making a Move
- **Click** on a highlighted square to move your selected piece there
- Valid moves are shown with green circles
- The game will automatically:
  - Move your piece to the selected square
  - Remove captured pieces (if any)
  - Promote to king when reaching the opposite end
  - Switch turns to the other player

#### 3. Special Moves

**Capturing (Jumping)**
- When an opponent's piece is adjacent and there's an empty square beyond it
- Click on the empty square beyond the opponent's piece
- The opponent's piece is removed from the board
- Multiple jumps in a single turn are allowed

**King Promotion**
- When a regular piece reaches the opposite end of the board
- Automatically becomes a king
- Kings are displayed with a gold crown symbol
- Kings can move and capture both forward and backward

### Game Rules

#### Movement Rules
- **Regular Pieces**:
  - Red pieces move downward (increasing row numbers)
  - Black pieces move upward (decreasing row numbers)
  - Move one square diagonally forward to an empty square

- **Kings**:
  - Can move one square diagonally in any direction
  - Can capture in any direction

#### Capture Rules
1. **Mandatory Capture**: If a capture is possible, you must make it
2. **Multiple Captures**: If after capturing, another capture is possible from the new position, you must continue capturing
3. **Capture Direction**: Regular pieces can only capture forward; kings can capture in any direction

#### Winning Conditions
The game ends when:
1. **All opponent pieces are captured**
2. **Opponent has no legal moves**
3. **Player resigns (by closing the game)**

### Controls

#### Mouse Controls
- **Left Click**: Select piece or make move
- **Reset Button**: Click to restart the game

#### Keyboard Shortcuts
- **ESC**: Exit the game
- **R**: Reset the game (alternative to button)
- **F11**: Toggle fullscreen mode

### Move Notation
The game uses algebraic notation similar to chess:
- **Columns**: A-H (left to right)
- **Rows**: 1-8 (bottom to top)
- **Example**: Moving from A3 to B4 is displayed as "A3-B4"

## Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError: No module named 'pygame'"
**Solution**: Install Pygame using:
```bash
pip install pygame
```

#### 2. Game window doesn't open
**Solution**: 
- Ensure all three files are in the same directory
- Check Python installation: `python --version`
- Try running with: `python3 main.py`

#### 3. Game runs but pieces don't move
**Solution**:
- Make sure you're clicking on valid moves (highlighted in green)
- Check if mandatory captures are required
- Verify you're selecting your own pieces (Red or Black based on turn)

#### 4. Performance issues or lag
**Solution**:
- Close other applications to free up system resources
- Reduce screen resolution if using high-resolution display
- Update graphics drivers

### Advanced Troubleshooting

#### Log Files
If the game crashes, check for error messages in the terminal/command prompt window.

#### Reinstallation
If problems persist:
1. Delete all game files
2. Re-download fresh copies
3. Reinstall Pygame: `pip install --upgrade pygame`
4. Try running again

## Tips and Strategies

### Beginner Tips
1. **Control the Center**: Pieces in the center have more movement options
2. **Create Kings**: Get your pieces to the opposite end to promote them
3. **Plan Ahead**: Think about your opponent's possible responses
4. **Force Captures**: Position pieces to force your opponent into disadvantageous captures

### Advanced Strategies
1. **The Fork**: Position a piece to threaten two opponent pieces simultaneously
2. **The Pin**: Trap opponent pieces against the edge of the board
3. **Sacrifice**: Sometimes sacrificing a piece can lead to capturing multiple opponent pieces
4. **King Advantage**: Kings are significantly more powerful - protect them!

## Frequently Asked Questions

### Q: Can I play against the computer?
**A**: Currently, the game only supports two human players on the same computer. Future versions may include AI opponents.

### Q: Is there online multiplayer?
**A**: No, this is a local two-player game only.

### Q: Can I customize the board colors?
**A**: Not in the current version. The colors are fixed to ensure clear visibility and traditional appearance.

### Q: How do I save my game?
**A**: The current version doesn't have a save feature. Games must be completed in one session.

### Q: What's the difference between this and international draughts?
**A**: This implements American/English checkers rules on an 8x8 board. International draughts uses a 10x10 board with slightly different rules.

## Support and Feedback

### Reporting Issues
If you encounter bugs or have suggestions:
1. Note the exact steps to reproduce the issue
2. Check if the issue persists after restarting the game
3. Contact support with:
   - Your operating system
   - Python version
   - Pygame version
   - Detailed description of the issue

### Feature Requests
We welcome suggestions for future versions! Common requests include:
- AI opponents with difficulty levels
- Online multiplayer
- Game statistics and history
- Customizable themes
- Tournament mode

## Credits

### Development
- **Game Engine**: Python with Pygame
- **Rules Implementation**: Complete standard checkers rules
- **UI Design**: Intuitive graphical interface with clear visual feedback

### Special Thanks
- Testers and early adopters
- The Pygame development community
- All checkers enthusiasts who provided feedback

## Version Information

**Current Version**: 1.0
**Release Date**: [Current Date]
**Compatibility**: Python 3.7+, Pygame 2.0+

### Changelog
**Version 1.0** (Initial Release)
- Complete checkers game implementation
- Graphical user interface
- All standard rules enforced
- Move highlighting and visual feedback
- Game state tracking and win detection

---

Enjoy the game! Whether you're a casual player or a checkers enthusiast, we hope this digital version brings you many hours of strategic fun. Remember, every master was once a beginner - keep playing and developing your skills!

**Happy Gaming!** 🎮♟️