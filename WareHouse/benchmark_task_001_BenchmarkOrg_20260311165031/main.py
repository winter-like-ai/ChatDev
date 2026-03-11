'''
Main entry point for the Capital of China application.
This file launches the GUI application.
'''
from gui import CapitalApp
def main():
    """Main function to start the application."""
    app = CapitalApp()
    app.run()
if __name__ == "__main__":
    main()