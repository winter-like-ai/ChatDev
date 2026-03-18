# Checkers Game - User Manual

## Overview

Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a modern graphical interface. The game follows standard international draughts rules with an 8x8 board, alternating turns between two players, and includes all standard capture and kinging rules.

## 🎮 Main Features

### Core Gameplay
- **8x8 Board**: Standard checkers board with alternating dark and light squares
- **Two Players**: Red and White pieces with Red starting first
- **Standard Rules**: 
  - Pieces move diagonally forward only (unless kinged)
  - Mandatory capture rule enforced
  - Multi-capture sequences supported
  - King promotion when reaching opponent's back row
  - Kings can move and capture both forward and backward

### User Interface
- **Visual Board**: Clean, intuitive graphical interface with color-coded pieces
- **Move Notation**: Each square displays coordinates (row, column) for easy move planning
- **Selection Highlighting**: Selected pieces and valid moves are clearly marked
- **Game Status Display**: Shows current turn, piece counts, and king counts
- **Game Over Detection**: Automatic win detection with restart options

### Game Management
- **Mandatory Capture Enforcement**: System prevents illegal moves when captures are available
- **Multi-Capture Sequences**: Players must complete all possible captures in a turn
- **Turn Management**: Automatic turn switching after valid moves
- **Restart Capability**: Easy game restart after completion

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Step-by-Step Installation

1. **Download the Game Files**
   Ensure you have the following files in a directory:
   - `main.py`
   - `game.py`
   - `gui.py`
   - `requirements.txt`

2. **Install Dependencies**
   Open a terminal/command prompt in the game directory and run:
   ```bash
   pip install -r requirements.txt
   ```
   This will install PyGame version 2.5.2, the only required dependency.

3. **Verify Installation**
   ```bash
   python --version
   pip show pygame
   ```
   You should see Python 3.7+ and PyGame 2.5.2 installed.

## 🎯 How to Play

### Starting the Game
1. Navigate to the game directory in your terminal
2. Run the game:
   ```bash
   python main.py
   ```
3. The game window will open with the board initialized

### Game Controls

#### Mouse Controls
- **Select a Piece**: Click on your piece (Red or White depending on turn)
- **Make a Move**: Click on a highlighted valid move position
- **Cancel Selection**: Click anywhere else on the board

#### Keyboard Controls
- **R Key**: Restart the game (only available when game is over)
- **ESC Key**: Quit the game at any time

### Understanding the Interface

#### Board Layout
- **Coordinates**: Each square shows (row, column) notation in the top-left corner
- **Square Colors**: Brown and beige alternating squares
- **Piece Colors**: 
  - Red pieces: Player 1 (starts first)
  - White pieces: Player 2

#### Status Information (Top-left corner)
- Current player's turn
- Remaining piece counts for both players
- Number of kings for each player

#### Visual Indicators
- **Green Outline**: Currently selected piece
- **Green Circles**: Valid move positions
- **Gray Center Dot**: King pieces

### Game Rules

#### Basic Movement
1. **Regular Pieces**:
   - Red pieces move downward (increasing row numbers)
   - White pieces move upward (decreasing row numbers)
   - Move one square diagonally forward to an empty square

2. **King Pieces**:
   - Can move diagonally in any direction
   - Move one square diagonally to an empty square

#### Capturing
1. **Mandatory Capture**: If a capture is available, you must take it
2. **Capture Move**: Jump over opponent's piece diagonally to an empty square
3. **Multi-Capture**: If another capture is available from the new position, you must continue capturing
4. **King Capture**: Kings can capture in any diagonal direction

#### King Promotion
- Red pieces become kings when reaching row 7 (bottom row)
- White pieces become kings when reaching row 0 (top row)
- Kings are marked with a gray dot in the center

#### Winning the Game
The game ends when:
- One player has no pieces remaining
- One player has no legal moves available
- The winner is announced with a game over message

### Playing a Turn

1. **Select Your Piece**
   - Click on one of your pieces
   - Valid moves will be highlighted with green circles

2. **Make Your Move**
   - Click on a highlighted square to move
   - If multiple captures are possible, you'll see only capture moves highlighted

3. **Complete Multi-Captures**
   - If you capture a piece and more captures are available:
     - The same piece remains selected
     - Only further capture moves are shown
     - You must complete all possible captures

4. **End Your Turn**
   - After completing all moves/captures, turn automatically switches
   - If no captures were made, turn switches after a single move

### Example Gameplay

1. **Starting Position**: Red pieces on rows 0-2, White pieces on rows 5-7
2. **First Move**: Red player selects piece at (2,1) and moves to (3,2)
3. **Capture Example**: White piece at (4,3) captures Red piece at (3,2) by moving to (2,4)
4. **King Promotion**: Red piece moves from (6,1) to (7,0) and becomes a king
5. **Multi-Capture**: King captures pieces at (6,1) and (4,3) in sequence

## 🛠️ Troubleshooting

### Common Issues

1. **Game Won't Start**
   ```
   Error: No module named 'pygame'
   ```
   **Solution**: Install dependencies: `pip install -r requirements.txt`

2. **Font Warning Messages**
   ```
   Warning: Could not find system font
   ```
   **Solution**: This is normal - the game will use default PyGame fonts

3. **Window Closes Immediately**
   **Solution**: Run from terminal/command prompt to see error messages

4. **Mouse Clicks Not Working**
   **Solution**: Ensure you're clicking within the board area (not on status text)

### Performance Tips
- Close other graphics-intensive applications if experiencing lag
- Reduce screen resolution if on older hardware
- Ensure latest graphics drivers are installed

## 📁 File Structure

```
checkers_game/
├── main.py          # Entry point - starts the game
├── game.py          # Core game logic and rules
├── gui.py           # Graphical interface and rendering
└── requirements.txt # Python dependencies
```

## 🔧 Advanced Usage

### Customizing the Game
The game code is modular and can be modified:

1. **Change Colors**: Modify color constants in `gui.py`
2. **Adjust Board Size**: Change `WIDTH` and `HEIGHT` in `GameGUI.__init__`
3. **Modify Rules**: Edit movement logic in `game.py`

### Running from Different Environments
- **IDEs**: Can be run from PyCharm, VS Code, etc.
- **Virtual Environments**: Works with venv, conda, etc.
- **Packaged Executable**: Can be converted to executable using PyInstaller

## 🎮 Tips for Beginners

1. **Control the Center**: Pieces in the center have more movement options
2. **Create Kings**: Getting kings early gives significant advantage
3. **Force Captures**: Position pieces to force opponent into disadvantageous captures
4. **Protect Back Row**: Keep pieces on your back row to prevent opponent kinging
5. **Plan Multi-Captures**: Look for opportunities to capture multiple pieces in one turn

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Ensure all dependencies are installed correctly
3. Verify Python version compatibility
4. Review the game rules if behavior seems unexpected

## 📄 License

This Checkers game implementation is provided for educational and entertainment purposes. Feel free to modify and distribute with proper attribution.

---

Enjoy the game! May the best strategist win! ♟️