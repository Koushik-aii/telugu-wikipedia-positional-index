"""
indexer.py - Positional Inverted Index Builder

Builds the positional inverted index:
- Vocabulary (lexicon) stored in RAM with CF, DF, offset, length
- Positional postings stored on secondary storage (postings.dat)
- Document catalog stored in documents.jsonl
"""

import json
import os
import sqlite3
import tempfile

from config import (
    INDEX_DIR, LEXICON_FILE, POSTINGS_FILE,
    DOCUMENTS_FILE, METADATA_FILE, ensure_dirs
)
from tokenizer import get_positions_dict


def build_index(articles, index_dir=None):
    """
    Build the positional inverted index from extracted articles.
    
    Uses a temporary SQLite database to stage term occurrences during
    construction, then writes the final postings file term by term.
    
    Args:
        articles: Iterable of dicts with 'id', 'title', 'text' keys
        index_dir: Optional override for index directory
    
    Returns:
        dict with index statistics
    """
    ensure_dirs()
    
    if index_dir:
        lexicon_file = os.path.join(index_dir, "lexicon.json")
        postings_file = os.path.join(index_dir, "postings.dat")
        documents_file = os.path.join(index_dir, "documents.jsonl")
        metadata_file = os.path.join(index_dir, "metadata.json")
    else:
        lexicon_file = LEXICON_FILE
        postings_file = POSTINGS_FILE
        documents_file = DOCUMENTS_FILE
        metadata_file = METADATA_FILE
    
    # Stats
    total_docs = 0
    total_tokens = 0
    doc_lengths = []
    
    # Use a temp SQLite database to accumulate postings
    # This avoids holding all postings in a huge Python dict
    temp_db_path = os.path.join(os.path.dirname(postings_file), "_temp_index.db")
    
    try:
        conn = sqlite3.connect(temp_db_path)
        cur = conn.cursor()
        
        # Optimize SQLite for bulk indexing speed
        cur.execute("PRAGMA synchronous = OFF")
        cur.execute("PRAGMA journal_mode = OFF")
        cur.execute("PRAGMA cache_size = 50000")
        
        # Create staging table without index during inserts for max speed
        cur.execute("""
            CREATE TABLE IF NOT EXISTS postings (
                term TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                positions TEXT NOT NULL
            )
        """)
        conn.commit()
        
        # Phase 1: Process documents and store postings in SQLite
        print("Phase 1: Processing documents and collecting postings...", flush=True)
        
        # Open documents file for writing
        with open(documents_file, 'w', encoding='utf-8') as doc_file:
            batch = []
            batch_size = 10000
            
            for article in articles:
                doc_id = str(article['id'])
                title = article['title']
                text = article['text']
                
                # Tokenize and get positions for each term
                term_positions = get_positions_dict(text)
                
                # Count tokens in this document
                doc_token_count = sum(len(positions) for positions in term_positions.values())
                total_tokens += doc_token_count
                doc_lengths.append(doc_token_count)
                total_docs += 1
                
                # Write document record
                doc_record = {
                    'id': doc_id,
                    'title': title,
                    'text': text
                }
                doc_file.write(json.dumps(doc_record, ensure_ascii=False) + '\n')
                
                # Add postings to batch
                for term, positions in term_positions.items():
                    batch.append((term, doc_id, json.dumps(positions)))
                
                # Flush batch to SQLite
                if len(batch) >= batch_size:
                    cur.executemany(
                        "INSERT INTO postings (term, doc_id, positions) VALUES (?, ?, ?)",
                        batch
                    )
                    batch = []
                
                if total_docs % 500 == 0:
                    print(f"  Processed {total_docs} documents ({total_tokens} tokens)...", flush=True)
            
            # Flush remaining batch
            if batch:
                cur.executemany(
                    "INSERT INTO postings (term, doc_id, positions) VALUES (?, ?, ?)",
                    batch
                )
                batch = []
            conn.commit()
        
        print(f"  Total documents processed: {total_docs}", flush=True)
        print(f"  Total tokens: {total_tokens}", flush=True)
        
        # Phase 2: Build lexicon and postings file
        print("\nPhase 2: Building lexicon and postings file...", flush=True)
        print("  Sorting postings and streaming to disk...", flush=True)
        
        # Create index now to sort efficiently
        cur.execute("CREATE INDEX idx_term ON postings(term, doc_id)")
        
        cur.execute("SELECT term, doc_id, positions FROM postings ORDER BY term, doc_id")
        
        lexicon = {}
        vocab_size = 0
        current_term = None
        current_postings = {}
        current_cf = 0
        
        with open(postings_file, 'wb') as pf:
            def flush_term(t, post_rec, cf_val):
                record_bytes = json.dumps(post_rec, ensure_ascii=False).encode('utf-8')
                offset = pf.tell()
                length = len(record_bytes)
                pf.write(record_bytes)
                lexicon[t] = {
                    'cf': cf_val,
                    'df': len(post_rec),
                    'offset': offset,
                    'length': length
                }
            
            for row in cur:
                term, doc_id, positions_json = row
                positions = json.loads(positions_json)
                
                if term != current_term:
                    if current_term is not None:
                        flush_term(current_term, current_postings, current_cf)
                        vocab_size += 1
                        if vocab_size % 10000 == 0:
                            print(f"  Written {vocab_size} terms to postings file...", flush=True)
                    current_term = term
                    current_postings = {}
                    current_cf = 0
                
                current_postings[doc_id] = positions
                current_cf += len(positions)
            
            if current_term is not None:
                flush_term(current_term, current_postings, current_cf)
                vocab_size += 1
        
        print(f"  Postings file created: {postings_file}")
        
        # Save lexicon
        with open(lexicon_file, 'w', encoding='utf-8') as lf:
            json.dump(lexicon, lf, ensure_ascii=False, indent=2)
        print(f"  Lexicon saved: {lexicon_file}")
        
        # Calculate average document length
        avg_doc_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 0
        
        # Save metadata
        postings_size = os.path.getsize(postings_file)
        metadata = {
            'total_documents': total_docs,
            'vocabulary_size': vocab_size,
            'total_tokens': total_tokens,
            'avg_document_length': round(avg_doc_length, 2),
            'postings_file_size': postings_size
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as mf:
            json.dump(metadata, mf, indent=2)
        print(f"  Metadata saved: {metadata_file}")
        
        print("\nIndex build complete!")
        print(f"  Documents: {total_docs}")
        print(f"  Vocabulary: {vocab_size}")
        print(f"  Total tokens: {total_tokens}")
        print(f"  Avg document length: {avg_doc_length:.2f}")
        print(f"  Postings file size: {postings_size / (1024*1024):.2f} MB")
        
        return metadata
    
    finally:
        # Clean up temp database
        conn.close()
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


def load_lexicon(lexicon_file=None):
    """
    Load the vocabulary (lexicon) into RAM.
    
    Returns:
        dict: The lexicon with term -> {cf, df, offset, length}
    """
    if lexicon_file is None:
        lexicon_file = LEXICON_FILE
    
    if not os.path.exists(lexicon_file):
        print(f"Error: Lexicon file not found: {lexicon_file}")
        return None
    
    with open(lexicon_file, 'r', encoding='utf-8') as f:
        lexicon = json.load(f)
    
    return lexicon


def retrieve_postings(term, lexicon, postings_file=None):
    """
    Retrieve positional postings for a term from secondary storage.
    
    Only reads the specific portion of the postings file for this term.
    Does NOT load the entire postings file into RAM.
    
    Args:
        term: The search term
        lexicon: The in-memory lexicon dictionary
        postings_file: Path to postings file (optional)
    
    Returns:
        dict: {doc_id: [positions]} or None if term not found
    """
    if postings_file is None:
        postings_file = POSTINGS_FILE
    
    if term not in lexicon:
        return None
    
    entry = lexicon[term]
    offset = entry['offset']
    length = entry['length']
    
    with open(postings_file, 'rb') as f:
        f.seek(offset)
        record_bytes = f.read(length)
    
    postings = json.loads(record_bytes.decode('utf-8'))
    return postings


def load_metadata(metadata_file=None):
    """Load index metadata."""
    if metadata_file is None:
        metadata_file = METADATA_FILE
    
    if not os.path.exists(metadata_file):
        return None
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_documents(documents_file=None):
    """
    Load the document catalog.
    
    Returns:
        dict: {doc_id: {title, text}}
    """
    if documents_file is None:
        documents_file = DOCUMENTS_FILE
    
    if not os.path.exists(documents_file):
        return {}
    
    docs = {}
    with open(documents_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                record = json.loads(line)
                docs[str(record['id'])] = record
    return docs


def validate_index(index_dir=None):
    """
    Validate the generated index for correctness.
    
    Checks:
    1. Every vocab term has valid CF and DF
    2. Every postings offset is valid
    3. Every postings record can be read
    4. CF matches total number of stored positions
    5. DF matches number of documents in postings
    6. Positions are positive, sorted, and unique
    7. Document IDs exist in document catalog
    8. Metadata matches actual files
    
    Returns:
        (bool, str): (passed, report_text)
    """
    if index_dir:
        lexicon_file = os.path.join(index_dir, "lexicon.json")
        postings_file = os.path.join(index_dir, "postings.dat")
        documents_file = os.path.join(index_dir, "documents.jsonl")
        metadata_file = os.path.join(index_dir, "metadata.json")
    else:
        lexicon_file = LEXICON_FILE
        postings_file = POSTINGS_FILE
        documents_file = DOCUMENTS_FILE
        metadata_file = METADATA_FILE
    
    report_lines = []
    report_lines.append("Index Validation")
    report_lines.append("=" * 40)
    
    errors = []
    
    # Load lexicon
    lexicon = load_lexicon(lexicon_file)
    if lexicon is None:
        return False, "Lexicon file not found."
    
    # Load document catalog
    docs = load_documents(documents_file)
    if not docs:
        errors.append("Document catalog is empty or not found.")
    
    doc_ids_in_catalog = set(docs.keys())
    
    vocab_count = len(lexicon)
    report_lines.append(f"Vocabulary entries: {vocab_count}")
    report_lines.append(f"Documents: {len(doc_ids_in_catalog)}")
    
    # Validate each term by keeping postings file open for speed
    checked = 0
    with open(postings_file, 'rb') as pf:
        for term, entry in lexicon.items():
            cf = entry.get('cf', 0)
            df = entry.get('df', 0)
            offset = entry.get('offset', -1)
            length = entry.get('length', 0)
            
            # Check CF and DF are positive
            if cf <= 0:
                errors.append(f"Term '{term}': CF is not positive ({cf})")
            if df <= 0:
                errors.append(f"Term '{term}': DF is not positive ({df})")
            
            # Check offset is valid
            if offset < 0:
                errors.append(f"Term '{term}': Invalid offset ({offset})")
                continue
            
            # Read postings from disk using open handle
            try:
                pf.seek(offset)
                record_bytes = pf.read(length)
                postings = json.loads(record_bytes.decode('utf-8'))
            except Exception as e:
                errors.append(f"Term '{term}': Cannot read postings: {e}")
                continue
            
            if postings is None:
                errors.append(f"Term '{term}': Postings record is None")
                continue
            
            # Check DF matches
            actual_df = len(postings)
            if actual_df != df:
                errors.append(f"Term '{term}': DF mismatch (lexicon={df}, actual={actual_df})")
            
            # Check CF and positions
            actual_cf = 0
            for doc_id, positions in postings.items():
                actual_cf += len(positions)
                
                # Check positions are positive integers
                for pos in positions:
                    if not isinstance(pos, int) or pos <= 0:
                        errors.append(f"Term '{term}' in doc {doc_id}: Invalid position {pos}")
                
                # Check positions are sorted and unique
                if positions != sorted(set(positions)):
                    errors.append(f"Term '{term}' in doc {doc_id}: Positions not sorted/unique")
                
                # Check doc_id exists in catalog
                if doc_ids_in_catalog and doc_id not in doc_ids_in_catalog:
                    errors.append(f"Term '{term}': Doc ID {doc_id} not in catalog")
            
            if actual_cf != cf:
                errors.append(f"Term '{term}': CF mismatch (lexicon={cf}, actual={actual_cf})")
            
            checked += 1
            if checked % 50000 == 0:
                print(f"  Validated {checked}/{vocab_count} terms...", flush=True)
    
    report_lines.append(f"Postings records checked: {checked}")
    report_lines.append("")
    
    # Check metadata
    metadata = load_metadata(metadata_file)
    if metadata:
        if metadata.get('vocabulary_size') != vocab_count:
            errors.append(f"Metadata vocab size mismatch: {metadata.get('vocabulary_size')} vs {vocab_count}")
        if metadata.get('total_documents') != len(doc_ids_in_catalog):
            errors.append(f"Metadata doc count mismatch: {metadata.get('total_documents')} vs {len(doc_ids_in_catalog)}")
    
    if errors:
        report_lines.append("ERRORS FOUND:")
        for err in errors[:20]:  # Show first 20 errors
            report_lines.append(f"  - {err}")
        if len(errors) > 20:
            report_lines.append(f"  ... and {len(errors) - 20} more errors")
        report_lines.append("")
        report_lines.append("Result: FAIL")
        return False, '\n'.join(report_lines)
    else:
        report_lines.append("Result: PASS")
        return True, '\n'.join(report_lines)

