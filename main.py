"""
main.py - Command-Line Interface for Telugu Positional Inverted Index

Usage:
    python main.py build [--limit N]     Build the index from Telugu Wikipedia dump
    python main.py term <term>           Look up a single term
    python main.py phrase <phrase>       Search for an exact phrase
    python main.py stats                 Display index statistics
    python main.py validate              Validate the index
"""

import argparse
import sys
import os

from config import DEFAULT_ARTICLE_LIMIT, ensure_dirs


def cmd_build(args):
    """Build the positional inverted index."""
    from dataset import find_dump_file, download_dump, extract_articles
    from indexer import build_index
    
    ensure_dirs()
    
    # Find or download the dump file
    dump_path = find_dump_file()
    
    if dump_path is None:
        print("Telugu Wikipedia dump not found in data/raw/")
        print("Attempting to download...")
        dump_path = download_dump()
    
    if dump_path is None:
        print("\nError: Could not find or download the Telugu Wikipedia dump.")
        print("Please download manually from: https://dumps.wikimedia.org/tewiki/")
        print("Place the .xml.bz2 file in the data/raw/ directory.")
        sys.exit(1)
    
    print(f"\nUsing dump file: {dump_path}")
    print(f"Article limit: {args.limit}")
    print()
    
    # Extract articles and build index
    articles = extract_articles(dump_path, limit=args.limit)
    stats = build_index(articles)
    
    if stats:
        print("\nIndex built successfully!")
    else:
        print("\nError building index.")
        sys.exit(1)


def cmd_term(args):
    """Look up a single term."""
    from search import SearchEngine
    
    engine = SearchEngine()
    engine.display_term_result(args.term)


def cmd_phrase(args):
    """Search for a phrase."""
    from search import SearchEngine
    
    engine = SearchEngine()
    engine.display_phrase_result(args.phrase)


def cmd_stats(args):
    """Display index statistics."""
    from search import SearchEngine
    
    engine = SearchEngine()
    engine.display_statistics()


def cmd_validate(args):
    """Validate the index."""
    from indexer import validate_index
    
    passed, report = validate_index()
    print(report)
    
    if not passed:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Telugu Positional Inverted Index - Information Retrieval Assignment"
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Build command
    build_parser = subparsers.add_parser('build', help='Build the index from Telugu Wikipedia dump')
    build_parser.add_argument(
        '--limit', type=int, default=DEFAULT_ARTICLE_LIMIT,
        help=f'Maximum number of articles to process (default: {DEFAULT_ARTICLE_LIMIT})'
    )
    build_parser.set_defaults(func=cmd_build)
    
    # Term lookup command
    term_parser = subparsers.add_parser('term', help='Look up a single term')
    term_parser.add_argument('term', type=str, help='Telugu term to search for')
    term_parser.set_defaults(func=cmd_term)
    
    # Phrase search command
    phrase_parser = subparsers.add_parser('phrase', help='Search for an exact phrase')
    phrase_parser.add_argument('phrase', type=str, help='Phrase to search for (in quotes)')
    phrase_parser.set_defaults(func=cmd_phrase)
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Display index statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate the index')
    validate_parser.set_defaults(func=cmd_validate)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()

