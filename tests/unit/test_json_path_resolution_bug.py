# pylint: disable=missing-docstring
"""
Unit test for Issue #17: Path resolution mismatch in JSON hash store

The bug: JSONHashStore.dump() uses str(k.resolve()) but
JSONHashStore.load() uses Path(k) without resolving.
This causes cache misses when paths don't match exactly.
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

import json
from pathlib import Path
import pytest

from duplicate_images.hash_store import JSONHashStore


def test_json_store_path_resolution_mismatch(tmp_path: Path):
    """
    Demonstrates the path resolution bug in JSON hash store.

    When we add a path to the store and save it, the path is resolved.
    When we load and try to get the same (unresolved) path, it fails.
    """
    cache_file = tmp_path / 'test.json'

    # Create a test file
    test_file = tmp_path / 'test_image.txt'
    test_file.write_text('fake image')

    # Use a relative path (or different representation)
    relative_path = Path('.') / test_file.relative_to(Path.cwd())

    # Store with relative path
    with JSONHashStore(cache_file, 'phash', {'hash_size': 8}) as store:
        # Mock hash value
        from imagehash import hex_to_hash
        mock_hash = hex_to_hash('0' * 16)
        store.add(relative_path, mock_hash)

    # Check what was actually saved in JSON
    with open(cache_file) as f:
        saved_data = json.load(f)
        saved_keys = list(saved_data[0].keys())
        print(f"Saved key: {saved_keys[0]}")
        print(f"Looking for: {str(relative_path)}")
        print(f"Resolved looking for: {str(relative_path.resolve())}")

    # Try to retrieve with the same relative path
    with JSONHashStore(cache_file, 'phash', {'hash_size': 8}) as store:
        retrieved = store.get(relative_path)

        # This should work but won't if there's a path mismatch
        assert retrieved is not None, \
            f"Failed to retrieve hash for {relative_path}. " \
            f"Saved as {saved_keys[0]}, looked up as {relative_path}"


def test_json_vs_pickle_path_handling(tmp_path: Path):
    """
    Compare how JSON and Pickle stores handle paths.
    Pickle should work, JSON might not.
    """
    from duplicate_images.hash_store import PickleHashStore
    from imagehash import hex_to_hash

    test_file = tmp_path / 'test_image.txt'
    test_file.write_text('fake image')
    mock_hash = hex_to_hash('0' * 16)

    # Test with relative path
    relative_path = Path('.') / test_file.relative_to(Path.cwd())

    # Pickle store
    pickle_file = tmp_path / 'test.pickle'
    with PickleHashStore(pickle_file, 'phash', {'hash_size': 8}) as store:
        store.add(relative_path, mock_hash)

    with PickleHashStore(pickle_file, 'phash', {'hash_size': 8}) as store:
        pickle_retrieved = store.get(relative_path)

    # JSON store
    json_file = tmp_path / 'test.json'
    with JSONHashStore(json_file, 'phash', {'hash_size': 8}) as store:
        store.add(relative_path, mock_hash)

    with JSONHashStore(json_file, 'phash', {'hash_size': 8}) as store:
        json_retrieved = store.get(relative_path)

    # Both should work the same way
    assert pickle_retrieved is not None, "Pickle store should work"
    assert json_retrieved is not None, "JSON store should work (but doesn't due to bug)"
    assert pickle_retrieved == json_retrieved


def test_json_saved_keys_are_resolved(tmp_path: Path):
    """
    Verify that JSON store saves resolved (absolute) paths.
    """
    from imagehash import hex_to_hash

    cache_file = tmp_path / 'test.json'
    test_file = tmp_path / 'test_image.txt'
    test_file.write_text('fake image')

    # Use a non-resolved path (with ../ or ./)
    non_resolved_path = tmp_path / '.' / 'test_image.txt'

    with JSONHashStore(cache_file, 'phash', {'hash_size': 8}) as store:
        mock_hash = hex_to_hash('0' * 16)
        store.add(non_resolved_path, mock_hash)

    # Check the saved JSON
    with open(cache_file) as f:
        data = json.load(f)
        saved_keys = list(data[0].keys())

        # The saved key should be an absolute path (resolved)
        assert len(saved_keys) == 1
        saved_path = Path(saved_keys[0])

        print(f"\nInput path: {non_resolved_path}")
        print(f"Saved path: {saved_path}")
        print(f"Resolved input: {non_resolved_path.resolve()}")

        # It should be absolute
        assert saved_path.is_absolute(), \
            f"Saved path should be absolute, got: {saved_path}"

        # It should match the resolved version of our input
        assert str(saved_path) == str(non_resolved_path.resolve()), \
            f"Saved path {saved_path} should match resolved input {non_resolved_path.resolve()}"
