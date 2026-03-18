# Checkers Game - User Manual

## Overview

Welcome to the Checkers (Draughts) game! This is a fully functional implementation of the classic board game with a modern graphical interface. The game features an 8x8 board, two-player gameplay with alternating turns, standard capture rules, and king promotion mechanics.

## ✨ Key Features

- **Complete Checkers Implementation**: Full implementation of standard Checkers rules
- **Visual Gameplay**: Clean, intuitive graphical interface with Pygame
- **Move Notation Support**: Board coordinates displayed for move tracking
- **Game State Tracking**: Real-time piece counts, king counts, and turn indicators
- **Interactive Controls**: Click-based piece selection and movement
- **Win Detection**: Automatic winner detection and celebration screen
- **Game Restart**: Easy restart functionality

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Step-by-Step Installation

1. **Clone or Download the Game Files**
   Ensure you have all the following files in the same directory:
   - `main.py`
   - `constants.py`
   - `piece.py`
   - `game.py`
   - `gui.py`
   - `requirements.txt`

2. **Install Dependencies**
   Open your terminal/command prompt and navigate to the game directory, then run:
   ```bash
   pip install -r requirements.txt
   ```
   This will install Pygame, the only required dependency.

3. **Verify Installation**
   ```bash
   python --version
   pip show pygame
   ```

## 🎮 How to Play

### Starting the Game
Run the game by executing:
```bash
python main.py
```

### Game Interface
The game window consists of two main sections:

1. **Game Board (Left)**
   - 8x8 checkerboard with alternating dark and light squares
   - Row numbers (0-7) on left and right sides
   - Column letters (A-H) on top and bottom
   - Red pieces start at the top (rows 0-2)
   - Blue pieces start at the bottom (rows 5-7)

2. **Information Panel (Right)**
   - Current turn indicator
   - Piece counts for both players
   - King counts for both players
   - Game instructions
   - Move notation display

### Game Rules

#### Basic Movement
- **Red** moves first
- Regular pieces move diagonally forward only
- Pieces can only move to dark squares
- One square per move (unless capturing)

#### Capturing
- Capture opponent pieces by jumping over them diagonally
- Multiple captures in one turn are allowed
- Captured pieces are removed from the board

#### King Promotion
- When a piece reaches the opposite end of the board:
  - Red pieces reaching row 7 become kings
  - Blue pieces reaching row 0 become kings
- Kings are marked with a gold crown
- Kings can move and capture both forward and backward

### Playing the Game

#### Selecting a Piece
1. Click on one of your pieces (red or blue depending on turn)
2. The selected piece will be highlighted in yellow
3. Valid move squares will be highlighted in green

#### Making a Move
1. After selecting a piece, click on a green-highlighted square
2. The piece will move to the selected square
3. If you jump over an opponent's piece, it will be captured
4. The turn automatically switches to the other player

#### Move Notation
The game uses algebraic notation similar to chess:
- Columns: A-H (left to right)
- Rows: 0-7 (top to bottom)
- Example: Moving from A3 to B4

### Game Controls

#### Mouse Controls
- **Left Click**: Select piece or destination square
- Move the cursor over the board to see coordinate hints

#### Keyboard Controls
- **R Key**: Restart the game (at any time)
- **ESC Key**: Quit the game
- **Window Close Button**: Exit the game

### Game States

#### Active Game
- Players alternate turns
- Valid moves are highlighted
- Piece counts update in real-time

#### Game End
When one player loses all pieces:
- Winner announcement screen appears
- "Press R to restart or ESC to quit" message displayed
- Game board is dimmed with overlay

## 🛠️ Troubleshooting

### Common Issues

1. **Game won't start**
   ```
   Error: No module named 'pygame'
   ```
   **Solution**: Install Pygame: `pip install pygame`

2. **Window appears but closes immediately**
   **Solution**: Run from command line to see error messages

3. **Pieces won't move**
   **Solution**: Ensure you're clicking on valid squares (highlighted in green)

4. **Game seems frozen**
   **Solution**: Check if it's the other player's turn (see turn indicator)

### Performance Tips
- Close other graphics-intensive applications
- Ensure your display drivers are up to date
- Run in full-screen mode if available (future feature)

## 📁 File Structure

```
checkers_game/
├── main.py          # Entry point - launches the game
├── constants.py     # Game constants (colors, sizes, etc.)
├── piece.py         # Piece class - handles individual pieces
├── game.py          # Game logic - rules, moves, state
├── gui.py           # Graphical interface - drawing, input
└── requirements.txt # Dependencies
```

## 🔧 Advanced Features

### Customization
You can modify game parameters in `constants.py`:
- Change colors
- Adjust board size
- Modify square dimensions
- Change game speed (FPS)

### Extending the Game
The modular design allows for easy extensions:
- Add AI opponent
- Implement network multiplayer
- Add sound effects
- Create different game modes

## 🤝 Support

### Getting Help
If you encounter issues:
1. Check the console for error messages
2. Verify all files are in the same directory
3. Ensure Python and Pygame are properly installed

### Reporting Bugs
Please report any issues with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots if applicable

## 📄 License
This Checkers game is provided for educational and entertainment purposes. Feel free to modify and distribute with proper attribution.

## 🎯 Quick Start Summary

1. Install Python and Pygame
2. Download all game files to one folder
3. Run `python main.py`
4. Click red pieces to start playing
5. Move diagonally, capture opponents, become king!

Enjoy the game! 🎮

---

*Note: This implementation follows standard American Checkers rules. Some regional variations may differ.*