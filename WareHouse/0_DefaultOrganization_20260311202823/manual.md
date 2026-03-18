# Checkers (Draughts) Game - User Manual

## Overview
Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a modern graphical interface. The game follows standard international draughts rules on an 8x8 board, featuring two-player gameplay with alternating turns, mandatory captures, king promotion, and multiple jumps.

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.8 or higher
- **RAM**: 4 GB minimum
- **Storage**: 50 MB free space
- **Display**: 1024x768 resolution minimum

### Recommended Requirements
- **Operating System**: Latest version of Windows, macOS, or Linux
- **Python**: Version 3.10 or higher
- **RAM**: 8 GB
- **Storage**: 100 MB free space
- **Display**: 1920x1080 resolution

## Installation Guide

### Step 1: Install Python
If you don't have Python installed, download and install it from [python.org](https://www.python.org/downloads/).

Verify installation by opening a terminal/command prompt and typing:
```bash
python --version
```

### Step 2: Install Pygame
The game requires Pygame library. Install it using pip:

```bash
pip install pygame
```

### Step 3: Download Game Files
Download all the game files and place them in a single directory:
- `main.py`
- `constants.py`
- `piece.py`
- `board.py`
- `game.py`

Your directory structure should look like:
```
checkers_game/
├── main.py
├── constants.py
├── piece.py
├── board.py
└── game.py
```

## How to Play

### Starting the Game
1. Navigate to the game directory in your terminal/command prompt
2. Run the game:
```bash
python main.py
```

### Game Interface
The game window consists of:
- **Game Board**: 8x8 checkerboard with alternating light and dark squares
- **Turn Indicator**: Top-left corner shows whose turn it is
- **Move Notation**: Top-right corner displays recent moves in algebraic notation
- **Instructions**: Bottom-left corner shows game controls
- **Valid Move Indicators**: Green circles highlight possible moves for selected pieces

### Game Controls

#### Mouse Controls
- **Left Click**: Select a piece or move to a highlighted square
- **Click on Piece**: Select your piece (must be your color and turn)
- **Click on Highlighted Square**: Move selected piece to that position

#### Keyboard Controls
- **R Key**: Reset the game to starting position
- **ESC Key**: Exit the game
- **Close Window**: Click the X button or press Alt+F4

### Game Rules

#### Starting Position
- Red pieces start on the top three rows (rows 5-7)
- White pieces start on the bottom three rows (rows 0-2)
- Only dark squares are used for pieces

#### Movement Rules
1. **Regular Pieces**:
   - Red pieces move upward (decreasing row numbers)
   - White pieces move downward (increasing row numbers)
   - Move one square diagonally forward to an empty dark square

2. **Kings**:
   - Can move both forward and backward
   - Move one square diagonally in any direction

#### Capturing Rules
1. **Mandatory Capture**: If a capture is available, you must take it
2. **Capture Move**: Jump over an opponent's piece diagonally to an empty square
3. **Multiple Jumps**: If another capture is available after a jump, you must continue jumping
4. **King Captures**: Kings can capture in all four diagonal directions

#### King Promotion
- Red pieces become kings when reaching row 0 (top row)
- White pieces become kings when reaching row 7 (bottom row)
- Kings are marked with a colored crown (yellow for red kings, blue for white kings)

#### Move Notation
Moves are displayed in algebraic notation:
- Columns: a-h (left to right)
- Rows: 1-8 (bottom to top)
- Example: "a3-b4" means moving from column a, row 3 to column b, row 4

### Game Flow
1. **Turn Order**: Red moves first, then alternating turns
2. **Piece Selection**: Click on your piece (must be your turn)
3. **Move Execution**: Click on a highlighted square to move
4. **Capture Sequences**: Continue clicking if multiple jumps are available
5. **Turn End**: Turn switches automatically after all possible moves/captures are completed
6. **Game End**: Game ends when one player has no pieces left or no valid moves

### Winning Conditions
You win the game when:
1. You capture all opponent's pieces
2. Your opponent has no valid moves left

