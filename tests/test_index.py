"""
test_index.py - Automated Tests for Telugu Positional Inverted Index

Uses a small synthetic Telugu dataset for predictable unit tests.
Does not depend on the full Wikipedia dataset.
"""

import unittest
import json
import os
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tokenizer import tokenize, normalize_text, get_positions_dict, is_telugu_char
from indexer import build_index, load_lexicon, retrieve_postings, validate_index
from search import SearchEngine


class TestTokenizer(unittest.TestCase):
    """Test Unicode normalization and Telugu tokenization."""
    
    def test_unicode_normalization(self):
        """Test that Unicode NFC normalization works."""
        text = "తెలుగు"
        normalized = normalize_text(text)
        self.assertEqual(normalized, text)
        # Empty string
        self.assertEqual(normalize_text(""), "")
        self.assertEqual(normalize_text(None), "")
    
    def test_telugu_char_detection(self):
        """Test Telugu character detection."""
        self.assertTrue(is_telugu_char('త'))
        self.assertTrue(is_telugu_char('ె'))
        self.assertTrue(is_telugu_char('ల'))
        self.assertFalse(is_telugu_char('a'))
        self.assertFalse(is_telugu_char('1'))
    
    def test_basic_telugu_tokenization(self):
        """Test tokenization of basic Telugu text."""
        text = "తెలుగు భాష భారతదేశంలో మాట్లాడే భాష"
        tokens = tokenize(text)
        
        token_strings = [t[0] for t in tokens]
        self.assertEqual(token_strings, ['తెలుగు', 'భాష', 'భారతదేశంలో', 'మాట్లాడే', 'భాష'])
    
    def test_one_based_positions(self):
        """Test that positions are one-based."""
        text = "తెలుగు భాష భారతదేశంలో మాట్లాడే భాష"
        tokens = tokenize(text)
        
        expected = [
            ('తెలుగు', 1),
            ('భాష', 2),
            ('భారతదేశంలో', 3),
            ('మాట్లాడే', 4),
            ('భాష', 5),
        ]
        self.assertEqual(tokens, expected)
    
    def test_english_lowercase(self):
        """Test that English text is lowercased."""
        text = "Telugu LANGUAGE"
        tokens = tokenize(text)
        token_strings = [t[0] for t in tokens]
        self.assertEqual(token_strings, ['telugu', 'language'])
    
    def test_empty_input(self):
        """Test handling of empty strings."""
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize(None), [])
    
    def test_mixed_text(self):
        """Test tokenization of mixed Telugu and English text."""
        text = "తెలుగు wikipedia"
        tokens = tokenize(text)
        self.assertEqual(len(tokens), 2)
        self.assertEqual(tokens[0][0], 'తెలుగు')
        self.assertEqual(tokens[1][0], 'wikipedia')
    
    def test_positions_dict(self):
        """Test get_positions_dict function."""
        text = "తెలుగు భాష తెలుగు"
        positions = get_positions_dict(text)
        self.assertEqual(positions['తెలుగు'], [1, 3])
        self.assertEqual(positions['భాష'], [2])


