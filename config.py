"""
config.py - Configuration for Telugu Positional Inverted Index
"""

import os

# Base project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data directories
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
INDEX_DIR = os.path.join(DATA_DIR, "index")

# Index files
LEXICON_FILE = os.path.join(INDEX_DIR, "lexicon.json")
POSTINGS_FILE = os.path.join(INDEX_DIR, "postings.dat")
DOCUMENTS_FILE = os.path.join(INDEX_DIR, "documents.jsonl")
METADATA_FILE = os.path.join(INDEX_DIR, "metadata.json")

# Default processing limit
DEFAULT_ARTICLE_LIMIT = 10000

# Telugu Unicode range
TELUGU_START = 0x0C00
TELUGU_END = 0x0C7F

# Ensure directories exist
def ensure_dirs():
    """Create required directories if they don't exist."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(INDEX_DIR, exist_ok=True)

