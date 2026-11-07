================================================================================
POSITIONAL INVERTED INDEX - TELUGU WIKIPEDIA
Information Retrieval Assignment
================================================================================

1. PROJECT TITLE
----------------
Positional Inverted Index Using Telugu Wikipedia

2. PROJECT OBJECTIVE
--------------------
Build a positional inverted index for Telugu Wikipedia articles. The system
indexes articles from the Telugu Wikipedia XML dump, stores the vocabulary
in main memory (RAM), and stores the complete positional postings lists on
secondary storage (disk). It supports single-term lookup, phrase search
using positional information, and index validation.

3. DATASET AND LANGUAGE
-----------------------
Language: Telugu
Dataset: Telugu Wikipedia (tewiki) XML dump
Source: https://dumps.wikimedia.org/tewiki/

4. DATASET SOURCE AND DOWNLOAD INSTRUCTIONS
--------------------------------------------
Step 1: Visit https://dumps.wikimedia.org/tewiki/
Step 2: Select the latest completed dump date (e.g., 20261101)
Step 3: Download the file: tewiki-YYYYMMDD-pages-articles-multistream.xml.bz2
Step 4: Place the downloaded file in the data/raw/ directory

The download script can also be used:
    python _download_dump.py

5. PROJECT STRUCTURE
--------------------
telugu-positional-index/
|
|-- data/
|   |-- raw/                    # Telugu Wikipedia XML dump (not in ZIP)
|   |-- index/                  # Generated index files (not in ZIP)
|       |-- lexicon.json        # Vocabulary with CF, DF, offset, length
|       |-- postings.dat        # Positional postings on disk
|       |-- documents.jsonl     # Document catalog
|       |-- metadata.json       # Index statistics
|
|-- tests/
|   |-- __init__.py
|   |-- test_index.py           # Automated unit tests
|
|-- config.py                   # Configuration and paths
|-- tokenizer.py                # Telugu tokenization
|-- dataset.py                  # Wikipedia XML extraction
|-- indexer.py                  # Positional index builder
|-- search.py                   # Search interface
|-- main.py                     # Command-line interface
|-- generate_output.py          # Output report generator
|-- package_submission.py       # ZIP packaging
|-- requirements.txt            # Dependencies
|-- README.txt                  # This file
|-- output.txt                  # Generated output report

6. DESCRIPTION OF EACH MODULE
------------------------------
config.py
    Contains all configuration settings: file paths, directory paths,
    default processing limits, and Telugu Unicode range constants.

tokenizer.py
    Handles Telugu text tokenization. Normalizes Unicode text using NFC,
    recognizes Telugu Unicode characters (U+0C00 to U+0C7F), splits text
    into meaningful tokens, and assigns one-based positions. English text
    is lowercased. No stopword removal is performed.

dataset.py
    Extracts articles from Telugu Wikipedia XML dumps. Uses streaming XML
    parsing (iterparse) for memory efficiency. Cleans Wikipedia markup
    including references, HTML tags, templates, internal/external links,
    and formatting syntax. Skips redirects and empty articles.

indexer.py
    Builds the positional inverted index. Uses a temporary SQLite database
    during construction to avoid holding all postings in memory. Writes
    the final postings file term by term. Calculates Collection Frequency
    (CF) and Document Frequency (DF) for every term. Also includes index
    validation and loading functions.

search.py
    Provides search functionality. Loads the vocabulary into RAM at startup.
    Retrieves postings from disk on demand using file seek operations.
    Supports single-term lookup and phrase search using positional info.

main.py
    Command-line interface. Supports commands: build, term, phrase, stats,
    and validate.

generate_output.py
    Generates the output.txt report with 10 rare Telugu terms and their
    positional indexes, plus 5 test cases demonstrating system functionality.

package_submission.py
    Creates the source ZIP and final submission ZIP files.

7. TEXT PREPROCESSING AND TOKENIZATION
--------------------------------------
The tokenizer performs these steps:
1. Unicode normalization using NFC form
2. Regular expression matching for Telugu character sequences (U+0C00-U+0C7F)
   and ASCII alphanumeric sequences
3. Telugu vowel signs and combining marks stay attached to base characters
4. English letters are converted to lowercase
5. Punctuation and whitespace serve as token boundaries
6. Empty and meaningless tokens are filtered out
7. Each token gets a one-based position number

Example:
    Input:  "telugu bhasha bharatadeshamlo matlade bhasha"
    (Telugu: తెలుగు భాష భారతదేశంలో మాట్లాడే భాష)

    Token      Position
    --------   --------
    తెలుగు       1
    భాష          2
    భారతదేశంలో    3
    మాట్లాడే      4
    భాష          5

No stopwords are removed. All meaningful tokens retain their positions.

8. WHAT IS A POSITIONAL INVERTED INDEX?
---------------------------------------
A positional inverted index maps each term in the collection to a list
of documents containing that term, along with the exact positions where
the term occurs in each document.

Example:
    తెలుగు
    CF = 4, DF = 2
    Document 101: [1, 5, 8]
    Document 102: [3]

This means the term "తెలుగు" occurs 4 times total (CF=4) across 2
documents (DF=2). In document 101, it appears at positions 1, 5, and 8.
In document 102, it appears at position 3.

The positional information enables phrase searching by verifying that
query terms appear at consecutive positions.

9. COLLECTION FREQUENCY (CF)
-----------------------------
CF(t) = Total number of occurrences of term t across all documents.

