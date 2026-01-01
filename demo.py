#!/usr/bin/env python3
"""
Example demonstration of the Dropbox Auto-Organizer
This script shows what files would be organized and where they would go.
No actual Dropbox connection required.
"""

import sys
import os
import re

# Add parent directory to path to import the organizer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from organize_dropbox import DropboxOrganizer


def demo_file_classification():
    """Demonstrate file classification logic."""
    print("=" * 70)
    print("DROPBOX AUTO-ORGANIZER - DEMO")
    print("=" * 70)
    print()
    
    # Example files to classify
    test_files = [
        "vacation_2023_beach.jpg",
        "family_photo_2022.png",
        "IMG_20240101_120000.jpg",
        "report.pdf",
        "meeting_notes.docx",
        "project_plan.txt",
        "data_analysis.xlsx",
        "USER_SCOPED_TEMP_abc123",
        "file_sync_temp",
        "backup.tmp",
        "random_file.dat",
        "presentation.pptx",
        "oldphoto_1999.jpg",
        ".dropbox",
        "README.md"
    ]
    
    print("FILE CLASSIFICATION DEMO")
    print("-" * 70)
    print()
    
    # Create mock config for testing
    config = {
        'folders': {
            'photos': 'Photos Archive',
            'documents': 'Documents & Files',
            'temp': 'Temp Files'
        },
        'rules': {
            'photos': {
                'enabled': True,
                'year_pattern': r'20\d{2}'
            },
            'documents': {
                'enabled': True,
                'extensions': ['.pdf', '.docx', '.txt', '.xlsx', '.pptx', '.doc', '.xls']
            },
            'temp': {
                'enabled': True,
                'patterns': ['USER_SCOPED_TEMP', '_sync', '.tmp']
            }
        },
        'skip': {
            'folders': ['Photos Archive', 'Documents & Files'],
            'files': ['.dropbox']
        }
    }
    
    # Simulate classification
    for filename in test_files:
        print(f"File: {filename}")
        
        # Check if should skip
        if filename in config['skip']['files']:
            print(f"  → SKIPPED (in skip list)")
            print()
            continue
        
        # Check for year in filename
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            year = year_match.group(0)
            destination = f"/{config['folders']['photos']}/{year}/{filename}"
            print(f"  → PHOTO: Detected year {year}")
            print(f"  → Destination: {destination}")
            print()
            continue
        
        # Check if document
        file_ext = os.path.splitext(filename.lower())[1]
        if file_ext in config['rules']['documents']['extensions']:
            destination = f"/{config['folders']['documents']}/{filename}"
            print(f"  → DOCUMENT: Extension {file_ext}")
            print(f"  → Destination: {destination}")
            print()
            continue
        
        # Check if temp file
        is_temp = False
        for pattern in config['rules']['temp']['patterns']:
            if pattern in filename:
                destination = f"/{config['folders']['temp']}/{filename}"
                print(f"  → TEMP FILE: Matched pattern '{pattern}'")
                print(f"  → Destination: {destination}")
                is_temp = True
                break
        
        if is_temp:
            print()
            continue
        
        # No match
        print(f"  → NO MATCH: File will remain in current location")
        print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("This demo shows how files would be organized:")
    print("  • Photos with years (20XX) → Photos Archive/YEAR/")
    print("  • Documents (.pdf, .docx, etc.) → Documents & Files/")
    print("  • Temp files (patterns) → Temp Files/")
    print("  • Other files remain in place")
    print()
    print("To use with your Dropbox:")
    print("  1. Set up your .env file with DROPBOX_ACCESS_TOKEN")
    print("  2. Run: python organize_dropbox.py")
    print("  3. Use dry_run: true in config.yaml to test first")
    print()


if __name__ == "__main__":
    demo_file_classification()
