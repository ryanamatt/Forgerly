# src/python/utils/chapter_utils

def calculate_word_count(text: str) -> int:
    """
    Calculates the word count of the plain text content.

    Words are counted by splitting the text using various whitespace separators.

    :param text: The plain text content string.
    :type text: str

    :returns: The calculated number of words.
    :rtype: int
    """
    # Use split() without arguments to handle various whitespace separators
    words = text.split()
    return len(words)

def calculate_character_count(text: str, include_spaces: bool = True) -> int:
    """
    Calculates the character count of the plain text content.

    :param text: The plain text content string.
    :type text: str
    :param include_spaces: If ``True`` (default), spaces and all other whitespace 
                           characters are included in the count. If ``False``, 
                           all whitespace is excluded.
    :type include_spaces: bool

    :returns: The calculated number of characters.
    :rtype: int
    """
    if include_spaces:
        return len(text)
    else:
        return len("".join(text.split())) # Counts characters excluding all whitespace

def calculate_read_time(word_count: int, wpm: int = 250) -> str:
    """
    Calculates the estimated read time based on word count and words-per-minute (WPM).

    The time is rounded up to the nearest whole minute and formatted as 'X min'.
    Uses a default WPM of 250 if not specified.

    :param word_count: The total number of words in the text.
    :type word_count: int
    :param wpm: The assumed reading speed in words per minute. Must be greater than 0.
    :type wpm: int

    :returns: A formatted string for the estimated read time (e.g., '5 min', '<1 min', '0 min').
    :rtype: str
    """
    if wpm <= 0 or word_count == 0:
        return "0 min"
    
    # Calculate time in minutes (round up to nearest whole minute)
    minutes = (word_count + wpm - 1) // wpm # Integer division equivalent of ceil(word_count / wpm)
    
    # Handle hours/minutes if needed, but for simplicity, stick to minutes
    if minutes == 0:
        # If words > 0 but time is less than 1 min, show '<1 min'
        return "<1 min" if word_count > 0 else "0 min"
    
    return f"{minutes} min"