If a term appears 3 times in document A and 2 times in document B,
then CF = 3 + 2 = 5.

10. DOCUMENT FREQUENCY (DF)
----------------------------
DF(t) = Number of distinct documents containing term t.

If a term appears in documents A and B (regardless of how many times),
then DF = 2.

11. HOW POSITIONAL POSTINGS ARE STORED
--------------------------------------
The postings file (postings.dat) contains JSON records for each term.
Each record maps document IDs to lists of positions:

    {"101": [1, 5, 8], "102": [3]}

Records are stored sequentially in the file. The lexicon stores the
byte offset and length of each record, allowing direct access without
reading the entire file.

12. MAIN MEMORY AND SECONDARY STORAGE ARCHITECTURE
----------------------------------------------------
Main Memory (RAM):
    - Vocabulary (all indexed terms)
    - Collection Frequency for each term
    - Document Frequency for each term
    - Byte offset into the postings file
    - Record length in the postings file

Secondary Storage (Disk):
    - Complete positional postings lists (postings.dat)
    - Document catalog (documents.jsonl)

When searching for a term:
    1. Look up the term in the in-memory vocabulary
    2. Get the offset and length from the vocabulary entry
    3. Open the postings file and seek to the offset
    4. Read exactly 'length' bytes
    5. Decode the JSON postings record
    6. Return the positional postings

This approach keeps memory usage low while allowing fast lookups.

13. INSTALLATION REQUIREMENTS
------------------------------
- Python 3.8 or later
- No external packages required (uses only Python standard library)

14. HOW TO PREPARE THE DATASET
-------------------------------
Step 1: Create the data directory:
    mkdir data\raw

Step 2: Download the Telugu Wikipedia dump:
    Visit https://dumps.wikimedia.org/tewiki/
    Download: tewiki-YYYYMMDD-pages-articles-multistream.xml.bz2
    Save to: data\raw\

Or use the download helper:
    python _download_dump.py

15. HOW TO BUILD THE INDEX
--------------------------
Build with default limit (10,000 articles):

    python main.py build

Build with a custom limit:

    python main.py build --limit 5000

The build process:
1. Reads the compressed XML dump using streaming parsing
2. Extracts and cleans Wikipedia articles
3. Tokenizes each article
4. Builds the positional index using a temporary SQLite staging database
5. Writes the lexicon (vocabulary) to lexicon.json
6. Writes the postings to postings.dat
7. Writes the document catalog to documents.jsonl
8. Writes index metadata to metadata.json

16. HOW TO SEARCH FOR A TERM
------------------------------
    python main.py term "తెలుగు"

This displays:
- The term
- Collection Frequency (CF)
- Document Frequency (DF)
- Document IDs with their position lists

17. HOW TO PERFORM PHRASE SEARCH
---------------------------------
    python main.py phrase "తెలుగు భాష"

The phrase search:
1. Tokenizes the query phrase
2. Retrieves postings for each term from disk
3. Finds documents containing all query terms
4. Checks that terms appear at consecutive positions
5. Returns documents where the exact phrase appears

18. HOW TO CHECK INDEX STATISTICS
-----------------------------------
    python main.py stats

Displays:
- Total indexed documents
- Vocabulary size
- Total indexed tokens
- Average document length
- Postings file size

19. HOW TO VALIDATE THE INDEX
-------------------------------
    python main.py validate

Checks:
- Every vocabulary term has valid CF and DF
- Every postings offset is valid
- Every postings record can be read from disk
- CF matches the total number of stored positions
- DF matches the number of documents in each postings record
- Positions are positive integers, sorted, and unique
- Document IDs exist in the document catalog
- Metadata matches actual files

20. HOW TO RUN AUTOMATED TESTS
-------------------------------
    python -m unittest discover -s tests -v

The test suite uses a small synthetic Telugu dataset and verifies:
- Unicode normalization and Telugu tokenization
- One-based token positions
- Collection Frequency calculation
- Document Frequency calculation
- Positional postings retrieval from disk
- Phrase searching
- Unknown term handling
- Index loading after close and reopen

21. DESCRIPTION OF OUTPUT.TXT
------------------------------
The output.txt file contains two sections:

Section A: Ten Rare Telugu Terms
    10 rare Telugu terms selected from the actual indexed corpus.
    For each term: CF, DF, document IDs, and positions.
    Selection criteria: low DF (primary), low CF (secondary),
    must be meaningful Telugu words with at least 2 Telugu characters.

Section B: Five Test Cases
    Test 1: Single-term lookup of a common term
    Test 2: Rare-term lookup with low document frequency
    Test 3: Repeated-term positions in a single document
    Test 4: Exact phrase search using positional index
    Test 5: Unknown-term lookup (term not in vocabulary)

All results are generated from the actual Telugu Wikipedia index.

22. DATASET AND INDEX HOSTING INFORMATION
------------------------------------------
Dataset Source: https://dumps.wikimedia.org/tewiki/

Dataset Details:
    Dump file: tewiki-20261101-pages-articles-multistream.xml.bz2
    Dump date: November 1, 2026
    Source: Wikimedia Foundation

GitHub/Drive Link to Complete Generated Index:
    [ADD ACTUAL LINK AFTER UPLOADING]

Note: The complete dataset and full generated index are NOT included in
the submission ZIP. They should be regenerated using the build command
or downloaded from the link above.

================================================================================
END OF README
================================================================================

