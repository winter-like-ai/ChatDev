# Checkers (Draughts) Game - User Manual

## Overview

Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with both graphical user interface (GUI) and notation-based input support. The game follows standard international draughts rules on an 8x8 board.

## Main Features

### 🎮 Game Features
- **Two-player gameplay** with alternating turns
- **Standard checkers rules** including mandatory captures
- **King promotion** when pieces reach the opposite end
- **Visual highlighting** of valid moves and selected pieces
- **Game state tracking** with winner detection
- **Reset functionality** for quick restarts

### 🖥️ Interface Features
- **Graphical board** with intuitive color coding
- **Mouse-based controls** for easy piece selection and movement
- **Notation input support** for traditional checkers notation
- **Real-time status display** showing current player's turn
- **Game over screen** with winner announcement

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Python**: Version 3.8 or higher
- **RAM**: 512 MB minimum
- **Storage**: 10 MB free space

### Recommended Requirements
- **Operating System**: Latest version of Windows, macOS, or Linux
- **Python**: Version 3.10 or higher
- **RAM**: 1 GB or more
- **Display**: 1024x768 resolution or higher

## Installation Guide

### Step 1: Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation by opening terminal/command prompt and typing:
   ```bash
   python --version
   ```

### Step 2: Download Game Files
1. Create a new folder for the game (e.g., `CheckersGame`)
2. Download all required files into this folder:
   - `main.py`
   - `game.py`
   - `board.py`
   - `piece.py`
   - `gui.py`
   - `constants.py`
   - `notation.py`
   - `requirements.txt`

### Step 3: Install Dependencies
Open terminal/command prompt in your game folder and run:

```bash
pip install -r requirements.txt
```

This will install PyGame, the only required dependency.

### Step 4: Verify Installation
Run a quick test to ensure everything is installed correctly:
```bash
python -c "import pygame; print('Pygame installed successfully!')"
```

## How to Play

### Starting the Game
1. Navigate to your game folder in terminal/command prompt
2. Run the game:
   ```bash
   python main.py
   ```
3. The game window will open automatically

### Game Controls

#### Mouse Controls (Default Mode)
- **Left-click** on a piece to select it
- **Left-click** on a highlighted square to move the selected piece
- Valid moves will be highlighted in green

#### Keyboard Controls
- **R**: Reset the game to initial state
- **ESC**: Quit the game
- **N**: Toggle between GUI and notation input modes (future feature)

### Game Rules

#### Basic Movement
- **Red pieces** (Player One) move downward
- **Blue pieces** (Player Two) move upward
- Regular pieces move diagonally forward one square
- Kings can move diagonally forward or backward

#### Capturing
- **Mandatory captures**: If a capture is available, you must take it
- Pieces capture by jumping over an opponent's piece diagonally
- Multiple captures in one turn are allowed (if available)

#### King Promotion
- A piece becomes a king when it reaches the opposite end of the board
- Kings are marked with a crown symbol
- Kings can move and capture in any diagonal direction

### Game Interface Elements

#### Board Layout
- **Light brown squares**: Regular squares
- **Dark brown squares**: Playable squares (where pieces start)
- **Green highlight**: Valid move destinations
- **Green border**: Currently selected piece

#### Status Display (Bottom of Screen)
- Current player's turn (Red or Blue)
- Game instructions
- Control reminders

#### Game Over Screen
- Winner announcement
- Restart/quit options

## Notation Input Mode (Advanced)

### Switching to Notation Mode
Currently, the game defaults to GUI mode. Future updates will include:
- Press **N** to toggle between GUI and notation modes
- Notation input field for entering moves

### Notation Format
When in notation mode, moves can be entered using algebraic notation:
- **Simple move**: `c3-d4` (move from c3 to d4)
- **Capture move**: `a5xb6` (capture from a5 to b6)

### Coordinate System
- Columns: a-h (left to right)
- Rows: 1-8 (bottom to top)
- Example: `c3` = column 3, row 3 (0-indexed: col=2, row=2)

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'pygame'"
```bash
pip install pygame
```

#### Game window doesn't open
- Ensure you're running `python main.py` from the correct directory
- Check that all game files are in the same folder

#### Game runs but pieces don't move
- Make sure you're clicking on valid pieces (your color only)
- Check that you're clicking on highlighted squares for movement

#### Game appears too small/large
- The game window is fixed at 640x720 pixels
- For different sizes, modify `WINDOW_WIDTH` and `WINDOW_HEIGHT` in `constants.py`

### Performance Issues
- Close other applications to free up system resources
- Reduce background processes if the game runs slowly

## Game Files Structure

```
CheckersGame/
├── main.py          # Entry point
├── game.py          # Main game logic
├── board.py         # Board management
├── piece.py         # Piece representation
├── gui.py           # Graphical interface
├── constants.py     # Game constants
├── notation.py      # Notation parsing
└── requirements.txt # Dependencies
```

## Customization

### Changing Colors
Edit `constants.py` to modify:
- Board colors (`LIGHT_BROWN`, `DARK_BROWN`)
- Piece colors (`RED`, `BLUE`)
- Highlight colors (`HIGHLIGHT_COLOR`)

### Changing Board Size
Modify `BOARD_SIZE` in `constants.py` (currently 8x8)

### Adjusting Game Speed
Change `FPS` (frames per second) in `constants.py` for smoother/faster gameplay

## Support

### Getting Help
If you encounter issues:
1. Check the troubleshooting section above
2. Verify all files are present and in the correct location
3. Ensure Python and PyGame are properly installed

### Reporting Bugs
Please report any bugs or issues with:
- Your operating system and Python version
- Steps to reproduce the issue
- Screenshots if applicable

## Future Updates

Planned features for future versions:
- **Single-player mode** with AI opponent
- **Notation input mode** with text entry
- **Move history** and replay functionality
- **Different game variants** (American checkers, international draughts)
- **Sound effects** and background music
- **Save/load game** functionality

## Credits

This Checkers game was developed by ChatDev using Python and PyGame. The implementation follows standard international draughts rules and provides both visual and notation-based gameplay options.

---

**Enjoy the game!** 🎮

For the best experience, ensure you're playing on a system that meets the recommended requirements and follow the installation instructions carefully.