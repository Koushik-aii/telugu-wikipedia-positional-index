"""
dataset.py - Telugu Wikipedia Dataset Extraction

Handles downloading, parsing, and cleaning Telugu Wikipedia XML dumps.
Uses streaming XML parsing for memory efficiency.
"""

import bz2
import re
import os
import sys
import xml.etree.ElementTree as ET
import json
import urllib.request

from config import RAW_DIR, ensure_dirs


# Wikipedia XML namespace
WIKI_NS = "{http://www.mediawiki.org/xml/export-0.11/}"


def find_dump_file():
    """Find an existing Telugu Wikipedia dump file in the raw data directory."""
    ensure_dirs()
    if not os.path.exists(RAW_DIR):
        return None
    for fname in os.listdir(RAW_DIR):
        if fname.startswith("tewiki") and fname.endswith(".xml.bz2"):
            return os.path.join(RAW_DIR, fname)
    return None


def download_dump(dump_url=None):
    """
    Download the Telugu Wikipedia dump.
    Uses streaming download with progress information.
    
    Args:
        dump_url: URL to download. If None, uses the latest known dump URL.
    
    Returns:
        Path to downloaded file, or None if download failed.
    """
    if dump_url is None:
        # Try the November 2026 dump first, then fall back
        dump_url = "https://dumps.wikimedia.org/tewiki/20261101/tewiki-20261101-pages-articles-multistream.xml.bz2"
    
    filename = dump_url.split("/")[-1]
    filepath = os.path.join(RAW_DIR, filename)
    
    if os.path.exists(filepath):
        print(f"Dump file already exists: {filepath}")
        return filepath
    
    ensure_dirs()
    print(f"Downloading Telugu Wikipedia dump...")
    print(f"URL: {dump_url}")
    print(f"Saving to: {filepath}")
    
    try:
        req = urllib.request.Request(dump_url, headers={"User-Agent": "TelguWikiIndexer/1.0"})
        response = urllib.request.urlopen(req, timeout=30)
        
        total_size = response.headers.get("Content-Length")
        if total_size:
            total_size = int(total_size)
            print(f"File size: {total_size / (1024*1024):.1f} MB")
        
        downloaded = 0
        chunk_size = 1024 * 1024  # 1 MB chunks
        
        with open(filepath, "wb") as f:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(f"\rProgress: {downloaded/(1024*1024):.1f} MB / {total_size/(1024*1024):.1f} MB ({pct:.1f}%)", end="", flush=True)
                else:
                    print(f"\rDownloaded: {downloaded/(1024*1024):.1f} MB", end="", flush=True)
        
        print(f"\nDownload complete: {filepath}")
        return filepath
    
    except Exception as e:
        print(f"\nDownload failed: {e}")
        # Clean up partial download
        if os.path.exists(filepath):
            os.remove(filepath)
        return None


def clean_wiki_text(text):
    """
    Clean Wikipedia markup from article text.
    
    Removes:
    - References (<ref>...</ref>)
    - HTML tags
    - Templates ({{...}})
    - Internal links ([[...]])
    - External links ([http...])
    - Formatting syntax (''', '', ==, etc.)
    - Categories, files, images
    
    Preserves meaningful Telugu text content.
    """
    if not text:
        return ""
    
    # Remove <ref>...</ref> tags and self-closing <ref ... />
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^/]*/>', '', text)
    text = re.sub(r'<ref[^>]*>', '', text)
    text = re.sub(r'</ref>', '', text)
    
    # Remove HTML comments
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # Remove remaining HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove templates {{...}} (handle nested braces simply)
    # Do multiple passes to handle nesting
    for _ in range(5):
        new_text = re.sub(r'\{\{[^{}]*\}\}', '', text)
        if new_text == text:
            break
        text = new_text
    
    # Remove leftover {{ and }}
    text = text.replace('{{', '').replace('}}', '')
    
    # Remove categories and file/image links
    text = re.sub(r'\[\[(వర్గం|Category|File|Image|చిత్రం|దస్త్రం):[^\]]*\]\]', '', text, flags=re.IGNORECASE)
    
    # Process internal links [[target|display]] -> display, [[target]] -> target
    text = re.sub(r'\[\[[^\]]*\|([^\]]*)\]\]', r'\1', text)
    text = re.sub(r'\[\[([^\]]*)\]\]', r'\1', text)
    
    # Remove external links [http... display] -> display
    text = re.sub(r'\[https?://[^\s\]]*\s*([^\]]*)\]', r'\1', text)
    text = re.sub(r'\[https?://[^\]]*\]', '', text)
    text = re.sub(r'https?://\S+', '', text)
    
    # Remove formatting
    text = text.replace("'''", "").replace("''", "")
    
    # Remove heading markers
    text = re.sub(r'={2,}', '', text)
    
    # Remove list markers
    text = re.sub(r'^\*+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^;+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^:+\s*', '', text, flags=re.MULTILINE)
    
    # Remove table markup
    text = re.sub(r'\{\|.*?\|\}', '', text, flags=re.DOTALL)
    text = re.sub(r'^\|.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^!.*$', '', text, flags=re.MULTILINE)
    
    # Remove magic words and parser functions
    text = re.sub(r'__[A-Z]+__', '', text)
    
    # Collapse multiple whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    
    return text


