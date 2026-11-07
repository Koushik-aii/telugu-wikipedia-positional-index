"""
tokenizer.py - Telugu Text Tokenizer

Handles Unicode normalization and tokenization for Telugu text.
Uses one-based positions for the positional inverted index.
"""

import re
import unicodedata


def normalize_text(text):
    """
    Normalize Unicode text using NFC form.
    This ensures Telugu combining marks are properly composed.
    """
    if not text:
        return ""
    return unicodedata.normalize("NFC", text)


def is_telugu_char(ch):
    """Check if a character is in the Telugu Unicode block (U+0C00-U+0C7F)."""
    cp = ord(ch)
    return 0x0C00 <= cp <= 0x0C7F


def is_meaningful_token(token):
    """
    Check if a token is meaningful (not just punctuation or whitespace).
    A meaningful token contains at least one letter or digit.
    """
    if not token:
        return False
    for ch in token:
        if ch.isalpha() or ch.isdigit() or is_telugu_char(ch):
            return True
    return False


def tokenize(text):
    """
    Tokenize Telugu text into a list of (token, position) tuples.
    
    Rules:
    - Normalize Unicode using NFC
    - Telugu characters (letters, vowel signs, combining marks) stay together
    - English text is lowercased
    - Split on whitespace and punctuation
    - Positions are one-based
    - All meaningful tokens are kept (no stopword removal)
    
    Returns:
        list of (token_string, position) tuples with one-based positions
    """
    if not text:
        return []
    
    # Normalize Unicode
    text = normalize_text(text)
    
    # Pattern to match tokens:
    # - Sequences of Telugu characters (letters, vowel signs, marks, numerals)
    # - Sequences of ASCII alphanumeric characters
    # - Telugu digits (U+0C66 to U+0C6F)
    # We use Unicode categories to keep combining marks attached
    
    # Build a regex that matches Telugu character sequences or ASCII word chars
    # Telugu block: \u0C00-\u0C7F
    # This includes letters, vowel signs, combining marks, and digits
    token_pattern = re.compile(
        r'[\u0C00-\u0C7F]+'   # Telugu characters (including marks and digits)
        r'|[a-zA-Z0-9]+'       # ASCII alphanumeric
        r'|[\u0C66-\u0C6F]+'   # Telugu digits (already covered above, but explicit)
    )
    
    raw_tokens = token_pattern.findall(text)
    
    result = []
    position = 0
    
    for token in raw_tokens:
        # Lowercase English letters
        processed = token.lower() if token.isascii() else token
        
        if is_meaningful_token(processed):
            position += 1  # one-based
            result.append((processed, position))
    
    return result


def get_tokens_only(text):
    """
    Get just the token strings from text (without positions).
    Useful for simple text processing.
    """
    return [token for token, pos in tokenize(text)]


def get_positions_dict(text):
    """
    Get a dictionary mapping each token to its list of positions.
    Useful for building the positional index of a single document.
    
    Returns:
        dict: {token: [pos1, pos2, ...]}
    """
    positions = {}
    for token, pos in tokenize(text):
        if token not in positions:
            positions[token] = []
        positions[token].append(pos)
    return positions

