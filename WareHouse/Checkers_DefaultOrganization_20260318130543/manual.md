```markdown
# Checkers Game - User Manual

## Overview
Welcome to the Checkers Game! This is a fully functional digital implementation of the classic board game Checkers (also known as Draughts). The game features a beautiful graphical interface, accurate game rules, and smooth gameplay for two players.

## System Requirements

### Minimum Requirements:
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux with GUI
- **Python**: Version 3.7 or higher
- **RAM**: 4 GB minimum
- **Storage**: 50 MB free space
- **Display**: 800x800 resolution minimum

### Recommended Requirements:
- **Operating System**: Latest version of Windows, macOS, or Linux
- **Python**: Version 3.9 or higher
- **RAM**: 8 GB
- **Storage**: 100 MB free space
- **Display**: 1920x1080 resolution

## Installation Guide

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

**Verification:**
```bash
python --version
# Should show Python 3.7 or higher
```

### Step 2: Download Game Files
Download all the game files to a folder on your computer:
- `main.py`
- `game.py`
- `gui.py`
- `requirements.txt`
- `readme.md`

### Step 3: Install Dependencies
Open a terminal/command prompt in the game folder and run:

**Using pip:**
```bash
pip install -r requirements.txt
```

**Using pip with virtual environment (recommended):**
```bash
# Create virtual environment
python -m venv checkers_env

# Activate it
# On Windows:
checkers_env\Scripts\activate
# On macOS/Linux:
source checkers_env/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Verify Installation
Check that PyGame is installed correctly:
```bash
python -c "import pygame; print('Pygame version:', pygame.version.ver)"
```

## How to Play

### Starting the Game
1. Navigate to the game folder in your terminal/command prompt
2. Run the game:
```bash
python main.py
```

### Game Interface
The game window consists of:

1. **Game Board (Center)**
   - 8x8 alternating brown and light brown squares
   - Red pieces start at the top (rows 0-2)
   - White pieces start at the bottom (rows 5-7)

2. **Information Panel (Top-left)**
   - Current player's turn (Red/White)
   - Piece counts for both players
   - King piece counts
   - Capture warnings (when applicable)
   - Selected piece coordinates

3. **Visual Indicators**
   - **Green highlight**: Selected piece
   - **Yellow highlight**: Valid move positions
   - **Yellow crown**: King pieces
   - **Red border**: Red pieces
   - **Gray border**: White pieces

### Game Rules

#### Basic Movement
- **Red pieces** move downward (increasing row numbers)
- **White pieces** move upward (decreasing row numbers)
- Pieces move diagonally forward to adjacent empty squares
- **Kings** can move both forward and backward

#### Capturing
- **Mandatory capture**: If a capture is possible, you MUST take it
- Pieces jump over opponent's pieces diagonally
- Multiple jumps in one turn are allowed
- Captured pieces are removed from the board

#### King Promotion
- When a piece reaches the opposite end of the board:
  - Red piece reaches row 7 → becomes King
  - White piece reaches row 0 → becomes King
- Kings are marked with a yellow crown

### Game Controls

#### Mouse Controls:
- **Left-click**: Select a piece or make a move
- **Click on piece**: Select your piece
- **Click on highlighted square**: Move selected piece
- **Click during game over**: Restart game

#### Game Flow:
1. Red player starts first
2. Click on your piece to select it
3. Valid moves will be highlighted in yellow
4. Click on a highlighted square to move
5. If a capture is available, only capture moves will be shown
6. After moving, turn passes to the other player
7. Continue until one player has no pieces left

### Special Features

#### Multiple Jumps
- If you capture a piece and can make another capture with the same piece, you must continue jumping
- The game will keep your piece selected for additional jumps
- Turn only changes when no more captures are possible

#### Mandatory Capture Enforcement
- The game automatically detects when captures are available
- If captures exist, only capture moves are shown
- A "MUST CAPTURE!" warning appears at the top

#### Game State Tracking
- Real-time piece counts
- King count tracking
- Turn indicator
- Move notation display