## Features

### Core Features
- **Complete Checkers Implementation**: All standard rules implemented
- **Graphical Interface**: Clean, intuitive Pygame-based interface
- **Move Validation**: Automatic validation of all moves
- **Mandatory Capture Enforcement**: System prevents illegal non-capture moves when captures are available
- **Multiple Jumps**: Support for consecutive captures in a single turn
- **King Promotion**: Automatic promotion when reaching opposite end
- **Move History**: Display of recent moves in algebraic notation
- **Turn Indicator**: Clear display of whose turn it is

### Visual Features
- **Color-coded Pieces**: Red and white pieces with clear distinction
- **King Visualization**: Crown symbols for king pieces
- **Valid Move Highlighting**: Green circles show possible moves
- **Board Coordinates**: Algebraic notation for move tracking
- **Winner Announcement**: Large display when game ends

### Game Management
- **Reset Function**: Instant game reset with R key
- **Game State Preservation**: Maintains all game rules and state
- **Error Prevention**: Prevents illegal moves and selections

## Troubleshooting

### Common Issues

#### Issue: "ModuleNotFoundError: No module named 'pygame'"
**Solution**: Install Pygame:
```bash
pip install pygame
```

#### Issue: Game window doesn't open
**Solution**: 
1. Check Python installation: `python --version`
2. Ensure all game files are in the same directory
3. Run from correct directory: `cd path/to/checkers_game`

#### Issue: Game runs but pieces don't move
**Solution**:
1. Ensure you're clicking on dark squares only
2. Check that it's your turn (see turn indicator)
3. Verify you're selecting your own colored pieces

#### Issue: Game crashes unexpectedly
**Solution**:
1. Update Pygame: `pip install --upgrade pygame`
2. Check Python version compatibility
3. Restart the game

### Performance Issues
- **Laggy Graphics**: Reduce other running applications
- **Slow Response**: Ensure your system meets minimum requirements
- **Display Issues**: Try running in windowed mode if fullscreen has issues

## Tips and Strategies

### Beginner Tips
1. **Control the Center**: Pieces in the center have more movement options
2. **Create Kings**: Get your pieces to the opposite end to promote them
3. **Force Captures**: Position pieces to force opponent into disadvantageous captures
4. **Protect Back Row**: Keep pieces on your back row to prevent easy king promotions

### Advanced Strategies
1. **Sacrifice Tactics**: Sometimes sacrificing a piece can lead to multiple captures
2. **King Positioning**: Kings are powerful - use them to control key squares
3. **Endgame Planning**: In endgames, focus on creating unstoppable king advantages
4. **Tempo Play**: Force your opponent into moves that benefit your position

## Development Information

### File Structure
- `main.py`: Game initialization and main loop
- `constants.py`: Game constants and configuration
- `piece.py`: Piece class with movement logic
- `board.py`: Board class with game state management
- `game.py`: Game class with turn management and UI

### Extending the Game
The modular design allows for easy extensions:
- Modify `constants.py` to change colors or board size
- Extend `piece.py` for custom movement rules
- Enhance `game.py` for additional game modes

## Support

### Getting Help
If you encounter issues:
1. Check the Troubleshooting section above
2. Verify your installation meets requirements
3. Ensure you're following the correct gameplay rules

### Reporting Bugs
Please report any bugs or issues with:
1. Your operating system and Python version
2. Steps to reproduce the issue
3. Screenshots if applicable

## License and Credits
This Checkers game is developed for educational and entertainment purposes. The implementation follows standard international draughts rules.

### Acknowledgments
- Game design based on international draughts rules
- Pygame library for graphical interface
- Standard algebraic notation for move tracking

## Version Information
- **Current Version**: 1.0
- **Release Date**: [Current Date]
- **Compatibility**: Python 3.8+, Pygame 2.0+

Enjoy playing Checkers! Remember, the best way to improve is to practice and analyze your games. Good luck and have fun!