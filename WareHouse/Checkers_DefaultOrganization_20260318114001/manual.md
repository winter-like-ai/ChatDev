# Checkers Game - User Manual

## Overview
Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a modern graphical interface. The game follows standard checkers rules with an 8x8 board, alternating turns between two players, and includes capture and kinging mechanics.

## Main Features

### 🎮 Game Features
- **Complete Checkers Implementation**: Full adherence to standard checkers rules
- **Graphical User Interface**: Clean, intuitive Pygame-based interface
- **Two-Player Game**: Red vs Black pieces with alternating turns
- **King Pieces**: Automatic promotion to kings when reaching opponent's back row
- **Mandatory Captures**: Enforces capture rules when available
- **Multiple Jumps**: Supports consecutive captures in a single turn
- **Move Notation**: Displays moves in algebraic notation (e.g., "C3-D4")
- **Game State Tracking**: Real-time status display and game over detection

### 🎨 Visual Features
- **Color-Coded Board**: Light and dark squares for clear visibility
- **Piece Highlighting**: Selected pieces and valid moves are clearly marked
- **King Visualization**: Crown symbols on promoted pieces
- **Status Bar**: Shows current player and game instructions
- **Game Over Screen**: Clear winner announcement with restart instructions

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.13+, or Linux
- **Python**: Version 3.7 or higher
- **RAM**: 512 MB minimum
- **Storage**: 10 MB free space

### Recommended Requirements
- **Operating System**: Windows 11, macOS 12+, or Ubuntu 20.04+
- **Python**: Version 3.9 or higher
- **RAM**: 1 GB or more
- **Display**: 1024x768 resolution or higher

## Installation Guide

### Step 1: Install Python
If you don't have Python installed, download and install it from:
- **Windows/Mac**: [python.org/downloads](https://www.python.org/downloads/)
- **Linux**: Use your distribution's package manager:
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install python3 python3-pip
  
  # Fedora
  sudo dnf install python3 python3-pip
  ```

### Step 2: Install Pygame
The game requires Pygame for the graphical interface. Install it using pip:

```bash
# Install Pygame
pip install pygame>=2.5.2

# Or if you have multiple Python versions
pip3 install pygame>=2.5.2
```

### Step 3: Download Game Files
Download the following files to a folder of your choice:
1. `main.py` - Main game launcher
2. `checkersgame.py` - Game logic and rules
3. `gamegui.py` - Graphical interface
4. `requirements.txt` - Dependencies list

### Step 4: Verify Installation
Open a terminal/command prompt and navigate to the game folder:

```bash
cd path/to/checkers/folder
python --version  # Should show Python 3.7+
python -c "import pygame; print(pygame.version.ver)"  # Should show 2.5.2+
```

## How to Play

### Starting the Game
1. Open a terminal/command prompt
2. Navigate to the game folder:
   ```bash
   cd path/to/checkers/folder
   ```
3. Run the game:
   ```bash
   python main.py
   ```

### Game Interface Layout
```
┌─────────────────────────────────────┐
│                                     │
│          CHECKERS BOARD             │
│    (8x8 grid with pieces)           │
│                                     │
├─────────────────────────────────────┤
│ Current Player: Red                 │
│ Click piece to select, then click   │
│ destination. Red starts.            │
│ Last move: C3-D4                    │
└─────────────────────────────────────┘
```

### Game Rules
1. **Starting Position**: Red pieces start at the bottom three rows, Black at the top
2. **Turn Order**: Red moves first, then players alternate
3. **Movement**:
   - Regular pieces move diagonally forward one square
   - Kings can move diagonally in any direction
4. **Capturing**:
   - Jump over opponent's piece to capture it
   - Multiple jumps allowed in one turn
   - Captures are mandatory when available
5. **King Promotion**:
   - Reach opponent's back row to become a king
   - Kings can move and capture in any diagonal direction

### Controls
- **Mouse**: Primary control method
  - Left-click: Select piece or destination
  - Click status bar: No effect (for information only)
- **Keyboard**:
  - `R` key: Restart game (when game is over)
  - `ESC` or close window: Exit game

### Playing a Turn
1. **Select a Piece**: Click on one of your pieces
   - Selected piece will turn gold
   - Valid moves will be highlighted with green borders
2. **Make a Move**: Click on a highlighted square
   - Regular move: Click adjacent diagonal square
   - Capture move: Click two squares away (jump over opponent)
3. **Multiple Captures**: If another capture is available, your piece remains selected
   - Continue clicking capture destinations
   - Turn ends when no more captures are possible

### Game States
- **Active Game**: Normal play, follow turn sequence
- **Mandatory Capture**: Green highlights show only capture moves
- **Game Over**: Screen dims with winner announcement
  - No pieces left for one player
  - No valid moves available for current player

## Troubleshooting

### Common Issues

**Issue**: "ModuleNotFoundError: No module named 'pygame'"
**Solution**: Install Pygame:
```bash
pip install pygame
```

**Issue**: Game window doesn't open or crashes immediately
**Solution**: Check Python version:
```bash
python --version
# If below 3.7, upgrade Python
```

**Issue**: Graphics appear distorted or pieces don't display
**Solution**: Update Pygame:
```bash
pip install --upgrade pygame
```

**Issue**: Can't select pieces or moves don't register
**Solution**: 
1. Ensure you're clicking on valid squares (dark squares only)
2. Check if capture is mandatory (only green highlights will work)
3. Verify it's your turn (status bar shows current player)

### Performance Tips
1. Close other applications if game runs slowly
2. Reduce screen resolution if on older hardware
3. Ensure graphics drivers are up to date

## Game Files Structure
```
checkers_game/
├── main.py          # Game launcher and main loop
├── checkersgame.py  # Game logic, rules, and board state
├── gamegui.py       # Graphical interface and rendering
└── requirements.txt # Dependencies list
```

## Advanced Features

### Move Notation
The game uses algebraic notation similar to chess:
- Columns: A-H (left to right)
- Rows: 1-8 (bottom to top)
- Example: "C3-D4" means piece moved from column C, row 3 to column D, row 4

### Game State Tracking
- Current player always displayed
- Last move shown in notation format
- Mandatory capture warnings (implied by move restrictions)
- Automatic win detection

### Customization
Advanced users can modify:
- Colors in `gamegui.py` `colors` dictionary
- Board size by changing `square_size` in `GameGUI.__init__`
- Piece appearance in `draw_piece` method

## Support

### Getting Help
If you encounter issues:
1. Check the Troubleshooting section above
2. Verify all installation steps were followed
3. Ensure your system meets minimum requirements

### Reporting Bugs
Please report any issues with:
1. Game version (files as provided)
2. Operating system and Python version
3. Steps to reproduce the issue
4. Error messages (if any)

## License & Credits
This Checkers game implementation is provided for educational and entertainment purposes. The code follows standard checkers rules and uses Pygame for graphics rendering.

### Dependencies
- **Pygame**: Community-driven multimedia library for Python
- **Python Standard Library**: Core Python functionality

### Development
Game developed with attention to:
- Clean code architecture
- User-friendly interface
- Accurate rule implementation
- Cross-platform compatibility

## Enjoy the Game!
We hope you enjoy playing Checkers! Remember:
- Strategy is key - plan multiple moves ahead
- Protect your back row to prevent king promotions
- Use forced captures to your advantage
- Have fun and good luck!

For updates or additional game versions, check back with the development team.

---
*Note: This is a two-player local game. Both players use the same computer and take turns.*