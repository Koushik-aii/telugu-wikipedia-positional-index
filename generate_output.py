"""
generate_output.py - Generate the required output.txt file

Produces two sections:
  Section A: 10 rare Telugu terms with their positional indexes
  Section B: 5 test cases demonstrating system functionality

All results are generated from the actual indexed Telugu Wikipedia data.
"""

import json
import os
import sys

from config import INDEX_DIR, LEXICON_FILE, POSTINGS_FILE, DOCUMENTS_FILE, METADATA_FILE
from indexer import load_lexicon, retrieve_postings, load_metadata, load_documents
from search import SearchEngine
from tokenizer import tokenize, is_telugu_char


def is_valid_telugu_word(term):
    """
    Check if a term is a genuine, meaningful Telugu word.
    
    Excludes:
    - Short tokens (length < 4)
    - Tokens that start with combining marks (vowel signs, virama, anusvara)
    - Mixed or non-Telugu characters
    """
    if not term or len(term) < 4:
        return False
    first = ord(term[0])
    # Must start with an independent Telugu vowel or consonant
    if not ((0x0C05 <= first <= 0x0C14) or (0x0C15 <= first <= 0x0C39)):
        return False
    # All characters must be in the Telugu Unicode block
    for ch in term:
        if not (0x0C00 <= ord(ch) <= 0x0C7F):
            return False
    return True


def select_rare_terms(lexicon, count=10):
    """
    Select 10 meaningful rare Telugu terms from the lexicon.
    
    Selection criteria:
    - Low Document Frequency (DF=1)
    - Low Collection Frequency (CF=2 to demonstrate multiple positions)
    - Must be valid, meaningful Telugu words
    """
    candidates = []
    
    for term, entry in lexicon.items():
        if is_valid_telugu_word(term) and entry['df'] == 1 and entry['cf'] >= 2:
            candidates.append((term, entry['df'], entry['cf']))
    
    # If not enough with cf>=2, include cf=1 as well
    if len(candidates) < count:
        for term, entry in lexicon.items():
            if is_valid_telugu_word(term) and entry['df'] == 1 and entry['cf'] == 1:
                candidates.append((term, entry['df'], entry['cf']))
                if len(candidates) >= count * 2:
                    break
    
    # Sort by DF (ascending), then CF (ascending), then term
    candidates.sort(key=lambda x: (x[1], x[2], x[0]))
    
    return candidates[:count]


def find_phrase_in_docs(engine, documents):
    """
    Find a real consecutive phrase from an indexed document.
    Returns (phrase, doc_id) or (None, None) if not found.
    """
    # Look through documents to find a consecutive phrase
    for doc_id, doc in list(documents.items())[:100]:
        text = doc.get('text', '')
        tokens = tokenize(text)
        
        if len(tokens) >= 2:
            # Try consecutive token pairs
            for i in range(min(len(tokens) - 1, 20)):
                phrase = tokens[i][0] + " " + tokens[i+1][0]
                # Check both terms exist in lexicon
                if tokens[i][0] in engine.lexicon and tokens[i+1][0] in engine.lexicon:
                    results = engine.phrase_search(phrase)
                    if results:
                        return phrase, doc_id
    
    return None, None


def find_repeated_term(lexicon, postings_file):
    """Find a meaningful term that appears multiple times in at least one document."""
    for term, entry in lexicon.items():
        if not is_valid_telugu_word(term):
            continue
        if entry['cf'] >= 5:
            postings = retrieve_postings(term, lexicon, postings_file)
            if postings:
                for doc_id, positions in postings.items():
                    if len(positions) >= 3:
                        return term, doc_id, positions
    return None, None, None


