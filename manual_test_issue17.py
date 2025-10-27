#!/usr/bin/env python3
"""
Manual test script to reproduce Issue #17
"""

import logging
import sys
from pathlib import Path
from duplicate_images.duplicate import get_matches
from duplicate_images.pair_finder_options import PairFinderOptions

# Enable logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def main():
    if len(sys.argv) < 2:
        print("Usage: python manual_test_issue17.py <image_directory>")
        sys.exit(1)

    image_dir = Path(sys.argv[1])
    cache_file = Path('test_hashes.json')

    print(f"\n=== First scan: Creating cache ===")
    matches1 = get_matches([image_dir], 'phash', hash_store_path=cache_file)
    print(f"Found {len(matches1)} duplicate groups")

    print(f"\n=== Second scan: Should use cache ===")
    matches2 = get_matches([image_dir], 'phash', hash_store_path=cache_file)
    print(f"Found {len(matches2)} duplicate groups")

    if matches1 == matches2:
        print("\n✓ Results match - cache is working correctly")
    else:
        print("\n✗ Results differ - cache may not be working")

if __name__ == '__main__':
    main()
