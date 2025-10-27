# pylint: disable=missing-docstring
"""
Test for Issue #17: JSON hash database not being used
https://github.com/lene/DuplicateImages/issues/17

The bug: When saving JSON hashes, paths are resolved to absolute paths.
When loading, paths are not resolved. This causes a mismatch when scanning
with relative paths, making the cache useless.
"""
__author__ = 'Lene Preuss <lene.preuss@gmail.com>'

from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from duplicate_images.duplicate import get_matches
from duplicate_images.pair_finder_options import PairFinderOptions


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
def test_json_cache_is_actually_used_with_relative_paths(
        tmp_dir: Path, data_dir: Path, test_set: str
) -> None:
    """
    Reproduce Issue #17: JSON hash database loads but doesn't use cached hashes.

    This test:
    1. Scans a directory and creates a JSON cache
    2. Scans again using the same (relative) paths
    3. Verifies that the hash function is NOT called (cached values used)
    """
    folder = data_dir / test_set
    cache_file = tmp_dir / 'hashes.json'

    # First scan: create the cache
    matches1 = get_matches([folder], 'phash', hash_store_path=cache_file)
    assert cache_file.is_file()

    # Second scan with the SAME path: should use cache
    with patch('imagehash.phash') as mock_phash:
        mock_phash.return_value = Mock()  # Should never be called
        matches2 = get_matches([folder], 'phash', hash_store_path=cache_file)

        # The bug: phash is called again even though cache exists
        assert mock_phash.call_count == 0, \
            f"phash was called {mock_phash.call_count} times, but should use cached hashes"

        assert matches1 == matches2


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
def test_json_cache_with_absolute_vs_relative_paths(
        tmp_dir: Path, data_dir: Path, test_set: str
) -> None:
    """
    Test that demonstrates the path resolution mismatch.

    When you scan with a relative path, then scan again with an absolute path
    (or vice versa), the cache should still work.
    """
    folder = data_dir / test_set
    cache_file = tmp_dir / 'hashes.json'

    # First scan with relative path
    relative_folder = Path('.') / folder.relative_to(Path.cwd())
    get_matches([relative_folder], 'phash', hash_store_path=cache_file)

    # Second scan with absolute path - should still use cache
    with patch('imagehash.phash') as mock_phash:
        mock_phash.return_value = Mock()
        get_matches([folder.resolve()], 'phash', hash_store_path=cache_file)

        # The bug: cache keys don't match because of path resolution mismatch
        assert mock_phash.call_count == 0, \
            "Cache should work regardless of relative vs absolute paths"


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
def test_pickle_cache_works_correctly_as_comparison(
        tmp_dir: Path, data_dir: Path, test_set: str
) -> None:
    """
    Verify that Pickle format works correctly (as reported in Issue #17).
    This serves as a comparison to show JSON is broken.
    """
    folder = data_dir / test_set
    cache_file = tmp_dir / 'hashes.pickle'

    # First scan: create the cache
    get_matches([folder], 'phash', hash_store_path=cache_file)

    # Second scan: should use cache
    with patch('imagehash.phash') as mock_phash:
        mock_phash.return_value = Mock()
        get_matches([folder], 'phash', hash_store_path=cache_file)

        # Pickle should work correctly
        assert mock_phash.call_count == 0, \
            "Pickle cache should work (as reported by user)"


@pytest.mark.parametrize('test_set', ['equal_but_binary_different'])
def test_json_cache_lookup_with_actual_file_path(
        tmp_dir: Path, data_dir: Path, test_set: str
) -> None:
    """
    Test the actual cache lookup mechanism more directly.
    """
    from duplicate_images.hash_store import JSONHashStore
    from duplicate_images.methods import IMAGE_HASH_ALGORITHM, get_hash_size_kwargs

    folder = data_dir / test_set
    cache_file = tmp_dir / 'hashes.json'

    # Create a hash store and add some hashes
    hash_func = IMAGE_HASH_ALGORITHM['phash']
    hash_kwargs = get_hash_size_kwargs(hash_func, None)

    with JSONHashStore(cache_file, 'phash', hash_kwargs) as store:
        test_file = next(folder.glob('**/*.jpg'))
        from PIL import Image
        test_hash = hash_func(Image.open(test_file), **hash_kwargs)
        store.add(test_file, test_hash)

    # Now try to retrieve it
    with JSONHashStore(cache_file, 'phash', hash_kwargs) as store:
        # This should find the hash, but won't due to the bug
        retrieved = store.get(test_file)
        assert retrieved is not None, \
            f"Should retrieve hash for {test_file}, but got None"
        assert retrieved == test_hash