def is_redirect(text):
    """Check if article text is a redirect."""
    if not text:
        return True
    text_lower = text.strip().lower()
    return text_lower.startswith("#redirect") or text_lower.startswith("#దారిమార్పు")


def extract_articles(dump_path, limit=10000):
    """
    Extract articles from a Telugu Wikipedia XML dump (BZ2 compressed).
    
    Uses streaming XML parsing for memory efficiency.
    Processes only main-namespace articles, skips redirects and empty articles.
    
    Args:
        dump_path: Path to the .xml.bz2 dump file
        limit: Maximum number of articles to extract
    
    Yields:
        dict with keys: id, title, text (cleaned)
    """
    print(f"Extracting articles from: {dump_path}")
    print(f"Article limit: {limit}")
    
    count = 0
    skipped_redirects = 0
    skipped_empty = 0
    
    # Open BZ2 file for streaming decompression (binary mode for speed)
    with bz2.open(dump_path, 'rb') as f:
        # Use iterparse for streaming XML parsing
        context = ET.iterparse(f, events=('start', 'end'))
        _, root = next(context)
        
        for event, elem in context:
            # Look for <page> elements on 'end' event
            if event == 'end' and (elem.tag == WIKI_NS + 'page' or elem.tag == 'page'):
                # Determine the namespace prefix used
                ns_prefix = ""
                if elem.tag.startswith('{'):
                    ns_prefix = elem.tag.split('}')[0] + '}'
                
                # Check namespace (0 = main articles)
                ns_elem = elem.find(ns_prefix + 'ns')
                if ns_elem is not None and ns_elem.text != '0':
                    elem.clear()
                    root.clear()
                    continue
                
                # Get article ID
                id_elem = elem.find(ns_prefix + 'id')
                article_id = id_elem.text if id_elem is not None else None
                
                # Get title
                title_elem = elem.find(ns_prefix + 'title')
                title = title_elem.text if title_elem is not None else ""
                
                # Get text content
                revision = elem.find(ns_prefix + 'revision')
                text = ""
                if revision is not None:
                    text_elem = revision.find(ns_prefix + 'text')
                    if text_elem is not None and text_elem.text:
                        text = text_elem.text
                
                # Skip redirects
                if is_redirect(text):
                    skipped_redirects += 1
                    elem.clear()
                    root.clear()
                    continue
                
                # Clean the text
                cleaned = clean_wiki_text(text)
                
                # Skip empty articles
                if not cleaned or len(cleaned.strip()) < 50:
                    skipped_empty += 1
                    elem.clear()
                    root.clear()
                    continue
                
                count += 1
                
                if count % 500 == 0:
                    print(f"  Extracted {count} articles...", flush=True)
                
                yield {
                    'id': article_id,
                    'title': title,
                    'text': cleaned
                }
                
                # Clear element and root to prevent memory accumulation
                elem.clear()
                root.clear()
                
                if count >= limit:
                    break
    
    print(f"\nExtraction complete:")
    print(f"  Articles extracted: {count}")
    print(f"  Redirects skipped: {skipped_redirects}")
    print(f"  Empty articles skipped: {skipped_empty}")