class TestIndexBuilder(unittest.TestCase):
    """Test positional index construction with synthetic data."""
    
    @classmethod
    def setUpClass(cls):
        """Create a temporary directory and build index from synthetic data."""
        cls.temp_dir = tempfile.mkdtemp(prefix="telugu_test_")
        cls.index_dir = os.path.join(cls.temp_dir, "index")
        os.makedirs(cls.index_dir, exist_ok=True)
        
        # Synthetic Telugu test documents
        cls.test_docs = [
            {
                'id': '101',
                'title': 'Test Document 1',
                'text': 'తెలుగు భాష భారతదేశంలో తెలుగు'
            },
            {
                'id': '102',
                'title': 'Test Document 2',
                'text': 'తెలుగు సాహిత్యం ప్రసిద్ధి'
            },
            {
                'id': '103',
                'title': 'Test Document 3',
                'text': 'భారతదేశంలో తెలుగు సాహిత్యం'
            }
        ]
        
        # Build the index
        cls.stats = build_index(iter(cls.test_docs), index_dir=cls.index_dir)
        
        # Load lexicon
        cls.lexicon = load_lexicon(os.path.join(cls.index_dir, "lexicon.json"))
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temporary directory."""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_collection_frequency(self):
        """Test that CF is calculated correctly."""
        # తెలుగు appears: doc101 x2, doc102 x1, doc103 x1 = CF 4
        self.assertEqual(self.lexicon['తెలుగు']['cf'], 4)
        # భాష appears: doc101 x1 = CF 1
        self.assertEqual(self.lexicon['భాష']['cf'], 1)
        # సాహిత్యం appears: doc102 x1, doc103 x1 = CF 2
        self.assertEqual(self.lexicon['సాహిత్యం']['cf'], 2)
    
    def test_document_frequency(self):
        """Test that DF is calculated correctly."""
        # తెలుగు appears in docs 101, 102, 103 = DF 3
        self.assertEqual(self.lexicon['తెలుగు']['df'], 3)
        # భాష appears only in doc 101 = DF 1
        self.assertEqual(self.lexicon['భాష']['df'], 1)
        # భారతదేశంలో appears in docs 101, 103 = DF 2
        self.assertEqual(self.lexicon['భారతదేశంలో']['df'], 2)
    
    def test_postings_retrieval(self):
        """Test that postings can be retrieved from disk correctly."""
        postings_file = os.path.join(self.index_dir, "postings.dat")
        
        # Retrieve postings for తెలుగు
        postings = retrieve_postings('తెలుగు', self.lexicon, postings_file)
        self.assertIsNotNone(postings)
        
        # Check doc 101: positions should be [1, 4]
        self.assertIn('101', postings)
        self.assertEqual(postings['101'], [1, 4])
        
        # Check doc 102: position should be [1]
        self.assertIn('102', postings)
        self.assertEqual(postings['102'], [1])
        
        # Check doc 103: position should be [2]
        self.assertIn('103', postings)
        self.assertEqual(postings['103'], [2])
    
    def test_unknown_term(self):
        """Test handling of unknown terms."""
        postings_file = os.path.join(self.index_dir, "postings.dat")
        postings = retrieve_postings('అజ్ఞాత', self.lexicon, postings_file)
        self.assertIsNone(postings)
    
    def test_index_validation(self):
        """Test that index validation passes."""
        passed, report = validate_index(self.index_dir)
        self.assertTrue(passed, f"Validation failed:\n{report}")
    
    def test_index_reload(self):
        """Test that index can be loaded after closing and reopening."""
        # Load lexicon fresh from disk
        lexicon2 = load_lexicon(os.path.join(self.index_dir, "lexicon.json"))
        self.assertIsNotNone(lexicon2)
        self.assertEqual(len(lexicon2), len(self.lexicon))
        
        # Verify a term
        self.assertEqual(lexicon2['తెలుగు']['cf'], self.lexicon['తెలుగు']['cf'])
        self.assertEqual(lexicon2['తెలుగు']['df'], self.lexicon['తెలుగు']['df'])
        
        # Verify postings retrieval with reloaded lexicon
        postings_file = os.path.join(self.index_dir, "postings.dat")
        postings = retrieve_postings('భాష', lexicon2, postings_file)
        self.assertIsNotNone(postings)
        self.assertIn('101', postings)


class TestPhraseSearch(unittest.TestCase):
    """Test phrase searching using positional information."""
    
    @classmethod
    def setUpClass(cls):
        """Create index for phrase search testing."""
        cls.temp_dir = tempfile.mkdtemp(prefix="telugu_phrase_test_")
        cls.index_dir = os.path.join(cls.temp_dir, "index")
        os.makedirs(cls.index_dir, exist_ok=True)
        
        cls.test_docs = [
            {
                'id': '201',
                'title': 'Phrase Test 1',
                'text': 'తెలుగు భాష భారతదేశంలో తెలుగు భాష'
            },
            {
                'id': '202',
                'title': 'Phrase Test 2',
                'text': 'సాహిత్యం తెలుగు భారతదేశంలో'
            },
        ]
        
        build_index(iter(cls.test_docs), index_dir=cls.index_dir)
        cls.engine = SearchEngine(index_dir=cls.index_dir)
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def test_phrase_found(self):
        """Test that a consecutive phrase is found."""
        # "తెలుగు భాష" should be found in doc 201 at positions 1 and 4
        results = self.engine.phrase_search("తెలుగు భాష")
        self.assertTrue(len(results) > 0)
        
        doc_ids = [r['doc_id'] for r in results]
        self.assertIn('201', doc_ids)
        
        # Check starting positions
        for r in results:
            if r['doc_id'] == '201':
                self.assertIn(1, r['positions'])
                self.assertIn(4, r['positions'])
    
    def test_phrase_not_found(self):
        """Test that a non-consecutive phrase is not found."""
        # "భాష సాహిత్యం" is not consecutive in any document
        results = self.engine.phrase_search("భాష సాహిత్యం")
        self.assertEqual(len(results), 0)
    
    def test_single_term_phrase(self):
        """Test phrase search with a single term."""
        results = self.engine.phrase_search("తెలుగు")
        self.assertTrue(len(results) > 0)
    
    def test_unknown_phrase(self):
        """Test phrase search with unknown term."""
        results = self.engine.phrase_search("అజ్ఞాతపదం మరొకటి")
        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()
