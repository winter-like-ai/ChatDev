'''
Main entry point for Checkers game
'''
from gui import GUI
def main():
    print("Starting Checkers Game...")
    print("Instructions:")
    print("1. Click on a piece to select it")
    print("2. Click on a highlighted square to move")
    print("3. Red pieces start at the bottom")
    print("4. Blue pieces start at the top")
    print("5. Press 'R' to reset the game")
    print("6. Press 'ESC' to quit")
    print("\nGame starting...")
    gui = GUI()
    gui.run()
if __name__ == "__main__":
    main()