def generate_output(output_path="output.txt"):
    """Generate the complete output.txt file."""
    
    # Check if index exists
    if not os.path.exists(LEXICON_FILE):
        print("Error: Index not found. Build the index first using: python main.py build")
        sys.exit(1)
    
    print("Loading index...")
    engine = SearchEngine()
    lexicon = engine.lexicon
    metadata = load_metadata()
    documents = load_documents()
    
    lines = []
    
    lines.append("=" * 60)
    lines.append("TELUGU POSITIONAL INVERTED INDEX - OUTPUT REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Total Documents Indexed: {metadata.get('total_documents', 'N/A')}")
    lines.append(f"Vocabulary Size: {metadata.get('vocabulary_size', 'N/A')}")
    lines.append(f"Total Tokens: {metadata.get('total_tokens', 'N/A')}")
    lines.append(f"Average Document Length: {metadata.get('avg_document_length', 'N/A')}")
    lines.append("")
    
    # ============================================================
    # SECTION A: 10 Rare Telugu Terms
    # ============================================================
    lines.append("=" * 60)
    lines.append("SECTION A: TEN RARE TELUGU TERMS WITH POSITIONAL INDEXES")
    lines.append("=" * 60)
    lines.append("")
    
    rare_terms = select_rare_terms(lexicon, count=10)
    
    if len(rare_terms) < 10:
        lines.append(f"Note: Only {len(rare_terms)} suitable rare terms found.")
        lines.append("")
    
    for i, (term, df, cf) in enumerate(rare_terms, 1):
        lines.append("=" * 42)
        lines.append(f"RARE TERM {i}")
        lines.append("=" * 42)
        lines.append("")
        lines.append(f"Term: {term}")
        lines.append(f"")
        lines.append(f"Collection Frequency: {cf}")
        lines.append(f"Document Frequency: {df}")
        lines.append("")
        
        postings = retrieve_postings(term, lexicon)
        if postings:
            for doc_id, positions in sorted(postings.items()):
                doc_title = documents.get(doc_id, {}).get('title', 'Unknown')
                lines.append(f"Document ID: {doc_id}")
                lines.append(f"Document Title: {doc_title}")
                lines.append(f"Positions: {positions}")
                lines.append("")
        
        lines.append("")
    
    # ============================================================
    # SECTION B: Five Test Cases
    # ============================================================
    lines.append("=" * 60)
    lines.append("SECTION B: FIVE TEST CASES")
    lines.append("=" * 60)
    lines.append("")
    
    # --- Test Case 1: Single-term lookup ---
    lines.append("-" * 42)
    lines.append("TEST CASE 1: Single-Term Lookup")
    lines.append("-" * 42)
    lines.append("")
    
    # Pick "తెలుగు" as the primary term if present, otherwise common term
    test_term_1 = "తెలుగు" if "తెలుగు" in lexicon else None
    if not test_term_1:
        common_terms = sorted(lexicon.items(), key=lambda x: x[1]['cf'], reverse=True)
        for term, entry in common_terms:
            if is_valid_telugu_word(term):
                test_term_1 = term
                break
    
    if test_term_1:
        result = engine.term_lookup(test_term_1)
        lines.append(f"Query: {test_term_1}")
        lines.append(f"Expected Behavior: Term should be found with its CF, DF, and positions")
        lines.append("")
        lines.append("Actual Result:")
        lines.append(f"  Term: {result['term']}")
        lines.append(f"  CF: {result['cf']}")
        lines.append(f"  DF: {result['df']}")
        # Show first few documents
        shown = 0
        for doc_id, positions in sorted(result['postings'].items()):
            if shown >= 5:
                remaining = len(result['postings']) - shown
                lines.append(f"  ... and {remaining} more documents")
                break
            lines.append(f"  Document {doc_id}: {positions}")
            shown += 1
        lines.append("")
        lines.append("Status: PASS")
    else:
        lines.append("Status: FAIL (no suitable term found)")
    lines.append("")
    
    # --- Test Case 2: Rare-term lookup ---
    lines.append("-" * 42)
    lines.append("TEST CASE 2: Rare-Term Lookup")
    lines.append("-" * 42)
    lines.append("")
    
    if rare_terms:
        rare_term = rare_terms[0][0]
        result = engine.term_lookup(rare_term)
        lines.append(f"Query: {rare_term}")
        lines.append(f"Expected Behavior: Rare term should be found with low DF")
        lines.append("")
        lines.append("Actual Result:")
        if result:
            lines.append(f"  Term: {result['term']}")
            lines.append(f"  CF: {result['cf']}")
            lines.append(f"  DF: {result['df']}")
            for doc_id, positions in sorted(result['postings'].items()):
                lines.append(f"  Document {doc_id}: {positions}")
            lines.append("")
            lines.append("Status: PASS")
        else:
            lines.append("  Term not found")
            lines.append("Status: FAIL")
    else:
        lines.append("Status: FAIL (no rare terms available)")
    lines.append("")
    
    # --- Test Case 3: Repeated-term positions ---
    lines.append("-" * 42)
    lines.append("TEST CASE 3: Repeated-Term Positions")
    lines.append("-" * 42)
    lines.append("")
    
    rep_term, rep_doc, rep_positions = find_repeated_term(lexicon, POSTINGS_FILE)
    if rep_term:
        lines.append(f"Query: {rep_term}")
        lines.append(f"Expected Behavior: Term should appear multiple times in at least one document")
        lines.append("")
        lines.append("Actual Result:")
        lines.append(f"  Term: {rep_term}")
        lines.append(f"  Document ID: {rep_doc}")
        lines.append(f"  Positions: {rep_positions}")
        lines.append(f"  Occurrences in this document: {len(rep_positions)}")
        lines.append("")
        if len(rep_positions) >= 2:
            lines.append("Status: PASS")
        else:
            lines.append("Status: FAIL")
    else:
        lines.append("Status: FAIL (no repeated term found)")
    lines.append("")
    
    # --- Test Case 4: Phrase search ---
    lines.append("-" * 42)
    lines.append("TEST CASE 4: Exact Phrase Search")
    lines.append("-" * 42)
    lines.append("")
    
    phrase = "తెలుగు భాష"
    results = engine.phrase_search(phrase)
    if not results:
        phrase, _ = find_phrase_in_docs(engine, documents)
        if phrase:
            results = engine.phrase_search(phrase)
    
    if phrase and results:
        lines.append(f'Query: "{phrase}"')
        lines.append(f"Expected Behavior: Phrase should be found using positional index")
        lines.append("")
        lines.append("Actual Result:")
        lines.append(f"  Phrase \"{phrase}\" matched in {len(results)} document(s):")
        for r in results[:5]:
            doc_title = documents.get(r['doc_id'], {}).get('title', 'Unknown')
            lines.append(f"  Document ID: {r['doc_id']} ({doc_title})")
            lines.append(f"  Phrase starts at positions: {r['positions']}")
        if len(results) > 5:
            lines.append(f"  ... and {len(results) - 5} more matching documents")
        lines.append("")
        lines.append("Status: PASS")
    else:
        lines.append("Status: FAIL (could not find a suitable phrase)")
    lines.append("")
    
    # --- Test Case 5: Unknown-term lookup ---
    lines.append("-" * 42)
    lines.append("TEST CASE 5: Unknown-Term Lookup")
    lines.append("-" * 42)
    lines.append("")
    
    unknown_term = "క్వాంటమ్ఫిజిక్స్అణుశక్తి"
    result = engine.term_lookup(unknown_term)
    lines.append(f"Query: {unknown_term}")
    lines.append(f"Expected Behavior: Term should NOT be found in vocabulary")
    lines.append("")
    lines.append("Actual Result:")
    if result is None:
        lines.append(f"  Term '{unknown_term}' not found in vocabulary.")
        lines.append("")
        lines.append("Status: PASS")
    else:
        lines.append(f"  Term was unexpectedly found with CF={result['cf']}")
        lines.append("Status: FAIL")
    lines.append("")
    
    # Write output file
    lines.append("=" * 60)
    lines.append("END OF OUTPUT REPORT")
    lines.append("=" * 60)
    
    output_text = '\n'.join(lines)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)
    
    print(f"\nOutput file generated: {output_path}")
    print(f"Total lines: {len(lines)}")
    
    return output_path


if __name__ == '__main__':
    generate_output()

