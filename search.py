"""
search.py - Search Interface for Positional Inverted Index

Supports:
- Single-term lookup
- Phrase search using positional information
- Index statistics display
"""

import json
import os
import sys

from config import LEXICON_FILE, POSTINGS_FILE, METADATA_FILE, DOCUMENTS_FILE
from indexer import load_lexicon, retrieve_postings, load_metadata, load_documents


class SearchEngine:
    """Simple search engine using the positional inverted index."""
    
    def __init__(self, index_dir=None):
        """
        Initialize the search engine by loading the lexicon into RAM.
        Postings remain on disk and are loaded on demand.
        """
        if index_dir:
            self.lexicon_file = os.path.join(index_dir, "lexicon.json")
            self.postings_file = os.path.join(index_dir, "postings.dat")
            self.metadata_file = os.path.join(index_dir, "metadata.json")
            self.documents_file = os.path.join(index_dir, "documents.jsonl")
        else:
            self.lexicon_file = LEXICON_FILE
            self.postings_file = POSTINGS_FILE
            self.metadata_file = METADATA_FILE
            self.documents_file = DOCUMENTS_FILE
        
        # Load vocabulary into RAM
        self.lexicon = load_lexicon(self.lexicon_file)
        if self.lexicon is None:
            raise FileNotFoundError("Index not found. Build the index first using: python main.py build")
        
        print(f"Loaded vocabulary with {len(self.lexicon)} terms.")
    
    def term_lookup(self, term):
        """
        Look up a single term in the index.
        
        Returns:
            dict with 'term', 'cf', 'df', 'postings' or None if not found
        """
        if term not in self.lexicon:
            return None
        
        entry = self.lexicon[term]
        postings = retrieve_postings(term, self.lexicon, self.postings_file)
        
        return {
            'term': term,
            'cf': entry['cf'],
            'df': entry['df'],
            'postings': postings
        }
    
    def phrase_search(self, phrase):
        """
        Search for an exact phrase using positional information.
        
        The phrase terms must appear consecutively in the correct order.
        Uses positional index to verify adjacency.
        
        Args:
            phrase: String containing the phrase to search for
        
        Returns:
            list of dicts: [{doc_id, positions}] where positions are
            the starting positions of the phrase in each document
        """
        from tokenizer import tokenize
        
        # Tokenize the phrase
        tokens = tokenize(phrase)
        if not tokens:
            return []
        
        terms = [t[0] for t in tokens]
        
        if len(terms) == 1:
            # Single term - just do a regular lookup
            result = self.term_lookup(terms[0])
            if result is None:
                return []
            return [
                {'doc_id': doc_id, 'positions': positions}
                for doc_id, positions in result['postings'].items()
            ]
        
        # Check all terms exist
        for term in terms:
            if term not in self.lexicon:
                return []
        
        # Get postings for all terms
        all_postings = []
        for term in terms:
            postings = retrieve_postings(term, self.lexicon, self.postings_file)
            all_postings.append(postings)
        
        # Find documents containing all terms
        common_docs = set(all_postings[0].keys())
        for postings in all_postings[1:]:
            common_docs &= set(postings.keys())
        
        if not common_docs:
            return []
        
        # Check positional adjacency in each common document
        results = []
        for doc_id in sorted(common_docs):
            # Get positions of first term
            first_positions = all_postings[0][doc_id]
            
            # For each position of the first term, check if subsequent
            # terms appear at consecutive positions
            matching_positions = []
            
            for start_pos in first_positions:
                match = True
                for i in range(1, len(terms)):
                    expected_pos = start_pos + i
                    if expected_pos not in all_postings[i][doc_id]:
                        match = False
                        break
                
                if match:
                    matching_positions.append(start_pos)
            
            if matching_positions:
                results.append({
                    'doc_id': doc_id,
                    'positions': matching_positions
                })
        
        return results
    
    def get_statistics(self):
        """
        Get index statistics.
        
        Returns:
            dict with statistics
        """
        metadata = load_metadata(self.metadata_file)
        if metadata is None:
            # Calculate from lexicon
            total_cf = sum(entry['cf'] for entry in self.lexicon.values())
            metadata = {
                'total_documents': 0,
                'vocabulary_size': len(self.lexicon),
                'total_tokens': total_cf,
                'avg_document_length': 0,
                'postings_file_size': 0
            }
        
        if os.path.exists(self.postings_file):
            metadata['postings_file_size'] = os.path.getsize(self.postings_file)
        
        return metadata
    
    def display_term_result(self, term):
        """Display results for a single term lookup."""
        result = self.term_lookup(term)
        
        if result is None:
            print(f"\nTerm '{term}' not found in vocabulary.")
            return
        
        print(f"\nTerm: {result['term']}")
        print(f"Collection Frequency (CF): {result['cf']}")
        print(f"Document Frequency (DF): {result['df']}")
        print()
        
        for doc_id, positions in sorted(result['postings'].items()):
            print(f"  Document ID: {doc_id}")
            print(f"  Positions: {positions}")
            print()
    
    def display_phrase_result(self, phrase):
        """Display results for a phrase search."""
        results = self.phrase_search(phrase)
        
        if not results:
            print(f"\nPhrase '{phrase}' not found in any document.")
            return
        
        print(f"\nPhrase: \"{phrase}\"")
        print(f"Found in {len(results)} document(s):")
        print()
        
        for result in results:
            print(f"  Document ID: {result['doc_id']}")
            print(f"  Phrase starts at positions: {result['positions']}")
            print()
    
    def display_statistics(self):
        """Display index statistics."""
        stats = self.get_statistics()
        
        print("\nIndex Statistics")
        print("=" * 40)
        print(f"Total indexed documents: {stats.get('total_documents', 'N/A')}")
        print(f"Vocabulary size: {stats.get('vocabulary_size', 'N/A')}")
        print(f"Total indexed tokens: {stats.get('total_tokens', 'N/A')}")
        print(f"Average document length: {stats.get('avg_document_length', 'N/A')}")
        
        size_bytes = stats.get('postings_file_size', 0)
        if size_bytes > 1024 * 1024:
            print(f"Postings file size: {size_bytes / (1024*1024):.2f} MB")
        elif size_bytes > 1024:
            print(f"Postings file size: {size_bytes / 1024:.2f} KB")
        else:
            print(f"Postings file size: {size_bytes} bytes")

