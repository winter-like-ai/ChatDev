'''
This file contains the main application class `WordCountCLI` that manages the CLI for the word count tool. It allows users to input a text file path, calculates the word count using a utility function, and displays the result in the console.
'''
import sys
from utils import count_words_in_file
class WordCountCLI:
    """
    A CLI tool for counting words in a text file.
    """
    def __init__(self):
        pass
    def run(self):
        """
        Run the CLI tool.
        """
        if len(sys.argv) != 2:
            print("Usage: python main.py <file_path>")
            sys.exit(1)
        file_path = sys.argv[1]
        try:
            word_count = count_words_in_file(file_path)
            print(f"Total Word Count: {word_count}")
        except FileNotFoundError:
            print("Error: The specified file was not found.")
        except Exception as e:
            print(f"Error: An error occurred while processing the file: {e}")
if __name__ == "__main__":
    app = WordCountCLI()
    app.run()