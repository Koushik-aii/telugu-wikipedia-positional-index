"""
package_submission.py - Create submission ZIP files

Creates:
1. <ROLL_NO>-src.zip   - Source code ZIP
2. <ROLL_NO>-A1-PostIndex-IR-M2026.zip - Final submission ZIP containing:
   - README.txt
   - <ROLL_NO>-src.zip
   - output.txt
"""

import argparse
import os
import zipfile
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Files and directories to include in the source ZIP
SOURCE_INCLUDES = [
    'config.py',
    'tokenizer.py',
    'dataset.py',
    'indexer.py',
    'search.py',
    'main.py',
    'generate_output.py',
    'package_submission.py',
    '_download_dump.py',
    'requirements.txt',
    'README.txt',
    'tests/',
]

# Patterns to exclude from the source ZIP
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.pyc',
    '.git',
    'venv',
    '.env',
    'data/raw/',
    'data/index/',
    '_temp_',
    '.db',
]


def should_exclude(filepath):
    """Check if a file should be excluded from the source ZIP."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath:
            return True
    return False


def create_source_zip(roll_no):
    """Create the source code ZIP file."""
    zip_name = f"{roll_no}-src.zip"
    zip_path = os.path.join(BASE_DIR, zip_name)
    
    print(f"Creating source ZIP: {zip_name}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in SOURCE_INCLUDES:
            full_path = os.path.join(BASE_DIR, item)
            
            if os.path.isfile(full_path):
                if not should_exclude(full_path):
                    zf.write(full_path, item)
                    print(f"  Added: {item}")
            elif os.path.isdir(full_path):
                for root, dirs, files in os.walk(full_path):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if not should_exclude(d)]
                    
                    for fname in files:
                        file_path = os.path.join(root, fname)
                        if not should_exclude(file_path):
                            arcname = os.path.relpath(file_path, BASE_DIR)
                            zf.write(file_path, arcname)
                            print(f"  Added: {arcname}")
    
    print(f"Source ZIP created: {zip_path}")
    return zip_path


def create_submission_zip(roll_no, src_zip_path):
    """Create the final submission ZIP file."""
    zip_name = f"{roll_no}-A1-PostIndex-IR-M2026.zip"
    zip_path = os.path.join(BASE_DIR, zip_name)
    
    readme_path = os.path.join(BASE_DIR, "README.txt")
    output_path = os.path.join(BASE_DIR, "output.txt")
    
    # Verify required files exist
    missing = []
    if not os.path.exists(readme_path):
        missing.append("README.txt")
    if not os.path.exists(output_path):
        missing.append("output.txt")
    if not os.path.exists(src_zip_path):
        missing.append(os.path.basename(src_zip_path))
    
    if missing:
        print(f"Error: Missing required files: {', '.join(missing)}")
        sys.exit(1)
    
    print(f"\nCreating submission ZIP: {zip_name}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(readme_path, "README.txt")
        print(f"  Added: README.txt")
        
        zf.write(src_zip_path, os.path.basename(src_zip_path))
        print(f"  Added: {os.path.basename(src_zip_path)}")
        
        zf.write(output_path, "output.txt")
        print(f"  Added: output.txt")
    
    print(f"Submission ZIP created: {zip_path}")
    
    # Verify contents
    print("\nVerifying submission ZIP contents:")
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        for name in names:
            info = zf.getinfo(name)
            print(f"  {name} ({info.file_size} bytes)")
        
        # Check exactly 3 files
        if len(names) == 3:
            print("\nVerification: PASS (exactly 3 files)")
        else:
            print(f"\nVerification: WARNING (expected 3 files, found {len(names)})")
    
    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Package submission ZIP files")
    parser.add_argument(
        '--roll-no', type=str, default='YOUR_ROLL_NO',
        help='Your roll number (e.g., 24CS12345)'
    )
    args = parser.parse_args()
    
    roll_no = args.roll_no
    print(f"Roll Number: {roll_no}")
    print()
    
    # Step 1: Create source ZIP
    src_zip = create_source_zip(roll_no)
    
    # Step 2: Create final submission ZIP
    sub_zip = create_submission_zip(roll_no, src_zip)
    
    print(f"\n{'=' * 50}")
    print("Packaging complete!")
    print(f"  Source ZIP: {src_zip}")
    print(f"  Submission ZIP: {sub_zip}")
    print(f"{'=' * 50}")


if __name__ == '__main__':
    main()

