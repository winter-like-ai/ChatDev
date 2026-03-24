'''
This file contains the utility function `count_words_in_file` that calculates the total word count in a given text file. It handles basic punctuation and counts sequences of alphanumeric characters as words.
'''
import re
def count_words_in_file(file_path):
    """
    Count the total number of words in a text file.
    Args:
        file_path (str): Path to the text file.
    Returns:
        int: Total word count.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            # Use regex to find sequences of alphanumeric characters
            words = re.findall(r'\b\w+\b', text)
            return len(words)
    except FileNotFoundError:
        raise FileNotFoundError("The specified file was not found.")
    except Exception as e:
        raise Exception(f"An error occurred while processing the file: {e}")