### Winning the Game
The game ends when:
1. One player captures all opponent's pieces
2. A player cannot make any legal moves

The winner is displayed with a game over screen showing:
- Winner announcement
- "Game Over!" message
- "Click to restart" prompt

## Troubleshooting

### Common Issues and Solutions:

#### 1. "ModuleNotFoundError: No module named 'pygame'"
```bash
# Reinstall pygame
pip uninstall pygame
pip install pygame==2.5.0
```

#### 2. Game window doesn't open
- Ensure you're running from the correct directory
- Check Python version: `python --version`
- Try running with administrator privileges

#### 3. Game runs but graphics are glitchy
- Update your graphics drivers
- Try running in windowed mode (modify gui.py if needed)
- Check display scaling settings

#### 4. Game crashes on click
- Ensure all files are in the same directory
- Check file permissions
- Try reinstalling dependencies

### Performance Tips:
1. Close other applications for smoother gameplay
2. Ensure your system meets minimum requirements
3. Update Python and PyGame to latest versions
4. Run in a dedicated virtual environment

## Game Features Summary

### Core Features:
- ✅ Two-player local gameplay
- ✅ Accurate checkers rules implementation
- ✅ Mandatory capture enforcement
- ✅ King promotion system
- ✅ Multiple jumps in single turn
- ✅ Visual move highlighting
- ✅ Game state tracking
- ✅ Win detection

### User Interface:
- ✅ Clean, intuitive board design
- ✅ Color-coded pieces
- ✅ Real-time game information
- ✅ Visual feedback for selections
- ✅ Game over screen with restart option

### Technical Features:
- ✅ 60 FPS smooth gameplay
- ✅ Efficient move validation
- ✅ Proper error handling
- ✅ Cross-platform compatibility
- ✅ No external dependencies beyond PyGame

## Advanced Usage

### Customizing the Game
You can modify the following in `gui.py`:

**Change Colors:**
```python
# Modify these color values (RGB format)
self.RED = (255, 0, 0)        # Red pieces
self.WHITE = (255, 255, 255)  # White pieces
self.GREEN = (0, 255, 0)      # Selection highlight
```

**Change Board Size:**
```python
self.WIDTH, self.HEIGHT = 800, 800  # Window size
self.SQUARE_SIZE = self.WIDTH // self.COLS  # Square size
```

### Saving Game State
The game currently doesn't save progress. To add save functionality, you would need to:
1. Serialize the game state from `game.get_game_state()`
2. Save to a file
3. Load and restore on startup

## Support and Feedback

### Getting Help:
1. Check the troubleshooting section above
2. Verify all installation steps were followed
3. Ensure Python and PyGame are properly installed

### Reporting Issues:
If you encounter bugs or have suggestions:
1. Note the exact error message
2. Describe what you were doing when it occurred
3. Include your system information (OS, Python version)

### Future Updates Planned:
- AI opponent with difficulty levels
- Online multiplayer support
- Game replay and move history
- Custom board themes
- Tournament mode
- Statistics tracking

## Legal and Credits

### License:
This game is provided for educational and entertainment purposes.

### Credits:
- Game Development: ChatDev Team
- PyGame Library: The PyGame Community
- Checkers Rules: Standard international draughts rules

### Disclaimer:
This software is provided "as is" without warranty of any kind. The developers are not responsible for any issues arising from its use.

---

## Quick Start Checklist
- [ ] Python 3.7+ installed
- [ ] Game files downloaded to same folder
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Game runs: `python main.py`
- [ ] Can select and move pieces
- [ ] Game ends properly when one player wins

Enjoy your game of Checkers! 🎮

*Last Updated: Version 1.0*
```

This comprehensive user manual provides everything a player needs to install, set up, and enjoy the Checkers game. It includes detailed installation instructions, gameplay rules, troubleshooting tips, and information about all game features. The manual is structured to be accessible to both technical and non-technical users, with clear step-by-step guides and visual descriptions of the game interface.