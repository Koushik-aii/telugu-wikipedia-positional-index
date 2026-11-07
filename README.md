# Positional Inverted Index Using Telugu Wikipedia

Information Retrieval (IR) Assignment — Implementation of a Positional Inverted Index for Indian Languages (Telugu Wikipedia).

---

## 📌 Project Overview
This project constructs an end-to-end **Positional Inverted Index** for Telugu Wikipedia articles. The system features a memory-efficient architecture:
- **Main Memory (RAM):** Holds vocabulary terms, Collection Frequency (CF), Document Frequency (DF), and secondary-storage byte offsets.
- **Secondary Storage (Disk):** Holds full positional postings lists in binary JSON format (`postings.dat`), accessed on-demand using exact byte offset seeks without loading the entire postings file into memory.

---

## 🚀 Key Features
- **Telugu Unicode Tokenizer:** NFC normalization, Telugu block recognition (`U+0C00–U+0C7F`), 1-based token positions, preserves Telugu vowel signs and combining marks.
- **Streaming Wikipedia Extraction:** XML `iterparse` on multistream BZ2 dumps, cleans Wikipedia markup (templates, refs, tables, links), skips redirects.
- **Accurate Frequency Calculation:** Computes both Collection Frequency (CF) and Document Frequency (DF).
- **Secondary Storage Postings Retrieval:** Fast $O(1)$ disk seek per term using precomputed byte offsets and record lengths.
- **Phrase Searching:** Verifies strict consecutive positional adjacency using the positional postings index.
- **Automated Validation & Testing:** Includes comprehensive unit tests and automated index verification.

---

## 📁 Repository Structure
```text
telugu-positional-index/
├── tests/
│   ├── __init__.py
│   └── test_index.py           # Unit tests (synthetic Telugu test data)
├── config.py                   # Configuration and path constants
├── tokenizer.py                # Telugu text normalization and tokenization
├── dataset.py                  # Wikipedia XML extraction and markup cleaning
├── indexer.py                  # Positional index builder and validator
├── search.py                   # In-memory vocabulary search and disk retrieval
├── main.py                     # CLI interface (build, term, phrase, stats, validate)
├── generate_output.py          # Output report generator (10 rare terms + 5 test cases)
├── package_submission.py       # ZIP packaging for academic submission
├── _download_dump.py           # Streaming dump downloader
├── requirements.txt            # Python dependencies (Standard library only)
├── README.txt                  # Full documentation for submission
├── README.md                   # GitHub documentation
└── output.txt                  # Programmatically generated execution output
```

---

## 🛠️ Setup & Installation
The project uses **Python 3.8+** standard library modules only (no external dependencies required).

```bash
git clone https://github.com/Koushik-aii/telugu-wikipedia-positional-index.git
cd telugu-wikipedia-positional-index
```

---

## 📖 Usage Instructions

### 1. Build the Index
Download the Telugu Wikipedia dump (or use the built-in streaming downloader):
```powershell
python main.py build --limit 10000
```

### 2. Single-Term Lookup
Search for an individual term:
```powershell
python main.py term "తెలుగు"
```

### 3. Exact Phrase Search
Search for consecutive phrases using positional postings:
```powershell
python main.py phrase "తెలుగు భాష"
```

### 4. Corpus Statistics
Display collection and vocabulary statistics:
```powershell
python main.py stats
```

### 5. Validate Index
Validate all vocabulary entries, offsets, postings, and catalog references:
```powershell
python main.py validate
```

### 6. Run Automated Tests
Execute the unit test suite:
```powershell
python -m unittest discover -s tests -v
```

### 7. Generate Submission Report & Packages
Generate `output.txt` and packaging ZIPs:
```powershell
python generate_output.py
python package_submission.py --roll-no <YOUR_ROLL_NO>
```

---

## 📊 Corpus & Index Statistics (10,000 Articles)
- **Dataset:** `tewiki-20261101-pages-articles-multistream.xml.bz2` (November 1, 2026)
- **Indexed Articles:** 10,000 articles
- **Vocabulary Size:** 271,758 unique terms
- **Total Indexed Tokens:** 4,744,750 tokens
- **Average Document Length:** 474.48 tokens / document
- **Postings File Size:** 50.07 MB (`postings.dat`)

---

## 📄 License
Academic and educational use under MIT License.
